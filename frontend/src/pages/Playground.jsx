import { useState, useEffect, useRef, useCallback } from 'react'

const GLAS_BASE = 'https://glas-mcp.onrender.com/api/v1'

async function callAnthropic(apiKey, model, messages, tools, systemPrompt) {
  const body = { model, max_tokens: 4096, system: systemPrompt, messages }
  if (tools?.length) body.tools = tools
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-api-key': apiKey, 'anthropic-version': '2023-06-01', 'anthropic-dangerous-direct-browser-access': 'true' },
    body: JSON.stringify(body),
  })
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e?.error?.message ?? `Anthropic ${res.status}`) }
  const data = await res.json()
  return { text: data.content?.filter(b => b.type === 'text').map(b => b.text).join('\n') ?? '', toolCalls: data.content?.filter(b => b.type === 'tool_use') ?? [], stopReason: data.stop_reason, rawContent: data.content }
}

async function callOpenAI(apiBase, apiKey, model, messages, extraHeaders = {}) {
  const oaMsgs = messages.map(m => ({ role: m.role, content: Array.isArray(m.content) ? m.content.filter(c => c.type === 'text').map(c => c.text).join('\n') : (m.content ?? '') })).filter(m => m.content)
  const res = await fetch(apiBase, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}`, ...extraHeaders }, body: JSON.stringify({ model, messages: oaMsgs, max_tokens: 4096 }) })
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e?.error?.message ?? `API ${res.status}`) }
  const data = await res.json()
  return { text: data.choices?.[0]?.message?.content ?? '', toolCalls: [], stopReason: 'end_turn', rawContent: [] }
}

async function callGemini(apiKey, model, messages) {
  const contents = messages.filter(m => m.role === 'user' || m.role === 'assistant').map(m => ({ role: m.role === 'assistant' ? 'model' : 'user', parts: [{ text: Array.isArray(m.content) ? m.content.filter(c => c.type === 'text').map(c => c.text).join('\n') : (m.content ?? '') }] })).filter(m => m.parts[0].text)
  const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ contents }) })
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e?.error?.message ?? `Gemini ${res.status}`) }
  const data = await res.json()
  return { text: data.candidates?.[0]?.content?.parts?.[0]?.text ?? '', toolCalls: [], stopReason: 'end_turn', rawContent: [] }
}

async function glasListTools() {
  const res = await fetch(`${GLAS_BASE}/tools`)
  if (!res.ok) throw new Error(`${res.status}`)
  const d = await res.json()
  return Array.isArray(d) ? d : (d.result ?? d.tools ?? [])
}

async function glasListProviders() {
  const res = await fetch(`${GLAS_BASE}/providers`)
  if (!res.ok) throw new Error(`${res.status}`)
  const d = await res.json()
  return d.providers ?? []
}

async function glasCallTool(name, args) {
  const res = await fetch(`${GLAS_BASE}/tools/${name}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ arguments: args }) })
  const json = await res.json()
  if (json.ok === false) throw new Error(json.error?.message ?? 'Tool error')
  return json.result ?? json
}

async function agentLoop(provider, apiKey, model, userText, history, mcpTools, enabledTools, onEvent) {
  const systemPrompt = `You are Glas Agent — a helpful AI with ${mcpTools.length} tools from the Glas MCP server. Use tools proactively. Be concise and accurate.`
  const claudeTools = provider.name === 'anthropic' ? mcpTools.filter(t => enabledTools.has(t.name)).map(t => ({ name: t.name, description: (t.description || t.name).slice(0, 400), input_schema: t.input_schema ?? { type: 'object', properties: {} } })) : []
  const messages = [...history, { role: 'user', content: userText }]

  for (let i = 0; i < 8; i++) {
    let result
    if (provider.name === 'anthropic') result = await callAnthropic(apiKey, model, messages, claudeTools, systemPrompt)
    else if (provider.name === 'google') result = await callGemini(apiKey, model, messages)
    else result = await callOpenAI(provider.api_base_url, apiKey, model, messages, provider.extra_headers ?? {})

    if (result.text) onEvent({ type: 'text', text: result.text })
    messages.push({ role: 'assistant', content: provider.name === 'anthropic' ? result.rawContent : result.text })
    if (!result.toolCalls?.length || result.stopReason === 'end_turn') break

    const toolResults = []
    for (const tc of result.toolCalls) {
      onEvent({ type: 'tool_call', id: tc.id, name: tc.name, input: tc.input })
      try {
        const raw = await glasCallTool(tc.name, tc.input)
        let text = raw?.image_base64 ? JSON.stringify({ ...raw, image_base64: '[base64]' }) : (typeof raw === 'string' ? raw : JSON.stringify(raw, null, 2))
        if (text.length > 8000) text = text.slice(0, 8000) + '…'
        onEvent({ type: 'tool_result', id: tc.id, name: tc.name, text, raw })
        toolResults.push({ type: 'tool_result', tool_use_id: tc.id, content: text })
      } catch (e) {
        const text = `Error: ${e.message}`
        onEvent({ type: 'tool_error', id: tc.id, name: tc.name, text })
        toolResults.push({ type: 'tool_result', tool_use_id: tc.id, content: text, is_error: true })
      }
    }
    messages.push({ role: 'user', content: toolResults })
  }
  return messages.filter(m => m.role === 'user' || m.role === 'assistant')
}

function ToolBadge({ name, input, result, raw, isError, isPending }) {
  const [open, setOpen] = useState(false)
  return (
    <div style={{ margin: '4px 0' }}>
      <button onClick={() => setOpen(o => !o)} style={{ display: 'inline-flex', alignItems: 'center', gap: 7, background: isError ? 'rgba(240,71,71,.08)' : 'rgba(91,110,245,.08)', border: `1px solid ${isError ? 'rgba(240,71,71,.25)' : 'rgba(91,110,245,.25)'}`, borderRadius: 6, padding: '4px 12px', color: isError ? 'var(--red)' : 'var(--primary)', fontSize: 11, fontFamily: 'JetBrains Mono,monospace', cursor: 'pointer' }}>
        <span style={{ display: 'inline-block', animation: isPending ? 'spin .7s linear infinite' : 'none' }}>{isPending ? '◌' : isError ? '⚠' : '✓'}</span>
        <span>{name}</span>
        <span style={{ opacity: .4, fontSize: 9 }}>{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div style={{ background: 'var(--code)', border: '1px solid var(--border)', borderRadius: 6, padding: '10px 12px', marginTop: 4, fontSize: 11, fontFamily: 'JetBrains Mono,monospace', whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: 240, overflowY: 'auto', lineHeight: 1.6 }}>
          {input && Object.keys(input).length > 0 && <div style={{ color: 'var(--green)', marginBottom: 8 }}>{'▶ Input\n' + JSON.stringify(input, null, 2)}</div>}
          {result && <div style={{ color: '#8A9BB8' }}>{'◀ Result\n' + result}</div>}
          {raw?.image_base64 && <img src={`data:image/png;base64,${raw.image_base64}`} alt="chart" style={{ maxWidth: '100%', borderRadius: 6, marginTop: 8, border: '1px solid var(--border)', display: 'block' }} />}
        </div>
      )}
    </div>
  )
}

function AsstMsg({ events }) {
  return (
    <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
      <div style={{ width: 28, height: 28, borderRadius: 7, flexShrink: 0, background: 'linear-gradient(135deg,var(--purple),var(--teal))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, marginTop: 2 }}>◈</div>
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
        {events.map((ev, i) => {
          if (ev.type === 'text') return <div key={i} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '3px 14px 14px 14px', padding: '10px 16px', fontSize: 14, lineHeight: 1.65, whiteSpace: 'pre-wrap', wordBreak: 'break-word', color: 'var(--text)' }}>{ev.text}</div>
          if (ev.type === 'tool_call') { const res = events.find((e, k) => k > i && (e.type === 'tool_result' || e.type === 'tool_error') && e.id === ev.id); return <ToolBadge key={i} name={ev.name} input={ev.input} result={res?.text} raw={res?.raw} isError={res?.type === 'tool_error'} isPending={!res} /> }
          return null
        })}
      </div>
    </div>
  )
}

const FALLBACK_PROVIDERS = [
  { name: 'anthropic',  display_name: 'Anthropic',      logo: '◆', color: '#CC785C', api_key_placeholder: 'sk-ant-api03-…', models: [{ id: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6' }, { id: 'claude-opus-4-6', label: 'Claude Opus 4.6' }, { id: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5' }], default_model: 'claude-sonnet-4-6', supports_tool_use: true,  request_format: 'anthropic', api_base_url: 'https://api.anthropic.com/v1/messages' },
  { name: 'google',     display_name: 'Google Gemini',  logo: '✦', color: '#4285F4', api_key_placeholder: 'AIzaSy…',        models: [{ id: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' }, { id: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' }], default_model: 'gemini-2.0-flash', supports_tool_use: false, request_format: 'gemini' },
  { name: 'groq',       display_name: 'Groq',           logo: '▲', color: '#F97316', api_key_placeholder: 'gsk_…',           models: [{ id: 'llama-3.3-70b-versatile', label: 'Llama 3.3 70B' }, { id: 'mixtral-8x7b-32768', label: 'Mixtral 8x7B' }], default_model: 'llama-3.3-70b-versatile', supports_tool_use: false, request_format: 'openai', api_base_url: 'https://api.groq.com/openai/v1/chat/completions' },
  { name: 'openrouter', display_name: 'OpenRouter',     logo: '◉', color: '#7C3AED', api_key_placeholder: 'sk-or-v1-…',     models: [{ id: 'anthropic/claude-sonnet-4-6', label: 'Claude Sonnet 4.6' }, { id: 'openai/gpt-4o', label: 'GPT-4o' }, { id: 'google/gemini-2.0-flash-exp', label: 'Gemini 2.0 Flash' }, { id: 'meta-llama/llama-3.3-70b-instruct', label: 'Llama 3.3 70B' }], default_model: 'anthropic/claude-sonnet-4-6', supports_tool_use: false, request_format: 'openai', api_base_url: 'https://openrouter.ai/api/v1/chat/completions', extra_headers: { 'HTTP-Referer': 'https://glas-mcp.onrender.com', 'X-Title': 'Glas MCP Playground' } },
]

const SUGGESTIONS = ['Search the web for the latest AI news', 'Plot a bar chart of global temperatures 2020–2024', 'Calculate compound interest: $10k at 7% over 20 years', 'Fetch and summarise https://example.com']

export default function Playground() {
  const [providers, setProviders] = useState(FALLBACK_PROVIDERS)
  const [activeProvider, setActiveProvider] = useState('anthropic')
  const [apiKeys, setApiKeys] = useState(() => { try { return JSON.parse(localStorage.getItem('glas_api_keys') ?? '{}') } catch { return {} } })
  const [model, setModel] = useState('claude-sonnet-4-6')
  const [tools, setTools] = useState([])
  const [enabledTools, setEnabledTools] = useState(new Set())
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [turns, setTurns] = useState(0)
  const historyRef = useRef([])
  const bottomRef = useRef(null)
  const taRef = useRef(null)

  useEffect(() => {
    glasListProviders().then(ps => { if (ps.length) { setProviders(ps); setModel(ps.find(p => p.name === 'anthropic')?.default_model ?? ps[0].default_model ?? '') } }).catch(() => {})
    glasListTools().then(ts => { setTools(ts); setEnabledTools(new Set(ts.map(t => t.name))) }).catch(() => {})
  }, [])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, loading])

  const prov = providers.find(p => p.name === activeProvider) ?? providers[0]
  const currentKey = apiKeys[activeProvider] ?? ''

  const switchProv = name => { setActiveProvider(name); const p = providers.find(x => x.name === name); if (p) setModel(p.default_model ?? p.models?.[0]?.id ?? '') }
  const setKey = (name, val) => { const next = { ...apiKeys, [name]: val }; setApiKeys(next); localStorage.setItem('glas_api_keys', JSON.stringify(next)) }
  const toggleTool = (name, on) => { const s = new Set(enabledTools); on ? s.add(name) : s.delete(name); setEnabledTools(s) }
  const clearChat = () => { setMessages([]); historyRef.current = []; setTurns(0) }

  const send = useCallback(async (text) => {
    const msg = (text ?? input).trim()
    if (!msg || loading || !currentKey.trim()) return
    setInput(''); if (taRef.current) taRef.current.style.height = 'auto'
    setLoading(true)
    setMessages(prev => [...prev, { role: 'user', text: msg }, { role: 'assistant', events: [] }])
    try {
      const hist = await agentLoop(prov, currentKey, model, msg, historyRef.current, tools, enabledTools, ev => {
        setMessages(prev => { const c = [...prev]; c[c.length - 1] = { ...c[c.length - 1], events: [...c[c.length - 1].events, ev] }; return c })
      })
      historyRef.current = hist; setTurns(t => t + 1)
    } catch (e) {
      setMessages(prev => { const c = [...prev]; c[c.length - 1] = { ...c[c.length - 1], events: [{ type: 'text', text: '⚠ ' + e.message }] }; return c })
    } finally { setLoading(false) }
  }, [input, loading, currentKey, prov, model, tools, enabledTools])

  const canSend = currentKey.length > 8 && !loading && input.trim()

  return (
    <div style={{ height: 'calc(100vh - 60px)', display: 'flex', overflow: 'hidden' }}>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}@keyframes pulse{0%,100%{transform:scale(.7);opacity:.35}50%{transform:scale(1.2);opacity:1}}`}</style>

      {/* Sidebar */}
      <aside style={{ width: 256, flexShrink: 0, borderRight: '1px solid var(--border)', background: 'var(--bg1)', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
        <div style={{ padding: '14px 14px 0' }}>
          {/* Provider grid */}
          <p style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.08em', color: 'var(--text3)', marginBottom: 8 }}>Provider</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 5, marginBottom: 16 }}>
            {providers.map(p => {
              const active = p.name === activeProvider
              return (
                <button key={p.name} onClick={() => switchProv(p.name)} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 10px', borderRadius: 7, fontSize: 11, fontWeight: 600, cursor: 'pointer', background: active ? `${p.color}1a` : 'var(--bg2)', border: `1px solid ${active ? p.color + '55' : 'var(--border)'}`, color: active ? p.color : 'var(--text2)', transition: 'all .15s' }}>
                  <span style={{ fontSize: 15 }}>{p.logo}</span>{p.display_name?.split(' ')[0]}
                </button>
              )
            })}
          </div>

          {/* API Key */}
          <p style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.08em', color: 'var(--text3)', marginBottom: 6 }}>{prov?.display_name} API Key</p>
          <input type="password" value={currentKey} onChange={e => setKey(activeProvider, e.target.value)} placeholder={prov?.api_key_placeholder ?? 'Paste key…'}
            style={{ width: '100%', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 7, padding: '8px 10px', color: 'var(--text)', fontSize: 11, fontFamily: 'JetBrains Mono,monospace', outline: 'none', marginBottom: 4 }}
            onFocus={e => e.target.style.borderColor = prov?.color ?? 'var(--primary)'}
            onBlur={e => e.target.style.borderColor = 'var(--border)'} />
          <p style={{ fontSize: 10, color: currentKey.length > 8 ? 'var(--green)' : 'var(--text3)', marginBottom: 14 }}>{currentKey.length > 8 ? '● Key saved locally' : 'Never sent to our servers.'}</p>

          {/* Model */}
          <p style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.08em', color: 'var(--text3)', marginBottom: 6 }}>Model</p>
          <select value={model} onChange={e => setModel(e.target.value)} style={{ width: '100%', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 7, padding: '8px 10px', color: 'var(--text)', fontSize: 12, outline: 'none', marginBottom: 16, cursor: 'pointer' }}>
            {(prov?.models ?? []).map(m => <option key={m.id} value={m.id}>{m.label}</option>)}
          </select>

          {/* Tools */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <p style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.08em', color: 'var(--text3)' }}>
              Tools {!prov?.supports_tool_use && <span style={{ fontWeight: 400 }}>(Anthropic only)</span>}
            </p>
            {prov?.supports_tool_use && <button onClick={() => setEnabledTools(new Set(tools.map(t => t.name)))} style={{ background: 'none', border: 'none', fontSize: 10, color: 'var(--primary)', cursor: 'pointer' }}>All</button>}
          </div>
          <div style={{ opacity: prov?.supports_tool_use ? 1 : .35 }}>
            {tools.map(t => (
              <label key={t.name} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '5px 4px', borderRadius: 5, cursor: prov?.supports_tool_use ? 'pointer' : 'default' }}>
                <input type="checkbox" checked={enabledTools.has(t.name)} disabled={!prov?.supports_tool_use} onChange={e => toggleTool(t.name, e.target.checked)} style={{ accentColor: 'var(--primary)' }} />
                <code style={{ fontSize: 11, color: 'var(--teal)' }}>{t.name}</code>
              </label>
            ))}
          </div>
        </div>

        {/* Session info */}
        <div style={{ margin: 14, marginTop: 'auto', padding: '10px 12px', background: 'var(--bg2)', borderRadius: 8, border: '1px solid var(--border)' }}>
          <p style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.08em', color: 'var(--text3)', marginBottom: 8 }}>Session</p>
          {[['Turns', turns], ['Messages', messages.length]].map(([l, v]) => (
            <div key={l} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text2)', marginBottom: 4 }}>
              <span>{l}</span><span style={{ color: 'var(--text)', fontWeight: 600 }}>{v}</span>
            </div>
          ))}
          <button onClick={clearChat} style={{ width: '100%', marginTop: 8, padding: 6, background: 'none', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text2)', fontSize: 11, cursor: 'pointer' }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--red)'; e.currentTarget.style.color = 'var(--red)' }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text2)' }}>
            Clear chat
          </button>
        </div>
      </aside>

      {/* Chat */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
        {/* Topbar */}
        <div style={{ padding: '9px 20px', borderBottom: '1px solid var(--border)', background: 'var(--bg1)', display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
          {prov && <><span style={{ fontSize: 16, color: prov.color }}>{prov.logo}</span><span style={{ fontSize: 13, fontWeight: 600 }}>{prov.display_name}</span><span style={{ fontSize: 11, color: 'var(--text3)', fontFamily: 'monospace' }}>{model}</span></>}
          {prov?.supports_tool_use && <span style={{ fontSize: 10, padding: '2px 7px', background: 'rgba(16,217,160,.1)', color: 'var(--green)', border: '1px solid rgba(16,217,160,.2)', borderRadius: 4, fontWeight: 600 }}>{enabledTools.size} tools</span>}
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px 28px 8px', display: 'flex', flexDirection: 'column', gap: 18 }}>
          {messages.length === 0 && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '40px 20px' }}>
              <div style={{ fontSize: 44, marginBottom: 14, background: 'linear-gradient(135deg,var(--purple),var(--teal))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>◈</div>
              <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text)', marginBottom: 8 }}>Glas Playground</h2>
              {!currentKey.trim()
                ? <p style={{ fontSize: 13, color: 'var(--text2)', maxWidth: 280, lineHeight: 1.7 }}>Paste your <strong style={{ color: 'var(--text)' }}>{prov?.display_name}</strong> API key in the left panel to start.</p>
                : <><p style={{ fontSize: 13, color: 'var(--text2)', maxWidth: 320, lineHeight: 1.7, marginBottom: 20 }}>{prov?.supports_tool_use ? `${enabledTools.size} tools active. ` : ''}Ask anything.</p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 7, width: '100%', maxWidth: 420 }}>
                    {SUGGESTIONS.map(s => (
                      <button key={s} onClick={() => send(s)} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 9, padding: '10px 16px', color: 'var(--text)', fontSize: 13, textAlign: 'left', cursor: 'pointer' }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.background = 'var(--primary-dim)' }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.background = 'var(--bg2)' }}>
                        {s}
                      </button>
                    ))}
                  </div></>
              }
            </div>
          )}

          {messages.map((msg, i) => {
            if (msg.role === 'user') return (
              <div key={i} style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <div style={{ background: 'linear-gradient(135deg,rgba(91,110,245,.2),rgba(91,110,245,.1))', border: '1px solid rgba(91,110,245,.25)', color: 'var(--text)', borderRadius: '14px 14px 3px 14px', padding: '10px 16px', maxWidth: '72%', fontSize: 14, lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{msg.text}</div>
              </div>
            )
            return <AsstMsg key={i} events={msg.events} />
          })}

          {loading && messages[messages.length - 1]?.events?.length === 0 && (
            <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
              <div style={{ width: 28, height: 28, borderRadius: 7, background: 'linear-gradient(135deg,var(--purple),var(--teal))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, opacity: .6 }}>◈</div>
              <div style={{ display: 'flex', gap: 4 }}>{[0,1,2].map(d => <div key={d} style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--primary)', opacity: .7, animation: `pulse 1.2s ${d*.2}s ease-in-out infinite` }} />)}</div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div style={{ padding: '12px 28px 16px', borderTop: '1px solid var(--border)', background: 'var(--bg1)', flexShrink: 0 }}>
          {!currentKey.trim() && <div style={{ marginBottom: 10, padding: '8px 12px', background: 'rgba(245,166,35,.08)', border: '1px solid rgba(245,166,35,.2)', borderRadius: 7, fontSize: 12, color: 'var(--yellow)' }}>⚠ Add your {prov?.display_name} API key to start chatting.</div>}
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 12, padding: '10px 12px', transition: 'border-color .2s' }}
            onFocusCapture={e => e.currentTarget.style.borderColor = 'var(--primary)'}
            onBlurCapture={e => e.currentTarget.style.borderColor = 'var(--border)'}>
            <textarea ref={taRef} value={input}
              onChange={e => { setInput(e.target.value); e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px' }}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
              placeholder={currentKey.trim() ? 'Ask anything — tools activate automatically…' : 'Add API key to start…'}
              disabled={loading || !currentKey.trim()} rows={1}
              style={{ flex: 1, background: 'transparent', border: 'none', outline: 'none', color: 'var(--text)', fontSize: 14, fontFamily: 'Inter,sans-serif', resize: 'none', lineHeight: 1.5, maxHeight: 160, minHeight: 24 }} />
            <button onClick={() => send()} disabled={!canSend} style={{ width: 36, height: 36, flexShrink: 0, borderRadius: 8, background: canSend ? 'var(--primary)' : 'var(--bg3)', border: canSend ? 'none' : '1px solid var(--border)', color: '#fff', fontSize: 16, cursor: canSend ? 'pointer' : 'not-allowed', display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: canSend ? 1 : .4 }}>↑</button>
          </div>
          <p style={{ textAlign: 'center', marginTop: 8, fontSize: 10, color: 'var(--text3)' }}>Your API key is stored locally and never sent to our servers.</p>
        </div>
      </div>
    </div>
  )
}
