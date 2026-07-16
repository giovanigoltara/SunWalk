import '../styles/landing.css'

interface LandingProps {
  onEnter: () => void
}

const PIPELINE_STEPS = [
  {
    icon: '🏙️',
    title: 'City geometry',
    text: 'Building footprints and heights are extracted from OpenStreetMap for the study area.'
  },
  {
    icon: '☀️',
    title: 'Solar position',
    text: 'Sun azimuth and altitude are computed with astronomical algorithms for any date and time.'
  },
  {
    icon: '🌆',
    title: 'Shadow casting',
    text: 'Every building shadow is projected geometrically onto a 2 m raster of the urban surface.'
  },
  {
    icon: '🚶',
    title: 'Sun-aware routing',
    text: 'Pedestrian routes are scored by sunlight exposure and optimized for sun or shade.'
  }
]

const RESEARCH_CARDS = [
  {
    icon: '🌡️',
    title: 'Climate adaptation',
    text: 'As heatwaves intensify, shade-optimized walking routes offer a low-cost, immediately deployable public-health intervention.'
  },
  {
    icon: '💛',
    title: 'Health & wellbeing',
    text: 'In high-latitude cities like Berlin, winter daylight is scarce. Sun-seeking routes support light exposure, mood, and circadian health.'
  },
  {
    icon: '📐',
    title: 'Urban planning',
    text: 'Street-level sunlight metrics quantify how urban form shapes the pedestrian experience, informing climate-adaptive design.'
  }
]

const TECH_STACK = [
  'Python', 'FastAPI', 'GeoPandas', 'Rasterio', 'pysolar',
  'OSMnx', 'React', 'TypeScript', 'MapLibre GL'
]

function Landing({ onEnter }: LandingProps) {
  return (
    <div className="landing">
      {/* Nav */}
      <nav className="landing-nav">
        <div className="landing-logo">
          <span className="landing-logo-sun" aria-hidden="true" />
          SunWalk
        </div>
        <button className="landing-cta landing-cta-small" onClick={onEnter}>
          Launch app
        </button>
      </nav>

      {/* Hero */}
      <header className="landing-hero">
        <div className="landing-sun" aria-hidden="true" />
        <p className="landing-eyebrow">
          Urban climate · Geospatial analysis · Pedestrian mobility
        </p>
        <h1 className="landing-title">
          Chase the sun<br />through the city.
        </h1>
        <p className="landing-subtitle">
          SunWalk models how buildings cast shadows across the city, minute by
          minute — and routes pedestrians along the sunniest or shadiest path.
          A research prototype for climate-adaptive, health-aware urban navigation.
        </p>
        <div className="landing-actions">
          <button className="landing-cta" onClick={onEnter}>
            Launch the app
          </button>
          <a className="landing-cta landing-cta-ghost" href="#how-it-works">
            How it works
          </a>
        </div>

        {/* Skyline silhouette */}
        <svg
          className="landing-skyline"
          viewBox="0 0 1200 160"
          preserveAspectRatio="xMidYMax slice"
          aria-hidden="true"
        >
          <path
            d="M0 160 V90 h40 V60 h30 V95 h25 V40 h20 v10 h20 V40 h20 V95 h30 V70 h45 V110 h35 V55 h15 V35 h15 v20 h15 V110 h40 V80 h50 V50 h25 v-15 h10 v15 h25 V115 h45 V75 h35 V95 h30 V45 h20 V25 h15 v20 h20 V95 h40 V65 h45 V105 h30 V60 h25 v-20 h10 v20 h25 V105 h40 V85 h50 V45 h30 V85 h35 V115 h45 V70 h30 V30 h15 v15 h15 V70 h25 V110 h40 V80 h35 V160 Z"
            fill="currentColor"
          />
        </svg>
      </header>

      {/* Stats */}
      <section className="landing-stats">
        <div className="landing-stat">
          <span className="landing-stat-value">2 m</span>
          <span className="landing-stat-label">Shadow raster resolution</span>
        </div>
        <div className="landing-stat">
          <span className="landing-stat-value">10 min</span>
          <span className="landing-stat-label">Temporal resolution</span>
        </div>
        <div className="landing-stat">
          <span className="landing-stat-value">100%</span>
          <span className="landing-stat-label">Open data (OpenStreetMap)</span>
        </div>
        <div className="landing-stat">
          <span className="landing-stat-value">Berlin-Mitte</span>
          <span className="landing-stat-label">Pilot district</span>
        </div>
      </section>

      {/* Pipeline */}
      <section className="landing-section" id="how-it-works">
        <h2 className="landing-section-title">How it works</h2>
        <p className="landing-section-intro">
          A fully reproducible geospatial pipeline, from raw open data to
          a route on your phone.
        </p>
        <div className="landing-grid landing-grid-4">
          {PIPELINE_STEPS.map((step, i) => (
            <div className="landing-card" key={step.title}>
              <span className="landing-card-step">{i + 1}</span>
              <span className="landing-card-icon" aria-hidden="true">{step.icon}</span>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Research relevance */}
      <section className="landing-section landing-section-alt">
        <h2 className="landing-section-title">Why it matters</h2>
        <p className="landing-section-intro">
          Sunlight at street level sits at the intersection of climate,
          health, and urban form — and it can now be modeled dynamically.
        </p>
        <div className="landing-grid landing-grid-3">
          {RESEARCH_CARDS.map(card => (
            <div className="landing-card" key={card.title}>
              <span className="landing-card-icon" aria-hidden="true">{card.icon}</span>
              <h3>{card.title}</h3>
              <p>{card.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Vision */}
      <section className="landing-section">
        <h2 className="landing-section-title">Research vision</h2>
        <p className="landing-section-intro landing-vision">
          SunWalk is designed as a modular, city-agnostic framework. The
          long-term agenda includes vegetation and tree-canopy shading,
          atmospheric attenuation, machine-learning height estimation from
          imagery, and validation against in-situ sensor measurements —
          scaling from one district to entire cities.
        </p>
        <div className="landing-tech">
          {TECH_STACK.map(tech => (
            <span className="landing-chip" key={tech}>{tech}</span>
          ))}
        </div>
      </section>

      {/* Footer CTA */}
      <footer className="landing-footer">
        <button className="landing-cta" onClick={onEnter}>
          Explore the live prototype
        </button>
        <p>
          Giovani Bonadiman Goltara · Urban Research · GIS · Data Analysis
        </p>
        <p className="landing-footer-muted">
          Research prototype · Berlin-Mitte pilot · MIT License
        </p>
      </footer>
    </div>
  )
}

export default Landing
