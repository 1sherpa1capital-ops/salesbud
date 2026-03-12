"""
Cold Email Sequence Engine via Resend
4-step cold email sequence from Synto Labs sales playbook
"""

import os
import random
import time
from typing import Any, Dict

import salesbud.utils.logger as logger
from salesbud.database import (
    get_config,
    get_daily_count,
    get_db,
    increment_daily_count,
    is_dry_run,
    log_activity,
)
from salesbud.models.lead import get_lead_by_id, update_lead_email_sent

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "Rhigden <rhigden@syntolabs.xyz>")


# ─── Cold Email Templates (from sales playbook) ────────────────────────────

EMAIL_TEMPLATES = {
    1: {
        "name": "Value-First",
        "subject": "Built this for {company} — took 3 mins",
        "body": """Hey {name},

I was researching {company} and noticed {observation}.

Ran your site through our automation engine and found:
• {insight_1}
• {insight_2}

I built a quick demo showing how we'd automate this.

No pitch, no calendar link, no obligation. Just wanted you to see what's possible.

If it's useful, reply and I'll explain how we built it.

If not, no worries — keep the demo.

— Rhigden
Founder, Synto Labs
P.S. This research took 3 minutes. That's the power of multi-agent workflows.""",
    },
    2: {
        "name": "Case Study",
        "subject": "How a similar agency saved 20h/week",
        "body": """Hey {name},

Since I last reached out, thought you'd find this relevant:

A similar agency in your space had the same challenge — {pain_point}.

We built a custom workflow for them:
• Scout Agent: Finds leads matching ICP
• Research Agent: Qualifies each lead in 30 seconds
• Writer Agent: Personalizes outreach
• Sender Agent: Sends at scale

Result: 20 hours/week saved, 3x response rate, $5k/month in reclaimed capacity.

Want to see how this would apply to {company}? Happy to do a free audit of your current workflow.

— Rhigden""",
    },
    3: {
        "name": "Soft Offer",
        "subject": "Free automation audit for {company}",
        "body": """Hey {name},

I've been thinking about {company}'s workflow.

Quick question: What's the ONE thing you'd automate if you could?

I'd be happy to do a free audit of your current workflows and identify:
• Top 3 automation opportunities
• Estimated time savings for each
• ROI projections (real numbers, not fluff)

No obligation — you get the audit whether we work together or not.

Worth 30 minutes of your time?

Reply "yes" and I'll send a Cal.com link.

— Rhigden""",
    },
    4: {
        "name": "Break-Up",
        "subject": "Permission to close your file?",
        "body": """Hey {name},

Haven't heard back, so I'm assuming automation isn't a priority right now.

That's completely fair — timing has to be right.

I'll close your file so I don't keep bothering you with emails.

If things change and you want to explore this, just reply and I'll reopen it. No hard feelings.

Best of luck with {company}!

— Rhigden""",
    },
}

# Default personalization vars
DEFAULT_EMAIL_VARS = {
    "observation": "your team handles a lot of repetitive client work",
    "insight_1": "15+ hours/week on manual lead qualification",
    "insight_2": "No systematic follow-up workflow",
    "pain_point": "manual lead qualification and repetitive proposals",
}

# Days to wait between each email step
EMAIL_STEP_DELAYS = {
    1: 0,  # Send immediately
    2: 3,  # Day 3
    3: 7,  # Day 7
    4: 14,  # Day 14
}


def send_email(to: str, subject: str, html: str, text: str = "") -> bool:
    """Send a single email via Resend API (or log in dry-run mode)."""
    if is_dry_run():
        logger.print_text("\n[DRY RUN] Would send email:")
        logger.print_text(f"  From: {RESEND_FROM_EMAIL}")
        logger.print_text(f"  To: {to}")
        logger.print_text(f"  Subject: {subject}")
        logger.print_text(f"  Body: {text[:150]}...")
        return True

    if not RESEND_API_KEY:
        logger.print_text("[Email] No RESEND_API_KEY found. Set it in .env")
        return False

    try:
        import resend

        resend.api_key = RESEND_API_KEY

        params: dict = {
            "from": RESEND_FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        if text:
            params["text"] = text

        result = resend.Emails.send(params)  # type: ignore[arg-type]
        logger.print_text(f"[Email] ✓ Sent to {to} (ID: {result.get('id', 'unknown')})")
        return True

    except Exception as e:
        logger.print_text(f"[Email] Error sending to {to}: {e}")
        import traceback

        traceback.print_exc()
        return False


def personalize_email(lead: Dict[str, Any], step: int) -> tuple:
    """Generate personalized email subject and body for a lead at a given step."""
    template = EMAIL_TEMPLATES[step]

    vars = DEFAULT_EMAIL_VARS.copy()
    vars["name"] = (lead.get("name") or "there").split()[0]  # First name only
    vars["company"] = lead.get("company") or "your company"

    # Simple industry detection from headline
    headline = (lead.get("headline") or "").lower()
    if "marketing" in headline:
        vars["pain_point"] = "managing campaigns at scale while keeping quality high"
        vars["observation"] = "your marketing team juggles a lot of moving pieces"
    elif "sales" in headline:
        vars["pain_point"] = "manual prospecting eating into selling time"
        vars["observation"] = "your sales process has some manual bottlenecks"
    elif "founder" in headline or "ceo" in headline:
        vars["pain_point"] = "wearing too many hats while trying to grow"
        vars["observation"] = "you're running a lot of ops manually alongside growth"

    subject = template["subject"].format(**vars)
    body = template["body"].format(**vars)

    return subject, body


def send_cold_email(lead: Dict[str, Any], step: int) -> bool:
    """Personalize and send a cold email at a given sequence step."""
    subject, body = personalize_email(lead, step)
    step_info = EMAIL_TEMPLATES[step]
    email = lead.get("email")

    if not email:
        logger.print_text(
            f"[Email] No email address for lead {lead.get('name', 'Unknown')} — skipping"
        )
        return False

    if is_dry_run():
        logger.print_text(
            f"\n[DRY RUN] Would send Email Step {step} ({step_info['name']}) to {lead.get('name', 'Unknown')}"
        )
        logger.print_text(f"[DRY RUN] To: {email}")
        logger.print_text(f"[DRY RUN] Subject: {subject}")
        logger.print_text(f"[DRY RUN] Body: {body[:150]}...")
        log_activity(lead["id"], "email_sent", f"[DRY RUN] Step {step}: {subject}")
        update_lead_email_sent(lead["id"], step)
        return True

    # Build HTML version
    html_body = body.replace("\n", "<br>")
    html = f"<div style='font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6;'>{html_body}</div>"

    success = send_email(email, subject, html, body)

    if success:
        log_activity(lead["id"], "email_sent", f"Step {step}: {subject}")
        update_lead_email_sent(lead["id"], step)

    return success


def get_leads_due_for_email(min_days: int = 3) -> list:
    """Get leads that are due for the next email step."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT * FROM leads
        WHERE email IS NOT NULL
        AND email != ''
        AND email_sequence_step > 0
        AND email_sequence_step < 4
        AND last_email_sent_at IS NOT NULL
        AND datetime(last_email_sent_at) <= datetime('now', '-{min_days} days')
        AND status NOT IN ('replied', 'booked', 'paused')
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_leads_ready_for_email_start() -> list:
    """Get leads that have email addresses but haven't started email sequence."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM leads
        WHERE email IS NOT NULL
        AND email != ''
        AND email_sequence_step = 0
        AND status NOT IN ('replied', 'booked', 'paused', 'completed')
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def start_email_sequence_for_lead(lead_id: int) -> bool:
    """Start the email sequence for a lead (send Step 1)."""
    lead = get_lead_by_id(lead_id)
    if not lead:
        logger.print_text(f"Lead {lead_id} not found.")
        return False

    if not lead.get("email"):
        logger.print_text(f"Lead {lead_id} ({lead.get('name')}) has no email address.")
        return False

    return send_cold_email(lead, step=1)


def is_quiet_mode() -> bool:
    """Check if quiet mode is enabled (for JSON output)."""
    return logger.is_quiet()


def run_email_sequence_step():
    """Run one step of the email sequence for all eligible leads."""
    quiet = is_quiet_mode()
    emails_per_hour = int(get_config("emails_per_hour") or 10)
    emails_per_day = int(get_config("emails_per_day") or 50)
    email_delay = int(get_config("email_delay_minutes") or 2)

    # Daily rate limit guard
    if not is_dry_run():
        sent_today = get_daily_count("emails")
        if sent_today >= emails_per_day:
            if not quiet:
                logger.print_text(
                    f"⛔ Daily email limit reached ({sent_today}/{emails_per_day}). Stopping."
                )
            return
        emails_per_hour = min(emails_per_hour, emails_per_day - sent_today)

    # First, start sequences for leads with emails who haven't started yet
    new_leads = get_leads_ready_for_email_start()
    if new_leads:
        if not quiet:
            logger.print_text(
                f"\n[Email Sequence] Starting sequences for {len(new_leads)} leads with emails"
            )
        for lead in new_leads[:emails_per_hour]:
            start_email_sequence_for_lead(lead["id"])
        return

    # Then, advance leads already in the email sequence
    # Step delays: 1→2 = 3 days, 2→3 = 4 days (day 7 - day 3), 3→4 = 7 days (day 14 - day 7)
    step_delays = {1: 3, 2: 4, 3: 7}

    all_due = []
    for current_step, delay in step_delays.items():
        leads = get_leads_due_for_email(min_days=delay)
        due_for_step = [lead for lead in leads if lead["email_sequence_step"] == current_step]
        all_due.extend(due_for_step)

    if not all_due:
        if not quiet:
            logger.print_text("No leads due for next email step.")
        return

    if not quiet:
        logger.print_text("\n=== Email Sequence Step ===")
        logger.print_text(f"Leads due for next step: {len(all_due)}")
        logger.print_text(f"Rate limit: {emails_per_hour} emails/hour")

    for i, lead in enumerate(all_due):
        if i >= emails_per_hour:
            if not quiet:
                logger.print_text(f"Rate limit reached ({emails_per_hour}/hour). Stopping.")
            break

        next_step = lead["email_sequence_step"] + 1
        if next_step > 4:
            if not quiet:
                logger.print_text(f"Lead {lead.get('name')} completed email sequence.")
            continue

        if i > 0 and not is_dry_run():
            delay = email_delay + random.randint(0, 3)
            if not quiet:
                logger.print_text(f"Waiting {delay} minutes before next email...")
            time.sleep(delay * 60)

        sent = send_cold_email(lead, next_step)
        if sent and not is_dry_run():
            increment_daily_count("emails")

    if not quiet:
        logger.print_text("\n=== Email Sequence Step Complete ===")
