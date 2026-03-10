# Next.js Webhook Handler for Resend Inbound Email Auto-Reply

This webhook handler receives emails from Resend and sends threaded auto-replies using the `In-Reply-To` and `References` headers.

## File: `app/api/webhook/route.ts`

```typescript
import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';
import { Resend } from 'resend';

// Initialize Resend client
const resend = new Resend(process.env.RESEND_API_KEY);

// Support email address that triggers auto-replies
const SUPPORT_EMAIL = 'support@mycompany.com';

// Auto-reply message
const AUTO_REPLY_HTML = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Auto-Reply</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="background: #f8f9fa; border-left: 4px solid #007bff; padding: 20px; border-radius: 4px;">
    <h2 style="margin-top: 0; color: #007bff;">Thanks for reaching out!</h2>
    <p>Thanks for your email, we'll respond within 24 hours.</p>
    <p style="margin-bottom: 0; font-size: 14px; color: #666;">
      This is an automated response. Please do not reply to this message.
    </p>
  </div>
</body>
</html>
`;

const AUTO_REPLY_TEXT = `Thanks for your email, we'll respond within 24 hours.

This is an automated response. Please do not reply to this message.`;

/**
 * Webhook handler for Resend inbound emails
 * Sends threaded auto-replies when someone emails support@mycompany.com
 */
export async function POST(request: NextRequest) {
  try {
    // Get the raw payload for webhook verification
    const payload = await request.text();

    // Extract Svix headers for webhook signature verification
    const svixId = request.headers.get('svix-id');
    const svixTimestamp = request.headers.get('svix-timestamp');
    const svixSignature = request.headers.get('svix-signature');

    // Verify webhook signature (CRITICAL for security)
    if (!svixId || !svixTimestamp || !svixSignature) {
      return NextResponse.json(
        { error: 'Missing webhook headers' },
        { status: 400 }
      );
    }

    const webhookSecret = process.env.RESEND_WEBHOOK_SECRET;
    if (!webhookSecret) {
      console.error('RESEND_WEBHOOK_SECRET not configured');
      return NextResponse.json(
        { error: 'Webhook secret not configured' },
        { status: 500 }
      );
    }

    // Verify the webhook signature
    let event;
    try {
      event = resend.webhooks.verify({
        payload,
        headers: {
          id: svixId,
          timestamp: svixTimestamp,
          signature: svixSignature,
        },
        webhookSecret,
      });
    } catch (err) {
      console.error('Webhook signature verification failed:', err);
      return NextResponse.json(
        { error: 'Invalid webhook signature' },
        { status: 401 }
      );
    }

    // Handle inbound email events
    if (event.type === 'email.received') {
      const emailData = event.data;

      // Log received email for debugging
      console.log('Inbound email received:', {
        from: emailData.from,
        to: emailData.to,
        subject: emailData.subject,
        messageId: emailData.message_id,
      });

      // Check if email was sent to support address
      const toAddresses = Array.isArray(emailData.to)
        ? emailData.to
        : [emailData.to];

      const isSupportEmail = toAddresses.some(
        (addr: string) => addr.toLowerCase() === SUPPORT_EMAIL.toLowerCase()
      );

      if (!isSupportEmail) {
        console.log('Email not addressed to support, skipping auto-reply');
        return NextResponse.json({ received: true, autoReply: false });
      }

      // Extract sender email address
      const senderEmail = extractEmailAddress(emailData.from);
      if (!senderEmail) {
        console.error('Could not extract sender email from:', emailData.from);
        return NextResponse.json(
          { error: 'Invalid sender address' },
          { status: 400 }
        );
      }

      // Build threading headers for proper email threading
      // In-Reply-To: The Message-ID of the email being replied to
      // References: Chain of Message-IDs in the conversation thread
      const threadingHeaders: Record<string, string> = {
        'In-Reply-To': emailData.message_id,
      };

      // Build References header
      // If the incoming email has a References header, append to it
      // Otherwise, just use the incoming message's Message-ID
      const existingReferences = emailData.headers?.['references'] || '';
      const references = existingReferences
        ? `${existingReferences} ${emailData.message_id}`
        : emailData.message_id;

      threadingHeaders['References'] = references;

      // Send the auto-reply with threading headers
      const { data: replyData, error: replyError } = await resend.emails.send({
        from: SUPPORT_EMAIL,
        to: [senderEmail],
        subject: `Re: ${emailData.subject}`,
        html: AUTO_REPLY_HTML,
        text: AUTO_REPLY_TEXT,
        headers: threadingHeaders,
      });

      if (replyError) {
        console.error('Failed to send auto-reply:', replyError);
        return NextResponse.json(
          { error: 'Failed to send auto-reply', details: replyError },
          { status: 500 }
        );
      }

      console.log('Auto-reply sent successfully:', {
        replyId: replyData?.id,
        to: senderEmail,
        inReplyTo: emailData.message_id,
        references,
      });

      return NextResponse.json({
        received: true,
        autoReply: true,
        replyId: replyData?.id,
      });
    }

    // Handle other webhook event types if needed
    console.log('Received webhook event:', event.type);
    return NextResponse.json({ received: true, type: event.type });

  } catch (error) {
    console.error('Webhook handler error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * Extract clean email address from a formatted address string
 * e.g., "John Doe <john@example.com>" -> "john@example.com"
 * e.g., "john@example.com" -> "john@example.com"
 */
function extractEmailAddress(fromHeader: string): string | null {
  if (!fromHeader) return null;

  // Try to extract email from angle brackets
  const angleMatch = fromHeader.match(/<([^>]+)>/);
  if (angleMatch) {
    return angleMatch[1].trim();
  }

  // If no angle brackets, assume the whole string is the email
  const cleanEmail = fromHeader.trim();
  if (isValidEmail(cleanEmail)) {
    return cleanEmail;
  }

  return null;
}

/**
 * Basic email validation
 */
function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Health check endpoint for GET requests
 */
export async function GET() {
  return NextResponse.json({
    status: 'ok',
    service: 'resend-webhook-handler',
    supportEmail: SUPPORT_EMAIL,
  });
}
```

## Environment Variables

Create a `.env.local` file with the following:

```bash
# Resend API Key - get from https://resend.com/api-keys
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Resend Webhook Secret - get from webhook settings in Resend dashboard
RESEND_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Override the support email address
# SUPPORT_EMAIL=support@mycompany.com
```

## Setup Instructions

### 1. Install Dependencies

```bash
npm install resend
# or
yarn add resend
# or
pnpm add resend
```

### 2. Configure Resend Webhook

1. Go to your Resend dashboard: https://resend.com/webhooks
2. Create a new webhook
3. Set the endpoint URL to: `https://yourdomain.com/api/webhook`
4. Select the "Email Received" event
5. Copy the webhook secret and add it to your `.env.local` as `RESEND_WEBHOOK_SECRET`

### 3. Enable Inbound Email (Receiving)

1. In Resend dashboard, go to Domains
2. Click on your domain
3. Enable "Inbound Email" feature
4. Configure the webhook URL to point to your `/api/webhook` endpoint

### 4. Deploy

Deploy to your hosting platform (Vercel, Railway, etc.):

```bash
# For Vercel
vercel --prod

# Environment variables will be read from .env.local
# Make sure to add them to your hosting platform's dashboard
```

## How Email Threading Works

### The Key Headers

1. **`In-Reply-To`**: Contains the `Message-ID` of the email being replied to. This tells email clients which message this is a reply to.

2. **`References`**: A space-separated list of all `Message-ID`s in the conversation thread. This maintains the full conversation history.

### Example Flow

```
1. Customer sends email to support@mycompany.com
   Message-ID: <abc123@customer-domain.com>

2. Your webhook receives the email and sends auto-reply with:
   In-Reply-To: <abc123@customer-domain.com>
   References: <abc123@customer-domain.com>

3. Customer's email client sees the In-Reply-To header
   and threads it under their original email
```

### Why This Works

- **Gmail**: Uses both `In-Reply-To` and `References` headers to group emails into conversation threads
- **Outlook**: Primarily uses `In-Reply-To` but also respects `References`
- **Apple Mail**: Uses `References` to build the conversation tree
- **Other clients**: Most modern email clients follow RFC 5322 threading standards

## Testing

### Local Testing with ngrok

```bash
# Start your Next.js dev server
npm run dev

# In another terminal, expose to internet with ngrok
ngrok http 3000

# Copy the ngrok HTTPS URL and set it in Resend webhook settings
# e.g., https://abc123.ngrok.io/api/webhook
```

### Send Test Email

```bash
# Using curl to trigger webhook (for testing without actual email)
curl -X POST http://localhost:3000/api/webhook \
  -H "Content-Type: application/json" \
  -H "svix-id: test-id-123" \
  -H "svix-timestamp: $(date +%s)" \
  -H "svix-signature: v1,testsignature" \
  -d '{
    "type": "email.received",
    "data": {
      "from": "test@example.com",
      "to": ["support@mycompany.com"],
      "subject": "Test Support Request",
      "message_id": "<test123@example.com>",
      "email_id": "email-uuid-here"
    }
  }'
```

## Security Considerations

1. **Webhook Signature Verification**: Always verify the Svix signature to ensure requests come from Resend
2. **Rate Limiting**: Consider adding rate limiting to prevent abuse
3. **Email Validation**: Validate sender addresses before sending replies
4. **Loop Prevention**: Ensure auto-replies don't trigger more auto-replies (handled by checking `to` address)

## Troubleshooting

### Auto-reply not threading

- Verify `In-Reply-To` header matches the original `Message-ID` exactly
- Check that `References` header includes the original message ID
- Ensure the `Message-ID` format includes angle brackets: `<id@domain.com>`

### Webhook not receiving events

- Verify webhook is configured in Resend dashboard
- Check that the endpoint URL is publicly accessible (not localhost)
- Verify `RESEND_WEBHOOK_SECRET` is set correctly

### Emails not sending

- Check `RESEND_API_KEY` is valid and has sending permissions
- Verify the sending domain is verified in Resend
- Check Resend dashboard for any sending errors
