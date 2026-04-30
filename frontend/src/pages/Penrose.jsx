/**
 * Penrose page — live in v2.5.
 *
 * Fetches SVG from /api/diagrams/penrose/{kind}/svg (rendered by
 * spacetime_lab.diagrams.render.render_svg from v1.5) and embeds
 * it inside react-zoom-pan-pinch for pan + zoom interaction.
 *
 * Toggle between Minkowski and Schwarzschild kinds; for Schwarzschild
 * a mass slider re-fetches at the new value.
 */

import { useEffect, useState } from 'react'
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch'
import { TexBlock, Tex } from '../components/Math'

const API = import.meta.env.VITE_API_URL || ''

const KINDS = [
  { id: 'minkowski', label: 'Minkowski', desc: 'Flat spacetime causal structure' },
  { id: 'schwarzschild', label: 'Schwarzschild', desc: 'Maximally extended four-region BH' },
]

export default function Penrose() {
  const [kind, setKind] = useState('schwarzschild')
  const [mass, setMass] = useState(1.0)
  const [svg, setSvg] = useState(null)
  const [manifest, setManifest] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setError(null)
    setSvg(null)

    const url = `${API}/api/diagrams/penrose/${kind}/svg?mass=${mass}&width=600&height=600`
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.text()
      })
      .then((text) => !cancelled && setSvg(text))
      .catch((e) => !cancelled && setError(e.message))

    fetch(`${API}/api/diagrams/penrose/${kind}/manifest?mass=${mass}`)
      .then((r) => r.ok ? r.json() : null)
      .then((j) => !cancelled && setManifest(j))
      .catch(() => {})

    return () => { cancelled = true }
  }, [kind, mass])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <section style={styles.card}>
        <h2 style={styles.title}>Penrose Diagrams</h2>
        <p style={styles.lede}>
          Conformal compactifications that bring the entire causal
          structure of an infinite spacetime onto a finite diagram.  Light
          rays are exactly 45° lines; future and past timelike infinity
          (<Tex>{'i^\\pm'}</Tex>), spacelike infinity (<Tex>{'i^0'}</Tex>),
          and null infinity (<Tex>{'\\mathscr{I}^\\pm'}</Tex>) sit on the
          boundary.
        </p>

        <div style={styles.tabRow}>
          {KINDS.map((k) => (
            <button
              key={k.id}
              onClick={() => setKind(k.id)}
              style={{
                ...styles.tab,
                ...(kind === k.id ? styles.tabActive : {}),
              }}
            >
              {k.label}
            </button>
          ))}
        </div>

        <div style={styles.activeDesc}>
          {KINDS.find((k) => k.id === kind)?.desc}
        </div>

        {kind === 'schwarzschild' && (
          <div style={styles.controlGroup}>
            <label style={styles.controlLabel}>
              Mass M: <strong style={{ color: '#ff6b9d' }}>{mass.toFixed(2)}</strong>
            </label>
            <input
              type="range" min="0.5" max="3" step="0.1" value={mass}
              onChange={(e) => setMass(parseFloat(e.target.value))}
              style={styles.slider}
            />
            <small style={styles.hint}>
              Mass affects the labelled horizon position; the conformal
              shape itself is mass-independent.
            </small>
          </div>
        )}

        <div style={styles.viewport}>
          {error && (
            <div style={styles.errorBanner}>⚠️ API: {error}</div>
          )}
          {!svg && !error && (
            <div style={styles.loading}>Loading diagram…</div>
          )}
          {svg && (
            <TransformWrapper
              minScale={0.5} maxScale={5} initialScale={1}
              centerOnInit centerZoomedOut
              wheel={{ step: 0.15 }}
            >
              {({ zoomIn, zoomOut, resetTransform }) => (
                <>
                  <div style={styles.zoomControls}>
                    <button onClick={() => zoomIn()} style={styles.zoomBtn}>+</button>
                    <button onClick={() => zoomOut()} style={styles.zoomBtn}>−</button>
                    <button onClick={() => resetTransform()} style={styles.zoomBtn}>⟲</button>
                  </div>
                  <TransformComponent wrapperStyle={{
                    width: '100%',
                    background: '#0a0a0f',
                    borderRadius: 10,
                  }}>
                    <div
                      dangerouslySetInnerHTML={{ __html: svg }}
                      style={styles.svgBox}
                    />
                  </TransformComponent>
                </>
              )}
            </TransformWrapper>
          )}
        </div>

        {manifest && (
          <div style={styles.manifestRow}>
            <Meta label="Regions" value={manifest.regions.join(', ') || '–'} />
            <Meta label="Coords" value={manifest.physical_coordinates.join(', ') || '–'} />
            <Meta label="Infinities" value={manifest.infinities.join('  ') || '–'} />
          </div>
        )}
      </section>

      <section style={styles.card}>
        <h3 style={{ margin: 0, color: '#fff' }}>How to read it</h3>
        <ul style={styles.bulletList}>
          <li>
            <strong>Light rays travel at 45°</strong> — that's the whole
            point of the conformal compactification: it preserves angles.
          </li>
          <li>
            Move <em>up</em> in the diagram = move forward in time. Past
            infinity at the bottom, future at the top.
          </li>
          <li>
            For Schwarzschild: regions <strong>I</strong> (our universe),{' '}
            <strong>II</strong> (BH interior), <strong>III</strong> (other
            universe), <strong>IV</strong> (white hole).  No causal contact
            between I and III.
          </li>
          <li>
            The two diagonal lines inside region II are the future event
            horizons.  Once crossed, you can only end at the singularity
            (the horizontal jagged line).
          </li>
        </ul>
        <p style={styles.cite}>
          Reference: Penrose 1964 (causal structure); Kruskal 1960,
          Szekeres 1960 (Schwarzschild maximal extension); Hawking & Ellis,{' '}
          <em>The Large Scale Structure of Space-Time</em>, ch. 5.  SVG
          renderer shipped in v1.5.0.
        </p>
      </section>
    </div>
  )
}

function Meta({ label, value }) {
  return (
    <div style={styles.meta}>
      <div style={styles.metaLabel}>{label}</div>
      <div style={styles.metaValue}>{value}</div>
    </div>
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
  lede: { fontSize: 14, color: '#9ca3af', marginBottom: 22, lineHeight: 1.6 },
  tabRow: { display: 'flex', gap: 8, marginBottom: 8 },
  tab: {
    padding: '8px 18px',
    borderRadius: 20,
    border: '1px solid rgba(255,255,255,0.1)',
    background: 'rgba(255,255,255,0.04)',
    color: '#c4b5fd',
    fontSize: 13,
    cursor: 'pointer',
  },
  tabActive: {
    background: 'linear-gradient(135deg, rgba(255,107,157,0.2), rgba(0,223,255,0.2))',
    color: '#fff',
    border: '1px solid rgba(255,107,157,0.4)',
  },
  activeDesc: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 18,
    fontStyle: 'italic',
  },
  controlGroup: { marginBottom: 18 },
  controlLabel: { display: 'block', fontSize: 13, color: '#c4b5fd', marginBottom: 6 },
  slider: { width: '100%', accentColor: '#ff6b9d' },
  hint: { display: 'block', fontSize: 11, color: '#6b7280', marginTop: 4 },
  viewport: {
    position: 'relative',
    background: '#0a0a0f',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 12,
    minHeight: 620,
    overflow: 'hidden',
  },
  zoomControls: {
    position: 'absolute',
    top: 10, right: 10,
    display: 'flex', flexDirection: 'column', gap: 4,
    zIndex: 10,
  },
  zoomBtn: {
    width: 32, height: 32,
    borderRadius: 6,
    border: '1px solid rgba(255,255,255,0.15)',
    background: 'rgba(0,0,0,0.5)',
    color: '#e8e8f0', fontSize: 16, cursor: 'pointer',
  },
  svgBox: { display: 'flex', justifyContent: 'center', padding: 10 },
  loading: {
    padding: 40, textAlign: 'center', color: '#6b7280', fontSize: 13,
  },
  errorBanner: {
    margin: 20,
    padding: '10px 16px',
    background: 'rgba(255,193,7,0.1)',
    border: '1px solid rgba(255,193,7,0.3)',
    borderRadius: 8,
    fontSize: 13,
    color: '#ffc107',
  },
  manifestRow: {
    display: 'flex', gap: 14, flexWrap: 'wrap', marginTop: 18,
  },
  meta: {
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 8,
    padding: '8px 14px',
  },
  metaLabel: {
    fontSize: 10, color: '#9ca3af',
    textTransform: 'uppercase', letterSpacing: 0.5,
  },
  metaValue: { fontSize: 12, fontFamily: 'monospace', color: '#fff' },
  bulletList: {
    fontSize: 14, color: '#c4b5fd', lineHeight: 1.8,
    paddingLeft: 20, marginTop: 14,
  },
  cite: { fontSize: 11, color: '#6b7280', marginTop: 16, fontStyle: 'italic' },
}
