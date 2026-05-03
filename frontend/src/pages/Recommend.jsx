import { useState } from 'react';
import PhoneCard from '../components/PhoneCard';

function Recommend() {
  const [step, setStep] = useState('form'); // 'form' | 'loading' | 'results'
  const [results, setResults] = useState([]);
  const [sortBy, setSortBy] = useState('match');
  const [compareList, setCompareList] = useState([]);

  // Form State
  const [preferences, setPreferences] = useState({
    priorities: {
      camera: 5,
      battery: 5,
      performance: 5,
      storage: 5,
      ram: 5
    },
    budget: 50000,
    os: 'Any',
    minRam: 8,
    minStorage: 128,
    primaryUse: 'normal'
  });

  const handleSliderChange = (name, value) => {
    setPreferences(prev => ({
      ...prev,
      priorities: {
        ...prev.priorities,
        [name]: parseInt(value)
      }
    }));
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setPreferences(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStep('loading');

    try {
      const payload = {
        max_budget: parseInt(preferences.budget),
        min_ram: parseInt(preferences.minRam),
        min_storage: parseInt(preferences.minStorage),
        os_preference: preferences.os === 'Any' ? null : preferences.os,
        primary_use: preferences.primaryUse,
        weights: {
          budget: 5, // Default weight or scaling for budget
          camera: preferences.priorities.camera,
          battery: preferences.priorities.battery,
          performance: preferences.priorities.performance,
          storage: preferences.priorities.storage,
          ram: preferences.priorities.ram
        }
      };

      const response = await fetch('http://localhost:8000/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error('Failed to fetch recommendations');
      }

      const data = await response.json();
      
      const mappedResults = data.recommendations.map(r => ({
        id: r.phone.id || r.phone.name,
        name: r.phone.name,
        match_percentage: r.match_percentage,
        price: r.phone.price,
        ram: r.phone.ram,
        storage: r.phone.storage,
        camera_summary: `${r.phone.camera}MP Main`,
        tags: r.tags ? r.tags.map(t => t.label) : [],
        reason: r.reasons && r.reasons.length > 0 ? r.reasons[0].detail : "Matches your criteria well based on our algorithm."
      }));

      setResults(mappedResults);
      setStep('results');

    } catch (error) {
      console.error("Failed to fetch recommendations:", error);
      alert("Failed to fetch recommendations. Please ensure the backend is running.");
      setStep('form');
    }
  };

  const toggleCompare = (phone) => {
    setCompareList(prev => {
      const exists = prev.find(p => p.id === phone.id);
      if (exists) return prev.filter(p => p.id !== phone.id);
      if (prev.length >= 2) {
        alert("You can only compare 2 phones at a time.");
        return prev;
      }
      return [...prev, phone];
    });
  };

  const getSortedResults = () => {
    const sorted = [...results];
    if (sortBy === 'match') sorted.sort((a, b) => b.match_percentage - a.match_percentage);
    if (sortBy === 'priceAsc') sorted.sort((a, b) => a.price - b.price);
    if (sortBy === 'priceDesc') sorted.sort((a, b) => b.price - a.price);
    return sorted;
  };

  return (
    <div className="container animate-fade-in">
      <div className="recommend-header">
        <h1 className="section-title">Get <span className="gradient-text">Recommendations</span></h1>
        <p className="section-subtitle">Tell us what matters most to you, and our AI will find the perfect smartphone.</p>
      </div>

      {step === 'form' && (
        <div className="glass-panel recommend-form-container">
          <form onSubmit={handleSubmit} className="recommend-form">
            
            <div className="form-section">
              <h3>Priorities (1-10)</h3>
              <div className="sliders-grid">
                {Object.keys(preferences.priorities).map(key => (
                  <div key={key} className="slider-group">
                    <label>
                      <span className="slider-label">{key.charAt(0).toUpperCase() + key.slice(1)}</span>
                      <span className="slider-value">{preferences.priorities[key]}</span>
                    </label>
                    <input 
                      type="range" 
                      min="1" max="10" 
                      value={preferences.priorities[key]} 
                      onChange={(e) => handleSliderChange(key, e.target.value)}
                      className="range-slider"
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="form-section">
              <h3>Budget & Requirements</h3>
              
              <div className="slider-group" style={{ marginBottom: '1.5rem' }}>
                <label>
                  <span className="slider-label">Max Budget (INR)</span>
                  <span className="slider-value">₹{Number(preferences.budget).toLocaleString('en-IN')}</span>
                </label>
                <input 
                  type="range" 
                  min="10000" max="200000" step="5000"
                  name="budget"
                  value={preferences.budget} 
                  onChange={handleChange}
                  className="range-slider"
                />
              </div>

              <div className="filters-grid">
                <div className="input-group">
                  <label>OS Preference</label>
                  <select name="os" value={preferences.os} onChange={handleChange} className="select-input">
                    <option value="Any">Any</option>
                    <option value="Android">Android</option>
                    <option value="iOS">iOS</option>
                  </select>
                </div>

                <div className="input-group">
                  <label>Primary Use</label>
                  <select name="primaryUse" value={preferences.primaryUse} onChange={handleChange} className="select-input">
                    <option value="normal">Everyday Use</option>
                    <option value="gaming">Gaming</option>
                    <option value="photography">Photography</option>
                  </select>
                </div>

                <div className="input-group">
                  <label>Min RAM (GB)</label>
                  <select name="minRam" value={preferences.minRam} onChange={handleChange} className="select-input">
                    <option value="4">4 GB</option>
                    <option value="6">6 GB</option>
                    <option value="8">8 GB</option>
                    <option value="12">12+ GB</option>
                  </select>
                </div>

                <div className="input-group">
                  <label>Min Storage (GB)</label>
                  <select name="minStorage" value={preferences.minStorage} onChange={handleChange} className="select-input">
                    <option value="64">64 GB</option>
                    <option value="128">128 GB</option>
                    <option value="256">256 GB</option>
                    <option value="512">512+ GB</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-primary" style={{ width: '100%', fontSize: '1.125rem', padding: '1rem' }}>
                Find My Perfect Phone
              </button>
            </div>
          </form>
        </div>
      )}

      {step === 'loading' && (
        <div className="loading-state">
          <div className="spinner"></div>
          <h2>Analyzing Options...</h2>
          <p>Finding the best matches for your criteria</p>
        </div>
      )}

      {step === 'results' && (
        <div className="results-container animate-fade-in">
          <div className="results-toolbar">
            <button className="btn btn-outline" onClick={() => setStep('form')}>
              ← Back to Preferences
            </button>
            
            <div className="sort-group">
              <label>Sort By:</label>
              <select className="select-input" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                <option value="match">Best Match</option>
                <option value="priceAsc">Price (Low to High)</option>
                <option value="priceDesc">Price (High to Low)</option>
              </select>
            </div>
          </div>

          {compareList.length > 0 && (
            <div className="compare-floating-bar glass-panel animate-fade-in">
              <span>{compareList.length}/2 selected for comparison</span>
              {compareList.length === 2 && (
                <button className="btn btn-primary" style={{ marginLeft: '1rem', padding: '0.5rem 1rem' }}>
                  Compare Selected
                </button>
              )}
            </div>
          )}

          <div className="recommendations-grid">
            {getSortedResults().map(phone => (
              <PhoneCard 
                key={phone.id} 
                phone={phone} 
                onCompare={toggleCompare}
                isCompared={compareList.some(p => p.id === phone.id)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Recommend;
