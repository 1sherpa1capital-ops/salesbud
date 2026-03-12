# Production Ready Testing Plan - SalesBud v1.4.0

> **Goal:** Comprehensive testing of all CLI features in production mode (dry_run = 0) before live deployment

**Date:** March 12, 2026  
**Version:** 1.4.0  
**Mode:** PRODUCTION (Live)  
**Status:** Planning Phase

---

## Pre-Flight Checklist

Before starting tests, verify:
- [ ] LinkedIn session is active (run `login` if needed)
- [ ] Resend API key is configured
- [ ] Database is initialized
- [ ] `icp.toon` has correct ICP definition
- [ ] Dry run is currently ON (we'll turn it OFF after safety checks)

---

## Phase 1: System & Configuration Tests

### 1.1 System Status Verification
**Purpose:** Ensure all systems are green before testing

```bash
cd /Users/guestr/Desktop/syntolabs/salesbud
uv run python -m salesbud status --toon
```

**Expected Results:**
- `dry_run`: Should show current status (start with "1", end with "0")
- `db_ok`: true
- `linkedin_auth`: "cookie" or "credentials"
- `resend_key_set`: true
- `total_leads`: Current count

**Success Criteria:**
- [ ] Database connected
- [ ] LinkedIn authenticated
- [ ] Resend API configured
- [ ] No errors in output

### 1.2 Configuration Tests
**Purpose:** Verify config get/set works in production

```bash
# Test 1: Get all config
uv run python -m salesbud config --toon

# Test 2: Get specific key
uv run python -m salesbud config dry_run --toon

# Test 3: Set a value (test in dry-run first, then production)
uv run python -m salesbud config test_key test_value --toon
uv run python -m salesbud config test_key --toon  # Verify it was set
```

**Expected Results:**
- All config commands return valid TOON output
- Values persist between calls
- No logger errors

**Success Criteria:**
- [ ] Config read works
- [ ] Config write works
- [ ] TOON format correct

---

## Phase 2: Lead Generation Pipeline

### 2.1 Lead Scraping
**Purpose:** Test LinkedIn scraping with real search

```bash
# Test with explicit parameters
uv run python -m salesbud scrape --query "CEO" --location "Austin, TX" --max 2 --toon

# Test with icp.toon defaults
uv run python -m salesbud scrape --max 2 --toon
```

**Expected Results:**
- Successfully scrapes 2 real LinkedIn profiles
- Captcha handling works (may require manual solve)
- TOON output with lead data
- Leads saved to database

**Success Criteria:**
- [ ] Scraped leads appear in database
- [ ] LinkedIn URLs are valid
- [ ] No duplicate leads created
- [ ] TOON format has all required fields

### 2.2 Connection Requests
**Purpose:** Send real connection requests (HIGH RISK - LIVE MODE)

**⚠️ WARNING:** This sends REAL LinkedIn connection requests

```bash
# First check dry_run status
uv run python -m salesbud config dry_run

# If dry_run = 1, set to 0 for production test
uv run python -m salesbud config dry_run 0

# Send 1 connection request to test
uv run python -m salesbud connect --max 1 --delay 5 --toon
```

**Expected Results:**
- Sends 1 real connection request
- Updates lead status to "connection_requested"
- Logs activity
- Respects rate limits

**Success Criteria:**
- [ ] Connection request sent successfully
- [ ] Lead status updated in DB
- [ ] Activity logged
- [ ] No rate limit errors

**Rollback:**
```bash
# Revert to dry-run if issues
uv run python -m salesbud config dry_run 1
```

### 2.3 Check Connections
**Purpose:** Verify connection status checking

```bash
# Wait a few minutes, then check
uv run python -m salesbud check-connections --toon
```

**Expected Results:**
- Checks pending connections
- Updates status if accepted
- Returns TOON with connection statuses

**Success Criteria:**
- [ ] Command completes without errors
- [ ] Statuses checked for pending connections

---

## Phase 3: DM & Email Sequences

### 3.1 DM Sequence
**Purpose:** Test 5-step NEPQ DM sequence

**⚠️ WARNING:** Sends REAL LinkedIn DMs

```bash
# Verify dry_run is OFF
uv run python -m salesbud config dry_run

# Run DM sequence step
uv run python -m salesbud sequence --toon
```

**Expected Results:**
- Sends DM to connected leads
- Respects sequence timing (3-day delays)
- Updates sequence_step in database
- Logs all activities

**Success Criteria:**
- [ ] DMs sent to eligible leads
- [ ] sequence_step incremented
- [ ] Activities logged
- [ ] Rate limits respected (8/hr, 50/day)

### 3.2 Email Sequence
**Purpose:** Test 4-step cold email sequence

**Prerequisites:**
- Lead must have email address
- Lead must be in email sequence

```bash
# First, add email to a lead
uv run python -m salesbud add-email <lead_id> test@example.com --toon

# Run email sequence
uv run python -m salesbud email-sequence --toon
```

**Expected Results:**
- Sends email via Resend
- Updates email_sequence_step
- Logs activity

**Success Criteria:**
- [ ] Email sent via Resend
- [ ] email_sequence_step incremented
- [ ] Activity logged
- [ ] Rate limits respected (10/hr, 50/day)

### 3.3 Full Workflow
**Purpose:** Test complete pipeline

```bash
uv run python -m salesbud workflow --max-leads 1 --max-connections 1 --toon
```

**Expected Results:**
- Scrapes leads
- Sends connections
- Runs DM sequence
- Runs email sequence

**Success Criteria:**
- [ ] All steps execute successfully
- [ ] No errors in chain
- [ ] TOON output for each step

---

## Phase 4: Email Discovery & Management

### 4.1 Add Email
**Purpose:** Test manual email assignment

```bash
uv run python -m salesbud add-email <lead_id> founder@company.com --toon
```

**Expected Results:**
- Email saved to lead
- Validation passes
- TOON output confirms

**Success Criteria:**
- [ ] Email saved in database
- [ ] Pydantic validation works
- [ ] Activity logged

### 4.2 Find Email (Single)
**Purpose:** Test browser-based email discovery

```bash
# Quick mode (faster, less verification)
uv run python -m salesbud find-email <lead_id> --quick --toon

# Full mode (slower, SMTP verification)
uv run python -m salesbud find-email <lead_id> --toon
```

**Expected Results:**
- Searches for email via browser
- Attempts SMTP verification (if not --quick)
- Saves found email

**Success Criteria:**
- [ ] Command runs without errors
- [ ] If email found, saved to lead
- [ ] email_source and email_verified set

### 4.3 Find Emails (Batch)
**Purpose:** Test batch email discovery

```bash
uv run python -m salesbud find-emails --max 3 --quick --toon
```

**Expected Results:**
- Processes up to 3 leads
- Discovers emails in parallel
- Updates each lead

**Success Criteria:**
- [ ] Multiple leads processed
- [ ] Results for each lead
- [ ] No errors during batch

### 4.4 Send Test Email
**Purpose:** Test Resend integration

```bash
uv run python -m salesbud email --to delivered@resend.dev -s "Production Test" -b "Testing live email" --toon
```

**Expected Results:**
- Email sent via Resend
- Delivery confirmed
- Activity logged

**Success Criteria:**
- [ ] Email sent successfully
- [ ] Resend API responds
- [ ] sent=true in TOON output

---

## Phase 5: Company Enrichment & Research

### 5.1 Set Company URL
**Purpose:** Test company URL assignment

```bash
uv run python -m salesbud set-company-url <lead_id> https://vercel.com --toon
```

**Expected Results:**
- URL saved to lead
- Pydantic validation passes

**Success Criteria:**
- [ ] company_url saved
- [ ] Validation works

### 5.2 Enrich (Single)
**Purpose:** Test Crawl4AI enrichment

```bash
uv run python -m salesbud enrich <lead_id> --toon
```

**Expected Results:**
- Scrapes company website
- Extracts description, size, signals
- Saves to database

**Success Criteria:**
- [ ] Crawl4AI scrapes successfully
- [ ] company_description populated
- [ ] buying_signals detected
- [ ] enriched_at timestamp set

### 5.3 Enrich All
**Purpose:** Test batch enrichment

```bash
uv run python -m salesbud enrich-all --max 3 --toon
```

**Expected Results:**
- Enriches up to 3 leads
- Processes each one
- Returns results

**Success Criteria:**
- [ ] Multiple leads enriched
- [ ] Results for each

### 5.4 Research (Agent-Browser)
**Purpose:** Test agent-browser integration

```bash
# Ensure company_url is set first
uv run python -m salesbud set-company-url <lead_id> https://vercel.com

# Run research
uv run python -m salesbud research <lead_id> --toon
```

**Expected Results:**
- Opens website via agent-browser
- Captures accessibility snapshot
- Saves 4,000+ chars of data

**Success Criteria:**
- [ ] Agent-browser runs successfully
- [ ] company_research populated
- [ ] Snapshot data is substantial

### 5.5 Personalize
**Purpose:** Test icebreaker generation

```bash
# Requires research data first
uv run python -m salesbud personalize <lead_id> --toon
```

**Expected Results:**
- Reads company_research
- Detects keywords (AI, SaaS, etc.)
- Generates contextual icebreaker
- Saves to personalization_angle

**Success Criteria:**
- [ ] Personalization generated
- [ ] Based on research data
- [ ] personalization_angle saved

---

## Phase 6: Inbox & Reply Management

### 6.1 Check Replies
**Purpose:** Test LinkedIn inbox scanning

```bash
uv run python -m salesbud check-replies --toon
```

**Expected Results:**
- Scans LinkedIn inbox
- Detects replies from leads
- Classifies intent (positive/neutral/negative)
- Auto-pauses sequences on reply

**Success Criteria:**
- [ ] Inbox scanned successfully
- [ ] Replies detected if present
- [ ] Lead statuses updated
- [ ] Activities logged

---

## Phase 7: Dashboard & Monitoring

### 7.1 Dashboard
**Purpose:** Test dashboard display

```bash
uv run python -m salesbud dashboard --toon
```

**Expected Results:**
- Shows stats (total, new, active, etc.)
- Lists all leads
- Shows DM and Email progress
- TOON format with complete data

**Success Criteria:**
- [ ] Dashboard renders
- [ ] Stats accurate
- [ ] All leads listed
- [ ] TOON format valid

### 7.2 Lead Detail
**Purpose:** Test individual lead view

```bash
uv run python -m salesbud lead <lead_id> --toon
```

**Expected Results:**
- Shows full lead details
- Lists activities
- Shows sequences progress

**Success Criteria:**
- [ ] Lead data complete
- [ ] Activities shown
- [ ] TOON format valid

---

## Phase 8: Production Readiness Verification

### 8.1 Run Production Check Script
**Purpose:** Final validation before go-live

```bash
uv run python scripts/prod_check.py
```

**Expected Results:**
- All checks pass (green ✓)
- No warnings or errors
- Confirms production ready

**Success Criteria:**
- [ ] Database check: PASS
- [ ] Dry run status: OFF
- [ ] Rate limits: Configured
- [ ] Lead database: Operational
- [ ] All checks: PASS

### 8.2 Final Status Check
**Purpose:** Confirm system is production-ready

```bash
uv run python -m salesbud status --toon
```

**Verify:**
- [ ] dry_run = "0" (OFF)
- [ ] db_ok = true
- [ ] linkedin_auth is set
- [ ] resend_key_set = true
- [ ] All rate limits configured

---

## Test Execution Order

### Recommended Sequence:

**Day 1 - Setup & Low-Risk Tests:**
1. Phase 1: System & Config
2. Phase 4: Email Discovery (use test emails)
3. Phase 5: Enrichment & Research
4. Phase 7: Dashboard & Monitoring

**Day 2 - Medium-Risk Tests:**
5. Phase 2: Lead Scraping (small batch)
6. Phase 4: Send Test Email

**Day 3 - High-Risk Tests (Live Mode):**
7. Turn OFF dry_run mode
8. Phase 2: Connection Requests (1-2 max)
9. Phase 3: DM Sequence (if connections accepted)
10. Phase 6: Check Replies

**Day 4 - Validation:**
11. Phase 8: Production Readiness
12. Monitor for 24 hours

---

## Rollback Plan

If any test fails:

```bash
# Immediately revert to dry-run
uv run python -m salesbud config dry_run 1

# Check system status
uv run python -m salesbud status --toon

# Review recent activities
uv run python -m salesbud dashboard
```

---

## Success Criteria Summary

### Must Pass (Critical):
- [ ] System status shows all green
- [ ] Can scrape leads successfully
- [ ] Can send connection requests (in production mode)
- [ ] Can send emails via Resend
- [ ] Dashboard shows accurate data
- [ ] Production check script passes

### Should Pass (Important):
- [ ] Email discovery works
- [ ] Enrichment captures company data
- [ ] Agent-browser research works
- [ ] Personalization generates icebreakers
- [ ] Reply detection functions

### Nice to Pass (Enhancement):
- [ ] Batch operations work efficiently
- [ ] Rate limiting prevents overages
- [ ] All TOON outputs valid
- [ ] Activities properly logged

---

## Sign-Off Checklist

Before declaring production ready:

- [ ] All Phase 1 tests passed
- [ ] All Phase 2 tests passed (with dry_run=0)
- [ ] All Phase 3 tests passed (with dry_run=0)
- [ ] All Phase 4 tests passed
- [ ] All Phase 5 tests passed
- [ ] All Phase 6 tests passed
- [ ] All Phase 7 tests passed
- [ ] Phase 8 production check passes
- [ ] No critical bugs found
- [ ] Rollback tested and works
- [ ] Monitoring in place
- [ ] Documentation updated

---

**Ready to Execute?** 
This plan covers all 26 CLI commands across 8 phases. Estimated time: 2-4 days depending on LinkedIn response times.
