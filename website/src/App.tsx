import { useState, useEffect } from 'react';
import { Github, Terminal, Bot, Mail, Shield } from 'lucide-react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Docs from './Docs';

const BinaryBackground = () => {
  const [binaryStr, setBinaryStr] = useState('');

  useEffect(() => {
    // Generate enough 1s and 0s to fill the screen
    const generateBinary = () => {
      let str = '';
      for (let i = 0; i < 4000; i++) {
        str += Math.random() < 0.2 ? '1' : '0';
        if (i % 80 === 0) str += '\n'; // Add line breaks
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
  const fullCommand = 'uv run python -m salesbud sequence --json';
  
  useEffect(() => {
    let i = 0;
    const typingInterval = setInterval(() => {
      setTypedCommand(fullCommand.slice(0, i));
      i++;
      if (i > fullCommand.length) {
        clearInterval(typingInterval);
        setTimeout(() => setShowOutput(true), 400);
      }
    }, 40);
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
      <div className="p-6 font-mono text-sm overflow-x-auto min-h-[380px]">
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
{`{\n`}
{`  `}<span className="text-app-pink">"success"</span>{`: `}<span className="text-[#AE81FF]">true</span>{`,\n`}
{`  `}<span className="text-app-pink">"count"</span>{`: `}<span className="text-[#AE81FF]">2</span>{`,\n`}
{`  `}<span className="text-app-pink">"data"</span>{`: [\n`}
{`    {\n`}
{`      `}<span className="text-app-pink">"name"</span>{`: `}<span className="text-app-yellow">"Alice M."</span>{`,\n`}
{`      `}<span className="text-app-pink">"role"</span>{`: `}<span className="text-app-yellow">"CEO"</span>{`,\n`}
{`      `}<span className="text-app-pink">"step"</span>{`: `}<span className="text-[#AE81FF]">2</span>{`,\n`}
{`      `}<span className="text-app-pink">"action"</span>{`: `}<span className="text-app-yellow">"connection_sent"</span>{`\n`}
{`    },\n`}
{`    {\n`}
{`      `}<span className="text-app-pink">"name"</span>{`: `}<span className="text-app-yellow">"Bob J."</span>{`,\n`}
{`      `}<span className="text-app-pink">"role"</span>{`: `}<span className="text-app-yellow">"VP Marketing"</span>{`,\n`}
{`      `}<span className="text-app-pink">"step"</span>{`: `}<span className="text-[#AE81FF]">3</span>{`,\n`}
{`      `}<span className="text-app-pink">"action"</span>{`: `}<span className="text-app-yellow">"email_sent"</span>{`\n`}
{`    }\n`}
{`  ]\n`}
{`}`}
            </pre>
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

const FeatureCard = ({ icon: Icon, title, description, className = '' }: { icon: any, title: string, description: string, className?: string }) => (
  <div className={`p-10 rounded-xl border border-[#3E3D32] bg-[#1E1F1C]/40 backdrop-blur-sm hover:bg-[#1E1F1C]/80 hover:border-app-dim/50 transition-all duration-300 flex flex-col group relative overflow-hidden ${className}`}>
    {/* AgentMail style dashed borders for the subtle tech feel */}
    <div className="absolute top-0 left-0 w-8 h-8 border-t border-l border-app-dim/30 opacity-0 group-hover:opacity-100 transition-opacity" />
    <div className="absolute bottom-0 right-0 w-8 h-8 border-b border-r border-app-dim/30 opacity-0 group-hover:opacity-100 transition-opacity" />
    
    <div className="w-14 h-14 rounded-xl bg-[#272822] border border-[#3E3D32] flex items-center justify-center mb-10 group-hover:scale-110 transition-transform duration-300 shadow-lg">
      <Icon className="w-6 h-6 text-app-text group-hover:text-app-pink transition-colors" />
    </div>
    <h3 className="text-2xl font-bold text-app-text mb-4 font-mono tracking-tight">{title}</h3>
    <p className="text-app-dim leading-relaxed flex-1 text-base">{description}</p>
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
        </Link>
        <div className="flex items-center gap-8 text-sm font-mono tracking-wide uppercase">
          <Link to="/docs" className="text-app-dim hover:text-app-text transition-colors flex items-center gap-2">
            DOCS
          </Link>
          <a 
            href="https://github.com/syntolabs/salesbud" 
            target="_blank" 
            rel="noreferrer"
            className="flex items-center gap-2 bg-[#F8F8F2] text-[#1E1F1C] px-4 py-2 hover:bg-[#E6DB74] transition-colors font-bold"
          >
            GITHUB
          </a>
        </div>
      </nav>

      <main className="flex-1 flex flex-col items-center pt-32 pb-24 px-6 lg:px-12 w-full max-w-7xl mx-auto z-10">
        {/* Hero */}
        <div className="w-full grid grid-cols-1 lg:grid-cols-2 gap-16 items-center animate-in fade-in duration-1000">
          <div className="text-left max-w-2xl">
            <h1 className="text-6xl md:text-8xl font-bold tracking-tighter mb-8 text-app-text leading-[1.1]">
              Email Outbound <br />
              <span className="text-app-dim font-mono text-5xl md:text-7xl block mt-2">for AI Agents</span>
            </h1>
            <p className="text-xl md:text-2xl text-app-dim mb-12 leading-relaxed font-light">
              SalesBud is the autonomous outbound API for agents. It manages your pipeline, scraping, and DMs like a human SDR.
            </p>
            <div className="flex flex-col sm:flex-row items-center gap-6">
              <Link 
                to="/docs" 
                className="w-full sm:w-auto flex items-center justify-center gap-2 bg-[#F8F8F2] text-[#1E1F1C] hover:bg-[#E6DB74] px-10 py-5 font-mono font-bold tracking-widest uppercase transition-colors"
              >
                START FOR FREE
              </Link>
              <a 
                href="https://github.com/syntolabs/salesbud" 
                className="w-full sm:w-auto flex items-center justify-center gap-2 border border-[#3E3D32] text-app-text hover:border-app-dim px-10 py-5 font-mono font-bold tracking-widest uppercase transition-colors"
              >
                DOCS
              </a>
            </div>
            <p className="mt-8 text-app-dim text-sm tracking-wide">No credit card required. Local-first workflow.</p>
          </div>
          
          {/* Terminal Section inside Hero Grid */}
          <div className="w-full">
            <TerminalDemo />
          </div>
        </div>

        {/* Features Header */}
        <div className="mt-40 text-center mb-16 px-4">
          <h2 className="text-5xl md:text-7xl font-bold text-app-text tracking-tighter mb-6">Built for scale.</h2>
          <div className="h-px w-full max-w-3xl mx-auto bg-gradient-to-r from-transparent via-[#3E3D32] to-transparent"></div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-[#3E3D32]/50 border border-[#3E3D32]/50 rounded-2xl overflow-hidden mt-8 w-full">
          <FeatureCard 
            className="md:col-span-2 lg:col-span-2 rounded-none border-none"
            icon={Bot}
            title="100M+ Actions Handled"
            description="Agent-first design built entirely around JSON outputs (--json) and standardized exit codes for perfect LLM workflow orchestration. No more parsing messy outputs."
          />
          <FeatureCard 
            className="md:col-span-1 lg:col-span-1 rounded-none border-none"
            icon={Terminal}
            title="Always On"
            description="Scrape LinkedIn profiles, send targeted connection requests, and run complex 5-step DM sequences autonomously in the background."
          />
          <FeatureCard 
            className="md:col-span-1 lg:col-span-1 rounded-none border-none"
            icon={Mail}
            title="Instant Discovery"
            description="Built-in Crawl4AI enrichment, intelligent email permutation guessing, and seamless Resend API integration for instantaneous cold outbound."
          />
          <FeatureCard 
            className="md:col-span-1 lg:col-span-2 rounded-none border-none"
            icon={Shield}
            title="Developer First"
            description="A stark, beautiful API wrap over Playwright browser automation. RESTful pipelines wrapped in simple CLI patterns. Get started in minutes, not days."
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-app-border/40 py-12 px-6 lg:px-12 text-center text-app-dim flex flex-col items-center">
        <div className="flex items-center gap-2 font-mono font-bold text-lg mb-4 text-app-text/70">
          <Terminal className="text-app-green w-5 h-5" />
          <span>SalesBud</span>
        </div>
        <p className="text-sm font-mono mb-6">Open Source under MIT License</p>
        <div className="flex gap-6">
          <a href="https://github.com/syntolabs/salesbud" className="hover:text-app-text transition-colors">
            <Github className="w-5 h-5" />
            <span className="sr-only">GitHub</span>
          </a>
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
