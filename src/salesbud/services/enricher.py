"""
Company enrichment service using Crawl4AI
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

import salesbud.utils.logger as logger


async def enrich_company(company_url: str) -> Dict[str, Any]:
    """
    Scrape company homepage and return structured data.
    Extracts: tagline (h1), description (meta), size signals, hiring signals
    """
    try:
        from crawl4ai import AsyncWebCrawler

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=company_url)  # type: ignore[attr-defined]

            if not result or not hasattr(result, "success") or not result.success:  # type: ignore[attr-defined]
                return {}

            html = result.html if hasattr(result, "html") else str(result)  # type: ignore[attr-defined]

            company_description = _extract_meta_description(html)
            tagline = _extract_h1_tagline(html)
            size_signals = _extract_size_signals(html)
            hiring_signals = _extract_hiring_signals(html)

            return {
                "company_description": company_description,
                "company_tagline": tagline,
                "company_size_est": size_signals,
                "buying_signals": hiring_signals,
            }
    except ImportError:
        logger.print_text("[Enrich] Crawl4AI not installed. Run: pip install crawl4ai")
        return {}
    except Exception as e:
        logger.print_text(f"[Enrich] Error enriching {company_url}: {e}")
        return {}


def _extract_meta_description(html: str) -> Optional[str]:
    """Extract meta description from HTML."""
    import re

    pattern = r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']'
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        return match.group(1)
    pattern = r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']description["\']'
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _extract_h1_tagline(html: str) -> Optional[str]:
    """Extract h1 tag content as company tagline."""
    import re

    pattern = r"<h1[^>]*>([^<]+)</h1>"
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _extract_size_signals(html: str) -> Optional[str]:
    """Extract company size signals from page content."""
    import re

    size_indicators = [
        r"(\d{1,3}(?:,\d{3})?)\s*(?:employees|workers|team members)",
        r"(?:team of|company with)\s*(\d+)",
        r"(\d+)\s*(?:people|staff)",
    ]
    for pattern in size_indicators:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return f"~{match.group(1)} employees"
    return None


def _extract_hiring_signals(html: str) -> Optional[str]:
    """Extract hiring signals from page content."""
    import re

    signals = []
    hiring_patterns = [
        (r"we\'re hiring", "hiring"),
        (r"join our team", "hiring"),
        (r"open positions", "hiring"),
        (r"careers?", "hiring"),
        (r"looking for", "hiring"),
    ]
    for pattern, label in hiring_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            signals.append(label)
    return ", ".join(signals) if signals else None


def enrich_lead(lead_id: int) -> bool:
    """Enrich a single lead. Returns True if data was found."""
    from salesbud.database import get_db
    from salesbud.models.lead import get_lead_by_id

    lead = get_lead_by_id(lead_id)
    if not lead:
        return False
    company_url = lead.get("company_url")

    if not company_url:
        return False

    data = asyncio.run(enrich_company(company_url))

    if data:
        conn = get_db()
        cursor = conn.cursor()

        now = datetime.utcnow().isoformat()

        cursor.execute(
            """
            UPDATE leads SET
                company_description = ?,
                company_size_est = ?,
                buying_signals = ?,
                enriched_at = ?
            WHERE id = ?
        """,
            (
                data.get("company_description"),
                data.get("company_size_est"),
                data.get("buying_signals"),
                now,
                lead_id,
            ),
        )

        conn.commit()
        conn.close()

        return True

    return False


def batch_enrich_leads(max_leads: int = 10) -> list:
    """Enrich multiple leads that have company_url but aren't enriched yet."""
    from salesbud.database import get_db

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, company, company_url
        FROM leads
        WHERE company_url IS NOT NULL
          AND company_url != ''
          AND (enriched_at IS NULL OR enriched_at = '')
        LIMIT ?
    """,
        (max_leads,),
    )

    leads = cursor.fetchall()
    conn.close()

    results = []

    for lead in leads:
        lead_id = lead["id"]
        company_url = lead["company_url"]

        logger.print_text(f"Enriching lead {lead_id}: {company_url}")

        data = asyncio.run(enrich_company(company_url))

        if data:
            conn = get_db()
            cursor = conn.cursor()

            now = datetime.utcnow().isoformat()

            cursor.execute(
                """
                UPDATE leads SET
                    company_description = ?,
                    company_size_est = ?,
                    buying_signals = ?,
                    enriched_at = ?
                WHERE id = ?
            """,
                (
                    data.get("company_description"),
                    data.get("company_size_est"),
                    data.get("buying_signals"),
                    now,
                    lead_id,
                ),
            )

            conn.commit()
            conn.close()

            results.append(
                {"lead_id": lead_id, "company": lead["company"], "enriched": True, "data": data}
            )
        else:
            results.append({"lead_id": lead_id, "company": lead["company"], "enriched": False})

    return results
