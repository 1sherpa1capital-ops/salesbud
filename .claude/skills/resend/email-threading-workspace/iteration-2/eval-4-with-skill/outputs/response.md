# Email Quoted Reply Formatting

Complete implementation for sending threaded email replies with properly quoted original message text, similar to Gmail's reply format.

## Overview

When replying to a client's email, you want to include their original message indented below your response. This creates a conversation thread that is easy to follow and matches user expectations from email clients like Gmail and Outlook.

## Complete Implementation

### 1. Basic Quoted Reply Function

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

interface OriginalEmail {
  message_id: string;
  from: string;
  to: string[];
  subject: string;
  html: string;
  text: string;
  created_at: string;
}

/**
 * Format a date for the quote header
 */
function formatQuoteDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

/**
 * Clean HTML content for quoting (remove scripts, etc.)
 */
function cleanHtmlForQuote(html: string): string {
  // Remove script tags and their contents
  let cleaned = html.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
  // Remove style tags and their contents
  cleaned = cleaned.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
  // Remove event handlers
  cleaned = cleaned.replace(/\son\w+="[^"]*"/gi, '');
  return cleaned;
}

/**
 * Build the References header chain from conversation history
 */
function buildReferencesChain(
  originalMessageId: string,
  previousReferences?: string
): string {
  if (previousReferences) {
    return `${previousReferences} ${originalMessageId}`;
  }
  return originalMessageId;
}
```

### 2. HTML Quoted Reply with Gmail-Style Formatting

```typescript
/**
 * Generate Gmail-style quoted HTML content
 */
function generateQuotedHtml(
  replyContent: string,
  originalEmail: OriginalEmail
): string {
  const cleanedOriginalHtml = cleanHtmlForQuote(originalEmail.html);
  const quoteDate = formatQuoteDate(originalEmail.created_at);
  const fromName = originalEmail.from;

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.5; color: #202124;">
  <!-- Your reply -->
  <div style="margin-bottom: 16px;">
    ${replyContent}
  </div>

  <!-- Gmail-style quoted block -->
  <div style="border-left: 1px solid #dadce0; padding-left: 16px; margin: 16px 0;">
    <!-- Quote header -->
    <div style="color: #5f6368; font-size: 14px; margin-bottom: 8px;">
      On ${quoteDate}, ${fromName} wrote:
    </div>

    <!-- Original message (indented) -->
    <div style="color: #5f6368;">
      ${cleanedOriginalHtml}
    </div>
  </div>
</body>
</html>`;
}
```

### 3. Plain Text Quoted Reply

```typescript
/**
 * Generate plain text quoted content
 */
function generateQuotedText(
  replyContent: string,
  originalEmail: OriginalEmail
): string {
  const quoteDate = formatQuoteDate(originalEmail.created_at);
  const fromName = originalEmail.from;

  // Indent the original text with "> " at the start of each line
  const quotedOriginal = originalEmail.text
    .split('\n')
    .map((line) => `> ${line}`)
    .join('\n');

  return `${replyContent}

On ${quoteDate}, ${fromName} wrote:
${quotedOriginal}`;
}
```

### 4. Complete Reply Function with Threading Headers

```typescript
interface ReplyOptions {
  from: string;
  replyContent: string;
  originalEmail: OriginalEmail;
  previousReferences?: string;
  conversationId?: string;
}

/**
 * Send a threaded reply with quoted original message
 */
async function sendQuotedReply(options: ReplyOptions) {
  const {
    from,
    replyContent,
    originalEmail,
    previousReferences,
    conversationId,
  } = options;

  // Generate new Message-ID for this reply
  const newMessageId = `<reply-${Date.now()}@${from.split('@')[1]}>`;

  // Build References chain
  const references = buildReferencesChain(
    originalEmail.message_id,
    previousReferences
  );

  // Generate quoted content
  const htmlContent = generateQuotedHtml(replyContent, originalEmail);
  const textContent = generateQuotedText(replyContent, originalEmail);

  // Clean subject line (remove Re: prefixes to avoid stacking)
  const cleanSubject = originalEmail.subject.replace(/^(Re:\s*)+/i, '');

  const { data, error } = await resend.emails.send({
    from,
    to: [originalEmail.from],
    subject: `Re: ${cleanSubject}`,
    html: htmlContent,
    text: textContent,
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': originalEmail.message_id,
      'References': references,
      'X-Conversation-ID': conversationId || '',
    },
  });

  if (error) {
    throw error;
  }

  return {
    resendId: data.id,
    messageId: newMessageId,
    references,
  };
}
```

### 5. Webhook Handler with Quoted Auto-Reply

```typescript
/**
 * Handle incoming email and send quoted reply
 */
export async function handleIncomingEmail(req: Request) {
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
    message_id,
    from,
    to,
    subject,
    in_reply_to,
  } = event.data;

  // Get full email content
  const { data: email } = await resend.emails.receiving.get(email_id);

  // Construct original email object
  const originalEmail: OriginalEmail = {
    message_id,
    from,
    to,
    subject,
    html: email.html,
    text: email.text,
    created_at: event.created_at,
  };

  // Get conversation history for References chain
  let previousReferences = '';
  if (in_reply_to) {
    const conversation = await db.conversations.findByMessageId(in_reply_to);
    if (conversation) {
      previousReferences = conversation.referencesChain;
    }
  }

  // Send quoted reply
  const result = await sendQuotedReply({
    from: to[0], // Reply from the address that received the email
    replyContent: 'Thank you for your email. We will respond shortly.',
    originalEmail,
    previousReferences,
    conversationId: in_reply_to,
  });

  // Store the reply in database
  await db.messages.create({
    messageId: result.messageId,
    inReplyTo: message_id,
    references: result.references,
    sentAt: new Date(),
  });

  return new Response('OK', { status: 200 });
}
```

### 6. Advanced: Multi-Level Threading with Full History

```typescript
interface ConversationMessage {
  messageId: string;
  from: string;
  to: string;
  subject: string;
  html: string;
  text: string;
  createdAt: string;
}

/**
 * Generate a reply with full conversation history quoted
 * (Useful for long email threads)
 */
function generateFullThreadQuote(
  replyContent: string,
  conversationHistory: ConversationMessage[]
): { html: string; text: string } {
  // Build nested quotes from conversation history (newest first)
  let nestedHtml = '';
  let nestedText = '';

  for (let i = conversationHistory.length - 1; i >= 0; i--) {
    const msg = conversationHistory[i];
    const quoteDate = formatQuoteDate(msg.createdAt);

    // HTML nesting
    const msgHtml = `
      <div style="border-left: 1px solid #dadce0; padding-left: 16px; margin: 8px 0;">
        <div style="color: #5f6368; font-size: 14px; margin-bottom: 8px;">
          On ${quoteDate}, ${msg.from} wrote:
        </div>
        <div style="color: #5f6368;">
          ${cleanHtmlForQuote(msg.html)}
        </div>
        ${i < conversationHistory.length - 1 ? '<div>{{NESTED}}</div>' : ''}
      </div>
    `;

    if (nestedHtml) {
      nestedHtml = msgHtml.replace('{{NESTED}}', nestedHtml);
    } else {
      nestedHtml = msgHtml.replace('<div>{{NESTED}}</div>', '');
    }

    // Text nesting
    const msgText = `On ${quoteDate}, ${msg.from} wrote:\n${msg.text
      .split('\n')
      .map((line) => `> ${line}`)
      .join('\n')}`;

    nestedText = nestedText
      ? msgText + '\n\n' + nestedText.split('\n').map((line) => `> ${line}`).join('\n')
      : msgText;
  }

  const html = `<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.5; color: #202124;">
  <div style="margin-bottom: 16px;">${replyContent}</div>
  ${nestedHtml}
</body>
</html>`;

  const text = `${replyContent}\n\n${nestedText}`;

  return { html, text };
}
```

### 7. Usage Examples

```typescript
// Example 1: Simple quoted reply
const originalEmail: OriginalEmail = {
  message_id: '<abc123@gmail.com>',
  from: 'client@example.com',
  to: ['team@syntolabs.xyz'],
  subject: 'Project Question',
  html: '<p>Can we schedule a call to discuss the timeline?</p>',
  text: 'Can we schedule a call to discuss the timeline?',
  created_at: '2024-03-07T10:30:00Z',
};

await sendQuotedReply({
  from: 'team@syntolabs.xyz',
  replyContent: '<p>Absolutely! How does tomorrow at 2pm work for you?</p>',
  originalEmail,
});

// Example 2: Reply from webhook handler
export async function POST(req: Request) {
  const event = await verifyWebhook(req);

  if (event.type === 'email.received') {
    const { data } = event;

    await sendQuotedReply({
      from: data.to[0],
      replyContent:
        '<p>Thanks for reaching out! We have received your message and will get back to you within 24 hours.</p>',
      originalEmail: {
        message_id: data.message_id,
        from: data.from,
        to: data.to,
        subject: data.subject,
        html: data.html || '',
        text: data.text || '',
        created_at: event.created_at,
      },
    });
  }

  return new Response('OK');
}
```

## Key Points

1. **Always include both HTML and text versions** - Some clients prefer plain text
2. **Clean the original HTML** - Remove scripts and styles for security
3. **Use proper indentation** - Gmail uses left border; plain text uses ">"
4. **Include threading headers** - Message-ID, In-Reply-To, and References
5. **Format dates nicely** - Use locale-aware formatting for readability
6. **Clean subject lines** - Avoid "Re: Re: Re:" by stripping existing prefixes
