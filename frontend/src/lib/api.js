/**
 * Centralised API client for the Spacetime Lab backend.
 *
 * Uses VITE_API_URL in production (set per Vercel env), falls back to
 * the Vite dev proxy ('/api/*' → http://localhost:8000) in dev.
 */

const API_URL = import.meta.env.VITE_API_URL || ''

async function get(path, params = {}) {
  const qs = new URLSearchParams(params).toString()
  const url = `${API_URL}${path}${qs ? `?${qs}` : ''}`
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${response.statusText}`)
  }
  return response.json()
}

export const api = {
  health: () => get('/api/health'),
  available: () => get('/api/metrics/available'),
  schwarzschild: {
    properties: (mass) => get('/api/metrics/schwarzschild', { mass }),
    effectivePotential: (mass, L, particle_type = 'massive') =>
      get('/api/metrics/schwarzschild/effective_potential', {
        mass,
        angular_momentum: L,
        particle_type,
      }),
  },
  kerr: {
    properties: (mass, spin) =>
      get('/api/metrics/kerr', { mass, spin }),
  },
  ads: {
    properties: (dimension, radius, G_N = 1) =>
      get('/api/metrics/ads', { dimension, radius, G_N }),
  },
  btz: {
    properties: (horizon_radius, ads_radius, G_N = 1) =>
      get('/api/metrics/btz', { horizon_radius, ads_radius, G_N }),
  },
  reissnerNordstrom: {
    properties: (mass, charge) =>
      get('/api/metrics/reissner-nordstrom', { mass, charge }),
  },
  diagrams: {
    penroseSvgUrl: (kind, opts = {}) => {
      const qs = new URLSearchParams({
        mass: 1.0, width: 600, height: 600, show_labels: true, ...opts,
      }).toString()
      return `${API_URL}/api/diagrams/penrose/${kind}/svg?${qs}`
    },
    penroseManifest: (kind, mass = 1.0) =>
      get(`/api/diagrams/penrose/${kind}/manifest`, { mass }),
    /** Returns { svg, samples, skipped, finalR }.  POST endpoint. */
    penroseSchwarzschildWithGeodesic: async (body) => {
      const r = await fetch(
        `${API_URL}/api/diagrams/penrose/schwarzschild/with_geodesic`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        },
      )
      if (!r.ok) throw new Error(`API ${r.status}: ${await r.text()}`)
      return {
        svg: await r.text(),
        samples: parseInt(r.headers.get('X-Overlay-Samples') || '0', 10),
        skipped: parseInt(r.headers.get('X-Overlay-Skipped') || '0', 10),
        finalR: parseFloat(r.headers.get('X-Geodesic-Final-R') || '0'),
      }
    },
  },
}
