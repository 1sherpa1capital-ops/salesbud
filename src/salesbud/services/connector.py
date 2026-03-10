"""
LinkedIn Connection Manager
Handles connection requests and tracks acceptance status
"""

import salesbud.utils.logger as logger
import os
import json
import time
from typing import List, Dict, Any, Optional
from playwright.sync_api import sync_playwright

from salesbud.utils.browser import (
    get_stealth_context,
    create_stealth_page,
    safe_goto,
    check_for_challenge,
    random_delay,
    jitter_delay,
)
from salesbud.database import is_dry_run, log_activity
from salesbud.models.lead import get_all_leads, update_lead_status

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
LINKEDIN_SESSION_COOKIE = os.getenv("LINKEDIN_SESSION_COOKIE")

CONNECTION_NOTE_TEMPLATE = """Hi {name}, came across your profile and loved what you're building at {company}. Would love to connect!"""


def send_connection_request(linkedin_url: str, name: str, company: str = "") -> bool:
    """Send a connection request to a LinkedIn profile."""
    if is_dry_run():
        note = CONNECTION_NOTE_TEMPLATE.format(
            name=name.split()[0], company=company or "your company"
        )
        logger.print_text(f"\n[DRY RUN] Would send connection request to: {name}")
        logger.print_text(f"[DRY RUN] LinkedIn URL: {linkedin_url}")
        logger.print_text(f"[DRY RUN] Note: {note}")
        return True

    session_cookie = os.getenv("LINKEDIN_SESSION_COOKIE")

    try:
        playwright = sync_playwright().start()
        context, browser = get_stealth_context(
            playwright, headless=True, session_cookie=session_cookie
        )
        page = create_stealth_page(context)

        if not safe_goto(page, linkedin_url, timeout=60000):
            logger.print_text(f"[Connector] Failed to navigate to {linkedin_url}")
            browser.close()
            playwright.stop()
            return False

        page.wait_for_timeout(random_delay(2000, 4000))

        challenge = check_for_challenge(page)
        if challenge:
            logger.print_text(f"[Connector] Challenge detected: {challenge}")
            browser.close()
            playwright.stop()
            return False

        # Look for Connect button
        connect_selectors = [
            'button[aria-label*="Connect"]',
            'button.artdeco-button--primary:has-text("Connect")',
            'button:has-text("Connect")',
        ]

        connect_btn = None
        for selector in connect_selectors:
            try:
                connect_btn = page.query_selector(selector)
                if connect_btn and connect_btn.is_visible():
                    break
            except:
                continue

        if not connect_btn:
            logger.print_text(f"[LinkedIn] Could not find Connect button for {name}")
            browser.close()
            playwright.stop()
            return False

        page.wait_for_timeout(int(jitter_delay(1.5) * 1000))
        connect_btn.click()
        page.wait_for_timeout(1000)

        # Add a note
        add_note_btn = page.query_selector('button[aria-label="Add a note"]')
        if add_note_btn:
            add_note_btn.click()
            page.wait_for_timeout(500)

            note = CONNECTION_NOTE_TEMPLATE.format(
                name=name.split()[0], company=company or "your company"
            )
            note_field = page.query_selector("textarea#custom-message")
            if note_field:
                note_field.fill(note[:300])
                page.wait_for_timeout(500)

        # Send the request
        send_btn = page.query_selector('button[aria-label="Send now"]')
        if send_btn:
            send_btn.click()
            logger.print_text(f"[LinkedIn] ✓ Connection request sent to {name}")
            page.wait_for_timeout(2000)
            browser.close()
            playwright.stop()
            return True
        else:
            logger.print_text(f"[LinkedIn] Could not find Send button")
            browser.close()
            playwright.stop()
            return False

    except Exception as e:
        logger.print_text(f"[LinkedIn] Error sending connection request: {e}")
        import traceback

        traceback.print_exc()
        return False


def check_connection_status(linkedin_url: str) -> str:
    """Check if a connection request has been accepted."""
    if is_dry_run():
        return "pending"

    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        if LINKEDIN_SESSION_COOKIE:
            cookies = json.loads(LINKEDIN_SESSION_COOKIE)
            context.add_cookies(cookies)

        page.goto(linkedin_url, timeout=60000)
        page.wait_for_timeout(3000)

        # Check for various buttons to determine status
        message_btn = page.query_selector('button[aria-label*="Message"]')
        if message_btn:
            browser.close()
            playwright.stop()
            return "connected"

        pending_btn = page.query_selector('button:has-text("Pending")')
        if pending_btn:
            browser.close()
            playwright.stop()
            return "pending"

        connect_btn = page.query_selector('button:has-text("Connect")')
        if connect_btn:
            browser.close()
            playwright.stop()
            return "not_connected"

        browser.close()
        playwright.stop()
        return "unknown"

    except Exception as e:
        logger.print_text(f"[LinkedIn] Error checking connection status: {e}")
        return "unknown"


def get_leads_to_connect() -> List[Dict[str, Any]]:
    """Get leads that need connection requests sent."""
    leads = get_all_leads()
    return [lead for lead in leads if lead["status"] == "new" and lead.get("linkedin_url")]


def run_connection_campaign(max_requests: int = 10, delay_seconds: int = 60):
    """Run a connection request campaign."""
    from salesbud.database import get_config

    dry_run = is_dry_run()

    logger.print_text(f"\n{'=' * 60}")
    logger.print_text("LinkedIn Connection Campaign")
    logger.print_text(f"{'=' * 60}")
    logger.print_text(f"Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")
    logger.print_text(f"Max requests: {max_requests}")
    logger.print_text(f"Delay between requests: {delay_seconds}s")

    leads = get_leads_to_connect()

    if not leads:
        logger.print_text("\nNo leads waiting for connection requests.")
        return

    logger.print_text(f"\nFound {len(leads)} leads to connect")
    logger.print_text("-" * 60)

    sent_count = 0

    for lead in leads[:max_requests]:
        if sent_count >= max_requests:
            break

        name = lead.get("name", "Unknown")
        linkedin_url = lead.get("linkedin_url", "")
        company = lead.get("company", "")

        logger.print_text(f"\n[{sent_count + 1}/{max_requests}] Connecting to: {name}")

        success = send_connection_request(linkedin_url, name, company)

        if success:
            update_lead_status(lead["id"], "connection_requested")
            log_activity(lead["id"], "connection_sent", f"Connection request sent to {name}")
            sent_count += 1

            if not dry_run and sent_count < max_requests:
                logger.print_text(f"Waiting {delay_seconds} seconds before next request...")
                time.sleep(delay_seconds)
        else:
            log_activity(
                lead["id"], "connection_failed", f"Failed to send connection request to {name}"
            )

    logger.print_text(f"\n{'=' * 60}")
    logger.print_text(f"Campaign complete. Sent {sent_count} connection requests.")
    logger.print_text(f"{'=' * 60}")


def check_pending_connections():
    """Check status of pending connection requests."""
    leads = get_all_leads()
    pending = [lead for lead in leads if lead["status"] == "connection_requested"]

    if not pending:
        logger.print_text("No pending connection requests to check.")
        return

    logger.print_text(f"\nChecking {len(pending)} pending connections...")

    connected_count = 0

    for lead in pending:
        linkedin_url = lead.get("linkedin_url", "")
        name = lead.get("name", "Unknown")

        status = check_connection_status(linkedin_url)

        if status == "connected":
            logger.print_text(f"  ✓ {name} accepted connection")
            update_lead_status(lead["id"], "connected")
            log_activity(lead["id"], "connection_accepted", f"Connection accepted by {name}")
            connected_count += 1
        elif status == "pending":
            logger.print_text(f"  ⏳ {name} still pending")
        elif status == "not_connected":
            logger.print_text(f"  ✗ {name} declined or not connected")
            update_lead_status(lead["id"], "connection_declined")
            log_activity(lead["id"], "connection_declined", f"Connection declined by {name}")

    logger.print_text(f"\n{connected_count} new connections ready for DM sequence!")
