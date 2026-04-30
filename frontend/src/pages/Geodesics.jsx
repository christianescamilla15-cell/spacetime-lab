/**
 * Geodesics page — v2.6 Geodesic Explorer 3D foundations.
 *
 * Three.js scene of Kerr horizons + ergosphere with an animated
 * trajectory that the user can integrate from custom initial state.
 * The integration runs server-side on the spacetime_lab symplectic
 * integrator; the frontend only animates the returned trajectory.
 *
 * Design notes for v2.7+ extensions:
 *   - InitialStatePicker via 3D click is deferred (current UI: numeric sliders)
 *   - Multiple simultaneous geodesics deferred (current: one at a time)
 *   - Real PlaybackControls scrubber works (slider 0-100%)
 */

import { useEffect, useState } from 'react'
import KerrScene3D from '../components/KerrScene3D'
import ConservationPanel from '../components/ConservationPanel'
import { TexBlock, Tex } from '../components/Math'

const API = import.meta.env.VITE_API_URL || ''

const DEFAULT_REQUEST = {
  metric: 'kerr',
  params: { mass: 1.0, spin: 0.5 },
  // (t, r, theta, phi) — start in the equatorial plane at r=10M
  initial_position: [0.0, 10.0, 1.5708, 0.0],
  // (p_t, p_r, p_theta, p_phi) — covariant; E=0.94, slight inclination, prograde
  initial_momentum: [-0.94, 0.0, 1.5, 3.0],
  step_size: 0.5,
  n_steps: 1500,
  decimation: 5,
}

export default function Geodesics() {
  const [req, setReq] = useState(DEFAULT_REQUEST)
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [playFraction, setPlayFraction] = useState(1.0)
  const [playing, setPlaying] = useState(false)

  // Integrate on mount + whenever the user clicks "Integrate"
  const runIntegration = async (request) => {
    setLoading(true)
    setError(null)
    setResponse(null)
    try {
      const r = await fetch(`${API}/api/geodesics/integrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      })
      if (!r.ok) {
        const err = await r.text()
        throw new Error(`HTTP ${r.status}: ${err}`)
      }
      const data = await r.json()
      setResponse(data)
      setPlayFraction(1.0)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // Initial integration on mount
  useEffect(() => {
    runIntegration(DEFAULT_REQUEST)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Animation loop for play mode
  useEffect(() => {
    if (!playing || !response) return
    const interval = setInterval(() => {
      setPlayFraction((f) => {
        const next = f + 0.005
        if (next >= 1.0) {
          setPlaying(false)
          return 1.0
        }
        return next
      })
    }, 33) // ~30 fps
    return () => clearInterval(interval)
  }, [playing, response])

  const update = (path, value) => {
    setReq((prev) => {
      const next = JSON.parse(JSON.stringify(prev))
      const keys = path.split('.')
      let target = next
      for (let i = 0; i < keys.length - 1; i++) {
        const k = keys[i]
        target = Array.isArray(target) ? target[parseInt(k, 10)] : target[k]
      }
      const lastKey = keys[keys.length - 1]
      if (Array.isArray(target)) target[parseInt(lastKey, 10)] = value
      else target[lastKey] = value
      return next
    })
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <section style={styles.card}>
        <h2 style={styles.title}>Geodesic Explorer</h2>
        <p style={styles.lede}>
          Integrate a timelike or null geodesic in Kerr or Schwarzschild via
          the symplectic implicit-midpoint integrator (Phase 3 / v0.3).
          Energy <Tex>{'E = -p_t'}</Tex> and z-angular-momentum{' '}
          <Tex>{'L_z = p_\\varphi'}</Tex> are conserved to machine precision
          because <Tex>{'t'}</Tex> and <Tex>{'\\varphi'}</Tex> are cyclic in
          Boyer-Lindquist.  Carter <Tex>{'\\mathcal{Q}'}</Tex> drifts at{' '}
          <Tex>{'O(h^2)'}</Tex> per step.
        </p>

        <div style={styles.formula}>
          <TexBlock>
            {'\\frac{dx^\\mu}{d\\lambda} = g^{\\mu\\nu}(x) p_\\nu, \\quad \\frac{dp_\\mu}{d\\lambda} = -\\tfrac{1}{2}\\, \\partial_\\mu g^{\\alpha\\beta}\\, p_\\alpha p_\\beta'}
          </TexBlock>
        </div>
      </section>

      <section style={styles.card}>
        <h3 style={styles.sub}>Initial state &amp; integration parameters</h3>

        <div style={styles.controlsRow}>
          <Slider label={<>Mass <Tex>{'M'}</Tex></>} color="#ff6b9d"
            value={req.params.mass} onChange={(v) => update('params.mass', v)}
            min={0.5} max={3} step={0.05} />
          <Slider label={<>Spin <Tex>{'a/M'}</Tex></>} color="#00dfff"
            value={req.params.spin / req.params.mass}
            onChange={(v) => update('params.spin', v * req.params.mass)}
            min={0} max={0.999} step={0.005} />
        </div>

        <div style={styles.subSection}>Position <Tex>{'x^\\mu'}</Tex></div>
        <div style={styles.controlsRow}>
          <Slider label="r₀" color="#fbbf24"
            value={req.initial_position[1]} onChange={(v) => update('initial_position.1', v)}
            min={3} max={30} step={0.5} />
          <Slider label="θ₀ (rad)" color="#a78bfa"
            value={req.initial_position[2]} onChange={(v) => update('initial_position.2', v)}
            min={0.1} max={Math.PI - 0.1} step={0.05} />
        </div>

        <div style={styles.subSection}>Covariant momentum <Tex>{'p_\\mu'}</Tex></div>
        <div style={styles.controlsRow}>
          <Slider label={<>p_t = <Tex>{'-E'}</Tex></>} color="#22c55e"
            value={req.initial_momentum[0]} onChange={(v) => update('initial_momentum.0', v)}
            min={-1.5} max={-0.5} step={0.01} />
          <Slider label={<>p_φ = <Tex>{'L_z'}</Tex></>} color="#fb923c"
            value={req.initial_momentum[3]} onChange={(v) => update('initial_momentum.3', v)}
            min={-5} max={5} step={0.1} />
          <Slider label="p_θ" color="#06b6d4"
            value={req.initial_momentum[2]} onChange={(v) => update('initial_momentum.2', v)}
            min={-3} max={3} step={0.05} />
        </div>

        <div style={styles.subSection}>Integration</div>
        <div style={styles.controlsRow}>
          <Slider label="Step size h" color="#c4b5fd"
            value={req.step_size} onChange={(v) => update('step_size', v)}
            min={0.05} max={2} step={0.05} />
          <Slider label="n steps" color="#c4b5fd"
            value={req.n_steps} onChange={(v) => update('n_steps', Math.round(v))}
            min={100} max={5000} step={100} />
          <Slider label="decimation" color="#c4b5fd"
            value={req.decimation} onChange={(v) => update('decimation', Math.round(v))}
            min={1} max={50} step={1} />
        </div>

        <button
          onClick={() => runIntegration(req)}
          disabled={loading}
          style={{
            ...styles.runButton,
            opacity: loading ? 0.6 : 1,
            cursor: loading ? 'wait' : 'pointer',
          }}
        >
          {loading ? 'Integrating…' : '▶ Integrate'}
        </button>

        {error && (
          <div style={styles.errorBanner}>⚠️ {error}</div>
        )}

        {response && (
          <div style={styles.metaRow}>
            <Meta label="Returned points"
              value={response.metadata.n_returned_points} />
            <Meta label="Integration time"
              value={`${response.metadata.integration_seconds}s`} />
            <Meta label="Affine λ_max"
              value={(response.metadata.step_size * response.metadata.n_steps).toFixed(1)} />
          </div>
        )}
      </section>

      <section style={styles.card}>
        <h3 style={styles.sub}>3D scene</h3>
        <KerrScene3D
          mass={req.params.mass}
          spin={req.params.spin}
          trajectory={response?.trajectory}
          trailFraction={playFraction}
        />

        {response && (
          <div style={styles.playRow}>
            <button
              onClick={() => {
                if (playFraction >= 1.0) setPlayFraction(0)
                setPlaying((p) => !p)
              }}
              style={styles.playBtn}
            >
              {playing ? '⏸ Pause' : '▶ Play'}
            </button>
            <input
              type="range" min="0" max="1" step="0.005"
              value={playFraction}
              onChange={(e) => {
                setPlaying(false)
                setPlayFraction(parseFloat(e.target.value))
              }}
              style={styles.scrubber}
            />
            <span style={styles.fractionLabel}>
              {(playFraction * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </section>

      {response && (
        <ConservationPanel
          trajectory={response.trajectory}
          drift={response.drift_residuals}
        />
      )}
    </div>
  )
}

function Slider({ label, value, onChange, min, max, step, color }) {
  return (
    <div style={styles.sliderCell}>
      <label style={styles.sliderLabel}>
        {label}: <strong style={{ color }}>{Number(value).toFixed(step >= 1 ? 0 : 2)}</strong>
      </label>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        style={{ width: '100%', accentColor: color }}
      />
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
    padding: 28,
  },
  title: { fontSize: 24, margin: '0 0 8px', color: '#fff' },
  sub: { fontSize: 16, margin: '0 0 18px', color: '#fff' },
  lede: { fontSize: 14, color: '#9ca3af', marginBottom: 18, lineHeight: 1.6 },
  formula: {
    background: 'rgba(0,223,255,0.05)',
    border: '1px solid rgba(0,223,255,0.15)',
    borderRadius: 10,
    padding: '10px 16px',
    overflowX: 'auto',
  },
  controlsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: 14,
    marginBottom: 8,
  },
  subSection: {
    fontSize: 11,
    color: '#c4b5fd',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: 18,
    marginBottom: 10,
  },
  sliderCell: { display: 'flex', flexDirection: 'column' },
  sliderLabel: { fontSize: 12, color: '#c4b5fd', marginBottom: 6 },
  runButton: {
    marginTop: 22,
    padding: '12px 26px',
    borderRadius: 22,
    background: 'linear-gradient(135deg, #ff6b9d, #00dfff)',
    color: '#fff',
    border: 'none',
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
  },
  errorBanner: {
    marginTop: 16,
    padding: '10px 16px',
    background: 'rgba(255,193,7,0.1)',
    border: '1px solid rgba(255,193,7,0.3)',
    borderRadius: 8,
    fontSize: 13,
    color: '#ffc107',
  },
  metaRow: { display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 18 },
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
  metaValue: { fontSize: 13, fontWeight: 600, fontFamily: 'monospace', color: '#fff' },
  playRow: {
    display: 'flex', gap: 12, alignItems: 'center',
    marginTop: 16,
  },
  playBtn: {
    padding: '8px 18px',
    borderRadius: 18,
    background: 'rgba(255,107,157,0.15)',
    color: '#ff6b9d',
    border: '1px solid rgba(255,107,157,0.3)',
    fontSize: 13, cursor: 'pointer',
  },
  scrubber: { flex: 1, accentColor: '#fbbf24' },
  fractionLabel: {
    fontSize: 12, color: '#fbbf24',
    fontFamily: 'monospace', minWidth: 38, textAlign: 'right',
  },
}
