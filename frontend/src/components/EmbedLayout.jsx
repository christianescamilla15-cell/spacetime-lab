/**
 * EmbedLayout — minimal layout for iframe-embeddable widget routes.
 *
 * No nav, no footer, no header.  Just renders the routed page with
 * tighter padding and a small "powered by" link in the bottom-right
 * so consumers know where it came from.
 *
 * Used for /embed/* routes that third-party blogs / Notion pages /
 * arXiv-paper companion sites can <iframe src="...">.
 */

import { Outlet, Link } from 'react-router-dom'

export default function EmbedLayout() {
  return (
    <div style={styles.app}>
      <main style={styles.main}>
        <Outlet />
      </main>
      <a
        href="https://spacetime-lab.vercel.app"
        target="_blank"
        rel="noopener noreferrer"
        style={styles.poweredBy}
      >
        powered by ⚫ Spacetime Lab
      </a>
    </div>
  )
}

const styles = {
  app: {
    minHeight: '100vh',
    background: '#0a0a0f',
    color: '#e8e8f0',
    position: 'relative',
  },
  main: {
    width: '100%',
    margin: 0,
    padding: '12px',
    boxSizing: 'border-box',
  },
  poweredBy: {
    position: 'fixed',
    bottom: 8,
    right: 12,
    fontSize: 10,
    color: '#6b7280',
    textDecoration: 'none',
    background: 'rgba(0,0,0,0.5)',
    padding: '3px 8px',
    borderRadius: 4,
    backdropFilter: 'blur(8px)',
  },
}
