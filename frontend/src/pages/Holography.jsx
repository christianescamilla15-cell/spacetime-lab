/**
 * Holography page — live in v2.5.
 *
 * Renders both Page curves (eternal BTZ + evaporating Schwarzschild)
 * side by side, using data from the new /api/holography/page_curve/*
 * endpoints.  This is the "money plot" of the project: the resolution
 * of the Hawking information paradox in two graphs.
 */

import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { TexBlock, Tex } from '../components/Math'

const API = import.meta.env.VITE_API_URL || ''

export default function Holography() {
  const { t } = useTranslation()
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 30 }}>
      <section style={styles.card}>
        <h2 style={styles.title}>{t('holography.title')}</h2>
        <p style={styles.lede}>
          {t('holography.lede')}
        </p>
      </section>

      <PageCurveCard
        title={t('holography.eternal.title')}
        kind="eternal"
        endpoint={`${API}/api/holography/page_curve/eternal`}
        defaultParams={{
          horizon_radius: 1.0,
          ads_radius: 1.0,
          epsilon: 0.01,
          t_max: 20.0,
          n_samples: 200,
        }}
        sliders={[
          { key: 'horizon_radius', label: t('holography.eternal.slider_horizon'), min: 0.3, max: 3, step: 0.05 },
          { key: 'ads_radius', label: t('holography.eternal.slider_ads'), min: 0.5, max: 2, step: 0.05 },
        ]}
        formula={'S(t) = \\min\\!\\left(S_{\\rm HM}(t),\\ 2 S_{BH}\\right)'}
        explainer={
          <>
            {t('holography.eternal.explainer_pre')}<Tex>{'2 S_{BH}'}</Tex>{t('holography.eternal.explainer_mid')}<Tex>{'t_P'}</Tex>{t('holography.eternal.explainer_post')}
          </>
        }
        accentColor="#00dfff"
      />

      <PageCurveCard
        title={t('holography.evaporating.title')}
        kind="evaporating"
        endpoint={`${API}/api/holography/page_curve/evaporating`}
        defaultParams={{ initial_mass: 1.0, n_samples: 200 }}
        sliders={[
          { key: 'initial_mass', label: t('holography.evaporating.slider_initial_mass'), min: 0.5, max: 3, step: 0.05 },
        ]}
        formula={'S(t) = \\min\\!\\left(S_{\\rm H}(t),\\ S_{\\rm island}(t)\\right)'}
        explainer={
          <>
            {t('holography.evaporating.explainer_pre')}<Tex>{'t_P = (1 - \\sqrt{2}/4)\\, t_{\\rm evap}'}</Tex>{t('holography.evaporating.explainer_post')}
          </>
        }
        accentColor="#ff6b9d"
      />
    </div>
  )
}

function PageCurveCard({
  title, kind, endpoint, defaultParams, sliders, formula, explainer, accentColor,
}) {
  const { t } = useTranslation()
  const [params, setParams] = useState(defaultParams)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    const qs = new URLSearchParams(params).toString()
    fetch(`${endpoint}?${qs}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((json) => !cancelled && (setData(json), setError(null)))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false))
    return () => { cancelled = true }
  }, [endpoint, JSON.stringify(params)])

  const updateSlider = (key, value) => {
    setParams((prev) => ({ ...prev, [key]: parseFloat(value) }))
  }

  return (
    <section style={styles.card}>
      <h3 style={{ ...styles.subTitle, color: accentColor }}>{title}</h3>

      <div style={styles.formula}>
        <TexBlock>{formula}</TexBlock>
      </div>

      <div style={styles.controls}>
        {sliders.map((s) => (
          <div key={s.key} style={styles.controlGroup}>
            <label style={styles.label}>
              {s.label}: <strong style={{ color: accentColor }}>
                {Number(params[s.key]).toFixed(2)}
              </strong>
            </label>
            <input
              type="range"
              min={s.min} max={s.max} step={s.step}
              value={params[s.key]}
              onChange={(e) => updateSlider(s.key, e.target.value)}
              style={styles.slider}
            />
          </div>
        ))}
      </div>

      {data && <PageCurvePlot data={data} accentColor={accentColor} kind={kind} />}

      {data && (
        <div style={styles.metaRow}>
          <Meta label={t('holography.meta.page_time')} value={data.page_time.toExponential(3)} />
          <Meta label={t('holography.meta.saturation')} value={data.saturation_entropy.toFixed(3)} />
          <Meta label={t('holography.meta.samples')} value={data.t_values.length} />
        </div>
      )}

      <p style={styles.explainer}>{explainer}</p>

      {loading && <div style={styles.statusBanner}>{t('common.loading')}</div>}
      {error && (
        <div style={styles.errorBanner}>⚠️ {t('common.api_error')}: {error}</div>
      )}
    </section>
  )
}

function PageCurvePlot({ data, accentColor, kind }) {
  const { t } = useTranslation()
  const W = 760
  const H = 320
  const pad = { top: 16, right: 24, bottom: 36, left: 56 }
  const plotW = W - pad.left - pad.right
  const plotH = H - pad.top - pad.bottom

  const ts = data.t_values
  const ss = data.s_values
  const t0 = ts[0]
  const t1 = ts[ts.length - 1]
  const sMax = Math.max(...ss) * 1.05 || 1
  const xScale = (t) => pad.left + ((t - t0) / (t1 - t0)) * plotW
  const yScale = (s) => pad.top + plotH - (s / sMax) * plotH

  // Build path with phase coloring: change stroke color at each phase boundary
  const pathSegments = []
  let segStart = 0
  for (let i = 1; i < data.phase_labels.length; i++) {
    if (data.phase_labels[i] !== data.phase_labels[i - 1]) {
      pathSegments.push({
        phase: data.phase_labels[segStart],
        d: ts.slice(segStart, i + 1)
          .map((t, idx) => `${idx === 0 ? 'M' : 'L'} ${xScale(t)} ${yScale(ss[segStart + idx])}`)
          .join(' '),
      })
      segStart = i
    }
  }
  pathSegments.push({
    phase: data.phase_labels[segStart],
    d: ts.slice(segStart)
      .map((t, idx) => `${idx === 0 ? 'M' : 'L'} ${xScale(t)} ${yScale(ss[segStart + idx])}`)
      .join(' '),
  })

  const phaseColor = {
    trivial: '#00dfff',
    hawking: '#fb923c',
    island: '#ff6b9d',
  }

  // X ticks
  const xTickCount = 6
  const xTicks = Array.from({ length: xTickCount + 1 }, (_, i) =>
    t0 + (i / xTickCount) * (t1 - t0)
  )
  const yTickCount = 5
  const yTicks = Array.from({ length: yTickCount + 1 }, (_, i) =>
    (i / yTickCount) * sMax
  )

  // Page time vertical line
  const tP = data.page_time
  const tpInRange = tP >= t0 && tP <= t1

  return (
    <svg width={W} height={H} style={{ background: 'rgba(10,10,15,0.5)', borderRadius: 10 }}>
      {/* grid */}
      {xTicks.map((t, i) => (
        <line key={`gx${i}`} x1={xScale(t)} y1={pad.top} x2={xScale(t)} y2={pad.top + plotH}
          stroke="rgba(255,255,255,0.05)" strokeDasharray="2 4" />
      ))}
      {yTicks.map((s, i) => (
        <line key={`gy${i}`} x1={pad.left} y1={yScale(s)} x2={pad.left + plotW} y2={yScale(s)}
          stroke="rgba(255,255,255,0.05)" strokeDasharray="2 4" />
      ))}

      {/* axes */}
      <line x1={pad.left} y1={pad.top + plotH} x2={pad.left + plotW} y2={pad.top + plotH}
        stroke="#888" />
      <line x1={pad.left} y1={pad.top} x2={pad.left} y2={pad.top + plotH} stroke="#888" />

      {/* x labels */}
      {xTicks.map((t, i) => (
        <text key={`tx${i}`} x={xScale(t)} y={pad.top + plotH + 18} fill="#888" fontSize="10"
          textAnchor="middle">
          {kind === 'evaporating' ? t.toExponential(1) : t.toFixed(1)}
        </text>
      ))}
      <text x={pad.left + plotW / 2} y={H - 6} fill="#c4b5fd" fontSize="11" textAnchor="middle">
        {t('holography.axes.time_label')} {kind === 'evaporating' ? t('holography.axes.time_units_evap') : ''}
      </text>

      {/* y labels */}
      {yTicks.map((s, i) => (
        <text key={`ty${i}`} x={pad.left - 8} y={yScale(s) + 4} fill="#888" fontSize="10"
          textAnchor="end">
          {s.toFixed(2)}
        </text>
      ))}
      <text x={14} y={pad.top + plotH / 2} fill="#c4b5fd" fontSize="11"
        textAnchor="middle"
        transform={`rotate(-90, 14, ${pad.top + plotH / 2})`}>
        S_rad
      </text>

      {/* Page time vertical line */}
      {tpInRange && (
        <g>
          <line x1={xScale(tP)} y1={pad.top} x2={xScale(tP)} y2={pad.top + plotH}
            stroke="#ffd700" strokeDasharray="4 4" opacity="0.7" />
          <text x={xScale(tP) + 4} y={pad.top + 12} fill="#ffd700" fontSize="10">
            t_P
          </text>
        </g>
      )}

      {/* Phase-coloured curve segments */}
      {pathSegments.map((seg, i) => (
        <path key={`seg${i}`} d={seg.d} fill="none"
          stroke={phaseColor[seg.phase] || accentColor} strokeWidth="2.5" />
      ))}

      {/* Phase legend */}
      <g transform={`translate(${pad.left + plotW - 180}, ${pad.top + 8})`}>
        {Object.entries(phaseColor).filter(([k]) =>
          data.phase_labels.includes(k)
        ).map(([k, c], i) => (
          <g key={k} transform={`translate(0, ${i * 18})`}>
            <rect width="14" height="3" y="6" fill={c} />
            <text x="20" y="10" fill="#9ca3af" fontSize="10">{k}</text>
          </g>
        ))}
      </g>
    </svg>
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
  subTitle: { fontSize: 18, margin: '0 0 18px' },
  lede: { fontSize: 14, color: '#9ca3af', marginBottom: 8, lineHeight: 1.6 },
  formula: {
    background: 'rgba(0,223,255,0.05)',
    border: '1px solid rgba(0,223,255,0.15)',
    borderRadius: 10,
    padding: '10px 18px',
    marginBottom: 20,
    overflowX: 'auto',
  },
  controls: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: 18,
    marginBottom: 20,
  },
  controlGroup: { display: 'flex', flexDirection: 'column' },
  label: { fontSize: 13, marginBottom: 6, color: '#c4b5fd' },
  slider: { width: '100%', accentColor: '#ff6b9d' },
  metaRow: {
    display: 'flex',
    gap: 18,
    flexWrap: 'wrap',
    marginTop: 14,
  },
  meta: {
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 8,
    padding: '8px 14px',
  },
  metaLabel: {
    fontSize: 10,
    color: '#9ca3af',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  metaValue: {
    fontSize: 14,
    fontWeight: 600,
    fontFamily: 'monospace',
    color: '#fff',
  },
  explainer: {
    fontSize: 13,
    color: '#c4b5fd',
    marginTop: 18,
    lineHeight: 1.6,
  },
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
    marginTop: 12,
  },
}
