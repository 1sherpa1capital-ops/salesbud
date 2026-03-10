import ReactMarkdown from 'react-markdown';
import { Github, Terminal, ArrowLeft, BookOpen } from 'lucide-react';
import { Link } from 'react-router-dom';

const markdownContent = `
# SalesBud Documentation

## Overview

SalesBud is a command-line tool for autonomous outbound sales. It scrapes LinkedIn, discovers emails, enriches company data, and runs DM/email sequences—all with structured JSON output.

## Installation

\`\`\`bash
git clone https://github.com/1sherpa1capital-ops/salesbud.git
cd salesbud

# Install dependencies
bun install  # or npm install

# Initialize
uv run python -m salesbud init
\`\`\`

## Quick Start

\`\`\`bash
# Check status
uv run python -m salesbud status --json

# Scrape leads
uv run python -m salesbud scrape --query "CEO" --location "Austin" --max 20 --json

# Run full workflow
uv run python -m salesbud workflow --query "CEO" --location "Austin" --max-leads 20 --json
\`\`\`

## Commands

### System
| Command | Description |
|---------|-------------|
| \`init\` | Initialize database |
| \`status\` | System health check |
| \`config\` | View/set configuration |

### Lead Generation
| Command | Description |
|---------|-------------|
| \`scrape\` | Scrape LinkedIn profiles |
| \`connect\` | Send connection requests |
| \`check-connections\` | Check pending connections |

### Email Discovery
| Command | Description |
|---------|-------------|
| \`find-email <id> [--quick]\` | Find email for lead |
| \`find-emails --max N [--quick]\` | Batch discover emails |
| \`add-email <id> <email>\` | Manually add email |

**Note:** Use \`--quick\` for fast mode (<10s).

### Company Enrichment
| Command | Description |
|---------|-------------|
| \`set-company-url <id> <url>\` | Set company URL |
| \`enrich <id>\` | Enrich lead data |
| \`enrich-all --max N\` | Batch enrich |

### Sequences
| Command | Description |
|---------|-------------|
| \`sequence\` | Run DM sequence step |
| \`email-sequence\` | Run email sequence step |
| \`workflow\` | Full pipeline |

### Monitoring
| Command | Description |
|---------|-------------|
| \`dashboard\` | View lead dashboard |
| \`lead <id>\` | View lead details |
| \`check-replies\` | Check for replies |

## Configuration

\`\`\`bash
# View config
uv run python -m salesbud config

# Set rate limits
uv run python -m salesbud config dms_per_hour 8
uv run python -m salesbud config emails_per_hour 10

# Enable production (CAUTION)
uv run python -m salesbud config dry_run 0
\`\`\`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| \`LINKEDIN_SESSION_COOKIE\` | Yes | JSON cookie with \`li_at\` |
| \`RESEND_API_KEY\` | For email | Resend API key |

## Rate Limits

- LinkedIn DMs: 8/hour, 50/day
- LinkedIn Connections: ≤10 per run
- Emails: 10/hour, 50/day

## Example Workflows

### Quick Lead Generation
\`\`\`bash
uv run python -m salesbud scrape --query "Founder" --location "NYC" --max 15 --json
uv run python -m salesbud find-emails --max 15 --quick --json
uv run python -m salesbud email-sequence --json
\`\`\`

### Deep Research Campaign
\`\`\`bash
# 1. Scrape
uv run python -m salesbud scrape --query "CTO" --location "SF" --max 10 --json

# 2. Set URLs and enrich
uv run python -m salesbud set-company-url 1 "https://company.com" --json
uv run python -m salesbud enrich 1 --json

# 3. Connect and sequence
uv run python -m salesbud connect --max 10 --json
uv run python -m salesbud sequence --json
\`\`\`

## Troubleshooting

**"scrape returns 0 leads"**
LinkedIn cookie expired. Refresh in .env:
\`\`\`bash
cat .env | grep LINKEDIN_SESSION_COOKIE
\`\`\`

**"No module named 'salesbud'"**
Use \`uv run python\` not plain \`python\`.

**Rate limit errors**
Reduce batch size: \`--max 5\`

## License

MIT License — Open source and free to use.
`;

export default function Docs() {
  return (
    <div className="min-h-screen bg-app-bg text-app-text">
      {/* Header */}
      <header className="border-b border-app-border px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 font-mono font-bold text-lg hover:opacity-80 transition-opacity">
            <Terminal className="w-5 h-5" />
            <span>SalesBud</span>
            <span className="text-xs text-app-dim font-normal">v1.2.0</span>
          </Link>
          <div className="flex items-center gap-6 text-sm">
            <Link to="/" className="text-app-dim hover:text-app-text transition-colors flex items-center gap-1.5">
              <ArrowLeft className="w-4 h-4" />
              Back
            </Link>
            <a 
              href="https://github.com/1sherpa1capital-ops/salesbud" 
              target="_blank" 
              rel="noreferrer"
              className="text-app-dim hover:text-app-text transition-colors flex items-center gap-1.5"
            >
              <Github className="w-4 h-4" />
              GitHub
            </a>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-12">
        <div className="prose prose-invert prose-pre:bg-app-surface prose-pre:border prose-pre:border-app-border max-w-none">
          <ReactMarkdown>{markdownContent}</ReactMarkdown>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-app-border px-6 py-8 mt-12">
        <div className="max-w-4xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-app-dim">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4" />
            <span>SalesBud Documentation</span>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/" className="hover:text-app-text transition-colors">
              Home
            </Link>
            <a 
              href="https://github.com/1sherpa1capital-ops/salesbud" 
              className="hover:text-app-text transition-colors"
            >
              GitHub
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}