import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer style={{
      borderTop: '1px solid var(--border)',
      padding: '40px 0 28px',
      marginTop: 'auto',
    }}>
      <div className="container">
        <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 1fr 1fr', gap: 40, marginBottom: 40 }}>
          {/* Brand */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <div style={{ width: 28, height: 28, borderRadius: 7, background: 'linear-gradient(135deg,#7C5CF0,#00C8F8)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 800, color: '#fff' }}>G</div>
              <span style={{ fontWeight: 700, fontSize: 15 }}>Glas MCP</span>
            </div>
            <p style={{ color: 'var(--text2)', fontSize: 13, lineHeight: 1.7, maxWidth: 240 }}>
              Modular Model Context Protocol server. 8 tools, zero configuration, production ready.
            </p>
            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              <span className="badge badge-green">Open Source</span>
              <span className="badge badge-gray">MIT License</span>
            </div>
          </div>

          <div>
            <p style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.08em', color: 'var(--text3)', marginBottom: 14 }}>Product</p>
            {[['/', 'Home'], ['/tools', 'Tools'], ['/playground', 'Playground'], ['/docs', 'Documentation']].map(([to, label]) => (
              <Link key={to} to={to} style={{ display: 'block', color: 'var(--text2)', fontSize: 13, marginBottom: 9, transition: 'color .15s' }}
                onMouseEnter={e => e.currentTarget.style.color = 'var(--text)'}
                onMouseLeave={e => e.currentTarget.style.color = 'var(--text2)'}>{label}</Link>
            ))}
          </div>

          <div>
            <p style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.08em', color: 'var(--text3)', marginBottom: 14 }}>Developers</p>
            {[['/api', 'API Reference'], ['/docs#quickstart', 'Quick Start'], ['/docs#tools', 'Adding Tools'], ['/docs#deploy', 'Deployment']].map(([to, label]) => (
              <Link key={to} to={to} style={{ display: 'block', color: 'var(--text2)', fontSize: 13, marginBottom: 9, transition: 'color .15s' }}
                onMouseEnter={e => e.currentTarget.style.color = 'var(--text)'}
                onMouseLeave={e => e.currentTarget.style.color = 'var(--text2)'}>{label}</Link>
            ))}
          </div>

          <div>
            <p style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.08em', color: 'var(--text3)', marginBottom: 14 }}>Connect</p>
            {[
              ['https://github.com/anguzudouglas/glas-mcp', 'GitHub'],
              ['https://glas-mcp.onrender.com/health', 'Server Status'],
              ['https://glas-mcp.onrender.com/docs', 'Swagger UI'],
            ].map(([href, label]) => (
              <a key={href} href={href} target="_blank" rel="noreferrer"
                style={{ display: 'block', color: 'var(--text2)', fontSize: 13, marginBottom: 9, transition: 'color .15s' }}
                onMouseEnter={e => e.currentTarget.style.color = 'var(--text)'}
                onMouseLeave={e => e.currentTarget.style.color = 'var(--text2)'}>{label} ↗</a>
            ))}
          </div>
        </div>

        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <p style={{ color: 'var(--text3)', fontSize: 12 }}>
            © 2025 Glas MCP · Built by <a href="https://github.com/anguzudouglas" target="_blank" rel="noreferrer" style={{ color: 'var(--text2)' }}>anguzudouglas</a>
          </p>
          <p style={{ color: 'var(--text3)', fontSize: 12 }}>
            Hosted on <a href="https://render.com" target="_blank" rel="noreferrer" style={{ color: 'var(--text2)' }}>Render</a>
          </p>
        </div>
      </div>
    </footer>
  )
}
