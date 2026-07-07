import { useState, useEffect } from 'react'

const GLAS_BASE = 'https://glas-mcp.onrender.com/api/v1'

const ENDPOINTS = [
  {
    group: 'Core',
    items: [
      { method:'GET',  path:'/health',      desc:'Server health probe. Returns tool count and MCP status.',
        response:`{ "status": "ok", "tools_loaded": 8, "providers_loaded": 4, "mcp_sse": true }` },
      { method:'GET',  path:'/api/v1',       desc:'API root — lists all available endpoints.',
        response:`{ "name": "Glas MCP REST API", "version": "1.0.0", "endpoints": [...] }` },
    ]
  },
  {
    group: 'Tools',
    items: [
      { method:'GET',  path:'/api/v1/tools', desc:'List all auto-discovered tools with their schemas.',
        response:`[{ "name": "web_search", "description": "...", "input_schema": { ... } }, ...]` },
      { method:'GET',  path:'/api/v1/tools/{name}', desc:'Get schema for a specific tool.',
        response:`{ "ok": true, "tool": { "name": "web_search", "input_schema": { ... } } }` },
      { method:'POST', path:'/api/v1/tools/{name}', desc:'Execute a tool. Body: { "arguments": { ... } }. Returns GURS.',
        response:`{ "ok": true, "tool": "web_search", "result": { ... }, "error": null, "meta": { ... } }`,
        body:`{ "arguments": { "query": "AI news", "num_results": 5 } }` },
    ]
  },
  {
    group: 'Providers',
    items: [
      { method:'GET',  path:'/api/v1/providers', desc:'List all AI provider configs loaded from providers/ directory.',
        response:`{ "ok": true, "providers": [{ "name": "anthropic", "display_name": "Anthropic", "models": [...] }], "count": 4 }` },
      { method:'GET',  path:'/api/v1/providers/{name}', desc:'Get a specific provider\'s full config.',
        response:`{ "ok": true, "provider": { "name": "anthropic", "api_base_url": "...", "models": [...] } }` },
    ]
  },
  {
    group: 'Skills',
    items: [
      { method:'GET',  path:'/api/v1/skills', desc:'List all skills with metadata.',
        response:`[{ "name": "web_search_skill", "tool": "web_search", "description": "...", "tags": [...] }]` },
      { method:'GET',  path:'/api/v1/skills/{name}', desc:'Get a skill\'s full markdown content.',
        response:`{ "name": "web_search_skill", "content_md": "# Web Search Skill\\n..." }` },
      { method:'POST', path:'/api/v1/skills', desc:'Create a new skill.',
        body:`{ "name": "my_skill", "tool": "web_search", "description": "...", "content_md": "# Guide\\n..." }` },
      { method:'PUT',  path:'/api/v1/skills/{name}', desc:'Update an existing skill.',
        body:`{ "description": "Updated description", "content_md": "# Updated\\n..." }` },
      { method:'DELETE',path:'/api/v1/skills/{name}', desc:'Delete a skill.' },
    ]
  },
  {
    group: 'MCP',
    items: [
      { method:'GET',  path:'/sse',      desc:'MCP Server-Sent Events transport. AI clients (Claude Desktop) connect here.' },
      { method:'POST', path:'/messages', desc:'MCP client → server messages endpoint.' },
    ]
  },
]

const METHOD_COLORS = {
  GET:    { bg:'rgba(16,217,160,.1)',  color:'#10D9A0', border:'rgba(16,217,160,.2)'  },
  POST:   { bg:'rgba(91,110,245,.1)', color:'#5B6EF5', border:'rgba(91,110,245,.2)'  },
  PUT:    { bg:'rgba(245,166,35,.1)', color:'#F5A623', border:'rgba(245,166,35,.2)'  },
  DELETE: { bg:'rgba(240,71,71,.1)',  color:'#F04747', border:'rgba(240,71,71,.2)'   },
}

function MethodBadge({ method }) {
  const s = METHOD_COLORS[method] ?? METHOD_COLORS.GET
  return (
    <span style={{ padding:'3px 8px', borderRadius:5, fontSize:10, fontWeight:700, fontFamily:'monospace', background:s.bg, color:s.color, border:`1px solid ${s.border}`, flexShrink:0, letterSpacing:'.04em' }}>
      {method}
    </span>
  )
}

function EndpointRow({ ep }) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)

  const curlExample = ep.body
    ? `curl -X ${ep.method} https://glas-mcp.onrender.com${ep.path} \\\n  -H "Content-Type: application/json" \\\n  -d '${ep.body}'`
    : `curl https://glas-mcp.onrender.com${ep.path}`

  const copy = () => { navigator.clipboard.writeText(curlExample); setCopied(true); setTimeout(() => setCopied(false), 1500) }

  return (
    <div style={{ border:'1px solid var(--border)', borderRadius:8, overflow:'hidden', marginBottom:8 }}>
      <div onClick={() => setOpen(o => !o)} style={{
        display:'flex', alignItems:'center', gap:12, padding:'12px 16px', cursor:'pointer',
        background: open ? 'var(--bg3)' : 'var(--bg2)', transition:'background .15s',
      }}>
        <MethodBadge method={ep.method} />
        <code style={{ fontSize:13, color:'var(--teal)', flex:1, fontFamily:'JetBrains Mono, monospace' }}>{ep.path}</code>
        <span style={{ fontSize:12, color:'var(--text2)', marginRight:8 }}>{ep.desc}</span>
        <span style={{ color:'var(--text3)', fontSize:11 }}>{open ? '▲' : '▼'}</span>
      </div>
      {open && (
        <div style={{ borderTop:'1px solid var(--border)', padding:'16px', background:'var(--bg1)' }}>
          {ep.body && (
            <div style={{ marginBottom:12 }}>
              <p style={{ fontSize:11, fontWeight:700, textTransform:'uppercase', letterSpacing:'.08em', color:'var(--text3)', marginBottom:6 }}>Request Body</p>
              <div style={{ background:'var(--code)', border:'1px solid var(--border)', borderRadius:6, padding:'12px 14px', fontFamily:'monospace', fontSize:12, color:'#a8b8d8', lineHeight:1.6 }}>
                {ep.body}
              </div>
            </div>
          )}
          {ep.response && (
            <div style={{ marginBottom:12 }}>
              <p style={{ fontSize:11, fontWeight:700, textTransform:'uppercase', letterSpacing:'.08em', color:'var(--text3)', marginBottom:6 }}>Response</p>
              <div style={{ background:'var(--code)', border:'1px solid var(--border)', borderRadius:6, padding:'12px 14px', fontFamily:'monospace', fontSize:12, color:'#a8b8d8', lineHeight:1.6 }}>
                {ep.response}
              </div>
            </div>
          )}
          <div style={{ position:'relative' }}>
            <p style={{ fontSize:11, fontWeight:700, textTransform:'uppercase', letterSpacing:'.08em', color:'var(--text3)', marginBottom:6 }}>Example</p>
            <div style={{ background:'var(--code)', border:'1px solid var(--border)', borderRadius:6, padding:'12px 14px', fontFamily:'monospace', fontSize:12, color:'#a8b8d8', lineHeight:1.6, whiteSpace:'pre' }}>
              {curlExample}
            </div>
            <button onClick={copy} style={{ position:'absolute', bottom:10, right:10, background:'var(--bg3)', border:'1px solid var(--border)', borderRadius:5, padding:'3px 9px', fontSize:11, color:'var(--text2)', cursor:'pointer' }}>
              {copied ? '✓' : 'Copy'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function ApiRef() {
  const [health, setHealth] = useState(null)
  const [toolCount, setToolCount] = useState(null)

  useEffect(() => {
    fetch('https://glas-mcp.onrender.com/health')
      .then(r => r.json())
      .then(d => { setHealth('online'); setToolCount(d.tools_loaded) })
      .catch(() => setHealth('offline'))
  }, [])

  return (
    <div>
      {/* Header */}
      <div style={{ borderBottom:'1px solid var(--border)', padding:'48px 0 32px', background:'linear-gradient(to bottom, var(--bg1), var(--bg0))' }}>
        <div className="container">
          <p style={{ fontSize:11, fontWeight:700, textTransform:'uppercase', letterSpacing:'.1em', color:'var(--primary)', marginBottom:8 }}>API Reference</p>
          <h1 style={{ fontSize:36, fontWeight:800, letterSpacing:'-.02em', marginBottom:8 }}>Plug & play from anywhere.</h1>
          <p style={{ color:'var(--text2)', fontSize:15, maxWidth:560, marginBottom:20 }}>All endpoints return the Glas Unified Response Schema (GURS). Base URL is the production server or your local instance.</p>

          <div style={{ display:'flex', gap:10, flexWrap:'wrap' }}>
            <div style={{ background:'var(--bg2)', border:'1px solid var(--border)', borderRadius:8, padding:'10px 16px', fontFamily:'monospace', fontSize:13 }}>
              <span style={{ color:'var(--text3)' }}>Base URL: </span>
              <span style={{ color:'var(--teal)' }}>https://glas-mcp.onrender.com</span>
            </div>
            <div style={{ display:'flex', alignItems:'center', gap:7, background:'var(--bg2)', border:'1px solid var(--border)', borderRadius:8, padding:'10px 16px', fontSize:13 }}>
              <div style={{ width:7, height:7, borderRadius:'50%', background: health==='online' ? 'var(--green)' : 'var(--text3)', boxShadow: health==='online' ? '0 0 6px var(--green)' : 'none' }} />
              <span style={{ color:'var(--text2)' }}>{health==='online' ? `Online · ${toolCount ?? '…'} tools` : health==='offline' ? 'Offline' : 'Checking…'}</span>
            </div>
            <a href="https://glas-mcp.onrender.com/api/docs" target="_blank" rel="noreferrer"
              style={{ display:'flex', alignItems:'center', gap:6, background:'var(--primary-dim)', border:'1px solid rgba(91,110,245,.25)', borderRadius:8, padding:'10px 16px', fontSize:13, color:'var(--primary)', fontWeight:600 }}>
              Swagger UI ↗
            </a>
          </div>
        </div>
      </div>

      {/* GURS schema */}
      <div className="container" style={{ padding:'32px 24px 0' }}>
        <div style={{ background:'var(--bg2)', border:'1px solid var(--border)', borderRadius:10, padding:'20px 24px', marginBottom:32 }}>
          <p style={{ fontSize:13, fontWeight:700, marginBottom:10 }}>Response Schema (GURS)</p>
          <div style={{ background:'var(--code)', borderRadius:6, padding:'14px 16px', fontFamily:'monospace', fontSize:12, color:'#a8b8d8', lineHeight:1.7 }}>
{`{
  "ok":     true | false,
  "tool":   "tool_name" | null,
  "result": { … } | null,
  "error":  { "code": str, "message": str, "details": any } | null,
  "meta": {
    "execution_time_ms": 312,
    "timestamp": "2025-01-01T00:00:00Z",
    "request_id": "uuid",
    "version": "1.0.0"
  }
}`}
          </div>
        </div>

        {/* Endpoint groups */}
        {ENDPOINTS.map(group => (
          <div key={group.group} style={{ marginBottom:36 }}>
            <h2 style={{ fontSize:18, fontWeight:700, marginBottom:14, display:'flex', alignItems:'center', gap:10 }}>
              {group.group}
              <span style={{ fontSize:11, color:'var(--text3)', fontWeight:400 }}>{group.items.length} endpoint{group.items.length!==1?'s':''}</span>
            </h2>
            {group.items.map(ep => <EndpointRow key={ep.path+ep.method} ep={ep} />)}
          </div>
        ))}

        {/* SDK note */}
        <div style={{ background:'rgba(91,110,245,.06)', border:'1px solid rgba(91,110,245,.2)', borderRadius:10, padding:'20px 24px', marginBottom:40 }}>
          <p style={{ fontSize:13, fontWeight:700, marginBottom:6, color:'var(--primary)' }}>No official SDK — the API is simple enough</p>
          <p style={{ fontSize:13, color:'var(--text2)', lineHeight:1.65 }}>
            Any HTTP client works. The pattern is always the same: <code style={{fontFamily:'monospace', color:'var(--teal)', fontSize:12}}>POST /api/v1/tools/{'{name}'}</code> with <code style={{fontFamily:'monospace', color:'var(--teal)', fontSize:12}}>{'{"arguments": {...}}'}</code>.
            Check the response <code style={{fontFamily:'monospace', color:'var(--teal)', fontSize:12}}>ok</code> field and use <code style={{fontFamily:'monospace', color:'var(--teal)', fontSize:12}}>result</code>.
          </p>
        </div>
      </div>
    </div>
  )
}
