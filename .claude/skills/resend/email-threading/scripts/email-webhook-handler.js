/**
 * Webhook Handler for Email Threading
 *
 * Use this in your Express/Fastify/Next.js API route
 * to receive emails and send threaded replies.
 */

import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);
const WEBHOOK_SECRET = process.env.RESEND_WEBHOOK_SECRET;

/**
 * Extract conversation ID from Message-ID
 */
function extractConversationId(messageId) {
  if (!messageId) return null;
  const match = messageId.match(/<([^@]+)@/);
  return match ? match[1] : null;
}

/**
 * Express/Node.js webhook handler
 * Mount at: POST /api/webhook/resend
 */
export async function handleWebhook(req, res) {
  try {
    // 1. Verify webhook signature (prevents spoofing)
    const payload = JSON.stringify(req.body);
    const signature = req.headers['svix-signature'];
    const timestamp = req.headers['svix-timestamp'];

    // Verify with Resend SDK
    const event = resend.webhooks.verify({
      payload: req.body,
      headers: {
        'svix-id': req.headers['svix-id'],
        'svix-timestamp': timestamp,
        'svix-signature': signature,
      },
      secret: WEBHOOK_SECRET,
    });

    // 2. Handle email.received event
    if (event.type === 'email.received') {
      await processReceivedEmail(event.data);
    }

    // 3. Always return 200 (Resend retries on failures)
    res.status(200).json({ ok: true });
  } catch (error) {
    console.error('Webhook error:', error);
    res.status(400).json({ error: error.message });
  }
}

/**
 * Process received email and optionally auto-reply
 */
async function processReceivedEmail(data) {
  console.log('\n📨 New email received');
  console.log(`   From: ${data.from}`);
  console.log(`   Subject: ${data.subject}`);

  // Fetch full email content + headers
  const { data: email, error } = await resend.emails.receiving.get(data.email_id);

  if (error) {
    console.error('Failed to fetch email:', error);
    return;
  }

  // Extract threading headers
  const incomingMessageId = email.headers['message-id'];
  const inReplyTo = email.headers['in-reply-to'];
  const conversationId = extractConversationId(inReplyTo) || `new-${Date.now()}`;

  console.log(`   Message-ID: ${incomingMessageId}`);
  console.log(`   In-Reply-To: ${inReplyTo || '(new thread)'}`);
  console.log(`   Conversation ID: ${conversationId}`);

  // === AUTO-REPLY EXAMPLE ===
  // Uncomment to automatically reply to all incoming emails

  // await sendThreadedReply({
  //   to: data.from,
  //   subject: data.subject,
  //   conversationId,
  //   replyToMessageId: incomingMessageId,
  //   previousReferences: email.headers['references'] || '',
  //   replyHtml: '<p>Thanks for your email! We\'ll respond shortly.</p>',
  //   replyText: 'Thanks for your email! We\'ll respond shortly.',
  // });
}

/**
 * Send a threaded reply
 */
async function sendThreadedReply({
  to,
  subject,
  conversationId,
  replyToMessageId,
  previousReferences,
  replyHtml,
  replyText,
}) {
  // Build References chain
  const references = previousReferences
    ? `${previousReferences} ${replyToMessageId}`
    : replyToMessageId;

  // Generate new Message-ID
  const newMessageId = `<reply-${Date.now()}-${Math.random().toString(36).substr(2, 9)}@syntolabs.xyz>`;

  const { data, error } = await resend.emails.send({
    from: 'Synto Labs <team@syntolabs.xyz>',
    to: [to],
    subject: subject.startsWith('Re:') ? subject : `Re: ${subject}`,
    html: replyHtml,
    text: replyText,
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': replyToMessageId,
      'References': references,
      'X-Conversation-ID': conversationId,
    },
  });

  if (error) {
    console.error('Failed to send reply:', error);
    return;
  }

  console.log(`✅ Threaded reply sent`);
  console.log(`   Resend ID: ${data.id}`);
  console.log(`   Message-ID: ${newMessageId}`);
  console.log(`   In-Reply-To: ${replyToMessageId}`);

  return data;
}

// Export for use in API routes
export { sendThreadedReply };
