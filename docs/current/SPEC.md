# SalesBud — Specification

**Version:** 1.3.0 | **Date:** March 11, 2026 | **Status:** Live — Production Ready

---

## 1. What It Does

SalesBud is a **Python CLI** that automates two-channel outbound sales development:

1. Scrapes leads from LinkedIn Sales Navigator (Playwright)
2. Sends personalized LinkedIn connection requests
3. Runs a **5-step NEPQ DM sequence** on connected leads
4. Runs a **4-step cold email sequence** via Resend on leads with emails
5. Shows both channels in a unified dashboard

**What's live (v1.1):**
- ✅ LinkedIn scraping, connections, 5-step DM sequence
- ✅ 4-step cold email via Resend (`rhigden@syntolabs.xyz`)
- ✅ Unified dashboard (DM step + Email step per lead)
- ✅ Dry-run mode for both channels (default on)
- ✅ `add-email` to manually assign email addresses
- ✅ **Production Hardened (v1.3.0):** Pydantic validation, DB-backed daily rate limits, retry logic, global JSON error handler, and idempotency guards.

---

## 2. Architecture

```
┌──────────────┐     ┌──────────────────────────────┐     ┌──────────────┐
│  CLI Entry   │────▶│  Services Layer              │────▶│  SQLite DB   │
│  (main.py)   │     │                              │     │  leads       │
│  argparse    │     └───┬──────┬──────┬────────┬───┘     │  activities  │
└──────────────┘         │      │      │        │         │  config      │
                         ▼      ▼      ▼        ▼         └──────────────┘
                    Scraper Connector Sequence Emailer
                   (Playwrt)(Playwrt) Engine  (Resend)
                         │      │                │
                         ▼      ▼                ▼
                    ┌──────────────────┐  ┌──────────────────┐
                    │  LinkedIn        │  │  Resend API      │
                    │  (session cookie)│  │  syntolabs.xyz   │
                    └──────────────────┘  └──────────────────┘
```

---

## 3. Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | ≥3.9 |
| Package manager | uv | Latest |
| Browser automation | Playwright | ≥1.40.0 |
| Email delivery | Resend SDK | ≥2.0.0 |
| Database | SQLite | Built-in |
| Environment | python-dotenv | ≥1.0.0 |
| Build system | Hatchling | Latest |

---

## 4. Project Structure

```
salesbud/
├── src/salesbud/
│   ├── main.py                  # CLI entry point (argparse)
│   ├── database.py              # SQLite connection, config, activity logging
│   ├── models/
│   │   └── lead.py              # Lead CRUD + email ops
│   ├── services/
│   │   ├── scraper.py           # LinkedIn scraping (Playwright)
│   │   ├── connector.py         # Connection requests + acceptance checks
│   │   ├── sequence.py          # 5-step NEPQ DM engine
│   │   └── emailer.py           # 4-step cold email engine (Resend)
│   └── cli/
│       └── dashboard.py         # Unified terminal dashboard
├── data/salesbud.db             # SQLite (gitignored)
├── .env                         # Credentials (gitignored)
└── .env.example
```

---

## 5. Database Schema

```sql
CREATE TABLE leads (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    linkedin_url        TEXT UNIQUE NOT NULL,
    name                TEXT,
    headline            TEXT,
    company             TEXT,
    location            TEXT,
    email               TEXT,                   -- manual or Apollo (post-MVP)
    status              TEXT DEFAULT 'new',     -- new, connection_requested, connected,
                                               --   active, replied, paused, booked, completed
    sequence_step       INTEGER DEFAULT 0,      -- LinkedIn DM step (0–5)
    email_sequence_step INTEGER DEFAULT 0,      -- Cold email step (0–4)
    last_dm_sent_at     TEXT,
    last_email_sent_at  TEXT,
    last_reply_at       TEXT,
    booking_date        TEXT,
    created_at          TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at          TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE activities (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id       INTEGER REFERENCES leads(id),
    activity_type TEXT NOT NULL,  -- dm_sent, email_sent, reply_received, booked, status_changed
    content       TEXT,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE config (
    key   TEXT PRIMARY KEY,
    value TEXT
);
```

**Config keys and defaults:**

| Key | Default | Description |
|-----|---------|-------------|
| `dry_run` | `1` | `1` = log only, `0` = live sends |
| `dms_per_hour` | `8` | LinkedIn DM rate limit / hour |
| `dms_per_day` | `50` | LinkedIn DM rate limit / day |
| `delay_minutes` | `5` | Min delay between DMs |
| `delay_variance` | `10` | Extra random delay (min) |
| `emails_per_hour` | `10` | Email rate limit / hour |
| `emails_per_day` | `50` | Email rate limit / day |
| `email_delay_minutes` | `2` | Min delay between emails |

---

## 6. Module Specifications

### `main.py` — CLI Entry Point

| Command | Arguments | Action |
|---------|-----------|--------|
| `init` | — | Initialize / migrate database |
| `scrape` | `--query`, `--location`, `--max` | Scrape leads from LinkedIn |
| `connect` | `--max`, `--delay` | Send connection requests |
| `check-connections` | — | Check pending connection status |
| `sequence` | — | Run next LinkedIn DM step |
| `email` | `--to`, `--subject`, `--body` | Send single test email via Resend |
| `email-sequence` | — | Run next cold email step |
| `add-email` | `lead_id`, `email_address` | Assign email address to a lead |
| `workflow` | `--query`, `--location`, `--max-leads`, `--max-connections` | Full pipeline (both channels) |
| `dashboard` | `--status` | Unified DM + Email dashboard |
| `lead` | `lead_id` | Full lead detail (DM step, Email step, activity log) |
| `reply` | `lead_id`, `reply_type` | Simulate reply (dry-run only) |
| `config` | `key`, `value` | Get / set config values |

### `database.py` — Database Layer

| Function | Description |
|----------|-------------|
| `get_db()` | SQLite connection with `Row` factory |
| `init_db()` | Create tables + seed default config |
| `get_config(key)` | Read config value |
| `set_config(key, value)` | Write config value |
| `is_dry_run()` | Returns `True` if `dry_run == "1"` |
| `log_activity(lead_id, type, content)` | Insert activity log row |
| `get_daily_count(action_type)` | Retrieve daily action counter |
| `increment_daily_count(action)` | Increment the daily action counter |

### `models/lead.py` — Lead CRUD

| Function | Description |
|----------|-------------|
| `get_all_leads()` | All leads ordered by `created_at DESC` |
| `get_lead_by_id(id)` | Single lead |
| `get_leads_by_status(status)` | Filtered by status |
| `add_lead(url, name, headline, company, location)` | Insert or return existing |
| `update_lead_status(id, status, step?)` | Status + optional step update |
| `update_lead_dm_sent(id, step)` | DM step + `last_dm_sent_at` |
| `update_lead_email(id, email)` | Set/update email address |
| `update_lead_email_sent(id, step)` | Email step + `last_email_sent_at` |
| `get_lead_stats()` | Aggregate counts by status + email counts |

### `services/scraper.py` — LinkedIn Scraper

**Auth:** Persistent browser state loaded from `./data/browser_state`. Initiate by running `uv run python -m salesbud login`.

**Flow:**
1. Launch headless Chromium, inject session cookie
2. Navigate `linkedin.com/search/results/people?keywords=...`
3. Detect security challenge → abort if found
4. Extract profile IDs via regex `/in/([a-zA-Z0-9-]+)`
5. Per profile: extract name, headline, company from DOM/JSON
6. `add_lead()` with dedup on LinkedIn URL

**Dry-run fallback:** Inserts 5 hardcoded sample leads.

### `services/connector.py` — Connection Manager

**Flow:**
1. Get `new` leads up to `max_requests`
2. Navigate to profile → find Connect button 
   - Strict scoping to `main section` (top card) to avoid sidebar profiles
   - Fallback to clicking "More" to find hidden Connect options
3. Click Connect → Add a Note → fill note template → Send
4. Update status to `connection_requested` (aborts cleanly if no button found)

**Check flow:** Visits profile → Message button = connected, Pending = still waiting, Connect = declined.

### `services/sequence.py` — DM Sequence Engine

**5-step NEPQ templates** with `{name}`, `{headline}`, `{company}`, `{industry}`, `{pain}`, `{challenge}`, `{company_size}`.

**Personalization:** Headline keyword detection → sets `industry` (marketing / sales / startup / B2B SaaS default).

**Flow:** New connected leads → Step 1 immediately. Subsequent steps: 3-day elapsed check → send → log → enforce hourly rate limit → Step 5 → `completed`.

### `services/emailer.py` — Cold Email Engine

**4-step sequence** (from sales playbook):

| Step | Name | Day | Subject |
|------|------|-----|---------|
| 1 | Value-First | 0 | "Built this for {company} — took 3 mins" |
| 2 | Case Study | 3 | "How a similar agency saved 20h/week" |
| 3 | Soft Offer | 7 | "Free automation audit for {company}" |
| 4 | Break-Up | 14 | "Permission to close your file?" |

| Function | Description |
|----------|-------------|
| `send_email(to, subject, html, text)` | Resend API call (or dry-run log) |
| `personalize_email(lead, step)` | Template → subject + body for lead |
| `send_cold_email(lead, step)` | Personalize + send + log to activities |
| `get_leads_ready_for_email_start()` | Email set, `email_sequence_step == 0` |
| `get_leads_due_for_email(min_days)` | Due for next step by elapsed days |
| `run_email_sequence_step()` | One tick across all eligible leads |

### `cli/dashboard.py` — Terminal Dashboard

- Color-coded ANSI table: ID | Name | Status | DM (x/5) | Email (x/4) | 📧 | Company
- Header stats: Pipeline summary + Email summary
- Config block: LinkedIn limits + Email limits
- `lead <id>`: full detail with last DM, last email, activity log (last 10)

---

## 7. Authentication

| Method | Configuration | Priority |
|--------|---------|----------|
| Persistent Browser State | `./data/browser_state` cache (via `login` command) | Primary |
| LinkedIn credentials | `LINKEDIN_EMAIL` + `LINKEDIN_PASSWORD` | Fallback |
| Resend | `RESEND_API_KEY` | Required for email |
| Sender address | `RESEND_FROM_EMAIL` | e.g. `Rhigden <rhigden@syntolabs.xyz>` |

> [!WARNING]
> LinkedIn sessions expire. If you hit a login wall or 0 leads, run `uv run python -m salesbud login` to authenticate and save session state.

---

## 8. Dry-Run Mode

When `dry_run = 1` (default):

| Component | Behavior |
|-----------|----------|
| Scraping | Inserts 5 hardcoded sample leads if no credentials |
| Connection requests | Logs to console, does not navigate |
| DM sending | `[DRY RUN] Would send:` + content, logs to activity table |
| Email sending | `[DRY RUN] Would send email:` + subject, does NOT call Resend |
| Reply detection | Manual via `reply <id> positive` |
| Connection checking | Returns "pending" for all pending leads |

---

## 9. Rate Limiting & Error Handling

**Rate limits:** (Enforced strictly via `get_daily_count` and `increment_daily_count` in the database to prevent abuse across CLI runs).

| Channel | Limit |
|---------|-------|
| LinkedIn DMs/hour | 8 |
| LinkedIn DMs/day | 50 |
| LinkedIn connections/run | ≤10 |
| Emails/hour | 10 |
| Emails/day | 50 |

**Errors:**

| Scenario | Response |
|----------|----------|
| LinkedIn session expired | Prints error, aborts |
| Security challenge detected | Aborts scraping, returns empty |
| Connect button not found | Logs failure, skips lead |
| Playwright timeout | 60s page load, 30s DOM |
| Invalid session cookie JSON | Falls back to credentials |
| Database locked | SQLite default retry |
| Input Validation Failure | Caught by Pydantic models, JSON error returned |
| Unhandled Exceptions | Caught by top-level `main.py` try/except, JSON error returned |

---

## 10. Functional Requirements

### Lead Acquisition
| ID | Requirement | ✓ |
|----|-------------|---|
| L1 | Search query: job title + location | ✅ |
| L2 | LinkedIn auth via session cookie | ✅ |
| L3 | Scrape Sales Navigator results | ✅ |
| L4 | Extract name, headline, company, location, URL | ✅ |
| L5 | Deduplicate by LinkedIn URL | ✅ |
| L6 | Store in SQLite | ✅ |
| L7 | Dry-run: insert sample leads | ✅ |

### LinkedIn DM Sequence
| ID | Requirement | ✓ |
|----|-------------|---|
| S1 | 5-step NEPQ sequence | ✅ |
| S2 | Personalize with name/company/headline | ✅ |
| S3 | 3-day delay between steps | ✅ |
| S4 | Skip if replied/booked/paused | ✅ |
| S5 | Rate limit: 8/hr, 50/day | ✅ |
| S6 | Log each DM to activity table | ✅ |

### Cold Email Sequence
| ID | Requirement | ✓ |
|----|-------------|---|
| E1 | 4-step sequence (Resend) | ✅ |
| E2 | Send from `rhigden@syntolabs.xyz` | ✅ |
| E3 | Personalize per lead | ✅ |
| E4 | Day 0 → 3 → 7 → 14 cadence | ✅ |
| E5 | Rate limit: 10/hr, 50/day | ✅ |
| E6 | `add-email` command | ✅ |
| E7 | Skip leads without email | ✅ |
| E8 | Dry-run mode | ✅ |

### Dashboard
| ID | Requirement | ✓ |
|----|-------------|---|
| D1 | All leads with status | ✅ |
| D2 | DM step (x/5) per lead | ✅ |
| D3 | Email step (x/4) per lead | ✅ |
| D4 | Email indicator (✓/-) | ✅ |
| D5 | Pipeline + email stats | ✅ |
| D6 | Full lead detail view | ✅ |

---

## 11. Success Metrics

| Metric | Target |
|--------|--------|
| Leads scraped/run | 10–50 |
| LinkedIn DMs/day | 30–50 |
| Emails/day | 30–50 |
| Account flag rate | <2% |
| LinkedIn reply rate | ≥8% |
| Email reply rate | ≥15% |
| Booked meetings/week | 1+ |

---

## 12. Post-MVP Roadmap

| Feature | Priority |
|---------|----------|
| LinkedIn reply detection (`inbox.py`) | P0 |
| Cal.com booking auto-trigger | P0 |
| Apollo email enrichment | P0 |
| Daily digest email | P1 |
| Railway cron scheduling | P1 |
| CRM sync (Notion/Airtable) | P2 |

→ See [../future/FUTURE-PRD.md](../future/FUTURE-PRD.md) for full v2.0 spec.
