/**
 * ConservationPanel — read-out of geodesic conservation diagnostics.
 *
 * Shows initial values + drift residuals for E, L_z, mass-shell μ²,
 * and Carter Q (Kerr only).  Color-codes the drift: green if exact (E
 * and L_z for Boyer-Lindquist Kerr), yellow if within 2nd-order budget
 * (μ², Q), red if obviously broken.
 */

import { useTranslation } from 'react-i18next'
import { Tex } from './Math'

export default function ConservationPanel({ trajectory, drift }) {
  const { t } = useTranslation()
  if (!trajectory || trajectory.length === 0 || !drift) return null
  const init = trajectory[0]

  return (
    <div style={styles.panel}>
      <div style={styles.title}>{t('conservation.title')}</div>
      <div style={styles.grid}>
        <Diagnostic
          label={<>{t('conservation.energy_label_pre')}<Tex>{'E = -p_t'}</Tex></>}
          initial={init.E}
          drift={drift.E_drift}
          tightBound={1e-9}
          looseBound={1e-6}
          unit={t('conservation.unit_E_cyclic')}
        />
        <Diagnostic
          label={<>{t('conservation.lz_label_pre')}<Tex>{'L_z = p_\\varphi'}</Tex></>}
          initial={init.L_z}
          drift={drift.L_z_drift}
          tightBound={1e-9}
          looseBound={1e-6}
          unit={t('conservation.unit_Lz_cyclic')}
        />
        <Diagnostic
          label={<>{t('conservation.mass_shell_label_pre')}<Tex>{'\\mu^2 = -2H'}</Tex></>}
          initial={init.mu_squared}
          drift={drift.mu_squared_drift}
          tightBound={1e-6}
          looseBound={1e-3}
          unit={t('conservation.unit_mu_hamilton')}
        />
        {init.Q_carter !== null && drift.Q_carter_drift !== null && (
          <Diagnostic
            label={<>{t('conservation.carter_label_pre')}<Tex>{'\\mathcal{Q}'}</Tex></>}
            initial={init.Q_carter}
            drift={drift.Q_carter_drift}
            tightBound={1e-6}
            looseBound={1e-3}
            unit={t('conservation.unit_carter_drift')}
          />
        )}
      </div>
      <p style={styles.legend}>
        {t('conservation.legend_pre')}<Tex>{'E'}</Tex>{t('conservation.legend_mid1')}<Tex>{'L_z'}</Tex>
        {t('conservation.legend_mid2')}<Tex>{'\\mu^2'}</Tex>{t('conservation.legend_mid3')}<Tex>{'\\mathcal{Q}'}</Tex>
        {t('conservation.legend_mid4')}<Tex>{'O(h^2)'}</Tex>{t('conservation.legend_post')}
      </p>
    </div>
  )
}

function Diagnostic({ label, initial, drift, tightBound, looseBound, unit }) {
  const { t } = useTranslation()
  const status = drift < tightBound
    ? 'tight'
    : drift < looseBound
      ? 'loose'
      : 'broken'
  const color = { tight: '#22c55e', loose: '#fbbf24', broken: '#ef4444' }[status]
  return (
    <div style={{ ...styles.cell, borderTop: `2px solid ${color}` }}>
      <div style={styles.cellLabel}>{label}</div>
      <div style={styles.cellInitial}>
        {t('conservation.initial_label')} <code>{initial.toExponential(4)}</code>
      </div>
      <div style={{ ...styles.cellDrift, color }}>
        {t('conservation.drift_label')} {drift.toExponential(2)}
      </div>
      <div style={styles.cellUnit}>{unit}</div>
    </div>
  )
}

const styles = {
  panel: {
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 12,
    padding: 22,
  },
  title: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 16,
    fontWeight: 600,
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: 12,
    marginBottom: 14,
  },
  cell: {
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 8,
    padding: 12,
  },
  cellLabel: {
    fontSize: 12,
    color: '#c4b5fd',
    marginBottom: 6,
    minHeight: 32,
  },
  cellInitial: {
    fontSize: 11,
    color: '#9ca3af',
    fontFamily: 'monospace',
    marginBottom: 4,
  },
  cellDrift: {
    fontSize: 14,
    fontWeight: 700,
    fontFamily: 'monospace',
    marginBottom: 4,
  },
  cellUnit: { fontSize: 10, color: '#6b7280', fontStyle: 'italic' },
  legend: { fontSize: 11, color: '#6b7280', lineHeight: 1.6, margin: 0 },
}
