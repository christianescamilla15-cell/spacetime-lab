/**
 * de Sitter page — partial v3.2 (FLRW general case still deferred).
 *
 * Single slider (L).  All quantities closed form, so the page is the
 * simplest in the lab — no fallbacks, no error paths beyond network.
 */

import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { TexBlock, Tex } from '../components/Math'

const API = import.meta.env.VITE_API_URL || ''

export default function DeSitter() {
  const { t } = useTranslation()
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
        <h2 style={styles.title}>{t('desitter.title')}</h2>
        <p style={styles.lede}>
          {t('desitter.desc_pre')}<Tex>{'\\Lambda > 0'}</Tex>{t('desitter.desc_mid1')}
          <Tex>{' r = L = \\sqrt{3/\\Lambda} '}</Tex>{t('desitter.desc_mid2')}
        </p>

        <div style={styles.formula}>
          <TexBlock>
            {'ds^2 = -\\left(1 - \\frac{r^2}{L^2}\\right) dt^2 + \\left(1 - \\frac{r^2}{L^2}\\right)^{-1} dr^2 + r^2 \\, d\\Omega^2'}
          </TexBlock>
        </div>

        <div style={styles.controlGroup}>
          <label style={styles.controlLabel}>
            {t('desitter.radius_label_pre')}<Tex>{'L'}</Tex>:{' '}
            <strong style={{ color: '#00dfff' }}>{radius.toFixed(2)}</strong>
          </label>
          <input
            type="range" min="0.5" max="5" step="0.05" value={radius}
            onChange={(e) => setRadius(parseFloat(e.target.value))}
            style={{ width: '100%', accentColor: '#00dfff' }}
          />
          <small style={styles.hint}>
            <Tex>{'L = 1/H = \\sqrt{3/\\Lambda}'}</Tex>{t('desitter.radius_hint_post')}
          </small>
        </div>

        {data && (
          <div style={styles.propsGrid}>
            <Prop label={t('desitter.props.cosmo_horizon')}
              value={data.cosmological_horizon.toFixed(4)}
              tex={'r_c = L'} color="#ff6b9d" />
            <Prop label={t('desitter.props.lambda')}
              value={data.cosmological_constant.toFixed(4)}
              tex={'\\Lambda = 3/L^2'} color="#a78bfa" />
            <Prop label={t('desitter.props.hubble')}
              value={data.hubble_parameter.toFixed(4)}
              tex={'H = 1/L = \\sqrt{\\Lambda/3}'} color="#22c55e" />
            <Prop label={t('desitter.props.gh_t')}
              value={data.hawking_temperature.toExponential(3)}
              tex={'T_{GH} = \\frac{1}{2\\pi L}'} color="#fbbf24" />
            <Prop label={t('desitter.props.horizon_area')}
              value={data.horizon_area.toFixed(3)}
              tex={'A = 4\\pi L^2'} color="#06b6d4" />
            <Prop label={t('desitter.props.entropy')}
              value={data.bekenstein_hawking_entropy.toFixed(3)}
              tex={'S = \\pi L^2'} color="#fb923c" />
            <Prop label={t('desitter.props.ricci')}
              value={data.ricci_scalar.toFixed(3)}
              tex={'R = 12/L^2 = 4\\Lambda'} color="#c4b5fd" />
          </div>
        )}

        {error && <div style={styles.errorBanner}>⚠️ {error}</div>}
      </section>

      <section style={styles.card}>
        <h3 style={{ margin: 0, color: '#fff' }}>{t('desitter.special_title')}</h3>
        <ul style={styles.bulletList}>
          <li>
            {t('desitter.bullet_curvature_pre')}<Tex>{'R = 12/L^2'}</Tex>{t('desitter.bullet_curvature_post')}
          </li>
          <li>
            {t('desitter.bullet_horizon_pre')}<Tex>{'L = 1/H'}</Tex>{t('desitter.bullet_horizon_post')}
          </li>
          <li>
            {t('desitter.bullet_gh_pre')}<Tex>{'T_{GH} = 1/(2\\pi L)'}</Tex>{t('desitter.bullet_gh_post')}
          </li>
          <li>
            {t('desitter.bullet_entropy_pre')}<Tex>{'S = A/4 = \\pi L^2'}</Tex>{t('desitter.bullet_entropy_post')}
          </li>
          <li>
            {t('desitter.bullet_flrw_pre')}<Tex>{'w = -1'}</Tex>{t('desitter.bullet_flrw_post')}
          </li>
        </ul>
        <p style={styles.cite}>
          {t('desitter.cite_paper')}
        </p>
        <p style={styles.cite}>
          {t('desitter.cite_flrw')}
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
