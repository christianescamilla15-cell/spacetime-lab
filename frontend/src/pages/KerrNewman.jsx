/**
 * Kerr-Newman page — second metric of v3.2.
 *
 * Three sliders: M, a/M, |Q|/M.  Cosmic censorship (a/M)² + (Q/M)² ≤ 1
 * enforced by clamping the slider product live (we just disable the
 * Integrate button if the user crosses the line; we DON'T silently
 * rescale — the user should see they hit the boundary).
 */

import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { TexBlock, Tex } from '../components/Math'
import { api } from '../lib/api'

export default function KerrNewman() {
  const { t } = useTranslation()
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
      setError(t('kn.censorship_blocked', { value: (aOverM ** 2 + qOverM ** 2).toFixed(4) }))
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
        <h2 style={styles.title}>{t('kn.title')}</h2>
        <p style={styles.lede}>
          {t('kn.desc')}
        </p>

        <div style={styles.formula}>
          <TexBlock>
            {'\\Sigma = r^2 + a^2 \\cos^2\\theta, \\quad \\Delta = r^2 - 2Mr + a^2 + Q^2'}
          </TexBlock>
          <div style={styles.formulaCaption}>
            {t('kn.formula_caption_pre')}<Tex>{'+Q^2'}</Tex>{t('kn.formula_caption_mid')}<Tex>{'\\Delta'}</Tex>{t('kn.formula_caption_post')}
          </div>
        </div>

        <div style={styles.controls}>
          <ControlSlider label={<>{t('kn.mass_label_pre')}<Tex>{'M'}</Tex></>} color="#ff6b9d"
            value={mass} onChange={setMass} min={0.5} max={3} step={0.05} />
          <ControlSlider label={<>{t('kn.spin_label_pre')}<Tex>{'a/M'}</Tex></>} color="#00dfff"
            value={aOverM} onChange={setAOverM} min={0} max={0.999} step={0.005} />
          <ControlSlider label={<>{t('kn.charge_label_pre')}<Tex>{'|Q|/M'}</Tex></>} color="#fbbf24"
            value={qOverM} onChange={setQOverM} min={0} max={0.999} step={0.005} />
        </div>

        <div style={{
          ...styles.censorshipBar,
          color: violatesCensorship ? '#ef4444' : censorshipMargin < 0.05 ? '#fbbf24' : '#22c55e',
        }}>
          {t('kn.censorship_label_pre')}<Tex>{'1 - (a/M)^2 - (Q/M)^2'}</Tex>{t('kn.censorship_label_mid')}
          <code>{censorshipMargin.toFixed(6)}</code>
          {violatesCensorship && t('kn.censorship_violated')}
          {!violatesCensorship && censorshipMargin < 0.05 && t('kn.censorship_near_extremal')}
        </div>

        {data && (
          <div style={styles.propsGrid}>
            <Prop label={t('kn.props.outer_horizon')} value={data.outer_horizon.toFixed(4)}
              tex={'r_+ = M + \\sqrt{M^2 - a^2 - Q^2}'} color="#ff6b9d" />
            <Prop label={t('kn.props.inner_horizon')} value={data.inner_horizon.toFixed(4)}
              tex={'r_- = M - \\sqrt{M^2 - a^2 - Q^2}'} color="#a78bfa" />
            <Prop label={t('kn.props.ergo_equator')} value={data.ergo_equator.toFixed(4)}
              tex={'r_E(\\pi/2) = M + \\sqrt{M^2 - Q^2}'} color="#00dfff" />
            <Prop label={t('kn.props.ergo_pole')} value={data.ergo_pole.toFixed(4)}
              tex={'r_E(0) = r_+'} color="#06b6d4" />
            <Prop label={t('kn.props.omega_h')} value={data.angular_velocity_horizon.toExponential(3)}
              tex={'\\Omega_H = \\frac{a}{r_+^2 + a^2}'} color="#c4b5fd" />
            <Prop label={t('kn.props.hawking_t')} value={data.hawking_temperature.toExponential(3)}
              tex={'T_H = \\frac{r_+ - r_-}{4\\pi(r_+^2 + a^2)}'} color="#fb923c" />
            <Prop label={t('kn.props.entropy')} value={data.bekenstein_hawking_entropy.toFixed(3)}
              tex={'S = \\pi(r_+^2 + a^2)'} color="#22c55e" />
            <Prop label={t('kn.props.vieta')} value={(data.outer_horizon * data.inner_horizon).toFixed(6)}
              tex={'r_+ r_- = a^2 + Q^2'}
              color={Math.abs(data.outer_horizon * data.inner_horizon - (spin * spin + charge * charge)) < 1e-9 ? '#22c55e' : '#fb923c'} />
            <Prop label={t('kn.props.extremal')} value={data.is_extremal ? t('kn.props.extremal_yes') : t('kn.props.extremal_no')}
              tex={'a^2 + Q^2 = M^2'} color={data.is_extremal ? '#ef4444' : '#9ca3af'} />
          </div>
        )}

        {loading && <div style={styles.statusBanner}>{t('common.loading')}</div>}
        {error && <div style={styles.errorBanner}>⚠️ {error}</div>}
      </section>

      <section style={styles.card}>
        <h3 style={{ margin: 0, color: '#fff' }}>{t('kn.limits_title')}</h3>
        <ul style={styles.bulletList}>
          <li>{t('kn.bullet_schwarzschild')}</li>
          <li>{t('kn.bullet_kerr')}</li>
          <li>{t('kn.bullet_rn')}</li>
          <li>{t('kn.bullet_both')}</li>
          <li>{t('kn.bullet_extremal')}</li>
        </ul>
        <p style={styles.cite}>
          {t('kn.cite_paper')}
        </p>
        <p style={styles.cite}>
          {t('kn.cite_isco')}
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
