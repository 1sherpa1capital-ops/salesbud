"""
LinkedIn Connection Manager - Optimized for single browser session
"""

import os
import time
from typing import Any, Dict, List

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

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
from salesbud.utils.paths import get_browser_state_dir

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
LINKEDIN_SESSION_COOKIE = os.getenv("LINKEDIN_SESSION_COOKIE")

CONNECTION_NOTE_TEMPLATE = """Hi {name}, came across your profile and loved what you're building at {company}. Would love to connect!"""


class LinkedInConnector:
    """
    Manages LinkedIn connections with persistent browser session.

    This class handles the browser lifecycle and provides methods for
    sending connection requests to LinkedIn profiles.

    Attributes:
        state_dir: Directory for browser state persistence
        headless: Whether to run browser in headless mode
        playwright: Playwright instance
        context: Browser context
        page: Active page instance
    """

    def __init__(self, state_dir: str, headless: bool = False):
        self.state_dir = state_dir
        self.headless = headless
        self.playwright: Playwright = None
        self.context: BrowserContext = None
        self.page: Page = None

    def start(self) -> bool:
        """Initialize browser session."""
        try:
            self.playwright = sync_playwright().start()
            self.context, self.page = get_persistent_context(
                self.playwright, state_dir=self.state_dir, headless=self.headless
            )
            logger.print_text("[Connector] Browser session started")
            return True
        except (ConnectionError, TimeoutError) as e:
            logger.print_text(f"[Connector] Network error starting browser: {e}")
            return False
        except (RuntimeError, OSError) as e:
            logger.print_text(f"[Connector] Unexpected error starting browser: {type(e).__name__}")
            import logging

            logging.error(f"Browser start error: {e}", exc_info=True)
            return False

    def stop(self):
        """Clean up browser session."""
        if self.context:
            try:
                self.context.close()
            except Exception:
                pass
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                pass
        logger.print_text("[Connector] Browser session closed")

    def send_connection(
        self, linkedin_url: str, name: str, company: str = "", personalization_angle: str = ""
    ) -> bool:
        """
        Send a single connection request to a LinkedIn profile.

        Args:
            linkedin_url: Full LinkedIn profile URL
            name: Person's name for personalization
            company: Company name for connection note
            personalization_angle: Custom message to use instead of template

        Returns:
            bool: True if request sent successfully, False otherwise

        Raises:
            ValueError: If linkedin_url is invalid
        """
        if not self.page:
            logger.print_text("[Connector] No active browser session")
            return False

        try:
            if not safe_goto(self.page, linkedin_url, timeout=60000):
                logger.print_text(f"[Connector] Failed to navigate to {linkedin_url}")
                return False

            self.page.wait_for_timeout(random_delay(2000, 4000))

            challenge = check_for_challenge(self.page)
            if challenge:
                logger.print_text(f"[Connector] Challenge detected: {challenge}")
                return False

            # Scope search to the main top card
            top_card = self.page.query_selector("main section")
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
                    except (AttributeError, TypeError):
                        continue
                    except RuntimeError:
                        continue

                if not connect_btn:
                    # Try finding it in the More menu
                    try:
                        more_buttons = top_card.query_selector_all(
                            'button[aria-label="More actions"], button[aria-label="More"]'
                        )
                        for m_btn in more_buttons:
                            if m_btn.is_visible():
                                m_btn.click()
                                self.page.wait_for_timeout(1000)

                                connect_options = self.page.query_selector_all(
                                    'div.artdeco-dropdown__content span:has-text("Connect"), div.artdeco-dropdown__content div:has-text("Connect")'
                                )
                                for c_btn in connect_options:
                                    text = c_btn.inner_text().strip()
                                    if text == "Connect" and c_btn.is_visible():
                                        connect_btn = c_btn
                                        break
                            if connect_btn:
                                break
                    except (AttributeError, TypeError):
                        pass
                    except RuntimeError:
                        pass

            if not connect_btn:
                logger.print_text(f"[LinkedIn] Could not find Connect button for {name}")
                return False

            self.page.wait_for_timeout(int(jitter_delay(1.5) * 1000))
            connect_btn.click()

            # Add a note
            add_note_btn = self.page.query_selector('button[aria-label="Add a note"]')
            if add_note_btn:
                add_note_btn.click()
                self.page.wait_for_timeout(500)

                if personalization_angle:
                    note = personalization_angle
                else:
                    note = CONNECTION_NOTE_TEMPLATE.format(
                        name=name.split()[0], company=company or "your company"
                    )
                note_field = self.page.query_selector("textarea#custom-message")
                if note_field:
                    note_field.fill(note[:300])
                    self.page.wait_for_timeout(500)

            # Send the request
            send_selectors = [
                'button[aria-label="Send now"]',
                'button[aria-label="Send"]',
                'button.artdeco-button--primary:has-text("Send")',
                'button:has-text("Send")',
                'button.artdeco-button--primary:has-text("Send without a note")',
            ]

            send_btn = None
            for selector in send_selectors:
                try:
                    send_btn = self.page.query_selector(selector)
                    if send_btn and send_btn.is_visible():
                        break
                except (AttributeError, TypeError):
                    continue
                except RuntimeError:
                    continue

            if send_btn:
                send_btn.click()
                logger.print_text(f"[LinkedIn] ✓ Connection request sent to {name}")
                self.page.wait_for_timeout(2000)
                return True
            else:
                logger.print_text("[LinkedIn] Could not find Send button")
                return False

        except (TimeoutError, ConnectionError) as e:
            logger.print_text(f"[LinkedIn] Network error sending connection request: {e}")
            return False
        except Exception as e:
            logger.print_text(
                f"[LinkedIn] Unexpected error sending connection request: {type(e).__name__}"
            )
            import logging

            logging.error(f"Connection error: {e}", exc_info=True)
            return False


def run_connection_campaign(max_requests: int = 10, delay_seconds: int = 60):
    """
    Run a connection request campaign with single browser session.

    Args:
        max_requests: Maximum number of connection requests to send
        delay_seconds: Delay between requests in seconds

    Returns:
        None

    Raises:
        ValueError: If max_requests is invalid
    """

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

    # Start single browser session for all connections
    state_dir = str(get_browser_state_dir())
    connector = LinkedInConnector(state_dir=state_dir, headless=False)

    if not connector.start():
        logger.print_text("❌ Failed to start browser session")
        return

    sent_count = 0

    try:
        for lead in leads[:max_requests]:
            if sent_count >= max_requests:
                break

            name = lead.get("name", "Unknown")
            linkedin_url = lead.get("linkedin_url", "")
            company = lead.get("company", "")

            logger.print_text(f"\n[{sent_count + 1}/{max_requests}] Connecting to: {name}")

            success = connector.send_connection(
                linkedin_url, name, company, lead.get("personalization_angle", "")
            )

            if success:
                update_lead_status(lead["id"], "connection_requested")
                log_activity(lead["id"], "connection_sent", f"Connection request sent to {name}")
                sent_count += 1
                if not dry_run:
                    increment_daily_count("connections")

                if not dry_run and sent_count < max_requests:
                    logger.print_text(f"Waiting {delay_seconds} seconds before next request...")
                    time.sleep(delay_seconds)
            else:
                log_activity(
                    lead["id"], "connection_failed", f"Failed to send connection request to {name}"
                )
                # Don't stop on failure, but add extra delay
                if not dry_run and sent_count < max_requests:
                    logger.print_text(f"Waiting {delay_seconds * 2}s after failure...")
                    time.sleep(delay_seconds * 2)

    finally:
        # Always close browser session
        connector.stop()

    logger.print_text(f"\n{'=' * 60}")
    logger.print_text(f"Campaign complete. Sent {sent_count} connection requests.")
    logger.print_text(f"{'=' * 60}")


def get_leads_to_connect() -> List[Dict[str, Any]]:
    """Get leads that need connection requests sent."""
    leads = get_all_leads()
    return [lead for lead in leads if lead["status"] == "new" and lead.get("linkedin_url")]


def check_pending_connections():
    """
    Check status of pending connection requests.

    Iterates through all leads with 'connection_requested' status
    and checks if they have been accepted, declined, or are still pending.

    Returns:
        None

    Raises:
        ValueError: If linkedin_url is invalid
    """
    leads = get_all_leads()
    pending = [lead for lead in leads if lead["status"] == "connection_requested"]

    if not pending:
        logger.print_text("No pending connection requests to check.")
        return

    logger.print_text(f"\nChecking {len(pending)} pending connections...")

    # Use single browser session for checking
    state_dir = str(get_browser_state_dir())
    connector = LinkedInConnector(state_dir=state_dir, headless=False)

    if not connector.start():
        logger.print_text("❌ Failed to start browser for checking")
        return

    connected_count = 0

    try:
        for lead in pending:
            linkedin_url = lead.get("linkedin_url", "")
            name = lead.get("name", "Unknown")

            # Navigate and check status
            if not safe_goto(connector.page, linkedin_url, timeout=60000):
                logger.print_text(f"  ⚠️ Could not check {name}")
                continue

            connector.page.wait_for_timeout(3000)

            # Check for various buttons
            message_btn = connector.page.query_selector('button[aria-label*="Message"]')
            if message_btn:
                logger.print_text(f"  ✓ {name} accepted connection")
                update_lead_status(lead["id"], "connected")
                log_activity(lead["id"], "connection_accepted", f"Connection accepted by {name}")
                connected_count += 1
                continue

            pending_btn = connector.page.query_selector('button:has-text("Pending")')
            if pending_btn:
                logger.print_text(f"  ⏳ {name} still pending")
                continue

            connect_btn = connector.page.query_selector('button:has-text("Connect")')
            if connect_btn:
                logger.print_text(f"  ✗ {name} declined or not connected")
                update_lead_status(lead["id"], "connection_declined")
                log_activity(lead["id"], "connection_declined", f"Connection declined by {name}")

    finally:
        connector.stop()

    logger.print_text(f"\nSummary: {connected_count}/{len(pending)} connections accepted")
