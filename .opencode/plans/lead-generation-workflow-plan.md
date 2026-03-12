# Lead Generation + Personalization + Connection Workflow Plan

**Goal:** Automated workflow to find leads, research for personalization, send connection requests, and queue personalized follow-up messages

**Mode:** Production (dry_run will be managed carefully)

---

## Workflow Overview

```
1. SCRAPE → Find leads on LinkedIn (icp.toon defaults)
2. SET URL → Set company URLs for enrichment  
3. RESEARCH → Agent-browser company research
4. PERSONALIZE → Generate contextual icebreakers
5. CONNECT → Send connection requests with notes
6. QUEUE DMs → Stage personalized messages for post-connection
```

---

## Phase 1: Lead Discovery

**Objective:** Scrape 5-10 fresh leads from LinkedIn

**Steps:**
1. Check current lead count
2. Scrape using icp.toon defaults (CEO/Founder/VP in 5 cities)
3. Verify leads saved to database

**Commands:**
```bash
cd /Users/guestr/Desktop/syntolabs/salesbud

# Check baseline
uv run python -m salesbud status --toon

# Scrape fresh leads
uv run python -m salesbud scrape --max 5 --toon

# Verify
sqlite3 data/salesbud.db "SELECT id, name, company, location, status FROM leads ORDER BY id DESC LIMIT 5;"
```

**Success Criteria:**
- [ ] 5 new leads scraped successfully
- [ ] All have LinkedIn URLs
- [ ] Status = "new"

---

## Phase 2: Company Research (Automated Batch)

**Objective:** Research each lead's company website for personalization

**Challenge:** Need to set company URLs first

**Steps:**
1. Extract company names from lead data
2. Guess company URLs (companyname.com)
3. Set URLs for each lead
4. Run agent-browser research on each

**Commands:**
```bash
# Get newest leads
LEADS=$(sqlite3 data/salesbud.db "SELECT id, company FROM leads WHERE status='new' ORDER BY id DESC LIMIT 5;")

# For each lead, set company URL and research
# Example for lead ID 25:
uv run python -m salesbud set-company-url 25 "https://companyname.com" --toon
uv run python -m salesbud research 25 --toon

# Verify research data saved
sqlite3 data/salesbud.db "SELECT id, company_url, LENGTH(company_research) FROM leads WHERE id=25;"
```

**Success Criteria:**
- [ ] Company URLs set for all 5 leads
- [ ] Research snapshots captured (4,000+ chars each)
- [ ] No agent-browser errors

---

## Phase 3: Generate Personalizations

**Objective:** Create contextual icebreakers based on research

**Steps:**
1. Run personalization on each researched lead
2. Verify personalization_angle generated
3. Review quality (should mention AI/SaaS/marketing based on research)

**Commands:**
```bash
# Generate for each lead
uv run python -m salesbud personalize 25 --toon

# Check results
sqlite3 data/salesbud.db "SELECT id, name, substr(personalization_angle, 1, 60) FROM leads WHERE id=25;"
```

**Success Criteria:**
- [ ] Personalization generated for all leads
- [ ] Contextual (mentions AI/SaaS/company focus)
- [ ] Saved to personalization_angle column

---

## Phase 4: Send Connection Requests

**Objective:** Send LinkedIn connection requests with personalized notes

**⚠️ WARNING:** This sends REAL connection requests (dry_run=0)

**Steps:**
1. Verify dry_run is OFF
2. Send connections with --delay for safety
3. Monitor for rate limits

**Commands:**
```bash
# Verify production mode
uv run python -m salesbud config dry_run

# Send connections (max 2-3 to be safe)
uv run python -m salesbud connect --max 2 --delay 10 --toon

# Check status
uv run python -m salesbud dashboard --toon
```

**Success Criteria:**
- [ ] Connection requests sent
- [ ] Lead status → "connection_requested"
- [ ] Activities logged
- [ ] No rate limit errors

**Rollback if issues:**
```bash
uv run python -m salesbud config dry_run 1
```

---

## Phase 5: Queue Follow-Up DMs

**Objective:** Stage personalized messages that auto-send after connection accepted

**Current Behavior:**
- Connector module checks for "connected" status
- Sequence module sends DMs to "connected" leads
- Personalization_angle used if available

**How it works:**
1. Connection request sent → status = "connection_requested"
2. Lead accepts → status = "connected" (detected by check-connections)
3. Sequence runs → sends DM with personalization

**Commands:**
```bash
# Check for accepted connections
uv run python -m salesbud check-connections --toon

# Run DM sequence (will use personalization_angle if present)
uv run python -m salesbud sequence --toon

# Verify messages sent
sqlite3 data/salesbud.db "SELECT id, name, status, sequence_step FROM leads WHERE status='active';"
```

**Success Criteria:**
- [ ] check-connections detects accepted requests
- [ ] sequence sends personalized DM
- [ ] sequence_step incremented
- [ ] Activity logged

---

## Implementation Questions

**Before we execute, please confirm:**

1. **How many connection requests?** 
   - Safe: 2-3 for testing
   - Moderate: 5
   - Aggressive: 10+ (not recommended)

2. **Locations?**
   - Use all 5 cities in icp.toon (London, Toronto, NY, Austin, Sydney)
   - Focus on specific city?

3. **Connection note strategy?**
   - Use generated personalization_angle as connection note?
   - Use generic note?
   - Use hybrid (generic + personalization)?

4. **Timing:**
   - Space connections 10+ seconds apart?
   - Send all at once?
   - Spread across hours?

5. **Safety:**
   - Keep dry_run=0 (production)?
   - Test 1 in dry_run first?
   - Your LinkedIn account age/activity level?

---

## Risk Mitigation

### LinkedIn Safety:
- **Rate limit:** 8 connections/hour, 50/day enforced
- **Delay:** 10+ seconds between requests
- **Daily max:** Start with 2-3, monitor for 24hrs before scaling

### Rollback Plan:
```bash
# If anything goes wrong:
uv run python -m salesbud config dry_run 1

# Check what was sent:
sqlite3 data/salesbud.db "SELECT id, name, status FROM leads WHERE status='connection_requested';"
```

### Monitoring:
- Check LinkedIn for notifications
- Monitor for captcha challenges
- Watch daily_counters table
- Review activities log

---

## Success Metrics

After workflow completion:

| Metric | Target |
|--------|--------|
| Leads scraped | 5 |
| Companies researched | 5 |
| Personalizations generated | 5 |
| Connection requests sent | 2-5 |
| Connection acceptance rate | 20-40% (expect 1-2 accepts) |
| Follow-up DMs sent | 1-2 (after accepts) |
| Errors | 0 |

---

**Ready to execute?** 
Confirm the questions above and I'll run the complete workflow with parallel agents.
