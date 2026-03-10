# Email Threading with Resend

This example shows how to maintain conversation threads when sending and receiving emails via Resend.

## The Problem

When you send emails via Resend:
- Resend generates a `Message-ID` header (e.g., `<abc123@resend.dev>`)
- The API only returns `{ "id": "email-id" }` — **not** the `Message-ID`
- Without the `Message-ID`, you can't properly thread replies

## The Solution

**Generate your own `Message-ID`** based on your internal conversation tracking.

## How Threading Works

Email clients (Gmail, Outlook, etc.) group emails using these headers:

| Header | Purpose |
|--------|---------|
| `Message-ID` | Unique ID for this email |
| `In-Reply-To` | Message-ID of the email being replied to |
| `References` | Space-separated list of all Message-IDs in the thread |

## Files

| File | Purpose |
|------|---------|
| `email-threading-example.js` | Full implementation with all functions |
| `email-webhook-handler.js` | Webhook endpoint for receiving emails |
| `test-threading.js` | Runnable test demonstrating the flow |

## Quick Start

### 1. Install Dependencies

```bash
npm install resend
```

### 2. Set Environment Variables

```bash
export RESEND_API_KEY=re_icZV24Db_2Gu2sF9xKqP7gmXX1gDQrr1Z
export RESEND_WEBHOOK_SECRET=your_webhook_secret  # For webhooks
```

### 3. Run the Test

```bash
node test-threading.js
```

This will:
1. Send you an initial email with a custom `Message-ID`
2. Simulate receiving a reply
3. Send a threaded reply back

**Check Gmail:** Both emails should appear in the **same thread**.

## Key Code Patterns

### Sending Initial Email (with Message-ID)

```javascript
const conversationId = `conv-${Date.now()}`;
const messageId = `<${conversationId}@syntolabs.xyz>`;

await resend.emails.send({
  from: 'team@syntolabs.xyz',
  to: ['client@example.com'],
  subject: 'Project Kickoff',
  html: '<p>Hello!</p>',
  headers: {
    'Message-ID': messageId,  // ← Custom Message-ID
    'X-Conversation-ID': conversationId,
  },
});
```

### Sending Threaded Reply

```javascript
await resend.emails.send({
  from: 'team@syntolabs.xyz',
  to: ['client@example.com'],
  subject: 'Re: Project Kickoff',
  html: '<p>Thanks for replying!</p>',
  headers: {
    'Message-ID': '<reply-123@syntolabs.xyz>',
    'In-Reply-To': '<client-msg-456@example.com>',  // ← Links to their reply
    'References': '<original@syn> <client-msg-456@example.com>',  // ← Full chain
  },
});
```

### Receiving Emails (Webhook)

```javascript
// Fetch full email content including headers
const { data: email } = await resend.emails.receiving.get(emailId);

const incomingMessageId = email.headers['message-id'];
const inReplyTo = email.headers['in-reply-to'];  // Points to your original email

// Extract your conversation ID from In-Reply-To
const conversationId = extractConversationId(inReplyTo);
```

## Webhook Setup

To receive emails and reply automatically:

1. **Configure Resend Dashboard:**
   - Go to https://resend.com/webhooks
   - Add webhook URL: `https://yourdomain.com/api/webhook/resend`
   - Select event: `email.received`

2. **Set up webhook endpoint:**
   See `email-webhook-handler.js` for Express/Next.js examples.

3. **Domain Setup:**
   - For custom domain: Add MX record (see Resend docs)
   - Or use: `<anything>@<your-id>.resend.app` (no setup needed)

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Not setting Message-ID | Always set custom Message-ID when sending |
| Wrong In-Reply-To | Must match the exact Message-ID of the email you're replying to |
| Missing References | Include full chain of Message-IDs |
| Not fetching email headers | Webhook only gives metadata — call `resend.emails.receiving.get()` for headers |

## Testing

**Always use your own email addresses** — never test with fake addresses like `test@gmail.com`. Resend provides test addresses:

| Address | Result |
|---------|--------|
| `delivered@resend.dev` | Simulates successful delivery |
| `bounced@resend.dev` | Simulates hard bounce |

## Resources

- [Resend Email Sending Docs](https://resend.com/docs/api-reference/emails/send-email)
- [Resend Receiving Docs](https://resend.com/docs/dashboard/receiving-emails)
- [Resend Webhooks](https://resend.com/docs/dashboard/webhooks)
