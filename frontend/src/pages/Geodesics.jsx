/**
 * Geodesics page — v2.7 polish.
 *
 * Changes vs v2.6:
 *   - Multiple simultaneous geodesics with per-trajectory colour
 *   - Preset orbits (4) with citations
 *   - 3D click-pick on the equatorial disk to set initial position
 *   - PlaybackControls scrubs ALL active trails together
 */

import { useEffect, useState } from 'react'
import KerrScene3D from '../components/KerrScene3D'
import ConservationPanel from '../components/ConservationPanel'
import { TexBlock, Tex } from '../components/Math'

const API = import.meta.env.VITE_API_URL || ''

const TRAIL_COLORS = ['#fbbf24', '#22c55e', '#06b6d4', '#fb923c', '#a78bfa']

const DEFAULT_REQUEST = {
  metric: 'kerr',
  params: { mass: 1.0, spin: 0.5 },
  initial_position: [0.0, 10.0, 1.5708, 0.0],
  initial_momentum: [-0.94, 0.0, 1.5, 3.0],
  step_size: 0.5,
  n_steps: 1500,
  decimation: 5,
}

/**
 * Preset library — each preset is a complete request body.
 * Citations: Bardeen-Press-Teukolsky 1972 (ISCO closed form);
 *            Wald §6.3 (Schwarzschild circular orbits).
 */
const PRESETS = [
  {
    name: 'Stable inclined orbit',
    desc: 'Kerr a=0.5M, r=10M, prograde, slight inclination',
    request: { ...DEFAULT_REQUEST },
  },
  {
    name: 'Plunge to horizon',
    desc: 'Kerr a=0.5M, starts at r=10M with strong inward p_r — falls in',
    request: {
      ...DEFAULT_REQUEST,
      initial_momentum: [-0.96, -0.45, 0.5, 1.8],
      n_steps: 800,
    },
  },
  {
    name: 'Schwarzschild bound orbit',
    desc: 'Schwarzschild M=1, eccentric bound orbit at r=8M',
    request: {
      metric: 'schwarzschild',
      params: { mass: 1.0 },
      initial_position: [0.0, 8.0, 1.5708, 0.0],
      initial_momentum: [-0.96, 0.0, 0.0, 3.7],
      step_size: 0.5,
      n_steps: 2500,
      decimation: 8,
    },
  },
  {
    name: 'Highly inclined Kerr',
    desc: 'Kerr a=0.9M, large p_θ — strong out-of-plane motion',
    request: {
      metric: 'kerr',
      params: { mass: 1.0, spin: 0.9 },
      initial_position: [0.0, 12.0, 0.9, 0.0],
      initial_momentum: [-0.95, 0.0, 2.5, 3.5],
      step_size: 0.4,
      n_steps: 1500,
      decimation: 5,
    },
  },
]

let nextId = 1

export default function Geodesics() {
  const [draft, setDraft] = useState(DEFAULT_REQUEST)
  const [trajectories, setTrajectories] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [playFraction, setPlayFraction] = useState(1.0)
  const [playing, setPlaying] = useState(false)

  const runIntegration = async (request, replaceAll = false) => {
    setLoading(true)
    setError(null)
    try {
      const r = await fetch(`${API}/api/geodesics/integrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      })
      if (!r.ok) {
        const err = await r.text()
        throw new Error(`HTTP ${r.status}: ${err.slice(0, 200)}`)
      }
      const data = await r.json()
      const newEntry = {
        id: nextId++,
        color: TRAIL_COLORS[(trajectories.length + (replaceAll ? 0 : 0)) % TRAIL_COLORS.length],
        request,
        response: data,
      }
      setTrajectories((prev) => (replaceAll ? [newEntry] : [...prev, newEntry]))
      setPlayFraction(1.0)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // Initial run
  useEffect(() => {
    runIntegration(DEFAULT_REQUEST, true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Animation loop
  useEffect(() => {
    if (!playing || trajectories.length === 0) return
    const interval = setInterval(() => {
      setPlayFraction((f) => {
        const next = f + 0.005
        if (next >= 1.0) {
          setPlaying(false)
          return 1.0
        }
        return next
      })
    }, 33)
    return () => clearInterval(interval)
  }, [playing, trajectories.length])

  const update = (path, value) => {
    setDraft((prev) => {
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

  const removeTrajectory = (id) => {
    setTrajectories((prev) => prev.filter((t) => t.id !== id))
  }

  const onPick = ({ r, theta, phi }) => {
    setDraft((prev) => ({
      ...prev,
      initial_position: [0.0, r, theta, phi],
    }))
  }

  // First trajectory is the "primary" used for the conservation panel
  const primary = trajectories[0]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <section style={styles.card}>
        <h2 style={styles.title}>Geodesic Explorer</h2>
        <p style={styles.lede}>
          Integrate timelike or null geodesics in Kerr / Schwarzschild via
          the symplectic implicit-midpoint integrator (Phase 3, v0.3).
          Click on the equatorial disk in the 3D scene below to set a new
          initial position, or use the preset library.
        </p>
        <div style={styles.formula}>
          <TexBlock>
            {'\\frac{dx^\\mu}{d\\lambda} = g^{\\mu\\nu}(x) p_\\nu, \\quad \\frac{dp_\\mu}{d\\lambda} = -\\tfrac{1}{2}\\, \\partial_\\mu g^{\\alpha\\beta}\\, p_\\alpha p_\\beta'}
          </TexBlock>
        </div>
      </section>

      <section style={styles.card}>
        <h3 style={styles.sub}>Presets</h3>
        <div style={styles.presetRow}>
          {PRESETS.map((p) => (
            <button
              key={p.name}
              onClick={() => {
                setDraft(p.request)
                runIntegration(p.request, true)
              }}
              style={styles.presetBtn}
              title={p.desc}
            >
              <strong>{p.name}</strong>
              <small>{p.desc}</small>
            </button>
          ))}
        </div>
      </section>

      <section style={styles.card}>
        <h3 style={styles.sub}>Initial state &amp; integration parameters</h3>

        <div style={styles.controlsRow}>
          <Slider label={<>Mass <Tex>{'M'}</Tex></>} color="#ff6b9d"
            value={draft.params.mass} onChange={(v) => update('params.mass', v)}
            min={0.5} max={3} step={0.05} />
          <Slider label={<>Spin <Tex>{'a/M'}</Tex></>} color="#00dfff"
            value={draft.params.spin / draft.params.mass}
            onChange={(v) => update('params.spin', v * draft.params.mass)}
            min={0} max={0.999} step={0.005} />
          <SelectMetric value={draft.metric}
            onChange={(v) => update('metric', v)} />
        </div>

        <div style={styles.subSection}>Position <Tex>{'x^\\mu'}</Tex></div>
        <div style={styles.controlsRow}>
          <Slider label="r₀" color="#fbbf24"
            value={draft.initial_position[1]}
            onChange={(v) => update('initial_position.1', v)}
            min={3} max={30} step={0.5} />
          <Slider label="θ₀ (rad)" color="#a78bfa"
            value={draft.initial_position[2]}
            onChange={(v) => update('initial_position.2', v)}
            min={0.1} max={Math.PI - 0.1} step={0.05} />
        </div>

        <div style={styles.subSection}>Covariant momentum <Tex>{'p_\\mu'}</Tex></div>
        <div style={styles.controlsRow}>
          <Slider label={<>p_t = <Tex>{'-E'}</Tex></>} color="#22c55e"
            value={draft.initial_momentum[0]}
            onChange={(v) => update('initial_momentum.0', v)}
            min={-1.5} max={-0.5} step={0.01} />
          <Slider label={<>p_φ = <Tex>{'L_z'}</Tex></>} color="#fb923c"
            value={draft.initial_momentum[3]}
            onChange={(v) => update('initial_momentum.3', v)}
            min={-5} max={5} step={0.1} />
          <Slider label="p_θ" color="#06b6d4"
            value={draft.initial_momentum[2]}
            onChange={(v) => update('initial_momentum.2', v)}
            min={-3} max={3} step={0.05} />
          <Slider label="p_r" color="#a78bfa"
            value={draft.initial_momentum[1]}
            onChange={(v) => update('initial_momentum.1', v)}
            min={-1} max={1} step={0.02} />
        </div>

        <div style={styles.subSection}>Integration</div>
        <div style={styles.controlsRow}>
          <Slider label="Step size h" color="#c4b5fd"
            value={draft.step_size} onChange={(v) => update('step_size', v)}
            min={0.05} max={2} step={0.05} />
          <Slider label="n steps" color="#c4b5fd"
            value={draft.n_steps}
            onChange={(v) => update('n_steps', Math.round(v))}
            min={100} max={5000} step={100} />
          <Slider label="decimation" color="#c4b5fd"
            value={draft.decimation}
            onChange={(v) => update('decimation', Math.round(v))}
            min={1} max={50} step={1} />
        </div>

        <div style={styles.actionRow}>
          <button onClick={() => runIntegration(draft, true)}
            disabled={loading} style={{ ...styles.runBtn, ...(loading && styles.btnDisabled) }}>
            {loading ? 'Integrating…' : '▶ Replace with this'}
          </button>
          <button onClick={() => runIntegration(draft, false)}
            disabled={loading || trajectories.length >= 5}
            style={{ ...styles.runBtnSec, ...(loading && styles.btnDisabled) }}
            title={trajectories.length >= 5 ? 'Maximum 5 trajectories at once' : 'Add a new trajectory alongside the existing ones'}>
            ➕ Add as new
          </button>
          <span style={styles.actionHint}>
            {trajectories.length}/5 trajectories
          </span>
        </div>

        {error && <div style={styles.errorBanner}>⚠️ {error}</div>}
      </section>

      <section style={styles.card}>
        <h3 style={styles.sub}>3D scene · click on the dark disk to set r₀, φ₀</h3>
        <KerrScene3D
          mass={draft.params.mass}
          spin={draft.metric === 'kerr' ? draft.params.spin : 0}
          trajectories={trajectories}
          trailFractions={trajectories.map(() => playFraction)}
          onPickInitialState={onPick}
        />

        <div style={styles.playRow}>
          <button onClick={() => {
            if (playFraction >= 1.0) setPlayFraction(0)
            setPlaying((p) => !p)
          }} style={styles.playBtn}>
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
          <span style={styles.fractionLabel}>{(playFraction * 100).toFixed(0)}%</span>
        </div>

        {trajectories.length > 0 && (
          <div style={styles.legend}>
            {trajectories.map((t) => (
              <div key={t.id} style={styles.legendItem}>
                <span style={{ ...styles.legendSwatch, background: t.color }} />
                <span style={styles.legendText}>
                  {t.request.metric} M={t.request.params.mass}
                  {t.request.metric === 'kerr' && ` a=${t.request.params.spin.toFixed(2)}`}
                  {' '}r₀={t.request.initial_position[1].toFixed(1)}M
                </span>
                <button onClick={() => removeTrajectory(t.id)}
                  style={styles.legendCloseBtn}
                  title="Remove this trajectory">✕</button>
              </div>
            ))}
          </div>
        )}
      </section>

      {primary && (
        <ConservationPanel
          trajectory={primary.response.trajectory}
          drift={primary.response.drift_residuals}
        />
      )}
    </div>
  )
}

function Slider({ label, value, onChange, min, max, step, color }) {
  return (
    <div style={styles.sliderCell}>
      <label style={styles.sliderLabel}>
        {label}: <strong style={{ color }}>
          {Number(value).toFixed(step >= 1 ? 0 : 2)}
        </strong>
      </label>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        style={{ width: '100%', accentColor: color }} />
    </div>
  )
}

function SelectMetric({ value, onChange }) {
  return (
    <div style={styles.sliderCell}>
      <label style={styles.sliderLabel}>Metric</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}
        style={styles.select}>
        <option value="kerr">Kerr</option>
        <option value="schwarzschild">Schwarzschild</option>
      </select>
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
  presetRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: 12,
  },
  presetBtn: {
    display: 'flex', flexDirection: 'column', gap: 6,
    padding: '14px 16px',
    borderRadius: 10,
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.1)',
    color: '#e8e8f0',
    cursor: 'pointer',
    textAlign: 'left',
    transition: 'all 0.15s',
  },
  controlsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
    gap: 14,
    marginBottom: 8,
  },
  subSection: {
    fontSize: 11, color: '#c4b5fd',
    textTransform: 'uppercase', letterSpacing: 0.5,
    marginTop: 18, marginBottom: 10,
  },
  sliderCell: { display: 'flex', flexDirection: 'column' },
  sliderLabel: { fontSize: 12, color: '#c4b5fd', marginBottom: 6 },
  select: {
    padding: '6px 10px',
    borderRadius: 8,
    background: 'rgba(255,255,255,0.06)',
    color: '#e8e8f0',
    border: '1px solid rgba(255,255,255,0.15)',
    fontSize: 13,
  },
  actionRow: {
    display: 'flex', gap: 12, marginTop: 22, alignItems: 'center', flexWrap: 'wrap',
  },
  runBtn: {
    padding: '12px 24px',
    borderRadius: 22,
    background: 'linear-gradient(135deg, #ff6b9d, #00dfff)',
    color: '#fff',
    border: 'none',
    fontSize: 14, fontWeight: 600,
    cursor: 'pointer',
  },
  runBtnSec: {
    padding: '12px 24px',
    borderRadius: 22,
    background: 'rgba(34,197,94,0.15)',
    color: '#22c55e',
    border: '1px solid rgba(34,197,94,0.3)',
    fontSize: 13, fontWeight: 600,
    cursor: 'pointer',
  },
  btnDisabled: { opacity: 0.6, cursor: 'wait' },
  actionHint: { fontSize: 12, color: '#9ca3af' },
  errorBanner: {
    marginTop: 16,
    padding: '10px 16px',
    background: 'rgba(255,193,7,0.1)',
    border: '1px solid rgba(255,193,7,0.3)',
    borderRadius: 8,
    fontSize: 13, color: '#ffc107',
  },
  playRow: {
    display: 'flex', gap: 12, alignItems: 'center', marginTop: 16,
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
  legend: {
    display: 'flex', flexDirection: 'column', gap: 6, marginTop: 14,
  },
  legendItem: {
    display: 'flex', alignItems: 'center', gap: 10,
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.08)',
    padding: '6px 12px', borderRadius: 8,
  },
  legendSwatch: { width: 16, height: 4, borderRadius: 2 },
  legendText: { fontSize: 12, color: '#c4b5fd', fontFamily: 'monospace', flex: 1 },
  legendCloseBtn: {
    border: 'none', background: 'transparent', color: '#9ca3af',
    cursor: 'pointer', fontSize: 14, padding: 4,
  },
}
