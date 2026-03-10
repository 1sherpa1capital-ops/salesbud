# Email Threading with Resend - Complete Guide

This guide shows how to send an initial email to a client and then reply to their response while maintaining the same Gmail/Outlook thread using Resend.

## How Email Threading Works

Email clients group related emails into threads using three key headers:

| Header | Purpose |
|--------|---------|
| `Message-ID` | Unique identifier for THIS email |
| `In-Reply-To` | Message-ID of the email being replied to |
| `References` | Space-separated list of ALL Message-IDs in the conversation |

## Prerequisites

```bash
npm install resend
```

```env
RESEND_API_KEY=re_icZV24Db_2Gu2sF9xKqP7gmXX1gDQrr1Z
RESEND_WEBHOOK_SECRET=your_webhook_secret_here
```

## Step 1: Send Initial Email with Message-ID

When sending the first email, set a custom `Message-ID` header so you can track the conversation:

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

async function sendInitialEmail(recipient: string, subject: string, content: string) {
  // Generate a unique conversation ID and Message-ID
  const conversationId = `conv-${Date.now()}`;
  const messageId = `<${conversationId}@syntolabs.xyz>`;

  const { data, error } = await resend.emails.send({
    from: 'Synto Labs <team@syntolabs.xyz>',
    to: [recipient],
    subject,
    html: content,
    headers: {
      'Message-ID': messageId,
      'X-Conversation-ID': conversationId,  // For your internal tracking
    },
  });

  if (error) {
    console.error('Failed to send email:', error);
    throw error;
  }

  // Store this information for later reference
  console.log('Email sent:', {
    conversationId,
    messageId,
    resendId: data.id,
  });

  // Save to your database
  await saveConversation({
    id: conversationId,
    recipient,
    subject,
    originalMessageId: messageId,
    resendId: data.id,
    createdAt: new Date(),
  });

  return { conversationId, messageId, resendId: data.id };
}

// Example usage
await sendInitialEmail(
  'client@example.com',
  'Project Proposal',
  '<p>Hi there! I wanted to discuss the project proposal with you.</p>'
);
```

## Step 2: Handle Reply via Webhook

When the client replies, Resend sends a webhook with their `message_id`. You need to extract this to send a properly threaded response:

```typescript
// Webhook payload structure when email is received
{
  "type": "email.received",
  "created_at": "2024-03-07T23:41:12.126Z",
  "data": {
    "email_id": "received_abc123",
    "message_id": "<abc123@gmail.com>",  // ← THEIR Message-ID (use this!)
    "from": "client@example.com",
    "to": ["team@syntolabs.xyz"],
    "subject": "Re: Project Proposal",
    "in_reply_to": "<conv-123@syntolabs.xyz>", // Points to your original email
    // ... other fields
  }
}
```

**Critical:** Use `data.message_id` for threading, NOT `data.email_id`.

## Step 3: Send Threaded Reply

Use their `message_id` in your reply headers to make it appear in the same thread:

```typescript
async function sendThreadedReply(
  conversationId: string,
  webhookData: {
    message_id: string;
    from: string;
    subject: string;
  },
  replyContent: string
) {
  // Get the conversation history
  const conversation = await getConversation(conversationId);

  // Build the References chain (all previous Message-IDs)
  const references = [
    conversation.originalMessageId,  // Your first email
    webhookData.message_id,          // Their reply
  ].join(' ');

  // Generate a new Message-ID for this reply
  const newMessageId = `<reply-${Date.now()}@syntolabs.xyz>`;

  const { data, error } = await resend.emails.send({
    from: 'Synto Labs <team@syntolabs.xyz>',
    to: [webhookData.from],
    subject: `Re: ${webhookData.subject.replace(/^Re: /, '')}`,
    html: `<p>${replyContent}</p>`,
    text: replyContent,
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': webhookData.message_id,  // ← Links to their email
      'References': references,               // ← Full conversation chain
    },
  });

  if (error) {
    console.error('Failed to send reply:', error);
    throw error;
  }

  // Update conversation with this reply
  await addMessageToConversation(conversationId, {
    messageId: newMessageId,
    inReplyTo: webhookData.message_id,
    sentAt: new Date(),
  });

  console.log('Threaded reply sent:', data.id);
  return data.id;
}

// Example usage
await sendThreadedReply(
  'conv-1709856000000',
  {
    message_id: '<abc123@gmail.com>',
    from: 'client@example.com',
    subject: 'Re: Project Proposal',
  },
  'Thanks for your reply! Let me know if you have any questions about the proposal.'
);
```

## Complete Webhook Handler Example

Here's a complete Next.js API route that receives emails and sends threaded auto-replies:

```typescript
// app/api/webhooks/resend/route.ts
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(req: Request) {
  try {
    // 1. Verify webhook signature (CRITICAL for security)
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

    // Only process received emails
    if (event.type !== 'email.received') {
      return new Response('OK', { status: 200 });
    }

    // 2. Extract threading information from webhook
    const {
      email_id,
      message_id,      // ← Their Message-ID (use for threading)
      from,
      to,
      subject,
      in_reply_to,     // ← Points to your original email
    } = event.data;

    console.log('Received reply:', {
      from,
      theirMessageId: message_id,
      inReplyTo: in_reply_to,
    });

    // 3. Get full email content (optional)
    const { data: email } = await resend.emails.receiving.get(email_id);

    // 4. Find or create conversation
    let conversation = await findConversationByMessageId(in_reply_to);

    if (!conversation) {
      // New conversation started by external sender
      conversation = await createConversation({
        recipient: from,
        subject,
        startedBy: 'external',
      });
    }

    // 5. Store received message
    await saveMessage({
      conversationId: conversation.id,
      messageId: message_id,
      from,
      to: to[0],
      subject,
      html: email.html,
      text: email.text,
      receivedAt: new Date(),
    });

    // 6. Send threaded auto-reply
    await sendAutoReply(conversation, message_id, from, subject);

    return new Response('OK', { status: 200 });
  } catch (error) {
    console.error('Webhook error:', error);
    return new Response('Error', { status: 500 });
  }
}

async function sendAutoReply(
  conversation: any,
  replyToMessageId: string,
  to: string,
  subject: string
) {
  // Get all Message-IDs in this conversation for References header
  const messages = await getMessagesByConversation(conversation.id);
  const messageIds = messages.map((m: any) => m.messageId);

  // Generate new Message-ID for this reply
  const newMessageId = `<reply-${Date.now()}@syntolabs.xyz>`;

  const { data, error } = await resend.emails.send({
    from: 'Synto Labs <team@syntolabs.xyz>',
    to: [to],
    subject: `Re: ${subject.replace(/^Re: /, '')}`,
    html: `
      <p>Thanks for your email! We've received your message and will respond within 24 hours.</p>
      <br>
      <p>Best regards,<br>Synto Labs Team</p>
    `,
    text: `Thanks for your email! We've received your message and will respond within 24 hours.

Best regards,
Synto Labs Team`,
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': replyToMessageId,
      'References': messageIds.join(' '),
    },
  });

  if (error) {
    console.error('Failed to send auto-reply:', error);
    throw error;
  }

  console.log('Auto-reply sent:', data.id);
  return data.id;
}
```

## Common Mistakes to Avoid

### Mistake 1: Using Wrong Message-ID

**❌ WRONG:**
```typescript
const messageId = payload.headers['message-id'];  // Wrong!
```

**✅ CORRECT:**
```typescript
const messageId = event.data.message_id;  // Correct!
```

### Mistake 2: Missing Threading Headers

**❌ WRONG:**
```typescript
await resend.emails.send({
  from: 'team@syntolabs.xyz',
  to: [recipient],
  subject: 'Re: Original Subject',
  html: '<p>Reply content</p>',
  // Missing headers! Email won't thread properly
});
```

**✅ CORRECT:**
```typescript
await resend.emails.send({
  from: 'team@syntolabs.xyz',
  to: [recipient],
  subject: 'Re: Original Subject',
  html: '<p>Reply content</p>',
  headers: {
    'Message-ID': '<reply-123@syntolabs.xyz>',
    'In-Reply-To': '<original-msg@sender.com>',
    'References': '<first-msg@syntolabs.xyz> <original-msg@sender.com>',
  },
});
```

### Mistake 3: Parsing JSON Before Verifying Webhook

**❌ WRONG:**
```typescript
const body = await req.json();  // This breaks signature verification!
const event = resend.webhooks.verify({ payload: JSON.stringify(body), ... });
```

**✅ CORRECT:**
```typescript
const payload = await req.text();  // Raw body
const event = resend.webhooks.verify({
  payload,
  headers: { ... },
  secret: process.env.RESEND_WEBHOOK_SECRET,
});
```

## Key Takeaways

1. **Always use `data.message_id`** from webhook payloads - it's the authoritative Message-ID
2. **Build the References chain** by appending each new Message-ID
3. **Set In-Reply-To** to the Message-ID you're directly replying to
4. **Store Message-IDs** in your database for building conversation chains
5. **Don't trust your custom Message-ID** - Amazon SES may rewrite it

## Testing Your Implementation

1. Send initial email with custom Message-ID
2. Reply to it from Gmail/Outlook
3. Check webhook payload for `message_id` and `in_reply_to`
4. Send threaded reply using those values
5. Verify in email client that both appear in same thread

## Resources

- [Resend Documentation](https://resend.com/docs)
- [Email Threading RFC 5322](https://tools.ietf.org/html/rfc5322#section-3.6.4)
- Synto Labs domain: `syntolabs.xyz` (verified)
- Available sending addresses: `team@syntolabs.xyz`, `rhigden@syntolabs.xyz`
