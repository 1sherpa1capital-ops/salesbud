# Next.js Webhook Handler for Resend Email Auto-Reply with Threading

## Overview

This implementation creates a Next.js API route that receives emails via Resend webhooks and sends threaded auto-replies. The key to email threading is preserving the `Message-ID`, `In-Reply-To`, and `References` headers.

## How Email Threading Works

For emails to appear threaded in clients (Gmail, Outlook, etc.), the auto-reply must include:

1. **`In-Reply-To`**: The `Message-ID` of the original email
2. **`References`**: A chain of `Message-ID`s from the conversation thread
3. **Same `Subject`**: With the `Re: ` prefix (optional but standard)

## Implementation

### 1. Webhook Handler - `/app/api/email-webhook/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

// Types for Resend webhook payload
interface ResendEmailWebhookPayload {
  type: 'email.sent' | 'email.delivered' | 'email.opened' | 'email.clicked' | 'email.bounced' | 'email.complained';
  data: {
    from: string;
    to: string[];
    subject: string;
    message_id: string;
    // Additional fields may be present depending on your Resend webhook configuration
  };
}

// Type for the inbound email webhook (Resend Inbound)
interface ResendInboundPayload {
  from: string;
  to: string[];
  subject: string;
  text: string;
  html?: string;
  headers: {
    'message-id': string;
    'in-reply-to'?: string;
    'references'?: string;
    [key: string]: string | undefined;
  };
}

export async function POST(request: NextRequest) {
  try {
    // Verify webhook signature (recommended for production)
    const signature = request.headers.get('resend-signature');
    if (!verifyWebhookSignature(await request.text(), signature)) {
      return NextResponse.json({ error: 'Invalid signature' }, { status: 401 });
    }

    // Parse the webhook payload
    const payload: ResendInboundPayload = await request.json();

    // Extract key information
    const {
      from,
      to,
      subject,
      headers
    } = payload;

    const originalMessageId = headers['message-id'];
    const originalReferences = headers['references'] || '';

    // Build the References header for threading
    // Include the original message ID in the chain
    const newReferences = originalReferences
      ? `${originalReferences} ${originalMessageId}`
      : originalMessageId;

    // Send auto-reply with threading headers
    await resend.emails.send({
      from: 'support@mycompany.com',
      to: [from],
      subject: `Re: ${subject.replace(/^Re: /i, '')}`, // Avoid double "Re:"
      text: `Thanks for your email, we'll respond within 24 hours.\n\n---\nOriginal Message:\nFrom: ${from}\nSubject: ${subject}`,
      html: `<p>Thanks for your email, we'll respond within 24 hours.</p>
             <hr style="border: none; border-top: 1px solid #ccc; margin: 20px 0;" />
             <p style="color: #666; font-size: 12px;">
               <strong>Original Message:</strong><br/>
               <strong>From:</strong> ${from}<br/>
               <strong>Subject:</strong> ${subject}
             </p>`,
      headers: {
        'In-Reply-To': originalMessageId,
        'References': newReferences,
        'X-Auto-Response-Suppress': 'OOF, AutoReply', // Prevent auto-reply loops
        'Precedence': 'auto_reply',
      },
    });

    // Log for monitoring
    console.log(`Auto-reply sent to ${from} for message ${originalMessageId}`);

    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    console.error('Webhook error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// Webhook signature verification
function verifyWebhookSignature(payload: string, signature: string | null): boolean {
  // In production, implement proper signature verification
  // using your Resend webhook secret
  // See: https://resend.com/docs/dashboard/webhooks#verifying-webhooks

  if (process.env.NODE_ENV === 'development') {
    return true; // Skip verification in development
  }

  if (!signature || !process.env.RESEND_WEBHOOK_SECRET) {
    return false;
  }

  // Implement HMAC verification here
  // const crypto = require('crypto');
  // const expectedSignature = crypto
  //   .createHmac('sha256', process.env.RESEND_WEBHOOK_SECRET)
  //   .update(payload)
  //   .digest('hex');
  // return signature === expectedSignature;

  return true; // Placeholder - implement proper verification
}

// Disable body parsing to access raw body for signature verification
export const config = {
  api: {
    bodyParser: false,
  },
};
```

### 2. Environment Variables - `.env.local`

```bash
# Resend API Key
RESEND_API_KEY=re_your_api_key_here

# Resend Webhook Secret (for verifying webhooks)
RESEND_WEBHOOK_SECRET=whsec_your_webhook_secret

# Support email address
SUPPORT_EMAIL=support@mycompany.com
```

### 3. Resend Configuration

#### Setting Up Inbound Email (Receiving)

1. **Verify your domain** in Resend dashboard
2. **Configure MX records** for your domain to route emails to Resend
3. **Set up inbound routing** in Resend dashboard:
   - Go to Domains > Your Domain > Inbound Routing
   - Add a webhook URL: `https://yourdomain.com/api/email-webhook`
   - Select "Forward to webhook"

#### Webhook Event Types to Enable

In Resend dashboard, enable these events for your webhook:
- `email.received` (for inbound emails)

### 4. Alternative: Using Resend's Inbound API Directly

If you need more control, you can use Resend's inbound email parsing:

```typescript
// /app/api/email-webhook/route.ts (Alternative Implementation)
import { NextRequest, NextResponse } from 'next/server';
import { Resend } from 'resend';
import { simpleParser } from 'mailparser'; // npm install mailparser

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const rawEmail = formData.get('email') as string;

    if (!rawEmail) {
      return NextResponse.json({ error: 'No email data' }, { status: 400 });
    }

    // Parse the raw email
    const parsed = await simpleParser(rawEmail);

    const from = parsed.from?.text || '';
    const subject = parsed.subject || '';
    const messageId = parsed.messageId || '';
    const inReplyTo = parsed.inReplyTo || '';
    const references = parsed.references || [];

    // Build references chain
    const referencesChain = [...references, messageId].join(' ');

    // Send threaded auto-reply
    await resend.emails.send({
      from: 'support@mycompany.com',
      to: [from],
      subject: `Re: ${subject}`,
      text: "Thanks for your email, we'll respond within 24 hours.",
      headers: {
        'In-Reply-To': messageId,
        'References': referencesChain,
        'X-Auto-Response-Suppress': 'OOF, AutoReply',
        'Precedence': 'auto_reply',
      },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json({ error: 'Server error' }, { status: 500 });
  }
}
```

### 5. Package Dependencies

```json
{
  "dependencies": {
    "next": "^14.x",
    "react": "^18.x",
    "resend": "^3.x",
    "mailparser": "^3.x" // Optional, for parsing raw emails
  }
}
```

Install with:
```bash
npm install resend mailparser
npm install -D @types/mailparser
```

## Key Implementation Details

### Threading Headers Explained

| Header | Purpose |
|--------|---------|
| `Message-ID` | Unique identifier for each email (generated by sender) |
| `In-Reply-To` | References the `Message-ID` of the email being replied to |
| `References` | Chain of all `Message-ID`s in the conversation thread |

### Auto-Reply Loop Prevention

The headers `X-Auto-Response-Suppress` and `Precedence` help prevent:
- Two auto-responders creating an infinite loop
- Vacation/out-of-office replies triggering your auto-reply

### Security Considerations

1. **Verify webhooks**: Always verify the Resend signature in production
2. **Rate limiting**: Consider implementing rate limiting per sender
3. **Email validation**: Validate the `from` address before sending replies
4. **Content filtering**: Consider filtering for spam before auto-replying

## Testing

### Local Testing with ngrok

1. Start your Next.js dev server:
   ```bash
   npm run dev
   ```

2. Expose via ngrok:
   ```bash
   ngrok http 3000
   ```

3. Configure Resend webhook to use the ngrok URL

4. Send a test email to your support address

### Manual Test Script

```typescript
// scripts/test-webhook.ts
const testPayload = {
  from: 'test@example.com',
  to: ['support@mycompany.com'],
  subject: 'Test Support Request',
  text: 'I need help with my account',
  headers: {
    'message-id': '<test-message-123@example.com>',
  },
};

fetch('http://localhost:3000/api/email-webhook', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(testPayload),
});
```

## Troubleshooting

### Emails Not Threading

1. Check that `In-Reply-To` matches the original `Message-ID` exactly
2. Verify `References` includes the original `Message-ID`
3. Ensure the subject line matches (with or without `Re:`)

### Webhook Not Receiving

1. Verify MX records are configured correctly
2. Check Resend dashboard for webhook delivery logs
3. Ensure your endpoint returns 200 status quickly (before processing)

### Auto-Reply Loops

1. Check for `X-Auto-Response-Suppress` header
2. Filter out emails with `Precedence: bulk` or `Precedence: auto_reply`
3. Implement a "sent auto-reply" cache to avoid duplicates

## References

- [Resend API Documentation](https://resend.com/docs/api-reference/emails/send-email)
- [Resend Webhooks](https://resend.com/docs/dashboard/webhooks)
- [Resend Inbound Email](https://resend.com/docs/dashboard/domains/inbound-routing)
- [RFC 5322 - Internet Message Format](https://tools.ietf.org/html/rfc5322)
- [Email Threading Best Practices](https://www.jwz.org/doc/threading.html)
