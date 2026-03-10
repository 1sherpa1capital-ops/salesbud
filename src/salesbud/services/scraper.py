"""
LinkedIn Lead Scraper using Playwright
Real browser automation with dry-run fallback
"""

import salesbud.utils.logger as logger
import os
import re
import json
from typing import List, Optional, Dict, Any
from playwright.sync_api import sync_playwright

from salesbud.database import is_dry_run, log_activity
from salesbud.models.lead import add_lead
from salesbud.utils.browser import (
    get_stealth_context,
    create_stealth_page,
    safe_goto,
    check_for_challenge,
    random_delay,
)

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
LINKEDIN_SESSION_COOKIE = os.getenv("LINKEDIN_SESSION_COOKIE")


def login_to_linkedin(page, context) -> bool:
    """Login to LinkedIn using session cookie or credentials."""
    if LINKEDIN_SESSION_COOKIE:
        try:
            cookies = json.loads(LINKEDIN_SESSION_COOKIE)
            context.add_cookies(cookies)
            logger.print_text("[LinkedIn] Using session cookie")
            return True
        except json.JSONDecodeError as e:
            logger.print_text(f"[LinkedIn] Failed to parse session cookie: {e}")
        except Exception as e:
            logger.print_text(f"[LinkedIn] Error adding cookies: {e}")

    if LINKEDIN_EMAIL and LINKEDIN_PASSWORD:
        page.goto("https://www.linkedin.com/login")
        page.fill("#username", LINKEDIN_EMAIL)
        page.fill("#password", LINKEDIN_PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        logger.print_text("[LinkedIn] Logged in with credentials")
        return True

    logger.print_text("[LinkedIn] No credentials found, cannot login")
    return False


def scrape_linkedin_search(
    query: str, location: Optional[str] = None, max_leads: int = 50
) -> List[Dict[str, Any]]:
    """Scrape leads from LinkedIn search."""
    leads = []
    try:
        # Build search URL
        base_url = "https://www.linkedin.com/search/results/people"
        keywords = query
        if location:
            keywords = f"{query} {location}"
        params = f"?keywords={keywords.replace(' ', '%20')}"
        params += "&origin=GLOBAL_SEARCH_HEADER"
        url = base_url + params

        playwright = sync_playwright().start()
        context, browser = get_stealth_context(
            playwright, headless=True, session_cookie=LINKEDIN_SESSION_COOKIE
        )
        page = create_stealth_page(context)

        logger.print_text(f"[LinkedIn] Navigating to: {url}")

        if not safe_goto(page, url, timeout=60000):
            logger.print_text("[LinkedIn] Failed to navigate to search page")
            browser.close()
            playwright.stop()
            return leads

        page.wait_for_timeout(random_delay(2000, 4000))

        # Check for security challenge
        challenge = check_for_challenge(page)
        if challenge:
            logger.print_text(f"[LinkedIn] Security challenge detected: {challenge}")
            browser.close()
            playwright.stop()
            return []
        # Extract leads from HTML
        html = page.content()
        profile_ids = re.findall(r"/in/([a-zA-Z0-9-]+)", html)
        profile_ids = list(dict.fromkeys(profile_ids))

        logger.print_text(f"[LinkedIn] Found {len(profile_ids)} unique profiles")

        for profile_id in profile_ids[:max_leads]:
            try:
                profile_url = f"https://www.linkedin.com/in/{profile_id}/"
                name = "Unknown"
                headline = ""
                company = ""

                # Try to extract name from anchor tags
                context_pattern = (
                    rf'<a[^>]*href="https://www\.linkedin\.com/in/{profile_id}/?"[^>]*>(.*?)</a>'
                )
                context_match = re.search(context_pattern, html, re.DOTALL)

                if context_match:
                    anchor_content = context_match.group(1)
                    clean_text = re.sub(r"<[^>]+>", "", anchor_content)
                    if clean_text.strip():
                        name = clean_text.strip()[:50]

                # Try to find headline
                headline_match = re.search(
                    rf'"publicIdentifier":"{profile_id}"[^}}]*"headline":"([^"]+)"', html
                )
                if headline_match:
                    headline = headline_match.group(1)
                    if " at " in headline:
                        company = headline.split(" at ")[-1].strip()

                lead = {
                    "name": name,
                    "headline": headline,
                    "company": company,
                    "linkedin_url": profile_url,
                    "location": location or "",
                }

                if lead["name"] and lead["name"] != "Unknown":
                    leads.append(lead)
                    logger.print_text(f"  - {lead['name']}")

            except Exception as e:
                logger.print_text(f"  [Error] Failed to extract lead: {e}")
                continue

        browser.close()
        playwright.stop()

    except Exception as e:
        logger.print_text(f"[LinkedIn] Scraping error: {e}")
        import traceback

        traceback.print_exc()

    return leads


def is_quiet_mode() -> bool:
    """Check if quiet mode is enabled (for JSON output)."""
    return logger.is_quiet()


def scrape_leads(query: str, location: Optional[str] = None, max_leads: int = 50) -> int:
    """Scrape leads from LinkedIn - main entry point."""
    quiet = is_quiet_mode()
    if not quiet:
        logger.print_text(f"\n=== LinkedIn Lead Scraper ===")
        logger.print_text(f"Query: {query}")
        logger.print_text(f"Location: {location or 'Any'}")
        logger.print_text(f"Max leads: {max_leads}")

    has_creds = bool(LINKEDIN_SESSION_COOKIE or (LINKEDIN_EMAIL and LINKEDIN_PASSWORD))

    if is_dry_run() or not has_creds:
        if is_dry_run() and not quiet:
            logger.print_text("Dry run: True")
        if not has_creds and not quiet:
            logger.print_text("No LinkedIn credentials - running in demo mode")

        if not quiet:
            logger.print_text("\n[DRY RUN] Example leads (simulated):")

        sample_leads = [
            {
                "name": "Sarah Chen",
                "headline": "CEO at TechFlow",
                "company": "TechFlow",
                "location": "Austin, TX",
            },
            {
                "name": "Mike Johnson",
                "headline": "VP Marketing at GrowthCo",
                "company": "GrowthCo",
                "location": "Austin, TX",
            },
            {
                "name": "Emily Davis",
                "headline": "Founder @ ScaleUp",
                "company": "ScaleUp",
                "location": "Austin, TX",
            },
            {
                "name": "Alex Rodriguez",
                "headline": "Head of Sales at B2BForce",
                "company": "B2BForce",
                "location": "Austin, TX",
            },
            {
                "name": "Jordan Lee",
                "headline": "Marketing Director at StartupX",
                "company": "StartupX",
                "location": "Austin, TX",
            },
        ]

        for lead in sample_leads[:max_leads]:
            linkedin_url = f"https://www.linkedin.com/in/{lead['name'].lower().replace(' ', '-')}"
            lead_id = add_lead(
                linkedin_url=linkedin_url,
                name=lead["name"],
                headline=lead["headline"],
                company=lead["company"],
                location=lead["location"],
            )
            if not quiet:
                logger.print_text(f"  - Added: {lead['name']}")
            log_activity(lead_id, "lead_added", f"Scraped: {lead['name']} at {lead['company']}")

        return len(sample_leads[:max_leads])

    # Real scraping
    if not quiet:
        logger.print_text("LinkedIn credentials: Found")
    leads = scrape_linkedin_search(query, location, max_leads)

    for lead in leads:
        lead_id = add_lead(
            linkedin_url=lead["linkedin_url"],
            name=lead["name"],
            headline=lead["headline"],
            company=lead["company"],
            location=lead.get("location", ""),
        )
        log_activity(lead_id, "lead_added", f"Scraped: {lead['name']} at {lead['company']}")

    return len(leads)


def get_scraper_status() -> Dict[str, int]:
    """Get current scraper status and stats."""
    from salesbud.models.lead import get_all_leads

    leads = get_all_leads()
    total = len(leads)
    new_count = sum(1 for l in leads if l["status"] == "new")
    active_count = sum(1 for l in leads if l["status"] == "active")
    completed = sum(1 for l in leads if l["status"] in ("completed", "booked"))

    return {"total": total, "new": new_count, "active": active_count, "completed": completed}
