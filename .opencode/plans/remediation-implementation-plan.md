# SalesBud Remediation Implementation Plan

## Overview
Fix all 70+ issues from the brutal audit across 4 parallel work streams.

## Work Stream 1: Security Fixes (CRITICAL)
**Lead:** Security Agent
**Issues:** SQL injection, credential exposure, command injection

### Tasks:
1. Fix SQL injection in sequence.py (lines 79-93)
2. Fix SQL injection in emailer.py (lines 245-257)
3. Add .env to .gitignore and document credential rotation
4. Fix command injection in researcher.py (lines 18-28)
5. Add URL validation utilities
6. Fix HTML escaping in email body (cli/main.py:526)
7. Add input validation for scrape parameters

## Work Stream 2: Database & Performance (CRITICAL)
**Lead:** Database Agent
**Issues:** Indexes, connection pooling, race conditions, pagination

### Tasks:
1. Add database indexes in init_db()
2. Implement connection singleton pattern
3. Fix race condition in increment_daily_count()
4. Add pagination to get_all_leads()
5. Implement activities retention policy
6. Enable SQLite WAL mode
7. Fix N+1 query patterns
8. Add batch update operations

## Work Stream 3: Resource Management & Error Handling (HIGH)
**Lead:** Stability Agent
**Issues:** Resource leaks, error handling, browser lifecycle

### Tasks:
1. Fix browser context reuse in sequence.py
2. Add try/finally blocks for all resource cleanup
3. Replace bare except clauses with specific exceptions
4. Add timeouts to all subprocess calls
5. Fix TOON escaping bug (backslash escaping)
6. Add proper exception handling in connector.py
7. Implement context managers for database connections
8. Fix error message sanitization

## Work Stream 4: Architecture & Code Quality (MEDIUM)
**Lead:** Architecture Agent
**Issues:** Refactoring, DRY violations, testing

### Tasks:
1. Extract ICP loading to shared utility
2. Create repository pattern for database access
3. Add comprehensive docstrings
4. Remove unused imports
5. Standardize error handling patterns
6. Create path utility module
7. Add type hints consistently
8. Create test structure

## Implementation Order

### Phase 1: Critical Security (Day 1)
- Security work stream starts immediately
- Database work stream starts immediately
- These are blocking - other streams wait

### Phase 2: Stability (Day 1-2)
- Resource management work stream
- Must verify Phase 1 fixes first

### Phase 3: Performance & Architecture (Day 2-3)
- Performance work stream
- Architecture work stream
- Can run in parallel with Phase 2

## Testing Strategy
1. Unit tests for validation functions
2. Integration tests for database operations
3. Mock tests for external services
4. Manual verification checklist

## Success Criteria
- [ ] All SQL injection vulnerabilities fixed
- [ ] All credentials rotated and secured
- [ ] Database indexes added
- [ ] Connection pooling implemented
- [ ] No bare except clauses
- [ ] All resources properly cleaned up
- [ ] Tests passing
- [ ] Manual testing completed

## Files to Modify (by priority)

### CRITICAL (Security):
1. src/salesbud/services/sequence.py
2. src/salesbud/services/emailer.py
3. src/salesbud/services/researcher.py
4. .gitignore
5. src/salesbud/cli/main.py

### HIGH (Database/Performance):
6. src/salesbud/database/connection.py
7. src/salesbud/models/lead.py
8. src/salesbud/cli/dashboard.py
9. src/salesbud/services/enricher.py
10. src/salesbud/services/connector.py

### MEDIUM (Code Quality):
11. src/salesbud/services/scraper.py
12. src/salesbud/services/email_finder.py
13. src/salesbud/utils/browser.py
14. src/salesbud/models/validation.py
15. src/salesbud/config/env.py

## Rollback Plan
- All changes in feature branch
- Database backup before migration
- Staged deployment (dev → staging → prod)
- Rollback scripts ready
