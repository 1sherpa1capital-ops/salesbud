"""
LinkedIn DM Sequence Engine
NEPQ-based 5-step DM sequence with dry-run support
"""

import salesbud.utils.logger as logger
import random
from typing import List, Dict, Any
from salesbud.database import is_dry_run, log_activity, get_db
from salesbud.models.lead import get_lead_by_id, update_lead_status, update_lead_dm_sent
from salesbud.utils.browser import (
    get_stealth_context,
    create_stealth_page,
    safe_goto,
    check_for_challenge,
    random_delay,
    jitter_delay,
)

DM_TEMPLATES = {
    1: {
        "name": "Value Hook",
        "template": "Hey {name}, noticed you're {headline} at {company} — been seeing a lot of {industry} founders struggling with {pain}. Quick question: how's {challenge} been going for you?",
    },
    2: {
        "name": "Pain Question",
        "template": "{name}, wanted to follow up — when you think about {pain}, what's been the hardest part? Is it the time it takes, the cost, or something else entirely?",
    },
    3: {
        "name": "Social Proof",
        "template": "{name}, quick update — we just helped a {company_size} team in {industry} cut their {pain} by 60% in 30 days. Happy to share what worked if useful.",
    },
    4: {
        "name": "Low-Stakes Offer",
        "template": "Hey {name}, no pressure at all — would you be open to a 15-min call where I show you exactly what we did? No pitch, just tactics. Happy to hop on whenever works for you.",
    },
    5: {
        "name": "Breakup",
        "template": "{name}, last ping — completely understand if now's not the right time. If anything changes or you want to chat later, just reply. Otherwise, I'll stop interrupting. Best of luck with {company}!",
    },
}

DEFAULT_VARS = {
    "industry": "B2B SaaS",
    "pain": "lead generation",
    "challenge": "getting qualified leads",
    "company_size": "10-50 person",
}


def personalize_dm(lead: Dict[str, Any], step: int) -> str:
    """Generate personalized DM for a lead at a given sequence step."""
    template = DM_TEMPLATES[step]["template"]
    vars = DEFAULT_VARS.copy()
    vars["name"] = lead.get("name", "there")
    vars["headline"] = lead.get("headline", "")
    vars["company"] = lead.get("company", "your company")

    if lead.get("headline"):
        headline_lower = lead["headline"].lower()
        if "marketing" in headline_lower:
            vars["industry"] = "marketing"
        elif "sales" in headline_lower:
            vars["industry"] = "sales"
        elif "founder" in headline_lower or "ceo" in headline_lower:
            vars["industry"] = "startup"

    return template.format(**vars)


def get_leads_due_for_step(min_days: int = 3) -> List[Dict[str, Any]]:
    """Get leads that are due for the next DM step."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT * FROM leads 
        WHERE status = 'active' 
        AND sequence_step > 0 
        AND sequence_step < 5
        AND last_dm_sent_at IS NOT NULL
        AND datetime(last_dm_sent_at) <= datetime('now', '-{min_days} days')
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_newly_connected_leads() -> List[Dict[str, Any]]:
    """Get leads that are connected but haven't started DM sequence yet."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM leads 
        WHERE status = 'connected' 
        AND sequence_step = 0
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def send_dm(lead: Dict[str, Any], step: int) -> bool:
    """Send a DM to a lead (or log in dry-run mode)."""
    dm_text = personalize_dm(lead, step)
    step_info = DM_TEMPLATES[step]

    if is_dry_run():
        logger.print_text(
            f"\n[DRY RUN] Would send DM Step {step} ({step_info['name']}) to {lead.get('name', 'Unknown')}"
        )
        logger.print_text(f"[DRY RUN] Message: {dm_text[:100]}...")
        logger.print_text(f"[DRY RUN] LinkedIn URL: {lead.get('linkedin_url', 'N/A')}")
        log_activity(lead["id"], "dm_sent", f"[DRY RUN] Step {step}: {dm_text[:200]}")
        update_lead_dm_sent(lead["id"], step)
        return True

    linkedin_url = lead.get("linkedin_url")
    if not linkedin_url:
        logger.print_text(f"[DM] No LinkedIn URL for lead {lead.get('name')} — skipping")
        return False

    try:
        from playwright.sync_api import sync_playwright
        import json
        import os
        import time

        session_cookie = os.getenv("LINKEDIN_SESSION_COOKIE")

        playwright = sync_playwright().start()
        context, browser = get_stealth_context(
            playwright, headless=True, session_cookie=session_cookie
        )
        page = create_stealth_page(context)

        if not safe_goto(page, linkedin_url, timeout=60000):
            logger.print_text(f"[DM] Failed to navigate to {linkedin_url}")
            browser.close()
            playwright.stop()
            return False

        page.wait_for_timeout(int(jitter_delay(2.5) * 1000))

        challenge = check_for_challenge(page)
        if challenge:
            logger.print_text(f"[DM] Challenge detected: {challenge}")
            browser.close()
            playwright.stop()
            return False

        # Try multiple selectors for the Message button. LinkedIn UI changes frequently.
        # First try the standard aria-label button
        msg_btn = page.query_selector('button[aria-label*="Message"]')
        if not msg_btn:
            # Fallback: Look for a button or link containing exactly the text "Message"
            msg_btn = page.query_selector('text="Message"')

        if not msg_btn:
            logger.print_text(
                f"[DM] No Message button for {lead.get('name')} — maybe not connected?"
            )
            browser.close()
            playwright.stop()
            return False

        # Force click to bypass any premium upsell banners covering the button
        msg_btn.click(force=True)
        page.wait_for_timeout(random.randint(1000, 2000))

        msg_box = page.query_selector('div[role="textbox"]')
        if not msg_box:
            logger.print_text(f"[DM] Could not find message box for {lead.get('name')}")
            browser.close()
            playwright.stop()
            return False

        msg_box.click()
        page.wait_for_timeout(int(jitter_delay(1) * 1000))
        page.keyboard.type(dm_text, delay=random.randint(30, 80))
        page.wait_for_timeout(random.randint(500, 1000))
        page.keyboard.press("Enter")

        page.wait_for_timeout(random.randint(1000, 2000))
        browser.close()
        playwright.stop()

        logger.print_text(f"[DM] Sent Step {step} to {lead.get('name')}")
        log_activity(lead["id"], "dm_sent", f"Step {step}: {dm_text[:200]}")
        update_lead_dm_sent(lead["id"], step)
        return True

    except Exception as e:
        logger.print_text(f"[DM] Error sending to {lead.get('name')}: {e}")
        import traceback

        traceback.print_exc()
        return False


def is_quiet_mode() -> bool:
    """Check if quiet mode is enabled (for JSON output)."""
    return logger.is_quiet()


def run_sequence_step():
    """Run one step of the sequence for all active leads."""
    from salesbud.database import get_config

    quiet = is_quiet_mode()
    dms_per_hour = int(get_config("dms_per_hour") or 8)
    dms_per_day = int(get_config("dms_per_day") or 50)
    delay_min = int(get_config("delay_minutes") or 5)
    delay_var = int(get_config("delay_variance") or 10)

    # First, check for newly connected leads and start their sequences
    newly_connected = get_newly_connected_leads()
    if newly_connected:
        if not quiet:
            logger.print_text(
                f"\n[Sequence] Starting sequences for {len(newly_connected)} newly connected leads"
            )
        for lead in newly_connected[:dms_per_hour]:
            start_sequence_for_lead(lead["id"])
        return

    # Then handle leads already in the sequence
    leads = get_leads_due_for_step(min_days=3)

    if not leads:
        if not quiet:
            logger.print_text("No leads due for next sequence step.")
        return

    if not quiet:
        logger.print_text(f"\n=== Sequence Step ===")
        logger.print_text(f"Leads due for next step: {len(leads)}")
        logger.print_text(f"Rate limit: {dms_per_hour} DMs/hour, {dms_per_day} DMs/day")

    for i, lead in enumerate(leads):
        if i >= dms_per_hour:
            if not quiet:
                logger.print_text(f"Rate limit reached ({dms_per_hour}/hour). Stopping.")
            break

        next_step = lead["sequence_step"] + 1
        if next_step > 5:
            update_lead_status(lead["id"], "completed", sequence_step=5)
            if not quiet:
                logger.print_text(f"Lead {lead['id']} ({lead.get('name')}) completed sequence.")
            continue

        if i > 0:
            delay = delay_min + random.randint(0, delay_var)
            if not quiet:
                logger.print_text(f"Waiting {delay} minutes before next DM...")

        send_dm(lead, next_step)

    if not quiet:
        logger.print_text(f"\n=== Sequence Step Complete ===")


def start_sequence_for_lead(lead_id: int) -> bool:
    """Start the sequence for a new lead (send Step 1)."""
    lead = get_lead_by_id(lead_id)
    if not lead:
        logger.print_text(f"Lead {lead_id} not found.")
        return False

    update_lead_status(lead_id, "active", sequence_step=0)
    send_dm(lead, step=1)
    update_lead_status(lead_id, "active", sequence_step=1)
    return True


def simulate_reply(lead_id: int, reply_type: str = "positive"):
    """Simulate a reply from a lead (for testing)."""
    lead = get_lead_by_id(lead_id)
    if not lead:
        logger.print_text(f"Lead {lead_id} not found.")
        return

    if reply_type == "positive":
        new_status = "replied"
        reply_text = "Yes, I'd love to chat!"
    elif reply_type == "neutral":
        new_status = "paused"
        reply_text = "Thanks for reaching out."
    else:
        new_status = "paused"
        reply_text = "Not interested."

    update_lead_status(lead_id, new_status)
    log_activity(lead_id, "reply_received", f"[SIMULATED] {reply_type}: {reply_text}")

    logger.print_text(f"[SIMULATED] Lead {lead_id} ({lead.get('name')}) replied: {reply_type}")
    logger.print_text(f"[SIMULATED] Sequence paused. Status updated to: {new_status}")

    if reply_type == "positive":
        logger.print_text(f"[SIMULATED] Would send booking link...")
