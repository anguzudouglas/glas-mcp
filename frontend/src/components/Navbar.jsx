import { useState, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'

const NAV_LINKS = [
  { to: '/', label: 'Home', exact: true },
  { to: '/tools', label: 'Tools' },
  { to: '/playground', label: 'Playground' },
  { to: '/docs', label: 'Docs' },
  { to: '/api', label: 'API' },
]

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => { setMobileOpen(false) }, [location])

  return (
    <header style={{
      position: 'sticky', top: 0, zIndex: 100,
      borderBottom: scrolled ? '1px solid var(--border)' : '1px solid transparent',
      background: scrolled ? 'rgba(7,9,15,.92)' : 'transparent',
      backdropFilter: scrolled ? 'blur(16px)' : 'none',
      transition: 'all .2s',
    }}>
      <div className="container" style={{ display: 'flex', alignItems: 'center', height: 60, gap: 8 }}>
        {/* Logo */}
        <NavLink to="/" style={{ display: 'flex', alignItems: 'center', gap: 10, marginRight: 16, flexShrink: 0 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'linear-gradient(135deg, #7C5CF0, #00C8F8)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 15, fontWeight: 800, color: '#fff', flexShrink: 0,
            boxShadow: '0 0 16px rgba(91,110,245,.3)',
          }}>G</div>
          <span style={{ fontWeight: 700, fontSize: 16, letterSpacing: '-.02em' }}>
            Glas <span style={{ color: 'var(--text2)', fontWeight: 400 }}>MCP</span>
          </span>
          <span className="badge badge-gray" style={{ fontSize: 10 }}>v1.0</span>
        </NavLink>

        {/* Nav links */}
        <nav style={{ display: 'flex', gap: 2, flex: 1 }} className="desktop-nav">
          {NAV_LINKS.map(({ to, label, exact }) => (
            <NavLink key={to} to={to} end={exact} style={({ isActive }) => ({
              padding: '6px 12px', borderRadius: 6, fontSize: 14, fontWeight: 500,
              color: isActive ? 'var(--text)' : 'var(--text2)',
              background: isActive ? 'var(--bg2)' : 'transparent',
              transition: 'all .15s',
            })}
              onMouseEnter={e => { if (!e.currentTarget.style.background.includes('bg2')) { e.currentTarget.style.color = 'var(--text)'; e.currentTarget.style.background = 'var(--bg2)'; } }}
              onMouseLeave={e => { if (e.currentTarget.getAttribute('aria-current') !== 'page') { e.currentTarget.style.color = 'var(--text2)'; e.currentTarget.style.background = 'transparent'; } }}
            >
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Right */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginLeft: 'auto' }}>
          <a href="https://github.com/anguzudouglas/glas-mcp" target="_blank" rel="noreferrer"
            className="btn btn-ghost btn-sm"
            style={{ gap: 6 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
            </svg>
            GitHub
          </a>
          <NavLink to="/playground" className="btn btn-primary btn-sm">
            Open Playground →
          </NavLink>
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .desktop-nav { display: none !important; }
        }
      `}</style>
    </header>
  )
}
