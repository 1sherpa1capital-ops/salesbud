# Next.js Webhook Handler: Threaded Auto-Reply

A complete Next.js API route that receives emails via Resend webhooks and sends threaded auto-replies.

## File: `app/api/webhooks/resend/route.ts`

```typescript
import { Resend } from 'resend';
import { NextRequest, NextResponse } from 'next/server';

const resend = new Resend(process.env.RESEND_API_KEY);

/**
 * Resend webhook handler for receiving emails and sending threaded auto-replies
 *
 * When someone emails support@mycompany.com, this handler:
 * 1. Verifies the webhook signature for security
 * 2. Extracts the sender's Message-ID for threading
 * 3. Sends a threaded auto-reply that appears in the same conversation
 */
export async function POST(req: NextRequest) {
  try {
    // 1. Get raw body for signature verification
    // IMPORTANT: Must use raw text, not parsed JSON, for signature verification
    const payload = await req.text();

    // 2. Verify webhook signature (security)
    const svixId = req.headers.get('svix-id');
    const svixTimestamp = req.headers.get('svix-timestamp');
    const svixSignature = req.headers.get('svix-signature');

    if (!svixId || !svixTimestamp || !svixSignature) {
      console.error('Missing Svix headers');
      return NextResponse.json(
        { error: 'Missing webhook headers' },
        { status: 400 }
      );
    }

    // Verify the webhook signature
    const event = resend.webhooks.verify({
      payload,
      headers: {
        'svix-id': svixId,
        'svix-timestamp': svixTimestamp,
        'svix-signature': svixSignature,
      },
      secret: process.env.RESEND_WEBHOOK_SECRET!,
    });

    // 3. Only process email.received events
    if (event.type !== 'email.received') {
      console.log(`Ignoring event type: ${event.type}`);
      return NextResponse.json({ received: true });
    }

    // 4. Extract email data from webhook payload
    const {
      email_id,
      message_id,      // CRITICAL: Their Message-ID for threading
      from,
      to,
      subject,
      in_reply_to,     // Points to our original email (if this is a reply)
    } = event.data;

    console.log('Received email:', {
      from,
      to: to[0],
      subject,
      messageId: message_id,
      inReplyTo: in_reply_to,
    });

    // 5. Send threaded auto-reply
    // This creates a reply that appears in the same thread in Gmail/Outlook
    await sendThreadedAutoReply({
      recipientEmail: from,
      originalSubject: subject,
      originalMessageId: message_id,
      replyToAddress: to[0],  // The address they sent to (e.g., support@mycompany.com)
    });

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error('Webhook error:', error);
    return NextResponse.json(
      { error: 'Webhook processing failed' },
      { status: 500 }
    );
  }
}

/**
 * Sends a threaded auto-reply that appears in the same email conversation
 *
 * Email threading works via three headers:
 * - Message-ID: Unique ID for this email
 * - In-Reply-To: Message-ID of the email we're replying to
 * - References: Space-separated list of all Message-IDs in the conversation
 */
interface AutoReplyParams {
  recipientEmail: string;
  originalSubject: string;
  originalMessageId: string;
  replyToAddress: string;
}

async function sendThreadedAutoReply({
  recipientEmail,
  originalSubject,
  originalMessageId,
  replyToAddress,
}: AutoReplyParams) {
  // Generate a unique Message-ID for our reply
  const timestamp = Date.now();
  const ourMessageId = `<autoreply-${timestamp}@mycompany.com>`;

  // Clean up subject line (remove existing "Re:" prefix to avoid duplication)
  const cleanSubject = originalSubject.replace(/^Re:\s*/i, '');
  const replySubject = `Re: ${cleanSubject}`;

  console.log('Sending threaded auto-reply:', {
    to: recipientEmail,
    subject: replySubject,
    ourMessageId,
    inReplyTo: originalMessageId,
  });

  const { data, error } = await resend.emails.send({
    from: `MyCompany Support <${replyToAddress}>`,
    to: [recipientEmail],
    subject: replySubject,
    html: `
      <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333;">
        <p>Thanks for your email! We've received your message and will respond within 24 hours.</p>

        <p style="margin-top: 20px;">
          <strong>Your request details:</strong><br>
          Subject: ${cleanSubject}<br>
          Received: ${new Date().toLocaleString()}
        </p>

        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">

        <p style="font-size: 12px; color: #666;">
          This is an automated response. Please do not reply to this email.<br>
          For urgent matters, please call us at (555) 123-4567.
        </p>
      </div>
    `,
    text: `Thanks for your email! We've received your message and will respond within 24 hours.

Your request details:
Subject: ${cleanSubject}
Received: ${new Date().toLocaleString()}

---
This is an automated response. Please do not reply to this email.
For urgent matters, please call us at (555) 123-4567.`,
    headers: {
      // CRITICAL: These three headers enable threading in Gmail/Outlook
      'Message-ID': ourMessageId,           // Our email's unique ID
      'In-Reply-To': originalMessageId,     // Links to their email (creates thread)
      'References': originalMessageId,      // Conversation chain
    },
  });

  if (error) {
    console.error('Failed to send auto-reply:', error);
    throw new Error(`Auto-reply failed: ${error.message}`);
  }

  console.log('Auto-reply sent successfully:', {
    resendId: data?.id,
    messageId: ourMessageId,
  });

  return data;
}

/**
 * GET handler for webhook verification (Resend may use this to verify endpoint)
 */
export async function GET() {
  return NextResponse.json({ status: 'Webhook endpoint active' });
}
```

## Environment Variables

Add these to your `.env.local`:

```bash
# Resend API Key
RESEND_API_KEY=re_your_api_key_here

# Resend Webhook Secret (from Resend Dashboard > Webhooks)
RESEND_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

## Setup Instructions

### 1. Configure Resend Inbound Email

In your Resend Dashboard:
- Go to **Domains** > Select your domain
- Enable **Inbound Email** for `support@mycompany.com`
- Set webhook URL to: `https://yourdomain.com/api/webhooks/resend`

### 2. Webhook Configuration

In Resend Dashboard:
- Go to **Webhooks** > **Create Webhook**
- Endpoint URL: `https://yourdomain.com/api/webhooks/resend`
- Events: Select `email.received`
- Copy the **Webhook Secret** to your `.env.local`

### 3. How Threading Works

When someone emails `support@mycompany.com`:

1. **Incoming Email** arrives with headers:
   ```
   Message-ID: <abc123@gmail.com>
   Subject: Help with my order
   ```

2. **Webhook fires** with `event.data.message_id` = `<abc123@gmail.com>`

3. **Auto-reply sends** with headers:
   ```
   Message-ID: <autoreply-123@mycompany.com>
   In-Reply-To: <abc123@gmail.com>
   References: <abc123@gmail.com>
   Subject: Re: Help with my order
   ```

4. **Result**: Both emails appear threaded in the user's inbox

## Key Threading Headers Explained

| Header | Purpose | Example |
|--------|---------|---------|
| `Message-ID` | Unique identifier for THIS email | `<autoreply-123@mycompany.com>` |
| `In-Reply-To` | Message-ID of the email being replied to | `<abc123@gmail.com>` |
| `References` | All Message-IDs in the conversation chain | `<abc123@gmail.com>` |

## Testing

1. **Send test email** to `support@mycompany.com` from Gmail
2. **Check webhook** delivered (Resend Dashboard > Webhooks > Logs)
3. **Verify auto-reply** received in your Gmail
4. **Confirm threading** - both emails should be grouped together

## Common Issues

### Emails Not Threading
- Ensure `In-Reply-To` exactly matches the original `Message-ID`
- Verify subject lines match (Gmail also threads by subject)
- Check that both emails are in the same folder (not spam)

### Webhook Verification Failing
- Use `req.text()` not `req.json()` for the raw payload
- Ensure all three Svix headers are present
- Verify webhook secret is correct

## Production Considerations

1. **Rate Limiting**: Add rate limiting to prevent spam
2. **Duplicate Prevention**: Track `email_id` to avoid double replies
3. **Database Storage**: Store conversations for context-aware replies
4. **Error Handling**: Implement retry logic for failed sends
5. **Monitoring**: Log all webhook events and auto-replies
