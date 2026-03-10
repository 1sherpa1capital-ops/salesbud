# SalesBud — Business Requirements Document (BRD)

**Product:** SalesBud  
**Version:** 1.0  
**Date:** March 10, 2026  
**Author:** Synto Labs  
**Stakeholder:** Rhigden (Founder)

---

## 1. Executive Summary

SalesBud is an autonomous outbound sales development tool that automates the LinkedIn prospecting pipeline for **Synto Labs**, an AI ops automation agency serving founder-led marketing agencies in the GTA.

The tool eliminates the 2–3 hour daily manual grind of searching for leads, sending connection requests, writing follow-up DMs, and tracking responses — freeing the founder to focus on closing deals and delivering client work.

**Business outcome:** Turn LinkedIn outreach from a willpower-dependent daily task into an automated pipeline that generates 1+ booked discovery calls per week.

---

## 2. Business Context

### 2.1 Company Background

| Attribute | Detail |
|-----------|--------|
| Company | Synto Labs |
| Founder | Rhigden |
| Type | AI ops automation agency |
| Target market | Founder-led marketing agencies (GTA) |
| Stage | Pre-revenue, active outreach phase |
| GTM | LinkedIn DMs + cold email outreach |

### 2.2 Current Pain Points

1. **Manual outreach is unsustainable** — 20+ personalized DMs/day requires 2–3 hours of focused work
2. **No SDR team** — Rhigden is the sole operator doing all prospecting, closing, and delivery
3. **Inconsistency kills pipeline** — missed days = zero pipeline movement; no automated follow-up
4. **No tracking system** — leads, statuses, and follow-ups tracked informally; no single source of truth
5. **Time-to-first-meeting is too long** — manual processes delay the path from lead discovery to booked call

### 2.3 Strategic Alignment

SalesBud directly supports Synto Labs' go-to-market strategy:

- **Daily outreach goal:** 20+ personalized DMs before any distractions
- **Prospecting channel:** LinkedIn (primary), cold email (secondary, planned)
- **ICP:** CEOs, VPs, founders of marketing agencies in Austin, GTA, and beyond
- **Revenue model:** Agency services — each booked meeting is a potential $2K–$10K/month contract

---

## 3. Business Objectives

### 3.1 Primary Objectives

| # | Objective | Measure |
|---|-----------|---------|
| 1 | **Automate LinkedIn outreach** to eliminate manual prospecting time | <15 min/day human involvement |
| 2 | **Generate booked meetings** from cold LinkedIn outreach | ≥1 booked call/week |
| 3 | **Maintain account safety** to protect LinkedIn presence | <2% flag rate |
| 4 | **Create a lead tracking system** as single source of truth | All leads in one database with status tracking |

### 3.2 Secondary Objectives

| # | Objective | Measure |
|---|-----------|---------|
| 5 | Prove the autonomous SDR model works for agency founders | Repeatable results over 30 days |
| 6 | Build foundation for multi-channel outreach (LinkedIn + email) | Modular architecture supports email addition |
| 7 | Potential to productize as SaaS for other founders | Clean, extensible codebase |

---

## 4. Stakeholder Analysis

| Stakeholder | Role | Interest | Success Criteria |
|-------------|------|----------|------------------|
| Rhigden (Founder) | Primary user, decision maker | Book meetings without manual grind | 1+ booked call/week; <15 min/day |
| Prospects (Leads) | Recipients of outreach | Receive relevant, non-spammy messages | ≥8% reply rate; messages feel personal |
| LinkedIn (Platform) | Infrastructure provider | Terms of Service compliance | <2% flag rate; human-speed behavior |
| Synto Labs (Company) | Business entity | Revenue generation | Pipeline of qualified leads |

---

## 5. Business Rules

### 5.1 Outreach Rules

| Rule | Rationale |
|------|-----------|
| Maximum 50 DMs per day | LinkedIn rate limit safety |
| Maximum 8 DMs per hour | Mimic human behavior |
| 5–15 minute random delay between DMs | Avoid detection patterns |
| Maximum 10 connection requests per day | Conservative to prevent flags |
| 3-day wait between sequence steps | NEPQ methodology spacing |
| Pause sequence immediately on any reply | Prevents "talking over" the prospect |
| Breakup message (Step 5) ends the sequence | Respectful close after 12 days |

### 5.2 Data Rules

| Rule | Rationale |
|------|-----------|
| Leads deduplicated by LinkedIn URL | No duplicate outreach |
| All data stored locally (SQLite) | No third-party data sharing |
| Activity log for every action | Audit trail for compliance |
| Dry-run mode enabled by default | Safety-first approach |

### 5.3 Compliance Rules

| Area | Requirement |
|------|-------------|
| LinkedIn ToS | Human-speed rate limits; no mass automation |
| Data privacy | Local storage only; no export to third parties |
| Messaging | NEPQ sales methodology; no aggressive or misleading copy |

---

## 6. Cost Analysis

### 6.1 MVP Cost (v1.0)

| Item | Cost |
|------|------|
| Development (self-built) | $0 (founder time) |
| Python + SQLite + Playwright | $0 (open source) |
| LinkedIn account | Existing (free tier) |
| **Total MVP** | **$0** |

### 6.2 Production Cost (v1.1+)

| Item | Monthly Cost |
|------|-------------|
| LinkedIn Sales Navigator | ~$100/month |
| Claude API (DM personalization) | ~$10–20/month |
| Cal.com (self-hosted) | $0 |
| Railway (hosting) | ~$5–10/month |
| **Total Production** | **~$115–130/month** |

### 6.3 ROI Projection

| Metric | Value |
|--------|-------|
| Monthly cost (production) | ~$125 |
| Booked meetings/month | 4+ (1/week target) |
| Average contract value | $2K–$10K/month |
| Close rate (founder-led sale) | ~25% |
| Monthly revenue from 1 close | $2K–$10K |
| **ROI** | **16x–80x monthly cost** |

---

## 7. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LinkedIn account flagged/restricted | High — loses primary outreach channel | Medium | Conservative rate limits; dry-run testing; human-speed delays |
| Session cookie expiration disrupts pipeline | Medium — requires manual refresh | High | Alert system (planned); document refresh process |
| Low reply rates (<3%) | Medium — low pipeline | Medium | A/B test DM templates; improve personalization with Claude API |
| LinkedIn HTML structure changes | Medium — breaks scraping | Medium | Regex-based extraction is fragile; plan migration to official API |
| Single operator dependency | High — no outreach if founder is unavailable | High | Automate to cron/scheduled operation (v1.1) |
| Competitor tools improve | Low — many alternatives exist | Medium | Focus on founder-specific workflow; productize if model works |

---

## 8. Constraints

| Constraint | Detail |
|------------|--------|
| No budget for paid tools (MVP) | Must use free/open-source stack |
| Solo operator | No DevOps team; must be CLI-simple to run |
| LinkedIn rate limits are non-negotiable | Over-sending = account ban |
| Must not feel spammy to recipients | NEPQ methodology ensures consultative tone |

---

## 9. Dependencies

| Dependency | Type | Risk |
|------------|------|------|
| LinkedIn (platform access) | External | High — if account restricted, pipeline stops |
| Playwright (browser automation) | Technical | Low — mature, well-maintained |
| Python ecosystem | Technical | Low — stable |
| LinkedIn session cookie | Operational | Medium — requires daily refresh |
| Founder availability | Operational | High — sole operator for non-automated steps |

---

## 10. Success Criteria for Business Sign-Off

### Phase 1: MVP Validation (✅ Complete)
- [x] Scraping extracts real LinkedIn profiles
- [x] Connection requests sent with personalized notes
- [x] 5-step DM sequence logged correctly in dry-run
- [x] Rate limiting enforced in all actions
- [x] Dashboard shows accurate lead status

### Phase 2: Production Validation (v1.1)
- [ ] DMs actually delivered via LinkedIn messaging
- [ ] Replies detected and sequence paused automatically
- [ ] At least 1 meeting booked from automated outreach
- [ ] Account flag rate stays below 2% over 30 days

### Phase 3: Business Validation (v1.2)
- [ ] Repeatable 1+ meeting/week from automated pipeline
- [ ] Multi-channel (LinkedIn + email) increases reply rate
- [ ] Cost per booked meeting under $50
- [ ] Foundation for productization assessed

---

## 11. Approval

| Role | Name | Date | Approval |
|------|------|------|----------|
| Founder / Stakeholder | Rhigden | | ☐ Approved |
| Technical Lead | Rhigden | | ☐ Approved |
