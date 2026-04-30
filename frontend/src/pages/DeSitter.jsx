/**
 * de Sitter page — partial v3.2 (FLRW general case still deferred).
 *
 * Single slider (L).  All quantities closed form, so the page is the
 * simplest in the lab — no fallbacks, no error paths beyond network.
 */

import { useEffect, useState } from 'react'
import { TexBlock, Tex } from '../components/Math'

const API = import.meta.env.VITE_API_URL || ''

export default function DeSitter() {
  const [radius, setRadius] = useState(1.0)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetch(`${API}/api/metrics/de-sitter?radius=${radius}`)
      .then((r) => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)))
      .then((d) => !cancelled && (setData(d), setError(null)))
      .catch((e) => !cancelled && setError(e.message))
    return () => { cancelled = true }
  }, [radius])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 30 }}>
      <section style={styles.card}>
        <h2 style={styles.title}>de Sitter spacetime</h2>
        <p style={styles.lede}>
          The unique maximally-symmetric vacuum solution of Einstein
          with positive cosmological constant <Tex>{'\\Lambda > 0'}</Tex>.
          Static patch coordinates show a *cosmological* event horizon at
          <Tex>{' r = L = \\sqrt{3/\\Lambda} '}</Tex> — analogous in form
          to Schwarzschild's BH horizon, but the metric is regular at the
          centre and the horizon is observer-dependent (each observer's
          past light cone has its own).
        </p>

        <div style={styles.formula}>
          <TexBlock>
            {'ds^2 = -\\left(1 - \\frac{r^2}{L^2}\\right) dt^2 + \\left(1 - \\frac{r^2}{L^2}\\right)^{-1} dr^2 + r^2 \\, d\\Omega^2'}
          </TexBlock>
        </div>

        <div style={styles.controlGroup}>
          <label style={styles.controlLabel}>
            de Sitter radius <Tex>{'L'}</Tex>:{' '}
            <strong style={{ color: '#00dfff' }}>{radius.toFixed(2)}</strong>
          </label>
          <input
            type="range" min="0.5" max="5" step="0.05" value={radius}
            onChange={(e) => setRadius(parseFloat(e.target.value))}
            style={{ width: '100%', accentColor: '#00dfff' }}
          />
          <small style={styles.hint}>
            <Tex>{'L = 1/H = \\sqrt{3/\\Lambda}'}</Tex> — three equivalent
            ways to think about it
          </small>
        </div>

        {data && (
          <div style={styles.propsGrid}>
            <Prop label="Cosmological horizon r_c"
              value={data.cosmological_horizon.toFixed(4)}
              tex={'r_c = L'} color="#ff6b9d" />
            <Prop label="Cosmological constant Λ"
              value={data.cosmological_constant.toFixed(4)}
              tex={'\\Lambda = 3/L^2'} color="#a78bfa" />
            <Prop label="Hubble parameter H"
              value={data.hubble_parameter.toFixed(4)}
              tex={'H = 1/L = \\sqrt{\\Lambda/3}'} color="#22c55e" />
            <Prop label="Gibbons-Hawking T"
              value={data.hawking_temperature.toExponential(3)}
              tex={'T_{GH} = \\frac{1}{2\\pi L}'} color="#fbbf24" />
            <Prop label="Horizon area A"
              value={data.horizon_area.toFixed(3)}
              tex={'A = 4\\pi L^2'} color="#06b6d4" />
            <Prop label="Bekenstein-Hawking S"
              value={data.bekenstein_hawking_entropy.toFixed(3)}
              tex={'S = \\pi L^2'} color="#fb923c" />
            <Prop label="Ricci scalar R"
              value={data.ricci_scalar.toFixed(3)}
              tex={'R = 12/L^2 = 4\\Lambda'} color="#c4b5fd" />
          </div>
        )}

        {error && <div style={styles.errorBanner}>⚠️ {error}</div>}
      </section>

      <section style={styles.card}>
        <h3 style={{ margin: 0, color: '#fff' }}>What's special about dS</h3>
        <ul style={styles.bulletList}>
          <li>
            <strong>Constant-curvature</strong>: <Tex>{'R = 12/L^2'}</Tex>{' '}
            everywhere; both the Ricci tensor and Riemann tensor are
            proportional to combinations of <Tex>{'g_{\\mu\\nu}'}</Tex>.
          </li>
          <li>
            <strong>Cosmological horizon</strong>: every observer sees a
            horizon at proper distance <Tex>{'L = 1/H'}</Tex>.  It is NOT
            a BH — there's no singularity inside, no ergosphere, no ISCO.
          </li>
          <li>
            <strong>Gibbons-Hawking radiation</strong> (1977): the
            horizon emits thermal radiation at <Tex>{'T_{GH} = 1/(2\\pi L)'}</Tex>{' '}
            — the cosmological analogue of Hawking radiation from a BH
            horizon.
          </li>
          <li>
            <strong>Bekenstein-Hawking entropy of a horizon you don't
            own</strong>: <Tex>{'S = A/4 = \\pi L^2'}</Tex>.  Holds even
            though no matter has fallen across this horizon — entropy
            from observer-dependent ignorance.
          </li>
          <li>
            <strong>Limit of FLRW with</strong> <Tex>{'w = -1'}</Tex>:
            an FLRW universe dominated by Λ asymptotes to dS.  Our late-
            ΛCDM universe is approximately dS.
          </li>
        </ul>
        <p style={styles.cite}>
          Reference: Wald §5.2; Hawking & Ellis §5.2; Gibbons & Hawking,{' '}
          <em>Phys. Rev. D</em> 15, 2738 (1977).  Bit-exact tests pin
          all closed-form invariants to ≤ 1e-12 in{' '}
          <code>tests/test_de_sitter.py</code>.
        </p>
        <p style={styles.cite}>
          General FLRW (with arbitrary equation of state, mixed matter
          components, Friedmann ODE) deferred to v3.2.full — see{' '}
          <code>docs/v3.2-flrw-de-sitter-spec.md</code>.  This page covers
          the closed-form Λ-only "easy half".
        </p>
      </section>
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
  controlGroup: { marginBottom: 24 },
  controlLabel: { display: 'block', fontSize: 13, marginBottom: 8, color: '#c4b5fd' },
  hint: { display: 'block', fontSize: 11, color: '#6b7280', marginTop: 6 },
  propsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
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
  errorBanner: {
    padding: '10px 16px',
    background: 'rgba(239,68,68,0.1)',
    border: '1px solid rgba(239,68,68,0.3)',
    borderRadius: 8,
    fontSize: 13, color: '#ef4444', marginTop: 16,
  },
  bulletList: { fontSize: 14, color: '#c4b5fd', lineHeight: 1.8, paddingLeft: 20, marginTop: 14 },
  cite: { fontSize: 11, color: '#6b7280', marginTop: 14, fontStyle: 'italic' },
}
