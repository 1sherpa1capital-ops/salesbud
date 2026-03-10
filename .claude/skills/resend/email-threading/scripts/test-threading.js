/**
 * Test Script: Email Threading Flow
 *
 * This demonstrates the complete flow of:
 * 1. Sending initial email (with custom Message-ID)
 * 2. Receiving reply (simulated)
 * 3. Sending threaded reply back
 *
 * Run: node test-threading.js
 */

import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

// Test recipient (your email)
const TEST_RECIPIENT = '1sherpa1capital@gmail.com';

/**
 * Send initial email with custom Message-ID
 */
async function sendInitialEmail() {
  const conversationId = `test-${Date.now()}`;
  const messageId = `<${conversationId}@syntolabs.xyz>`;

  console.log('\n📤 SENDING INITIAL EMAIL');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`To: ${TEST_RECIPIENT}`);
  console.log(`Subject: Project Proposal`);
  console.log(`Message-ID: ${messageId}`);

  const { data, error } = await resend.emails.send({
    from: 'Synto Labs <team@syntolabs.xyz>',
    to: [TEST_RECIPIENT],
    subject: 'Project Proposal',
    html: `
      <p>Hi there!</p>
      <p>I'd love to discuss a potential project with you. Are you available for a call this week?</p>
      <p>Best,<br>Synto Labs Team</p>
    `,
    text: `Hi there!\n\nI'd love to discuss a potential project with you. Are you available for a call this week?\n\nBest,\nSynto Labs Team`,
    headers: {
      'Message-ID': messageId,
      'X-Conversation-ID': conversationId,
    },
  });

  if (error) {
    console.error('❌ Failed:', error);
    throw error;
  }

  console.log('✅ Email sent successfully!');
  console.log(`   Resend ID: ${data.id}`);

  return { conversationId, messageId, resendId: data.id };
}

/**
 * Send a threaded reply
 * In real scenario, this would happen after receiving client's reply
 */
async function sendThreadedReply(conversationId, originalMessageId, inReplyTo) {
  // Generate new Message-ID for this reply
  const replyMessageId = `<${conversationId}-reply-${Date.now()}@syntolabs.xyz>`;

  // Build References header (chain of all messages)
  const references = `${originalMessageId} ${inReplyTo}`;

  console.log('\n📤 SENDING THREADED REPLY');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`To: ${TEST_RECIPIENT}`);
  console.log(`Subject: Re: Project Proposal`);
  console.log(`Message-ID: ${replyMessageId}`);
  console.log(`In-Reply-To: ${inReplyTo}`);
  console.log(`References: ${references}`);

  const { data, error } = await resend.emails.send({
    from: 'Synto Labs <team@syntolabs.xyz>',
    to: [TEST_RECIPIENT],
    subject: 'Re: Project Proposal',
    html: `
      <p>Thanks for getting back to me!</p>
      <p>Based on your feedback, I've prepared a detailed proposal. Let me know what you think.</p>
      <br>
      <div style="border-left: 2px solid #ccc; padding-left: 10px; color: #666;">
        <p><strong>On Mon, Client wrote:</strong></p>
        <p>I'm interested! Can you send more details?</p>
      </div>
      <p>Best,<br>Synto Labs Team</p>
    `,
    text: `Thanks for getting back to me!\n\nBased on your feedback, I've prepared a detailed proposal. Let me know what you think.\n\n---\nOn Mon, Client wrote:\nI'm interested! Can you send more details?\n\nBest,\nSynto Labs Team`,
    headers: {
      'Message-ID': replyMessageId,
      'In-Reply-To': inReplyTo,
      'References': references,
      'X-Conversation-ID': conversationId,
    },
  });

  if (error) {
    console.error('❌ Failed:', error);
    throw error;
  }

  console.log('✅ Threaded reply sent successfully!');
  console.log(`   Resend ID: ${data.id}`);

  return { messageId: replyMessageId, resendId: data.id };
}

/**
 * Main test flow
 */
async function main() {
  console.log('\n╔════════════════════════════════════════════════════════════╗');
  console.log('║     EMAIL THREADING TEST WITH RESEND                       ║');
  console.log('╚════════════════════════════════════════════════════════════╝');

  try {
    // Step 1: Send initial email
    const { conversationId, messageId, resendId } = await sendInitialEmail();

    console.log('\n📋 SAVE THIS INFO (for the reply):');
    console.log(`   Conversation ID: ${conversationId}`);
    console.log(`   Original Message-ID: ${messageId}`);
    console.log(`   Original Resend ID: ${resendId}`);

    // Step 2: Wait for user to "reply" (simulated)
    console.log('\n⏳ INSTRUCTIONS:');
    console.log('   1. Check your Gmail for the initial email');
    console.log('   2. Reply to it (this creates the In-Reply-To header)');
    console.log('   3. In real code, you\'d capture that reply via webhook');
    console.log('   4. For this test, we\'ll simulate the reply headers');

    // Simulating client's reply Message-ID
    const simulatedClientReplyId = `<client-reply-${Date.now()}@gmail.com>`;

    console.log('\n   (Simulating client reply with Message-ID: ' + simulatedClientReplyId + ')');

    // Step 3: Send threaded reply
    await sendThreadedReply(conversationId, messageId, simulatedClientReplyId);

    console.log('\n✅ TEST COMPLETE!');
    console.log('\n📧 Check your Gmail:');
    console.log('   - Both emails should be in the SAME THREAD');
    console.log('   - Gmail groups them by In-Reply-To and References headers');
    console.log('   - Without those headers, they\'d appear as separate emails');

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    process.exit(1);
  }
}

// Run the test
main();
