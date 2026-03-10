import { Github, Terminal, Zap, Eye, Database, Bot, ChevronRight } from 'lucide-react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Docs from './Docs';

const TerminalDemo = () => {
  return (
    <div className="w-full max-w-3xl mx-auto my-12">
      {/* Simple Terminal Window */}
      <div className="border border-app-border bg-app-surface">
        {/* Terminal Header */}
        <div className="h-8 px-3 flex items-center bg-app-border/50 border-b border-app-border">
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-[#FF5F56]" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#FFBD2E]" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#27C93F]" />
          </div>
          <div className="flex-1 text-center font-mono text-[10px] text-app-dim">
            salesbud — zsh
          </div>
        </div>
        
        {/* Terminal Body */}
        <div className="p-4 font-mono text-sm">
          <div className="flex items-center text-app-text">
            <span className="text-app-pink mr-2">❯</span>
            <span className="text-app-green">uv</span>
            <span className="text-app-text ml-1.5">run python -m salesbud dashboard</span>
          </div>
          
          <div className="mt-4">
            <div className="text-app-text mb-2">
              <span className="font-bold">SalesBud</span> — LIVE
            </div>
            
            <div className="text-app-text mb-4">
              Leads: <span className="font-bold">12</span> total |{' '}
              <span className="text-app-blue">11</span> new |{' '}
              <span className="text-app-yellow">0</span> pending |{' '}
              <span className="text-app-green">0</span> connected |{' '}
              <span className="text-app-cyan">1</span> active
            </div>
            
            {/* Simple Table */}
            <div className="border-t border-app-border mt-4 pt-4">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="text-app-dim border-b border-app-border">
                    <th className="py-1 pr-4 font-normal">ID</th>
                    <th className="py-1 pr-4 font-normal">Name</th>
                    <th className="py-1 pr-4 font-normal">Status</th>
                    <th className="py-1 pr-4 font-normal text-center">DM</th>
                    <th className="py-1 pr-4 font-normal text-center">Email</th>
                    <th className="py-1 font-normal">Company</th>
                  </tr>
                </thead>
                <tbody className="text-app-text">
                  <tr className="border-b border-app-border/50">
                    <td className="py-1.5 pr-4 text-app-dim">1</td>
                    <td className="py-1.5 pr-4">Marouf Shah</td>
                    <td className="py-1.5 pr-4"><span className="text-app-cyan">active</span></td>
                    <td className="py-1.5 pr-4 text-center">1</td>
                    <td className="py-1.5 pr-4 text-center text-app-green">✓</td>
                    <td className="py-1.5 text-app-dim">Synto Labs</td>
                  </tr>
                  <tr className="border-b border-app-border/50">
                    <td className="py-1.5 pr-4 text-app-dim">2</td>
                    <td className="py-1.5 pr-4">Chris-Tia Donaldson</td>
                    <td className="py-1.5 pr-4"><span className="text-app-blue">new</span></td>
                    <td className="py-1.5 pr-4 text-center">0</td>
                    <td className="py-1.5 pr-4 text-center text-app-dim">·</td>
                    <td className="py-1.5 text-app-dim">—</td>
                  </tr>
                  <tr className="border-b border-app-border/50">
                    <td className="py-1.5 pr-4 text-app-dim">3</td>
                    <td className="py-1.5 pr-4">Revathi Advaithi</td>
                    <td className="py-1.5 pr-4"><span className="text-app-blue">new</span></td>
                    <td className="py-1.5 pr-4 text-center">0</td>
                    <td className="py-1.5 pr-4 text-center text-app-dim">·</td>
                    <td className="py-1.5 text-app-dim">Flex</td>
                  </tr>
                  <tr>
                    <td className="py-1.5 pr-4 text-app-dim">4</td>
                    <td className="py-1.5 pr-4">Chris Cocks</td>
                    <td className="py-1.5 pr-4"><span className="text-app-blue">new</span></td>
                    <td className="py-1.5 pr-4 text-center">0</td>
                    <td className="py-1.5 pr-4 text-center text-app-dim">·</td>
                    <td className="py-1.5 text-app-dim">Microsoft</td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <div className="mt-4 text-app-dim text-xs">
              Commands: lead &lt;id&gt; | add-email &lt;id&gt; &lt;email&gt; | sequence
            </div>
            
            <div className="mt-4 flex items-center text-app-text">
              <span className="text-app-pink mr-2">❯</span>
              <span className="w-2 h-4 bg-app-text animate-pulse" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const CommandItem = ({ command, description }: { command: string; description: string }) => (
  <div className="flex items-start gap-4 py-2 border-b border-app-border/30 last:border-0">
    <code className="text-app-green font-mono text-sm min-w-[240px]">{command}</code>
    <span className="text-app-dim text-sm">{description}</span>
  </div>
);

function Home() {
  return (
    <div className="min-h-screen font-sans bg-app-bg text-app-text">
      {/* Clean Header */}
      <header className="border-b border-app-border px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 font-mono font-bold text-lg">
            <Terminal className="w-5 h-5" />
            <span>SalesBud</span>
            <span className="text-xs text-app-dim font-normal">v1.2.0</span>
          </Link>
          <div className="flex items-center gap-6 text-sm">
            <Link to="/docs" className="text-app-dim hover:text-app-text transition-colors">
              Documentation
            </Link>
            <a 
              href="https://github.com/1sherpa1capital-ops/salesbud" 
              target="_blank" 
              rel="noreferrer"
              className="flex items-center gap-1.5 text-app-dim hover:text-app-text transition-colors"
            >
              <Github className="w-4 h-4" />
              GitHub
            </a>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-16">
        {/* Hero */}
        <div className="mb-16">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            Autonomous Outbound CLI
          </h1>
          <p className="text-app-dim text-lg max-w-2xl mb-8">
            SalesBud is a two-channel outbound API (LinkedIn + Email) designed for AI agents. 
            Every command returns structured JSON for perfect machine readability.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link 
              to="/docs" 
              className="inline-flex items-center gap-2 bg-app-text text-app-bg px-6 py-3 font-mono text-sm hover:bg-app-text/90 transition-colors"
            >
              Get Started
              <ChevronRight className="w-4 h-4" />
            </Link>
            <a 
              href="https://github.com/1sherpa1capital-ops/salesbud" 
              className="inline-flex items-center gap-2 border border-app-border px-6 py-3 font-mono text-sm hover:border-app-text transition-colors"
            >
              <Github className="w-4 h-4" />
              View Source
            </a>
          </div>
        </div>

        {/* Terminal Demo */}
        <TerminalDemo />

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-app-border mb-16">
          {[
            { label: 'Test Cases', value: '50', color: 'text-app-text' },
            { label: 'Pass Rate', value: '100%', color: 'text-app-green' },
            { label: 'Fast Mode', value: '<10s', color: 'text-app-cyan' },
            { label: 'API Costs', value: 'Zero', color: 'text-app-yellow' },
          ].map((stat) => (
            <div key={stat.label} className="bg-app-bg p-6 text-center">
              <div className={`text-2xl font-bold font-mono ${stat.color}`}>{stat.value}</div>
              <div className="text-xs text-app-dim uppercase tracking-wider mt-1">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Features */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold mb-8">Features</h2>
          <div className="grid md:grid-cols-2 gap-px bg-app-border">
            {[
              { icon: Eye, title: 'Browser Stealth', desc: 'Anti-detection measures for LinkedIn automation' },
              { icon: Zap, title: 'Fast Discovery', desc: 'Find emails in under 10 seconds with --quick flag' },
              { icon: Database, title: 'Enrichment', desc: 'Auto-enrich leads with company intelligence' },
              { icon: Bot, title: 'Multi-Skill', desc: 'Integrates with agent-browser and copywriting skills' },
            ].map((feature) => (
              <div key={feature.title} className="bg-app-bg p-6 flex gap-4">
                <feature.icon className="w-5 h-5 text-app-pink flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-bold mb-1">{feature.title}</h3>
                  <p className="text-app-dim text-sm">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Commands */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold mb-6">Quick Start</h2>
          <div className="bg-app-surface border border-app-border p-6">
            <CommandItem command="scrape --query CEO" description="Scrape LinkedIn leads" />
            <CommandItem command="connect --max 10" description="Send connection requests" />
            <CommandItem command="find-emails --quick" description="Discover emails fast" />
            <CommandItem command="sequence" description="Run DM sequence" />
          </div>
        </div>

        {/* Code Example */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold mb-6">One Command, Full Pipeline</h2>
          <div className="bg-app-surface border border-app-border p-4 font-mono text-sm">
            <div className="text-app-dim mb-2"># Run complete outbound campaign</div>
            <div className="text-app-text">
              <span className="text-app-green">uv</span> run python -m salesbud workflow \\
            </div>
            <div className="text-app-text ml-4">
              --query <span className="text-app-yellow">"CEO"</span> \\
            </div>
            <div className="text-app-text ml-4">
              --location <span className="text-app-yellow">"Austin, TX"</span> \\
            </div>
            <div className="text-app-text ml-4">
              --max-leads <span className="text-app-cyan">20</span> \\
            </div>
            <div className="text-app-text ml-4">
              --json
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-app-border px-6 py-8">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-app-dim">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4" />
            <span>SalesBud v1.2.0</span>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/docs" className="hover:text-app-text transition-colors">
              Documentation
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

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/docs" element={<Docs />} />
      </Routes>
    </Router>
  );
}