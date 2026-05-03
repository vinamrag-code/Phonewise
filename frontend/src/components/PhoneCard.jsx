function PhoneCard({ phone, onCompare, isCompared }) {
  return (
    <div className="phone-card glass-panel animate-fade-in delay-1">
      <div className="phone-card-header">
        <h3 className="phone-name">{phone.name}</h3>
        <div className="match-badge">
          {phone.match_percentage}% Match
        </div>
      </div>
      
      <div className="phone-image-placeholder">
        {/* Placeholder image representation */}
      </div>
      
      <div className="phone-tags">
        {phone.tags && phone.tags.map(tag => (
          <span key={tag} className="tag">{tag}</span>
        ))}
      </div>
      
      <div className="phone-specs">
        <div className="spec-row">
          <span className="spec-label">Price</span>
          <span className="spec-value">₹{phone.price ? phone.price.toLocaleString('en-IN') : 'N/A'}</span>
        </div>
        <div className="spec-row">
          <span className="spec-label">RAM/Storage</span>
          <span className="spec-value">{phone.ram}GB / {phone.storage}GB</span>
        </div>
        <div className="spec-row">
          <span className="spec-label">Camera</span>
          <span className="spec-value">{phone.camera_summary}</span>
        </div>
      </div>

      <div className="phone-reason">
        <strong>Why this phone?</strong>
        <p>{phone.reason}</p>
      </div>

      <div className="phone-card-actions">
        <button 
          className={`btn ${isCompared ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => onCompare(phone)}
        >
          {isCompared ? 'Added to Compare' : 'Add to Compare'}
        </button>
      </div>
    </div>
  );
}

export default PhoneCard;
