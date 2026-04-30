/**
 * Kerr-Newman page — second metric of v3.2.
 *
 * Three sliders: M, a/M, |Q|/M.  Cosmic censorship (a/M)² + (Q/M)² ≤ 1
 * enforced by clamping the slider product live (we just disable the
 * Integrate button if the user crosses the line; we DON'T silently
 * rescale — the user should see they hit the boundary).
 */

import { useEffect, useState } from 'react'
import { TexBlock, Tex } from '../components/Math'
import { api } from '../lib/api'

export default function KerrNewman() {
  const [mass, setMass] = useState(1.0)
  const [aOverM, setAOverM] = useState(0.5)
  const [qOverM, setQOverM] = useState(0.3)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const spin = mass * aOverM
  const charge = mass * qOverM
  const censorshipMargin = 1.0 - (aOverM * aOverM + qOverM * qOverM)
  const violatesCensorship = censorshipMargin < -1e-9

  useEffect(() => {
    if (violatesCensorship) {
      setData(null)
      setError(`(a/M)² + (Q/M)² = ${(aOverM ** 2 + qOverM ** 2).toFixed(4)} > 1 — naked singularity, request blocked`)
      return
    }
    let cancelled = false
    setLoading(true)
    api.kerrNewman.properties(mass, spin, charge)
      .then((d) => !cancelled && (setData(d), setError(null)))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false))
    return () => { cancelled = true }
  }, [mass, spin, charge, violatesCensorship, aOverM, qOverM])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 30 }}>
      <section style={styles.card}>
        <h2 style={styles.title}>Kerr-Newman Black Hole</h2>
        <p style={styles.lede}>
          The two-charge generalisation of Kerr — the unique stationary,
          axisymmetric, asymptotically-flat solution of the
          Einstein-Maxwell equations sourced by a point mass with both
          spin and electric charge (Newman et al. 1965).  Reduces to
          Kerr at <Tex>{'Q = 0'}</Tex>, to RN at <Tex>{'a = 0'}</Tex>,
          to Schwarzschild at both.
        </p>

        <div style={styles.formula}>
          <TexBlock>
            {'\\Sigma = r^2 + a^2 \\cos^2\\theta, \\quad \\Delta = r^2 - 2Mr + a^2 + Q^2'}
          </TexBlock>
          <div style={styles.formulaCaption}>
            Boyer-Lindquist; the only thing Q changes vs. Kerr is the
            extra <Tex>{'+Q^2'}</Tex> in <Tex>{'\\Delta'}</Tex>.
          </div>
        </div>

        <div style={styles.controls}>
          <ControlSlider label={<>Mass <Tex>{'M'}</Tex></>} color="#ff6b9d"
            value={mass} onChange={setMass} min={0.5} max={3} step={0.05} />
          <ControlSlider label={<>Spin <Tex>{'a/M'}</Tex></>} color="#00dfff"
            value={aOverM} onChange={setAOverM} min={0} max={0.999} step={0.005} />
          <ControlSlider label={<>Charge <Tex>{'|Q|/M'}</Tex></>} color="#fbbf24"
            value={qOverM} onChange={setQOverM} min={0} max={0.999} step={0.005} />
        </div>

        <div style={{
          ...styles.censorshipBar,
          color: violatesCensorship ? '#ef4444' : censorshipMargin < 0.05 ? '#fbbf24' : '#22c55e',
        }}>
          Cosmic-censorship margin <Tex>{'1 - (a/M)^2 - (Q/M)^2'}</Tex>:{' '}
          <code>{censorshipMargin.toFixed(6)}</code>
          {violatesCensorship && ' — VIOLATED (naked singularity)'}
          {!violatesCensorship && censorshipMargin < 0.05 && ' — near extremal'}
        </div>

        {data && (
          <div style={styles.propsGrid}>
            <Prop label="Outer horizon r₊" value={data.outer_horizon.toFixed(4)}
              tex={'r_+ = M + \\sqrt{M^2 - a^2 - Q^2}'} color="#ff6b9d" />
            <Prop label="Inner horizon r₋" value={data.inner_horizon.toFixed(4)}
              tex={'r_- = M - \\sqrt{M^2 - a^2 - Q^2}'} color="#a78bfa" />
            <Prop label="Ergo equator" value={data.ergo_equator.toFixed(4)}
              tex={'r_E(\\pi/2) = M + \\sqrt{M^2 - Q^2}'} color="#00dfff" />
            <Prop label="Ergo pole" value={data.ergo_pole.toFixed(4)}
              tex={'r_E(0) = r_+'} color="#06b6d4" />
            <Prop label="Ω_H" value={data.angular_velocity_horizon.toExponential(3)}
              tex={'\\Omega_H = \\frac{a}{r_+^2 + a^2}'} color="#c4b5fd" />
            <Prop label="Hawking T" value={data.hawking_temperature.toExponential(3)}
              tex={'T_H = \\frac{r_+ - r_-}{4\\pi(r_+^2 + a^2)}'} color="#fb923c" />
            <Prop label="BH entropy" value={data.bekenstein_hawking_entropy.toFixed(3)}
              tex={'S = \\pi(r_+^2 + a^2)'} color="#22c55e" />
            <Prop label="Vieta r₊r₋" value={(data.outer_horizon * data.inner_horizon).toFixed(6)}
              tex={'r_+ r_- = a^2 + Q^2'}
              color={Math.abs(data.outer_horizon * data.inner_horizon - (spin * spin + charge * charge)) < 1e-9 ? '#22c55e' : '#fb923c'} />
            <Prop label="Extremal?" value={data.is_extremal ? 'YES' : 'no'}
              tex={'a^2 + Q^2 = M^2'} color={data.is_extremal ? '#ef4444' : '#9ca3af'} />
          </div>
        )}

        {loading && <div style={styles.statusBanner}>Loading…</div>}
        {error && <div style={styles.errorBanner}>⚠️ {error}</div>}
      </section>

      <section style={styles.card}>
        <h3 style={{ margin: 0, color: '#fff' }}>Three limits, one metric</h3>
        <ul style={styles.bulletList}>
          <li>
            <strong>Schwarzschild</strong> (<Tex>{'a=0, Q=0'}</Tex>):{' '}
            <Tex>{'r_+ = 2M'}</Tex>, no ergosphere, no Cauchy horizon.
          </li>
          <li>
            <strong>Kerr</strong> (<Tex>{'Q=0'}</Tex>): the page already
            exists at <code>/kerr</code>; this page reproduces it bit-exactly
            when you slide <Tex>{'|Q|/M'}</Tex> to 0.
          </li>
          <li>
            <strong>Reissner-Nordström</strong> (<Tex>{'a=0'}</Tex>): the page
            at <code>/reissner-nordstrom</code>; this page reproduces it
            bit-exactly when you slide <Tex>{'a/M'}</Tex> to 0.
          </li>
          <li>
            <strong>Both</strong>: <Tex>{'r_+ + r_- = 2M'}</Tex>,{' '}
            <Tex>{'r_+ r_- = a^2 + Q^2'}</Tex> (3-parameter Vieta's
            generalisation; "Vieta r₊r₋" card above checks it client-side).
          </li>
          <li>
            <strong>Extremal</strong> (<Tex>{'a^2 + Q^2 = M^2'}</Tex>):
            horizons merge at <Tex>{'r = M'}</Tex>, <Tex>{'T_H = 0'}</Tex>{' '}
            (third law).
          </li>
        </ul>
        <p style={styles.cite}>
          Reference: Newman et al., <em>J. Math. Phys.</em> 6, 918 (1965)
          — "Metric of a rotating, charged mass".  Wald §12.3.  Bit-exact
          tests pin all three limits in <code>tests/test_kerr_newman.py</code>.
        </p>
        <p style={styles.cite}>
          ISCO closed form (Aliev-Galtsov 1981) deferred to v3.2.1 — the
          polynomial is genuinely gnarly.  Kerr's ISCO endpoints
          (<code>/api/metrics/kerr</code>) cover the <Tex>{'Q=0'}</Tex>{' '}
          slice, and RN's (<code>/api/metrics/reissner-nordstrom</code>)
          cover the <Tex>{'a=0'}</Tex> slice.
        </p>
      </section>
    </div>
  )
}

function ControlSlider({ label, value, onChange, min, max, step, color }) {
  return (
    <div style={styles.controlGroup}>
      <label style={styles.controlLabel}>
        {label}: <strong style={{ color }}>{value.toFixed(3)}</strong>
      </label>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        style={{ width: '100%', accentColor: color }} />
    </div>
  )
}

function Prop({ label, value, tex, color }) {
  return (
    <div style={{ ...styles.prop, borderTop: `2px solid ${color}` }}>
      <div style={styles.propLabel}>{label}</div>
      <div style={{ ...styles.propValue, color }}>{value}</div>
      <div style={styles.propTex}><TexBlock>{tex}</TexBlock></div>
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
  lede: { fontSize: 14, color: '#9ca3af', marginBottom: 24, lineHeight: 1.6 },
  formula: {
    background: 'rgba(0,223,255,0.05)',
    border: '1px solid rgba(0,223,255,0.15)',
    borderRadius: 10,
    padding: '14px 20px',
    marginBottom: 24,
    overflowX: 'auto',
  },
  formulaCaption: { fontSize: 12, color: '#9ca3af', marginTop: 10 },
  controls: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: 18,
    marginBottom: 14,
  },
  controlGroup: { display: 'flex', flexDirection: 'column' },
  controlLabel: { fontSize: 13, marginBottom: 8, color: '#c4b5fd' },
  censorshipBar: {
    fontSize: 12,
    fontFamily: 'monospace',
    padding: '8px 14px',
    background: 'rgba(255,255,255,0.04)',
    borderRadius: 8,
    marginBottom: 22,
  },
  propsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: 14,
  },
  prop: {
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 10,
    padding: 14,
  },
  propLabel: {
    fontSize: 11, color: '#9ca3af',
    textTransform: 'uppercase', letterSpacing: 0.4, marginBottom: 6,
  },
  propValue: { fontSize: 18, fontWeight: 700, fontFamily: 'monospace', marginBottom: 4 },
  propTex: { fontSize: 11 },
  statusBanner: {
    padding: '8px 14px',
    background: 'rgba(0,223,255,0.08)',
    border: '1px solid rgba(0,223,255,0.2)',
    borderRadius: 8,
    fontSize: 12, color: '#00dfff', marginTop: 12,
  },
  errorBanner: {
    padding: '10px 16px',
    background: 'rgba(239,68,68,0.1)',
    border: '1px solid rgba(239,68,68,0.3)',
    borderRadius: 8,
    fontSize: 13, color: '#ef4444', marginTop: 12,
  },
  bulletList: { fontSize: 14, color: '#c4b5fd', lineHeight: 1.8, paddingLeft: 20, marginTop: 14 },
  cite: { fontSize: 11, color: '#6b7280', marginTop: 12, fontStyle: 'italic' },
}
