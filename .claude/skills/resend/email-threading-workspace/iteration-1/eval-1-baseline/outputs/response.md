# Email Threading with Resend - Complete Guide

This guide demonstrates how to send an initial email and maintain thread continuity when replying using the Resend API.

## Overview

Email threading in Gmail (and other clients) relies on specific email headers. To maintain a thread, you need to set the `In-Reply-To` and `References` headers correctly.

## Key Concepts

### Email Headers for Threading

1. **Message-ID**: A unique identifier for each email (format: `<unique-id@domain.com>`)
2. **In-Reply-To**: The Message-ID of the email you're replying to
3. **References**: A chain of Message-IDs from the entire thread history

### How Threading Works

- Gmail groups emails into a thread when they share the same subject (with "Re:" prefix) AND have matching `In-Reply-To`/`References` headers
- The `References` header should contain all Message-IDs in the thread, space-separated
- The `In-Reply-To` header should point to the immediate parent message

## Implementation

### Step 1: Send Initial Email

```javascript
// send-initial-email.js
import { Resend } from 'resend';

const resend = new Resend('re_YOUR_API_KEY');

// Generate a unique Message-ID for tracking
const generateMessageId = () => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 10);
  return `<${timestamp}.${random}@syntolabs.xyz>`;
};

async function sendInitialEmail() {
  const messageId = generateMessageId();

  try {
    const { data, error } = await resend.emails.send({
      from: 'team@syntolabs.xyz',
      to: 'client@example.com',
      subject: 'Project Proposal Discussion',
      html: `
        <h1>Hello!</h1>
        <p>I'd like to discuss our project proposal with you.</p>
        <p>Let me know when you have a moment to chat.</p>
        <p>Best regards,<br>Team at Synto Labs</p>
      `,
      text: `Hello!\n\nI'd like to discuss our project proposal with you.\n\nLet me know when you have a moment to chat.\n\nBest regards,\nTeam at Synto Labs`,
      // Custom headers must be set via the headers property
      headers: {
        'Message-ID': messageId,
        'X-Custom-Tracking': 'proposal-outreach-001'
      }
    });

    if (error) {
      console.error('Error sending email:', error);
      return;
    }

    // Store the Message-ID and Resend ID for future reference
    const emailRecord = {
      resendId: data.id,
      messageId: messageId,
      to: 'client@example.com',
      subject: 'Project Proposal Discussion',
      sentAt: new Date().toISOString()
    };

    // Save to your database or storage
    console.log('Email sent successfully:', emailRecord);
    return emailRecord;

  } catch (err) {
    console.error('Exception:', err);
  }
}

sendInitialEmail();
```

### Step 2: Handle Incoming Reply (Webhook)

When the client replies, you need to capture their email's Message-ID to use in your response.

```javascript
// webhook-handler.js
import express from 'express';
import { Resend } from 'resend';

const app = express();
app.use(express.json());

const resend = new Resend('re_YOUR_API_KEY');

// Store for email threads (use a database in production)
const emailThreads = new Map();

// Webhook endpoint to receive email events
app.post('/webhook/email-event', async (req, res) => {
  const event = req.body;

  // Handle inbound email (requires Resend inbound routing setup)
  if (event.type === 'email.received') {
    const {
      from,
      to,
      subject,
      text,
      html,
      headers
    } = event.data;

    // Extract threading headers from the incoming email
    const incomingMessageId = headers['message-id'];
    const inReplyTo = headers['in-reply-to'];
    const references = headers['references'] || '';

    // Find the original email thread
    const threadId = findThreadId(inReplyTo, references);

    if (threadId) {
      // Store the incoming message details
      const thread = emailThreads.get(threadId);
      thread.messages.push({
        messageId: incomingMessageId,
        from,
        subject,
        content: text,
        receivedAt: new Date().toISOString()
      });

      // Update the thread's references chain
      thread.references = references
        ? `${references} ${incomingMessageId}`
        : incomingMessageId;

      console.log(`Received reply in thread ${threadId}:`, {
        from,
        subject,
        incomingMessageId
      });
    }
  }

  res.status(200).send('OK');
});

function findThreadId(inReplyTo, references) {
  // Search through stored threads to find matching Message-ID
  for (const [threadId, thread] of emailThreads.entries()) {
    const allMessageIds = thread.messages.map(m => m.messageId);
    if (inReplyTo && allMessageIds.includes(inReplyTo)) {
      return threadId;
    }
    if (references) {
      const refIds = references.split(' ').map(r => r.trim());
      if (refIds.some(ref => allMessageIds.includes(ref))) {
        return threadId;
      }
    }
  }
  return null;
}

app.listen(3000, () => {
  console.log('Webhook server running on port 3000');
});
```

### Step 3: Send Reply Maintaining Thread

```javascript
// send-reply.js
import { Resend } from 'resend';

const resend = new Resend('re_YOUR_API_KEY');

async function sendReply(originalEmailRecord, replyContent) {
  // Generate new Message-ID for this reply
  const newMessageId = `<${Date.now()}.${Math.random().toString(36).substring(2)}@syntolabs.xyz>`;

  // Build References header: original Message-ID + any previous references
  const references = originalEmailRecord.references
    ? `${originalEmailRecord.references} ${originalEmailRecord.lastMessageId}`
    : originalEmailRecord.messageId;

  try {
    const { data, error } = await resend.emails.send({
      from: 'team@syntolabs.xyz',
      to: originalEmailRecord.to,
      // Keep the same subject (Gmail will add "Re:" automatically or you can include it)
      subject: `Re: ${originalEmailRecord.subject.replace(/^Re: /, '')}`,
      html: `
        <p>${replyContent}</p>
        <br>
        <p>Best regards,<br>Team at Synto Labs</p>
      `,
      text: `${replyContent}\n\nBest regards,\nTeam at Synto Labs`,
      headers: {
        'Message-ID': newMessageId,
        'In-Reply-To': originalEmailRecord.lastMessageId || originalEmailRecord.messageId,
        'References': references
      }
    });

    if (error) {
      console.error('Error sending reply:', error);
      return;
    }

    // Update the thread record
    const updatedRecord = {
      ...originalEmailRecord,
      messages: [
        ...originalEmailRecord.messages,
        {
          resendId: data.id,
          messageId: newMessageId,
          type: 'sent',
          content: replyContent,
          sentAt: new Date().toISOString()
        }
      ],
      lastMessageId: newMessageId,
      references: references
    };

    console.log('Reply sent successfully:', updatedRecord);
    return updatedRecord;

  } catch (err) {
    console.error('Exception:', err);
  }
}

// Example usage
const originalEmail = {
  resendId: 'email_123',
  messageId: '<1709832000000.abc123@syntolabs.xyz>',
  lastMessageId: '<client-reply-456@example.com>', // From client's reply
  references: '<1709832000000.abc123@syntolabs.xyz>',
  to: 'client@example.com',
  subject: 'Project Proposal Discussion',
  messages: []
};

sendReply(
  originalEmail,
  'Thank you for your response! I\'d be happy to schedule a call next Tuesday at 2pm. Does that work for you?'
);
```

## Complete Working Example

```javascript
// complete-email-thread-example.js
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

class EmailThreadManager {
  constructor() {
    this.threads = new Map();
  }

  generateMessageId() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 10);
    return `<${timestamp}.${random}@syntolabs.xyz>`;
  }

  async sendInitialEmail({ to, subject, html, text }) {
    const messageId = this.generateMessageId();
    const threadId = `thread_${Date.now()}`;

    const { data, error } = await resend.emails.send({
      from: 'team@syntolabs.xyz',
      to,
      subject,
      html,
      text,
      headers: {
        'Message-ID': messageId
      }
    });

    if (error) throw error;

    const thread = {
      id: threadId,
      participants: [to],
      subject,
      messages: [{
        resendId: data.id,
        messageId,
        direction: 'outbound',
        timestamp: new Date().toISOString()
      }],
      references: messageId
    };

    this.threads.set(threadId, thread);
    return { threadId, messageId, resendId: data.id };
  }

  async sendReply({ threadId, content, inReplyToMessageId }) {
    const thread = this.threads.get(threadId);
    if (!thread) throw new Error('Thread not found');

    const newMessageId = this.generateMessageId();

    const { data, error } = await resend.emails.send({
      from: 'team@syntolabs.xyz',
      to: thread.participants[0],
      subject: `Re: ${thread.subject}`,
      html: `<p>${content}</p>`,
      text: content,
      headers: {
        'Message-ID': newMessageId,
        'In-Reply-To': inReplyToMessageId,
        'References': thread.references
      }
    });

    if (error) throw error;

    // Update thread
    thread.messages.push({
      resendId: data.id,
      messageId: newMessageId,
      direction: 'outbound',
      timestamp: new Date().toISOString()
    });
    thread.references = `${thread.references} ${newMessageId}`;

    return { messageId: newMessageId, resendId: data.id };
  }

  recordInboundEmail({ threadId, messageId, from, subject, content }) {
    const thread = this.threads.get(threadId);
    if (!thread) return;

    thread.messages.push({
      messageId,
      from,
      direction: 'inbound',
      content,
      timestamp: new Date().toISOString()
    });

    // Update references chain
    thread.references = `${thread.references} ${messageId}`;
  }
}

// Usage example
const manager = new EmailThreadManager();

async function demo() {
  // Step 1: Send initial email
  console.log('Sending initial email...');
  const initial = await manager.sendInitialEmail({
    to: 'client@example.com',
    subject: 'Project Kickoff',
    html: '<h1>Welcome!</h1><p>Excited to work with you.</p>',
    text: 'Welcome! Excited to work with you.'
  });
  console.log('Initial email sent:', initial);

  // Step 2: Simulate receiving a reply (in production, this comes from webhook)
  const clientReplyMessageId = '<client-reply-123@example.com>';
  manager.recordInboundEmail({
    threadId: initial.threadId,
    messageId: clientReplyMessageId,
    from: 'client@example.com',
    subject: 'Re: Project Kickoff',
    content: 'Thanks! Looking forward to it.'
  });

  // Step 3: Send reply maintaining thread
  console.log('Sending reply...');
  const reply = await manager.sendReply({
    threadId: initial.threadId,
    content: 'Great! I\'ll send over the contract shortly.',
    inReplyToMessageId: clientReplyMessageId
  });
  console.log('Reply sent:', reply);
}

demo().catch(console.error);
```

## Important Notes

### Resend Limitations

1. **Inbound Email**: Resend is primarily for sending. To receive replies, you need:
   - Resend's inbound routing feature (beta)
   - Or a separate email service (like AWS SES, SendGrid Inbound Parse)
   - Or an email forwarding service

2. **Custom Headers**: Resend supports custom headers via the `headers` property in the send options.

### Best Practices

1. **Always store Message-IDs**: When you send an email, save the Message-ID you generated
2. **Track the full thread**: Maintain a `references` chain that includes all Message-IDs
3. **Use consistent From address**: Threading works best when the from address remains consistent
4. **Subject line**: Keep the subject consistent (Gmail strips "Re:" prefixes when matching)

### Testing

To test email threading:
1. Send an email using the code above
2. Check the email headers in Gmail (three dots menu > "Show original")
3. Verify the Message-ID header is present
4. Reply to the email and check that Gmail groups them in a thread

## Resources

- [Resend API Documentation](https://resend.com/docs/api-reference/emails/send-email)
- [RFC 5322 - Email Headers](https://tools.ietf.org/html/rfc5322)
- [Gmail Threading Behavior](https://support.google.com/mail/answer/5900)
