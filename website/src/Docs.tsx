import ReactMarkdown from 'react-markdown';
import { Github, Terminal, ArrowLeft, Book, Zap, Eye, Bot } from 'lucide-react';
import { Link } from 'react-router-dom';

const markdownContent = `
# SalesBud v1.2.0 Documentation

**The autonomous outbound CLI built specifically for AI agents.**

SalesBud is a two-channel outbound API (LinkedIn DMs + Cold Email) designed to be operated entirely from the command line by AI agents like Claude Code, OpenCode, or any LLM with tool access. Every command returns structured JSON for perfect machine readability.

---

## 🚀 What's New in v1.2.0

### Browser Stealth System
New anti-detection measures to prevent LinkedIn from blocking automation:
- Rotating user agents and viewport randomization
- Stealth script to hide \`navigator.webdriver\` and automation signatures
- Human-like timing with jitter delays
- Automatic retry on ERR_TOO_MANY_REDIRECTS
- CAPTCHA/challenge detection

### Fast Email Discovery
New \`--quick\` flag for blazing fast email finding:
- **< 10 seconds** vs 60s normal mode
- Parallel processing with 5 workers
- Skips slow company page scraping (saves ~40s)
- Reduced timeouts: DuckDuckGo 15s→5s, SMTP 10s→3s

### Company Enrichment
Automatically enrich leads with company intelligence:
- Set company URLs with \`set-company-url\` command
- Extract descriptions, size estimates, buying signals
- Powered by Crawl4AI web scraping
- Batch enrichment with \`enrich-all\`

### Multi-Skill Coordination
Seamlessly integrates with other AI skills:
- **agent-browser**: Fallback when find-email fails
- **copywriting**: Improve messaging when reply rates are low
- **sales-coach**: Objection handling and strategy

---

## 📋 Quick Start

\`\`\`bash
# Clone and setup
git clone https://github.com/1sherpa1capital-ops/salesbud.git
cd salesbud

# Install dependencies
bun install  # or: npm install

# Initialize database
uv run python -m salesbud init

# Check system status
uv run python -m salesbud status --json

# Run your first campaign
uv run python -m salesbud workflow --query "CEO" --location "Austin" --max-leads 10 --json
\`\`\`

---

## 🛠️ All Commands

### System Commands

| Command | Description |
|---------|-------------|
| \`init\` | Initialize database with automatic migration |
| \`status\` | System health (DB, queues, auth) |
| \`config [key] [value]\` | Get/set configuration |
| \`test\` | Run full test sequence |

### Lead Generation

| Command | Description |
|---------|-------------|
| \`scrape --query "CEO" --location "Austin" --max 20\` | Scrape LinkedIn profiles |
| \`connect --max 10\` | Send connection requests |
| \`check-connections\` | Check pending connection status |

### Email Discovery

| Command | Description |
|---------|-------------|
| \`find-email <id> [--quick]\` | Find email for specific lead |
| \`find-emails --max 20 [--quick]\` | Batch discover emails |
| \`add-email <id> <email>\` | Manually add email to lead |

**Use \`--quick\` for fast mode (<10s)** when you don't need full verification.

### Company Enrichment

| Command | Description |
|---------|-------------|
| \`set-company-url <id> <url>\` | Set company URL (required before enrich) |
| \`enrich <id>\` | Enrich lead with company data |
| \`enrich-all --max 10\` | Batch enrich multiple leads |

**Note:** You must set company_url before running enrich.

### Sequences

| Command | Description |
|---------|-------------|
| \`sequence\` | Run DM sequence step (5-step NEPQ) |
| \`email-sequence\` | Run cold email step (4-step) |
| \`workflow\` | Full pipeline: scrape → connect → check → sequence → email |

### Inbox & Monitoring

| Command | Description |
|---------|-------------|
| \`check-replies\` | Scan LinkedIn inbox for replies |
| \`dashboard\` | Unified DM + Email dashboard |
| \`lead <id>\` | Full lead detail with activity log |

---

## 🤖 Agent Usage (Mode B)

For AI agents operating SalesBud autonomously:

### 1. Always Check Status First

\`\`\`bash
uv run python -m salesbud status --json
\`\`\`

Check \`dry_run\` mode before any campaign that sends messages.

### 2. Full Outbound Campaign with Deep Research

\`\`\`bash
# 1. Scrape leads
uv run python -m salesbud scrape --query "CEO" --location "Austin" --max 20 --json

# 2. Set company URLs for enrichment
uv run python -m salesbud set-company-url 1 "https://company1.com" --json
uv run python -m salesbud set-company-url 2 "https://company2.com" --json

# 3. Enrich leads with company data
uv run python -m salesbud enrich 1 --json
uv run python -m salesbud enrich 2 --json

# 4. Discover emails (use --quick for speed)
uv run python -m salesbud find-emails --max 20 --quick --json

# 5. Send connections
uv run python -m salesbud connect --max 10 --json

# 6. Check connections (wait 24-48h in production)
uv run python -m salesbud check-connections --json

# 7. Run sequences
uv run python -m salesbud sequence --json
uv run python -m salesbud email-sequence --json

# 8. Monitor for replies
uv run python -m salesbud check-replies --json
\`\`\`

### 3. Multi-Skill Workflow

When SalesBud alone isn't enough, coordinate with other skills:

\`\`\`bash
# Scenario: find-email fails
uv run python -m salesbud find-email 42 --quick --json
# Output: {"success": false}

# SWITCH TO agent-browser skill
# Visit company website, extract email from /team page
# RETURN TO salesbud

uv run python -m salesbud add-email 42 "found@company.com" --json
\`\`\`

---

## 🎯 Key Features

### Browser Stealth System
Located in \`src/salesbud/utils/browser.py\`:
- **STEALTH_SCRIPT**: Hides automation markers
- **get_stealth_context()**: Creates anti-detection browser context
- **safe_goto()**: Navigation with retry logic
- **jitter_delay()**: Human-like timing

### Rate Limits (Respected Even with Stealth)
- LinkedIn DMs: 8/hour, 50/day
- LinkedIn Connections: ≤10 per run
- Emails: 10/hour, 50/day

### Safety Features
- Dry-run mode by default
- Automatic status checks
- Cookie expiration detection
- Comprehensive troubleshooting

---

## 📊 JSON Output Format

Every command supports \`--json\` for machine-readable output:

\`\`\`json
{
  "success": true,
  "count": 20,
  "data": [...],
  "errors": []
}
\`\`\`

### Exit Codes
- \`0\` - Success
- \`1\` - Error (check "errors" field)
- \`2\` - Rate-limited (try again later)
- \`3\` - Nothing to process (no leads due)

---

## 🔧 Configuration

\`\`\`bash
# View all config
uv run python -m salesbud config

# Set rate limits
uv run python -m salesbud config dms_per_hour 8
uv run python -m salesbud config emails_per_hour 10

# Enable production mode (CAUTION)
uv run python -m salesbud config dry_run 0
\`\`\`

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| \`LINKEDIN_SESSION_COOKIE\` | Yes | JSON cookie array with \`li_at\` |
| \`LINKEDIN_EMAIL\` | Fallback | LinkedIn email |
| \`LINKEDIN_PASSWORD\` | Fallback | LinkedIn password |
| \`RESEND_API_KEY\` | For email | Resend API key |
| \`RESEND_FROM_EMAIL\` | No | Sender (default provided) |

---

## 🧪 Testing

SalesBud includes 50 comprehensive evals with 100% pass rate:

\`\`\`bash
# View eval results
ls .agents/skills/salesbud-cli-workspace/iteration-4/

# Run your own tests
uv run python -m salesbud test
\`\`\`

### Eval Categories
- **30 Trigger Tests** - When to use the skill
- **20 Functional Tests** - Command execution accuracy
- **100% Pass Rate** - Production ready

---

## 🐛 Troubleshooting

### "scrape returns 0 leads"
LinkedIn session cookie expired. Refresh in .env:
\`\`\`bash
cat .env | grep LINKEDIN_SESSION_COOKIE
# Refresh cookie in browser DevTools → Application → Cookies → li_at
\`\`\`

### "No module named 'salesbud'"
Use \`uv run python\` not plain \`python\`:
\`\`\`bash
# Wrong
python -m salesbud

# Right
uv run python -m salesbud
\`\`\`

### Rate Limit Errors
Wait before retrying or reduce batch sizes:
\`\`\`bash
uv run python -m salesbud connect --max 5  # Smaller batch
\`\`\`

### enrich Command Requires company_url
Set URL before enriching:
\`\`\`bash
uv run python -m salesbud set-company-url 5 "https://company.com" --json
uv run python -m salesbud enrich 5 --json
\`\`\`

---

## 📚 Resources

- **[GitHub Repository](https://github.com/1sherpa1capital-ops/salesbud)** - Source code & issues
- **[AGENTS.md](/AGENTS.md)** - Complete AI agent reference
- **[CHANGELOG.md](/changelog.md)** - Version history
- **[PRD.md](/docs/current/PRD.md)** - Product requirements
- **[SPEC.md](/docs/current/SPEC.md)** - Technical specification

---

## 💡 Example Workflows

### Workflow 1: Quick Lead Generation
\`\`\`bash
uv run python -m salesbud scrape --query "Founder" --location "NYC" --max 15 --json
uv run python -m salesbud find-emails --max 15 --quick --json
uv run python -m salesbud email-sequence --json
\`\`\`

### Workflow 2: Deep Research Campaign
\`\`\`bash
# 1. Scrape
uv run python -m salesbud scrape --query "CTO" --location "SF" --max 10 --json

# 2. Research (use agent-browser skill for each company)
# 3. Set URLs and enrich
uv run python -m salesbud set-company-url 1 "https://company.com" --json
uv run python -m salesbud enrich 1 --json

# 4. Connect and sequence
uv run python -m salesbud connect --max 10 --json
uv run python -m salesbud sequence --json
\`\`\`

### Workflow 3: Full Pipeline
\`\`\`bash
uv run python -m salesbud workflow --query "VP Sales" --location "Chicago" --max-leads 20 --max-connections 10 --json
\`\`\`

---

## 📄 License

MIT License - Open source and free to use.

Built with stealth. Tested with 50 evals. Ready for production.
`;

export default function Docs() {
  return (
    <div className="min-h-screen font-sans selection:bg-app-pink/30 flex flex-col bg-app-bg text-app-text">
      {/* Navigation */}
      <nav className="border-b border-app-border/40 py-6 px-6 lg:px-12 flex justify-between items-center backdrop-blur-md sticky top-0 z-50">
        <Link to="/" className="flex items-center gap-2 font-mono font-bold text-xl tracking-tight hover:opacity-80 transition-opacity">
          <Terminal className="text-app-text w-6 h-6" />
          <span>SalesBud</span>
          <span className="text-xs bg-app-pink/20 text-app-pink px-2 py-0.5 rounded font-mono">v1.2</span>
        </Link>
        <div className="flex items-center gap-6 text-sm font-medium">
          <Link to="/" className="text-app-dim hover:text-app-text transition-colors flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" /> Back
          </Link>
          <a 
            href="https://github.com/1sherpa1capital-ops/salesbud" 
            target="_blank" 
            rel="noreferrer"
            className="flex items-center gap-2 bg-[#F8F8F2] text-[#1E1F1C] px-4 py-2 hover:bg-[#E6DB74] transition-colors font-bold"
          >
            <Github className="w-4 h-4" />
            GITHUB
          </a>
        </div>
      </nav>

      {/* Sidebar + Main Content */}
      <div className="flex-1 flex">
        {/* Sidebar */}
        <aside className="hidden lg:block w-64 border-r border-app-border/20 p-6 sticky top-[73px] h-[calc(100vh-73px)] overflow-y-auto">
          <nav className="space-y-6">
            <div>
              <h3 className="text-xs font-bold text-app-dim uppercase tracking-wider mb-3 flex items-center gap-2">
                <Zap className="w-3 h-3" /> What's New
              </h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#whats-new-in-v120" className="text-app-text hover:text-app-pink transition-colors">v1.2.0 Features</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-bold text-app-dim uppercase tracking-wider mb-3 flex items-center gap-2">
                <Book className="w-3 h-3" /> Getting Started
              </h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#quick-start" className="text-app-text hover:text-app-pink transition-colors">Quick Start</a></li>
                <li><a href="#all-commands" className="text-app-text hover:text-app-pink transition-colors">All Commands</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-bold text-app-dim uppercase tracking-wider mb-3 flex items-center gap-2">
                <Bot className="w-3 h-3" /> Agent Usage
              </h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#agent-usage-mode-b" className="text-app-text hover:text-app-pink transition-colors">Mode B Guide</a></li>
                <li><a href="#multi-skill-workflow" className="text-app-text hover:text-app-pink transition-colors">Multi-Skill</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-bold text-app-dim uppercase tracking-wider mb-3 flex items-center gap-2">
                <Eye className="w-3 h-3" /> Features
              </h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#key-features" className="text-app-text hover:text-app-pink transition-colors">Key Features</a></li>
                <li><a href="#browser-stealth-system" className="text-app-text hover:text-app-pink transition-colors">Stealth System</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-bold text-app-dim uppercase tracking-wider mb-3">Resources</h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#resources" className="text-app-text hover:text-app-pink transition-colors">Links</a></li>
                <li><a href="#example-workflows" className="text-app-text hover:text-app-pink transition-colors">Workflows</a></li>
                <li><a href="#troubleshooting" className="text-app-text hover:text-app-pink transition-colors">Troubleshooting</a></li>
              </ul>
            </div>
          </nav>
        </aside>

        {/* Main Docs Content */}
        <main className="flex-1 w-full max-w-4xl mx-auto py-12 px-6 lg:px-12">
          <div className="prose prose-invert prose-pre:bg-[#272822] prose-pre:border prose-pre:border-[#3E3D32] prose-a:text-app-pink hover:prose-a:text-app-pink/80 max-w-none prose-headings:font-mono prose-headings:tracking-tight">
            <ReactMarkdown>{markdownContent}</ReactMarkdown>
          </div>
        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-app-border/40 py-8 px-6 lg:px-12 text-center text-app-dim flex flex-col items-center">
        <div className="flex items-center gap-2 font-mono font-bold text-lg mb-2 text-app-text/70">
          <Terminal className="text-app-green w-5 h-5" />
          <span>SalesBud Docs</span>
          <span className="text-xs bg-app-pink/20 text-app-pink px-2 py-0.5 rounded">v1.2.0</span>
        </div>
        <p className="text-sm">Built with stealth. Tested with 50 evals.</p>
      </footer>
    </div>
  );
}