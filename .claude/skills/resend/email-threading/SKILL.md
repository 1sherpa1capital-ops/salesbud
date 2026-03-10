---
name: email-threading
description: Use when maintaining email conversation threads with Resend - sending replies that appear threaded in Gmail/Outlook, using Message-ID, In-Reply-To, and References headers. Essential when the user mentions threading, conversation chains, replying to emails, keeping emails grouped, or email threads. Also use when receiving emails and sending responses that should appear in the same thread.
---

# Email Threading with Resend

## Overview

Email clients (Gmail, Outlook, Apple Mail) group related emails into threads using three HTTP headers:

| Header | Purpose |
|--------|---------|
| `Message-ID` | Unique identifier for THIS email |
| `In-Reply-To` | Message-ID of the email being replied to |
| `References` | Space-separated list of ALL Message-IDs in the conversation |

**The Challenge:** When you send via Resend, Amazon SES may rewrite your custom Message-ID. The solution is to use the `message_id` from webhook payloads when replying.

## Quick Reference

### Sending Initial Email

```javascript
const { data } = await resend.emails.send({
  from: 'team@yourdomain.com',
  to: ['client@example.com'],
  subject: 'Project Proposal',
  html: '<p>Hello!</p>',
  headers: {
    'Message-ID': '<conv-123@yourdomain.com>',  // Set your own
  },
});
```

### Replying to a Received Email

```javascript
// Webhook payload includes message_id
const theirMessageId = event.data.message_id;  // e.g., <abc123@gmail.com>

await resend.emails.send({
  from: 'team@yourdomain.com',
  to: [event.data.from],
  subject: `Re: ${event.data.subject}`,
  html: '<p>Thanks for your reply!</p>',
  headers: {
    'In-Reply-To': theirMessageId,
    'References': `<your-original-msg@yourdomain.com> ${theirMessageId}`,
  },
});
```

## The Complete Threading Workflow

### Step 1: Send Initial Email

Generate a custom Message-ID so you can track the conversation:

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

async function startConversation(recipient: string, subject: string, content: string) {
  const conversationId = `conv-${Date.now()}`;
  const messageId = `<${conversationId}@yourdomain.com>`;

  const { data, error } = await resend.emails.send({
    from: 'Your Company <team@yourdomain.com>',
    to: [recipient],
    subject,
    html: content,
    headers: {
      'Message-ID': messageId,
      'X-Conversation-ID': conversationId,  // For your tracking
    },
  });

  if (error) throw error;

  // Store this for later reference
  await db.conversations.create({
    id: conversationId,
    recipient,
    subject,
    originalMessageId: messageId,
    resendId: data.id,
  });

  return { conversationId, messageId };
}
```

### Step 2: Receive Reply via Webhook

When someone replies, Resend sends a webhook with their Message-ID:

```typescript
// Webhook payload structure
{
  "type": "email.received",
  "created_at": "2024-03-07T23:41:12.126Z",
  "data": {
    "email_id": "received_abc123",     // Resend's internal ID
    "message_id": "<abc123@gmail.com>", // ← THEIR Message-ID (use this!)
    "from": "client@example.com",
    "to": ["team@yourdomain.com"],
    "subject": "Re: Project Proposal",
    "in_reply_to": "<conv-123@yourdomain.com>", // Points to your original
    // ...
  }
}
```

**Critical:** Use `data.message_id` for threading, NOT `data.email_id`.

### Step 3: Send Threaded Reply

Use their Message-ID in your reply:

```typescript
async function sendReply(
  conversationId: string,
  webhookData: EmailReceivedEvent
) {
  // Get conversation history
  const conversation = await db.conversations.get(conversationId);

  // Build References chain (all previous Message-IDs)
  const references = [
    conversation.originalMessageId,     // Your first email
    webhookData.message_id,             // Their reply
  ].join(' ');

  // Generate new Message-ID for this reply
  const newMessageId = `<reply-${Date.now()}@yourdomain.com>`;

  const { data, error } = await resend.emails.send({
    from: 'Your Company <team@yourdomain.com>',
    to: [webhookData.from],
    subject: `Re: ${webhookData.subject.replace(/^Re: /, '')}`,
    html: `<p>Thanks for your reply!</p>`,
    text: `Thanks for your reply!`,
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': webhookData.message_id,  // ← Links to their email
      'References': references,               // ← Full conversation chain
    },
  });

  if (error) throw error;

  // Update conversation
  await db.conversations.update(conversationId, {
    $push: {
      messages: {
        messageId: newMessageId,
        inReplyTo: webhookData.message_id,
        sentAt: new Date(),
      },
    },
  });

  return data.id;
}
```

## Complete Webhook Handler

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(req: Request) {
  // 1. Verify webhook signature
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
    email_id,
    message_id,      // ← Their Message-ID
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

  // 3. Get email body
  const { data: email } = await resend.emails.receiving.get(email_id);

  // 4. Find or create conversation
  let conversation;
  if (in_reply_to) {
    // This is a reply to our email - find the conversation
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
    messageId,           // Store their Message-ID
    from,
    to: to[0],
    subject,
    html: email.html,
    text: email.text,
    receivedAt: new Date(),
  });

  // 6. (Optional) Auto-reply
  await sendThreadedReply(conversation, message_id, from, subject);

  return new Response('OK', { status: 200 });
}

async function sendThreadedReply(
  conversation: Conversation,
  replyToMessageId: string,
  to: string,
  subject: string
) {
  // Get all Message-IDs in this conversation
  const messages = await db.messages.findByConversation(conversation.id);
  const messageIds = messages.map(m => m.messageId);

  const newMessageId = `<reply-${Date.now()}@yourdomain.com>`;

  await resend.emails.send({
    from: conversation.fromAddress,
    to: [to],
    subject: `Re: ${subject.replace(/^Re: /, '')}`,
    html: '<p>Thanks for your email! We\'ll respond shortly.</p>',
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': replyToMessageId,
      'References': messageIds.join(' '),
    },
  });
}
```

## Common Mistakes (Don't Do This!)

### Mistake 1: Using `headers['message-id']` Instead of `event.data.message_id`

**❌ WRONG:**
```typescript
// Don't extract from headers in the payload body
const messageId = payload.headers['message-id'];  // Wrong!
```

**✅ CORRECT:**
```typescript
// Use the message_id field from the webhook event data
const messageId = event.data.message_id;  // Correct!
```

**Why:** Resend webhooks provide `message_id` directly in `event.data`, not nested in headers. The webhook payload structure is:
```json
{
  "type": "email.received",
  "data": {
    "email_id": "...",
    "message_id": "<abc123@gmail.com>",  // <-- Use this!
    "from": "...",
    "subject": "..."
  }
}
```

### Mistake 2: Forgetting Threading Headers

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

### Mistake 3: Parsing JSON Before Verifying Webhook

**❌ WRONG:**
```typescript
// Don't parse JSON before verification
const body = await req.json();  // This breaks signature verification!
const event = resend.webhooks.verify({ payload: JSON.stringify(body), ... });
```

**✅ CORRECT:**
```typescript
// Use raw body text for verification
const payload = await req.text();  // Raw body
const event = resend.webhooks.verify({
  payload,  // Pass raw text, not parsed JSON
  headers: {
    'svix-id': req.headers.get('svix-id'),
    'svix-timestamp': req.headers.get('svix-timestamp'),
    'svix-signature': req.headers.get('svix-signature'),
  },
  secret: process.env.RESEND_WEBHOOK_SECRET,
});
```

**Why:** Signature verification requires the exact bytes of the raw request body. Parsing and re-stringifying JSON changes whitespace/encoding and breaks verification.

### Mistake 4: Not Including All Threading Headers

**❌ WRONG:**
```typescript
// Only including In-Reply-To
headers: {
  'In-Reply-To': originalMessageId,
}
```

**✅ CORRECT:**
```typescript
// Include all three threading headers
headers: {
  'Message-ID': newMessageId,           // Your email's ID
  'In-Reply-To': originalMessageId,     // Parent email ID
  'References': referencesChain,        // Full conversation chain
}
```

## Common Issues

### Issue 1: Custom Message-ID Gets Rewritten

**Problem:** You set a custom Message-ID, but SES rewrites it.

**Solution:** Don't rely on your custom Message-ID for threading. When you receive a reply, the `in_reply_to` field in the webhook will contain the ACTUAL Message-ID that was sent (the SES-generated one). Store this for threading.

```typescript
// When receiving, always use the actual message_id from webhook
const actualMessageIdSent = event.data.in_reply_to;  // This is what they replied to
```

### Issue 2: Emails Not Threading

**Checklist:**
- ✅ `In-Reply-To` matches the recipient's Message-ID exactly
- ✅ `References` includes ALL previous Message-IDs in order
- ✅ Subject lines match (Gmail also threads by subject)
- ✅ Both emails are in the same folder (not one in spam)

### Issue 3: Can't Find Conversation

If `in_reply_to` doesn't match any stored Message-ID:
- The reply might be to an old email not in your system
- The original was sent from a different system
- Treat it as a new conversation

## Working Example: Reply with Quoted Text

```typescript
async function replyWithQuote(
  originalEmail: ReceivedEmail,
  replyContent: string
) {
  // Build quoted HTML
  const quotedHtml = `
    <p>${replyContent}</p>
    <br>
    <div style="border-left: 2px solid #ccc; padding-left: 10px; color: #666;">
      <p><strong>On ${formatDate(originalEmail.created_at)}, ${originalEmail.from} wrote:</strong></p>
      <div>${originalEmail.html}</div>
    </div>
  `;

  const quotedText = `${replyContent}\n\n---\nOn ${formatDate(originalEmail.created_at)}, ${originalEmail.from} wrote:\n${originalEmail.text}`;

  await resend.emails.send({
    from: 'Your Company <team@yourdomain.com>',
    to: [originalEmail.from],
    subject: `Re: ${originalEmail.subject.replace(/^Re: /, '')}`,
    html: quotedHtml,
    text: quotedText,
    headers: {
      'Message-ID': `<reply-${Date.now()}@yourdomain.com>`,
      'In-Reply-To': originalEmail.message_id,
      'References': buildReferencesChain(originalEmail),
    },
  });
}
```

## Testing Threading

1. Send initial email with custom Message-ID
2. Reply to it from Gmail/Outlook
3. Check webhook payload for `message_id` and `in_reply_to`
4. Send threaded reply using those values
5. Verify in email client that both appear in same thread

## Key Takeaways

1. **Always use `data.message_id`** from webhook payloads - it's the authoritative Message-ID
2. **Build the References chain** by appending each new Message-ID
3. **Set In-Reply-To** to the Message-ID you're directly replying to
4. **Store Message-IDs** in your database for building conversation chains
5. **Don't trust your custom Message-ID** - SES may rewrite it
