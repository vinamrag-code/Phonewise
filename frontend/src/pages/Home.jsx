import { Link } from 'react-router-dom';

function Home() {
  const popularComparisons = [
    { id: 1, phone1: "iPhone 15 Pro", phone2: "Samsung Galaxy S24 Ultra" },
    { id: 2, phone1: "Google Pixel 8 Pro", phone2: "iPhone 15 Pro Max" },
    { id: 3, phone1: "OnePlus 12", phone2: "Samsung Galaxy S24+" }
  ];

  return (
    <div className="container animate-fade-in">
      {/* Hero Section */}
      <section className="hero">
        <span className="hero-badge">Next-Gen Comparison Tool</span>
        <h1>Find Your Perfect <br/><span className="gradient-text">Smartphone</span></h1>
        <p>Make an informed decision with our intelligent comparison engine. Compare specs, features, and make the smart choice today.</p>
        <div className="hero-actions">
          <Link to="/recommend" className="btn btn-primary">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
            Get Recommendations
          </Link>
          <Link to="/compare" className="btn btn-outline">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M16 3h5v5M4 20L21 3M21 16v5h-5M15 15l6 6M4 4l5 5"/>
            </svg>
            Compare Phones Now
          </Link>
        </div>
      </section>

      {/* Popular Comparisons */}
      <section className="animate-fade-in delay-1">
        <h2 className="section-title">Popular <span className="gradient-text">Comparisons</span></h2>
        <p className="section-subtitle">See how the most sought-after devices stack up against each other.</p>
        
        <div className="comparisons-grid">
          {popularComparisons.map(comp => (
            <div key={comp.id} className="comparison-card glass-panel">
              <div className="phone-name">{comp.phone1}</div>
              <div className="vs-badge">VS</div>
              <div className="phone-name">{comp.phone2}</div>
            </div>
          ))}
        </div>
      </section>

      {/* About Section */}
      <section className="about-section animate-fade-in delay-2">
        <h2 className="section-title">About <span className="gradient-text">PhoneWise</span></h2>
        <div className="about-content">
          <div className="about-text">
            <p>
              At PhoneWise, we believe that choosing your next smartphone shouldn't be a daunting task. With dozens of models released every year, the sheer amount of technical jargon can overwhelm even the most tech-savvy buyers.
            </p>
            <p>
              That's why we've built a comprehensive, intuitive, and lightning-fast platform to help you compare devices side-by-side. 
            </p>
            
            <ul className="feature-list">
              <li className="feature-item">
                <div className="feature-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                </div>
                Unbiased, data-driven comparisons
              </li>
              <li className="feature-item">
                <div className="feature-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                </div>
                Lightning fast, real-time results
              </li>
              <li className="feature-item">
                <div className="feature-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                </div>
                Simple, beautiful interface
              </li>
            </ul>
          </div>
          <div className="about-image glass-panel" style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(236, 72, 153, 0.2))' }}>
            <svg width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="url(#gradient)" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
              <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="#ec4899" />
                </linearGradient>
              </defs>
              <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
              <line x1="12" y1="18" x2="12.01" y2="18"/>
            </svg>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;
