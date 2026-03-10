# SalesBud CLI Reference for AI Agents

This file provides a complete reference for AI agents (OpenCode, Claude Code, etc.) to operate SalesBud autonomously.

## Critical Requirements

### Always Use These Patterns
1. **Use `uv run python`** - Never use plain `python`:
   ```bash
   # WRONG - will fail to find module
   python -m salesbud status --json
   
   # CORRECT - uses project virtual environment
   uv run python -m salesbud status --json
   ```

2. **Change to correct directory first**:
   ```bash
   cd /Users/guestr/Desktop/syntolabs/salesbud
   uv run python -m salesbud status --json
   ```

3. **Always use `--json`** for machine-readable output when automating.

4. **Save all changes to changelog.md** - After completing any work, document what was done in `changelog.md`

## Quick Start

```bash
# Always start by checking system status
cd /Users/guestr/Desktop/syntolabs/salesbud
uv run python -m salesbud status --json

# Check dry-run mode before running any campaign
uv run python -m salesbud config dry_run
```

## All Commands

### System

| Command | Description |
|---------|-------------|
| `init` | Initialize database |
| `status` | Show system health (DB, queues, auth status) |
| `config [key] [value]` | Get/set config values |
| `test` | Run full test sequence |

### Lead Generation

| Command | Arguments | Description |
|---------|-----------|-------------|
| `scrape` | `--query`, `--location`, `--max` | Scrape leads from LinkedIn |
| `connect` | `--max`, `--delay` | Send connection requests |
| `check-connections` | — | Check pending connection status |

### Sequences

| Command | Description |
|---------|-------------|
| `sequence` | Run next DM sequence step (5-step NEPQ) |
| `email-sequence` | Run next cold email step (4-step) |
| `workflow` | Full pipeline: scrape → connect → check → sequence → email |

### Individual Actions

| Command | Arguments | Description |
|---------|-----------|-------------|
| `email` | `--to`, `--subject`, `--body` | Send single email via Resend |
| `add-email` | `lead_id`, `email` | Manually add email to lead |
| `reply` | `lead_id`, `reply_type` | Simulate reply (dry-run only) |

### Email Discovery

| Command | Arguments | Description |
|---------|-----------|-------------|
| `find-email` | `lead_id`, `[--quick]` | Find email for a specific lead. Use `--quick` for fast mode (<10s) |
| `find-emails` | `--max N`, `[--quick]` | Batch discover emails for leads. Use `--quick` for parallel processing |

### Company Enrichment

| Command | Arguments | Description |
|---------|-----------|-------------|
| `set-company-url` | `lead_id`, `company_url` | Set company URL for a lead (required before enrich) |
| `enrich` | `lead_id` | Enrich lead with company data (Crawl4AI) |
| `enrich-all` | `--max N` | Batch enrich multiple leads |

**Note:** `enrich` requires `company_url` to be set first using `set-company-url` command.

### Inbox

| Command | Description |
|---------|-------------|
| `check-replies` | Scan LinkedIn inbox for replies from leads |

### Dashboard

| Command | Arguments | Description |
|---------|-----------|-------------|
| `dashboard` | — | Show unified DM + Email dashboard |
| `lead` | `lead_id` | Show full lead detail with activity log |

---

## JSON Output Format

All commands support `--json` flag for machine-readable output:

```json
{"success": true, "count": 5, "data": [...], "errors": []}
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Did command complete without error |
| `count` | int | Number of items processed |
| `data` | list | Relevant output items |
| `errors` | list | Non-fatal errors encountered |

### Command-Specific Data Payloads

| Command | Data Contents |
|---------|--------------|
| `init` | `[{"db_path": "...", "initialized": true}]` |
| `scrape` | List of scraped lead dicts |
| `connect` | `[{"lead_id": int, "name": str, "result": "sent"/"skipped"/"failed"}]` |
| `check-connections` | `[{"lead_id": int, "name": str, "status": str}]` |
| `sequence` | `[{"lead_id": int, "name": str, "step": int, "sent": bool}]` |
| `email` | `[{"to": str, "subject": str, "sent": bool}]` |
| `email-sequence` | `[{"lead_id": int, "name": str, "step": int, "sent": bool}]` |
| `add-email` | `[{"lead_id": int, "email": str, "name": str}]` |
| `find-email` | `[{"lead_id": int, "email": str, "verified": bool}]` |
| `find-emails` | List of found emails with verification status |
| `enrich` | `[{"lead_id": int, "company_description": str, "company_size_est": str, "buying_signals": [...]}]` |
| `enrich-all` | List of enriched leads |
| `check-replies` | `[{"lead_id": int, "name": str, "message": str, "detected_intent": "positive/neutral/negative"}]` |
| `workflow` | List of workflow step results |
| `dashboard` | `{"stats": {...}, "leads": [...]}` |
| `lead` | Lead dict + `"activities": [...]` |
| `reply` | `[{"lead_id": int, "reply_type": str, "new_status": str}]` |
| `config` | `{"dry_run": "1", "dms_per_hour": "8", ...}` |
| `status` | See below |

### Status Command Data

```json
{
  "dry_run": true,
  "db_ok": true,
  "db_path": "/path/to/salesbud.db",
  "total_leads": 23,
  "dm_queue": 4,
  "email_queue": 2,
  "linkedin_auth": "cookie",
  "resend_key_set": true,
  "config": {"dms_per_hour": "8", "emails_per_hour": "10", ...}
}
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (check "errors" field) |
| 2 | Rate-limited (try again later) |
| 3 | Nothing to process (no leads due) |

---

## Key Rules for AI Agents

1. **Always use `uv run python`** - not plain `python`
2. **Always check dry_run status first**: `uv run python -m salesbud config dry_run`
3. **Do not run workflow in production until dry_run = 0 is confirmed**
4. **If scrape returns 0 leads, LinkedIn session cookie may be expired**
5. **add-email is the fallback for email discovery if find-email fails**
6. **Check status before starting any campaign to verify auth is configured**
7. **Use `--quick` flag for email discovery when speed matters** (skips slow verification)
8. **Set company_url before running enrich** - use `set-company-url` command first
9. **Switch to other skills when SalesBud CLI alone isn't enough**:
   - `find-email` fails → Use **agent-browser** skill to manually extract from website
   - Low reply rates (<5%) → Use **copywriting** skill to improve messaging
   - Need objection handling → Use **sales-coach** skill for strategy

---

## Browser Stealth System

SalesBud now includes anti-detection measures to prevent LinkedIn from blocking automation:

### Features
- **Rotating User Agents**: Random selection from realistic browser signatures
- **Viewport Randomization**: Varies screen dimensions to avoid fingerprinting
- **Stealth Script**: Hides `navigator.webdriver` and other automation markers
- **Human-like Timing**: Random delays (jitter) between actions
- **Retry Logic**: Automatic retry on ERR_TOO_MANY_REDIRECTS
- **Challenge Detection**: Identifies CAPTCHA/security checks

### Implementation
Located in `src/salesbud/utils/browser.py` and integrated into:
- `services/scraper.py` - LinkedIn search scraping
- `services/connector.py` - Connection requests
- `services/sequence.py` - DM sequences

### Rate Limits
Even with stealth, respect these limits:
- 8 LinkedIn DMs/hour, 50/day
- 10 emails/hour, 50/day
- Max 10 connections per run

---

## Multi-Skill Coordination

SalesBud works best when combined with other AI skills:

### When to Switch Skills

| Situation | Switch To | How |
|-----------|-----------|-----|
| `find-email` returns no results | **agent-browser** | Visit company website, extract from /team or /contact pages |
| Reply rate < 5% | **copywriting** | Rewrite DM/email templates with better hooks |
| Need objection handling | **sales-coach** | Get NEPQ-based response strategies |
| Setting up A/B tests | **cold-email** | Subject line optimization, testing framework |

### Example Workflow

```bash
# 1. SalesBud: Scrape leads
cd /Users/guestr/Desktop/syntolabs/salesbud
uv run python -m salesbud scrape --query "CEO" --location "Austin" --max 10 --json

# 2. Agent-Browser: Research each lead's company website
# (Switch to agent-browser skill)
# agent-browser open https://company.com
# agent-browser snapshot -i

# 3. SalesBud: Enrich with discovered data
uv run python -m salesbud set-company-url 5 "https://company.com" --json
uv run python -m salesbud enrich 5 --json

# 4. Copywriting: Personalize messages based on research
# (Switch to copywriting skill)
# "Rewrite DM sequence for SaaS founders with AI automation angle"

# 5. SalesBud: Execute outreach
uv run python -m salesbud connect --max 10 --json
uv run python -m salesbud sequence --json
```

---

## Troubleshooting

### "No module named 'salesbud'"
- Ensure you're in the correct directory: `/Users/guestr/Desktop/syntolabs/salesbud`
- Use `uv run python -m salesbud` NOT `python -m salesbud`

### "scrape" returns 0 leads instantly
- LinkedIn session cookie likely expired
- Check: `cat .env | grep LINKEDIN_SESSION_COOKIE`
- Refresh cookie manually in browser and update `.env`

### Rate limit errors
- System enforces: 8 DMs/hour, 10 emails/hour, 50/day each
- Wait before retrying or reduce batch sizes with `--max 5`

### "Database not initialized"
- Run: `uv run python -m salesbud init`

### Dry-run mode active
- Check: `uv run python -m salesbud config dry_run`
- Set to 0 for real sends: `uv run python -m salesbud config dry_run 0`

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LINKEDIN_SESSION_COOKIE` | For scraping/DM | JSON cookie array with `li_at` |
| `LINKEDIN_EMAIL` | Fallback | LinkedIn email |
| `LINKEDIN_PASSWORD` | Fallback | LinkedIn password |
| `RESEND_API_KEY` | For email | Resend API key |
| `RESEND_FROM_EMAIL` | No | Sender email (default: Rhigden <rhigden@syntolabs.xyz>) |

---

## Example Agent Workflows

### Full Outbound Campaign with Deep Research

```bash
cd /Users/guestr/Desktop/syntolabs/salesbud

# 1. Check status
uv run python -m salesbud status --json

# 2. Scrape leads
uv run python -m salesbud scrape --query "CEO" --location "Austin" --max 20 --json

# 3. (Optional) Deep research with agent-browser skill
# Visit company websites, check recent news, find personalization angles

# 4. Set company URLs for enrichment
uv run python -m salesbud set-company-url 1 "https://company1.com" --json
uv run python -m salesbud set-company-url 2 "https://company2.com" --json

# 5. Enrich leads with company data
uv run python -m salesbud enrich 1 --json
uv run python -m salesbud enrich 2 --json

# 6. Send connections
uv run python -m salesbud connect --max 10 --json

# 7. Check connections (in production, wait 24-48h)
uv run python -m salesbud check-connections --json

# 8. Discover emails (use --quick for fast mode)
uv run python -m salesbud find-emails --max 10 --quick --json

# 9. Run DM sequence
uv run python -m salesbud sequence --json

# 10. Run email sequence
uv run python -m salesbud email-sequence --json

# 11. Check for replies
uv run python -m salesbud check-replies --json

# 12. Monitor dashboard
uv run python -m salesbud dashboard --json
```

### Enrich and Follow Up

```bash
cd /Users/guestr/Desktop/syntolabs/salesbud

# Enrich company data
uv run python -m salesbud enrich-all --max 10 --json

# Check specific lead detail
uv run python -m salesbud lead 42 --json
```

---

## Rate Limits

| Channel | Limit |
|---------|-------|
| LinkedIn DMs/hour | 8 |
| LinkedIn DMs/day | 50 |
| LinkedIn connections/run | ≤10 |
| Emails/hour | 10 |
| Emails/day | 50 |

Configurable via `config` command:
```bash
uv run python -m salesbud config dms_per_hour 8
uv run python -m salesbud config emails_per_hour 10
```
