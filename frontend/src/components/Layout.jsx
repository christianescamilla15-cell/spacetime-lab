/**
 * App-wide layout: top nav + outlet for the routed page + footer.
 *
 * v2.7: stacks vertically on narrow viewports (≤720px) — the 6 nav
 * items would wrap to 2-3 lines and steal too much above-the-fold
 * space on phone, so we collapse to brand-on-top + nav-below.
 */

import { NavLink, Outlet } from 'react-router-dom'
import useMediaQuery from '../lib/useMediaQuery'

export default function Layout() {
  const isMobile = useMediaQuery('(max-width: 720px)')

  return (
    <div style={styles.app}>
      <header style={{ ...styles.header, ...(isMobile && styles.headerMobile) }}>
        <NavLink to="/" style={styles.brandLink}>
          <h1 style={{ ...styles.brand, ...(isMobile && styles.brandMobile) }}>
            <span style={styles.logo}>⚫</span> Spacetime Lab
          </h1>
        </NavLink>
        <nav style={{ ...styles.nav, ...(isMobile && styles.navMobile) }}>
          <NavItem to="/schwarzschild">Schwarzschild</NavItem>
          <NavItem to="/kerr">Kerr</NavItem>
          <NavItem to="/btz">BTZ</NavItem>
          <NavItem to="/geodesics">Geodesics</NavItem>
          <NavItem to="/penrose">Penrose</NavItem>
          <NavItem to="/holography">Holography</NavItem>
        </nav>
      </header>

      <main style={styles.main}>
        <Outlet />
      </main>

      <footer style={styles.footer}>
        <p>
          Built by{' '}
          <a href="https://github.com/christianescamilla15-cell"
            style={styles.footerLink} target="_blank" rel="noopener noreferrer">
            Christian Hernández
          </a>{' '}— an AI engineer learning GR by building tools for it.
        </p>
        <p style={styles.footerSmall}>
          v2.7 · 700+ tests · 15 notebooks · MIT License · © 2026
        </p>
      </footer>
    </div>
  )
}

function NavItem({ to, children }) {
  return (
    <NavLink to={to}
      style={({ isActive }) => ({
        ...styles.navLink,
        ...(isActive && styles.navLinkActive),
      })}>
      {children}
    </NavLink>
  )
}

const styles = {
  app: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #0a0a0f 0%, #1a0a1a 100%)',
    color: '#e8e8f0',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '20px 32px',
    borderBottom: '1px solid rgba(255,255,255,0.08)',
    flexWrap: 'wrap',
    gap: 16,
  },
  headerMobile: {
    flexDirection: 'column',
    padding: '14px 12px',
    gap: 10,
  },
  brandLink: { textDecoration: 'none' },
  brand: {
    fontSize: 28, margin: 0, fontWeight: 700,
    background: 'linear-gradient(135deg, #ff6b9d, #00dfff)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    display: 'inline-flex', alignItems: 'center', gap: 12,
  },
  brandMobile: { fontSize: 22 },
  logo: { fontSize: 24, WebkitTextFillColor: 'initial' },
  nav: { display: 'flex', gap: 4, flexWrap: 'wrap' },
  navMobile: {
    width: '100%',
    justifyContent: 'center',
    overflowX: 'auto',
    flexWrap: 'nowrap',
  },
  navLink: {
    padding: '8px 14px',
    borderRadius: 20,
    fontSize: 13,
    color: '#9ca3af',
    textDecoration: 'none',
    transition: 'all 0.15s',
    whiteSpace: 'nowrap',
  },
  navLinkActive: {
    background: 'rgba(255,107,157,0.12)',
    color: '#ff6b9d',
    border: '1px solid rgba(255,107,157,0.3)',
  },
  main: {
    flex: 1,
    maxWidth: 1100,
    width: '100%',
    margin: '0 auto',
    padding: '40px 20px',
    boxSizing: 'border-box',
  },
  footer: {
    textAlign: 'center',
    padding: '40px 20px',
    borderTop: '1px solid rgba(255,255,255,0.08)',
    color: '#6b7280',
    fontSize: 13,
  },
  footerLink: { color: '#ff6b9d', textDecoration: 'none' },
  footerSmall: { fontSize: 11, marginTop: 8 },
}
