# SalesBud

Autonomous outbound SDR agent. Runs the full loop: **scrape → connect → DM sequence → cold email → book**.

## Quick Start

```bash
uv sync
uv run python -m salesbud init
uv run python -m salesbud workflow --query "CEO" --location "Austin, TX"
```

## Commands

```bash
# LinkedIn
uv run python -m salesbud scrape --query "CEO" --location "Austin"
uv run python -m salesbud connect --max 10
uv run python -m salesbud check-connections
uv run python -m salesbud sequence

# Email (Resend → rhigden@syntolabs.xyz)
uv run python -m salesbud add-email <id> <email>
uv run python -m salesbud email-sequence
uv run python -m salesbud email --to test@example.com -s "Test" -b "Hello"

# Email Discovery (use --quick for fast mode <10s)
uv run python -m salesbud find-email <id> --quick
uv run python -m salesbud find-emails --max 10 --quick

# Company Enrichment
uv run python -m salesbud set-company-url <id> <url>
uv run python -m salesbud enrich <id>
uv run python -m salesbud enrich-all --max 10

# Monitor
uv run python -m salesbud dashboard
uv run python -m salesbud lead <id>
uv run python -m salesbud config

# Go live (default is dry-run)
uv run python -m salesbud config dry_run 0
```

## What's New in v1.3

- 🛡️ **Production Readiness** - Pydantic validation, DB-backed daily rate limits, and idempotency guards.
- ✅ **Pre-Flight Validation** - Run `uv run python scripts/prod_check.py` to verify system health before going live.
- 🐍 **Modern Python** - Project requirement bumped to Python 3.13+ with the latest stable dependencies.

## What's New in v1.2

- 🕵️ **Browser Stealth System** - Anti-detection measures for LinkedIn automation
- ⚡ **Fast Email Discovery** - `--quick` flag for <10s email finding (vs 60s normal)
- 🏢 **Company Enrichment** - Set company URLs and enrich with Crawl4AI
- 🔄 **Multi-Skill Coordination** - Works with agent-browser, copywriting, sales-coach skills
- 📊 **50 Eval Test Suite** - 100% pass rate on comprehensive test suite

## Status

✅ **v1.3** — Prod-ready with input validation, rate limits, and full stealth.

## Docs

- **[AGENTS.md](AGENTS.md)** — AI Agent reference (complete CLI guide)
- **[MVP-SPEC.md](docs/MVP-SPEC.md)** — Full spec (v1.1)
- **[STRUCTURE.md](docs/STRUCTURE.md)** — File layout + env vars
- **[PRD.md](docs/PRD.md)** — Product requirements
- **[SPEC.md](docs/SPEC.md)** — Technical spec
- **[skillet.md](skillet.md)** — Skills reference
- **[CHANGELOG.md](changelog.md)** — Version history
