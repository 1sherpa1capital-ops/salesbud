# Email Threading: Quoted Reply Formatting

This example shows how to send a threaded email reply with quoted text from the original message, similar to how Gmail formats replies.

## HTML Formatting for Quoted Reply

The HTML version uses a left border to visually distinguish the quoted content:

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

async function sendQuotedReply(
  originalEmail: {
    message_id: string;
    from: string;
    subject: string;
    created_at: string;
    html: string;
    text: string;
  },
  replyContent: string,
  conversationMessageIds: string[]
) {
  // Format the date for the quote header
  const dateStr = new Date(originalEmail.created_at).toLocaleString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short'
  });

  // Build HTML with styled quote block
  const htmlContent = `
    <div style="font-family: Arial, sans-serif; line-height: 1.5;">
      <p>${replyContent}</p>
      <br>
      <div style="border-left: 2px solid #ccc; padding-left: 10px; margin-left: 5px; color: #666;">
        <p style="margin-top: 0;"><strong>On ${dateStr}, ${originalEmail.from} wrote:</strong></p>
        <div style="margin-left: 10px;">
          ${originalEmail.html}
        </div>
      </div>
    </div>
  `;

  // Build text version with '>' quoting
  const quotedText = originalEmail.text
    .split('\n')
    .map(line => `> ${line}`)
    .join('\n');

  const textContent = `${replyContent}\n\nOn ${dateStr}, ${originalEmail.from} wrote:\n${quotedText}`;

  // Send the threaded reply
  const { data, error } = await resend.emails.send({
    from: 'Your Company <team@yourdomain.com>',
    to: [originalEmail.from],
    subject: `Re: ${originalEmail.subject.replace(/^Re: /, '')}`,
    html: htmlContent,
    text: textContent,
    headers: {
      'Message-ID': `<reply-${Date.now()}@yourdomain.com>`,
      'In-Reply-To': originalEmail.message_id,
      'References': conversationMessageIds.join(' '),
    },
  });

  if (error) throw error;
  return data.id;
}
```

## Example Output

### HTML Version (as seen in Gmail/Outlook)

```html
<div style="font-family: Arial, sans-serif; line-height: 1.5;">
  <p>Thanks for reaching out! I'd be happy to discuss the project timeline with you.</p>
  <br>
  <div style="border-left: 2px solid #ccc; padding-left: 10px; margin-left: 5px; color: #666;">
    <p style="margin-top: 0;"><strong>On Mon, Mar 3, 2025 at 2:30 PM EST, client@example.com wrote:</strong></p>
    <div style="margin-left: 10px;">
      <p>Hi there,</p>
      <p>Can we schedule a call to discuss the project timeline?</p>
      <p>Thanks,<br>John</p>
    </div>
  </div>
</div>
```

**Visual Result:**

The quoted section appears with a gray left border, indented content, and the "On [date], [sender] wrote:" header in bold.

### Text Version (for plain text clients)

```
Thanks for reaching out! I'd be happy to discuss the project timeline with you.

On Mon, Mar 3, 2025 at 2:30 PM EST, client@example.com wrote:
> Hi there,
>
> Can we schedule a call to discuss the project timeline?
>
> Thanks,
> John
```

## Key Components

| Component | HTML | Text |
|-----------|------|------|
| **Quote Indicator** | `border-left: 2px solid #ccc` | `>` prefix on each line |
| **Attribution Line** | `<strong>On [date], [sender] wrote:</strong>` | `On [date], [sender] wrote:` |
| **Indentation** | `padding-left: 10px` | N/A (using > prefix) |
| **Threading Headers** | `In-Reply-To` and `References` | Same headers |

## Threading Headers

The headers ensure the reply appears in the same thread:

```typescript
headers: {
  'Message-ID': '<reply-1234567890@yourdomain.com>',  // New unique ID for this email
  'In-Reply-To': '<original-msg-id@client.com>',       // The email we're replying to
  'References': '<first-msg@yourdomain.com> <original-msg-id@client.com>', // Full chain
}
```

## Complete Working Example

```typescript
// Example: Replying to a client inquiry
const originalEmail = {
  message_id: '<abc123@client-domain.com>',
  from: 'john@client.com',
  subject: 'Project Timeline Question',
  created_at: '2025-03-03T14:30:00Z',
  html: '<p>Hi team,</p><p>When can we expect the first deliverable?</p><p>Best,<br>John</p>',
  text: 'Hi team,\n\nWhen can we expect the first deliverable?\n\nBest,\nJohn'
};

const conversationHistory = [
  '<initial-456@yourdomain.com>',  // Your first email
  '<abc123@client-domain.com>'     // Client's reply
];

await sendQuotedReply(
  originalEmail,
  "We're targeting next Friday for the first draft. I'll send over a detailed schedule shortly!",
  conversationHistory
);
```

## Styling Tips

1. **Border Color**: Use a light gray (`#ccc` or `#ddd`) for the quote border
2. **Text Color**: Slightly dim the quoted text (`#666`) to distinguish it from your response
3. **Padding**: Add `padding-left` to create space between the border and quoted content
4. **Attribution**: Always include the date and sender for context
5. **Mobile**: The border-left approach works well on mobile devices without horizontal scrolling
