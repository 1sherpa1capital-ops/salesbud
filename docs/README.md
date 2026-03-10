# SalesBud Docs

**v1.1** — LinkedIn DMs + Cold Email via Resend

---

## 📁 current/ — Active development

| File | Purpose |
|------|---------|
| [SPEC.md](current/SPEC.md) | Full spec: architecture, modules, schema, requirements, CLI commands |
| [PRD.md](current/PRD.md) | Product requirements — free tools only, $0/month |
| [COMPLIANCE.md](current/COMPLIANCE.md) | Audit of implemented requirements + P0/P1/P2 checklist |
| [STRUCTURE.md](current/STRUCTURE.md) | File layout, env vars, CLI quick reference |

## 🤖 AI Agent Skills

| Skill | Purpose |
|-------|---------|
| `salesbud-cli` | Core skill for operating SalesBud CLI autonomously. Triggers on: find leads, scrape linkedin, run sequence, send DMs, cold email, enrich, dashboard |
| `.claude/skills/resend/send-email` | Send single and batch emails via Resend API |

## 📁 future/ — Not relevant yet

| File | Purpose |
|------|---------|
| [FUTURE-PRD.md](future/FUTURE-PRD.md) | v2.0 PRD: Apollo, Cal.com, Claude AI, Railway, CRM sync |
| [BRD.md](future/BRD.md) | Business requirements (pre-MVP planning) |

---

## Quick orientation

- **What's built?** → [COMPLIANCE.md](current/COMPLIANCE.md)
- **How does it work?** → [SPEC.md](current/SPEC.md)
- **What's the file layout?** → [STRUCTURE.md](current/STRUCTURE.md)
- **What's next after MVP?** → [FUTURE-PRD.md](future/FUTURE-PRD.md)
