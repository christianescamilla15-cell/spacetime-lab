import { useState, useEffect, useMemo } from 'react'

/**
 * EffectivePotential — Interactive visualization of V_eff(r) for
 * Schwarzschild geodesics. Shows the potential curve with markers for
 * the event horizon, photon sphere, ISCO, and critical points.
 *
 * Computes client-side (no API call needed) since V_eff is a simple formula.
 */
export default function EffectivePotential() {
  const [mass, setMass] = useState(1.0)
  const [angularMomentum, setL] = useState(4.0)
  const [particleType, setParticleType] = useState('massive')

  // Compute V_eff client-side
  const data = useMemo(() => {
    const rMin = 2 * mass + 0.05
    const rMax = 30
    const nPoints = 400
    const rValues = []
    const vValues = []

    for (let i = 0; i < nPoints; i++) {
      const r = rMin + (i / (nPoints - 1)) * (rMax - rMin)
      const f = 1 - (2 * mass) / r
      let V
      if (particleType === 'massive') {
        V = f * (1 + (angularMomentum * angularMomentum) / (r * r))
      } else {
        V = f * ((angularMomentum * angularMomentum) / (r * r))
      }
      rValues.push(r)
      vValues.push(V)
    }

    // Find extrema
    const critical = []
    for (let i = 1; i < vValues.length - 1; i++) {
      if (vValues[i - 1] < vValues[i] && vValues[i] > vValues[i + 1]) {
        critical.push({ r: rValues[i], v: vValues[i], type: 'max' })
      } else if (vValues[i - 1] > vValues[i] && vValues[i] < vValues[i + 1]) {
        critical.push({ r: rValues[i], v: vValues[i], type: 'min' })
      }
    }

    return {
      rValues,
      vValues,
      critical,
      horizon: 2 * mass,
      photonSphere: 3 * mass,
      isco: 6 * mass,
      vMin: Math.min(...vValues),
      vMax: Math.max(...vValues),
    }
  }, [mass, angularMomentum, particleType])

  // SVG dimensions
  const width = 700
  const height = 400
  const padding = { top: 30, right: 40, bottom: 50, left: 60 }
  const plotW = width - padding.left - padding.right
  const plotH = height - padding.top - padding.bottom

  // Scales
  const rMin = data.rValues[0]
  const rMax = data.rValues[data.rValues.length - 1]
  const vMin = Math.min(0, data.vMin - 0.05)
  const vMax = data.vMax + 0.05

  const xScale = (r) => padding.left + ((r - rMin) / (rMax - rMin)) * plotW
  const yScale = (v) => padding.top + plotH - ((v - vMin) / (vMax - vMin)) * plotH

  // Build path
  const pathD = data.rValues
    .map((r, i) => `${i === 0 ? 'M' : 'L'} ${xScale(r)} ${yScale(data.vValues[i])}`)
    .join(' ')

  // Grid lines
  const xTicks = [5, 10, 15, 20, 25, 30]
  const yTicks = [0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2]

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>⚛️ Effective Potential V_eff(r)</h2>
        <p style={styles.subtitle}>
          Governs radial geodesic motion: (dr/dτ)² = E² − V_eff(r)
        </p>
      </div>

      {/* Controls */}
      <div style={styles.controls}>
        <div style={styles.controlGroup}>
          <label style={styles.label}>
            Mass M: <strong style={{ color: '#ff6b9d' }}>{mass.toFixed(2)}</strong>
          </label>
          <input
            type="range"
            min="0.5"
            max="3"
            step="0.1"
            value={mass}
            onChange={(e) => setMass(parseFloat(e.target.value))}
            style={styles.slider}
          />
        </div>

        <div style={styles.controlGroup}>
          <label style={styles.label}>
            Angular momentum L: <strong style={{ color: '#00dfff' }}>{angularMomentum.toFixed(2)}</strong>
          </label>
          <input
            type="range"
            min="0"
            max="8"
            step="0.1"
            value={angularMomentum}
            onChange={(e) => setL(parseFloat(e.target.value))}
            style={styles.slider}
          />
          <small style={styles.hint}>
            For massive particles: stable orbit requires L {'>'} 2√3 M ≈ {(2 * Math.sqrt(3) * mass).toFixed(2)}
          </small>
        </div>

        <div style={styles.particleTypeGroup}>
          <button
            onClick={() => setParticleType('massive')}
            style={{
              ...styles.typeBtn,
              ...(particleType === 'massive' && styles.typeBtnActive),
            }}
          >
            Massive
          </button>
          <button
            onClick={() => setParticleType('photon')}
            style={{
              ...styles.typeBtn,
              ...(particleType === 'photon' && styles.typeBtnActive),
            }}
          >
            Photon
          </button>
        </div>
      </div>

      {/* SVG plot */}
      <div style={styles.plotContainer}>
        <svg width={width} height={height} style={styles.svg}>
          {/* Background grid */}
          {xTicks.map((x) => (
            <line
              key={`vx-${x}`}
              x1={xScale(x)}
              y1={padding.top}
              x2={xScale(x)}
              y2={padding.top + plotH}
              stroke="rgba(255,255,255,0.06)"
              strokeDasharray="2 4"
            />
          ))}
          {yTicks.map((y) => (
            <line
              key={`hy-${y}`}
              x1={padding.left}
              y1={yScale(y)}
              x2={padding.left + plotW}
              y2={yScale(y)}
              stroke="rgba(255,255,255,0.06)"
              strokeDasharray="2 4"
            />
          ))}

          {/* X axis */}
          <line
            x1={padding.left}
            y1={padding.top + plotH}
            x2={padding.left + plotW}
            y2={padding.top + plotH}
            stroke="#888"
            strokeWidth="1"
          />
          {xTicks.map((x) => (
            <g key={`xt-${x}`}>
              <line
                x1={xScale(x)}
                y1={padding.top + plotH}
                x2={xScale(x)}
                y2={padding.top + plotH + 5}
                stroke="#888"
              />
              <text
                x={xScale(x)}
                y={padding.top + plotH + 20}
                fill="#888"
                fontSize="11"
                textAnchor="middle"
              >
                {x}
              </text>
            </g>
          ))}
          <text
            x={padding.left + plotW / 2}
            y={height - 10}
            fill="#c4b5fd"
            fontSize="12"
            textAnchor="middle"
          >
            r (Schwarzschild radius)
          </text>

          {/* Y axis */}
          <line
            x1={padding.left}
            y1={padding.top}
            x2={padding.left}
            y2={padding.top + plotH}
            stroke="#888"
            strokeWidth="1"
          />
          {yTicks.map((y) => (
            <g key={`yt-${y}`}>
              <line
                x1={padding.left - 5}
                y1={yScale(y)}
                x2={padding.left}
                y2={yScale(y)}
                stroke="#888"
              />
              <text
                x={padding.left - 10}
                y={yScale(y) + 4}
                fill="#888"
                fontSize="11"
                textAnchor="end"
              >
                {y.toFixed(1)}
              </text>
            </g>
          ))}
          <text
            x={15}
            y={padding.top + plotH / 2}
            fill="#c4b5fd"
            fontSize="12"
            textAnchor="middle"
            transform={`rotate(-90, 15, ${padding.top + plotH / 2})`}
          >
            V_eff(r)
          </text>

          {/* Event horizon marker */}
          {data.horizon >= rMin && data.horizon <= rMax && (
            <g>
              <line
                x1={xScale(data.horizon)}
                y1={padding.top}
                x2={xScale(data.horizon)}
                y2={padding.top + plotH}
                stroke="#ff6b9d"
                strokeWidth="2"
                strokeDasharray="4 4"
              />
              <text
                x={xScale(data.horizon) + 5}
                y={padding.top + 15}
                fill="#ff6b9d"
                fontSize="11"
              >
                Horizon
              </text>
            </g>
          )}

          {/* Photon sphere marker */}
          {data.photonSphere >= rMin && data.photonSphere <= rMax && (
            <g>
              <line
                x1={xScale(data.photonSphere)}
                y1={padding.top}
                x2={xScale(data.photonSphere)}
                y2={padding.top + plotH}
                stroke="#00dfff"
                strokeWidth="1"
                strokeDasharray="2 2"
                opacity="0.6"
              />
              <text
                x={xScale(data.photonSphere) + 5}
                y={padding.top + 30}
                fill="#00dfff"
                fontSize="10"
              >
                Photon sphere
              </text>
            </g>
          )}

          {/* ISCO marker */}
          {data.isco >= rMin && data.isco <= rMax && (
            <g>
              <line
                x1={xScale(data.isco)}
                y1={padding.top}
                x2={xScale(data.isco)}
                y2={padding.top + plotH}
                stroke="#ffd700"
                strokeWidth="1"
                strokeDasharray="2 2"
                opacity="0.6"
              />
              <text x={xScale(data.isco) + 5} y={padding.top + 45} fill="#ffd700" fontSize="10">
                ISCO
              </text>
            </g>
          )}

          {/* V_eff curve */}
          <path d={pathD} fill="none" stroke="url(#gradient)" strokeWidth="3" />
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ff6b9d" />
              <stop offset="100%" stopColor="#00dfff" />
            </linearGradient>
          </defs>

          {/* Critical points */}
          {data.critical.map((pt, i) => (
            <g key={`crit-${i}`}>
              <circle
                cx={xScale(pt.r)}
                cy={yScale(pt.v)}
                r="6"
                fill={pt.type === 'max' ? '#ff4444' : '#44ff88'}
                stroke="#fff"
                strokeWidth="2"
              />
              <text
                x={xScale(pt.r)}
                y={yScale(pt.v) - 12}
                fill={pt.type === 'max' ? '#ff4444' : '#44ff88'}
                fontSize="10"
                textAnchor="middle"
                fontWeight="bold"
              >
                {pt.type === 'max' ? 'Unstable' : 'Stable'}
              </text>
            </g>
          ))}
        </svg>
      </div>

      {/* Legend / explanation */}
      <div style={styles.legend}>
        <div style={styles.legendItem}>
          <span style={{ color: '#ff6b9d' }}>━━</span> Event horizon (r = 2M)
        </div>
        <div style={styles.legendItem}>
          <span style={{ color: '#00dfff' }}>╶╶</span> Photon sphere (r = 3M)
        </div>
        <div style={styles.legendItem}>
          <span style={{ color: '#ffd700' }}>╶╶</span> ISCO (r = 6M)
        </div>
        <div style={styles.legendItem}>
          <span style={{ color: '#44ff88' }}>●</span> Stable circular orbit (local min)
        </div>
        <div style={styles.legendItem}>
          <span style={{ color: '#ff4444' }}>●</span> Unstable circular orbit (local max)
        </div>
      </div>

      <div style={styles.explanation}>
        <strong>Physics insight:</strong> A test particle with energy E² and angular
        momentum L moves radially according to <code>(dr/dτ)² = E² − V_eff(r)</code>.
        The particle is "trapped" in the regions where E² ≥ V_eff. Local minima of
        V_eff correspond to <em>stable circular orbits</em>, local maxima to{' '}
        <em>unstable circular orbits</em>. For massive particles, a stable orbit
        requires L {'>'} 2√3 M; this threshold defines the ISCO.
      </div>
    </div>
  )
}

const styles = {
  container: {
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 16,
    padding: 32,
  },
  header: { marginBottom: 24 },
  title: {
    fontSize: 22,
    margin: '0 0 8px',
    color: '#fff',
  },
  subtitle: {
    fontSize: 13,
    color: '#9ca3af',
    fontFamily: 'monospace',
    margin: 0,
  },
  controls: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 20,
    marginBottom: 24,
  },
  controlGroup: {
    display: 'flex',
    flexDirection: 'column',
  },
  label: {
    fontSize: 13,
    color: '#c4b5fd',
    marginBottom: 6,
  },
  slider: {
    width: '100%',
    accentColor: '#ff6b9d',
  },
  hint: {
    fontSize: 11,
    color: '#6b7280',
    marginTop: 4,
  },
  particleTypeGroup: {
    gridColumn: '1 / -1',
    display: 'flex',
    gap: 8,
    justifyContent: 'center',
  },
  typeBtn: {
    padding: '8px 20px',
    borderRadius: 20,
    border: '1px solid rgba(255,255,255,0.15)',
    background: 'rgba(255,255,255,0.05)',
    color: '#c4b5fd',
    fontSize: 13,
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  typeBtnActive: {
    background: 'linear-gradient(135deg, #ff6b9d, #00dfff)',
    color: '#fff',
    border: '1px solid transparent',
  },
  plotContainer: {
    display: 'flex',
    justifyContent: 'center',
    marginBottom: 20,
  },
  svg: {
    background: 'rgba(10,10,15,0.5)',
    borderRadius: 10,
  },
  legend: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 16,
    justifyContent: 'center',
    padding: '16px 0',
    fontSize: 12,
    color: '#9ca3af',
    borderTop: '1px solid rgba(255,255,255,0.08)',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  explanation: {
    padding: 16,
    marginTop: 8,
    background: 'rgba(255,107,157,0.05)',
    border: '1px solid rgba(255,107,157,0.15)',
    borderRadius: 10,
    fontSize: 13,
    color: '#c4b5fd',
    lineHeight: 1.6,
  },
}
