/**
 * CORRECT Email Threading with Resend
 * Based on Context7 documentation
 */

import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

/**
 * Send initial email WITH custom Message-ID
 * This is the key - we must set our own Message-ID
 */
export async function sendInitialEmail({ to, subject, html, text }) {
  // Generate conversation ID
  const conversationId = `conv-${Date.now()}`;

  // Generate custom Message-ID (this is critical!)
  // Format must match standard Message-ID: <unique-id@domain.com>
  const messageId = `<${conversationId}@syntolabs.xyz>`;

  const { data, error } = await resend.emails.send({
    from: 'Synto Labs <rhigden@syntolabs.xyz>',
    to: [to],
    subject,
    html,
    text,
    headers: {
      'Message-ID': messageId,  // ← CRITICAL: Set your own Message-ID
    },
  });

  if (error) throw error;

  console.log('✅ Initial email sent');
  console.log(`   Message-ID: ${messageId}`);
  console.log(`   Resend ID: ${data.id}`);

  return { conversationId, messageId, resendId: data.id };
}

/**
 * Handle incoming reply webhook
 * The webhook payload includes message_id directly!
 */
export async function handleIncomingReply(webhookPayload) {
  const { type, data } = webhookPayload;

  if (type !== 'email.received') return;

  console.log('\n📨 Received reply');
  console.log(`   From: ${data.from}`);
  console.log(`   Subject: ${data.subject}`);
  console.log(`   Their Message-ID: ${data.message_id}`);  // ← This is the key!

  // Fetch full email to get body content
  const { data: email } = await resend.emails.receiving.get(data.email_id);

  return {
    from: data.from,
    subject: data.subject,
    theirMessageId: data.message_id,  // Use this for In-Reply-To!
    html: email.html,
    text: email.text,
    // Also check email.headers['in-reply-to'] to see what they're replying to
  };
}

/**
 * Send threaded reply
 * Use the message_id from the received email
 */
export async function sendThreadedReply({
  to,
  subject,
  replyToMessageId,    // ← data.message_id from webhook
  references,          // ← Chain of previous Message-IDs
  html,
  text,
}) {
  // Build References header
  const referencesHeader = references.join(' ');

  // Generate new Message-ID for our reply
  const newMessageId = `<reply-${Date.now()}@syntolabs.xyz>`;

  const { data, error } = await resend.emails.send({
    from: 'Synto Labs <rhigden@syntolabs.xyz>',
    to: [to],
    subject: subject.startsWith('Re:') ? subject : `Re: ${subject}`,
    html,
    text,
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': replyToMessageId,     // ← Links to their email
      'References': referencesHeader,       // ← Full conversation chain
    },
  });

  if (error) throw error;

  console.log('✅ Threaded reply sent');
  console.log(`   New Message-ID: ${newMessageId}`);
  console.log(`   In-Reply-To: ${replyToMessageId}`);
  console.log(`   References: ${referencesHeader}`);

  return { messageId: newMessageId, resendId: data.id };
}

/**
 * Complete flow example
 */
async function completeExample() {
  // Step 1: Send initial email
  const { messageId: ourMessageId } = await sendInitialEmail({
    to: '1sherpa1capital@gmail.com',
    subject: 'Test Thread',
    html: '<p>Hello! Please reply to this.</p>',
    text: 'Hello! Please reply to this.',
  });

  // Step 2: When user replies, webhook fires with their message_id
  // (Simulating what the webhook would send)
  const simulatedWebhook = {
    type: 'email.received',
    data: {
      email_id: 'received_abc123',
      from: '1sherpa1capital@gmail.com',
      subject: 'Re: Test Thread',
      message_id: '<their-reply-msg-id@gmail.com>',  // ← From Gmail
    },
  };

  const incoming = await handleIncomingReply(simulatedWebhook);

  // Step 3: Send threaded reply
  await sendThreadedReply({
    to: incoming.from,
    subject: incoming.subject,
    replyToMessageId: incoming.theirMessageId,  // ← Their Message-ID
    references: [ourMessageId, incoming.theirMessageId],  // ← Both
    html: '<p>Thanks for replying! This should be threaded.</p>',
    text: 'Thanks for replying! This should be threaded.',
  });
}

// Run example
completeExample().catch(console.error);
