/**
 * Kerr black hole page — first new physics surface added in v2.5.
 *
 * Two interactive sliders (M, a/M) drive a backend call to
 * /api/metrics/kerr that returns horizons, ergosphere(theta), ISCO
 * prograde + retrograde, photon sphere prograde + retrograde, Hawking T,
 * BH entropy, and the LaTeX line element.
 *
 * The 2D equatorial visualisation overlays:
 *   - inner horizon r_-
 *   - outer horizon r_+
 *   - ergosphere at the equator (= 2M, independent of a in equatorial plane)
 *   - ergosphere at the pole (= r_+, since cos²θ = 1)
 *   - ISCO prograde (closer to BH) and retrograde
 *   - photon sphere prograde and retrograde
 */

import { useEffect, useState } from 'react'
import { TexBlock, Tex } from '../components/Math'
import { api } from '../lib/api'

export default function Kerr() {
  const [mass, setMass] = useState(1.0)
  const [aOverM, setAOverM] = useState(0.7)
  const [props, setProps] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const spin = mass * aOverM

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    api.kerr
      .properties(mass, spin)
      .then((data) => {
        if (cancelled) return
        setProps(data)
        setError(null)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err.message)
        setProps(clientFallback(mass, spin))
      })
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [mass, spin])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 30 }}>
      <section style={styles.card}>
        <h2 style={styles.sectionTitle}>Kerr Black Hole</h2>
        <p style={styles.sectionDesc}>
          The two-parameter rotating vacuum solution. As <Tex>{'a / M'}</Tex>
          {' '}grows from 0 (Schwarzschild) toward 1 (extremal), the inner and
          outer horizons approach, the ergosphere bulges, and the ISCO splits
          into prograde and retrograde branches.
        </p>

        <div style={styles.formula}>
          <TexBlock>
            {'ds^2 = -\\left(1 - \\frac{2Mr}{\\Sigma}\\right) dt^2 - \\frac{4Mar\\sin^2\\theta}{\\Sigma} dt\\,d\\phi + \\frac{\\Sigma}{\\Delta} dr^2 + \\Sigma\\, d\\theta^2 + \\left(r^2 + a^2 + \\frac{2Ma^2 r \\sin^2\\theta}{\\Sigma}\\right) \\sin^2\\theta\\, d\\phi^2'}
          </TexBlock>
          <div style={styles.formulaCaption}>
            <Tex>{'\\Sigma \\equiv r^2 + a^2 \\cos^2\\theta'}</Tex>
            {' · '}
            <Tex>{'\\Delta \\equiv r^2 - 2Mr + a^2'}</Tex>
            {' · Boyer-Lindquist coordinates.'}
          </div>
        </div>

        <div style={styles.controls}>
          <div style={styles.controlGroup}>
            <label style={styles.label}>
              Mass M: <strong style={{ color: '#ff6b9d' }}>{mass.toFixed(2)}</strong>
            </label>
            <input
              type="range"
              min="0.5"
              max="3"
              step="0.05"
              value={mass}
              onChange={(e) => setMass(parseFloat(e.target.value))}
              style={styles.slider}
            />
          </div>

          <div style={styles.controlGroup}>
            <label style={styles.label}>
              Spin <Tex>{'a / M'}</Tex>:{' '}
              <strong style={{ color: '#00dfff' }}>{aOverM.toFixed(3)}</strong>
            </label>
            <input
              type="range"
              min="0"
              max="0.999"
              step="0.001"
              value={aOverM}
              onChange={(e) => setAOverM(parseFloat(e.target.value))}
              style={styles.slider}
            />
            <small style={styles.hint}>
              Cosmic censorship requires <Tex>{'|a| \\le M'}</Tex> · extremal at{' '}
              <Tex>{'a/M = 1'}</Tex>
            </small>
          </div>
        </div>

        {props && (
          <div style={styles.propertiesGrid}>
            <PropertyCard
              label="Outer horizon r₊"
              value={props.outer_horizon.toFixed(4)}
              formulaTex={'r_+ = M + \\sqrt{M^2 - a^2}'}
              color="#ff6b9d"
            />
            <PropertyCard
              label="Inner horizon r₋"
              value={props.inner_horizon.toFixed(4)}
              formulaTex={'r_- = M - \\sqrt{M^2 - a^2}'}
              color="#a78bfa"
            />
            <PropertyCard
              label="Ergosphere (equator)"
              value={props.ergo_equator.toFixed(4)}
              formulaTex={'r_E = 2M'}
              color="#00dfff"
            />
            <PropertyCard
              label="ISCO prograde"
              value={props.isco_prograde.toFixed(4)}
              formulaTex={'r_{\\rm ISCO}^+ \\le 6M'}
              color="#22c55e"
            />
            <PropertyCard
              label="ISCO retrograde"
              value={props.isco_retrograde.toFixed(4)}
              formulaTex={'r_{\\rm ISCO}^- \\ge 6M'}
              color="#f59e0b"
            />
            <PropertyCard
              label="Photon sphere (+)"
              value={props.photon_sphere_prograde.toFixed(4)}
              formulaTex={'r_\\gamma^+'}
              color="#00dfff"
            />
            <PropertyCard
              label="Horizon ang. velocity"
              value={props.angular_velocity_horizon.toExponential(3)}
              formulaTex={'\\Omega_H = \\frac{a}{r_+^2 + a^2}'}
              color="#c4b5fd"
            />
            <PropertyCard
              label="Hawking T"
              value={props.hawking_temperature.toExponential(3)}
              formulaTex={'T_H = \\frac{r_+ - r_-}{4\\pi(r_+^2 + a^2)}'}
              color="#fb923c"
            />
            <PropertyCard
              label="BH Entropy"
              value={props.bekenstein_hawking_entropy.toFixed(3)}
              formulaTex={'S = \\pi(r_+^2 + a^2)'}
              color="#ff6b9d"
            />
          </div>
        )}

        <div style={styles.visualBox}>
          <KerrEquatorialPlot props={props} mass={mass} />
        </div>

        {loading && <div style={styles.statusBanner}>Loading…</div>}
        {error && (
          <div style={styles.errorBanner}>
            ⚠️ Using client-side fallback (API: {error})
          </div>
        )}
      </section>

      <section style={styles.card}>
        <h3 style={{ margin: 0, color: '#fff' }}>What changes as you spin it up?</h3>
        <ul style={styles.bulletList}>
          <li>
            At <Tex>{'a = 0'}</Tex>: Schwarzschild — both horizons meet at{' '}
            <Tex>{'r = 2M'}</Tex>, ISCO = <Tex>{'6M'}</Tex>, ergosphere collapses
            onto the horizon.
          </li>
          <li>
            For <Tex>{'0 < a < M'}</Tex>: <Tex>{'r_+'}</Tex> shrinks from{' '}
            <Tex>{'2M'}</Tex> down to <Tex>{'M'}</Tex>; <Tex>{'r_-'}</Tex> grows
            from 0 up to <Tex>{'M'}</Tex>; the ergosphere{' '}
            <Tex>{'(r_E = 2M)'}</Tex> separates from <Tex>{'r_+'}</Tex>.
          </li>
          <li>
            ISCO splits: prograde shrinks down to <Tex>{'M'}</Tex> at extremal
            (energy efficiency 42%), retrograde grows toward <Tex>{'9M'}</Tex>.
          </li>
          <li>
            Hawking <Tex>{'T_H \\to 0'}</Tex> as <Tex>{'a \\to M'}</Tex>:
            extremal Kerr is a zero-temperature black hole (third law).
          </li>
        </ul>
        <p style={styles.cite}>
          Reference: Boyer & Lindquist 1967; Bardeen, Press & Teukolsky 1972;
          Wald, <em>General Relativity</em>, ch. 12.
        </p>
      </section>
    </div>
  )
}

function PropertyCard({ label, value, formulaTex, color }) {
  return (
    <div style={{ ...styles.property, borderTop: `2px solid ${color}` }}>
      <div style={styles.propertyLabel}>{label}</div>
      <div style={{ ...styles.propertyValue, color }}>{value}</div>
      <div style={styles.propertyFormula}>
        <TexBlock>{formulaTex}</TexBlock>
      </div>
    </div>
  )
}

function KerrEquatorialPlot({ props, mass }) {
  const size = 460
  const cx = size / 2
  const cy = size / 2
  // Scale so the largest feature (ISCO retrograde, max ~9M) fits comfortably
  const maxR = props ? Math.max(props.isco_retrograde, 9 * mass) : 9 * mass
  const scale = (size / 2 - 30) / maxR

  if (!props) {
    return (
      <svg width={size} height={size} style={{ background: '#0a0a0f' }}>
        <text x={cx} y={cy} fill="#6b7280" fontSize="13" textAnchor="middle">
          loading…
        </text>
      </svg>
    )
  }

  const r_plus = props.outer_horizon * scale
  const r_minus = props.inner_horizon * scale
  const r_ergo = props.ergo_equator * scale
  const isco_pro = props.isco_prograde * scale
  const isco_retro = props.isco_retrograde * scale
  const ph_pro = props.photon_sphere_prograde * scale

  return (
    <svg width={size} height={size} style={{ background: '#0a0a0f', borderRadius: 12 }}>
      <defs>
        <radialGradient id="kerr-bh">
          <stop offset="0%" stopColor="#000" />
          <stop offset="85%" stopColor="#1a0a1a" />
          <stop offset="100%" stopColor="#4a1a4a" />
        </radialGradient>
        <radialGradient id="ergo-fill" cx="50%" cy="50%">
          <stop offset={`${(r_plus / r_ergo) * 100}%`} stopColor="rgba(0,223,255,0)" />
          <stop offset="100%" stopColor="rgba(0,223,255,0.18)" />
        </radialGradient>
      </defs>

      {/* ISCO retrograde */}
      <circle cx={cx} cy={cy} r={isco_retro} fill="none"
        stroke="#f59e0b" strokeWidth="1" strokeDasharray="6 6" opacity="0.6" />
      <text x={cx + isco_retro + 4} y={cy - 5} fill="#f59e0b" fontSize="10">ISCO−</text>

      {/* ISCO prograde */}
      <circle cx={cx} cy={cy} r={isco_pro} fill="none"
        stroke="#22c55e" strokeWidth="1" strokeDasharray="4 4" opacity="0.7" />
      <text x={cx + isco_pro + 4} y={cy + 11} fill="#22c55e" fontSize="10">ISCO+</text>

      {/* Photon sphere prograde */}
      <circle cx={cx} cy={cy} r={ph_pro} fill="none"
        stroke="#00dfff" strokeWidth="1" strokeDasharray="2 3" opacity="0.7" />

      {/* Ergosphere fill — the "static limit" annulus between r_+ and r_ergo */}
      <circle cx={cx} cy={cy} r={r_ergo} fill="url(#ergo-fill)" />
      <circle cx={cx} cy={cy} r={r_ergo} fill="none"
        stroke="#00dfff" strokeWidth="1.5" opacity="0.85" />
      <text x={cx + r_ergo - 4} y={cy + 24} fill="#00dfff" fontSize="10" textAnchor="end">
        ergo r=2M
      </text>

      {/* Outer horizon r_+ */}
      <circle cx={cx} cy={cy} r={r_plus} fill="url(#kerr-bh)"
        stroke="#ff6b9d" strokeWidth="2" />
      <text x={cx + r_plus + 4} y={cy + 38} fill="#ff6b9d" fontSize="10">r₊</text>

      {/* Inner horizon r_- (Cauchy) */}
      <circle cx={cx} cy={cy} r={r_minus} fill="none"
        stroke="#a78bfa" strokeWidth="1" strokeDasharray="3 3" opacity="0.85" />
      {r_minus > 6 && (
        <text x={cx + r_minus + 4} y={cy + 50} fill="#a78bfa" fontSize="10">r₋</text>
      )}

      {/* Singularity (ring) */}
      <circle cx={cx} cy={cy} r="2" fill="#fff" />

      {/* Title */}
      <text x={cx} y={size - 10} fill="#6b7280" fontSize="11" textAnchor="middle">
        Equatorial slice (θ = π/2)
      </text>
    </svg>
  )
}

function clientFallback(M, a) {
  // Closed-form fallback if backend is down. All formulae from Wald 1984.
  const sqrtDisc = Math.sqrt(Math.max(M * M - a * a, 0))
  const r_plus = M + sqrtDisc
  const r_minus = M - sqrtDisc
  // ISCO closed form (Bardeen-Press-Teukolsky 1972)
  const Z1 = 1 + Math.cbrt(1 - (a / M) ** 2) *
             (Math.cbrt(1 + a / M) + Math.cbrt(1 - a / M))
  const Z2 = Math.sqrt(3 * (a / M) ** 2 + Z1 * Z1)
  const isco_prograde = M * (3 + Z2 - Math.sqrt((3 - Z1) * (3 + Z1 + 2 * Z2)))
  const isco_retrograde = M * (3 + Z2 + Math.sqrt((3 - Z1) * (3 + Z1 + 2 * Z2)))
  // Photon sphere prograde (closed form, see Bardeen 1972)
  const ph_pro = 2 * M * (1 + Math.cos(2 / 3 * Math.acos(-a / M)))
  return {
    mass: M,
    spin: a,
    outer_horizon: r_plus,
    inner_horizon: r_minus,
    ergo_equator: 2 * M,
    isco_prograde,
    isco_retrograde,
    photon_sphere_prograde: ph_pro,
    angular_velocity_horizon: a / (r_plus * r_plus + a * a),
    hawking_temperature: (r_plus - r_minus) /
      (4 * Math.PI * (r_plus * r_plus + a * a)),
    bekenstein_hawking_entropy: Math.PI * (r_plus * r_plus + a * a),
  }
}

const styles = {
  card: {
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 16,
    padding: 32,
  },
  sectionTitle: { fontSize: 24, margin: '0 0 8px', color: '#fff' },
  sectionDesc: { fontSize: 14, color: '#9ca3af', marginBottom: 24, lineHeight: 1.6 },
  formula: {
    background: 'rgba(0,223,255,0.05)',
    border: '1px solid rgba(0,223,255,0.15)',
    borderRadius: 10,
    padding: '14px 20px',
    marginBottom: 24,
    overflowX: 'auto',
  },
  formulaCaption: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 10,
    fontFamily: 'monospace',
  },
  controls: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 24,
    marginBottom: 24,
  },
  controlGroup: { display: 'flex', flexDirection: 'column' },
  label: { fontSize: 13, marginBottom: 8, color: '#c4b5fd' },
  slider: { width: '100%', accentColor: '#ff6b9d' },
  hint: { fontSize: 11, color: '#6b7280', marginTop: 6 },
  propertiesGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: 14,
    marginBottom: 24,
  },
  property: {
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 10,
    padding: 14,
  },
  propertyLabel: {
    fontSize: 11,
    color: '#9ca3af',
    textTransform: 'uppercase',
    letterSpacing: 0.4,
    marginBottom: 6,
  },
  propertyValue: { fontSize: 18, fontWeight: 700, fontFamily: 'monospace', marginBottom: 4 },
  propertyFormula: { fontSize: 11, marginBottom: 4 },
  visualBox: { display: 'flex', justifyContent: 'center', padding: '16px 0' },
  statusBanner: {
    padding: '8px 14px',
    background: 'rgba(0,223,255,0.08)',
    border: '1px solid rgba(0,223,255,0.2)',
    borderRadius: 8,
    fontSize: 12,
    color: '#00dfff',
    marginTop: 12,
  },
  errorBanner: {
    padding: '10px 16px',
    background: 'rgba(255,193,7,0.1)',
    border: '1px solid rgba(255,193,7,0.3)',
    borderRadius: 8,
    fontSize: 13,
    color: '#ffc107',
    marginTop: 16,
  },
  bulletList: {
    fontSize: 14,
    color: '#c4b5fd',
    lineHeight: 1.8,
    paddingLeft: 20,
    marginTop: 14,
  },
  cite: {
    fontSize: 11,
    color: '#6b7280',
    marginTop: 16,
    fontStyle: 'italic',
  },
}
