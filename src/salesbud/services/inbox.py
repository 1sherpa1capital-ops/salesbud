"""
Scan LinkedIn inbox for new replies from leads in our sequences.
"""

import salesbud.utils.logger as logger
import os
import json
import random
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright


def check_linkedin_inbox() -> List[Dict[str, Any]]:
    """
    Use Playwright to navigate to LinkedIn messaging.
    For each thread, check if the sender is one of our tracked leads.
    Return list of {"lead_id": int, "name": str, "message": str, "detected_intent": str}
    """
    from salesbud.models.lead import get_all_leads, update_lead_status
    from salesbud.database import log_activity

    replies_found = []

    # Build lookup: lead name (lowercase) → lead dict
    leads = get_all_leads()
    # Only look for replies from leads in active sequences
    active_statuses = {"active", "connection_requested", "connected", "replied"}
    tracked_by_name = {}
    for lead in leads:
        if lead.get("status") in active_statuses and lead.get("name"):
            tracked_by_name[lead["name"].lower()] = lead

    if not tracked_by_name:
        logger.print_text("[Inbox] No active leads to check replies for.")
        return []

    session_cookie = os.getenv("LINKEDIN_SESSION_COOKIE")

    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        )

        if session_cookie:
            try:
                context.add_cookies(json.loads(session_cookie))
            except Exception as e:
                logger.print_text(f"[Inbox] Could not parse session cookie: {e}")
                browser.close()
                playwright.stop()
                return []
        else:
            logger.print_text("[Inbox] No LINKEDIN_SESSION_COOKIE set — cannot check inbox.")
            browser.close()
            playwright.stop()
            return []

        page = context.new_page()

        logger.print_text("[Inbox] Navigating to LinkedIn messaging...")
        page.goto("https://www.linkedin.com/messaging/", timeout=60000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(random.randint(3000, 5000))

        # Check if we're actually logged in (redirect to login = session expired)
        if "login" in page.url or "authwall" in page.url:
            logger.print_text("[Inbox] LinkedIn session expired. Refresh LINKEDIN_SESSION_COOKIE in .env")
            browser.close()
            playwright.stop()
            return []

        # Find conversation threads in the messaging sidebar
        thread_selectors = [
            "li.msg-conversation-listitem",
            "div.msg-conversations-container__convo-item",
            "li[data-control-name='overlay.open_conversation']",
            ".msg-conversation-card",
        ]

        threads = []
        for selector in thread_selectors:
            threads = page.query_selector_all(selector)
            if threads:
                break

        logger.print_text(f"[Inbox] Found {len(threads)} conversation threads")

        for thread in threads:
            try:
                # Extract sender name
                name_el = (
                    thread.query_selector("h3")
                    or thread.query_selector(".msg-conversation-card__participant-names")
                    or thread.query_selector("span.truncate")
                )
                # Extract message snippet
                snippet_el = (
                    thread.query_selector("p")
                    or thread.query_selector(".msg-conversation-card__message-snippet")
                    or thread.query_selector("span.msg-conversation-listitem__message-snippet")
                )

                if not name_el:
                    continue

                sender_name = name_el.inner_text().strip().lower()
                message = snippet_el.inner_text().strip() if snippet_el else ""

                # Match against our tracked leads by name (partial match)
                matched_lead = None
                for tracked_name, lead in tracked_by_name.items():
                    # Match if their full name or first name appears in thread name
                    first_name = tracked_name.split()[0] if tracked_name else ""
                    if tracked_name in sender_name or (first_name and first_name in sender_name):
                        matched_lead = lead
                        break

                if not matched_lead:
                    continue

                # Skip if we already know they replied
                if matched_lead.get("status") == "replied":
                    continue

                intent = classify_intent(message)

                logger.print_text(
                    f"[Inbox] Reply detected from {matched_lead['name']} "
                    f"(intent: {intent}): {message[:60]}..."
                )

                # Update lead — pause sequence on any reply
                update_lead_status(matched_lead["id"], "replied")
                log_activity(
                    matched_lead["id"],
                    "reply_received",
                    f"[AUTO-DETECTED] intent={intent}: {message[:300]}",
                )

                replies_found.append(
                    {
                        "lead_id": matched_lead["id"],
                        "name": matched_lead["name"],
                        "message": message,
                        "detected_intent": intent,
                    }
                )

            except Exception as e:
                # Don't let one thread error kill the whole scan
                continue

        browser.close()
        playwright.stop()

    except Exception as e:
        logger.print_text(f"[Inbox] Error checking LinkedIn inbox: {e}")
        import traceback

        traceback.print_exc()

    if replies_found:
        logger.print_text(f"[Inbox] Found {len(replies_found)} replies. Sequences paused for those leads.")
    else:
        logger.print_text("[Inbox] No new replies found.")

    return replies_found


def classify_intent(message: str) -> str:
    """Classify reply intent based on keywords."""
    message_lower = message.lower()

    positive_keywords = [
        "yes",
        "love",
        "interested",
        "schedule",
        "call",
        "chat",
        "sure",
        "definitely",
        "sounds good",
        "let's talk",
        "happy to",
        "would love",
        "open to",
        "tell me more",
    ]
    negative_keywords = [
        "no",
        "not interested",
        "stop",
        "remove",
        "unsubscribe",
        "leave me alone",
        "do not contact",
        "don't contact",
        "not for me",
        "not now",
        "pass",
    ]

    for kw in negative_keywords:
        if kw in message_lower:
            return "negative"
    for kw in positive_keywords:
        if kw in message_lower:
            return "positive"

    return "neutral"
