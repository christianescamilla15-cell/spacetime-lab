/**
 * Penrose page — stub for v2.6.
 *
 * Placeholder while the backend SVG endpoint and the pan/zoom viewer are
 * wired up.  Showing visitors that the section exists is better than
 * hiding it; the empty state explains what's coming.
 */

export default function Penrose() {
  return (
    <section style={styles.card}>
      <h2 style={styles.title}>Penrose Diagrams</h2>
      <p style={styles.lede}>
        Conformal compactifications of Minkowski and Schwarzschild spacetimes,
        showing causal structure and infinity.  Already shipped in the Python
        package as <code>spacetime_lab.diagrams.penrose</code> with{' '}
        matplotlib, SVG and TikZ render backends (v0.2 → v1.5).
      </p>
      <div style={styles.placeholder}>
        <span style={styles.placeholderEmoji}>◇</span>
        <div style={styles.placeholderTitle}>Coming in v2.6</div>
        <div style={styles.placeholderDesc}>
          Pan & zoom on the four-region maximally extended Schwarzschild
          diagram, hover to label past/future timelike and null infinity,
          toggle between Minkowski and Schwarzschild kinds.
        </div>
        <a
          href="https://github.com/christianescamilla15-cell/spacetime-lab/tree/master/spacetime_lab/diagrams"
          target="_blank"
          rel="noopener noreferrer"
          style={styles.link}
        >
          See the Python module on GitHub →
        </a>
      </div>
    </section>
  )
}

const styles = {
  card: {
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 16,
    padding: 32,
  },
  title: { fontSize: 24, margin: '0 0 8px', color: '#fff' },
  lede: { fontSize: 14, color: '#9ca3af', marginBottom: 28, lineHeight: 1.6 },
  placeholder: {
    textAlign: 'center',
    padding: '60px 30px',
    background: 'rgba(255,255,255,0.02)',
    border: '1px dashed rgba(255,255,255,0.12)',
    borderRadius: 12,
  },
  placeholderEmoji: { fontSize: 48, color: '#a78bfa' },
  placeholderTitle: { fontSize: 18, color: '#fff', margin: '12px 0 8px' },
  placeholderDesc: {
    fontSize: 13,
    color: '#9ca3af',
    lineHeight: 1.6,
    maxWidth: 460,
    margin: '0 auto 16px',
  },
  link: {
    display: 'inline-block',
    color: '#ff6b9d',
    textDecoration: 'none',
    fontSize: 13,
    padding: '8px 16px',
    borderRadius: 20,
    border: '1px solid rgba(255,107,157,0.3)',
  },
}
