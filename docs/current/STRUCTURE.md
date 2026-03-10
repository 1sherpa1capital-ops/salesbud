# SalesBud — Project Structure

**Version:** 1.1 | **Updated:** March 10, 2026

---

## Directory Layout

```
salesbud/
├── .env                           # Live credentials (do not commit)
├── .env.example                   # Template with all required vars
├── .gitignore
├── pyproject.toml                 # uv project config + dependencies
├── uv.lock                        # Lock file
├── skillet.md                     # Relevant skills reference
├── README.md                      # Quick start
│
├── data/
│   └── salesbud.db                # SQLite database (leads, activities, config)
│
├── docs/
│   ├── MVP-SPEC.md                # ← This spec (v1.1)
│   ├── PRD.md                     # Product Requirements Document
│   ├── SPEC.md                    # Technical Specification
│   ├── BRD.md                     # Business Requirements Document
│   ├── README.md                  # Detailed docs index
│   └── STRUCTURE.md               # This file
│
└── src/
    └── salesbud/                  # Main Python package
        ├── __init__.py
        ├── __main__.py            # Enables: python -m salesbud
        ├── main.py                # CLI entry point (all commands)
        ├── database.py            # SQLite schema, config helpers
        │
        ├── models/
        │   ├── __init__.py
        │   └── lead.py            # Lead CRUD: add, update, stats, email ops
        │
        ├── services/
        │   ├── __init__.py
        │   ├── scraper.py         # LinkedIn scraping (Playwright)
        │   ├── connector.py       # Connection requests + acceptance checks
        │   ├── sequence.py        # 5-step LinkedIn DM engine (NEPQ)
        │   └── emailer.py         # 4-step cold email engine (Resend)
        │
        └── cli/
            ├── __init__.py
            └── dashboard.py       # Unified dashboard: DM + Email columns
```

---

## Environment Variables (`.env`)

| Variable | Required | Purpose |
|----------|----------|---------|
| `LINKEDIN_SESSION_COOKIE` | Yes | LinkedIn auth (JSON cookie array) |
| `LINKEDIN_EMAIL` | Fallback | Login email |
| `LINKEDIN_PASSWORD` | Fallback | Login password |
| `RESEND_API_KEY` | Yes | Resend email API |
| `RESEND_FROM_EMAIL` | Yes | Sender address (e.g. `Rhigden <rhigden@syntolabs.xyz>`) |
| `CAL_API_KEY` | Post-MVP | Cal.com booking |

---

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | All CLI commands routed here |
| `database.py` | Init schema, config get/set, `is_dry_run()` |
| `lead.py` | All lead CRUD + `update_lead_email()`, `update_lead_email_sent()` |
| `scraper.py` | LinkedIn Sales Navigator scraper |
| `sequence.py` | LinkedIn DM 5-step NEPQ engine |
| `emailer.py` | Resend 4-step cold email engine |
| `dashboard.py` | CLI display: pipeline + email stats, DM + Email step columns |

---

## CLI Quick Reference

```bash
# Setup
uv sync                                           # Install dependencies
uv run python -m salesbud init                    # Init/migrate database

# LinkedIn
uv run python -m salesbud scrape --query "CEO" --location "Austin"
uv run python -m salesbud connect --max 5
uv run python -m salesbud check-connections
uv run python -m salesbud sequence

# Email
uv run python -m salesbud add-email <id> sarah@company.com
uv run python -m salesbud email-sequence
uv run python -m salesbud email --to test@example.com -s "Test" -b "Hello"

# Monitor
uv run python -m salesbud dashboard
uv run python -m salesbud lead <id>
uv run python -m salesbud config

# Full workflow (both channels)
uv run python -m salesbud workflow --query "CEO" --max-leads 10
```

---

## Current State

Database: `data/salesbud.db` — 15 leads
- 8 new, 1 connected, 5 active (DM sequence), 1 replied
- 1 lead with email address (Mike Johnson → mike@growthco.com)

Working features:
- ✅ LinkedIn scraping (real + dry-run)
- ✅ Connection requests + acceptance checking
- ✅ 5-step NEPQ DM sequence
- ✅ 4-step cold email sequence via Resend
- ✅ Unified dashboard (both channels)
- ✅ Dry-run mode (both channels)
- ✅ SQLite with email schema columns

---

## Project Stats

| Item | Count |
|------|-------|
| Python files | 11 |
| Lines of code | ~2,000 |
| Package manager | uv |
| Database | SQLite |
| Email provider | Resend (free, 2k/mo) |
