import { useState, useEffect } from 'react'

const GLAS_BASE = 'https://glas-mcp.onrender.com/api/v1'

const CAT_META = {
  search:    { label:'Search',    color:'#5B6EF5', bg:'rgba(91,110,245,.1)',   border:'rgba(91,110,245,.2)'  },
  fetch:     { label:'Fetch',     color:'#00C8F8', bg:'rgba(0,200,248,.1)',    border:'rgba(0,200,248,.2)'   },
  math:      { label:'Math',      color:'#F5A623', bg:'rgba(245,166,35,.1)',   border:'rgba(245,166,35,.2)'  },
  chart:     { label:'Charts',    color:'#10D9A0', bg:'rgba(16,217,160,.1)',   border:'rgba(16,217,160,.2)'  },
  document:  { label:'Documents', color:'#7C5CF0', bg:'rgba(124,92,240,.1)',   border:'rgba(124,92,240,.2)'  },
}

function getCategory(name) {
  if (name.includes('search')) return 'search'
  if (name.includes('fetch'))  return 'fetch'
  if (name.includes('math'))   return 'math'
  if (name.includes('chart') || name.includes('plot')) return 'chart'
  return 'document'
}

function PropRow({ name, schema }) {
  const prop = schema?.properties?.[name] ?? {}
  const required = (schema?.required ?? []).includes(name)
  return (
    <tr>
      <td style={{ padding:'8px 12px', fontFamily:'monospace', fontSize:12, color:'var(--teal)', verticalAlign:'top' }}>
        {name}
        {required && <span style={{ color:'var(--red)', marginLeft:3 }}>*</span>}
      </td>
      <td style={{ padding:'8px 12px', fontSize:11, color:'var(--text3)', fontFamily:'monospace', verticalAlign:'top' }}>
        {prop.type ?? 'any'}
        {prop.default !== undefined && <span style={{ color:'var(--text3)', marginLeft:6 }}>= {JSON.stringify(prop.default)}</span>}
      </td>
      <td style={{ padding:'8px 12px', fontSize:12, color:'var(--text2)', verticalAlign:'top', lineHeight:1.5 }}>
        {prop.description ?? '—'}
      </td>
    </tr>
  )
}

function ToolCard({ tool }) {
  const [open, setOpen] = useState(false)
  const cat = getCategory(tool.name)
  const meta = CAT_META[cat]
  const props = Object.keys(tool.input_schema?.properties ?? {})

  return (
    <div style={{
      background:'var(--bg2)', border:'1px solid var(--border)',
      borderRadius:12, overflow:'hidden',
      transition:'border-color .15s, box-shadow .15s',
      ...(open ? { borderColor:'var(--border2)', boxShadow:'0 4px 24px rgba(0,0,0,.3)' } : {}),
    }}
      onMouseEnter={e => { if(!open) e.currentTarget.style.borderColor='var(--border2)' }}
      onMouseLeave={e => { if(!open) e.currentTarget.style.borderColor='var(--border)' }}
    >
      <div style={{ padding:'20px 22px', cursor:'pointer', userSelect:'none' }} onClick={() => setOpen(o => !o)}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:8 }}>
          <div style={{ display:'flex', alignItems:'center', gap:10 }}>
            <code style={{ fontSize:13, color:'var(--teal)', fontWeight:700 }}>{tool.name}</code>
            <span style={{
              fontSize:10, padding:'2px 8px', borderRadius:4, fontWeight:600,
              background:meta.bg, color:meta.color, border:`1px solid ${meta.border}`,
            }}>{meta.label}</span>
          </div>
          <span style={{ color:'var(--text3)', fontSize:12, marginLeft:10, flexShrink:0 }}>
            {open ? '▲ Close' : '▼ Expand'}
          </span>
        </div>
        <p style={{ fontSize:13, color:'var(--text2)', lineHeight:1.6 }}>{tool.description}</p>
        {!open && (
          <div style={{ display:'flex', gap:6, marginTop:10, flexWrap:'wrap' }}>
            {props.slice(0,4).map(p => (
              <span key={p} style={{ fontSize:10, padding:'2px 7px', background:'var(--bg3)', border:'1px solid var(--border)', borderRadius:4, color:'var(--text3)', fontFamily:'monospace' }}>{p}</span>
            ))}
            {props.length > 4 && <span style={{ fontSize:10, color:'var(--text3)' }}>+{props.length-4} more</span>}
          </div>
        )}
      </div>

      {open && (
        <div style={{ borderTop:'1px solid var(--border)', padding:'0 22px 20px' }}>
          {/* Parameters table */}
          {props.length > 0 && (
            <div style={{ marginTop:16 }}>
              <p style={{ fontSize:11, fontWeight:700, textTransform:'uppercase', letterSpacing:'.08em', color:'var(--text3)', marginBottom:10 }}>Parameters</p>
              <div style={{ background:'var(--code)', borderRadius:8, border:'1px solid var(--border)', overflow:'hidden' }}>
                <table style={{ width:'100%', borderCollapse:'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom:'1px solid var(--border)' }}>
                      {['Name','Type','Description'].map(h => (
                        <th key={h} style={{ padding:'8px 12px', fontSize:10, fontWeight:700, textTransform:'uppercase', letterSpacing:'.06em', color:'var(--text3)', textAlign:'left' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {props.map(p => <PropRow key={p} name={p} schema={tool.input_schema} />)}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* cURL example */}
          <div style={{ marginTop:16 }}>
            <p style={{ fontSize:11, fontWeight:700, textTransform:'uppercase', letterSpacing:'.08em', color:'var(--text3)', marginBottom:8 }}>Example</p>
            <div style={{ background:'var(--code)', borderRadius:8, border:'1px solid var(--border)', padding:'14px 16px', fontFamily:'monospace', fontSize:12, color:'#a8b8d8', lineHeight:1.7, overflowX:'auto' }}>
              <span style={{ color:'#6fcf97' }}>curl</span> -X POST https://glas-mcp.onrender.com/api/v1/tools/<span style={{ color:'var(--teal)' }}>{tool.name}</span> \{'\n'}
              {'  '}<span style={{ color:'var(--text3)' }}>-H</span> <span style={{ color:'#f5c06a' }}>"Content-Type: application/json"</span> \{'\n'}
              {'  '}<span style={{ color:'var(--text3)' }}>-d</span> <span style={{ color:'#f5c06a' }}>'{JSON.stringify({ arguments: Object.fromEntries(props.slice(0,2).map(p => [p, '...'])) })}'</span>
            </div>
          </div>

          <div style={{ marginTop:12, display:'flex', gap:8 }}>
            <a href="/playground" style={{ fontSize:12, color:'var(--primary)', fontWeight:600 }}>Try in Playground →</a>
            <span style={{ color:'var(--text3)' }}>·</span>
            <a href="/api" style={{ fontSize:12, color:'var(--text2)' }}>API Reference</a>
          </div>
        </div>
      )}
    </div>
  )
}

export default function Tools() {
  const [tools, setTools] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    fetch(`${GLAS_BASE}/tools`)
      .then(r => r.json())
      .then(d => { setTools(Array.isArray(d) ? d : (d.result ?? d.tools ?? [])); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  const cats = ['all', ...Object.keys(CAT_META)]
  const filtered = tools.filter(t => {
    const matchSearch = t.name.includes(search.toLowerCase()) || (t.description ?? '').toLowerCase().includes(search.toLowerCase())
    const matchCat = filter === 'all' || getCategory(t.name) === filter
    return matchSearch && matchCat
  })

  return (
    <div>
      {/* Header */}
      <div style={{ borderBottom:'1px solid var(--border)', padding:'48px 0 32px', background:'linear-gradient(to bottom, var(--bg1), var(--bg0))' }}>
        <div className="container">
          <p style={{ fontSize:11, fontWeight:700, textTransform:'uppercase', letterSpacing:'.1em', color:'var(--primary)', marginBottom:8 }}>Tools</p>
          <h1 style={{ fontSize:36, fontWeight:800, letterSpacing:'-.02em', marginBottom:8 }}>
            {tools.length || 8} tools. Zero configuration.
          </h1>
          <p style={{ color:'var(--text2)', fontSize:15, maxWidth:560 }}>
            Every tool is auto-discovered, self-describing, and callable over MCP or REST. Click any card to see parameters and examples.
          </p>
        </div>
      </div>

      <div className="container" style={{ padding:'32px 24px' }}>
        {/* Filters */}
        <div style={{ display:'flex', gap:12, marginBottom:28, flexWrap:'wrap', alignItems:'center' }}>
          <input
            value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search tools…"
            style={{
              background:'var(--bg2)', border:'1px solid var(--border)', borderRadius:8,
              padding:'8px 14px', color:'var(--text)', fontSize:13, outline:'none', width:220,
            }}
            onFocus={e => e.target.style.borderColor='var(--primary)'}
            onBlur={e => e.target.style.borderColor='var(--border)'}
          />
          <div style={{ display:'flex', gap:4 }}>
            {cats.map(c => (
              <button key={c} onClick={() => setFilter(c)} style={{
                padding:'7px 14px', borderRadius:7, fontSize:12, fontWeight:600, cursor:'pointer',
                background: filter===c ? 'var(--primary-dim)' : 'var(--bg2)',
                color: filter===c ? 'var(--primary)' : 'var(--text2)',
                border: filter===c ? '1px solid rgba(91,110,245,.3)' : '1px solid var(--border)',
              }}>
                {c === 'all' ? 'All' : CAT_META[c]?.label ?? c}
              </button>
            ))}
          </div>
          <span style={{ fontSize:12, color:'var(--text3)', marginLeft:'auto' }}>
            {filtered.length} of {tools.length} tools
          </span>
        </div>

        {/* Tool cards */}
        {loading && (
          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill,minmax(400px,1fr))', gap:14 }}>
            {[...Array(6)].map((_,i) => (
              <div key={i} style={{ background:'var(--bg2)', border:'1px solid var(--border)', borderRadius:12, padding:'20px 22px', height:100, opacity:.5 }} />
            ))}
          </div>
        )}
        {error && <p style={{ color:'var(--red)', fontSize:13 }}>⚠ {error}</p>}
        {!loading && !error && (
          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill,minmax(420px,1fr))', gap:14 }}>
            {filtered.map(t => <ToolCard key={t.name} tool={t} />)}
          </div>
        )}
        {!loading && !error && filtered.length === 0 && (
          <p style={{ color:'var(--text2)', fontSize:13, textAlign:'center', padding:'40px 0' }}>No tools match your search.</p>
        )}
      </div>
    </div>
  )
}
