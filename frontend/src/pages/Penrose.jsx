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
import { useTranslation } from 'react-i18next'
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch'
import { TexBlock, Tex } from '../components/Math'
import { api } from '../lib/api'

const API = import.meta.env.VITE_API_URL || ''

// id-only list; labels + descriptions come from i18n at render time.
const KIND_IDS = ['minkowski', 'schwarzschild']

// Default Schwarzschild bound orbit used by the geodesic overlay (v2.7.1).
// Same physics as the "Schwarzschild bound orbit" preset in /geodesics.
const DEFAULT_OVERLAY_BODY = {
  mass: 1.0,
  initial_position: [0.0, 8.0, 1.5708, 0.0],
  initial_momentum: [-0.96, 0.0, 0.0, 3.7],
  step_size: 0.5,
  n_steps: 600,
  width: 620,
  height: 620,
  overlay_color: '#fbbf24',
}

export default function Penrose() {
  const { t } = useTranslation()
  const [kind, setKind] = useState('schwarzschild')

  const kindMeta = (id) => ({
    minkowski: { label: t('penrose.kind_minkowski'), desc: t('penrose.kind_minkowski_desc') },
    schwarzschild: { label: t('penrose.kind_schwarzschild'), desc: t('penrose.kind_schwarzschild_desc') },
  }[id])
  const [mass, setMass] = useState(1.0)
  const [svg, setSvg] = useState(null)
  const [manifest, setManifest] = useState(null)
  const [error, setError] = useState(null)
  const [overlayOn, setOverlayOn] = useState(false)
  const [overlayMeta, setOverlayMeta] = useState(null)

  useEffect(() => {
    let cancelled = false
    setError(null)
    setSvg(null)
    setOverlayMeta(null)

    if (overlayOn && kind === 'schwarzschild') {
      // POST endpoint with overlay
      api.diagrams.penroseSchwarzschildWithGeodesic({
        ...DEFAULT_OVERLAY_BODY,
        mass,
      })
        .then((res) => {
          if (cancelled) return
          setSvg(res.svg)
          setOverlayMeta({
            samples: res.samples,
            skipped: res.skipped,
            finalR: res.finalR,
          })
        })
        .catch((e) => !cancelled && setError(e.message))
    } else {
      // Plain GET endpoint (no overlay)
      const url = `${API}/api/diagrams/penrose/${kind}/svg?mass=${mass}&width=600&height=600`
      fetch(url)
        .then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`)
          return r.text()
        })
        .then((text) => !cancelled && setSvg(text))
        .catch((e) => !cancelled && setError(e.message))
    }

    fetch(`${API}/api/diagrams/penrose/${kind}/manifest?mass=${mass}`)
      .then((r) => r.ok ? r.json() : null)
      .then((j) => !cancelled && setManifest(j))
      .catch(() => {})

    return () => { cancelled = true }
  }, [kind, mass, overlayOn])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <section style={styles.card}>
        <h2 style={styles.title}>{t('penrose.title')}</h2>
        <p style={styles.lede}>
          {t('penrose.lede_pre')}<Tex>{'i^\\pm'}</Tex>{t('penrose.lede_mid1')}<Tex>{'i^0'}</Tex>{t('penrose.lede_mid2')}<Tex>{'\\mathscr{I}^\\pm'}</Tex>{t('penrose.lede_post')}
        </p>

        <div style={styles.tabRow}>
          {KIND_IDS.map((id) => (
            <button
              key={id}
              onClick={() => setKind(id)}
              style={{
                ...styles.tab,
                ...(kind === id ? styles.tabActive : {}),
              }}
            >
              {kindMeta(id).label}
            </button>
          ))}
        </div>

        <div style={styles.activeDesc}>
          {kindMeta(kind)?.desc}
        </div>

        {kind === 'schwarzschild' && (
          <div style={styles.controlGroup}>
            <label style={styles.controlLabel}>
              {t('penrose.mass_label')}: <strong style={{ color: '#ff6b9d' }}>{mass.toFixed(2)}</strong>
            </label>
            <input
              type="range" min="0.5" max="3" step="0.1" value={mass}
              onChange={(e) => setMass(parseFloat(e.target.value))}
              style={styles.slider}
            />
            <small style={styles.hint}>
              {t('penrose.mass_hint')}
            </small>

            {/* v2.7.1: optional geodesic overlay */}
            <label style={{ ...styles.controlLabel, marginTop: 16, cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={overlayOn}
                onChange={(e) => setOverlayOn(e.target.checked)}
                style={{ marginRight: 8, accentColor: '#fbbf24' }}
              />
              {t('penrose.overlay_label_pre')}<Tex>{'(t,r) \\to (U,V)'}</Tex>
            </label>
            {overlayMeta && (
              <div style={styles.overlayMeta}>
                <code>{overlayMeta.samples}</code>{t('penrose.overlay_meta_mid1')}
                <code>{overlayMeta.skipped}</code>{t('penrose.overlay_meta_mid2')}
                <code>{overlayMeta.finalR.toFixed(2)}M</code>
              </div>
            )}
          </div>
        )}

        <div style={styles.viewport}>
          {error && (
            <div style={styles.errorBanner}>⚠️ {t('common.api_error')}: {error}</div>
          )}
          {!svg && !error && (
            <div style={styles.loading}>{t('common.loading_diagram')}</div>
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
            <Meta label={t('penrose.manifest.regions')} value={manifest.regions.join(', ') || '–'} />
            <Meta label={t('penrose.manifest.coords')} value={manifest.physical_coordinates.join(', ') || '–'} />
            <Meta label={t('penrose.manifest.infinities')} value={manifest.infinities.join('  ') || '–'} />
          </div>
        )}
      </section>

      <section style={styles.card}>
        <h3 style={{ margin: 0, color: '#fff' }}>{t('penrose.how_to_read')}</h3>
        <ul style={styles.bulletList}>
          <li>{t('penrose.bullet_a')}</li>
          <li>{t('penrose.bullet_b')}</li>
          <li>{t('penrose.bullet_c')}</li>
          <li>{t('penrose.bullet_d')}</li>
        </ul>
        <p style={styles.cite}>
          {t('penrose.cite')}
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
  overlayMeta: {
    fontSize: 11,
    color: '#fbbf24',
    marginTop: 8,
    fontFamily: 'monospace',
  },
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
