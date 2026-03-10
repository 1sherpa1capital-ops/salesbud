# Email Threading with Resend - Complete Guide

This guide shows how to send an initial email to a client and then reply to it maintaining the same thread in Gmail/Outlook using Resend.

## How Email Threading Works

Email clients group related emails using three key headers:

| Header | Purpose |
|--------|---------|
| `Message-ID` | Unique identifier for THIS email |
| `In-Reply-To` | Message-ID of the email being replied to |
| `References` | Space-separated list of ALL Message-IDs in the conversation |

## Step 1: Send Initial Email

When sending the first email, set a custom Message-ID so you can track the conversation:

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

async function startConversation(recipient: string, subject: string, content: string) {
  const conversationId = `conv-${Date.now()}`;
  const messageId = `<${conversationId}@syntolabs.xyz>`;

  const { data, error } = await resend.emails.send({
    from: 'Synto Labs <team@syntolabs.xyz>',
    to: [recipient],
    subject,
    html: content,
    headers: {
      'Message-ID': messageId,
      'X-Conversation-ID': conversationId,
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

## Step 2: Receive Reply via Webhook

When the client replies, Resend sends a webhook with their Message-ID:

```typescript
// Webhook payload structure
{
  "type": "email.received",
  "created_at": "2024-03-07T23:41:12.126Z",
  "data": {
    "email_id": "received_abc123",
    "message_id": "<abc123@gmail.com>",  // THEIR Message-ID (use this!)
    "from": "client@example.com",
    "to": ["team@syntolabs.xyz"],
    "subject": "Re: Project Proposal",
    "in_reply_to": "<conv-123@syntolabs.xyz>", // Points to your original
  }
}
```

**Critical:** Use `data.message_id` for threading, NOT `data.email_id`.

## Step 3: Send Threaded Reply

Use their Message-ID in your reply headers:

```typescript
async function sendReply(
  conversationId: string,
  webhookData: EmailReceivedEvent
) {
  // Get conversation history
  const conversation = await db.conversations.get(conversationId);

  // Build References chain (all previous Message-IDs)
  const references = [
    conversation.originalMessageId,
    webhookData.message_id,
  ].join(' ');

  // Generate new Message-ID for this reply
  const newMessageId = `<reply-${Date.now()}@syntolabs.xyz>`;

  const { data, error } = await resend.emails.send({
    from: 'Synto Labs <team@syntolabs.xyz>',
    to: [webhookData.from],
    subject: `Re: ${webhookData.subject.replace(/^Re: /, '')}`,
    html: `<p>Thanks for your reply!</p>`,
    text: `Thanks for your reply!`,
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': webhookData.message_id,
      'References': references,
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

## Complete Working Example

Here is a complete webhook handler that receives emails and sends threaded replies:

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
    message_id,      // Their Message-ID
    from,
    to,
    subject,
    in_reply_to,     // Points to your original email
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
    conversation = await db.conversations.findByOriginalMessageId(in_reply_to);
  }

  if (!conversation) {
    conversation = await db.conversations.create({
      recipient: from,
      subject,
      startedBy: 'external',
    });
  }

  // 5. Store received message
  await db.messages.create({
    conversationId: conversation.id,
    messageId,
    from,
    to: to[0],
    subject,
    html: email.html,
    text: email.text,
    receivedAt: new Date(),
  });

  // 6. Send threaded reply
  await sendThreadedReply(conversation, message_id, from, subject);

  return new Response('OK', { status: 200 });
}

async function sendThreadedReply(
  conversation: Conversation,
  replyToMessageId: string,
  to: string,
  subject: string
) {
  const messages = await db.messages.findByConversation(conversation.id);
  const messageIds = messages.map(m => m.messageId);

  const newMessageId = `<reply-${Date.now()}@syntolabs.xyz>`;

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

## Key Points

1. **Always use `data.message_id`** from webhook payloads - it's the authoritative Message-ID
2. **Set `In-Reply-To`** to the Message-ID you're directly replying to
3. **Build the `References` chain** by including all previous Message-IDs
4. **Store Message-IDs** in your database for building conversation chains
5. **Subject lines matter** - Gmail also threads by matching subjects

## Common Issues

**Custom Message-ID gets rewritten:** Amazon SES may rewrite your custom Message-ID. When receiving replies, use `in_reply_to` from the webhook to find your original email.

**Emails not threading:** Check that:
- `In-Reply-To` matches exactly
- `References` includes all previous Message-IDs
- Subject lines match (without the "Re: " prefix)
