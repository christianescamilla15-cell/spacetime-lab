/**
 * Home / landing page — entry point for first-time visitors.
 *
 * Goals: explain what the lab is in 30 seconds, and steer visitors to
 * one of the four physics pages.
 */

import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export default function Home() {
  const { t } = useTranslation()
  return (
    <div>
      <section style={styles.hero}>
        <h1 style={styles.heroTitle}>
          {t('home.hero_title')}
        </h1>
        <p style={styles.heroLede}>
          {t('home.hero_lede')}
        </p>
        <div style={styles.ctas}>
          <Link to="/schwarzschild" style={styles.ctaPrimary}>
            {t('home.cta_start')}
          </Link>
          <a
            href="https://github.com/christianescamilla15-cell/spacetime-lab"
            target="_blank"
            rel="noopener noreferrer"
            style={styles.ctaSecondary}
          >
            {t('home.cta_github')}
          </a>
        </div>
      </section>

      <section style={styles.cardGrid}>
        <PageCard
          to="/schwarzschild"
          title="Schwarzschild"
          subtitle={t('home.cards.schwarzschild.subtitle')}
          desc={t('home.cards.schwarzschild.desc')}
          status="ready"
        />
        <PageCard
          to="/kerr"
          title="Kerr"
          subtitle={t('home.cards.kerr.subtitle')}
          desc={t('home.cards.kerr.desc')}
          status="ready"
        />
        <PageCard
          to="/btz"
          title="BTZ"
          subtitle={t('home.cards.btz.subtitle')}
          desc={t('home.cards.btz.desc')}
          status="ready"
        />
        <PageCard
          to="/reissner-nordstrom"
          title="Reissner-Nordström"
          subtitle={t('home.cards.rn.subtitle')}
          desc={t('home.cards.rn.desc')}
          status="ready"
        />
        <PageCard
          to="/kerr-newman"
          title="Kerr-Newman"
          subtitle={t('home.cards.kn.subtitle')}
          desc={t('home.cards.kn.desc')}
          status="ready"
        />
        <PageCard
          to="/de-sitter"
          title="de Sitter"
          subtitle={t('home.cards.ds.subtitle')}
          desc={t('home.cards.ds.desc')}
          status="ready"
        />
        <PageCard
          to="/geodesics"
          title={t('nav.geodesics')}
          subtitle={t('home.cards.geo.subtitle')}
          desc={t('home.cards.geo.desc')}
          status="ready"
        />
        <PageCard
          to="/penrose"
          title={t('home.cards.penrose.title')}
          subtitle={t('home.cards.penrose.subtitle')}
          desc={t('home.cards.penrose.desc')}
          status="ready"
        />
        <PageCard
          to="/holography"
          title={t('nav.holography')}
          subtitle={t('home.cards.holo.subtitle')}
          desc={t('home.cards.holo.desc')}
          status="ready"
        />
      </section>

      <section style={styles.statsCard}>
        <h2 style={styles.statsTitle}>{t('home.stats_title')}</h2>
        <div style={styles.statsGrid}>
          <Stat label={t('home.stats_tests')} value="655+" />
          <Stat label={t('home.stats_modules')} value="8" />
          <Stat label={t('home.stats_notebooks')} value="15" />
          <Stat label={t('home.stats_release')} value="v2.1.0" />
        </div>
        <p style={styles.statsCaption}>
          {t('home.stats_caption')}
        </p>
      </section>
    </div>
  )
}

function PageCard({ to, title, subtitle, desc, status }) {
  const { t } = useTranslation()
  return (
    <Link to={to} style={styles.pageCard}>
      <div style={styles.pageCardTitle}>{title}</div>
      <div style={styles.pageCardSubtitle}>{subtitle}</div>
      <p style={styles.pageCardDesc}>{desc}</p>
      <div style={status === 'ready' ? styles.statusReady : styles.statusBuilding}>
        {status === 'ready' ? t('home.status_ready') : t('home.status_building')}
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
