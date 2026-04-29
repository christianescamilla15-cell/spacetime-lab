/**
 * Schwarzschild page — wraps the original v0.0.1 visualisation
 * (Schwarzschild card + EffectivePotential) inside the v2.5 routed
 * layout.  No physics changes; just moved out of App.jsx so each route
 * gets its own self-contained component.
 */

import { useState, useEffect } from 'react'
import EffectivePotential from '../EffectivePotential'
import { TexBlock } from '../components/Math'
import { api } from '../lib/api'

export default function Schwarzschild() {
  const [mass, setMass] = useState(1.0)
  const [properties, setProperties] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    api.schwarzschild
      .properties(mass)
      .then((data) => !cancelled && (setProperties(data), setError(null)))
      .catch((err) => {
        if (cancelled) return
        setError(err.message)
        // Client-side fallback so the page is usable even if API is down
        setProperties({
          mass,
          event_horizon: 2 * mass,
          isco: 6 * mass,
          photon_sphere: 3 * mass,
          surface_gravity: 1 / (4 * mass),
          hawking_temperature: 1 / (8 * Math.PI * mass),
          bekenstein_hawking_entropy: 4 * Math.PI * mass * mass,
          line_element_latex:
            'ds^2 = -(1 - 2M/r) dt^2 + (1 - 2M/r)^{-1} dr^2 + r^2 d\\Omega^2',
        })
      })
    return () => {
      cancelled = true
    }
  }, [mass])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 30 }}>
      <section style={styles.card}>
        <h2 style={styles.sectionTitle}>Schwarzschild Black Hole</h2>
        <p style={styles.sectionDesc}>
          The simplest exact black hole solution — a non-rotating, uncharged,
          spherically symmetric vacuum spacetime.
        </p>

        <div style={styles.formula}>
          <TexBlock>
            {'ds^2 = -\\left(1 - \\frac{2M}{r}\\right) dt^2 + \\left(1 - \\frac{2M}{r}\\right)^{-1} dr^2 + r^2 \\, d\\Omega^2'}
          </TexBlock>
        </div>

        <div style={styles.controlGroup}>
          <label style={styles.label}>
            Mass parameter M: <strong>{mass.toFixed(2)}</strong>
          </label>
          <input
            type="range"
            min="0.1"
            max="10"
            step="0.1"
            value={mass}
            onChange={(e) => setMass(parseFloat(e.target.value))}
            style={styles.slider}
          />
          <small style={styles.hint}>(geometric units G = c = 1)</small>
        </div>

        {properties && (
          <div style={styles.propertiesGrid}>
            <PropertyCard
              label="Event Horizon"
              value={properties.event_horizon.toFixed(3)}
              formulaTex="r_s = 2M"
              description="Point of no return"
            />
            <PropertyCard
              label="ISCO"
              value={properties.isco.toFixed(3)}
              formulaTex="r = 6M"
              description="Innermost stable circular orbit"
            />
            <PropertyCard
              label="Photon Sphere"
              value={properties.photon_sphere.toFixed(3)}
              formulaTex="r = 3M"
              description="Unstable light orbit"
            />
            <PropertyCard
              label="Hawking Temperature"
              value={properties.hawking_temperature.toExponential(3)}
              formulaTex="T = \\frac{1}{8\\pi M}"
              description="Quantum radiation temperature"
            />
            <PropertyCard
              label="Surface Gravity"
              value={properties.surface_gravity.toFixed(4)}
              formulaTex="\\kappa = \\frac{1}{4M}"
              description="Gravity at horizon"
            />
            <PropertyCard
              label="BH Entropy"
              value={properties.bekenstein_hawking_entropy.toFixed(3)}
              formulaTex="S = 4\\pi M^2"
              description="Bekenstein-Hawking entropy"
            />
          </div>
        )}

        <div style={styles.visualBox}>
          <BlackHoleVisual mass={mass} properties={properties} />
        </div>

        {error && (
          <div style={styles.errorBanner}>
            ⚠️ Using client-side fallback (API: {error})
          </div>
        )}
      </section>

      <EffectivePotential />
    </div>
  )
}

function PropertyCard({ label, value, formulaTex, description }) {
  return (
    <div style={styles.property}>
      <div style={styles.propertyLabel}>{label}</div>
      <div style={styles.propertyValue}>{value}</div>
      <div style={styles.propertyFormula}>
        <TexBlock>{formulaTex}</TexBlock>
      </div>
      <div style={styles.propertyDesc}>{description}</div>
    </div>
  )
}

function BlackHoleVisual({ mass, properties }) {
  if (!properties) return null
  const size = 400
  const cx = size / 2
  const cy = size / 2
  const scale = 20
  const horizon = properties.event_horizon * scale
  const photon = properties.photon_sphere * scale
  const isco = properties.isco * scale

  return (
    <svg width={size} height={size} style={{ background: '#0a0a0f' }}>
      <defs>
        <radialGradient id="bh-gradient">
          <stop offset="0%" stopColor="#000" />
          <stop offset="80%" stopColor="#1a0a1a" />
          <stop offset="100%" stopColor="#4a1a4a" />
        </radialGradient>
      </defs>

      <circle
        cx={cx}
        cy={cy}
        r={isco}
        fill="none"
        stroke="#ffd700"
        strokeWidth="1"
        strokeDasharray="4 4"
        opacity="0.5"
      />
      <text x={cx + isco + 8} y={cy} fill="#ffd700" fontSize="11">
        ISCO
      </text>

      <circle
        cx={cx}
        cy={cy}
        r={photon}
        fill="none"
        stroke="#00dfff"
        strokeWidth="1"
        strokeDasharray="2 2"
        opacity="0.7"
      />
      <text x={cx + photon + 8} y={cy + 15} fill="#00dfff" fontSize="11">
        Photon sphere
      </text>

      <circle
        cx={cx}
        cy={cy}
        r={horizon}
        fill="url(#bh-gradient)"
        stroke="#ff6b9d"
        strokeWidth="2"
      />
      <text x={cx + horizon + 8} y={cy + 30} fill="#ff6b9d" fontSize="11">
        Event horizon
      </text>

      <circle cx={cx} cy={cy} r="2" fill="#fff" />
      <text x={cx + 8} y={cy - 8} fill="#fff" fontSize="10">
        r=0
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
  sectionTitle: { fontSize: 24, margin: '0 0 8px', color: '#fff' },
  sectionDesc: { fontSize: 14, color: '#9ca3af', marginBottom: 24 },
  formula: {
    background: 'rgba(0,223,255,0.05)',
    border: '1px solid rgba(0,223,255,0.15)',
    borderRadius: 10,
    padding: '14px 20px',
    marginBottom: 24,
    overflowX: 'auto',
  },
  controlGroup: { marginBottom: 24 },
  label: { display: 'block', fontSize: 14, marginBottom: 8, color: '#c4b5fd' },
  slider: { width: '100%', accentColor: '#ff6b9d' },
  hint: { display: 'block', color: '#6b7280', marginTop: 4 },
  propertiesGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: 16,
    marginBottom: 24,
  },
  property: {
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 10,
    padding: 16,
  },
  propertyLabel: {
    fontSize: 11,
    color: '#9ca3af',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  propertyValue: {
    fontSize: 22,
    fontWeight: 700,
    color: '#ff6b9d',
    fontFamily: 'monospace',
    marginBottom: 4,
  },
  propertyFormula: { fontSize: 12, color: '#00dfff', marginBottom: 4 },
  propertyDesc: { fontSize: 11, color: '#6b7280' },
  visualBox: { display: 'flex', justifyContent: 'center', padding: '24px 0' },
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
