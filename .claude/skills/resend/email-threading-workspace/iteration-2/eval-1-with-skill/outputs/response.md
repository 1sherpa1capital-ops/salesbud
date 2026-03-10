# Email Threading with Resend - Complete Implementation Guide

This guide shows how to send an initial email to a client and then reply to it maintaining the conversation thread in Gmail/Outlook using Resend.

## How Email Threading Works

Email clients group related emails using three HTTP headers:

| Header | Purpose |
|--------|---------|
| `Message-ID` | Unique identifier for THIS email |
| `In-Reply-To` | Message-ID of the email being replied to |
| `References` | Space-separated list of ALL Message-IDs in the conversation |

## Complete Code Example

### 1. Project Setup

```bash
npm install resend
```

### 2. Environment Variables

```bash
# .env
RESEND_API_KEY=re_icZV24Db_2Gu2sF9xKqP7gmXX1gDQrr1Z
RESEND_WEBHOOK_SECRET=your_webhook_secret
```

### 3. Send Initial Email

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

/**
 * Send the initial email to start a conversation
 * This sets up the Message-ID that will be used for threading
 */
async function sendInitialEmail(recipient: string, subject: string, content: string) {
  // Generate a unique conversation ID
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

  if (error) {
    console.error('Failed to send email:', error);
    throw error;
  }

  // Store conversation in your database
  await saveConversation({
    id: conversationId,
    recipient,
    subject,
    originalMessageId: messageId,
    resendId: data.id,
    createdAt: new Date(),
  });

  console.log('Initial email sent:', {
    conversationId,
    messageId,
    resendId: data.id,
  });

  return { conversationId, messageId, resendId: data.id };
}

// Example usage
await sendInitialEmail(
  'client@example.com',
  'Project Proposal for Q2',
  '<p>Hi there!</p><p>I wanted to reach out about...</p>'
);
```

### 4. Webhook Handler - Receive Reply

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

/**
 * Webhook endpoint that handles incoming emails
 * Extracts the Message-ID for threading when client replies
 */
export async function POST(req: Request) {
  // 1. Get raw body for signature verification
  const payload = await req.text();

  // 2. Verify webhook signature
  const event = resend.webhooks.verify({
    payload,
    headers: {
      'svix-id': req.headers.get('svix-id'),
      'svix-timestamp': req.headers.get('svix-timestamp'),
      'svix-signature': req.headers.get('svix-signature'),
    },
    secret: process.env.RESEND_WEBHOOK_SECRET,
  });

  // Only handle received emails
  if (event.type !== 'email.received') {
    return new Response('OK', { status: 200 });
  }

  // 3. Extract threading information
  const {
    email_id,        // Resend's internal ID
    message_id,      // Client's Message-ID (use this for threading!)
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

  // 4. Get full email content
  const { data: email } = await resend.emails.receiving.get(email_id);

  // 5. Find the conversation this reply belongs to
  const conversation = await findConversationByMessageId(in_reply_to);

  if (!conversation) {
    console.log('No existing conversation found, treating as new');
    return new Response('OK', { status: 200 });
  }

  // 6. Store the received message
  await saveMessage({
    conversationId: conversation.id,
    messageId,              // Store their Message-ID
    from,
    to: to[0],
    subject,
    html: email.html,
    text: email.text,
    receivedAt: new Date(),
  });

  // 7. Send a threaded reply
  await sendThreadedReply(conversation, message_id, from, subject);

  return new Response('OK', { status: 200 });
}
```

### 5. Send Threaded Reply

```typescript
/**
 * Send a reply that appears in the same Gmail/Outlook thread
 * Uses In-Reply-To and References headers for threading
 */
async function sendThreadedReply(
  conversation: Conversation,
  replyToMessageId: string,    // Client's Message-ID from webhook
  to: string,
  subject: string
) {
  // Get all previous messages in this conversation
  const messages = await getMessagesByConversation(conversation.id);

  // Build References chain (all Message-IDs in order)
  const references = messages.map(m => m.messageId).join(' ');

  // Generate new Message-ID for this reply
  const newMessageId = `<reply-${Date.now()}@syntolabs.xyz>`;

  const { data, error } = await resend.emails.send({
    from: 'Synto Labs <team@syntolabs.xyz>',
    to: [to],
    subject: `Re: ${subject.replace(/^Re: /, '')}`,
    html: `
      <p>Thanks for your reply!</p>
      <p>We'll review your feedback and get back to you shortly.</p>
      <br>
      <p>Best regards,</p>
      <p>The Synto Labs Team</p>
    `,
    text: `Thanks for your reply!\n\nWe'll review your feedback and get back to you shortly.\n\nBest regards,\nThe Synto Labs Team`,
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': replyToMessageId,  // Links to client's email
      'References': references,          // Full conversation chain
    },
  });

  if (error) {
    console.error('Failed to send reply:', error);
    throw error;
  }

  // Store this reply
  await saveMessage({
    conversationId: conversation.id,
    messageId: newMessageId,
    inReplyTo: replyToMessageId,
    to,
    subject: `Re: ${subject}`,
    sentAt: new Date(),
  });

  console.log('Threaded reply sent:', {
    messageId: newMessageId,
    inReplyTo: replyToMessageId,
    resendId: data.id,
  });

  return data.id;
}
```

### 6. Reply with Quoted Text

```typescript
/**
 * Send a reply that includes quoted original message
 * This is the standard email reply format users expect
 */
async function replyWithQuote(
  originalEmail: ReceivedEmail,
  replyContent: string
) {
  const conversation = await findConversationByMessageId(originalEmail.in_reply_to);
  const messages = await getMessagesByConversation(conversation.id);

  // Format the quoted HTML
  const quotedHtml = `
    <p>${replyContent}</p>
    <br>
    <div style="border-left: 2px solid #ccc; padding-left: 10px; color: #666;">
      <p><strong>On ${formatDate(originalEmail.created_at)}, ${originalEmail.from} wrote:</strong></p>
      <div>${originalEmail.html}</div>
    </div>
  `;

  // Format the quoted plain text
  const quotedText = `${replyContent}\n\n---\nOn ${formatDate(originalEmail.created_at)}, ${originalEmail.from} wrote:\n${originalEmail.text}`;

  const newMessageId = `<reply-${Date.now()}@syntolabs.xyz>`;

  await resend.emails.send({
    from: 'Synto Labs <team@syntolabs.xyz>',
    to: [originalEmail.from],
    subject: `Re: ${originalEmail.subject.replace(/^Re: /, '')}`,
    html: quotedHtml,
    text: quotedText,
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': originalEmail.message_id,
      'References': messages.map(m => m.messageId).join(' '),
    },
  });
}
```

### 7. Complete Working Example

```typescript
// complete-example.ts
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

// In-memory storage (replace with your database)
const conversations = new Map();
const messages = new Map();

interface Conversation {
  id: string;
  recipient: string;
  subject: string;
  originalMessageId: string;
  resendId: string;
}

interface Message {
  conversationId: string;
  messageId: string;
  inReplyTo?: string;
  from?: string;
  to?: string;
  subject?: string;
  html?: string;
  text?: string;
  receivedAt?: Date;
  sentAt?: Date;
}

/**
 * STEP 1: Send initial email to client
 */
export async function startConversation(
  recipient: string,
  subject: string,
  htmlContent: string
) {
  const conversationId = `conv-${Date.now()}`;
  const messageId = `<${conversationId}@syntolabs.xyz>`;

  const { data, error } = await resend.emails.send({
    from: 'Synto Labs <team@syntolabs.xyz>',
    to: [recipient],
    subject,
    html: htmlContent,
    headers: {
      'Message-ID': messageId,
      'X-Conversation-ID': conversationId,
    },
  });

  if (error) throw error;

  // Store conversation
  conversations.set(conversationId, {
    id: conversationId,
    recipient,
    subject,
    originalMessageId: messageId,
    resendId: data.id,
  });

  // Store message
  messages.set(messageId, {
    conversationId,
    messageId,
    to: recipient,
    subject,
    sentAt: new Date(),
  });

  console.log('✅ Initial email sent');
  console.log('   Conversation ID:', conversationId);
  console.log('   Message ID:', messageId);
  console.log('   Resend ID:', data.id);

  return { conversationId, messageId };
}

/**
 * STEP 2: Handle incoming reply via webhook
 */
export async function handleIncomingEmail(req: Request) {
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
    return new Response('OK', { status: 200 });
  }

  const { message_id, from, subject, in_reply_to } = event.data;

  console.log('📨 Received reply from:', from);
  console.log('   Their Message-ID:', message_id);
  console.log('   In-Reply-To:', in_reply_to);

  // Find conversation
  const conversation = Array.from(conversations.values()).find(
    c => c.originalMessageId === in_reply_to
  );

  if (!conversation) {
    console.log('⚠️ No conversation found for this reply');
    return new Response('OK', { status: 200 });
  }

  // Store their message
  messages.set(message_id, {
    conversationId: conversation.id,
    messageId: message_id,
    inReplyTo: in_reply_to,
    from,
    subject,
    receivedAt: new Date(),
  });

  // Send threaded reply
  await sendReply(conversation, message_id, from, subject);

  return new Response('OK', { status: 200 });
}

/**
 * STEP 3: Send threaded reply
 */
async function sendReply(
  conversation: Conversation,
  replyToMessageId: string,
  to: string,
  subject: string
) {
  // Get all Message-IDs in conversation
  const conversationMessages = Array.from(messages.values()).filter(
    m => m.conversationId === conversation.id
  );
  const references = conversationMessages.map(m => m.messageId).join(' ');

  // Generate new Message-ID
  const newMessageId = `<reply-${Date.now()}@syntolabs.xyz>`;

  const { data, error } = await resend.emails.send({
    from: 'Synto Labs <team@syntolabs.xyz>',
    to: [to],
    subject: `Re: ${subject.replace(/^Re: /, '')}`,
    html: `
      <p>Hi there,</p>
      <p>Thanks for getting back to us! We've received your message and will respond with more details soon.</p>
      <br>
      <p>Best regards,</p>
      <p><strong>Synto Labs Team</strong></p>
    `,
    text: `Hi there,\n\nThanks for getting back to us! We've received your message and will respond with more details soon.\n\nBest regards,\nSynto Labs Team`,
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': replyToMessageId,
      'References': references,
    },
  });

  if (error) throw error;

  // Store reply
  messages.set(newMessageId, {
    conversationId: conversation.id,
    messageId: newMessageId,
    inReplyTo: replyToMessageId,
    to,
    subject: `Re: ${subject}`,
    sentAt: new Date(),
  });

  console.log('✅ Threaded reply sent');
  console.log('   Message ID:', newMessageId);
  console.log('   In-Reply-To:', replyToMessageId);
  console.log('   References:', references);

  return data.id;
}

// Example usage
async function main() {
  // 1. Send initial email
  const { conversationId, messageId } = await startConversation(
    'client@example.com',
    'Project Proposal',
    '<p>Hello! I wanted to discuss a project with you...</p>'
  );

  // 2. When client replies, webhook calls handleIncomingEmail()
  // 3. Which automatically calls sendReply() to maintain thread
}
```

## Webhook Payload Structure

When a client replies, Resend sends this webhook payload:

```json
{
  "type": "email.received",
  "created_at": "2024-03-07T23:41:12.126Z",
  "data": {
    "email_id": "received_abc123",
    "message_id": "<abc123@gmail.com>",
    "from": "client@example.com",
    "to": ["team@syntolabs.xyz"],
    "subject": "Re: Project Proposal",
    "in_reply_to": "<conv-123@syntolabs.xyz>",
    "headers": {
      "message-id": "<abc123@gmail.com>",
      "in-reply-to": "<conv-123@syntolabs.xyz>",
      "references": "<conv-123@syntolabs.xyz>"
    }
  }
}
```

**Critical:** Use `event.data.message_id` (not `event.data.email_id`) for threading.

## Common Mistakes to Avoid

1. **Using `email_id` instead of `message_id`** - Always use `data.message_id` from the webhook
2. **Missing threading headers** - Must include `Message-ID`, `In-Reply-To`, and `References`
3. **Parsing JSON before verification** - Use `req.text()` not `req.json()` for webhook verification
4. **Not storing Message-IDs** - You need these to build the References chain

## Testing the Flow

1. Send initial email using `startConversation()`
2. Check your email and reply to it
3. Webhook receives the reply with `message_id` and `in_reply_to`
4. Your code sends threaded reply using those values
5. Check Gmail - both emails should appear in the same thread

## Key Takeaways

- **Message-ID**: Unique identifier for each email you send
- **In-Reply-To**: The Message-ID of the email you're responding to
- **References**: Space-separated list of all Message-IDs in the conversation
- Always use the `message_id` from webhook payloads, not your custom one (SES may rewrite it)
