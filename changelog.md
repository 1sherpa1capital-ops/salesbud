# Changelog

All notable changes to SalesBud will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Comprehensive Security & Performance Remediation (2026-03-12)
MAJOR UPDATE: Addressed 70+ audit findings across security, database, performance, and architecture.

**CRITICAL SECURITY FIXES:**
- ✅ **SQL Injection Patched** - Fixed parameterized queries in `sequence.py` and `emailer.py`
- ✅ **Command Injection Blocked** - Added URL validation in `researcher.py` before subprocess execution
- ✅ **XSS Prevention** - Added HTML escaping in email body rendering (`cli/main.py`)
- ✅ **Credential Protection** - Added `.env` to `.gitignore` to prevent accidental commits
- ✅ **TOON Format Fixed** - Corrected backslash escaping bug in output formatter

**DATABASE & PERFORMANCE:**
- ✅ **6 Database Indexes** - Added indexes on status, created_at, email, sequence tracking, activities
- ✅ **Connection Singleton** - Implemented pooled connections with WAL mode for better concurrency
- ✅ **Race Condition Eliminated** - Fixed rate limiting with atomic UPSERT operations
- ✅ **Pagination Support** - Added `get_leads_paginated()` for efficient large dataset handling
- ✅ **Data Retention** - Added `cleanup_old_activities()` function (90-day retention policy)

**STABILITY & ERROR HANDLING:**
- ✅ **Subprocess Timeouts** - Added 60s timeouts to all agent-browser calls
- ✅ **Specific Exceptions** - Replaced 20+ bare `except Exception` clauses with specific types
- ✅ **Transaction Context Manager** - Added `db_transaction()` for automatic commit/rollback
- ✅ **Error Sanitization** - Secure logging prevents information disclosure in production
- ✅ **Resource Cleanup** - Enhanced browser lifecycle management in sequence service

**ARCHITECTURE & CODE QUALITY:**
- ✅ **Path Centralization** - Created `utils/paths.py` (eliminated 10+ hardcoded path patterns)
- ✅ **ICP Loader Utility** - Extracted duplicate config loading into `utils/icp_loader.py`
- ✅ **Exception Hierarchy** - Created `exceptions.py` with custom error types
- ✅ **Documentation** - Added comprehensive docstrings to 13+ public functions
- ✅ **DRY Violations Fixed** - Consolidated ICP loading, standardized patterns

**TEST SUITE:**
- ✅ **Testing Framework** - Added pytest and pytest-asyncio
- ✅ **Unit Tests** - Created tests for validation, database, services
- ✅ **Integration Tests** - Added CLI command testing
- ✅ **Mock Utilities** - Created MockDB and fixtures in `conftest.py`

**Files Changed:** 18 files modified, 3 new files created
**Commits:** 2 major commits (remediation + test suite)

---

### Stability Fixes (2026-03-12)
Production-ready stability improvements for critical error handling:

**Task 1: Subprocess Timeouts (CRITICAL)**
- Added `timeout=60` to all `subprocess.run()` calls in `services/researcher.py`
- Lines 35, 42, 51: agent-browser commands with 60s timeout
- Line 69: agent-browser close command with 30s timeout
- Prevents indefinite hangs during company research operations

**Task 2: Specific Exception Handling**
Replaced bare `except Exception` clauses with specific exception types:
- `services/scraper.py` (lines 149, 156): Changed to `(ValueError, AttributeError, TypeError)` and `(RuntimeError, ConnectionError, TimeoutError)`
- `services/connector.py` (lines 70, 146-147, 171-172, 216-217, 231): Changed to `(ConnectionError, TimeoutError)`, `(AttributeError, TypeError, RuntimeError)`
- `services/sequence.py` (lines 88, 97, 101): Changed to `(RuntimeError, OSError, ConnectionError)`
- `services/emailer.py` (line 171): Changed to `(RuntimeError, ConnectionError, TimeoutError)`
- `services/email_finder.py` (lines 92, 94, 97, 98, 126, 145, 194, 195, 259, 260): Changed to specific `(socket.error, OSError)`, `(dns.resolver.*)`, `(ValueError)`, `(RuntimeError)`
- `services/enricher.py` (line 42): Changed to `(RuntimeError, ConnectionError)`

**Task 3: Database Transaction Context Manager**
- Added `db_transaction()` context manager to `database/connection.py` (lines 44-62)
- Provides automatic commit/rollback with proper resource cleanup
- Alias alongside existing `get_db_cursor()` for API consistency

**Task 4: Error Message Sanitization**
- Modified `cli/main.py` exception handler (lines 306-317)
- Full error details now logged securely via `logging.error()` with `exc_info=True`
- User-facing messages sanitized to generic "An internal error occurred"
- Prevents sensitive information leakage in production

**Task 5: Resource Cleanup in Sequence Service**
- Enhanced `DMSequenceRunner.stop()` method in `services/sequence.py` (lines 92-104)
- Changed bare `except Exception` to specific `(RuntimeError, OSError)`
- Ensures browser context and playwright instances are reliably closed
- Prevents memory leaks and zombie browser processes

**Benefits:**
- Eliminates indefinite subprocess hangs
- More predictable error handling with specific exception types
- Secure error logging prevents information disclosure
- Reliable resource cleanup prevents memory leaks
- Production-ready stability for critical operations

---

### Architecture Improvements (2026-03-12)
Refactored codebase for better maintainability and code quality:

**New Utility Modules:**
- Created `salesbud/utils/icp_loader.py` - Centralized ICP config loading from `icp.toon` or `icp.json` files
- Created `salesbud/utils/paths.py` - Centralized path management for data directories and database
- Created `salesbud/exceptions.py` - Custom exception hierarchy (SalesBudError, ValidationError, DatabaseError, LinkedInError, EmailError, RateLimitError)

**Path Centralization:**
- Eliminated 10+ hardcoded `Path(__file__).parent.parent.parent.parent / "data"` patterns across codebase
- All services now import from `salesbud.utils.paths` for consistent path resolution
- Updated files: `connector.py`, `sequence.py`, `scraper.py`, `inbox.py`, `main.py`, `connection.py`

**Code Quality:**
- Added comprehensive docstrings to all public functions in:
  - `models/lead.py`: get_all_leads, get_lead_by_id, add_lead with proper Args/Returns docs
  - `services/connector.py`: LinkedInConnector class, send_connection, run_connection_campaign, check_pending_connections
  - `services/sequence.py`: DMSequenceRunner class, personalize_dm, send_dm_to_lead, get_leads_due_for_step, run_sequence_step

**Refactoring:**
- Extracted duplicate ICP loading logic from `main.py` (scrape and workflow commands) into `load_icp_config()` utility
- Reduced code duplication in CLI commands
- Standardized error handling patterns across services

**Benefits:**
- Single source of truth for file paths
- Easier testing and mocking
- Better IDE support with proper type hints
- Reduced maintenance burden when directory structure changes
- Clearer API documentation via docstrings

---

### Test Results - Phase 2: Email Discovery & Company Enrichment (2026-03-12)
All Phase 2 production tests completed successfully on Lead ID 22 (Herb Dyer):

| Test | Status | Notes |
|------|--------|-------|
| `add-email` | ✅ PASS | Email test@example.com added successfully |
| `email` | ✅ PASS | Resend email to delivered@resend.dev sent successfully |
| `set-company-url` | ✅ PASS | Company URL https://vercel.com set |
| `enrich` | ✅ PASS | Crawl4AI extracted company description and buying signals ("hiring") |
| `research` | ✅ PASS | Agent-browser captured full page structure (106 interactive elements) |
| `personalize` | ✅ PASS | Generated contextual icebreaker mentioning AI focus |
| Database Verify | ✅ PASS | All fields (email, company_url, company_research, personalization_angle) persisted correctly |

**Key Findings:**
- Email delivery via Resend API functional
- Crawl4AI enrichment working (0.95s fetch time)
- Agent-browser research operational - captured 106 page elements
- Personalization engine generating relevant angles based on research data
- All database write operations confirmed with SQLite verification

### Added
- **Zero-Config Search**: Added `icp.json` file parsing capability to the `scrape` and `workflow` commands. If you run those commands without passing the `--query` or `--location` arguments, they will now automatically look for an `icp.json` payload in the root directory.
- **Persistent Auth**: Created a dedicated `login` command which launches a headed browser for the user to log into LinkedIn manually (solving 2FA headers/emails). State is cleanly saved to `./data/browser_state`, entirely replacing the unstable `.env` cookie pasting workflow.
- **Landing Page & Docs UI**: Built a complete minimalist, Monokai-themed landing page (`website/`) for SalesBud CLI. Features include binary code rain background, Geist typography, a headless SVG ghost-bot logo, and comprehensive agent-first product positioning.
- **Rich CLI TUI**: Integrated `rich` to provide beautiful panels, tables, and colors for human operators navigating the CLI (Mode A operation).
- **Centralized Logger**: Added `logger.py` to route all stdout, ensuring 100% strict JSON output suppression for headless AI agents (Mode B operation).
- **Agent Browser Integration**: Added `agent-browser` driven company website research and personalization pipeline. Added new columns (`company_research`, `personalization_angle`) to leads. Included `research` and `personalize` commands to the CLI. Outbound DMs and Connection notes now automatically use generated contextual personalization angles.

### Changed
- **TOON Format Migration**: Migrated all machine-readable CLI output from JSON to TOON (Token-Oriented Object Notation) format. TOON is optimized for AI agents, reducing token usage while remaining easily parsable. All `--json` flags are now `--toon`, and the `print_json()` utility has been replaced with `print_toon()`.
- **Anti-Bot Bypass**: Modified all scraping/automations (scraper, connector, dm sequences, inbox check) to run with `headless=False` (visible browser). This drastically reduces LinkedIn's bot challenge surface and allows human-in-the-loop interventions.
- **Challenge Bypass**: Refactored `check_for_challenge()` in `browser.py` to pause for 60 seconds whenever LinkedIn shows a Captcha wall, allowing the user to manually solve the Captcha in the browser window instead of crashing immediately.
- Refactored `src/salesbud/cli/dashboard.py` to use `rich.table.Table` and `rich.panel.Panel` for stunning visual presentation of leads and stats.
- Replaced >250 raw `print()` statements across all inner scraper/emailer services, actively preventing JSON parsing errors for LLM agents.

### Fixed
- **Connection Logic Locators**: Completely refactored `connector.py` to strictly scope the "Connect" button lookup to the `main section` (top card) of a profile. This prevents the bot from accidentally navigating to and clicking on profiles in the "People also viewed" sidebar.
- **Hidden Connection Actions**: `connector.py` now correctly clicks the "More actions" dropdown to find the "Connect" or "Message" button if it is hidden from the main profile row, dramatically increasing the connect rate on customized profiles.
- **Empty Connect Handling**: The connector module safely handles profiles where the user strictly blocks connection requests, logging the warning rather than failing or clicking an invalid element.
- **Orphaned Contexts**: Added strictly scoped `finally:` blocks to Playwright execution in the connection commands to ensure the browser context is reliably closed even if a DOM element exception is thrown, preventing memory leaks and stalled zombie processes.

---

## [1.3.0] - 2026-03-11

### Added
- **Production Readiness Check**: New `scripts/prod_check.py` to validate Python version, env vars, DB state, and rate limits before dropping dry-run mode.
- **Input Validation**: `pydantic v2` implemented across all CLI data entry points (`add-email`, `email`, `set-company-url`, etc.) returning clean JSON errors.
- **Daily Rate Limiting**: Centralized SQLite counters for `dms_per_day` and `emails_per_day` with enforced guards in `connector.py` and `emailer.py`.
- **Idempotency Guards**: `sequence.py` now blocks duplicate DMs sent to the same lead on the same day.

### Changed
- **Dependencies**: Required Python version bumped to `^3.13`. All `uv` dependencies upgraded to their latest stable releases.
- **Clean Exceptions**: Top-level `try/except` block in `main.py` catches all unhandled exceptions and formats them as proper JSON for AI operator consumption.
- **Docs**: Comprehensive newly updated `SKILL.md` for `salesbud-cli`.

---

## [1.2.0] - 2026-03-10

### Added
- **Database Schema v2.0**: Added 7 new columns for enrichment and email verification
  - `company_url`, `company_description`, `company_size_est`, `buying_signals`
  - `email_source`, `email_verified`, `enriched_at`
  - Automatic migration for existing databases
- **New CLI Commands**:
  - `set-company-url <id> <url>` - Set company URL for enrichment
  - `enrich-all --max N` - Batch company enrichment with Crawl4AI
  - `find-email --quick` - Fast email discovery mode (<10s)
  - `find-emails --quick` - Batch email discovery with parallel processing
- **Browser Stealth System**: New `utils/browser.py` with anti-detection measures
  - Rotating user agents and viewport sizes
  - `STEALTH_SCRIPT` to hide automation signatures
  - `jitter_delay()` and `random_delay()` for human-like timing
  - `safe_goto()` with retry logic for LinkedIn navigation
  - `check_for_challenge()` for CAPTCHA detection
- **LinkedIn Anti-Detection**: Updated all Playwright services with stealth
  - `services/scraper.py` - Stealth browsing for lead scraping
  - `services/connector.py` - Stealth for connection requests
  - `services/sequence.py` - Stealth for DM sequences
- **Email Finder Optimization**:
  - `--quick` flag for <10s operation (vs 60s normal)
  - Parallel processing with `ThreadPoolExecutor(max_workers=5)`
  - Skip company page scraping in quick mode (saves ~40s)
  - Reduced timeouts: DuckDuckGo 15s→5s, SMTP 10s→3s
- **AI Agent Skill v2.0**: Enhanced `salesbud-cli` skill with multi-skill coordination
  - 50 comprehensive evals (100% pass rate)
  - Skill switching guidance (agent-browser, copywriting, sales-coach)
  - Multi-skill workflow documentation
  - Quick Skill Switch Guide at top of SKILL.md

### Changed
- **Enrichment Flow**: Now requires `set-company-url` before `enrich` command
- **Email Discovery**: Defaults to thorough mode, use `--quick` for fast results
- **LinkedIn Navigation**: All profile access now uses stealth measures
- **Workflow Command**: Fixed `logger.print_text()` errors, added proper text arguments

### Fixed
- **Critical Bug**: `services/scraper.py` using undefined `base_url` and `params` variables
- **Playwright Errors**: ERR_TOO_MANY_REDIRECTS with new stealth context
- **Type Safety**: Added proper null checks throughout codebase
- **Async/Sync Conflict**: Resolved Playwright sync API issues in enricher

### Documentation
- **AGENTS.md**: Updated with new commands, stealth measures, skill integration
- **SKILL.md**: Complete rewrite with multi-skill coordination (415 lines)
  - Quick Skill Switch Guide
  - Related Skills section with handoff patterns
  - Multi-skill workflow diagrams
  - 50 eval cases documented
- **Evals**: Comprehensive test suite in `evals/evals.json`
  - 30 trigger tests (100% accuracy)
  - 20 functional tests (100% accuracy)
  - Skill integration tests included

### Security
- **Stealth Measures**: Anti-detection to prevent LinkedIn account restrictions
- **Rate Limiting**: Respects 8 DMs/hour, 10 emails/hour limits
- **Dry-run Safety**: Always defaults to safe mode, requires explicit enable

---

## [1.1.0] - 2026-03-10

### Added
- **AI Agent Skill**: Created `salesbud-cli` skill for autonomous CLI operation
- **Progress Report**: Created `progress.md` documenting system status
- **Type Safety**: Added type annotations and null checks throughout codebase

### Fixed
- `main.py`: Null safety issues on `.get()` calls in enrich command
- `email_finder.py`: Optional parameter typing and MX record attribute access
- `emailer.py`: Dict vs SendParams type mismatch
- `enricher.py`: AsyncGenerator handling for Crawl4AI
- `lead.py`: Return type mismatch in add_lead function

### Updated
- `AGENTS.md`: Added Critical Requirements section, troubleshooting, changelog rule
- `docs/README.md`: Added AI Agent Skills section
- `docs/skillsfordev.md`: Added salesbud-cli as section 0
- `ENGINEER_PROMPT.md`: Updated completion checklist, added changelog rule
- `main.py`: Workflow help text now uses `uv run python`
- All documentation now enforces `uv run python` pattern

### Documentation
- Complete CLI reference in AGENTS.md
- Troubleshooting section for common errors
- Quick reference tables for all commands

---

## [1.0.0] - 2026-03-01

### Added
- Initial release
- LinkedIn scraping with Playwright
- Connection request automation
- 5-step NEPQ DM sequence
- 4-step cold email via Resend
- Email discovery with SMTP verification
- Company enrichment with Crawl4AI
- LinkedIn inbox reply detection
- Unified dashboard
- Dry-run mode for safe testing

[Unreleased]: https://github.com/syntolabs/salesbud/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/syntolabs/salesbud/releases/tag/v1.3.0
[1.2.0]: https://github.com/syntolabs/salesbud/releases/tag/v1.2.0
[1.1.0]: https://github.com/syntolabs/salesbud/releases/tag/v1.1.0
[1.0.0]: https://github.com/syntolabs/salesbud/releases/tag/v1.0.0
