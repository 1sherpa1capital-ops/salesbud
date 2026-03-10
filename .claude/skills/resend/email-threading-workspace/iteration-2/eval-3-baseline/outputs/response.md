# Complete Solution: Email Conversation Tracking with Resend

## Overview

This guide provides a complete solution for tracking email conversations with Resend, enabling you to send emails to clients and when they reply, look up the original conversation and send properly threaded responses that reference all previous emails.

---

## How Email Threading Works

Email clients (Gmail, Outlook, Apple Mail) group related emails into conversations using three key headers:

| Header | Purpose |
|--------|---------|
| `Message-ID` | Unique identifier for THIS email |
| `In-Reply-To` | Message-ID of the email being replied to |
| `References` | Space-separated list of ALL Message-IDs in the conversation |

### The Threading Chain

```
Email 1 (You)          Email 2 (Client)       Email 3 (You)
Message-ID: <A>   →   In-Reply-To: <A>  →   In-Reply-To: <B>
                       Message-ID: <B>        References: <A> <B>
                                              Message-ID: <C>
```

---

## Architecture Overview

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Your Database  │     │   Resend     │     │  Client Email   │
│                 │     │              │     │                 │
│  conversations  │◄────┤  Send API    ├────►│  Gmail/Outlook  │
│  messages       │     └──────┬───────┘     └────────┬────────┘
│                 │            │                      │
└─────────────────┘            │                      │
       ▲                       │                      │
       │              ┌────────▼────────┐            │
       │              │  Webhook        │            │
       └──────────────┤  email.received │◄───────────┘
                      └─────────────────┘
```

---

## Database Schema

### Conversations Table

```sql
CREATE TABLE conversations (
  id TEXT PRIMARY KEY,                    -- Your conversation ID
  recipient TEXT NOT NULL,                -- Client email address
  subject TEXT NOT NULL,                  -- Original subject
  status TEXT DEFAULT 'active',           -- active, closed, archived
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  original_message_id TEXT,               -- Your first email's Message-ID
  started_by TEXT DEFAULT 'us'            -- 'us' or 'external'
);
```

### Messages Table

```sql
CREATE TABLE messages (
  id TEXT PRIMARY KEY,
  conversation_id TEXT REFERENCES conversations(id),
  message_id TEXT UNIQUE NOT NULL,        -- The actual Message-ID header
  in_reply_to TEXT,                       -- Parent message Message-ID
  references_chain TEXT,                  -- Space-separated Message-IDs
  direction TEXT NOT NULL,                -- 'sent' or 'received'
  from_address TEXT NOT NULL,
  to_address TEXT NOT NULL,
  subject TEXT NOT NULL,
  html_body TEXT,
  text_body TEXT,
  sent_at TIMESTAMP,
  received_at TIMESTAMP,
  resend_id TEXT                          -- Resend's email ID (for sent)
);
```

---

## Implementation

### Step 1: Send Initial Email (Start Conversation)

```typescript
import { Resend } from 'resend';
import { v4 as uuidv4 } from 'uuid';

const resend = new Resend(process.env.RESEND_API_KEY);

interface Conversation {
  id: string;
  recipient: string;
  subject: string;
  originalMessageId: string;
  resendId: string;
}

async function startConversation(
  recipient: string,
  subject: string,
  htmlContent: string,
  textContent?: string
): Promise<Conversation> {
  // Generate unique identifiers
  const conversationId = uuidv4();
  const messageId = `<${conversationId}@yourdomain.com>`;

  // Send the email
  const { data, error } = await resend.emails.send({
    from: 'Your Company <team@yourdomain.com>',
    to: [recipient],
    subject,
    html: htmlContent,
    text: textContent,
    headers: {
      'Message-ID': messageId,
      'X-Conversation-ID': conversationId,
    },
  });

  if (error) throw error;

  // Store in database
  const conversation: Conversation = {
    id: conversationId,
    recipient,
    subject,
    originalMessageId: messageId,
    resendId: data.id,
  };

  await db.conversations.create({
    id: conversationId,
    recipient,
    subject,
    original_message_id: messageId,
    started_by: 'us',
    created_at: new Date(),
  });

  await db.messages.create({
    id: uuidv4(),
    conversation_id: conversationId,
    message_id: messageId,
    direction: 'sent',
    from_address: 'team@yourdomain.com',
    to_address: recipient,
    subject,
    html_body: htmlContent,
    text_body: textContent,
    sent_at: new Date(),
    resend_id: data.id,
  });

  return conversation;
}
```

### Step 2: Webhook Handler (Receive Replies)

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

interface EmailReceivedEvent {
  type: 'email.received';
  created_at: string;
  data: {
    email_id: string;
    message_id: string;        // ← Their Message-ID (use for threading!)
    from: string;
    to: string[];
    cc?: string[];
    bcc?: string[];
    subject: string;
    in_reply_to?: string;      // ← Points to your original email
    created_at: string;
    attachments?: Array<{
      id: string;
      filename: string;
      content_type: string;
    }>;
  };
}

export async function handleWebhook(req: Request): Promise<Response> {
  // 1. Verify webhook signature (CRITICAL!)
  const payload = await req.text();
  const signature = req.headers.get('svix-signature');
  const timestamp = req.headers.get('svix-timestamp');
  const id = req.headers.get('svix-id');

  const event = resend.webhooks.verify({
    payload,
    headers: {
      'svix-id': id,
      'svix-timestamp': timestamp,
      'svix-signature': signature,
    },
    secret: process.env.RESEND_WEBHOOK_SECRET,
  }) as EmailReceivedEvent;

  if (event.type !== 'email.received') {
    return new Response('OK', { status: 200 });
  }

  // 2. Extract key data
  const {
    email_id,
    message_id,        // Their Message-ID
    from,
    to,
    subject,
    in_reply_to,       // Your Message-ID they're replying to
  } = event.data;

  console.log('Received reply:', {
    from,
    theirMessageId: message_id,
    inReplyTo: in_reply_to,
  });

  // 3. Fetch full email content (webhook only has metadata)
  const { data: email } = await resend.emails.receiving.get(email_id);

  // 4. Find or create conversation
  let conversationId: string;

  if (in_reply_to) {
    // Try to find existing conversation
    const existingMsg = await db.messages.findByMessageId(in_reply_to);
    if (existingMsg) {
      conversationId = existingMsg.conversation_id;
      console.log(`Found conversation: ${conversationId}`);
    } else {
      // Reply to unknown email - create new conversation
      conversationId = await createNewConversation(from, subject, 'external');
    }
  } else {
    // New email without reply reference
    conversationId = await createNewConversation(from, subject, 'external');
  }

  // 5. Store received message
  await db.messages.create({
    id: uuidv4(),
    conversation_id: conversationId,
    message_id,              // Store their Message-ID
    in_reply_to,
    direction: 'received',
    from_address: from,
    to_address: to[0],
    subject,
    html_body: email.html,
    text_body: email.text,
    received_at: new Date(),
  });

  // 6. Update conversation timestamp
  await db.conversations.update(conversationId, {
    updated_at: new Date(),
  });

  // 7. (Optional) Process auto-reply or notification
  // await processReply(conversationId, from, subject, email.text);

  return new Response('OK', { status: 200 });
}

async function createNewConversation(
  recipient: string,
  subject: string,
  startedBy: 'us' | 'external'
): Promise<string> {
  const id = uuidv4();
  await db.conversations.create({
    id,
    recipient,
    subject,
    started_by: startedBy,
    created_at: new Date(),
    updated_at: new Date(),
  });
  return id;
}
```

### Step 3: Send Threaded Reply

```typescript
interface ThreadedReplyOptions {
  conversationId: string;
  replyToMessageId: string;    // The Message-ID you're replying to
  to: string;
  subject: string;
  htmlContent: string;
  textContent?: string;
}

async function sendThreadedReply(options: ThreadedReplyOptions): Promise<string> {
  const { conversationId, replyToMessageId, to, subject, htmlContent, textContent } = options;

  // 1. Get conversation history
  const messages = await db.messages.findByConversation(conversationId, {
    orderBy: 'sent_at ASC',
  });

  // 2. Build References chain (all Message-IDs in order)
  const messageIds = messages.map(m => m.message_id);
  const references = messageIds.join(' ');

  // 3. Generate new Message-ID for this reply
  const newMessageId = `<reply-${Date.now()}-${uuidv4().slice(0, 8)}@yourdomain.com>`;

  // 4. Clean subject (ensure it has Re: prefix)
  const cleanSubject = subject.startsWith('Re:')
    ? subject
    : `Re: ${subject}`;

  // 5. Send the reply
  const { data, error } = await resend.emails.send({
    from: 'Your Company <team@yourdomain.com>',
    to: [to],
    subject: cleanSubject,
    html: htmlContent,
    text: textContent,
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': replyToMessageId,    // ← Links to their email
      'References': references,            // ← Full conversation chain
      'X-Conversation-ID': conversationId,
    },
  });

  if (error) throw error;

  // 6. Store sent message
  await db.messages.create({
    id: uuidv4(),
    conversation_id: conversationId,
    message_id: newMessageId,
    in_reply_to: replyToMessageId,
    references_chain: references,
    direction: 'sent',
    from_address: 'team@yourdomain.com',
    to_address: to,
    subject: cleanSubject,
    html_body: htmlContent,
    text_body: textContent,
    sent_at: new Date(),
    resend_id: data.id,
  });

  // 7. Update conversation
  await db.conversations.update(conversationId, {
    updated_at: new Date(),
  });

  return data.id;
}
```

### Step 4: Reply with Quoted History

```typescript
interface QuotedReplyOptions extends ThreadedReplyOptions {
  includeQuotedHistory?: boolean;
}

async function sendQuotedReply(options: QuotedReplyOptions): Promise<string> {
  const {
    conversationId,
    replyToMessageId,
    to,
    subject,
    htmlContent,
    textContent,
    includeQuotedHistory = true
  } = options;

  // Get the message we're replying to
  const originalMessage = await db.messages.findByMessageId(replyToMessageId);

  if (!originalMessage) {
    throw new Error('Original message not found');
  }

  // Build quoted content
  let finalHtml = htmlContent;
  let finalText = textContent || '';

  if (includeQuotedHistory) {
    const date = new Date(originalMessage.received_at || originalMessage.sent_at)
      .toLocaleString();

    const quotedHtml = `
      <br>
      <div style="border-left: 2px solid #ccc; margin-left: 10px; padding-left: 10px; color: #666;">
        <p>On ${date}, ${originalMessage.from_address} wrote:</p>
        <div>${originalMessage.html_body || originalMessage.text_body}</div>
      </div>
    `;

    const quotedText = `\n\nOn ${date}, ${originalMessage.from_address} wrote:\n${originalMessage.text_body || ''}`;

    finalHtml = htmlContent + quotedHtml;
    finalText = finalText + quotedText;
  }

  return sendThreadedReply({
    conversationId,
    replyToMessageId,
    to,
    subject,
    htmlContent: finalHtml,
    textContent: finalText,
  });
}
```

---

## Complete Working Example

### Next.js API Route

```typescript
// app/api/webhooks/resend/route.ts
import { Resend } from 'resend';
import { NextRequest, NextResponse } from 'next/server';

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(req: NextRequest) {
  try {
    // Verify webhook
    const payload = await req.text();
    const event = resend.webhooks.verify({
      payload,
      headers: {
        'svix-id': req.headers.get('svix-id'),
        'svix-timestamp': req.headers.get('svix-timestamp'),
        'svix-signature': req.headers.get('svix-signature'),
      },
      secret: process.env.RESEND_WEBHOOK_SECRET,
    });

    if (event.type !== 'email.received') {
      return NextResponse.json({ status: 'ignored' });
    }

    const { email_id, message_id, from, to, subject, in_reply_to } = event.data;

    // Get full email content
    const { data: email } = await resend.emails.receiving.get(email_id);

    // Find conversation
    let conversation = null;
    if (in_reply_to) {
      conversation = await db.conversations.findByMessageId(in_reply_to);
    }

    // Create if not found
    if (!conversation) {
      conversation = await db.conversations.create({
        recipient: from,
        subject,
        started_by: 'external',
      });
    }

    // Store message
    await db.messages.create({
      conversation_id: conversation.id,
      message_id,
      in_reply_to,
      direction: 'received',
      from_address: from,
      to_address: to[0],
      subject,
      html_body: email.html,
      text_body: email.text,
      received_at: new Date(),
    });

    // Auto-reply example
    if (shouldAutoReply(subject)) {
      await sendAutoReply(conversation.id, message_id, from, subject);
    }

    return NextResponse.json({ status: 'processed' });
  } catch (error) {
    console.error('Webhook error:', error);
    return NextResponse.json(
      { error: 'Processing failed' },
      { status: 500 }
    );
  }
}

async function sendAutoReply(
  conversationId: string,
  replyToMessageId: string,
  to: string,
  subject: string
) {
  const messages = await db.messages.findByConversation(conversationId);
  const references = messages.map(m => m.message_id).join(' ');
  const newMessageId = `<auto-${Date.now()}@yourdomain.com>`;

  await resend.emails.send({
    from: 'Your Company <team@yourdomain.com>',
    to: [to],
    subject: `Re: ${subject.replace(/^Re: /, '')}`,
    html: '<p>Thanks for your email! We\'ll respond shortly.</p>',
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': replyToMessageId,
      'References': references,
    },
  });
}
```

---

## Common Mistakes to Avoid

### Mistake 1: Using Wrong Message-ID

**WRONG:**
```typescript
// Don't use email_id for threading
const messageId = event.data.email_id;  // Wrong!
```

**CORRECT:**
```typescript
// Use message_id from webhook data
const messageId = event.data.message_id;  // Correct!
```

### Mistake 2: Parsing JSON Before Verification

**WRONG:**
```typescript
const body = await req.json();  // Breaks signature verification!
const event = resend.webhooks.verify({ payload: JSON.stringify(body), ... });
```

**CORRECT:**
```typescript
const payload = await req.text();  // Raw body
const event = resend.webhooks.verify({ payload, ... });
```

### Mistake 3: Missing Threading Headers

**WRONG:**
```typescript
await resend.emails.send({
  to: [recipient],
  subject: 'Re: Subject',
  html: '<p>Reply</p>',
  // Missing headers!
});
```

**CORRECT:**
```typescript
await resend.emails.send({
  to: [recipient],
  subject: 'Re: Subject',
  html: '<p>Reply</p>',
  headers: {
    'Message-ID': newMessageId,
    'In-Reply-To': parentMessageId,
    'References': referencesChain,
  },
});
```

---

## Testing Your Implementation

### 1. Send Test Email

```typescript
const conversation = await startConversation(
  'your-test-email@gmail.com',
  'Test Conversation',
  '<p>This is a test email.</p>'
);
console.log('Conversation started:', conversation.id);
```

### 2. Reply from Gmail/Outlook

Reply to the test email from your email client.

### 3. Verify Webhook Received

Check your webhook handler logs:
```
Received reply: {
  from: 'your-test-email@gmail.com',
  theirMessageId: '<abc123@gmail.com>',
  inReplyTo: '<your-conv-id@yourdomain.com>'
}
```

### 4. Send Threaded Reply

```typescript
await sendThreadedReply({
  conversationId: conversation.id,
  replyToMessageId: '<abc123@gmail.com>',
  to: 'your-test-email@gmail.com',
  subject: 'Test Conversation',
  htmlContent: '<p>Thanks for your reply!</p>',
});
```

### 5. Verify Threading

Check Gmail/Outlook - all three emails should appear in the same conversation thread.

---

## Environment Variables

```bash
# Resend
RESEND_API_KEY=re_xxxxxxxxxxxxxxxx
RESEND_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxx

# Database
DATABASE_URL=postgresql://...

# Domain
EMAIL_DOMAIN=yourdomain.com
FROM_EMAIL=team@yourdomain.com
```

---

## Key Takeaways

1. **Always use `data.message_id`** from webhook payloads - it's the authoritative Message-ID
2. **Build the References chain** by appending each new Message-ID in order
3. **Set In-Reply-To** to the Message-ID you're directly replying to
4. **Store Message-IDs** in your database for building conversation chains
5. **Verify webhooks** using the raw body text, not parsed JSON
6. **Fetch full email content** using `resend.emails.receiving.get(email_id)` - webhooks only contain metadata

---

## Additional Resources

- [Resend Receiving Documentation](https://resend.com/docs/dashboard/receiving/introduction)
- [Resend Reply to Emails](https://resend.com/docs/dashboard/receiving/reply-to-emails)
- [Email Threading RFC 5322](https://tools.ietf.org/html/rfc5322#section-3.6.4)
