/**
 * Reissner-Nordström page — first surface of v3.1.
 *
 * Two sliders (M, |Q|/M).  Cosmic censorship enforced at the slider
 * range so the user can't request |Q| > M.  Live readouts of horizons
 * (outer, inner), photon sphere, ISCO, Hawking T, BH entropy.
 */

import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { TexBlock, Tex } from '../components/Math'
import { api } from '../lib/api'

export default function ReissnerNordstrom() {
  const { t } = useTranslation()
  const [mass, setMass] = useState(1.0)
  const [qOverM, setQOverM] = useState(0.6)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const charge = mass * qOverM

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    api.reissnerNordstrom
      .properties(mass, charge)
      .then((d) => !cancelled && (setData(d), setError(null)))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false))
    return () => { cancelled = true }
  }, [mass, charge])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 30 }}>
      <section style={styles.card}>
        <h2 style={styles.title}>{t('rn.title')}</h2>
        <p style={styles.lede}>
          {t('rn.desc_pre')}<Tex>{'|Q|/M'}</Tex>{t('rn.desc_post')}
        </p>

        <div style={styles.formula}>
          <TexBlock>
            {'ds^2 = -\\left(1 - \\frac{2M}{r} + \\frac{Q^2}{r^2}\\right) dt^2 + \\left(1 - \\frac{2M}{r} + \\frac{Q^2}{r^2}\\right)^{-1} dr^2 + r^2 \\, d\\Omega^2'}
          </TexBlock>
        </div>

        <div style={styles.controls}>
          <ControlSlider
            label={<>{t('rn.mass_label_pre')}<Tex>{'M'}</Tex></>} color="#ff6b9d"
            value={mass} onChange={setMass}
            min={0.5} max={3} step={0.05}
          />
          <ControlSlider
            label={<>{t('rn.qm_label_pre')}<Tex>{'|Q|/M'}</Tex></>} color="#fbbf24"
            value={qOverM} onChange={setQOverM}
            min={0} max={0.999} step={0.005}
            hint={<>{t('rn.qm_hint_pre')}<Tex>{'|Q| \\le M'}</Tex>{t('rn.qm_hint_mid')}<Tex>{'|Q|/M = 1'}</Tex></>}
          />
        </div>

        {data && (
          <div style={styles.propsGrid}>
            <Prop label={t('rn.props.outer_horizon')}
              value={data.outer_horizon.toFixed(4)}
              tex={'r_+ = M + \\sqrt{M^2 - Q^2}'} color="#ff6b9d" />
            <Prop label={t('rn.props.inner_horizon')}
              value={data.inner_horizon.toFixed(4)}
              tex={'r_- = M - \\sqrt{M^2 - Q^2}'} color="#a78bfa" />
            <Prop label={t('rn.props.photon_sphere')}
              value={data.photon_sphere.toFixed(4)}
              tex={'r_\\gamma = \\tfrac{1}{2}(3M + \\sqrt{9M^2 - 8Q^2})'} color="#00dfff" />
            <Prop label={t('rn.props.isco')}
              value={data.isco.toFixed(4)}
              tex={'r_{\\rm ISCO} \\to 6M\\ \\text{at}\\ Q=0'} color="#22c55e" />
            <Prop label={t('rn.props.kappa')}
              value={data.surface_gravity.toExponential(3)}
              tex={'\\kappa = \\frac{r_+ - r_-}{2 r_+^2}'} color="#fb923c" />
            <Prop label={t('rn.props.hawking_t')}
              value={data.hawking_temperature.toExponential(3)}
              tex={'T_H = \\frac{\\kappa}{2\\pi}'} color="#fbbf24" />
            <Prop label={t('rn.props.horizon_area')}
              value={data.horizon_area.toFixed(3)}
              tex={'A = 4\\pi r_+^2'} color="#06b6d4" />
            <Prop label={t('rn.props.entropy')}
              value={data.bekenstein_hawking_entropy.toFixed(3)}
              tex={'S = \\pi r_+^2'} color="#ff6b9d" />
            <Prop label={t('rn.props.vieta')}
              value={(data.outer_horizon * data.inner_horizon).toFixed(6)}
              tex={'r_+ r_- = Q^2'}
              color={Math.abs(data.outer_horizon * data.inner_horizon - charge * charge) < 1e-9 ? '#22c55e' : '#fb923c'} />
          </div>
        )}

        <div style={styles.visualBox}>
          <RNRadialPlot data={data} mass={mass} />
        </div>

        {loading && <div style={styles.statusBanner}>{t('common.loading')}</div>}
        {error && <div style={styles.errorBanner}>⚠️ {error}</div>}
      </section>

      <section style={styles.card}>
        <h3 style={{ margin: 0, color: '#fff' }}>{t('rn.what_changes_title')}</h3>
        <ul style={styles.bulletList}>
          <li>{t('rn.bullet_a')}</li>
          <li>{t('rn.bullet_b')}</li>
          <li>{t('rn.bullet_c')}</li>
          <li>{t('rn.bullet_d')}</li>
        </ul>
        <p style={styles.cite}>
          {t('rn.cite')}
        </p>
      </section>
    </div>
  )
}

function ControlSlider({ label, value, onChange, min, max, step, color, hint }) {
  return (
    <div style={styles.controlGroup}>
      <label style={styles.controlLabel}>
        {label}: <strong style={{ color }}>{value.toFixed(3)}</strong>
      </label>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        style={{ width: '100%', accentColor: color }} />
      {hint && <small style={styles.hint}>{hint}</small>}
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

function RNRadialPlot({ data, mass }) {
  const { t } = useTranslation()
  const size = 460
  const cx = size / 2
  const cy = size / 2
  if (!data) {
    return (
      <svg width={size} height={size} style={{ background: '#0a0a0f' }}>
        <text x={cx} y={cy} fill="#6b7280" fontSize="13" textAnchor="middle">
          {t('common.loading')}
        </text>
      </svg>
    )
  }
  const maxR = Math.max(data.isco, 8 * mass) * 1.05
  const scale = (size / 2 - 30) / maxR

  const r_plus = data.outer_horizon * scale
  const r_minus = data.inner_horizon * scale
  const r_photon = data.photon_sphere * scale
  const r_isco = data.isco * scale

  return (
    <svg width={size} height={size} style={{ background: '#0a0a0f', borderRadius: 12 }}>
      <defs>
        <radialGradient id="rn-bh">
          <stop offset="0%" stopColor="#000" />
          <stop offset="85%" stopColor="#1a0a1a" />
          <stop offset="100%" stopColor="#4a1a4a" />
        </radialGradient>
      </defs>

      {/* ISCO */}
      <circle cx={cx} cy={cy} r={r_isco} fill="none"
        stroke="#22c55e" strokeWidth="1" strokeDasharray="4 4" opacity="0.65" />
      <text x={cx + r_isco + 4} y={cy + 11} fill="#22c55e" fontSize="10">ISCO</text>

      {/* Photon sphere */}
      <circle cx={cx} cy={cy} r={r_photon} fill="none"
        stroke="#00dfff" strokeWidth="1" strokeDasharray="2 3" opacity="0.7" />
      <text x={cx + r_photon + 4} y={cy + 24} fill="#00dfff" fontSize="10">photon r_γ</text>

      {/* Outer horizon */}
      <circle cx={cx} cy={cy} r={r_plus} fill="url(#rn-bh)"
        stroke="#ff6b9d" strokeWidth="2" />
      <text x={cx + r_plus + 4} y={cy + 38} fill="#ff6b9d" fontSize="10">r₊</text>

      {/* Inner Cauchy horizon */}
      {r_minus > 4 && (
        <>
          <circle cx={cx} cy={cy} r={r_minus} fill="none"
            stroke="#a78bfa" strokeWidth="1" strokeDasharray="3 3" opacity="0.85" />
          <text x={cx + r_minus + 4} y={cy + 50} fill="#a78bfa" fontSize="10">r₋</text>
        </>
      )}

      <circle cx={cx} cy={cy} r="2" fill="#fff" />

      <text x={cx} y={size - 10} fill="#6b7280" fontSize="11" textAnchor="middle">
        {t('rn.spherical_caption')}
      </text>
    </svg>
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
  controls: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 24,
    marginBottom: 24,
  },
  controlGroup: { display: 'flex', flexDirection: 'column' },
  controlLabel: { fontSize: 13, marginBottom: 8, color: '#c4b5fd' },
  hint: { fontSize: 11, color: '#6b7280', marginTop: 6 },
  propsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
    gap: 14,
    marginBottom: 24,
  },
  prop: {
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 10,
    padding: 14,
  },
  propLabel: {
    fontSize: 11, color: '#9ca3af',
    textTransform: 'uppercase', letterSpacing: 0.4,
    marginBottom: 6,
  },
  propValue: { fontSize: 18, fontWeight: 700, fontFamily: 'monospace', marginBottom: 4 },
  propTex: { fontSize: 11 },
  visualBox: { display: 'flex', justifyContent: 'center', padding: '16px 0' },
  statusBanner: {
    padding: '8px 14px',
    background: 'rgba(0,223,255,0.08)',
    border: '1px solid rgba(0,223,255,0.2)',
    borderRadius: 8,
    fontSize: 12, color: '#00dfff', marginTop: 12,
  },
  errorBanner: {
    padding: '10px 16px',
    background: 'rgba(255,193,7,0.1)',
    border: '1px solid rgba(255,193,7,0.3)',
    borderRadius: 8,
    fontSize: 13, color: '#ffc107', marginTop: 16,
  },
  bulletList: {
    fontSize: 14, color: '#c4b5fd', lineHeight: 1.8,
    paddingLeft: 20, marginTop: 14,
  },
  cite: { fontSize: 11, color: '#6b7280', marginTop: 16, fontStyle: 'italic' },
}
