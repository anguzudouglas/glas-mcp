import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'

const STATS = [
  { value: '8', label: 'Production Tools' },
  { value: 'SSE', label: 'MCP Transport' },
  { value: 'REST', label: 'API Style' },
  { value: '0', label: 'Config Required' },
]

const FEATURES = [
  {
    icon: '⚡',
    title: 'Zero Configuration',
    desc: 'Drop a folder with main.py and tool.yaml — it auto-discovers and registers on restart. No registration code, no wiring.',
    badge: 'Auto-discovery',
  },
  {
    icon: '🔌',
    title: 'Dual Transport',
    desc: 'Every tool is reachable via MCP over SSE (for AI agents) and plain REST JSON (for your own apps). One server, two interfaces.',
    badge: 'SSE + REST',
  },
  {
    icon: '🛠',
    title: '8 Built-in Tools',
    desc: 'Web search, web fetch, math, chart generation, DOCX, XLSX, PPTX, and PDF — all production-hardened and ready to use.',
    badge: 'Batteries included',
  },
  {
    icon: '🐳',
    title: 'Docker Ready',
    desc: 'Single Dockerfile. One command to build and run locally, or point Render at the repo and it deploys automatically.',
    badge: 'One-command deploy',
  },
  {
    icon: '📐',
    title: 'Typed Schemas',
    desc: 'Every tool declares its input schema in tool.yaml. Auto-surfaced to MCP clients — no extra documentation step.',
    badge: 'JSON Schema',
  },
  {
    icon: '🔑',
    title: 'Multi-Provider Playground',
    desc: 'Built-in playground supports Anthropic (Claude), OpenRouter, Groq, and Gemini. Paste your key and start in 10 seconds.',
    badge: 'Bring your key',
  },
]

const TOOLS_PREVIEW = [
  { name: 'web_search', cat: 'Search', desc: 'DuckDuckGo search, up to 250 results' },
  { name: 'web_fetch', cat: 'Fetch', desc: 'Scrape and parse any URL' },
  { name: 'math_eval', cat: 'Math', desc: 'Evaluate mathematical expressions' },
  { name: 'plot_chart', cat: 'Charts', desc: 'Generate charts as base64 PNG' },
  { name: 'create_docx', cat: 'Documents', desc: 'Generate Word documents' },
  { name: 'create_xlsx', cat: 'Documents', desc: 'Generate Excel spreadsheets' },
  { name: 'create_pptx', cat: 'Documents', desc: 'Generate PowerPoint presentations' },
  { name: 'create_pdf', cat: 'Documents', desc: 'Generate PDF files' },
]

const CAT_COLORS = {
  Search: { bg: 'rgba(91,110,245,.1)', color: '#5B6EF5', border: 'rgba(91,110,245,.2)' },
  Fetch: { bg: 'rgba(0,200,248,.1)', color: '#00C8F8', border: 'rgba(0,200,248,.2)' },
  Math: { bg: 'rgba(245,166,35,.1)', color: '#F5A623', border: 'rgba(245,166,35,.2)' },
  Charts: { bg: 'rgba(16,217,160,.1)', color: '#10D9A0', border: 'rgba(16,217,160,.2)' },
  Documents: { bg: 'rgba(124,92,240,.1)', color: '#7C5CF0', border: 'rgba(124,92,240,.2)' },
}

const JS_SNIPPET = `const BASE = "https://glas-mcp.onrender.com/api/v1";

async function callTool(name, args) {
  const res = await fetch(\`\${BASE}/tools/\${name}\`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ arguments: args }),
  });
  const { ok, result, error } = await res.json();
  if (!ok) throw new Error(error.message);
  return result;
}

// Web search
const results = await callTool("web_search", {
  query: "Model Context Protocol", num_results: 5
});

// Generate a chart
const chart = await callTool("plot_chart", {
  chart_type: "bar",
  data: { categories: ["Q1","Q2","Q3"], values: [[100,145,130]] },
  title: "Quarterly Revenue",
});`

const CLAUDE_SNIPPET = `{
  "mcpServers": {
    "glas": {
      "url": "https://glas-mcp.onrender.com/sse"
    }
  }
}`

export default function Home() {
  const [activeTab, setActiveTab] = useState('js')
  const [serverStatus, setServerStatus] = useState(null)

  useEffect(() => {
    fetch('https://glas-mcp.onrender.com/health')
      .then(r => r.json())
      .then(() => setServerStatus('online'))
      .catch(() => setServerStatus('offline'))
  }, [])

  return (
    <div>
      {/* Hero */}
      <section style={{ padding: '80px 0 60px', position: 'relative', overflow: 'hidden' }}>
        {/* Background glow */}
        <div style={{
          position: 'absolute', top: -100, left: '50%', transform: 'translateX(-50%)',
          width: 800, height: 400, borderRadius: '50%',
          background: 'radial-gradient(ellipse, rgba(91,110,245,.12) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />

        <div className="container-sm" style={{ textAlign: 'center', position: 'relative' }}>
          {/* Status */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginBottom: 24 }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 7,
              background: 'var(--bg2)', border: '1px solid var(--border)',
              borderRadius: 20, padding: '5px 12px', fontSize: 12, color: 'var(--text2)',
            }}>
              <div style={{
                width: 6, height: 6, borderRadius: '50%',
                background: serverStatus === 'online' ? 'var(--green)' : serverStatus === 'offline' ? 'var(--red)' : 'var(--text3)',
                boxShadow: serverStatus === 'online' ? '0 0 6px var(--green)' : 'none',
              }} />
              {serverStatus === 'online' ? 'Server online' : serverStatus === 'offline' ? 'Server offline' : 'Checking status…'}
            </div>
            <a href="https://github.com/anguzudouglas/glas-mcp" target="_blank" rel="noreferrer"
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 20, padding: '5px 12px', fontSize: 12, color: 'var(--text2)' }}>
              ⭐ Star on GitHub
            </a>
          </div>

          <h1 className="fade-up" style={{ fontSize: 'clamp(36px, 6vw, 64px)', fontWeight: 800, lineHeight: 1.1, letterSpacing: '-.03em', marginBottom: 20 }}>
            Give your AI agent<br />
            <span className="grad-text">superpowers.</span>
          </h1>

          <p className="fade-up-2" style={{ fontSize: 17, color: 'var(--text2)', lineHeight: 1.7, maxWidth: 520, margin: '0 auto 36px' }}>
            Glas MCP is a modular Model Context Protocol server exposing 8 production-ready tools over SSE and REST. Plug into any MCP client in 30 seconds.
          </p>

          <div className="fade-up-3" style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/playground" className="btn btn-primary btn-lg">
              ▶ Try Playground
            </Link>
            <Link to="/docs" className="btn btn-secondary btn-lg">
              Read the Docs
            </Link>
            <a href="https://github.com/anguzudouglas/glas-mcp" target="_blank" rel="noreferrer" className="btn btn-ghost btn-lg">
              GitHub ↗
            </a>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section style={{ borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)', padding: '0' }}>
        <div className="container">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)' }}>
            {STATS.map((s, i) => (
              <div key={i} style={{
                padding: '24px 0', textAlign: 'center',
                borderRight: i < 3 ? '1px solid var(--border)' : 'none',
              }}>
                <div style={{ fontSize: 28, fontWeight: 800, letterSpacing: '-.02em', marginBottom: 4 }}
                  className="grad-text">{s.value}</div>
                <div style={{ fontSize: 12, color: 'var(--text2)', fontWeight: 500 }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tools grid */}
      <section style={{ padding: '72px 0' }}>
        <div className="container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 36 }}>
            <div>
              <p style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.1em', color: 'var(--primary)', marginBottom: 8 }}>Tools</p>
              <h2 style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-.02em' }}>8 tools. Zero configuration.</h2>
              <p style={{ color: 'var(--text2)', marginTop: 6, fontSize: 14 }}>Every tool is auto-discovered, self-describing, and callable over MCP or REST.</p>
            </div>
            <Link to="/tools" className="btn btn-secondary btn-sm">View all tools →</Link>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            {TOOLS_PREVIEW.map((t) => {
              const c = CAT_COLORS[t.cat]
              return (
                <div key={t.name} className="card" style={{ padding: '16px 18px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                    <code style={{ fontSize: 12, color: 'var(--teal)', fontWeight: 600 }}>{t.name}</code>
                    <span style={{ fontSize: 10, padding: '2px 7px', borderRadius: 4, fontWeight: 600, background: c.bg, color: c.color, border: `1px solid ${c.border}` }}>{t.cat}</span>
                  </div>
                  <p style={{ fontSize: 12, color: 'var(--text2)', lineHeight: 1.5 }}>{t.desc}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Quick Start */}
      <section style={{ padding: '0 0 72px' }}>
        <div className="container">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 40, alignItems: 'start' }}>
            {/* Code */}
            <div>
              <p style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.1em', color: 'var(--primary)', marginBottom: 8 }}>Quick Start</p>
              <h2 style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-.02em', marginBottom: 12 }}>Plug & play from anywhere.</h2>
              <p style={{ color: 'var(--text2)', lineHeight: 1.7, marginBottom: 24, fontSize: 14 }}>Call any tool over REST in a single fetch. Or connect via MCP for native agent integration.</p>

              <div style={{ display: 'flex', gap: 4, marginBottom: 0 }}>
                {[['js', 'JavaScript'], ['claude', 'Claude Desktop'], ['curl', 'curl']].map(([id, label]) => (
                  <button key={id} onClick={() => setActiveTab(id)} style={{
                    padding: '7px 14px', borderRadius: '6px 6px 0 0', fontSize: 12, fontWeight: 600,
                    background: activeTab === id ? 'var(--code-bg)' : 'var(--bg2)',
                    color: activeTab === id ? 'var(--text)' : 'var(--text2)',
                    border: activeTab === id ? '1px solid var(--border)' : '1px solid transparent',
                    borderBottom: activeTab === id ? '1px solid var(--code-bg)' : '1px solid var(--border)',
                    marginBottom: -1, cursor: 'pointer',
                  }}>{label}</button>
                ))}
              </div>

              <div className="code-block" style={{ borderRadius: '0 6px 6px 6px' }}>
                <pre style={{ fontSize: 12 }}>
                  {activeTab === 'js' && JS_SNIPPET}
                  {activeTab === 'claude' && CLAUDE_SNIPPET}
                  {activeTab === 'curl' && `curl -X POST https://glas-mcp.onrender.com/api/v1/tools/web_search \\
  -H "Content-Type: application/json" \\
  -d '{"arguments": {"query": "MCP tools", "num_results": 5}}'`}
                </pre>
              </div>
            </div>

            {/* Features list */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <p style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.1em', color: 'var(--primary)', marginBottom: 4 }}>Features</p>
              {FEATURES.map((f, i) => (
                <div key={i} style={{ display: 'flex', gap: 14, padding: '14px 16px', background: 'var(--bg2)', borderRadius: 8, border: '1px solid var(--border)' }}>
                  <div style={{ fontSize: 20, flexShrink: 0, marginTop: 1 }}>{f.icon}</div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                      <p style={{ fontSize: 13, fontWeight: 700 }}>{f.title}</p>
                      <span className="badge badge-gray" style={{ fontSize: 10 }}>{f.badge}</span>
                    </div>
                    <p style={{ fontSize: 12, color: 'var(--text2)', lineHeight: 1.6 }}>{f.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: '60px 0', borderTop: '1px solid var(--border)' }}>
        <div className="container" style={{ textAlign: 'center' }}>
          <div style={{
            background: 'linear-gradient(135deg, rgba(91,110,245,.08), rgba(124,92,240,.08))',
            border: '1px solid rgba(91,110,245,.2)',
            borderRadius: 16, padding: '48px 40px',
          }}>
            <h2 style={{ fontSize: 28, fontWeight: 700, marginBottom: 10 }}>Ready to start building?</h2>
            <p style={{ color: 'var(--text2)', marginBottom: 28, fontSize: 14 }}>Open the playground and start using all 8 tools in under a minute.</p>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
              <Link to="/playground" className="btn btn-primary btn-lg">Open Playground →</Link>
              <Link to="/docs" className="btn btn-secondary btn-lg">Read Docs</Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
