# Email Conversation Tracking with Resend

## Overview

To track email conversations with Resend, you need to use three key email headers that email clients (Gmail, Outlook, Apple Mail) use to group related emails into threads:

| Header | Purpose |
|--------|---------|
| `Message-ID` | Unique identifier for THIS email |
| `In-Reply-To` | Message-ID of the email being replied to |
| `References` | Space-separated list of ALL Message-IDs in the conversation |

**Critical Note:** When you send via Resend, Amazon SES may rewrite your custom Message-ID. The solution is to use the `message_id` from webhook payloads when replying.

---

## Complete Solution for Conversation Tracking

### 1. Database Schema for Tracking Conversations

```typescript
// Database schema to store conversations
interface Conversation {
  id: string;                    // Your internal conversation ID
  recipient: string;             // Client email address
  subject: string;               // Email subject
  originalMessageId: string;     // Your first email's Message-ID
  resendId: string;              // Resend's email ID
  createdAt: Date;
  messages: Message[];
}

interface Message {
  messageId: string;             // The actual Message-ID header value
  from: string;
  to: string;
  subject: string;
  html: string;
  text: string;
  direction: 'sent' | 'received';
  inReplyTo?: string;            // For replies, the parent Message-ID
  references?: string;           // Full conversation chain
  sentAt?: Date;
  receivedAt?: Date;
}
```

### 2. Send Initial Email (Start a Conversation)

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

async function startConversation(
  recipient: string,
  subject: string,
  content: string
) {
  // Generate unique identifiers
  const conversationId = `conv-${Date.now()}`;
  const messageId = `<${conversationId}@yourdomain.com>`;

  const { data, error } = await resend.emails.send({
    from: 'Your Company <team@yourdomain.com>',
    to: [recipient],
    subject,
    html: content,
    headers: {
      'Message-ID': messageId,
      'X-Conversation-ID': conversationId,  // Custom header for your tracking
    },
  });

  if (error) throw error;

  // Store conversation in your database
  await db.conversations.create({
    id: conversationId,
    recipient,
    subject,
    originalMessageId: messageId,
    resendId: data.id,
    createdAt: new Date(),
    messages: [{
      messageId,
      from: 'team@yourdomain.com',
      to: recipient,
      subject,
      html: content,
      direction: 'sent',
      sentAt: new Date(),
    }],
  });

  return { conversationId, messageId, resendId: data.id };
}
```

### 3. Webhook Handler to Receive Replies

When someone replies, Resend sends a webhook with their Message-ID. **Use `data.message_id` for threading, NOT `data.email_id`.**

```typescript
export async function POST(req: Request) {
  // 1. Verify webhook signature (CRITICAL - use raw body)
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
    return new Response('OK', { status: 200 });
  }

  // 2. Extract threading info from webhook
  const {
    email_id,        // Resend's internal ID (for fetching full email)
    message_id,      // ← THEIR Message-ID (use this for threading!)
    from,
    to,
    subject,
    in_reply_to,     // ← Points to your original email (if threaded)
  } = event.data;

  console.log('Received reply:', {
    from,
    theirMessageId: message_id,
    inReplyTo: in_reply_to,
  });

  // 3. Get full email content
  const { data: email } = await resend.emails.receiving.get(email_id);

  // 4. Find or create conversation
  let conversation;
  if (in_reply_to) {
    // This is a reply - find the conversation by the message they replied to
    conversation = await db.conversations.findByOriginalMessageId(in_reply_to);
  }

  if (!conversation) {
    // New conversation started by external sender
    conversation = await db.conversations.create({
      recipient: from,
      subject,
      startedBy: 'external',
    });
  }

  // 5. Store received message
  await db.messages.create({
    conversationId: conversation.id,
    messageId,           // Store their Message-ID!
    from,
    to: to[0],
    subject,
    html: email.html,
    text: email.text,
    direction: 'received',
    receivedAt: new Date(),
  });

  // 6. (Optional) Process or auto-reply
  await processReply(conversation, message_id, from, subject, email);

  return new Response('OK', { status: 200 });
}
```

### 4. Send Threaded Reply

Use their Message-ID in your reply headers to maintain the thread:

```typescript
async function sendReply(
  conversationId: string,
  replyToMessageId: string,  // The Message-ID you're replying to
  replyContent: string
) {
  // Get conversation history
  const conversation = await db.conversations.get(conversationId);
  const messages = await db.messages.findByConversation(conversationId);

  // Build References chain (all previous Message-IDs in order)
  const references = messages
    .map(m => m.messageId)
    .filter(Boolean)
    .join(' ');

  // Generate new Message-ID for this reply
  const newMessageId = `<reply-${Date.now()}@yourdomain.com>`;

  const { data, error } = await resend.emails.send({
    from: 'Your Company <team@yourdomain.com>',
    to: [conversation.recipient],
    subject: `Re: ${conversation.subject}`,
    html: replyContent,
    text: stripHtml(replyContent),
    headers: {
      'Message-ID': newMessageId,           // Your new email's ID
      'In-Reply-To': replyToMessageId,      // ← Links to their email
      'References': references,             // ← Full conversation chain
    },
  });

  if (error) throw error;

  // Update conversation with your reply
  await db.messages.create({
    conversationId,
    messageId: newMessageId,
    from: 'team@yourdomain.com',
    to: conversation.recipient,
    subject: `Re: ${conversation.subject}`,
    html: replyContent,
    direction: 'sent',
    inReplyTo: replyToMessageId,
    references,
    sentAt: new Date(),
  });

  return data.id;
}
```

### 5. Reply with Quoted Text (Full Thread Context)

To show the full conversation history in your reply:

```typescript
async function replyWithQuote(
  conversationId: string,
  replyToMessageId: string,
  replyContent: string
) {
  // Get the email we're replying to
  const originalEmail = await db.messages.findByMessageId(replyToMessageId);
  const conversation = await db.conversations.get(conversationId);
  const allMessages = await db.messages.findByConversation(conversationId);

  // Build References chain
  const references = allMessages.map(m => m.messageId).join(' ');

  // Build quoted HTML
  const quotedHtml = `
    <p>${replyContent}</p>
    <br>
    <div style="border-left: 2px solid #ccc; padding-left: 10px; color: #666;">
      <p><strong>On ${formatDate(originalEmail.receivedAt)}, ${originalEmail.from} wrote:</strong></p>
      <div>${originalEmail.html}</div>
    </div>
  `;

  const quotedText = `${replyContent}\n\n---\nOn ${formatDate(originalEmail.receivedAt)}, ${originalEmail.from} wrote:\n${originalEmail.text}`;

  const newMessageId = `<reply-${Date.now()}@yourdomain.com>`;

  await resend.emails.send({
    from: 'Your Company <team@yourdomain.com>',
    to: [originalEmail.from],
    subject: `Re: ${conversation.subject.replace(/^Re: /, '')}`,
    html: quotedHtml,
    text: quotedText,
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': replyToMessageId,
      'References': references,
    },
  });

  // Store in database
  await db.messages.create({
    conversationId,
    messageId: newMessageId,
    from: 'team@yourdomain.com',
    to: originalEmail.from,
    subject: `Re: ${conversation.subject}`,
    html: quotedHtml,
    text: quotedText,
    direction: 'sent',
    inReplyTo: replyToMessageId,
    references,
    sentAt: new Date(),
  });
}
```

---

## Webhook Payload Structure

When you receive an email, the webhook payload looks like this:

```json
{
  "type": "email.received",
  "created_at": "2024-03-07T23:41:12.126Z",
  "data": {
    "email_id": "received_abc123",
    "message_id": "<abc123@gmail.com>",
    "from": "client@example.com",
    "to": ["team@yourdomain.com"],
    "subject": "Re: Project Proposal",
    "in_reply_to": "<conv-123@yourdomain.com>",
    "references": "<conv-123@yourdomain.com>",
    "created_at": "2024-03-07T23:41:12.126Z"
  }
}
```

**Key fields for threading:**
- `data.message_id` - The sender's Message-ID (use this in your reply's `In-Reply-To`)
- `data.in_reply_to` - Points to your original email (use to find the conversation)
- `data.references` - Conversation chain from the sender's perspective

---

## Common Mistakes to Avoid

### Mistake 1: Using `email_id` instead of `message_id`

**❌ WRONG:**
```typescript
const messageId = event.data.email_id;  // Wrong! This is Resend's internal ID
```

**✅ CORRECT:**
```typescript
const messageId = event.data.message_id;  // Correct! This is the actual Message-ID header
```

### Mistake 2: Parsing JSON before webhook verification

**❌ WRONG:**
```typescript
const body = await req.json();  // This breaks signature verification!
const event = resend.webhooks.verify({ payload: JSON.stringify(body), ... });
```

**✅ CORRECT:**
```typescript
const payload = await req.text();  // Use raw body
const event = resend.webhooks.verify({ payload, ... });
```

### Mistake 3: Missing threading headers

**❌ WRONG:**
```typescript
await resend.emails.send({
  from: 'team@yourdomain.com',
  to: [recipient],
  subject: 'Re: Original Subject',
  html: '<p>Reply content</p>',
  // Missing headers! Email won't thread properly
});
```

**✅ CORRECT:**
```typescript
await resend.emails.send({
  from: 'team@yourdomain.com',
  to: [recipient],
  subject: 'Re: Original Subject',
  html: '<p>Reply content</p>',
  headers: {
    'Message-ID': '<reply-123@yourdomain.com>',
    'In-Reply-To': '<original-msg@sender.com>',
    'References': '<first-msg@yourdomain.com> <original-msg@sender.com>',
  },
});
```

---

## Troubleshooting

### Emails Not Threading

Checklist:
- ✅ `In-Reply-To` matches the recipient's Message-ID exactly
- ✅ `References` includes ALL previous Message-IDs in order
- ✅ Subject lines match (Gmail also threads by subject)
- ✅ Both emails are in the same folder (not one in spam)

### Can't Find Original Conversation

If `in_reply_to` doesn't match any stored Message-ID:
- The reply might be to an old email not in your system
- The original was sent from a different system
- Treat it as a new conversation

### Custom Message-ID Gets Rewritten

Don't rely on your custom Message-ID. When you receive a reply, the `in_reply_to` field contains the ACTUAL Message-ID that was sent (potentially SES-rewritten). Store this for threading.

---

## Key Takeaways

1. **Always use `data.message_id`** from webhook payloads - it's the authoritative Message-ID
2. **Build the References chain** by appending each new Message-ID
3. **Set In-Reply-To** to the Message-ID you're directly replying to
4. **Store Message-IDs** in your database for building conversation chains
5. **Don't trust your custom Message-ID** - SES may rewrite it
6. **Verify webhooks using raw body text** - parsing JSON breaks signature verification
