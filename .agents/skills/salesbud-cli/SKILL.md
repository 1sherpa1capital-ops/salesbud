---
name: salesbud-cli
description: >
  SalesBud is a production-ready outbound SDR CLI. Use it to scrape LinkedIn
  leads, sequence LinkedIn DMs, send cold email campaigns, discover email
  addresses, and enrich lead profiles. All mutations default to dry-run mode —
  always check the status command first. Input validation is enforced via
  Pydantic; bad inputs return clean JSON errors.
---

# SalesBud CLI Skill

SalesBud is an autonomous outbound SDR agent built as a Python CLI.  
It runs on **Python 3.13+**, uses **pydantic v2** for input validation,
and stores all state in a local SQLite database.

---

## Safety Policy

> **CRITICAL**: All write operations (connect, DM, email, scrape) are blocked
> by `dry_run = 1` by default. **Never disable dry_run without explicit user
> confirmation**.

1. Always call `salesbud status --json` first to confirm dry/live mode.
2. Only disable dry_run after explicit user approval: `salesbud config dry_run 0`
3. Respect daily rate limits (`dms_per_day`, `emails_per_day`).
4. Idempotency guards prevent double-sending DMs or emails on the same day.

---

## Invocation

```bash
# All commands support --json flag for machine-readable output
uv run python -m salesbud <command> [args] [--json] [--dry-run]

# Or after pip install:
salesbud <command> [args] [--json]
```

---

## Command Reference

### Diagnostics

| Command | Description |
|---------|-------------|
| `salesbud status --json` | DB health, lead count, dry_run state, config |
| `salesbud dashboard --json` | Sequence progress, pipeline metrics |
| `salesbud config-get [key] --json` | Read config value or all config |
| `salesbud config <key> <value> --json` | Set a config value |

**status example output:**
```json
{
  "success": true,
  "data": [{
    "dry_run": true,
    "db_ok": true,
    "total_leads": 42,
    "dm_queue": 5,
    "email_queue": 3,
    "linkedin_auth": "cookie",
    "resend_key_set": true,
    "config": {
      "dms_per_day": "50",
      "emails_per_day": "50"
    }
  }]
}
```

### Lead Management

| Command | Description |
|---------|-------------|
| `salesbud leads --json` | List all leads |
| `salesbud lead <lead_id> --json` | Show full detail for a lead |
| `salesbud add-email <lead_id> <email> --json` | Set verified email for a lead |
| `salesbud set-company-url <lead_id> <url> --json` | Set company URL for enrichment |
| `salesbud delete <lead_id> --json` | Remove a lead |

> `add-email` and `set-company-url` validate inputs with Pydantic — bad emails or
> invalid URLs return `{"success": false, "errors": ["..."]}`.

### Lead Scraping

```bash
salesbud scrape \
  --query "CEO agency" \
  --location "Austin, TX" \
  --max 50 \
  --json [--dry-run]
```

Scrapes LinkedIn Sales Navigator. Requires browser, LinkedIn session cookie.
`--max` accepts 1–500 (validated). `--dry-run` flag simulates scrape.

### Email Discovery & Enrichment

| Command | Description |
|---------|-------------|
| `salesbud find-emails --max 10 --json` | MX + pattern + scraping for all leads without email |
| `salesbud find-email <lead_id> --json` | Find email for a specific lead |
| `salesbud enrich --max 10 --json` | AI-powered enrichment from company URL |
| `salesbud enrich-lead <lead_id> --json` | Enrich a specific lead |

### LinkedIn Outreach

```bash
# Connection campaign (dry-run safe)
salesbud connect --max 10 --delay 60 --json [--dry-run]

# DM sequence step
salesbud sequence --json [--dry-run]

# Check replies in LinkedIn inbox
salesbud check-replies --max 20 --json
```

`--max` for connect accepts 1–100 (validated). `--delay` ≥0 seconds between requests.

Daily production limits enforce `dms_per_day` config — rate limit guard aborts early with `{"success": false}` when reached.

### Cold Email

```bash
# Run email sequence step for all eligible leads
salesbud email-sequence --json [--dry-run]

# Send one-off email (Pydantic-validated)
salesbud email \
  --to "founder@company.com" \
  --subject "Quick question" \
  --body "Your body text here" \
  --json [--dry-run]

# Check connection requests sent
salesbud check-connections --json
```

**Email sequence** tracks leads in 4-step drip (days 0, 3, 7, 14). Each step
uses a personalized template from the sales playbook. Daily `emails_per_day`
limit is enforced server-side.

### Sequence Control

```bash
# Pause / resume a lead
salesbud pause <lead_id> --json
salesbud resume <lead_id> --json

# Manual step override  
salesbud advance <lead_id> --json

# Mark lead as replied/booked
salesbud replied <lead_id> --json
```

---

## Config Keys

| Key | Default | Description |
|-----|---------|-------------|
| `dry_run` | `1` | `0` = live, `1` = dry-run |
| `dms_per_hour` | `8` | Max DMs per hour |
| `dms_per_day` | `50` | Max DMs per day (rate limit) |
| `delay_minutes` | `5` | Base delay between DMs |
| `delay_variance` | `10` | Random jitter added to delay |
| `emails_per_hour` | `10` | Max emails per hour |
| `emails_per_day` | `50` | Max emails per day (rate limit) |
| `email_delay_minutes` | `2` | Base delay between emails |

```bash
# Go live (confirm with user first!)
salesbud config dry_run 0

# Tighten safety limits
salesbud config dms_per_day 20
salesbud config emails_per_day 20
```

---

## Prod Readiness Pre-flight

```bash
uv run python scripts/prod_check.py
```

Checks: Python ≥3.13, pydantic, playwright, env vars, DB, rate limits, lead count.

---

## Error Handling

All commands return either:
```json
{"success": true, "count": N, "data": [...], "errors": []}
```
or on failure:
```json
{"success": false, "count": 0, "data": [], "errors": ["reason..."]}
```

Validation errors (email format, URL format, out-of-range integers) are caught
before any DB or network call and returned as clean JSON.

---

## Environment Variables

```bash
LINKEDIN_SESSION_COOKIE=<json-serialized cookie array>
RESEND_API_KEY=re_XXXXXXXXXXXX
RESEND_FROM_EMAIL="Rhigden <rhigden@syntolabs.xyz>"
LINKEDIN_EMAIL=email@example.com    # optional (password login fallback)
LINKEDIN_PASSWORD=secretpassword    # optional
```

---

## Example Agent Workflow

```bash
# 1. Pre-flight check
uv run python scripts/prod_check.py

# 2. Check current state
salesbud status --json
salesbud dashboard --json

# 3. Scrape new leads (dry-run safe)
salesbud scrape --query "Marketing Agency CEO" --max 50 --json --dry-run

# 4. Find emails for leads
salesbud find-emails --max 20 --json --dry-run

# 5. Enrich profiles
salesbud enrich --max 10 --json --dry-run

# 6. Go live (ONLY after user approval)
salesbud config dry_run 0

# 7. Run sequence step
salesbud sequence --json

# 8. Run email sequence
salesbud email-sequence --json

# 9. Check replies
salesbud check-replies --json

# 10. Monitor pipeline
salesbud dashboard --json
```
