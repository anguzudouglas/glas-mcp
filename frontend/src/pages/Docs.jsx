import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

const SECTIONS = [
  { id:'overview',    label:'Overview' },
  { id:'quickstart',  label:'Quick Start' },
  { id:'architecture',label:'Architecture' },
  { id:'tools',       label:'Using Tools' },
  { id:'providers',   label:'Providers' },
  { id:'mcp',         label:'MCP Integration' },
  { id:'adding-tools',label:'Adding Tools' },
  { id:'skills',      label:'Skills System' },
  { id:'deploy',      label:'Deployment' },
  { id:'env',         label:'Environment' },
  { id:'faq',         label:'FAQ' },
]

function Section({ id, title, children }) {
  return (
    <section id={id} style={{ marginBottom:56, scrollMarginTop:80 }}>
      <h2 style={{ fontSize:22, fontWeight:700, letterSpacing:'-.01em', marginBottom:16, paddingBottom:10, borderBottom:'1px solid var(--border)' }}>{title}</h2>
      {children}
    </section>
  )
}

function Code({ children, lang='bash' }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(children.trim())
    setCopied(true); setTimeout(() => setCopied(false), 1500)
  }
  return (
    <div style={{ position:'relative', marginBottom:16 }}>
      <div style={{ background:'var(--code)', border:'1px solid var(--border)', borderRadius:8, padding:'16px 20px', overflowX:'auto' }}>
        <pre style={{ fontFamily:'JetBrains Mono, monospace', fontSize:12.5, color:'#a8b8d8', lineHeight:1.7, margin:0 }}>{children.trim()}</pre>
      </div>
      <button onClick={copy} style={{
        position:'absolute', top:10, right:10, background:'var(--bg3)', border:'1px solid var(--border)',
        borderRadius:5, padding:'3px 9px', fontSize:11, color:'var(--text2)', cursor:'pointer',
      }}>{copied ? '✓ Copied' : 'Copy'}</button>
    </div>
  )
}

function Note({ type='info', children }) {
  const styles = {
    info:    { bg:'rgba(91,110,245,.08)',  border:'rgba(91,110,245,.25)', color:'var(--primary)', icon:'ℹ' },
    warning: { bg:'rgba(245,166,35,.08)', border:'rgba(245,166,35,.25)', color:'var(--yellow)',  icon:'⚠' },
    tip:     { bg:'rgba(16,217,160,.08)', border:'rgba(16,217,160,.25)', color:'var(--green)',   icon:'✦' },
  }
  const s = styles[type]
  return (
    <div style={{ background:s.bg, border:`1px solid ${s.border}`, borderRadius:8, padding:'12px 16px', marginBottom:16, display:'flex', gap:10, fontSize:13, lineHeight:1.6 }}>
      <span style={{ color:s.color, flexShrink:0 }}>{s.icon}</span>
      <div style={{ color:'var(--text2)' }}>{children}</div>
    </div>
  )
}

function H3({ children }) {
  return <h3 style={{ fontSize:16, fontWeight:700, marginBottom:8, marginTop:20, color:'var(--text)' }}>{children}</h3>
}

function P({ children, style }) {
  return <p style={{ color:'var(--text2)', lineHeight:1.75, marginBottom:12, fontSize:14, ...style }}>{children}</p>
}

function InlineCode({ children }) {
  return <code style={{ fontFamily:'monospace', fontSize:12, background:'var(--bg3)', border:'1px solid var(--border)', borderRadius:4, padding:'1px 6px', color:'var(--teal)' }}>{children}</code>
}

export default function Docs() {
  const [active, setActive] = useState('overview')

  useEffect(() => {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) setActive(e.target.id) })
    }, { rootMargin:'-20% 0px -70% 0px' })
    SECTIONS.forEach(s => {
      const el = document.getElementById(s.id)
      if (el) observer.observe(el)
    })
    return () => observer.disconnect()
  }, [])

  return (
    <div style={{ display:'flex', minHeight:'calc(100vh - 60px)' }}>
      {/* TOC sidebar */}
      <aside style={{
        width:220, flexShrink:0, borderRight:'1px solid var(--border)',
        position:'sticky', top:60, height:'calc(100vh - 60px)',
        overflowY:'auto', padding:'24px 0', background:'var(--bg1)',
      }}>
        <p style={{ fontSize:10, fontWeight:700, textTransform:'uppercase', letterSpacing:'.1em', color:'var(--text3)', padding:'0 16px', marginBottom:12 }}>On this page</p>
        {SECTIONS.map(s => (
          <a key={s.id} href={`#${s.id}`} onClick={() => setActive(s.id)} style={{
            display:'block', padding:'6px 16px', fontSize:13,
            color: active===s.id ? 'var(--primary)' : 'var(--text2)',
            background: active===s.id ? 'var(--primary-dim)' : 'transparent',
            borderRight: active===s.id ? '2px solid var(--primary)' : '2px solid transparent',
            transition:'all .15s',
          }}
            onMouseEnter={e => { if(active!==s.id) e.currentTarget.style.color='var(--text)' }}
            onMouseLeave={e => { if(active!==s.id) e.currentTarget.style.color='var(--text2)' }}
          >{s.label}</a>
        ))}

        <div style={{ margin:'20px 16px 0', padding:'14px', background:'var(--bg2)', border:'1px solid var(--border)', borderRadius:8 }}>
          <p style={{ fontSize:11, fontWeight:700, color:'var(--text2)', marginBottom:8 }}>Resources</p>
          <a href="https://github.com/anguzudouglas/glas-mcp" target="_blank" rel="noreferrer" style={{ display:'block', fontSize:12, color:'var(--text2)', marginBottom:5 }}>GitHub ↗</a>
          <Link to="/api" style={{ display:'block', fontSize:12, color:'var(--text2)', marginBottom:5 }}>API Reference</Link>
          <a href="https://glas-mcp.onrender.com/api/docs" target="_blank" rel="noreferrer" style={{ display:'block', fontSize:12, color:'var(--text2)' }}>Swagger UI ↗</a>
        </div>
      </aside>

      {/* Content */}
      <div style={{ flex:1, overflowY:'auto', padding:'40px 48px 80px', maxWidth:860 }}>

        <Section id="overview" title="Overview">
          <P>Glas MCP is a modular <strong style={{ color:'var(--text)' }}>Model Context Protocol</strong> server that exposes 8 production-ready tools over both SSE (for AI agents) and REST (for your own apps). Drop a folder with <InlineCode>main.py</InlineCode> and <InlineCode>tool.yaml</InlineCode> and it auto-registers on next restart.</P>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:12, marginTop:16 }}>
            {[['8 Tools','web_search, web_fetch, math, charts, docx, xlsx, pptx, pdf'],['Dual Transport','MCP over SSE for agents, REST JSON for apps'],['Auto-Discovery','Add a folder → tool is live. No wiring needed.']].map(([t,d]) => (
              <div key={t} style={{ background:'var(--bg2)', border:'1px solid var(--border)', borderRadius:8, padding:'14px 16px' }}>
                <p style={{ fontSize:13, fontWeight:700, marginBottom:4 }}>{t}</p>
                <p style={{ fontSize:12, color:'var(--text2)', lineHeight:1.5 }}>{d}</p>
              </div>
            ))}
          </div>
        </Section>

        <Section id="quickstart" title="Quick Start">
          <H3>1. Clone and run locally</H3>
          <Code>{`git clone https://github.com/anguzudouglas/glas-mcp
cd glas-mcp
pip install -r glas_mcp/requirements.txt
python main.py`}</Code>
          <P>The server starts on <InlineCode>http://localhost:8000</InlineCode>. The playground is at <InlineCode>/</InlineCode> and the API is at <InlineCode>/api/v1</InlineCode>.</P>

          <H3>2. Call a tool via REST</H3>
          <Code>{`curl -X POST http://localhost:8000/api/v1/tools/web_search \\
  -H "Content-Type: application/json" \\
  -d '{"arguments": {"query": "Model Context Protocol", "num_results": 5}}'`}</Code>

          <H3>3. Connect Claude Desktop via MCP</H3>
          <Code lang="json">{`// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "glas": {
      "url": "https://glas-mcp.onrender.com/sse"
    }
  }
}`}</Code>
          <Note type="tip">The hosted server at <strong>glas-mcp.onrender.com</strong> is always available — no setup needed for MCP clients.</Note>

          <H3>4. Dev mode (backend + frontend)</H3>
          <Code>{`DEV=true python main.py
# Backend: http://localhost:8000
# Frontend: http://localhost:5173  (Vite with HMR)`}</Code>
        </Section>

        <Section id="architecture" title="Architecture">
          <P>Glas MCP is a single FastAPI application. On startup it scans three directories and auto-loads their contents:</P>
          <Code>{`glas_mcp/
├── main.py              FastAPI app + MCP SSE + frontend serving
├── engine/
│   ├── tools_loader.py     Scans tools/ and loads BaseTool instances
│   └── providers_loader.py Scans providers/ and loads provider.yaml configs
├── factory/
│   └── tool_factory.py     Dynamically imports tool modules
├── tools/               8 built-in tools (auto-discovered)
│   ├── web_search/
│   │   ├── main.py      Tool implementation
│   │   └── tool.yaml    Schema declaration
│   └── …
├── providers/           AI provider configs (auto-discovered)
│   ├── Anthropic/provider.yaml
│   ├── Google/provider.yaml
│   ├── Groq/provider.yaml
│   └── OpenRouter/provider.yaml
├── skills/              Agent guidance markdowns
└── static/              Built React frontend (served as SPA)`}</Code>

          <H3>Request flow</H3>
          <P>MCP client → <InlineCode>GET /sse</InlineCode> (SSE handshake) → <InlineCode>POST /messages</InlineCode> (tool calls) → <InlineCode>ToolsLoader</InlineCode> → tool <InlineCode>execute()</InlineCode></P>
          <P>REST client → <InlineCode>POST /api/v1/tools/{'{name}'}</InlineCode> → <InlineCode>ToolFactory</InlineCode> → tool <InlineCode>execute()</InlineCode> → GURS response</P>
        </Section>

        <Section id="tools" title="Using Tools">
          <H3>REST API</H3>
          <P>All tools are callable via <InlineCode>POST /api/v1/tools/{'{name}'}</InlineCode> with a JSON body:</P>
          <Code>{`{
  "arguments": {
    "param1": "value1",
    "param2": 42
  }
}`}</Code>
          <P>Every response follows the <strong style={{color:'var(--text)'}}>Glas Unified Response Schema (GURS)</strong>:</P>
          <Code lang="json">{`{
  "ok":     true,
  "tool":   "web_search",
  "result": { … },
  "error":  null,
  "meta": {
    "execution_time_ms": 312,
    "timestamp": "2025-01-01T00:00:00Z",
    "request_id": "abc-123",
    "version": "1.0.0"
  }
}`}</Code>

          <H3>JavaScript example</H3>
          <Code lang="js">{`const BASE = "https://glas-mcp.onrender.com/api/v1";

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
const results = await callTool("web_search", { query: "AI news", num_results: 10 });

// Generate a chart → returns { image_base64: "..." }
const chart = await callTool("plot_chart", {
  chart_type: "bar",
  data: { categories: ["Q1","Q2","Q3"], values: [[100, 145, 130]], labels: ["Revenue"] },
  title: "Quarterly Revenue",
  colors: ["#5B6EF5"],
});
document.querySelector("img").src = \`data:image/png;base64,\${chart.image_base64}\`;`}</Code>
        </Section>

        <Section id="providers" title="Providers">
          <P>Providers are auto-discovered from <InlineCode>glas_mcp/providers/</InlineCode>. Each folder contains a <InlineCode>provider.yaml</InlineCode> that declares the API config, models, and auth strategy.</P>

          <H3>Supported providers</H3>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(2,1fr)', gap:12, marginBottom:16 }}>
            {[
              { name:'Anthropic', logo:'◆', color:'#CC785C', note:'Full tool use support (Claude models)' },
              { name:'Google Gemini', logo:'✦', color:'#4285F4', note:'Gemini 2.0 Flash and Pro' },
              { name:'Groq', logo:'▲', color:'#F97316', note:'Ultra-fast Llama and Mixtral' },
              { name:'OpenRouter', logo:'◉', color:'#7C3AED', note:'50+ models via one API key' },
            ].map(p => (
              <div key={p.name} style={{ background:'var(--bg2)', border:'1px solid var(--border)', borderRadius:8, padding:'14px 16px', display:'flex', gap:10 }}>
                <span style={{ color:p.color, fontSize:18, flexShrink:0 }}>{p.logo}</span>
                <div>
                  <p style={{ fontSize:13, fontWeight:700, marginBottom:3 }}>{p.name}</p>
                  <p style={{ fontSize:12, color:'var(--text2)' }}>{p.note}</p>
                </div>
              </div>
            ))}
          </div>

          <H3>Provider YAML schema</H3>
          <Code lang="yaml">{`name: anthropic                   # Unique identifier
display_name: Anthropic           # UI label
logo: "◆"                        # Single char icon
color: "#CC785C"                  # Brand color (hex)
api_base_url: https://api.anthropic.com/v1/messages
auth_type: header                 # header | bearer | query_param
auth_header: x-api-key
extra_headers:
  anthropic-version: "2023-06-01"
supports_tool_use: true           # Enable tool calls for this provider
request_format: anthropic         # anthropic | openai | gemini
response_format: anthropic
models:
  - id: claude-sonnet-4-6
    label: Claude Sonnet 4.6
    context_window: 200000
    default: true
default_model: claude-sonnet-4-6`}</Code>

          <H3>Adding a new provider</H3>
          <Code>{`mkdir glas_mcp/providers/MyProvider
# Create provider.yaml with the schema above
# Restart the server — provider auto-loads and appears in /api/v1/providers`}</Code>
          <Note type="tip">Provider configs are served at <InlineCode>GET /api/v1/providers</InlineCode> so the frontend loads them dynamically — no frontend rebuild needed.</Note>
        </Section>

        <Section id="mcp" title="MCP Integration">
          <H3>Claude Desktop</H3>
          <Code lang="json">{`// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "glas": { "url": "https://glas-mcp.onrender.com/sse" }
  }
}`}</Code>

          <H3>Any MCP client (SSE transport)</H3>
          <Code>{`SSE endpoint:  GET  https://glas-mcp.onrender.com/sse
Messages:      POST https://glas-mcp.onrender.com/messages`}</Code>

          <H3>Tool discovery</H3>
          <P>Connected MCP clients see all 8 tools automatically via the <InlineCode>list_tools</InlineCode> handler. No configuration required.</P>
        </Section>

        <Section id="adding-tools" title="Adding Tools">
          <P>Create a new subdirectory in <InlineCode>glas_mcp/tools/</InlineCode> with two files:</P>

          <H3>tool.yaml — schema declaration</H3>
          <Code lang="yaml">{`name: my_tool
description: What this tool does.
input_schema:
  type: object
  properties:
    query:
      type: string
      description: The input text.
    limit:
      type: integer
      description: Max results.
      default: 10
  required:
    - query`}</Code>

          <H3>main.py — implementation</H3>
          <Code lang="python">{`from glas_mcp.tools.base import BaseTool

class MyTool(BaseTool):
    async def execute(self, arguments: dict) -> dict:
        query = arguments["query"]
        limit = arguments.get("limit", 10)

        # Your logic here
        result = {"query": query, "limit": limit, "data": []}

        return result   # Must be JSON-serialisable`}</Code>

          <P>Restart the server — <InlineCode>ToolsLoader</InlineCode> scans the directory and <InlineCode>ToolFactory</InlineCode> dynamically imports your class. The tool is immediately available over both MCP and REST.</P>
          <Note type="warning">The class must inherit from <InlineCode>BaseTool</InlineCode> and implement <InlineCode>async execute(self, arguments: dict) → dict</InlineCode>.</Note>
        </Section>

        <Section id="skills" title="Skills System">
          <P>Skills are markdown guides that tell the agent <em>how</em> to use each tool effectively. They live in <InlineCode>glas_mcp/skills/</InlineCode> and are served via <InlineCode>GET /api/v1/skills/{'{name}'}</InlineCode>.</P>

          <H3>skill.yaml</H3>
          <Code lang="yaml">{`name: web_search_skill
tool: web_search
version: "1.0.0"
description: Guide for high-quality DuckDuckGo searches
tags: [search, web, research]`}</Code>

          <H3>skill.md</H3>
          <P>The <InlineCode>skill.md</InlineCode> file contains free-form guidance: example queries, anti-patterns, data-handling rules. The playground injects active skills into the agent system prompt automatically.</P>
        </Section>

        <Section id="deploy" title="Deployment">
          <H3>Render (recommended)</H3>
          <P>The repo includes a <InlineCode>render.yaml</InlineCode> for one-click deploy. Connect the GitHub repo in Render and it auto-deploys on every push.</P>

          <H3>Docker</H3>
          <Code>{`# Build
docker build -t glas-mcp .

# Run
docker run -p 8000:8000 glas-mcp

# With environment variables
docker run -p 8000:8000 --env-file .env glas-mcp

# Docker Compose
docker-compose up`}</Code>

          <H3>Building the frontend for production</H3>
          <Code>{`cd frontend
npm install
npm run build
# Output → glas_mcp/static/   (served by FastAPI)

# Or let main.py build it automatically:
python main.py  # builds if glas_mcp/static/ is empty`}</Code>
        </Section>

        <Section id="env" title="Environment Variables">
          <div style={{ background:'var(--code)', border:'1px solid var(--border)', borderRadius:8, overflow:'hidden' }}>
            <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
              <thead>
                <tr style={{ borderBottom:'1px solid var(--border)' }}>
                  {['Variable','Default','Description'].map(h => (
                    <th key={h} style={{ padding:'10px 16px', textAlign:'left', fontSize:11, fontWeight:700, textTransform:'uppercase', letterSpacing:'.06em', color:'var(--text3)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  ['PORT','8000','Server listen port'],
                  ['HOST','0.0.0.0','Bind address'],
                  ['DEV','false','Enable dev mode + Vite'],
                  ['VITE_PORT','5173','Vite dev server port'],
                  ['ANTHROPIC_API_KEY','—','Anthropic API key (optional, for server-side use)'],
                  ['GOOGLE_API_KEY','—','Google Gemini API key'],
                  ['GROQ_API_KEY','—','Groq API key'],
                  ['OPENROUTER_API_KEY','—','OpenRouter API key'],
                ].map(([k,d,desc],i) => (
                  <tr key={k} style={{ borderBottom:'1px solid var(--border)', background: i%2 ? 'rgba(255,255,255,.01)' : 'transparent' }}>
                    <td style={{ padding:'10px 16px', fontFamily:'monospace', fontSize:12, color:'var(--teal)' }}>{k}</td>
                    <td style={{ padding:'10px 16px', fontFamily:'monospace', fontSize:12, color:'var(--text3)' }}>{d}</td>
                    <td style={{ padding:'10px 16px', color:'var(--text2)', fontSize:13 }}>{desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        <Section id="faq" title="FAQ">
          {[
            ['Do I need Node.js to run Glas MCP?', 'Only if you want to run the Vite dev server (DEV=true). In production, the React app is pre-built to glas_mcp/static/ during the Docker build — no Node at runtime.'],
            ['Can I use Glas MCP without Docker?', 'Yes. pip install -r glas_mcp/requirements.txt then python main.py. Docker is optional.'],
            ['Tool use only works with Anthropic?', 'Tool calling in the playground requires Anthropic (Claude) since other providers don\'t support structured tool calls natively. All providers can chat normally.'],
            ['How do I add Google Workspace tools?', 'Set up OAuth credentials and drop them in .env. The oauth_handlers/ module handles the OAuth flow for Drive, Docs, Sheets, and Slides.'],
            ['Is the API rate-limited?', 'The hosted server on Render\'s free tier has no rate limit enforced by Glas, but Render\'s free tier may sleep after inactivity. Self-host for production loads.'],
          ].map(([q, a]) => (
            <div key={q} style={{ marginBottom:16, background:'var(--bg2)', border:'1px solid var(--border)', borderRadius:8, padding:'16px 18px' }}>
              <p style={{ fontWeight:700, fontSize:14, marginBottom:6 }}>{q}</p>
              <p style={{ fontSize:13, color:'var(--text2)', lineHeight:1.65 }}>{a}</p>
            </div>
          ))}
        </Section>

      </div>
    </div>
  )
}
