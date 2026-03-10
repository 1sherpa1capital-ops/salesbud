import { useState, useEffect } from 'react';
import { Github, Terminal, Bot, Mail, Shield, Zap, Eye, Database } from 'lucide-react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Docs from './Docs';

const BinaryBackground = () => {
  const [binaryStr, setBinaryStr] = useState('');

  useEffect(() => {
    const generateBinary = () => {
      let str = '';
      for (let i = 0; i < 4000; i++) {
        str += Math.random() < 0.2 ? '1' : '0';
        if (i % 80 === 0) str += '\n';
      }
      return str;
    };
    
    setBinaryStr(generateBinary());
  }, []);

  return <div className="binary-bg">{binaryStr}</div>;
};

const TerminalDemo = () => {
  const [typedCommand, setTypedCommand] = useState('');
  const [showOutput, setShowOutput] = useState(false);
  const fullCommand = 'uv run python -m salesbud workflow --query "CEO" --location "Austin" --max-leads 20 --json';
  
  useEffect(() => {
    let i = 0;
    const typingInterval = setInterval(() => {
      setTypedCommand(fullCommand.slice(0, i));
      i++;
      if (i > fullCommand.length) {
        clearInterval(typingInterval);
        setTimeout(() => setShowOutput(true), 400);
      }
    }, 30);
    return () => clearInterval(typingInterval);
  }, []);

  return (
    <div className="w-full max-w-4xl mx-auto rounded-xl overflow-hidden bg-[#1E1F1C]/90 backdrop-blur-xl terminal-shadow my-16 border border-[#3E3D32]">
      {/* Terminal Header */}
      <div className="h-12 px-4 flex items-center bg-[#272822] border-b border-[#3E3D32] relative">
        <div className="flex gap-2 absolute left-4">
          <div className="w-3 h-3 rounded-full bg-[#FF5F56] border border-[#E0443E]" />
          <div className="w-3 h-3 rounded-full bg-[#FFBD2E] border border-[#DEA123]" />
          <div className="w-3 h-3 rounded-full bg-[#27C93F] border border-[#1AAB29]" />
        </div>
        <div className="flex-1 text-center font-mono text-xs text-app-dim select-none flex items-center justify-center gap-2">
          salesbud — -zsh — 80x24
        </div>
      </div>
      
      {/* Terminal Body */}
      <div className="p-6 font-mono text-sm overflow-x-auto min-h-[420px]">
        <div className="flex items-center text-app-text/90">
          <span className="text-app-pink mr-3 font-bold">❯</span>
          <span className="text-app-green">{typedCommand.split(' ')[0]}</span>
          <span className="text-app-text ml-2">
            {typedCommand.split(' ').slice(1).join(' ')}
          </span>
          {!showOutput && <span className="w-2.5 h-5 bg-app-text ml-1 animate-pulse" />}
        </div>
        
        {showOutput && (
          <div className="mt-4 animate-in fade-in slide-in-from-top-2 duration-500">
            <div className="bg-[#272822]/50 border border-[#3E3D32]/50 rounded-lg p-5 mt-3 shadow-inner">
            <pre className="text-app-text/90 leading-relaxed text-[13px]">
{`{`}<span className="text-app-pink">"success"</span>{`: `}<span className="text-[#AE81FF]">true</span>{`,\n`}
{`  `}<span className="text-app-pink">"count"</span>{`: `}<span className="text-[#AE81FF]">20</span>{`,\n`}
{`  `}<span className="text-app-pink">"data"</span>{`: {\n`}
{`    `}<span className="text-app-pink">"steps"</span>{`: {\n`}
{`      `}<span className="text-app-pink">"scrape"</span>{`: `}<span className="text-[#AE81FF]">20</span>{` leads added,\n`}
{`      `}<span className="text-app-pink">"connect"</span>{`: `}<span className="text-[#AE81FF]">10</span>{` requests sent,\n`}
{`      `}<span className="text-app-pink">"emails_found"</span>{`: `}<span className="text-[#AE81FF]">15</span>{`,\n`}
{`      `}<span className="text-app-pink">"enriched"</span>{`: `}<span className="text-[#AE81FF]">20</span>{` companies\n`}
{`    }\n`}
{`  }\n`}
{`}`}
            </pre>
            </div>
            <div className="mt-4 text-app-dim text-xs">
              ✓ Anti-detection stealth active • Rate limits respected • Dry-run safe
            </div>
            <div className="mt-6 flex items-center text-app-text/90">
              <span className="text-app-pink mr-3 font-bold">❯</span>
              <span className="w-2.5 h-5 bg-app-dim ml-1 animate-pulse" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const FeatureCard = ({ icon: Icon, title, description, highlight = false, className = '' }: { icon: any, title: string, description: string, highlight?: boolean, className?: string }) => (
  <div className={`p-8 rounded-xl border ${highlight ? 'border-app-pink/30 bg-app-pink/5' : 'border-[#3E3D32] bg-[#1E1F1C]/40'} backdrop-blur-sm hover:bg-[#1E1F1C]/80 hover:border-app-dim/50 transition-all duration-300 flex flex-col group relative overflow-hidden ${className}`}>
    <div className="absolute top-0 left-0 w-8 h-8 border-t border-l border-app-dim/30 opacity-0 group-hover:opacity-100 transition-opacity" />
    <div className="absolute bottom-0 right-0 w-8 h-8 border-b border-r border-app-dim/30 opacity-0 group-hover:opacity-100 transition-opacity" />
    
    <div className={`w-12 h-12 rounded-xl ${highlight ? 'bg-app-pink/20 border-app-pink/30' : 'bg-[#272822] border-[#3E3D32]'} border flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 shadow-lg`}>
      <Icon className={`w-6 h-6 ${highlight ? 'text-app-pink' : 'text-app-text'} group-hover:text-app-pink transition-colors`} />
    </div>
    <h3 className="text-xl font-bold text-app-text mb-3 font-mono tracking-tight">{title}</h3>
    <p className="text-app-dim leading-relaxed flex-1 text-sm">{description}</p>
    {highlight && (
      <div className="mt-4 text-xs font-mono text-app-pink">NEW IN v1.2</div>
    )}
  </div>
);

const StatsBar = () => (
  <div className="w-full border-y border-[#3E3D32]/50 bg-[#1E1F1C]/30 backdrop-blur-sm">
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-8">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
        <div>
          <div className="text-3xl font-bold text-app-pink font-mono">50</div>
          <div className="text-xs text-app-dim uppercase tracking-wider mt-1">Test Cases</div>
        </div>
        <div>
          <div className="text-3xl font-bold text-app-green font-mono">100%</div>
          <div className="text-xs text-app-dim uppercase tracking-wider mt-1">Pass Rate</div>
        </div>
        <div>
          <div className="text-3xl font-bold text-app-yellow font-mono">&lt;10s</div>
          <div className="text-xs text-app-dim uppercase tracking-wider mt-1">Fast Mode</div>
        </div>
        <div>
          <div className="text-3xl font-bold text-app-blue font-mono">Zero</div>
          <div className="text-xs text-app-dim uppercase tracking-wider mt-1">API Costs</div>
        </div>
      </div>
    </div>
  </div>
);

function Home() {
  return (
    <div className="min-h-screen font-sans selection:bg-app-pink/30 flex flex-col relative">
      <BinaryBackground />
      {/* Navigation */}
      <nav className="border-b border-app-border/20 py-6 px-6 lg:px-12 flex justify-between items-center backdrop-blur-md sticky top-0 z-50">
        <Link to="/" className="flex items-center gap-2 font-mono font-bold text-xl tracking-tight">
          <Terminal className="text-app-text w-6 h-6" />
          <span>SalesBud</span>
          <span className="text-xs bg-app-pink/20 text-app-pink px-2 py-0.5 rounded font-mono">v1.2</span>
        </Link>
        <div className="flex items-center gap-8 text-sm font-mono tracking-wide uppercase">
          <Link to="/docs" className="text-app-dim hover:text-app-text transition-colors flex items-center gap-2">
            DOCS
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

      <main className="flex-1 flex flex-col items-center w-full z-10">
        {/* Hero */}
        <div className="w-full max-w-7xl mx-auto pt-24 pb-16 px-6 lg:px-12">
          <div className="w-full grid grid-cols-1 lg:grid-cols-2 gap-16 items-center animate-in fade-in duration-1000">
            <div className="text-left max-w-2xl">
              <div className="inline-flex items-center gap-2 text-app-pink text-sm font-mono mb-6 border border-app-pink/30 bg-app-pink/5 px-4 py-2 rounded-full">
                <Zap className="w-4 h-4" />
                <span>Now with Browser Stealth & Multi-Skill Coordination</span>
              </div>
              <h1 className="text-5xl md:text-7xl font-bold tracking-tighter mb-6 text-app-text leading-[1.1]">
                Outbound Sales<br />
                <span className="text-app-dim font-mono text-4xl md:text-6xl block mt-2">for AI Agents</span>
              </h1>
              <p className="text-lg md:text-xl text-app-dim mb-8 leading-relaxed">
                SalesBud v1.2 is the autonomous outbound CLI built for AI agents. Scrape LinkedIn, discover emails, enrich companies, and run sequences—all with anti-detection stealth and 100% JSON output.
              </p>
              <div className="flex flex-col sm:flex-row items-center gap-4">
                <Link 
                  to="/docs" 
                  className="w-full sm:w-auto flex items-center justify-center gap-2 bg-[#F8F8F2] text-[#1E1F1C] hover:bg-[#E6DB74] px-8 py-4 font-mono font-bold tracking-widest uppercase transition-colors"
                >
                  GET STARTED
                </Link>
                <a 
                  href="https://github.com/1sherpa1capital-ops/salesbud" 
                  className="w-full sm:w-auto flex items-center justify-center gap-2 border border-[#3E3D32] text-app-text hover:border-app-dim px-8 py-4 font-mono font-bold tracking-widest uppercase transition-colors"
                >
                  <Github className="w-4 h-4" />
                  VIEW ON GITHUB
                </a>
              </div>
              <p className="mt-6 text-app-dim text-sm">
                <span className="text-app-green">✓</span> Open source • <span className="text-app-green">✓</span> Local-first • <span className="text-app-green">✓</span> 50 evals passing
              </p>
            </div>
            
            <div className="w-full">
              <TerminalDemo />
            </div>
          </div>
        </div>

        {/* Stats Bar */}
        <StatsBar />

        {/* Features Grid */}
        <div className="w-full max-w-7xl mx-auto py-24 px-6 lg:px-12">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-app-text tracking-tighter mb-4">
              Built for AI Agents. <span className="text-app-dim">Battle-tested.</span>
            </h2>
            <p className="text-app-dim text-lg max-w-2xl mx-auto">
              Every command returns structured JSON. Every operation respects rate limits. 
              Every feature is tested with 50 comprehensive evals.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard 
              icon={Eye}
              title="Browser Stealth System"
              description="Anti-detection measures including rotating user agents, viewport randomization, and human-like timing to prevent LinkedIn account restrictions."
              highlight={true}
            />
            <FeatureCard 
              icon={Zap}
              title="Fast Email Discovery"
              description="New --quick flag finds emails in under 10 seconds (vs 60s normal) using parallel processing and intelligent timeout reduction."
              highlight={true}
            />
            <FeatureCard 
              icon={Database}
              title="Company Enrichment"
              description="Automatically enrich leads with company descriptions, size estimates, and buying signals using Crawl4AI-powered web scraping."
              highlight={true}
            />
            <FeatureCard 
              icon={Bot}
              title="Multi-Skill Coordination"
              description="Seamlessly integrates with agent-browser, copywriting, and sales-coach skills for complex workflows beyond CLI capabilities."
              highlight={true}
            />
            <FeatureCard 
              icon={Terminal}
              title="100% JSON Output"
              description="Every command supports --json flag for perfect LLM integration. Structured data that AI agents can parse and act on without ambiguity."
            />
            <FeatureCard 
              icon={Shield}
              title="Safety First"
              description="Dry-run mode by default. Never send real messages without explicit confirmation. Comprehensive safety checklist included."
            />
            <FeatureCard 
              icon={Mail}
              title="Two-Channel Outbound"
              description="LinkedIn DM sequences (5-step NEPQ) and cold email (4-step Resend) running in parallel for maximum reach."
            />
            <FeatureCard 
              className="md:col-span-2"
              icon={Github}
              title="Open Source & Free"
              description="Zero API costs. Built on open-source primitives: Playwright for automation, Resend for email (2k/mo free), Crawl4AI for enrichment, and DuckDuckGo for discovery."
            />
          </div>
        </div>

        {/* Code Example */}
        <div className="w-full border-y border-[#3E3D32]/50 bg-[#1E1F1C]/30 backdrop-blur-sm py-24">
          <div className="max-w-5xl mx-auto px-6 lg:px-12">
            <h2 className="text-3xl md:text-4xl font-bold text-app-text tracking-tighter mb-8 text-center">
              One Command. Full Pipeline.
            </h2>
            <div className="bg-[#272822] rounded-xl border border-[#3E3D32] p-6 overflow-x-auto">
              <pre className="font-mono text-sm text-app-text/90">
                <code>
{`# Run complete outbound campaign with stealth
uv run python -m salesbud workflow \\
  --query "CEO" \\
  --location "Austin, TX" \\
  --max-leads 20 \\
  --json

# Output: 20 leads scraped, 10 connections sent, 15 emails found, 20 enriched`}
                </code>
              </pre>
            </div>
            <p className="text-center text-app-dim mt-6 text-sm">
              The workflow command orchestrates scrape → connect → find-emails → enrich → sequences automatically.
            </p>
          </div>
        </div>

        {/* CTA Section */}
        <div className="w-full max-w-7xl mx-auto py-24 px-6 lg:px-12 text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-app-text tracking-tighter mb-6">
            Ready to automate your outbound?
          </h2>
          <p className="text-app-dim text-lg mb-8 max-w-2xl mx-auto">
            Join the agents already using SalesBud to run autonomous outbound campaigns. 
            100% open source. Zero API costs. Production-ready.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link 
              to="/docs" 
              className="w-full sm:w-auto flex items-center justify-center gap-2 bg-app-pink text-[#1E1F1C] hover:bg-app-pink/90 px-8 py-4 font-mono font-bold tracking-widest uppercase transition-colors"
            >
              READ THE DOCS
            </Link>
            <a 
              href="https://github.com/1sherpa1capital-ops/salesbud" 
              className="w-full sm:w-auto flex items-center justify-center gap-2 border border-[#3E3D32] text-app-text hover:border-app-dim px-8 py-4 font-mono font-bold tracking-widest uppercase transition-colors"
            >
              <Github className="w-4 h-4" />
              STAR ON GITHUB
            </a>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-app-border/40 py-12 px-6 lg:px-12 text-center text-app-dim flex flex-col items-center">
        <div className="flex items-center gap-2 font-mono font-bold text-lg mb-4 text-app-text/70">
          <Terminal className="text-app-green w-5 h-5" />
          <span>SalesBud</span>
          <span className="text-xs bg-app-pink/20 text-app-pink px-2 py-0.5 rounded">v1.2.0</span>
        </div>
        <p className="text-sm font-mono mb-4">Open Source under MIT License</p>
        <div className="flex gap-6 text-sm">
          <a href="https://github.com/1sherpa1capital-ops/salesbud" className="hover:text-app-text transition-colors flex items-center gap-2">
            <Github className="w-4 h-4" />
            GitHub
          </a>
          <Link to="/docs" className="hover:text-app-text transition-colors">
            Documentation
          </Link>
        </div>
        <p className="mt-8 text-xs text-app-dim/60">
          Built with stealth. Tested with 50 evals. Ready for production.
        </p>
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