#!/usr/bin/env python3
"""
SalesBud Pre-flight Production Check
Validates all systems before going live (turning off dry_run).

Usage:
    cd /path/to/salesbud
    uv run python scripts/prod_check.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from toon_format import encode, decode
from typing import Any

# ── Colours ────────────────────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"  {GREEN}✓{RESET}  {msg}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}⚠{RESET}  {msg}")


def fail(msg: str) -> None:
    print(f"  {RED}✗{RESET}  {msg}")


# ── Helpers ─────────────────────────────────────────────────────────────────
def _parse_compact_toon(output: str) -> dict:
    """Parse our compact TOON format into a dict."""
    import re

    if not output.startswith("{"):
        return {"success": False, "error": output}

    # Remove outer braces
    content = output[1:-1] if output.endswith("}") else output[1:]

    result = {"success": False, "count": 0, "data": [], "errors": []}

    # Parse s: (success)
    if "s:T" in content[:10]:
        result["success"] = True
    elif "s:F" in content[:10]:
        result["success"] = False

    # Parse c: (count)
    count_match = re.search(r"c:(\d+)", content)
    if count_match:
        result["count"] = int(count_match.group(1))

    # Parse d: (data) - handle tabular format: d:[N]field1,field2,...:{values}
    # Pattern: d:\[(\d+)\]([^:]+):\{([^}]*)\}
    tabular_match = re.search(r"d:\[(\d+)\]([^:]+):\{([^}]*)\}", content)
    if tabular_match:
        count = int(tabular_match.group(1))
        keys_str = tabular_match.group(2)
        values_str = tabular_match.group(3)

        keys = keys_str.split(",")
        # Parse values - handle quoted strings, T/F, numbers
        values = []
        i = 0
        while i < len(values_str):
            if values_str[i] == '"':
                # Quoted string
                j = i + 1
                while j < len(values_str) and values_str[j] != '"':
                    if values_str[j] == "\\" and j + 1 < len(values_str):
                        j += 2
                    else:
                        j += 1
                values.append(values_str[i + 1 : j])
                i = j + 2  # Skip quote and comma
            elif values_str[i] == "{":
                # Nested object (config) - find matching brace
                brace_count = 1
                j = i + 1
                while j < len(values_str) and brace_count > 0:
                    if values_str[j] == "{":
                        brace_count += 1
                    elif values_str[j] == "}":
                        brace_count -= 1
                    j += 1
                values.append(values_str[i:j])
                i = j + 1  # Skip comma
            elif values_str[i] == "T":
                values.append(True)
                i += 2  # Skip T and comma
            elif values_str[i] == "F":
                values.append(False)
                i += 2  # Skip F and comma
            elif values_str[i] == "n" and values_str[i : i + 4] == "null":
                values.append(None)
                i += 5  # Skip null and comma
            elif values_str[i].isdigit() or values_str[i] == "-":
                # Number
                j = i
                while j < len(values_str) and (values_str[j].isdigit() or values_str[j] == "."):
                    j += 1
                val = values_str[i:j]
                values.append(int(val) if "." not in val else float(val))
                i = j + 1  # Skip comma
            else:
                i += 1

        # Build data object from keys and values
        data_obj = {}
        for idx, key in enumerate(keys):
            if idx < len(values):
                val = values[idx]
                # Handle nested config object
                if key == "config" and isinstance(val, str) and val.startswith("{"):
                    # Parse config object
                    config = {}
                    config_content = val[1:-1]  # Remove braces
                    # Parse key:value pairs from config
                    for pair in re.findall(r'(\w+):("[^"]*"|\w+)', config_content):
                        k, v = pair
                        v = v.strip('"')
                        config[k] = v
                    data_obj[key] = config
                else:
                    data_obj[key] = val

        result["data"] = [data_obj]
    else:
        # Fallback: simple data extraction
        result["data"] = [{}]

    return result


def run_toon(cmd: str) -> Any:
    """Run a salesbud CLI command and return parsed TOON."""
    result = subprocess.run(
        f"uv run python -m salesbud {cmd}",
        shell=True,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
        timeout=30,
    )
    output = result.stdout.strip()
    try:
        # Try TOON decoder first
        return decode(output)
    except NotImplementedError:
        # TOON decoder not yet implemented in library, use our parser
        return _parse_compact_toon(output)
    except Exception:
        return {"success": False, "error": result.stderr or output}


def check_section(title: str) -> None:
    print(f"\n{BOLD}{title}{RESET}")
    print("  " + "─" * 50)


# ── Checks ───────────────────────────────────────────────────────────────────
def check_env() -> int:
    check_section("Environment Variables")
    errors = 0

    linkedin_cookie = os.getenv("LINKEDIN_SESSION_COOKIE")
    resend_key = os.getenv("RESEND_API_KEY")
    resend_from = os.getenv("RESEND_FROM_EMAIL")

    if linkedin_cookie:
        try:
            cookies = json.loads(linkedin_cookie)
            if isinstance(cookies, list) and len(cookies) > 0:
                ok(f"LINKEDIN_SESSION_COOKIE set ({len(cookies)} cookies)")
            else:
                warn("LINKEDIN_SESSION_COOKIE present but empty/malformed")
        except json.JSONDecodeError:
            fail("LINKEDIN_SESSION_COOKIE is not valid JSON")
            errors += 1
    else:
        warn("LINKEDIN_SESSION_COOKIE not set — LinkedIn features will not work")

    if resend_key:
        if resend_key.startswith("re_"):
            ok(f"RESEND_API_KEY set (re_...{resend_key[-4:]})")
        else:
            warn("RESEND_API_KEY set but doesn't start with 're_' — might be invalid")
    else:
        warn("RESEND_API_KEY not set — email features will not work")

    if resend_from:
        ok(f"RESEND_FROM_EMAIL: {resend_from}")
    else:
        warn("RESEND_FROM_EMAIL not set — will use default 'rhigden@syntolabs.xyz'")

    return errors


def check_database() -> int:
    check_section("Database")
    errors = 0

    status = run_toon("status --toon")
    if status.get("success"):
        data = status.get("data", [{}])[0]
        if data.get("db_ok"):
            ok(f"DB connected — {data.get('total_leads', 0)} leads in database")
        else:
            fail("DB connection failed")
            errors += 1

        dry = data.get("dry_run", True)
        if dry:
            warn("DRY RUN mode is ON — no real actions will be taken")
            warn("  Run: uv run python -m salesbud config dry_run 0  to go live")
        else:
            ok("DRY RUN mode is OFF — PRODUCTION mode")
    else:
        fail("Could not run status command")
        errors += 1

    return errors


def check_rate_limits() -> int:
    check_section("Rate Limits & Daily Counters")
    errors = 0

    status = run_toon("status --toon")
    if status.get("success"):
        data = status.get("data", [{}])[0]
        config = data.get("config", {})

        dms_per_day = int(config.get("dms_per_day", 50))
        emails_per_day = int(config.get("emails_per_day", 50))

        ok(f"DM limit: {dms_per_day}/day")
        ok(f"Email limit: {emails_per_day}/day")

        if dms_per_day > 100:
            warn(f"DMs per day ({dms_per_day}) is high — LinkedIn may flag you")
        if emails_per_day > 200:
            warn(f"Emails per day ({emails_per_day}) is high — check Resend limits")

    return errors


def check_leads() -> int:
    check_section("Lead Database")
    errors = 0

    status = run_toon("status --toon")
    if status.get("success"):
        data = status.get("data", [{}])[0]
        total = data.get("total_leads", 0)
        dm_q = data.get("dm_queue", 0)
        email_q = data.get("email_queue", 0)

        if total == 0:
            warn(
                "No leads in database — run: uv run python -m salesbud scrape --query 'CEO' --location 'Austin'"
            )
        else:
            ok(f"Total leads: {total}")

        ok(f"DM queue: {dm_q} leads ready")
        ok(f"Email queue: {email_q} leads ready")

    return errors


def check_python_version() -> int:
    check_section("Runtime")
    errors = 0

    import platform

    v = platform.python_version()
    major, minor, _ = v.split(".")
    if int(major) == 3 and int(minor) >= 13:
        ok(f"Python {v}")
    elif int(major) == 3 and int(minor) >= 11:
        warn(f"Python {v} — recommend upgrading to 3.13")
    else:
        fail(f"Python {v} — version too old, upgrade to 3.13")
        errors += 1

    # Check key packages
    try:
        import pydantic

        ok(f"pydantic {pydantic.__version__}")
    except ImportError:
        fail("pydantic not installed — run: uv sync")
        errors += 1

    try:
        import playwright  # noqa: F401

        ok("playwright installed")
    except ImportError:
        fail("playwright not installed — run: uv sync")
        errors += 1

    return errors


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  SalesBud Production Readiness Check{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")

    total_errors = 0
    total_errors += check_python_version()
    total_errors += check_env()
    total_errors += check_database()
    total_errors += check_rate_limits()
    total_errors += check_leads()

    print(f"\n{BOLD}{'=' * 60}{RESET}")
    if total_errors == 0:
        print(f"{GREEN}{BOLD}  ✓ All checks passed — ready for prod!{RESET}")
        print(f"\n  To go live: {BOLD}uv run python -m salesbud config dry_run 0{RESET}")
    else:
        print(f"{RED}{BOLD}  ✗ {total_errors} error(s) found — fix before going live{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}\n")

    sys.exit(0 if total_errors == 0 else 1)


if __name__ == "__main__":
    main()
