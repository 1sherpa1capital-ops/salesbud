# Quoted Reply Formatting for Email Threading

Complete implementation for sending threaded email replies with properly quoted original message text, similar to Gmail's reply format.

## Overview

When replying to a client's email, include their original message indented below your response. This creates a proper conversation thread that email clients (Gmail, Outlook, Apple Mail) can display correctly.

## Implementation

### TypeScript Types

```typescript
interface ReceivedEmail {
  message_id: string;
  from: string;
  to: string[];
  subject: string;
  html?: string;
  text?: string;
  created_at: string;
  in_reply_to?: string;
  references?: string;
}

interface ReplyOptions {
  replyContent: string;
  fromAddress: string;
  fromName?: string;
  domain: string;
}

interface SendEmailResult {
  id: string;
}
```

### Core Quoted Reply Function

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

/**
 * Formats a date for email quoting
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
    timeZoneName: 'short',
  });
}

/**
 * Extracts display name from email address
 * e.g., "John Doe <john@example.com>" -> "John Doe"
 *       "john@example.com" -> "john@example.com"
 */
function extractDisplayName(from: string): string {
  const match = from.match(/^(.*?)\s*<(.+)>$/);
  return match ? match[1].trim() : from;
}

/**
 * Builds HTML for quoted original message with Gmail-style formatting
 */
function buildQuotedHtml(
  replyContent: string,
  originalEmail: ReceivedEmail
): string {
  const sender = extractDisplayName(originalEmail.from);
  const date = formatQuoteDate(originalEmail.created_at);
  const originalHtml = originalEmail.html || `<pre>${originalEmail.text || ''}</pre>`;

  return `
    <div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.5;">
      <div style="margin-bottom: 16px;">
        ${replyContent}
      </div>

      <div style="border-left: 2px solid #ccc; margin: 16px 0; padding-left: 12px; color: #666;">
        <div style="margin-bottom: 8px;">
          <strong>On ${date}, ${sender} wrote:</strong>
        </div>
        <div style="color: #555;">
          ${originalHtml}
        </div>
      </div>
    </div>
  `;
}

/**
 * Builds plain text for quoted original message
 */
function buildQuotedText(
  replyContent: string,
  originalEmail: ReceivedEmail
): string {
  const sender = extractDisplayName(originalEmail.from);
  const date = formatQuoteDate(originalEmail.created_at);
  const originalText = originalEmail.text || '';

  // Indent the original message with "> " at the start of each line
  const indentedOriginal = originalText
    .split('\n')
    .map(line => `> ${line}`)
    .join('\n');

  return `${replyContent}

On ${date}, ${sender} wrote:
${indentedOriginal}`;
}

/**
 * Builds the References header chain for threading
 */
function buildReferencesChain(originalEmail: ReceivedEmail): string {
  const refs: string[] = [];

  // Include original references if present
  if (originalEmail.references) {
    refs.push(...originalEmail.references.split(/\s+/));
  }

  // Include the email we're replying to
  if (originalEmail.message_id) {
    // Avoid duplicates
    if (!refs.includes(originalEmail.message_id)) {
      refs.push(originalEmail.message_id);
    }
  }

  return refs.join(' ');
}

/**
 * Generates a new Message-ID for the reply
 */
function generateMessageId(domain: string): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 10);
  return `<reply-${timestamp}-${random}@${domain}>`;
}

/**
 * Cleans up the subject line by ensuring proper Re: prefix
 */
function formatReplySubject(subject: string): string {
  const cleanSubject = subject.replace(/^(Re:\s*)+/i, '');
  return `Re: ${cleanSubject}`;
}
```

### Main Reply Function

```typescript
/**
 * Sends a threaded email reply with quoted original message
 *
 * @param originalEmail - The email being replied to (from webhook)
 * @param options - Reply options including content and sender info
 * @returns Result from Resend send operation
 */
export async function sendQuotedReply(
  originalEmail: ReceivedEmail,
  options: ReplyOptions
): Promise<SendEmailResult> {
  const {
    replyContent,
    fromAddress,
    fromName = 'Your Company',
    domain,
  } = options;

  // Build quoted content
  const html = buildQuotedHtml(replyContent, originalEmail);
  const text = buildQuotedText(replyContent, originalEmail);

  // Generate threading headers
  const newMessageId = generateMessageId(domain);
  const references = buildReferencesChain(originalEmail);
  const subject = formatReplySubject(originalEmail.subject);

  // Send the reply
  const { data, error } = await resend.emails.send({
    from: `${fromName} <${fromAddress}>`,
    to: [originalEmail.from],
    subject,
    html,
    text,
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': originalEmail.message_id,
      'References': references,
    },
  });

  if (error) {
    throw new Error(`Failed to send reply: ${error.message}`);
  }

  return { id: data.id };
}
```

### Alternative: Inline Reply Style

```typescript
/**
 * Builds HTML for inline replies (replying point-by-point)
 * Original message is shown with inline responses
 */
function buildInlineReplyHtml(
  inlineReplies: Array<{ original: string; reply: string }>,
  originalEmail: ReceivedEmail
): string {
  const sender = extractDisplayName(originalEmail.from);
  const date = formatQuoteDate(originalEmail.created_at);

  const inlineContent = inlineReplies
    .map(({ original, reply }) => `
      <div style="margin-bottom: 16px;">
        <div style="border-left: 3px solid #ddd; padding-left: 12px; color: #666; margin-bottom: 8px;">
          <em>${original}</em>
        </div>
        <div style="padding-left: 12px;">
          ${reply}
        </div>
      </div>
    `)
    .join('');

  return `
    <div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.5;">
      <div style="margin-bottom: 16px;">
        <p>Hi ${sender.split(' ')[0]},</p>
        <p>Please see my responses inline below:</p>
      </div>

      ${inlineContent}

      <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #eee; color: #999; font-size: 12px;">
        <em>Original message from ${sender} on ${date}</em>
      </div>
    </div>
  `;
}
```

### Complete Webhook Handler Example

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);
const DOMAIN = 'syntolabs.xyz';

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

  const email = event.data;

  // 2. Generate AI response or use template
  const replyContent = await generateReply(email.text || email.html || '');

  // 3. Send quoted reply
  try {
    const result = await sendQuotedReply(email, {
      replyContent,
      fromAddress: 'team@syntolabs.xyz',
      fromName: 'Synto Labs',
      domain: DOMAIN,
    });

    console.log('Reply sent:', result.id);
  } catch (error) {
    console.error('Failed to send reply:', error);
    return new Response('Error', { status: 500 });
  }

  return new Response('OK', { status: 200 });
}

// Example reply generator
async function generateReply(emailContent: string): Promise<string> {
  // This would typically call an AI service
  // For demonstration, returning a simple response
  return `
    <p>Thank you for your email!</p>
    <p>I've reviewed your message and will get back to you with a detailed response shortly.</p>
    <p>Best regards,<br>The Team</p>
  `;
}
```

## Usage Examples

### Basic Reply with Quote

```typescript
const originalEmail: ReceivedEmail = {
  message_id: '<abc123@gmail.com>',
  from: 'John Doe <john@example.com>',
  to: ['team@syntolabs.xyz'],
  subject: 'Project Question',
  html: '<p>When can we expect the proposal?</p>',
  text: 'When can we expect the proposal?',
  created_at: '2024-03-07T10:30:00Z',
};

await sendQuotedReply(originalEmail, {
  replyContent: `
    <p>Hi John,</p>
    <p>Thanks for reaching out! We'll have the proposal ready by Friday.</p>
    <p>Best,<br>Ryan</p>
  `,
  fromAddress: 'team@syntolabs.xyz',
  fromName: 'Synto Labs',
  domain: 'syntolabs.xyz',
});
```

### Reply with Multiple Quote Levels

```typescript
/**
 * Handles replies that already have quoted content (nested threading)
 */
function buildNestedQuotedHtml(
  replyContent: string,
  originalEmail: ReceivedEmail,
  previousQuotes?: string[]
): string {
  const sender = extractDisplayName(originalEmail.from);
  const date = formatQuoteDate(originalEmail.created_at);

  let nestedQuotes = '';
  if (previousQuotes && previousQuotes.length > 0) {
    nestedQuotes = previousQuotes
      .map((quote, index) => `
        <div style="margin-left: ${(index + 1) * 12}px;
                    border-left: 2px solid #ddd;
                    padding-left: 8px;
                    color: #888;
                    margin-top: 8px;">
          ${quote}
        </div>
      `)
      .join('');
  }

  return `
    <div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.5;">
      <div style="margin-bottom: 16px;">
        ${replyContent}
      </div>

      <div style="border-left: 2px solid #ccc; margin: 16px 0; padding-left: 12px; color: #666;">
        <div style="margin-bottom: 8px;">
          <strong>On ${date}, ${sender} wrote:</strong>
        </div>
        <div style="color: #555;">
          ${originalEmail.html || `<pre>${originalEmail.text}</pre>`}
        </div>
        ${nestedQuotes}
      </div>
    </div>
  `;
}
```

## Output Format

### HTML Output Example

```html
<div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.5;">
  <div style="margin-bottom: 16px;">
    <p>Hi John,</p>
    <p>Thanks for reaching out! We'll have the proposal ready by Friday.</p>
    <p>Best,<br>Ryan</p>
  </div>

  <div style="border-left: 2px solid #ccc; margin: 16px 0; padding-left: 12px; color: #666;">
    <div style="margin-bottom: 8px;">
      <strong>On Thu, Mar 7, 2024 at 10:30 AM EST, John Doe wrote:</strong>
    </div>
    <div style="color: #555;">
      <p>When can we expect the proposal?</p>
    </div>
  </div>
</div>
```

### Text Output Example

```
Hi John,

Thanks for reaching out! We'll have the proposal ready by Friday.

Best,
Ryan

On Thu, Mar 7, 2024 at 10:30 AM EST, John Doe wrote:
> When can we expect the proposal?
```

## Key Points

1. **Always include both HTML and text versions** - Some email clients prefer plain text
2. **Use left border styling** - The grey left border is the standard visual cue for quoted content
3. **Include timestamp and sender** - Essential for email threading context
4. **Indent with `> ` in text version** - Standard convention for quoted text
5. **Maintain threading headers** - Message-ID, In-Reply-To, and References are critical
6. **Handle nested quotes** - Previous replies may already contain quoted content
