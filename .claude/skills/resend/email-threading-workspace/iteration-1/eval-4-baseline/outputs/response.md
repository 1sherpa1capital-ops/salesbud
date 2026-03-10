# Email Threading with Quoted Text

## Problem
When replying to a client's email, you want to include the original message indented below your response, similar to Gmail's threaded email format.

## Solution

### HTML Email Format

For HTML emails, use a blockquote element with appropriate styling:

```html
<div style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
  <p>Hi John,</p>

  <p>Thanks for reaching out. I've reviewed your proposal and would love to discuss next steps.</p>

  <p>Are you available for a call Tuesday at 2pm?</p>

  <p>Best regards,<br>
  Sarah</p>
</div>

<br>
<div style="border-left: 2px solid #ddd; margin-left: 10px; padding-left: 10px; color: #666;">
  <p style="margin: 0;"><strong>From:</strong> John Doe &lt;john@example.com&gt;</p>
  <p style="margin: 0;"><strong>Sent:</strong> Monday, March 3, 2025 at 9:00 AM</p>
  <p style="margin: 0;"><strong>To:</strong> Sarah Smith &lt;sarah@company.com&gt;</p>
  <p style="margin: 0;"><strong>Subject:</strong> Project Proposal</p>
  <br>
  <p>Hi Sarah,</p>

  <p>I'd like to discuss a potential project with your team.</p>

  <p>Please let me know when you're available.</p>

  <p>Thanks,<br>
  John</p>
</div>
```

### Plain Text Format

For plain text emails, use the greater-than (>) character to prefix quoted lines:

```
Hi John,

Thanks for reaching out. I've reviewed your proposal and would love to discuss next steps.

Are you available for a call Tuesday at 2pm?

Best regards,
Sarah

---
On Monday, March 3, 2025, John Doe <john@example.com> wrote:

> Hi Sarah,
>
> I'd like to discuss a potential project with your team.
>
> Please let me know when you're available.
>
> Thanks,
> John
```

## Implementation Notes

1. **HTML Blockquote Styling**: The left border (`border-left`) visually separates the quoted content, matching Gmail's style.

2. **Header Information**: Include From, Sent, To, and Subject fields in the quoted section for context.

3. **Plain Text Indentation**: Each line of the original message should be prefixed with `> ` to indicate it's quoted text.

4. **Resend API Integration**: When using the Resend API, include the threaded content in the `html` or `text` field:

```javascript
const response = await resend.emails.send({
  from: 'sarah@company.com',
  to: 'john@example.com',
  subject: 'Re: Project Proposal',
  html: htmlContent,  // HTML version with blockquote
  text: textContent   // Plain text version with > prefixes
});
```

## Best Practices

- Always provide both HTML and plain text versions for maximum compatibility
- Keep quoted text at the bottom (bottom-posting) for professional communication
- Trim excessive quoted content if the thread is long
- Maintain consistent formatting throughout your email correspondence
