"""
Email discovery and verification service
"""

# Suppress urllib3/requests version mismatch warnings (must be before imports)
import warnings

warnings.filterwarnings("ignore", message=".*urllib3.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*RequestsDependencyWarning.*")

import re
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import dns.resolver
import requests

from salesbud.database import get_db

SKIP_VERIFY_DOMAINS = {"gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "icloud.com"}


def extract_domain_from_linkedin(
    linkedin_url: Optional[str] = None, company: Optional[str] = None
) -> Optional[str]:
    """Extract company domain from LinkedIn URL or company name."""
    if not linkedin_url and not company:
        return None

    if company:
        company_clean = company.lower().strip()
        company_clean = re.sub(r"[^\w\s-]", "", company_clean)
        company_clean = company_clean.replace(" ", "")
        return f"{company_clean}.com"

    if linkedin_url:
        match = re.search(r"linkedin\.com/company/([^/?]+)", linkedin_url)
        if match:
            company_slug = match.group(1)
            company_slug = re.sub(
                r"-*(inc|llc|corp|co|ltd)$", "", company_slug, flags=re.IGNORECASE
            )
            return f"{company_slug}.com"

    return None


def find_emails_on_page(html: str) -> list:
    """Extract email addresses from HTML using regex."""
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    emails = re.findall(email_pattern, html)
    return list(set(emails))


def verify_smtp(email: str, timeout: int = 10) -> bool:
    """MX lookup + RCPT TO check. Skip verification for common providers."""
    domain = email.lower().split("@")[-1]

    if domain in SKIP_VERIFY_DOMAINS:
        return True

    try:
        mx_records = dns.resolver.resolve(domain, "MX")
        if not mx_records:
            return False

        mx_host = str(mx_records[0].exchange).rstrip(".")  # type: ignore[attr-defined]

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        try:
            sock.connect((mx_host, 25))
            sock.send(b"EHLO localhost\r\n")

            response = sock.recv(1024).decode("utf-8", errors="ignore")

            sock.send("MAIL FROM:<verify@example.com>\r\n".encode())
            sock.recv(1024)

            sock.send(f"RCPT TO:<{email}>\r\n".encode())
            response = sock.recv(1024).decode("utf-8", errors="ignore")

            sock.send(b"QUIT\r\n")
            sock.close()

            return "250" in response or "OK" in response
        except (socket.error, OSError):
            sock.close()
            return False
        except RuntimeError:
            sock.close()
            return False
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
        return False
    except (dns.resolver.NoResolver, socket.error):
        return False


def search_duckduckgo(
    first_name: str, last_name: str, company: str, timeout: int = 15
) -> Optional[str]:
    """Search DuckDuckGo for email address."""
    try:
        query = f'"{first_name} {last_name}" {company} email'
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=headers,
            timeout=timeout,
        )

        if response.status_code == 200:
            emails = find_emails_on_page(response.text)
            for email in emails:
                if company.lower() in email.lower().split("@")[-1]:
                    return email
            if emails:
                return emails[0]
    except (requests.RequestException, TimeoutError):
        pass
    except ValueError:
        pass

    return None


def scrape_company_pages(domain: str) -> list:
    """Scrape company website pages for email addresses."""
    emails = []
    paths = ["/contact", "/team", "/about", "/about-us", "/contact-us"]

    for path in paths:
        try:
            url = f"https://{domain}{path}"
            response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code == 200:
                page_emails = find_emails_on_page(response.text)
                emails.extend(page_emails)
        except (requests.RequestException, TimeoutError):
            continue
        except ValueError:
            continue

    return list(set(emails))


def guess_email_patterns(first_name: str, last_name: str, domain: str) -> list:
    """Generate email patterns for a person."""
    first = first_name.lower() if first_name else ""
    last = last_name.lower() if last_name else ""

    patterns = [
        f"{first}@{domain}",
        f"{first}.{last}@{domain}",
        f"{first}{last}@{domain}",
        f"{first[0]}{last}@{domain}" if first else None,
        f"{first}{last[0]}@{domain}" if last else None,
        (
            f"{first_name[0] if first_name else ''}{last_name}@{domain}"
            if first_name and last_name
            else None
        ),
    ]

    return [p for p in patterns if p]


def find_email_for_lead(lead: dict, quick_mode: bool = False) -> Optional[str]:
    """Main function that tries all strategies to find email for a lead."""
    name = lead.get("name", "")
    company = lead.get("company", "")
    linkedin_url = lead.get("linkedin_url", "")

    if not name:
        return None

    parts = name.split()
    first_name = parts[0] if parts else ""
    last_name = parts[-1] if len(parts) > 1 else ""

    domain = extract_domain_from_linkedin(linkedin_url, company)
    if not domain:
        return None

    if quick_mode:
        try:
            search_result = search_duckduckgo(first_name, last_name, company, timeout=5)
            if search_result:
                return search_result
        except (requests.RequestException, TimeoutError):
            pass
        except ValueError:
            pass

        patterns = guess_email_patterns(first_name, last_name, domain)
        for pattern in patterns:
            if verify_smtp(pattern, timeout=3):
                return pattern
        return None

    search_result = search_duckduckgo(first_name, last_name, company)
    if search_result:
        return search_result

    page_emails = scrape_company_pages(domain)
    for email in page_emails:
        if domain in email.lower():
            return email

    patterns = guess_email_patterns(first_name, last_name, domain)
    for pattern in patterns:
        if verify_smtp(pattern):
            return pattern

    return None


def update_lead_email_with_verification(lead_id: int, email: str, source: str, verified: bool):
    """Update lead email with source and verified status."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE leads SET email = ?, email_source = ?, email_verified = ? WHERE id = ?",
        (email, source, 1 if verified else 0, lead_id),
    )
    conn.commit()
    conn.close()


def batch_find_emails(max_leads: int = 10, quick_mode: bool = False) -> list:
    """Find emails for leads without emails."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE email IS NULL OR email = '' LIMIT ?", (max_leads,))
    leads = [dict(row) for row in cursor.fetchall()]
    conn.close()

    results = []

    if quick_mode:
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_lead = {
                executor.submit(find_email_for_lead, lead, quick_mode=True): lead for lead in leads
            }
            for future in as_completed(future_to_lead, timeout=60):
                lead = future_to_lead[future]
                try:
                    email = future.result(timeout=10)
                    if email:
                        verified = verify_smtp(email, timeout=3)
                        update_lead_email_with_verification(lead["id"], email, "search", verified)
                        results.append(
                            {"lead_id": lead["id"], "email": email, "verified": verified}
                        )
                except (TimeoutError, ValueError):
                    continue
                except RuntimeError:
                    continue
    else:
        for lead in leads:
            email = find_email_for_lead(lead, quick_mode=False)
            if email:
                verified = verify_smtp(email)
                update_lead_email_with_verification(lead["id"], email, "search", verified)
                results.append({"lead_id": lead["id"], "email": email, "verified": verified})

    return results
