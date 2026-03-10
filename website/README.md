# SalesBud Website

The official website for SalesBud v1.2.0 - Autonomous outbound CLI for AI agents.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 🛠️ Tech Stack

- **Framework:** React 19 + TypeScript
- **Build Tool:** Vite 7
- **Styling:** Tailwind CSS 4
- **Router:** React Router 7
- **Icons:** Lucide React
- **Fonts:** Geist Sans & Mono

## 📁 Project Structure

```
website/
├── src/
│   ├── App.tsx          # Homepage with features & CTA
│   ├── Docs.tsx         # Documentation page
│   ├── index.css        # Global styles
│   └── main.tsx         # Entry point
├── public/              # Static assets
├── index.html           # HTML template
└── package.json         # Dependencies
```

## 📝 Content

### Homepage (App.tsx)
- Hero section with animated terminal demo
- Stats bar (50 evals, 100% pass rate, <10s fast mode, zero API costs)
- Feature grid highlighting v1.2.0 features:
  - Browser Stealth System
  - Fast Email Discovery
  - Company Enrichment
  - Multi-Skill Coordination
- Code example section
- CTA section

### Docs Page (Docs.tsx)
- Comprehensive documentation for SalesBud v1.2.0
- Sidebar navigation with sections:
  - What's New (v1.2.0 features)
  - Getting Started
  - Agent Usage (Mode B)
  - All Commands
  - Features
  - Resources
  - Troubleshooting
  - Example Workflows

## 🎨 Design System

### Colors (Monokai Theme)
- Background: `#1E1F1C`
- Text: `#F8F8F2`
- Dim: `#75715E`
- Pink: `#F92672`
- Green: `#A6E22E`
- Yellow: `#E6DB74`
- Blue: `#66D9EF`

### Typography
- Headings: Geist Sans, bold, tracking-tighter
- Body: Geist Sans
- Code: Geist Mono

## 📦 Deployment

The site is built to `dist/` directory and can be deployed to any static host:

```bash
# Build
npm run build

# Deploy to GitHub Pages, Vercel, Netlify, etc.
```

## 🔗 Links

- **GitHub:** https://github.com/1sherpa1capital-ops/salesbud
- **Documentation:** See AGENTS.md in root repository
- **Live Site:** [Your deployment URL]

## 📄 License

MIT License - Same as SalesBud project