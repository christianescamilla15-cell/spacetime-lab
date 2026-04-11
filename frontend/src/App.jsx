import { useState, useEffect } from 'react'
import EffectivePotential from './EffectivePotential'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [mass, setMass] = useState(1.0)
  const [properties, setProperties] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchProperties(mass)
  }, [mass])

  const fetchProperties = async (m) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/api/metrics/schwarzschild?mass=${m}`)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const data = await response.json()
      setProperties(data)
    } catch (err) {
      setError(err.message)
      // Fallback to client-side computation if API is down
      setProperties({
        mass: m,
        event_horizon: 2 * m,
        isco: 6 * m,
        photon_sphere: 3 * m,
        surface_gravity: 1 / (4 * m),
        hawking_temperature: 1 / (8 * Math.PI * m),
        bekenstein_hawking_entropy: 4 * Math.PI * m * m,
        line_element_latex: `ds^2 = -(1 - 2M/r) dt^2 + (1 - 2M/r)^{-1} dr^2 + r^2 d\\Omega^2`,
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.app}>
      {/* Header */}
      <header style={styles.header}>
        <h1 style={styles.title}>
          <span style={styles.logo}>⚫</span> Spacetime Lab
        </h1>
        <p style={styles.tagline}>
          Interactive platform for exploring black hole physics
        </p>
        <div style={styles.badges}>
          <span style={styles.badge}>v0.0.1 Alpha</span>
          <span style={styles.badge}>MIT License</span>
          <a
            href="https://github.com/christianescamilla15-cell/spacetime-lab"
            target="_blank"
            rel="noopener noreferrer"
            style={styles.badgeLink}
          >
            GitHub ↗
          </a>
        </div>
      </header>

      {/* Main content */}
      <main style={styles.main}>
        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>Schwarzschild Black Hole</h2>
          <p style={styles.sectionDesc}>
            Explore the simplest exact black hole solution — a non-rotating,
            uncharged, spherically symmetric spacetime.
          </p>

          {/* Mass slider */}
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
            <small style={styles.hint}>
              (in geometric units G = c = 1)
            </small>
          </div>

          {/* Properties */}
          {properties && (
            <div style={styles.propertiesGrid}>
              <PropertyCard
                label="Event Horizon"
                value={properties.event_horizon.toFixed(3)}
                formula="r_s = 2M"
                description="The point of no return"
              />
              <PropertyCard
                label="ISCO"
                value={properties.isco.toFixed(3)}
                formula="r = 6M"
                description="Innermost stable circular orbit"
              />
              <PropertyCard
                label="Photon Sphere"
                value={properties.photon_sphere.toFixed(3)}
                formula="r = 3M"
                description="Unstable light orbit"
              />
              <PropertyCard
                label="Hawking Temperature"
                value={properties.hawking_temperature.toExponential(3)}
                formula="T = 1 / (8π M)"
                description="Quantum radiation temperature"
              />
              <PropertyCard
                label="Surface Gravity"
                value={properties.surface_gravity.toFixed(4)}
                formula="κ = 1 / (4M)"
                description="Gravity at horizon"
              />
              <PropertyCard
                label="BH Entropy"
                value={properties.bekenstein_hawking_entropy.toFixed(3)}
                formula="S = 4π M²"
                description="Bekenstein-Hawking entropy"
              />
            </div>
          )}

          {/* Visual representation */}
          <div style={styles.visualBox}>
            <BlackHoleVisual mass={mass} properties={properties} />
          </div>

          {error && (
            <div style={styles.errorBanner}>
              ⚠️ Using client-side fallback (API: {error})
            </div>
          )}
        </section>

        {/* Effective Potential — Phase 1 addition */}
        <EffectivePotential />

        {/* Roadmap preview */}
        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>🚀 Roadmap</h2>
          <div style={styles.phaseGrid}>
            {PHASES.map((phase) => (
              <div
                key={phase.num}
                style={{
                  ...styles.phase,
                  ...(phase.status === 'current' && styles.phaseCurrent),
                }}
              >
                <div style={styles.phaseNum}>Phase {phase.num}</div>
                <div style={styles.phaseName}>{phase.name}</div>
                <div style={styles.phaseStatus}>
                  {phase.status === 'current' ? '🏗️ Building' : '📅 Planned'}
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer style={styles.footer}>
        <p>
          Built by{' '}
          <a
            href="https://github.com/christianescamilla15-cell"
            style={styles.footerLink}
          >
            Christian Hernández
          </a>{' '}
          — an AI engineer learning GR by building tools for it.
        </p>
        <p style={styles.footerSmall}>
          © 2026 Spacetime Lab · MIT License
        </p>
      </footer>
    </div>
  )
}

function PropertyCard({ label, value, formula, description }) {
  return (
    <div style={styles.property}>
      <div style={styles.propertyLabel}>{label}</div>
      <div style={styles.propertyValue}>{value}</div>
      <div style={styles.propertyFormula}>{formula}</div>
      <div style={styles.propertyDesc}>{description}</div>
    </div>
  )
}

function BlackHoleVisual({ mass, properties }) {
  if (!properties) return null

  const size = 400
  const cx = size / 2
  const cy = size / 2
  const scale = 20  // pixels per geometric unit
  const horizon = properties.event_horizon * scale
  const photon = properties.photon_sphere * scale
  const isco = properties.isco * scale

  return (
    <svg width={size} height={size} style={{ background: '#0a0a0f' }}>
      {/* Grid */}
      <defs>
        <radialGradient id="bh-gradient">
          <stop offset="0%" stopColor="#000" />
          <stop offset="80%" stopColor="#1a0a1a" />
          <stop offset="100%" stopColor="#4a1a4a" />
        </radialGradient>
      </defs>

      {/* ISCO (outer) */}
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

      {/* Photon sphere */}
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

      {/* Event horizon — the black hole itself */}
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

      {/* Singularity at center */}
      <circle cx={cx} cy={cy} r="2" fill="#fff" />
      <text x={cx + 8} y={cy - 8} fill="#fff" fontSize="10">
        r=0
      </text>
    </svg>
  )
}

const PHASES = [
  { num: 1, name: 'Schwarzschild', status: 'current' },
  { num: 2, name: 'Penrose Diagrams', status: 'planned' },
  { num: 3, name: 'Kerr Geodesics', status: 'planned' },
  { num: 4, name: 'Horizon Finders', status: 'planned' },
  { num: 5, name: 'GW + LIGO', status: 'planned' },
  { num: 6, name: 'Quantum Info', status: 'planned' },
  { num: 7, name: 'AdS/CFT', status: 'planned' },
  { num: 8, name: 'RT/HRT Surfaces', status: 'planned' },
  { num: 9, name: 'v1.0 Release', status: 'planned' },
]

const styles = {
  app: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #0a0a0f 0%, #1a0a1a 100%)',
    color: '#e8e8f0',
  },
  header: {
    textAlign: 'center',
    padding: '60px 20px 40px',
    borderBottom: '1px solid rgba(255,255,255,0.08)',
  },
  title: {
    fontSize: 48,
    margin: 0,
    fontWeight: 700,
    background: 'linear-gradient(135deg, #ff6b9d, #00dfff)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 16,
  },
  logo: { fontSize: 40, WebkitTextFillColor: 'initial' },
  tagline: {
    fontSize: 16,
    color: '#9ca3af',
    marginTop: 12,
  },
  badges: {
    display: 'flex',
    gap: 10,
    justifyContent: 'center',
    marginTop: 20,
  },
  badge: {
    padding: '4px 12px',
    borderRadius: 20,
    background: 'rgba(255,255,255,0.08)',
    fontSize: 12,
    color: '#c4b5fd',
  },
  badgeLink: {
    padding: '4px 12px',
    borderRadius: 20,
    background: 'rgba(255,107,157,0.15)',
    fontSize: 12,
    color: '#ff6b9d',
    textDecoration: 'none',
    border: '1px solid rgba(255,107,157,0.3)',
  },
  main: {
    maxWidth: 1100,
    margin: '0 auto',
    padding: '40px 20px',
    display: 'flex',
    flexDirection: 'column',
    gap: 30,
  },
  card: {
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 16,
    padding: 32,
  },
  sectionTitle: {
    fontSize: 24,
    margin: '0 0 8px',
    color: '#fff',
  },
  sectionDesc: {
    fontSize: 14,
    color: '#9ca3af',
    marginBottom: 24,
  },
  controlGroup: {
    marginBottom: 24,
  },
  label: {
    display: 'block',
    fontSize: 14,
    marginBottom: 8,
    color: '#c4b5fd',
  },
  slider: {
    width: '100%',
    accentColor: '#ff6b9d',
  },
  hint: {
    display: 'block',
    color: '#6b7280',
    marginTop: 4,
  },
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
  propertyFormula: {
    fontSize: 12,
    color: '#00dfff',
    fontFamily: 'monospace',
    marginBottom: 4,
  },
  propertyDesc: {
    fontSize: 11,
    color: '#6b7280',
  },
  visualBox: {
    display: 'flex',
    justifyContent: 'center',
    padding: '24px 0',
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
  phaseGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
    gap: 12,
  },
  phase: {
    padding: 16,
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 10,
  },
  phaseCurrent: {
    background: 'rgba(255,107,157,0.08)',
    border: '1px solid rgba(255,107,157,0.3)',
  },
  phaseNum: {
    fontSize: 11,
    color: '#9ca3af',
    marginBottom: 4,
  },
  phaseName: {
    fontSize: 14,
    fontWeight: 600,
    color: '#fff',
    marginBottom: 4,
  },
  phaseStatus: {
    fontSize: 11,
    color: '#6b7280',
  },
  footer: {
    textAlign: 'center',
    padding: '40px 20px',
    borderTop: '1px solid rgba(255,255,255,0.08)',
    color: '#6b7280',
    fontSize: 13,
  },
  footerLink: {
    color: '#ff6b9d',
    textDecoration: 'none',
  },
  footerSmall: {
    fontSize: 11,
    marginTop: 8,
  },
}
