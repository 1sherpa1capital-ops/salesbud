"""
LinkedIn Connection Manager
Handles connection requests and tracks acceptance status
"""

import os
import time
from typing import Any, Dict, List

from playwright.sync_api import sync_playwright

import salesbud.utils.logger as logger
from salesbud.database import (
    get_config,
    get_daily_count,
    increment_daily_count,
    is_dry_run,
    log_activity,
)
from salesbud.models.lead import get_all_leads, update_lead_status
from salesbud.utils.browser import (
    check_for_challenge,
    get_persistent_context,
    jitter_delay,
    random_delay,
    safe_goto,
)

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
LINKEDIN_SESSION_COOKIE = os.getenv("LINKEDIN_SESSION_COOKIE")

CONNECTION_NOTE_TEMPLATE = """Hi {name}, came across your profile and loved what you're building at {company}. Would love to connect!"""


def send_connection_request(
    linkedin_url: str, name: str, company: str = "", personalization_angle: str = ""
) -> bool:
    """Send a connection request to a LinkedIn profile."""
    if is_dry_run():
        if personalization_angle:
            note = personalization_angle
        else:
            note = CONNECTION_NOTE_TEMPLATE.format(
                name=name.split()[0], company=company or "your company"
            )
        logger.print_text(f"\n[DRY RUN] Would send connection request to: {name}")
        logger.print_text(f"[DRY RUN] LinkedIn URL: {linkedin_url}")
        logger.print_text(f"[DRY RUN] Note: {note}")
        return True



    from pathlib import Path
    state_dir = str(Path(__file__).parent.parent.parent.parent / "data" / "browser_state")

    playwright = None
    context = None
    try:
        playwright = sync_playwright().start()
        context, page = get_persistent_context(
            playwright, state_dir=state_dir, headless=False
        )

        if not safe_goto(page, linkedin_url, timeout=60000):
            logger.print_text(f"[Connector] Failed to navigate to {linkedin_url}")
            return False

        page.wait_for_timeout(random_delay(2000, 4000))

        challenge = check_for_challenge(page)
        if challenge:
            logger.print_text(f"[Connector] Challenge detected: {challenge}")
            return False

        # Scope search to the main top card to avoid sidebars
        top_card = page.query_selector("main section")
        connect_btn = None

        if top_card:
            connect_selectors = [
                'button[aria-label*="Connect"]',
                'button.artdeco-button--primary:has-text("Connect")',
                'button:has-text("Connect")',
            ]
            for selector in connect_selectors:
                try:
                    elements = top_card.query_selector_all(selector)
                    for el in elements:
                        if el.is_visible():
                            connect_btn = el
                            break
                    if connect_btn:
                        break
                except Exception:
                    continue

            if not connect_btn:
                # Try finding it in the More menu of the top card
                try:
                    more_buttons = top_card.query_selector_all('button[aria-label="More actions"], button[aria-label="More"]')
                    for m_btn in more_buttons:
                        if m_btn.is_visible():
                            m_btn.click()
                            page.wait_for_timeout(1000)
                            
                            # Dropdowns are often attached to the body, so query the page
                            connect_options = page.query_selector_all('div.artdeco-dropdown__content span:has-text("Connect"), div.artdeco-dropdown__content div:has-text("Connect")')
                            for c_btn in connect_options:
                                text = c_btn.inner_text().strip()
                                if text == "Connect" and c_btn.is_visible():
                                    connect_btn = c_btn
                                    break
                        if connect_btn:
                            break
                except Exception:
                    pass

        if not connect_btn:
            logger.print_text(f"[LinkedIn] Could not find Connect button for {name}")
            return False


        assert connect_btn is not None
        page.wait_for_timeout(int(jitter_delay(1.5) * 1000))
        connect_btn.click() # type: ignore

        # Add a note
        add_note_btn = page.query_selector('button[aria-label="Add a note"]')
        if add_note_btn:
            add_note_btn.click()
            page.wait_for_timeout(500)

            if personalization_angle:
                note = personalization_angle
            else:
                note = CONNECTION_NOTE_TEMPLATE.format(
                    name=name.split()[0], company=company or "your company"
                )
            note_field = page.query_selector("textarea#custom-message")
            if note_field:
                note_field.fill(note[:300]) # type: ignore
                page.wait_for_timeout(500)

        # Send the request
        send_selectors = [
            'button[aria-label="Send now"]',
            'button[aria-label="Send"]',
            'button.artdeco-button--primary:has-text("Send")',
            'button:has-text("Send")',
            'button.artdeco-button--primary:has-text("Send without a note")'
        ]

        send_btn = None
        for selector in send_selectors:
            try:
                send_btn = page.query_selector(selector)
                if send_btn and send_btn.is_visible():
                    break
            except Exception:
                continue

        if send_btn:
            send_btn.click() # type: ignore
            logger.print_text(f"[LinkedIn] ✓ Connection request sent to {name}")
            page.wait_for_timeout(2000)
            return True
        else:
            logger.print_text("[LinkedIn] Could not find Send button")
            return False

    except Exception as e:
        logger.print_text(f"[LinkedIn] Error sending connection request: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        if context:
            try:
                context.close()
            except Exception:
                pass
        if playwright:
            try:
                playwright.stop()
            except Exception:
                pass


def check_connection_status(linkedin_url: str) -> str:
    """Check if a connection request has been accepted."""
    if is_dry_run():
        return "pending"

    playwright = None
    context = None
    try:
        from pathlib import Path

        state_dir = str(
            Path(__file__).parent.parent.parent.parent / "data" / "browser_state"
        )

        playwright = sync_playwright().start()
        context, page = get_persistent_context(
            playwright, state_dir=state_dir, headless=False
        )

        page.goto(linkedin_url, timeout=60000)
        page.wait_for_timeout(3000)

        # Check for various buttons to determine status
        message_btn = page.query_selector('button[aria-label*="Message"]')
        if message_btn:
            return "connected"

        pending_btn = page.query_selector('button:has-text("Pending")')
        if pending_btn:
            return "pending"

        connect_btn = page.query_selector('button:has-text("Connect")')
        if connect_btn:
            return "not_connected"

        return "unknown"

    except Exception as e:
        logger.print_text(f"[LinkedIn] Error checking connection status: {e}")
        return "unknown"
    finally:
        if context:
            try:
                context.close()
            except Exception:
                pass
        if playwright:
            try:
                playwright.stop()
            except Exception:
                pass
    return "unknown"


def get_leads_to_connect() -> List[Dict[str, Any]]:
    """Get leads that need connection requests sent."""
    leads = get_all_leads()
    return [lead for lead in leads if lead["status"] == "new" and lead.get("linkedin_url")]


def run_connection_campaign(max_requests: int = 10, delay_seconds: int = 60):
    """Run a connection request campaign."""

    dry_run = is_dry_run()
    dms_per_day = int(get_config("dms_per_day") or 50)

    # Daily rate limit guard
    if not dry_run:
        sent_today = get_daily_count("connections")
        if sent_today >= dms_per_day:
            logger.print_text(
                f"⛔ Daily connection limit reached ({sent_today}/{dms_per_day}). Stopping."
            )
            return
        max_requests = min(max_requests, dms_per_day - sent_today)

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

    sent_count: int = 0

    for lead in leads[:max_requests]: # type: ignore
        if sent_count >= max_requests: # type: ignore
            break

        name = lead.get("name", "Unknown")
        linkedin_url = lead.get("linkedin_url", "")
        company = lead.get("company", "")

        logger.print_text(f"\n[{sent_count + 1}/{max_requests}] Connecting to: {name}") # type: ignore

        success = send_connection_request(
            linkedin_url, name, company, lead.get("personalization_angle", "")
        )

        if success:
            update_lead_status(lead["id"], "connection_requested")
            log_activity(lead["id"], "connection_sent", f"Connection request sent to {name}")
            sent_count += 1 # type: ignore
            if not dry_run:
                increment_daily_count("connections")

            if not dry_run and sent_count < max_requests: # type: ignore
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
