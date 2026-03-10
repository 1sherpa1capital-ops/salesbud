/**
 * Email Threading Example with Resend
 *
 * This demonstrates how to maintain conversation threads when sending
 * and receiving emails via Resend.
 */

import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

// In-memory storage (use database in production)
const conversations = new Map();

/**
 * Generate a custom Message-ID for threading
 * Format: <conversation-id@yourdomain.com>
 */
function generateMessageId(conversationId) {
  return `<${conversationId}@syntolabs.xyz>`;
}

/**
 * Extract conversation ID from a Message-ID header
 */
function extractConversationId(messageId) {
  if (!messageId) return null;
  const match = messageId.match(/<([^@]+)@/);
  return match ? match[1] : null;
}

/**
 * Send initial email to start a conversation
 */
export async function sendInitialEmail({
  to,
  subject,
  html,
  text,
  metadata = {}
}) {
  // Generate unique conversation ID
  const conversationId = `conv-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  const messageId = generateMessageId(conversationId);

  // Send email with custom Message-ID
  const { data, error } = await resend.emails.send({
    from: 'Synto Labs <team@syntolabs.xyz>',
    to: [to],
    subject,
    html,
    text,
    headers: {
      'Message-ID': messageId,
      'X-Conversation-ID': conversationId,
    },
    tags: [
      { name: 'conversation_id', value: conversationId },
      { name: 'email_type', value: 'initial' },
    ],
  });

  if (error) {
    console.error('Failed to send:', error);
    throw error;
  }

  // Store conversation
  conversations.set(conversationId, {
    id: conversationId,
    recipient: to,
    subject,
    messages: [{
      id: data.id,
      messageId,
      type: 'sent',
      timestamp: new Date().toISOString(),
    }],
    metadata,
  });

  console.log(`✅ Initial email sent`);
  console.log(`   Conversation ID: ${conversationId}`);
  console.log(`   Message-ID: ${messageId}`);
  console.log(`   Resend ID: ${data.id}`);

  return {
    conversationId,
    messageId,
    resendId: data.id,
  };
}

/**
 * Send a reply in an existing conversation thread
 */
export async function sendReply({
  conversationId,
  replyToMessageId,  // The Message-ID we're replying to
  references,        // Array of previous Message-IDs in the chain
  to,
  subject,
  html,
  text,
}) {
  // Build References header (space-separated list of all Message-IDs)
  const referencesHeader = references.join(' ');

  // Generate new Message-ID for this reply
  const newMessageId = generateMessageId(`${conversationId}-reply-${Date.now()}`);

  const { data, error } = await resend.emails.send({
    from: 'Synto Labs <team@syntolabs.xyz>',
    to: [to],
    subject: subject.startsWith('Re:') ? subject : `Re: ${subject}`,
    html,
    text,
    headers: {
      'Message-ID': newMessageId,
      'In-Reply-To': replyToMessageId,
      'References': referencesHeader,
      'X-Conversation-ID': conversationId,
    },
    tags: [
      { name: 'conversation_id', value: conversationId },
      { name: 'email_type', value: 'reply' },
    ],
  });

  if (error) {
    console.error('Failed to send reply:', error);
    throw error;
  }

  // Update conversation
  const conversation = conversations.get(conversationId);
  if (conversation) {
    conversation.messages.push({
      id: data.id,
      messageId: newMessageId,
      inReplyTo: replyToMessageId,
      type: 'sent',
      timestamp: new Date().toISOString(),
    });
  }

  console.log(`✅ Reply sent`);
  console.log(`   New Message-ID: ${newMessageId}`);
  console.log(`   In-Reply-To: ${replyToMessageId}`);
  console.log(`   References: ${referencesHeader}`);

  return {
    messageId: newMessageId,
    resendId: data.id,
  };
}

/**
 * Process incoming email webhook from Resend
 * Call this from your webhook endpoint
 */
export async function processIncomingEmail(webhookPayload) {
  const { type, data } = webhookPayload;

  if (type !== 'email.received') {
    console.log('Ignoring non-received event:', type);
    return;
  }

  console.log('\n📨 Incoming email received');
  console.log(`   From: ${data.from}`);
  console.log(`   To: ${data.to.join(', ')}`);
  console.log(`   Subject: ${data.subject}`);

  // 1. Fetch full email content and headers
  const { data: email, error } = await resend.emails.receiving.get(data.email_id);

  if (error) {
    console.error('Failed to fetch email:', error);
    return;
  }

  // 2. Extract Message-ID headers
  const incomingMessageId = email.headers['message-id'];
  const inReplyTo = email.headers['in-reply-to'];
  const references = email.headers['references'] || '';

  console.log(`   Message-ID: ${incomingMessageId}`);
  console.log(`   In-Reply-To: ${inReplyTo || '(none)'}`);

  // 3. Find existing conversation or create new
  let conversationId;
  let messageChain = [];

  if (inReplyTo) {
    // This is a reply - find the conversation
    conversationId = extractConversationId(inReplyTo);
    const conversation = conversations.get(conversationId);

    if (conversation) {
      // Build references chain
      messageChain = [
        ...conversation.messages.map(m => m.messageId),
        incomingMessageId,
      ];
      console.log(`   Found conversation: ${conversationId}`);
    } else {
      console.log(`   Unknown conversation, starting new thread`);
      conversationId = `conv-${Date.now()}`;
      messageChain = [incomingMessageId];
    }
  } else {
    // New conversation started by external sender
    conversationId = `conv-${Date.now()}`;
    messageChain = [incomingMessageId];
    console.log(`   New conversation started: ${conversationId}`);
  }

  // 4. Store the incoming message
  if (!conversations.has(conversationId)) {
    conversations.set(conversationId, {
      id: conversationId,
      recipient: data.from,
      subject: data.subject,
      messages: [],
    });
  }

  const conversation = conversations.get(conversationId);
  conversation.messages.push({
    messageId: incomingMessageId,
    inReplyTo,
    from: data.from,
    type: 'received',
    timestamp: new Date().toISOString(),
    html: email.html,
    text: email.text,
  });

  return {
    conversationId,
    incomingMessageId,
    messageChain,
    from: data.from,
    subject: data.subject,
    html: email.html,
    text: email.text,
  };
}

/**
 * Reply to a received email
 */
export async function replyToIncomingEmail({
  conversationId,
  replyHtml,
  replyText,
}) {
  const conversation = conversations.get(conversationId);

  if (!conversation) {
    throw new Error(`Conversation ${conversationId} not found`);
  }

  // Get the last received message
  const lastReceived = conversation.messages
    .filter(m => m.type === 'received')
    .pop();

  if (!lastReceived) {
    throw new Error('No received message to reply to');
  }

  // Build the message chain for References header
  const messageChain = conversation.messages
    .map(m => m.messageId)
    .filter(Boolean);

  return sendReply({
    conversationId,
    replyToMessageId: lastReceived.messageId,
    references: messageChain,
    to: lastReceived.from,
    subject: conversation.subject,
    html: replyHtml,
    text: replyText,
  });
}

/**
 * Example usage
 */
async function example() {
  // Scenario 1: Send initial email to client
  console.log('\n=== SCENARIO 1: Send Initial Email ===\n');
  const { conversationId, messageId } = await sendInitialEmail({
    to: 'client@example.com',
    subject: 'Project Kickoff',
    html: '<p>Hi! Excited to start working together.</p>',
    text: 'Hi! Excited to start working together.',
  });

  // Scenario 2: Client replies (simulated webhook)
  console.log('\n=== SCENARIO 2: Client Replies (Simulated) ===\n');

  // In reality, this comes from Resend webhook
  const simulatedWebhook = {
    type: 'email.received',
    data: {
      email_id: 'recv_abc123',
      from: 'client@example.com',
      to: ['team@syntolabs.xyz'],
      subject: 'Re: Project Kickoff',
    },
  };

  // Note: In production, you'd fetch the actual email from Resend
  // For this example, we'll simulate the received email data
  console.log('   (In production, fetch from: resend.emails.receiving.get(email_id))');

  // Scenario 3: Reply to client maintaining thread
  console.log('\n=== SCENARIO 3: Send Threaded Reply ===\n');

  // This is what you'd do after processing the incoming email
  const replyResult = await sendReply({
    conversationId,
    replyToMessageId: '<client-reply-123@example.com>',  // From client's email
    references: [messageId, '<client-reply-123@example.com>'], // Full chain
    to: 'client@example.com',
    subject: 'Re: Project Kickoff',
    html: `
      <p>Thanks for your reply! Let's schedule a call.</p>
      <br>
      <div style="border-left: 2px solid #ccc; padding-left: 10px; color: #666;">
        <p><strong>On Mon, Client wrote:</strong></p>
        <p>Sounds great! When can we start?</p>
      </div>
    `,
    text: `Thanks for your reply! Let's schedule a call.

---
On Mon, Client wrote:
Sounds great! When can we start?`,
  });

  console.log('\n=== Conversation Summary ===');
  console.log(JSON.stringify(conversations.get(conversationId), null, 2));
}

// Run example if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  example().catch(console.error);
}
