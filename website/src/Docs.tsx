import ReactMarkdown from 'react-markdown';
import { Github, Terminal, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

const markdownContent = `
# SalesBud Documentation

**SalesBud is a two-channel outbound API built specifically for AI agents.** 

It is designed to be operated entirely from the command line by agents like Claude Code or OpenCode. There is no web UI. The CLI surface is a machine-readable API that your AI can compose, sequence, and execute to run end-to-end outbound campaigns.

---

## The Mental Model

\`\`\`text
You (or an AI Agent)
        ↓  natural language
    "Find 20 CEOs in Austin and start both sequences"
        ↓  AI agent translates to CLI commands
    salesbud workflow --query "CEO" --location "Austin" --max-leads 20 --json
        ↓  CLI executes, returns structured JSON
        ↓  AI reads output, decides next step
\`\`\`

## Core Capabilities

SalesBud handles the entire outbound lifecycle across two synchronous channels:

1. **LinkedIn Automation:** Scraping, connection requests, and dynamic DM sequences (powered by Playwright).
2. **Cold Email:** Browser-based email discovery, SMTP verification, and deep personalization (powered by Resend).
3. **Web Enrichment:** Company scraping to detect buying signals and tailor messaging (powered by Crawl4AI).
4. **Autonomous Operation:** 100% JSON-compliant outputs for every command.

---

## Agent Setup (Mode B)

To let your AI agent drive SalesBud, tell your agent to read the \`AGENTS.md\` file at the root of the repository.

### Example Agent Commands

\`\`\`bash
# 1. Discover current state
uv run python -m salesbud status --json

# 2. Find and enrich leads
uv run python -m salesbud scrape --query "Founder" --location "NY" --max 15 --json
uv run python -m salesbud find-emails --max 15 --json
uv run python -m salesbud enrich-all --max 15 --json

# 3. Execute sequences
uv run python -m salesbud sequence --json
uv run python -m salesbud email-sequence --json

# 4. Check for replies (auto-pauses sequences on reply)
uv run python -m salesbud check-replies --json
\`\`\`

---

## Human-in-the-Loop Use (Mode A)

You can still use SalesBud manually. Just omit the \`--json\` flag for human-readable terminal output.

\`\`\`bash
# Initialize database and view dashboard
uv run python -m salesbud init
uv run python -m salesbud dashboard

# Dry-run a sequence to verify logic before sending
uv run python -m salesbud sequence
uv run python -m salesbud email-sequence

# Go live
uv run python -m salesbud config dry_run 0
\`\`\`

---

## Cost Stack

SalesBud is built on open-source, free-tier primitives to keep your outbound costs at absolute zero.

* **LinkedIn Automation:** Playwright (Free)
* **Cold Email Delivery:** Resend (2,000/mo Free)
* **Email Discovery:** \`browser-use\` + SMTP (Unlimited Free)
* **Web Enrichment:** Crawl4AI (Open Source)
`;

export default function Docs() {
  return (
    <div className="min-h-screen font-sans selection:bg-app-pink/30 flex flex-col bg-app-bg text-app-text">
      {/* Navigation */}
      <nav className="border-b border-app-border/40 py-6 px-6 lg:px-12 flex justify-between items-center backdrop-blur-md sticky top-0 z-50">
        <Link to="/" className="flex items-center gap-2 font-mono font-bold text-xl tracking-tight hover:opacity-80 transition-opacity">
          <Terminal className="text-app-pink w-6 h-6" />
          <span>Sales<span className="text-app-blue">Bud</span></span>
        </Link>
        <div className="flex items-center gap-6 text-sm font-medium">
          <Link to="/" className="text-app-dim hover:text-app-text transition-colors flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" /> Back to Home
          </Link>
          <a 
            href="https://github.com/syntolabs/salesbud" 
            target="_blank" 
            rel="noreferrer"
            className="text-app-dim hover:text-app-text transition-colors flex items-center gap-2"
          >
            <Github className="w-5 h-5" />
            <span className="hidden sm:inline">GitHub</span>
          </a>
        </div>
      </nav>

      {/* Main Docs Content */}
      <main className="flex-1 w-full max-w-4xl mx-auto py-16 px-6">
        <div className="prose prose-invert prose-pre:bg-[#272822] prose-pre:border prose-pre:border-[#3E3D32] prose-a:text-app-blue hover:prose-a:text-app-blue/80 max-w-none">
          <ReactMarkdown>{markdownContent}</ReactMarkdown>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-app-border/40 py-12 px-6 lg:px-12 text-center text-app-dim flex flex-col items-center">
        <div className="flex items-center gap-2 font-mono font-bold text-lg mb-4 text-app-text/70">
          <Terminal className="text-app-green w-5 h-5" />
          <span>SalesBud Docs</span>
        </div>
      </footer>
    </div>
  );
}
