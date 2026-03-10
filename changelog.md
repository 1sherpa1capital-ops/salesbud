# Changelog

All notable changes to SalesBud will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Landing Page & Docs UI**: Built a complete minimalist, Monokai-themed landing page (`website/`) for SalesBud CLI. Features include binary code rain background, Geist typography, a headless SVG ghost-bot logo, and comprehensive agent-first product positioning.
- **Rich CLI TUI**: Integrated `rich` to provide beautiful panels, tables, and colors for human operators navigating the CLI (Mode A operation).
- **Centralized Logger**: Added `logger.py` to route all stdout, ensuring 100% strict JSON output suppression for headless AI agents (Mode B operation).

### Changed
- Refactored `src/salesbud/cli/dashboard.py` to use `rich.table.Table` and `rich.panel.Panel` for stunning visual presentation of leads and stats.
- Replaced >250 raw `print()` statements across all inner scraper/emailer services, actively preventing JSON parsing errors for LLM agents.

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

[Unreleased]: https://github.com/syntolabs/salesbud/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/syntolabs/salesbud/releases/tag/v1.1.0
[1.0.0]: https://github.com/syntolabs/salesbud/releases/tag/v1.0.0
