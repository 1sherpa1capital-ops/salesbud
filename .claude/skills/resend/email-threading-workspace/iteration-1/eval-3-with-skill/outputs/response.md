# Email Conversation Tracking with Resend

## Overview

To track email conversations with Resend, you need to store Message-IDs in a database and use them to build proper threading headers (`In-Reply-To` and `References`) when sending replies. This ensures emails appear threaded in Gmail, Outlook, and other clients.

---

## Database Schema

### PostgreSQL Schema

```sql
-- Conversations table tracks email threads
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id TEXT UNIQUE,                    -- Your custom conversation ID (e.g., "conv-123")
  recipient_email TEXT NOT NULL,
  sender_email TEXT NOT NULL,
  subject TEXT NOT NULL,
  status TEXT DEFAULT 'active',               -- active, closed, archived
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  last_message_at TIMESTAMP
);

-- Messages table stores individual emails with their Message-IDs
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  message_id TEXT NOT NULL UNIQUE,            -- The actual Message-ID header value
  in_reply_to TEXT,                           -- Message-ID this email replies to
  references TEXT,                            -- Space-separated list of Message-IDs
  direction TEXT NOT NULL,                    -- 'sent' or 'received'
  from_email TEXT NOT NULL,
  to_email TEXT NOT NULL,
  subject TEXT NOT NULL,
  html_body TEXT,
  text_body TEXT,
  resend_id TEXT,                             -- Resend's email ID (for sent emails)
  created_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast conversation lookups
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_message_id ON messages(message_id);
CREATE INDEX idx_messages_in_reply_to ON messages(in_reply_to);
```

### Prisma Schema

```prisma
model Conversation {
  id            String    @id @default(uuid())
  externalId    String?   @unique @map("external_id")
  recipientEmail String   @map("recipient_email")
  senderEmail   String    @map("sender_email")
  subject       String
  status        String    @default("active")
  createdAt     DateTime  @default(now()) @map("created_at")
  updatedAt     DateTime  @updatedAt @map("updated_at")
  lastMessageAt DateTime? @map("last_message_at")

  messages      Message[]

  @@map("conversations")
}

model Message {
  id              String   @id @default(uuid())
  conversationId  String   @map("conversation_id")
  messageId       String   @unique @map("message_id")
  inReplyTo       String?  @map("in_reply_to")
  references      String?
  direction       String   // 'sent' or 'received'
  fromEmail       String   @map("from_email")
  toEmail         String   @map("to_email")
  subject         String
  htmlBody        String?  @map("html_body")
  textBody        String?  @map("text_body")
  resendId        String?  @map("resend_id")
  createdAt       DateTime @default(now()) @map("created_at")

  conversation    Conversation @relation(fields: [conversationId], references: [id], onDelete: Cascade)

  @@index([conversationId])
  @@index([messageId])
  @@index([inReplyTo])
  @@map("messages")
}
```

---

## Implementation

### 1. Send Initial Email and Store Conversation

```typescript
import { Resend } from 'resend';
import { PrismaClient } from '@prisma/client';

const resend = new Resend(process.env.RESEND_API_KEY);
const prisma = new PrismaClient();

async function sendInitialEmail(
  recipient: string,
  subject: string,
  htmlContent: string
) {
  // Generate custom Message-ID for tracking
  const conversationId = `conv-${Date.now()}`;
  const messageId = `<${conversationId}@syntolabs.xyz>`;

  // Send email via Resend
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

  // Create conversation record
  const conversation = await prisma.conversation.create({
    data: {
      externalId: conversationId,
      recipientEmail: recipient,
      senderEmail: 'team@syntolabs.xyz',
      subject,
      lastMessageAt: new Date(),
    },
  });

  // Store sent message with Message-ID
  await prisma.message.create({
    data: {
      conversationId: conversation.id,
      messageId: messageId,
      direction: 'sent',
      fromEmail: 'team@syntolabs.xyz',
      toEmail: recipient,
      subject,
      htmlBody: htmlContent,
      resendId: data.id,
    },
  });

  return { conversation, messageId };
}
```

### 2. Webhook Handler to Receive Replies

```typescript
export async function POST(req: Request) {
  // Verify webhook signature
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

  const {
    email_id,
    message_id,      // Their Message-ID (use this for threading!)
    from,
    to,
    subject,
    in_reply_to,     // Points to your original email
  } = event.data;

  // Find conversation by the email they replied to
  let conversation = null;
  if (in_reply_to) {
    const originalMessage = await prisma.message.findUnique({
      where: { messageId: in_reply_to },
      include: { conversation: true },
    });
    if (originalMessage) {
      conversation = originalMessage.conversation;
    }
  }

  // If no conversation found, create new one
  if (!conversation) {
    conversation = await prisma.conversation.create({
      data: {
        recipientEmail: from,
        senderEmail: to[0],
        subject: subject.replace(/^Re: /, ''),
        lastMessageAt: new Date(),
      },
    });
  }

  // Fetch full email content
  const { data: email } = await resend.emails.receiving.get(email_id);

  // Store received message
  await prisma.message.create({
    data: {
      conversationId: conversation.id,
      messageId: message_id,        // Store their Message-ID
      inReplyTo: in_reply_to,
      direction: 'received',
      fromEmail: from,
      toEmail: to[0],
      subject,
      htmlBody: email.html,
      textBody: email.text,
    },
  });

  // Update conversation timestamp
  await prisma.conversation.update({
    where: { id: conversation.id },
    data: { lastMessageAt: new Date() },
  });

  return new Response('OK', { status: 200 });
}
```

### 3. Build References Chain and Send Threaded Reply

```typescript
async function sendThreadedReply(
  conversationId: string,
  replyContent: string
) {
  // Get conversation with all messages
  const conversation = await prisma.conversation.findUnique({
    where: { id: conversationId },
    include: {
      messages: {
        orderBy: { createdAt: 'asc' },
      },
    },
  });

  if (!conversation) throw new Error('Conversation not found');

  // Get the last received message (what we're replying to)
  const lastReceived = conversation.messages
    .filter(m => m.direction === 'received')
    .pop();

  if (!lastReceived) throw new Error('No received message to reply to');

  // Build References header: ALL Message-IDs in the conversation
  const references = conversation.messages
    .map(m => m.messageId)
    .join(' ');

  // Generate new Message-ID for this reply
  const newMessageId = `<reply-${Date.now()}@syntolabs.xyz>`;

  // Send threaded reply
  const { data, error } = await resend.emails.send({
    from: `Synto Labs <${conversation.senderEmail}>`,
    to: [conversation.recipientEmail],
    subject: `Re: ${conversation.subject}`,
    html: replyContent,
    text: stripHtml(replyContent),
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': lastReceived.messageId,  // Points to their email
      'References': references,               // Full conversation chain
    },
  });

  if (error) throw error;

  // Store sent reply
  await prisma.message.create({
    data: {
      conversationId: conversation.id,
      messageId: newMessageId,
      inReplyTo: lastReceived.messageId,
      references: references,
      direction: 'sent',
      fromEmail: conversation.senderEmail,
      toEmail: conversation.recipientEmail,
      subject: `Re: ${conversation.subject}`,
      htmlBody: replyContent,
      resendId: data.id,
    },
  });

  return data.id;
}
```

### 4. Look Up Conversation by Message-ID

```typescript
async function findConversationByMessageId(messageId: string) {
  // Find by direct Message-ID match
  const message = await prisma.message.findUnique({
    where: { messageId },
    include: { conversation: { include: { messages: true } } },
  });

  if (message) {
    return message.conversation;
  }

  // Or find by in_reply_to reference
  const replyMessage = await prisma.message.findFirst({
    where: { inReplyTo: messageId },
    include: { conversation: { include: { messages: true } } },
  });

  if (replyMessage) {
    return replyMessage.conversation;
  }

  return null;
}
```

---

## Complete Workflow Example

```typescript
// 1. Start a conversation
const { conversation, messageId } = await sendInitialEmail(
  'client@example.com',
  'Project Proposal',
  '<p>Here is our proposal...</p>'
);

// 2. Later, when webhook receives reply, it's automatically stored
// with reference to the original message

// 3. Reply to the conversation (automatically threaded)
await sendThreadedReply(
  conversation.id,
  '<p>Thanks for your feedback! Here are the revisions...</p>'
);

// 4. The reply includes:
//    - Message-ID: <reply-123@syntolabs.xyz>
//    - In-Reply-To: <client-msg-456@gmail.com>
//    - References: <conv-123@syntolabs.xyz> <client-msg-456@gmail.com>
```

---

## Key Points

1. **Store every Message-ID**: Both sent and received emails need their Message-IDs stored
2. **Use `data.message_id` from webhooks**: This is the authoritative Message-ID from the sender
3. **Build References by joining all Message-IDs**: Use `.join(' ')` to create the space-separated list
4. **Set In-Reply-To to the specific message being replied to**: This creates the parent-child link
5. **Query by `in_reply_to` to find conversations**: When receiving a reply, look up the original message

---

## Files

- **Skill**: `/Users/guestr/Desktop/syntolabs/.claude/skills/resend/email-threading/SKILL.md`
- **Evals**: `/Users/guestr/Desktop/syntolabs/.claude/skills/resend/email-threading/evals/evals.json`
