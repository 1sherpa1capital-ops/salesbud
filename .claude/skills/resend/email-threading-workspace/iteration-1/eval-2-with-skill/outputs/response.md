# Next.js Webhook Handler for Threaded Auto-Reply

A complete implementation for receiving emails via Resend webhooks and sending threaded auto-replies that appear in the same conversation thread in Gmail/Outlook.

## File: `app/api/email/route.ts`

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

  // Only handle incoming emails
  if (event.type !== 'email.received') {
    return new Response('OK', { status: 200 });
  }

  // 2. Extract threading info from webhook
  const {
    email_id,
    message_id,      // Their Message-ID (use this for threading!)
    from,
    to,
    subject,
    in_reply_to,     // Points to your original email (if threaded)
  } = event.data;

  console.log('Received email:', {
    from,
    to,
    theirMessageId: message_id,
    inReplyTo: in_reply_to,
  });

  // 3. Send threaded auto-reply
  await sendThreadedAutoReply({
    to: from,
    from: to[0], // Use the address they emailed
    subject,
    replyToMessageId: message_id,
  });

  return new Response('OK', { status: 200 });
}

interface AutoReplyParams {
  to: string;
  from: string;
  subject: string;
  replyToMessageId: string;
}

async function sendThreadedAutoReply({
  to,
  from,
  subject,
  replyToMessageId,
}: AutoReplyParams) {
  // Generate new Message-ID for this reply
  const newMessageId = `<auto-reply-${Date.now()}@mycompany.com>`;

  // Clean up subject line (remove Re: prefix if present)
  const cleanSubject = subject.replace(/^Re: /i, '');

  const { data, error } = await resend.emails.send({
    from: `Support <${from}>`,
    to: [to],
    subject: `Re: ${cleanSubject}`,
    html: `
      <div style="font-family: Arial, sans-serif; max-width: 600px;">
        <p>Thanks for your email, we'll respond within 24 hours.</p>
        <br>
        <p style="color: #666; font-size: 12px;">
          This is an automated response. A member of our team will review your message shortly.
        </p>
      </div>
    `,
    text: `Thanks for your email, we'll respond within 24 hours.\n\nThis is an automated response. A member of our team will review your message shortly.`,
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': replyToMessageId,  // Links to their email
      'References': replyToMessageId,   // Conversation chain
      'X-Auto-Response-Suppress': 'All',
      'Precedence': 'auto_reply',
    },
  });

  if (error) {
    console.error('Failed to send auto-reply:', error);
    throw error;
  }

  console.log('Auto-reply sent:', {
    to,
    messageId: newMessageId,
    inReplyTo: replyToMessageId,
    resendId: data.id,
  });

  return data.id;
}
```

## Environment Variables

Add to your `.env.local`:

```bash
RESEND_API_KEY=re_your_api_key_here
RESEND_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

## How Threading Works

| Header | Purpose |
|--------|---------|
| `Message-ID` | Unique identifier for THIS auto-reply email |
| `In-Reply-To` | Message-ID of the email being replied to (from webhook) |
| `References` | Space-separated list of Message-IDs in the conversation |

## Key Implementation Details

1. **Webhook Verification**: Always verify the webhook signature using `resend.webhooks.verify()` to ensure the request is authentic

2. **Use `event.data.message_id`**: This is the critical field from the webhook payload - it's the sender's Message-ID that you must reference in your reply

3. **Threading Headers**:
   - `In-Reply-To`: Set to the sender's `message_id` from the webhook
   - `References`: Include the sender's `message_id` to build the conversation chain
   - `Message-ID`: Generate a unique ID for your reply

4. **Subject Line**: Use `Re: ${subject}` and strip any existing `Re:` prefix to avoid `Re: Re:`

5. **Auto-Reply Headers**: Added `X-Auto-Response-Suppress` and `Precedence` to indicate this is an automated response

## Testing

1. Set up webhook endpoint in Resend dashboard pointing to `https://yourdomain.com/api/email`
2. Enable "Inbound Email" for your domain in Resend
3. Send an email to `support@mycompany.com`
4. Check that the auto-reply appears in the same thread in Gmail/Outlook

## Resend Webhook Payload Structure

```json
{
  "type": "email.received",
  "created_at": "2024-03-07T23:41:12.126Z",
  "data": {
    "email_id": "received_abc123",
    "message_id": "<abc123@gmail.com>",
    "from": "client@example.com",
    "to": ["support@mycompany.com"],
    "subject": "Help with my order",
    "in_reply_to": null,
    "references": null
  }
}
```

The `message_id` field is what you use for threading - NOT `email_id`.
