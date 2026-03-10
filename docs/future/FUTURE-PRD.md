# SalesBud — Future PRD (Paid APIs)

**Version:** 2.0 (Post-MVP)  
**Date:** March 10, 2026  
**Status:** Planning — build after MVP is live and generating calls  
**Trigger:** Ship when MVP produces 3+ booked calls in 2 weeks

---

## 1. Vision

An always-on autonomous outbound SDR that never sleeps. Rhigden wakes up to booked discovery calls — no manual inputs required.

**Gap from MVP:** MVP requires manual email entry, manual reply handling, and manual scheduling. v2.0 closes all three.

---

## 2. What Changes in v2.0

| Capability | MVP | v2.0 |
|------------|-----|-------|
| Email discovery | Manual `add-email` | Apollo API auto-enrichment |
| Reply detection | Manual `reply` command | LinkedIn inbox scanner (Playwright) |
| Booking | Manual calendar link | Cal.com auto-triggered on positive reply |
| Personalization | Template-based | Claude API (GPT-4o optional) |
| Scheduling | Manual daily CLI | Railway cron (always-on) |
| Monitoring | CLI dashboard | Daily Resend digest email |
| Data output | Local SQLite | Notion/Airtable CRM sync |

---

## 3. New APIs Required

| API | Purpose | Cost |
|-----|---------|------|
| Apollo.io | Email + phone enrichment from LinkedIn profile | $49/mo (Basic, 120 credits/day) |
| Cal.com | Meeting booking via API + webhook confirmation | $0 (free self-hosted) |
| Claude API | AI-powered DM + email personalization | ~$5/mo (Haiku, batch mode) |
| Railway | Cloud hosting + cron scheduling | $5/mo (Hobby plan) |
| Airtable/Notion | CRM for booked leads | $0–$10/mo |

**Estimated monthly cost: ~$60–70/mo** (covers ~200 enrichments + AI + hosting)

---

## 4. New Features (v2.0)

### 4.1 Apollo Email Enrichment

**Service:** `services/enricher.py`

```python
# Auto-enriches connected leads with email from Apollo
python -m salesbud enrich --max 50
# Or automatically runs during workflow
python -m salesbud workflow --auto-enrich
```

**Flow:**
1. Get connected leads with no email address
2. Call Apollo `/people/match` with name + LinkedIn URL
3. Extract email and phone
4. `update_lead_email()` + log to activities
5. Email sequence auto-starts on next `email-sequence` run

**Rate limit:** Apollo Basic = 120 credits/day (~4 credits/match)

---

### 4.2 LinkedIn Reply Detection

**Service:** `services/inbox.py`

```python
# Check LinkedIn inbox for new replies from leads in sequence
python -m salesbud check-replies
```

**Flow:**
1. Launch Playwright, navigate to `linkedin.com/messaging`
2. Scan recent messages for senders who match leads in `active` status
3. For each match: classify reply as `positive / neutral / negative` (keyword matching)
4. `positive/neutral` → update status to `replied`, pause DM sequence
5. `positive` → trigger Cal.com booking link DM
6. Log to activities

**Scheduler:** Run every 30 minutes via Railway cron.

---

### 4.3 Cal.com Booking Integration

**Config:** `CAL_API_KEY` (already in `.env`)

```python
# Triggered automatically after positive reply classification
# Sends booking link via LinkedIn DM or email reply
```

**Flow:**
1. On `positive` classification: get lead's LinkedIn URL
2. Send DM: "Would you be open to a 30-min call? Here's my calendar: cal.com/rhigden"
3. Cal.com webhook → `POST /webhook` → mark lead as `booked`, store `booking_date`
4. Send confirmation Resend email to lead

---

### 4.4 Claude AI Personalization

**Service:** Add to `services/personalize.py`

```python
# Called before sending any DM or email
# Replaces template-based personalization
python -m salesbud workflow --ai-personalize
```

**Prompt structure:**
- System: "You are Rhigden, founder of Synto Labs, reaching out to [role]..."
- User: Lead's headline + company + recent LinkedIn activity
- Output: Personalized DM for the appropriate sequence step

**Model:** `claude-3-haiku-20240307` (cheapest, ~$0.25/1000 messages)

---

### 4.5 Railway Deployment (Always-On)

**`Procfile` or Railway service:**
```
worker: python -m salesbud cron
```

**`cron` command (new):**
```bash
# Runs every morning at 9am ET
09:00 → scrape + connect + check-connections + sequence + email-sequence + check-replies
21:00 → check-replies + send daily digest
```

**Digest email** (via Resend, sent to `rhigden@syntolabs.xyz`):
```
SalesBud Daily Report — March 10
- DMs sent: 12 | Replies: 2 | Positive: 1
- Emails sent: 8 | Opens: 3
- New leads: 5 | Booked: 1 🎉
```

---

### 4.6 CRM Sync

**Option A — Notion** (free):
- Push booked leads to a Notion database via Notion API
- Fields: Name, Company, LinkedIn, Email, Booking Date, Source

**Option B — Airtable** (free up to 1,200 records):
- Same structure, better filtering/views

**Trigger:** On `status = booked`, sync immediately via webhook.

---

## 5. Updated Architecture (v2.0)

```
                     ┌─────────────────┐
                     │  Railway Cron   │
                     │  09:00 / 21:00  │
                     └───────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │   Scraper    │  │  Inbox       │  │  Enricher    │
  │  (LinkedIn)  │  │  (LinkedIn   │  │  (Apollo)    │
  └──────┬───────┘  │   replies)   │  └──────┬───────┘
         │          └──────┬───────┘         │
         │                 │                 │
         ▼                 ▼                 ▼
  ┌──────────────────────────────────────────────────┐
  │                  SQLite Database                  │
  │  leads / activities / config                      │
  └──────────────────────────────────────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │  Connector   │  │  Sequencer   │  │  Emailer     │
  │  (LinkedIn)  │  │  (DMs, LI)   │  │  (Resend)    │
  └──────────────┘  └──────┬───────┘  └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Booker      │
                    │  (Cal.com)   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  CRM Sync    │
                    │  (Notion)    │
                    └──────────────┘
```

---

## 6. New CLI Commands (v2.0)

| Command | Purpose |
|---------|---------|
| `enrich --max N` | Apollo auto-enrich N connected leads |
| `check-replies` | Scan LinkedIn inbox for replies |
| `cron` | Run full scheduled pipeline |
| `digest` | Send daily summary email |
| `webhook start` | Start local webhook server for Cal.com |
| `crm sync` | Push booked leads to Notion/Airtable |

---

## 7. Updated Database Schema (v2.0)

```sql
-- New columns on leads table
ALTER TABLE leads ADD COLUMN phone TEXT;
ALTER TABLE leads ADD COLUMN apollo_id TEXT;
ALTER TABLE leads ADD COLUMN cal_booking_url TEXT;
ALTER TABLE leads ADD COLUMN crm_synced_at TEXT;
ALTER TABLE leads ADD COLUMN enriched_at TEXT;

-- New config keys
INSERT INTO config VALUES ('apollo_api_key', '');
INSERT INTO config VALUES ('cal_api_key', '');
INSERT INTO config VALUES ('notion_api_key', '');
INSERT INTO config VALUES ('claude_api_key', '');
INSERT INTO config VALUES ('cron_enabled', '0');
INSERT INTO config VALUES ('daily_digest_email', 'rhigden@syntolabs.xyz');
```

---

## 8. Success Metrics (v2.0)

| Metric | MVP Target | v2.0 Target |
|--------|------------|-------------|
| Booked calls/week | 1 | 3–5 |
| Manual inputs/day | ~10 min | ~0 min |
| Leads enriched/day | Manual | 50 auto |
| Reply detection | Manual | Real-time |
| Email open rate | — | ≥40% |
| LinkedIn reply rate | ≥8% | ≥12% |

---

## 9. Build Sequence (Post-MVP)

1. **Reply detection** first (`inbox.py`) — enables Cal.com trigger
2. **Cal.com integration** — closes the booking loop
3. **Apollo enrichment** — removes `add-email` bottleneck
4. **Railway cron** — goes fully autonomous
5. **Daily digest** — visibility without opening terminal
6. **CRM sync** — booked leads tracked outside SQLite
7. **Claude personalization** — last, after volume justifies cost
