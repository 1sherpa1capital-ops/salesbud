# SalesBud — Product Requirements Document

**Version:** 2.0 (Rolling out / v1.3.0 Live)
**Date:** March 11, 2026
**Status:** Active Development — v1.3.0 base exists (production hardened), v2.0 gaps identified
**Philosophy:** Build a rock-solid CLI. Let AI agents (OpenCode / Claude Code) be the UI.

---

## 1. Vision

SalesBud is a **two-channel outbound pipeline** that a person OR an AI agent can operate entirely from the command line.

**The mental model:**
```
You (or OpenCode/Claude Code)
        ↓  natural language
    "Find 20 CEOs in Austin and start both sequences"
        ↓  AI agent translates to CLI commands
python -m salesbud workflow --query "CEO" --location "Austin" --max-leads 20
        ↓  CLI executes, returns structured output
        ↓  AI reads output, decides next step
```

**Why this design:**
- OpenCode and Claude Code already read terminal output and run follow-up commands autonomously
- The CLI surface becomes a machine-readable API the AI can compose and sequence
- No web UI to build — the TUI (OpenCode) IS the UI
- Every feature is testable, scriptable, and auditable

---

## 2. Current State (v1.1 — Built ✅)

| Feature | Status |
|---------|--------|
| LinkedIn scraping (Playwright) | ✅ Working |
| LinkedIn connection requests | ✅ Working |
| 5-step NEPQ DM sequence | ✅ Working (dry-run only — see Section 2A) |
| 4-step cold email via Resend | ✅ Working |
| Unified CLI dashboard | ✅ Working |
| Dry-run mode | ✅ Working |
| Manual `add-email` | ✅ Working |
| Production Hardening (Pydantic, Limits, Idempotency) | ✅ Working (v1.3.0) |

---

## 2A. Current Implementation Reality

**Brutally honest snapshot of what actually exists in code vs. what the PRD claims.**

### What's confirmed working (code-verified)

**CLI commands in `main.py`:** `init`, `scrape`, `connect`, `check-connections`, `sequence`, `email`, `email-sequence`, `add-email`, `find-email`, `find-emails`, `workflow`, `dashboard`, `lead`, `reply`, `config`, `status`, `enrich`, `enrich-all`, `check-replies`, `test`, `help` — **20 commands total.**

**Database schema (`database.py`):**
```
leads: id, linkedin_url, name, headline, company, location, email,
       status, sequence_step, email_sequence_step, last_dm_sent_at,
       last_email_sent_at, last_reply_at, booking_date, created_at, updated_at,
       email_source, email_verified, company_url, company_description,
       company_size_est, buying_signals, enriched_at
activities: id, lead_id, activity_type, content, created_at
config: key, value (with 8 default keys)
```

**Services that exist:** `scraper.py`, `connector.py`, `sequence.py`, `emailer.py`, `email_finder.py`, `enricher.py`, `inbox.py` — all present.

**What's actually implemented end-to-end:**
- LinkedIn scraping: real Playwright code, session cookie auth, dry-run fallback with 5 sample leads
- Connection requests: real Playwright code (3-selector fallback), dry-run logs only
- DM sending: real Playwright code for production mode, dry-run logs only
- Email via Resend: fully implemented, dry-run mode works correctly
- Email sequence (4-step): logic complete, personalization working
- Dashboard: shows both DM (x/5) and email (x/4) columns — confirmed
- JSON output: all commands support `--json` flag
- Status command: returns system health with DB/path/queue/auth status
- Email discovery: browser-based discovery + SMTP verification
- Company enrichment: Crawl4AI-powered scraping
- Inbox checking: Playwright-based LinkedIn inbox scanning
- AGENTS.md: complete CLI reference at repo root

### All v2.0 features now implemented

All previously identified gaps have been closed:
- ✅ Real LinkedIn DM sending in production mode
- ✅ JSON output on all commands
- ✅ Status command for health checks
- ✅ Email discovery (find-email, find-emails)
- ✅ Company enrichment (enrich, enrich-all)
- ✅ Reply detection (check-replies)
- ✅ AGENTS.md at repo root
- ✅ Location search fixed (uses keywords, not hardcoded geoUrn)
- ✅ sqlite3 import moved to top of lead.py

### Remaining items (external dependencies)

These require user action to complete:
- Install `crawl4ai`, `dnspython`, `bs4` for email discovery and enrichment
- Install `agent-browser` CLI for advanced browsing
- Resend bounce webhook for email verification feedback
- Optional: cron/launchd setup for scheduling

---

## 3. Problems to Solve in v2.0

| Problem | Impact |
|---------|--------|
| No `--json` output — AI agents can't parse CLI output | **Blocks Mode B entirely** |
| DM send in production is a stub — no real Playwright DM sending | **Sequences don't actually work live** |
| No email discovery — manual `add-email` only | Requires manual research per lead |
| No web enrichment — can't personalize beyond LinkedIn headline | Generic messaging |
| No reply detection — must manually check LinkedIn inbox | Missed replies, sequences don't auto-pause |
| No `status/cron/digest/find-email/enrich/check-replies` commands | Missing Mode B surface |
| No `AGENTS.md` — AI agent has no CLI reference | AI must guess commands |
| Location search uses hardcoded US geoUrn | International searches broken |
| No parameterless search | CLI forces explicit long `--query` | AI must guess ICP |

---

## 4. Users & Usage Modes

### Mode A: Human-in-the-loop (Current)
Rhigden runs commands manually each morning. Reviews dashboard. Adds emails.

### Mode B: AI-Operated (Target)
OpenCode or Claude Code reads `AGENTS.md`, understands the CLI, and operates SalesBud autonomously. Rhigden says: *"Run the workflow for CFOs in NYC, max 15 leads, get emails, start both sequences."* The agent does the rest.

**For Mode B to work, the CLI needs:**
- `--json` output flags on every command (machine-readable)
- Clear exit codes (0 = success, 1 = error, 2 = rate-limited, 3 = nothing to process)
- Idempotent commands (safe to re-run)
- A `status` command the AI can poll
- An `AGENTS.md` at the repo root with the full CLI reference
- A local `icp.json` definition for zero-config searching

**The agent-browser + SalesBud CLI combo for email discovery:**
```bash
# AI agent discovers email using agent-browser:
agent-browser open https://company.com/team && agent-browser snapshot -i
# (AI reads snapshot, finds email pattern)
python -m salesbud add-email 42 found@company.com --json
python -m salesbud email-sequence --json
```

---

## 5. Tools & Technology Decisions

### 5.1 Browser Automation — Playwright + agent-browser (CLI) + browser-use

| Tool | Role | How Used | Cost |
|------|------|----------|------|
| **Playwright** | LinkedIn scraping, DM sending, connection requests | Our Python code drives it directly | Free |
| **agent-browser** | Ad-hoc browsing by OpenCode/Claude Code agent | AI calls `agent-browser open <url>` from terminal | Free |
| **browser-use** | Python-level AI-steered browser loops | Called from `services/` for email discovery | Free |

**agent-browser IS a CLI** (vercel-labs/agent-browser). Not yet installed — install with:
```bash
npm install -g @vercel-labs/agent-browser
agent-browser install   # downloads browser binaries
agent-browser --version
```

> [!WARNING]
> **LinkedIn Session Risk:** Sessions expire if not kept active. Beyond expiry, all LinkedIn operations silently fail or redirect to login. Mitigations required:
> - Run `uv run python -m salesbud login` to launch a browser, map the session, and save it to `./data/browser_state` before running campaigns.
> - Add jitter to all Playwright timing: use `page.wait_for_timeout(random.randint(2000, 5000))` not fixed waits
> - Randomize delays between actions: currently `connector.py` uses fixed `time.sleep(delay_seconds)` — should use `delay_seconds + random.randint(-10, 30)`
> - Add explicit login-state check before each Playwright session and abort with clear error if not authenticated

### 5.2 Web Scraping — Crawl4AI

Open source Python library (MIT, 40k+ GitHub stars). Built on Playwright. Converts any web page into structured JSON or LLM-ready Markdown.

```bash
pip install crawl4ai && crawl4ai-setup
```

**Use cases in SalesBud:**
- `enrich <id>` → scrape company homepage → populate description, size estimate, tech stack
- Identify buying signals (hiring pages, press releases, fundraising news)
- Scrape G2/Capterra for warm leads actively researching tools

### 5.3 Email Discovery — Browser-Based (No API Keys Needed)

**Decision: No Hunter/Prospeo/Tomba APIs. Use agent-browser + browser-use + web search instead.**

Free API tiers (25–75/mo) are too low. Browser-based discovery is unlimited, free, and already in our stack.

**How it works for each lead with no email:**
```
1. browser-use searches: "firstname lastname company email" on DuckDuckGo
2. agent-browser opens company website → checks /team, /about, /contact
3. Pattern guess: first@company.com, first.last@company.com, flast@company.com
4. SMTP-verify the candidate email (DNS MX lookup + RCPT TO ping, no API)
5. Store confirmed email → start email sequence
```

**CLI commands:**
```bash
python -m salesbud find-email <id>      # browser-use powered, SMTP verified
python -m salesbud find-emails --max 10 # batch for connected leads without email
```

> [!WARNING]
> **SMTP RCPT TO Risk:** Google Workspace (gmail.com domains and G Suite) and Microsoft 365 (outlook.com and hosted Exchange) both **block SMTP RCPT TO probing** — they return a 250 OK even for non-existent addresses, making verification unreliable.
>
> **Recommended fallback strategy:**
> 1. Pattern-guess the email address from name + company domain
> 2. Attempt to send Step 1 email via Resend
> 3. Monitor Resend bounce webhook (`/webhooks/resend`) → mark `email_verified = 0` and pause sequence on hard bounce
> 4. Do NOT rely on SMTP RCPT TO as ground truth for Google/M365 domains

**SMTP verification (use only for custom domains, not Google/M365):**
```python
# services/email_verifier.py
import smtplib, dns.resolver
def verify_smtp(email: str) -> bool:
    domain = email.split('@')[1]
    # Skip SMTP check for known anti-probe domains
    BLOCKED_DOMAINS = {'gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com'}
    if domain in BLOCKED_DOMAINS:
        return True  # Assume valid, let Resend bounce handle it
    mx = dns.resolver.resolve(domain, 'MX')[0].exchange.to_text()
    with smtplib.SMTP(mx, timeout=10) as s:
        s.helo(); s.mail('')
        code, _ = s.rcpt(email)
    return code == 250
```

**Dependencies added:** `dnspython` (MX lookups), `crawl4ai`, `browser-use`.

### 5.4 AI Agent UI — OpenCode + Claude Code

**OpenCode** ([github.com/sst/opencode](https://github.com/sst/opencode)):
- Open source terminal TUI, model-agnostic (Claude / GPT-4o / Gemini)
- Reads files, runs shell commands, maintains session context
- User speaks naturally → agent composes CLI commands → reads JSON output → continues

**Claude Code** (Anthropic) — same idea, Claude-native, better for long multi-step tasks.

**`AGENTS.md` at repo root** tells OpenCode/Claude Code how to drive SalesBud.

---

## 6. Known Gaps & Risks

### Gap Analysis Table

| PRD Section | Feature | Status | Notes |
|-------------|---------|--------|-------|
| Phase 1 | `--json` flag on all commands | ✅ DONE | Added to all commands |
| Phase 1 | `status` command | ✅ DONE | Implemented with --json |
| Phase 1 | Structured exit codes | ✅ DONE | 0/1/2/3 defined in main.py |
| Phase 1 | `--quiet` flag | ⚪ DEFERRED | Not critical for v2.0 |
| Phase 2 | `find-email <id>` | ✅ DONE | email_finder.py + CLI |
| Phase 2 | `find-emails --max N` | ✅ DONE | email_finder.py + CLI |
| Phase 2 | SMTP email verification | ✅ DONE | verify_smtp in email_finder.py |
| Phase 2 | `email_source` DB column | ✅ DONE | Added to schema |
| Phase 2 | `email_verified` DB column | ✅ DONE | Added to schema |
| Phase 3 | `enrich <id>` | ✅ DONE | enricher.py + CLI |
| Phase 3 | `enrich-all --max N` | ✅ DONE | enricher.py + CLI |
| Phase 3 | `company_url` DB column | ✅ DONE | Added to schema |
| Phase 3 | `company_description` DB column | ✅ DONE | Added to schema |
| Phase 3 | Buying signals detection | ✅ DONE | Part of enricher.py |
| Phase 4 | `check-replies` command | ✅ DONE | inbox.py + CLI |
| Phase 4 | Reply auto-pause | ✅ DONE | Part of check-replies |
| Phase 4 | Cal.com booking link on reply | ⚪ DEFERRED | Manual for now |
| Phase 5 | `cron` command | ⚪ DEFERRED | Not in v2.0 scope |
| Phase 5 | `digest` command | ⚪ DEFERRED | Not in v2.0 scope |
| Phase 5 | Railway / local scheduling | ⚪ DEFERRED | Use launchd/cron manually |
| v1.1 | Real LinkedIn DM send (production) | ✅ DONE | Playwright in send_dm() |
| v1.1 | Location-aware scraping | ✅ DONE | Keywords include location |
| v1.1 | LinkedIn scraping | ✅ DONE | Full Playwright implementation + Stealth |
| v1.1 | Connection requests | ✅ DONE | Full Playwright implementation (Handles missing Connect buttons strictly, avoids sidebars) |
| v1.1 | 5-step DM sequence (logic) | ✅ DONE | Dry-run + production |
| v1.1 | 4-step email via Resend | ✅ DONE | Full implementation |
| v1.1 | Unified dashboard | ✅ DONE | DM + Email columns |
| v1.1 | Dry-run mode | ✅ DONE | Both channels |
| v1.1 | `add-email` command | ✅ DONE | Confirmed |
| v1.1 | `config` command | ✅ DONE | Get/set all keys |
| v1.1 | Rate limiting (DMs) | ✅ DONE | dms_per_hour enforced |
| v1.1 | Rate limiting (email) | ✅ DONE | emails_per_hour enforced |
| Code quality | `sqlite3` import at bottom of `lead.py` | ✅ DONE | Moved to top |
| Code quality | `agent-browser` not installed | ⚪ DEFERRED | User to install |
| Code quality | `crawl4ai`, `browser-use`, `dnspython` not installed | ⚪ DEFERRED | User to install |

---

## 7. Feature Roadmap

### Phase 1 — Make the CLI AI-Readable (Week 1) 🔴 CRITICAL

These are low-effort, high-leverage changes. **Mode B is impossible without them.**

| Feature | Command | Notes |
|---------|---------|-------|
| `--json` flag on all commands | All 14 commands | Return `{"success": bool, "count": int, "data": [...]}` |
| `status` command | `python -m salesbud status` | DB counts, rate limit state, dry_run, mode |
| Structured exit codes | All commands | 0=ok, 1=error, 2=rate-limited, 3=nothing to process |
| `--quiet` flag | All commands | Suppress human-readable output for scripting |
| `icp.json` parsing | `scrape`, `workflow` | Load `--query`/`--location` from `icp.json` if omitted |
| Fix real DM send | `sequence` | Add Playwright messaging code to `send_dm()` |

### Phase 2 — Email Discovery (Week 1-2)

| Feature | Command | Tool | Notes |
|---------|---------|------|-------|
| Find email for one lead | `find-email <id>` | browser-use web search + agent-browser | SMTP-verified |
| Batch email discovery | `find-emails --max N` | Same, one at a time | No rate limits |
| SMTP verification | Auto on find | smtplib + dnspython | Skip Google/M365 domains |
| Resend bounce webhook | `/webhooks/resend` | Resend webhook handler | Mark bounced emails |
| Email source tracking | DB column | `email_source` field | Track how email was found |

### Phase 3 — Web Enrichment (Week 2-3)

| Feature | Command | Tool | Notes |
|---------|---------|------|-------|
| Enrich company data | `enrich <id>` | Crawl4AI | Scrape company homepage |
| Batch enrich | `enrich-all --max N` | Crawl4AI | All connected leads |
| Store company data | DB columns | `company_description`, `company_size_est` | Better personalization |
| Buying signal detection | Part of enrich | keyword scan | Hiring? Fundraising? |

### Phase 4 — Reply Detection (Week 3-4)

| Feature | Command | Tool | Notes |
|---------|---------|------|-------|
| Scan LinkedIn inbox | `check-replies` | Playwright | Navigate messaging, parse threads |
| Classify reply intent | Auto | Keyword rules | positive/neutral/negative |
| Auto-pause sequence | Auto | On any reply | Status → `replied` |
| Send Cal.com link on positive | Auto | Hardcoded URL initially | DM booking link |

### Phase 5 — Scheduling (Week 4+)

| Feature | Notes |
|---------|-------|
| `cron` command | Full morning pipeline in one call |
| `digest` command | Send daily summary email via Resend |
| Local scheduling | macOS `launchd` plist (not Railway — see cost note below) |

---

## 8. Updated CLI Surface

### Current Commands (v1.1) — all confirmed in code
```bash
init, scrape, connect, check-connections, sequence,
email, email-sequence, add-email, workflow, dashboard, lead, reply, config, test
```

### New Commands (v2.0)
```bash
# Machine-readable output (Phase 1)
<any command> --json         # {"success": bool, "count": int, "data": [...]}
<any command> --quiet        # Suppress output for scripting
status                       # System health JSON
scrape                       # Uses local icp.json if query/location omitted

# Email discovery (Phase 2)
find-email <id>              # browser-use + SMTP verify for one lead
find-emails --max N          # Batch discovery for connected leads

# Web enrichment (Phase 3)
enrich <id>                  # Crawl4AI scrape of company URL
enrich-all --max N           # Batch enrich connected leads

# Inbox & replies (Phase 4)
check-replies                # Playwright scan of LinkedIn inbox

# Scheduling (Phase 5)
cron                         # Full morning workflow (for launchd/cron)
digest                       # Send daily email summary
```

---

## 9. AI Agent Reference (`AGENTS.md` Additions)

The following must be added to `AGENTS.md` at the repo root before Mode B is usable:

```markdown
## SalesBud CLI Reference for AI Agents

### Always start with:
python -m salesbud status --json

### Discover current state:
python -m salesbud dashboard --json

### Find leads (reads --query/--location from icp.json if omitted):
python -m salesbud scrape --json
# Or specify explicitly:
python -m salesbud scrape --query "CEO" --location "Austin" --max 20 --json

### Discover emails (for leads without email):
python -m salesbud find-emails --max 10 --json
# OR: use agent-browser to find email manually, then:
python -m salesbud add-email <id> <email> --json

### Run sequences:
python -m salesbud sequence --json
python -m salesbud email-sequence --json

### Check for replies:
python -m salesbud check-replies --json

### All JSON output follows this schema:
{"success": bool, "count": int, "data": [...], "errors": [...]}

### Exit codes:
0 = success
1 = error (check "errors" field)
2 = rate-limited (try again later)
3 = nothing to process (no leads due)

### Key rules:
- Always check dry_run status first: python -m salesbud config dry_run
- Do not run workflow in production until dry_run = 0 is confirmed
- If scrape returns 0 leads, LinkedIn session cookie may be expired
- add-email is the fallback for email discovery if find-email fails
```

---

## 10. Database Schema (Current + v2.0 Additions)

### Current schema (confirmed in code)
```sql
leads: id, linkedin_url, name, headline, company, location, email,
       status, sequence_step, email_sequence_step,
       last_dm_sent_at, last_email_sent_at, last_reply_at,
       booking_date, created_at, updated_at
```

### v2.0 additions needed
```sql
ALTER TABLE leads ADD COLUMN company_url TEXT;
ALTER TABLE leads ADD COLUMN company_description TEXT;
ALTER TABLE leads ADD COLUMN company_size_est TEXT;
ALTER TABLE leads ADD COLUMN buying_signals TEXT;       -- JSON list
ALTER TABLE leads ADD COLUMN email_source TEXT;        -- browser/manual/smtp-guess
ALTER TABLE leads ADD COLUMN email_verified INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN enriched_at TEXT;
```

---

## 11. Cost Stack (v2.0)

| Tool | Version / Cost | Notes |
|------|----------------|-------|
| LinkedIn automation | Playwright 1.58.0 — Free | 50 DMs/day |
| Cold email delivery | Resend 2.23.0 — Free (2,000/mo) | 2,000 emails/month |
| Email discovery | browser-use + agent-browser + SMTP — Free | Unlimited, no credit caps |
| Web enrichment | Crawl4AI — Free (open source) | Unlimited |
| AI UI | OpenCode — Free (open source) | Model of your choice |
| agent-browser CLI | vercel-labs/agent-browser — Free (npm) | Install once |
| Email verification | dnspython + smtplib — Free | MX + RCPT TO check |
| Scheduling | macOS `launchd` — Free | Use local cron, not Railway |
| Database | SQLite — Free | Built-in |

> [!NOTE]
> **Railway removed from cost stack.** Railway's free tier was sunset in 2023. Hobby tier starts at $5/month and requires credit card. For now, use `launchd` (macOS) or `cron` (Linux) for local scheduling. Add Railway/Fly.io as a paid option in the future PRD only.

**Total monthly cost: $0 — unlimited volume, no API credit caps**

---

## 12. Acceptance Criteria (v2.0 Complete)

### Confirmed complete (code-verified)
- [x] LinkedIn scraping works with session cookie
- [x] Connection requests sent via Playwright (dry-run + live)
- [x] 5-step DM sequence logic exists and runs (dry-run confirmed)
- [x] 4-step email sequence via Resend works end-to-end
- [x] Dashboard shows DM (x/5) and Email (x/4) per lead
- [x] Dry-run mode for both channels
- [x] `add-email` assigns email to lead and starts sequence on next run
- [x] `config` command reads/writes all 8 config keys
- [x] Rate limiting enforced for both DMs and emails

### Not yet complete (must pass before v2.0 ship)
- [x] `--json` flag works on all 14+ commands, output parseable by `json.loads()`
- [x] `status --json` returns system health without DB writes
- [x] Exit codes: 0=ok, 1=error, 2=rate-limited, 3=nothing-to-process
- [x] `AGENTS.md` exists at repo root with full CLI reference
- [x] Real LinkedIn DM send implemented in `send_dm()` production path
- [x] Location search uses correct geoUrn for the provided `--location` arg
- [x] `find-email <id>` uses browser-use and stores SMTP-verified result
- [x] `find-emails --max 10` batch discovers emails for connected leads
- [x] `enrich <id>` uses Crawl4AI to scrape company URL and store description
- [x] `check-replies` scans LinkedIn inbox and auto-pauses sequences for replies
- [ ] agent-browser installed and callable (`agent-browser --version` works)
- [ ] `crawl4ai`, `browser-use`, `dnspython` installed (`uv sync`)
- [x] `sqlite3` import moved to top of `lead.py`
- [ ] Resend bounce webhook endpoint created (or documented manual process)
- [ ] `cron` command runs full morning pipeline in one call

---

## 13. Go-Live Checklist

### Pre-Flight Verification Commands

```bash
# 0. Production readiness check
uv run python scripts/prod_check.py

# 1. Initialize database (or migrate)
python -m salesbud init
python -m salesbud init --json

# 2. Check system status
python -m salesbud status
python -m salesbud status --json

# 3. Check config
python -m salesbud config
python -m salesbud config dry_run

# 4. Verify dashboard
python -m salesbud dashboard

# 5. Test email (dry-run first)
python -m salesbud email --to test@example.com -s "Test" -b "Hello"

# 6. Run sequence (dry-run)
python -m salesbud sequence
python -m salesbud sequence --json

# 7. Run email sequence (dry-run)
python -m salesbud email-sequence
python -m salesbud email-sequence --json
```

### Steps to Go Live

1. **Turn off dry-run mode:**
   ```bash
   python -m salesbud config dry_run 0
   ```

2. **Authenticate with LinkedIn:**
   - Run `uv run python -m salesbud login` to open a headed browser and store your credentials session natively.

3. **Live email test (use Resend safe address):**
   ```bash
   python -m salesbud email --to delivered@resend.dev -s "Test" -b "Testing SalesBud live"
   ```

4. **Live connection request test:**
   ```bash
   python -m salesbud connect --max 1
   ```

5. **Monitor:**
   - Resend dashboard for delivery/bounces
   - LinkedIn for connection accepts
   - Run `python -m salesbud dashboard` to track pipeline

### Post-MVP (Optional)

- Set up cron/launchd for morning workflow
- Configure Resend bounce webhook
- Install `agent-browser` for advanced browsing
