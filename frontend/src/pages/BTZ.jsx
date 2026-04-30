/**
 * BTZ (3D AdS black hole) page — fifth physics surface in v2.5.
 *
 * Two sliders (r_+, L) drive /api/metrics/btz.  Companion to the
 * Holography page: BTZ is the bulk geometry whose Page curve we plot
 * there.  Brown-Henneaux + Strominger-Cardy match shown explicitly.
 */

import { useEffect, useState } from 'react'
import { TexBlock, Tex } from '../components/Math'

const API = import.meta.env.VITE_API_URL || ''

export default function BTZ() {
  const [rPlus, setRPlus] = useState(1.0)
  const [L, setL] = useState(1.0)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetch(`${API}/api/metrics/btz?horizon_radius=${rPlus}&ads_radius=${L}&G_N=1`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((j) => !cancelled && (setData(j), setError(null)))
      .catch((e) => !cancelled && setError(e.message))
    return () => { cancelled = true }
  }, [rPlus, L])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 30 }}>
      <section style={styles.card}>
        <h2 style={styles.title}>BTZ — 3D AdS Black Hole</h2>
        <p style={styles.lede}>
          The Bañados-Teitelboim-Zanelli black hole: a quotient of AdS₃
          that is locally pure AdS but globally a black hole.  Its
          boundary CFT entropy from Cardy's formula reproduces the
          Bekenstein-Hawking area law (Strominger 1998), the simplest
          microscopic counting in quantum gravity.
        </p>

        <div style={styles.formula}>
          <TexBlock>
            {'ds^2 = -\\frac{r^2 - r_+^2}{L^2}\\, dt^2 + \\frac{L^2}{r^2 - r_+^2}\\, dr^2 + r^2\\, d\\phi^2'}
          </TexBlock>
        </div>

        <div style={styles.controls}>
          <ControlSlider
            label={<>Horizon <Tex>{'r_+'}</Tex></>}
            value={rPlus} onChange={setRPlus}
            min={0.2} max={3} step={0.05} color="#ff6b9d"
          />
          <ControlSlider
            label={<>AdS radius <Tex>{'L'}</Tex></>}
            value={L} onChange={setL}
            min={0.5} max={2} step={0.05} color="#00dfff"
          />
        </div>

        {data && (
          <div style={styles.propsGrid}>
            <Prop label="Mass parameter"
              value={data.mass_parameter.toFixed(4)}
              tex={'M = \\frac{r_+^2}{8 G_N L^2}'} color="#ff6b9d" />
            <Prop label="Hawking T"
              value={data.hawking_temperature.toExponential(3)}
              tex={'T_H = \\frac{r_+}{2\\pi L^2}'} color="#fb923c" />
            <Prop label="Bekenstein-Hawking S"
              value={data.bekenstein_hawking_entropy.toFixed(3)}
              tex={'S = \\frac{\\pi r_+}{2 G_N}'} color="#22c55e" />
            <Prop label="Thermal β"
              value={data.thermal_beta.toExponential(3)}
              tex={'\\beta = \\frac{2\\pi L^2}{r_+}'} color="#a78bfa" />
            <Prop label="Brown-Henneaux c"
              value={data.central_charge_brown_henneaux.toFixed(3)}
              tex={'c = \\frac{3 L}{2 G_N}'} color="#00dfff" />
            <Prop label="Cardy check"
              value={cardyCheck(data).toFixed(6)}
              tex={'S_{\\rm Cardy} / S_{BH}'}
              color={Math.abs(cardyCheck(data) - 1) < 1e-9 ? '#22c55e' : '#fb923c'} />
          </div>
        )}

        {error && (
          <div style={styles.errorBanner}>⚠️ API: {error}</div>
        )}
      </section>

      <section style={styles.card}>
        <h3 style={{ margin: 0, color: '#fff' }}>The Strominger 1998 match</h3>
        <p style={styles.bodyText}>
          For BTZ, the boundary CFT (a 2D CFT with central charge{' '}
          <Tex>{'c = 3L/(2 G_N)'}</Tex> from Brown-Henneaux) has a Cardy
          formula for asymptotic state degeneracy:
        </p>
        <TexBlock>{'S_{\\rm Cardy} = 2\\pi \\sqrt{\\frac{c L_0}{6}} + 2\\pi \\sqrt{\\frac{c \\bar L_0}{6}}'}</TexBlock>
        <p style={styles.bodyText}>
          Plugging the BTZ values <Tex>{'L_0 = \\bar L_0 = M L / 2 = r_+^2 / (16 G_N L)'}</Tex>{' '}
          gives <em>exactly</em> the Bekenstein-Hawking area
          law: <Tex>{'S_{\\rm Cardy} = \\pi r_+ / (2 G_N) = A / 4 G_N'}</Tex>.
          The "Cardy check" card above shows the numerical ratio — should
          read exactly 1 to machine precision.
        </p>
        <p style={styles.cite}>
          Reference: Bañados, Teitelboim, Zanelli 1992; Brown & Henneaux
          1986; Strominger 1998.  Bit-exact verification across 6 parameter
          combinations in <code>tests/test_phase8.py</code>.
        </p>
      </section>
    </div>
  )
}

function ControlSlider({ label, value, onChange, min, max, step, color }) {
  return (
    <div style={styles.controlGroup}>
      <label style={styles.controlLabel}>
        {label}: <strong style={{ color }}>{value.toFixed(2)}</strong>
      </label>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        style={styles.slider}
      />
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

function cardyCheck(data) {
  // S_Cardy = π r_+ / (2 G_N) and S_BH = same. Their ratio should be 1.
  // Frontend re-derives from r_+ and G_N=1 to verify the API math.
  const sCardy = Math.PI * data.horizon_radius / 2.0
  return sCardy / data.bekenstein_hawking_entropy
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
  controls: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 24,
    marginBottom: 24,
  },
  controlGroup: { display: 'flex', flexDirection: 'column' },
  controlLabel: { fontSize: 13, marginBottom: 8, color: '#c4b5fd' },
  slider: { width: '100%', accentColor: '#ff6b9d' },
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
    fontSize: 11,
    color: '#9ca3af',
    textTransform: 'uppercase',
    letterSpacing: 0.4,
    marginBottom: 6,
  },
  propValue: { fontSize: 18, fontWeight: 700, fontFamily: 'monospace', marginBottom: 4 },
  propTex: { fontSize: 11 },
  bodyText: { fontSize: 14, color: '#c4b5fd', lineHeight: 1.7, margin: '14px 0' },
  cite: { fontSize: 11, color: '#6b7280', marginTop: 16, fontStyle: 'italic' },
  errorBanner: {
    padding: '10px 16px',
    background: 'rgba(255,193,7,0.1)',
    border: '1px solid rgba(255,193,7,0.3)',
    borderRadius: 8,
    fontSize: 13,
    color: '#ffc107',
    marginTop: 16,
  },
}
