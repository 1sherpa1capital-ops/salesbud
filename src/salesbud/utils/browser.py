"""
Browser Stealth Utilities for Playwright
Hides automation signatures and provides human-like behavior
"""

import random
import time
import json
from typing import Optional, Dict, Any, List, Tuple, cast
from playwright.sync_api import BrowserContext, Page, Playwright, Browser, ViewportSize

STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        {0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
         description: "Portable Document Format", filename: "internal-pdf-viewer", length: 1, name: "Chrome PDF Plugin"}
    ]
});
window.chrome = {runtime: {}};
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'});
"""

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

VIEWPORT_SIZES = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1280, "height": 720},
]


def random_delay(min_ms: int = 1000, max_ms: int = 3000) -> int:
    return random.randint(min_ms, max_ms)


def jitter_delay(base_seconds: float, variance: float = 0.3) -> float:
    variance_sec = base_seconds * variance
    return max(0.5, base_seconds + random.uniform(-variance_sec, variance_sec))


def get_stealth_context(
    playwright: Playwright,
    headless: bool = True,
    session_cookie: Optional[str] = None,
) -> Tuple[BrowserContext, Browser]:
    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
    ]

    browser = playwright.chromium.launch(headless=headless, args=args)

    context = browser.new_context(
        viewport=cast(ViewportSize, random.choice(VIEWPORT_SIZES)),
        user_agent=random.choice(USER_AGENTS),
        locale="en-US",
        timezone_id="America/New_York",
    )

    if session_cookie:
        try:
            cookies = json.loads(session_cookie)
            context.add_cookies(cookies)
        except Exception:
            pass

    return context, browser


def create_stealth_page(context: BrowserContext) -> Page:
    page = context.new_page()
    page.add_init_script(STEALTH_SCRIPT)
    return page


def safe_goto(page: Page, url: str, timeout: int = 60000, retries: int = 2) -> bool:
    for attempt in range(retries):
        try:
            page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            page.wait_for_timeout(random_delay(1000, 2000))
            return True
        except Exception as e:
            if "ERR_TOO_MANY_REDIRECTS" in str(e) and attempt < retries - 1:
                page.wait_for_timeout(random_delay(3000, 5000))
                continue
            elif attempt < retries - 1:
                continue
            return False
    return False


def check_for_challenge(page: Page) -> Optional[str]:
    url = page.url.lower()
    content = page.content().lower()

    indicators = ["captcha", "challenge", "security check", "verify you're human"]
    for indicator in indicators:
        if indicator in url or indicator in content:
            return indicator
    return None


def human_like_click(page: Page, selector: str):
    page.wait_for_timeout(random_delay(300, 800))
    page.click(selector)
    page.wait_for_timeout(random_delay(500, 1000))


def human_like_type(page: Page, selector: str, text: str):
    page.click(selector)
    page.wait_for_timeout(random_delay(200, 400))
    for char in text:
        page.keyboard.press(char)
        time.sleep(random.randint(30, 80) / 1000)
    page.wait_for_timeout(random_delay(300, 600))
