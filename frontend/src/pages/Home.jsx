/**
 * Home / landing page — entry point for first-time visitors.
 *
 * Goals: explain what the lab is in 30 seconds, and steer visitors to
 * one of the four physics pages.
 */

import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div>
      <section style={styles.hero}>
        <h1 style={styles.heroTitle}>
          Interactive black-hole physics, in your browser.
        </h1>
        <p style={styles.heroLede}>
          Spacetime Lab is a Python + web platform for exploring exact
          solutions of General Relativity — from the Schwarzschild horizon
          to the Page curve of an evaporating black hole.
        </p>
        <div style={styles.ctas}>
          <Link to="/schwarzschild" style={styles.ctaPrimary}>
            Start with Schwarzschild →
          </Link>
          <a
            href="https://github.com/christianescamilla15-cell/spacetime-lab"
            target="_blank"
            rel="noopener noreferrer"
            style={styles.ctaSecondary}
          >
            GitHub ↗
          </a>
        </div>
      </section>

      <section style={styles.cardGrid}>
        <PageCard
          to="/schwarzschild"
          title="Schwarzschild"
          subtitle="Phase 1 · v0.1 → v0.4"
          desc="The simplest exact black hole. Sliders for mass; live readouts of horizon, ISCO, photon sphere, Hawking T."
          status="ready"
        />
        <PageCard
          to="/kerr"
          title="Kerr"
          subtitle="Phase 3 · v0.3 → v1.2"
          desc="Rotating black hole. Tune (M, a/M); see the ergosphere deform, ISCO split into prograde / retrograde."
          status="ready"
        />
        <PageCard
          to="/btz"
          title="BTZ"
          subtitle="Phase 8 · v0.8 → v1.3"
          desc="The 3D AdS black hole — bulk dual of the BTZ Page curve. Strominger-Cardy match verified to machine precision."
          status="ready"
        />
        <PageCard
          to="/reissner-nordstrom"
          title="Reissner-Nordström"
          subtitle="Phase 4 deferred · v3.1 in UI"
          desc="Charged static BH. Cosmic censorship enforced; closed-form horizons + photon sphere; ISCO numerical from dL²/dr=0."
          status="ready"
        />
        <PageCard
          to="/geodesics"
          title="Geodesics"
          subtitle="Phase 3 · v0.3 (v2.6 in UI)"
          desc="Integrate timelike geodesics in Kerr or Schwarzschild via the symplectic implicit-midpoint integrator. 3D scene with horizons, ergosphere, animated trail."
          status="ready"
        />
        <PageCard
          to="/penrose"
          title="Penrose Diagrams"
          subtitle="Phase 2 · v0.2 → v1.5"
          desc="Maximally extended causal structure. Pan & zoom over Minkowski and Schwarzschild conformal diagrams."
          status="ready"
        />
        <PageCard
          to="/holography"
          title="Holography"
          subtitle="Phase 7-9 · v0.7 → v2.1"
          desc="Page curves for both eternal BTZ and evaporating Schwarzschild — the resolution of the information paradox in two interactive plots."
          status="ready"
        />
      </section>

      <section style={styles.statsCard}>
        <h2 style={styles.statsTitle}>Where the project stands</h2>
        <div style={styles.statsGrid}>
          <Stat label="Tests passing" value="655+" />
          <Stat label="Modules" value="8" />
          <Stat label="Notebooks" value="15" />
          <Stat label="Latest release" value="v2.1.0" />
        </div>
        <p style={styles.statsCaption}>
          Built sequentially through Phase 1 (Schwarzschild) → Phase 9
          (Page curve, v1.0) → v2.x post-release sprint (real QES + replica
          wormholes + higher-d RT).
        </p>
      </section>
    </div>
  )
}

function PageCard({ to, title, subtitle, desc, status }) {
  return (
    <Link to={to} style={styles.pageCard}>
      <div style={styles.pageCardTitle}>{title}</div>
      <div style={styles.pageCardSubtitle}>{subtitle}</div>
      <p style={styles.pageCardDesc}>{desc}</p>
      <div style={status === 'ready' ? styles.statusReady : styles.statusBuilding}>
        {status === 'ready' ? '✓ Live' : '🏗 Building'}
      </div>
    </Link>
  )
}

function Stat({ label, value }) {
  return (
    <div style={styles.stat}>
      <div style={styles.statValue}>{value}</div>
      <div style={styles.statLabel}>{label}</div>
    </div>
  )
}

const styles = {
  hero: {
    textAlign: 'center',
    padding: '40px 20px 60px',
  },
  heroTitle: {
    fontSize: 42,
    margin: 0,
    fontWeight: 700,
    color: '#fff',
    lineHeight: 1.15,
  },
  heroLede: {
    fontSize: 17,
    color: '#9ca3af',
    maxWidth: 720,
    margin: '24px auto 0',
    lineHeight: 1.6,
  },
  ctas: {
    marginTop: 40,
    display: 'flex',
    gap: 16,
    justifyContent: 'center',
    flexWrap: 'wrap',
  },
  ctaPrimary: {
    padding: '14px 28px',
    borderRadius: 30,
    background: 'linear-gradient(135deg, #ff6b9d, #00dfff)',
    color: '#fff',
    textDecoration: 'none',
    fontSize: 15,
    fontWeight: 600,
  },
  ctaSecondary: {
    padding: '14px 28px',
    borderRadius: 30,
    background: 'rgba(255,255,255,0.06)',
    color: '#e8e8f0',
    textDecoration: 'none',
    fontSize: 15,
    fontWeight: 600,
    border: '1px solid rgba(255,255,255,0.12)',
  },
  cardGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
    gap: 20,
    marginBottom: 40,
  },
  pageCard: {
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 14,
    padding: 24,
    textDecoration: 'none',
    color: 'inherit',
    transition: 'all 0.15s',
  },
  pageCardTitle: {
    fontSize: 20,
    fontWeight: 700,
    color: '#fff',
    marginBottom: 4,
  },
  pageCardSubtitle: {
    fontSize: 12,
    color: '#c4b5fd',
    fontFamily: 'monospace',
    marginBottom: 12,
  },
  pageCardDesc: {
    fontSize: 13,
    color: '#9ca3af',
    lineHeight: 1.6,
    margin: '0 0 16px',
  },
  statusReady: {
    fontSize: 11,
    color: '#22c55e',
    fontWeight: 600,
  },
  statusBuilding: {
    fontSize: 11,
    color: '#f59e0b',
    fontWeight: 600,
  },
  statsCard: {
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 14,
    padding: 32,
  },
  statsTitle: {
    fontSize: 18,
    margin: '0 0 24px',
    color: '#fff',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
    gap: 20,
    marginBottom: 20,
  },
  stat: {
    textAlign: 'center',
  },
  statValue: {
    fontSize: 32,
    fontWeight: 700,
    background: 'linear-gradient(135deg, #ff6b9d, #00dfff)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  statLabel: {
    fontSize: 11,
    color: '#9ca3af',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: 4,
  },
  statsCaption: {
    fontSize: 13,
    color: '#6b7280',
    marginTop: 16,
    lineHeight: 1.6,
    textAlign: 'center',
  },
}
