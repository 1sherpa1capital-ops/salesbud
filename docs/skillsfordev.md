# SalesBud — Skills Reference

Maps available agent skills to SalesBud architecture components (v1.1 — LinkedIn DMs + Cold Email).

## 0. Core CLI Orchestration (Active — v1.1)

Powers the CLI execution layer that AI agents use to operate SalesBud.

- **`salesbud-cli`**: Core skill for autonomous SalesBud CLI operation. Triggers on: find leads, scrape linkedin, run sequence, send DMs, send connections, find emails, start outbound, check replies, enrich leads, linkedin outreach, cold email campaign, dashboard stats. **Always use `uv run python -m salesbud` not `python -m salesbud`.**
- **[AGENTS.md](../AGENTS.md)**: Complete CLI reference with all commands, JSON schemas, exit codes, and troubleshooting.

## 1. Core Agent Orchestration & Browser Automation

Powers the foundational execution layer of `main.py` and Playwright browsing.

- **`agent-browser`**: CLI for AI agent browser automation. Critical for LinkedIn scraping, extraction, and messaging loop.
- **`browser-use`**: Core skill for automating LinkedIn navigation reliably.
- **`agentic-development-principles`**: Strategic principles ensuring the dry-run modes are architected correctly for human oversight.
- **`agent-evaluation`**: Evaluate reply classification agents (positive / neutral / negative detection).

## 2. Email Outreach (Active — v1.1)

Powers the cold email channel via Resend (`rhigden@syntolabs.xyz`, `syntolabs.xyz` verified).

- **`resend/send-email`** (`.claude/skills/resend/send-email`): Core skill — single + batch email, idempotency keys, error handling, retry logic. **Active use.**
- **`resend/email-threading`** (`.claude/skills/resend/email-threading`): For reply threading (post-MVP — when Resend inbound is set up).
- **`resend/resend-inbound`** (`.claude/skills/resend/resend-inbound`): For receiving and processing replies automatically (post-MVP).
- **`cold-email`**: Strategic guidance for the 4-step sequence (Value-First → Case Study → Soft Offer → Break-Up). **Templates from sales-playbook.md.**
- **`email-sequence`**: Timing and flow best practices for the 3-day delay cadence.

## 3. Infrastructure, Database & Testing

Handles stability, data persistence, and reliability.

- **`database-schema-design`**: SQLite schema (`leads`, `activities`, `config`) optimization. Includes new `email`, `email_sequence_step`, `last_email_sent_at` columns.
- **`environment-setup`**: Managing `.env` boundary for LinkedIn session cookies, `RESEND_API_KEY`, and `CAL_API_KEY`.
- **`backend-testing`**: `pytest` coverage for sequence logic — ensuring no lead is double-messaged or emailed after a booked call.
- **`deployment-automation`**: CI/CD for the orchestrator to Railway (post-MVP).

## 4. Communication Strategy & Copywriting

Drives effectiveness of both outreach channels.

- **`copywriting`**: Refining both the 5-step LinkedIn NEPQ sequence and the 4-step cold email sequence.
- **`sales-enablement`**: Aligning value prop across DM and email channels with the discovery call.
- **`marketing-psychology`**: Refining the value hooks and low-stakes offers.

## 5. Post-MVP Growth & Pipeline

- **`revops`**: CRM logging strategy once booked leads need to push out of SQLite.
- **`data-analysis`** & **`log-analysis`**: Monitor flag rate <2% and surface sequence effectiveness.
- **`analytics-tracking`**: Track email open/click rates (Resend dashboard + webhooks).

