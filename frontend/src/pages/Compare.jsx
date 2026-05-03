import { useState, useEffect } from 'react';

function Compare() {
  const [phones, setPhones] = useState([]);
  const [phone1Id, setPhone1Id] = useState('');
  const [phone2Id, setPhone2Id] = useState('');
  const [isComparing, setIsComparing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchPhones = async () => {
      try {
        const res = await fetch('http://localhost:8000/phones');
        const data = await res.json();
        setPhones(data);
      } catch (err) {
        console.error("Failed to fetch phones:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchPhones();
  }, []);

  const handleCompare = () => {
    if (phone1Id && phone2Id) {
      setIsComparing(true);
    }
  };

  const phone1 = phones.find(p => String(p.id || p.name) === phone1Id);
  const phone2 = phones.find(p => String(p.id || p.name) === phone2Id);

  return (
    <div className="container animate-fade-in">
      <div className="compare-header">
        <h1 className="section-title">Compare <span className="gradient-text">Devices</span></h1>
        <p className="section-subtitle">Select two smartphones below to see a detailed side-by-side comparison of their specifications and features.</p>
      </div>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '2rem' }}>Loading phones...</div>
      ) : (
        <>
          <div className="compare-container">
            {/* Device 1 Selector */}
            <div className="selector-panel glass-panel">
              <div className="input-group">
                <label>Device 1</label>
                <select 
                  className="select-input" 
                  value={phone1Id} 
                  onChange={(e) => {
                    setPhone1Id(e.target.value);
                    setIsComparing(false);
                  }}
                >
                  <option value="">Select a smartphone...</option>
                  {phones.map(phone => (
                    <option key={phone.id || phone.name} value={phone.id || phone.name}>{phone.name}</option>
                  ))}
                </select>
              </div>
              {phone1 && isComparing && (
                <div className="device-preview animate-fade-in delay-1" style={{ textAlign: 'center', marginTop: '1rem' }}>
                  <div style={{ width: '120px', height: '240px', background: 'linear-gradient(180deg, #1e293b, #0f172a)', margin: '0 auto 1rem', borderRadius: '24px', border: '4px solid #334155' }}></div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: '600' }}>{phone1.name}</h3>
                </div>
              )}
            </div>

            {/* Device 2 Selector */}
            <div className="selector-panel glass-panel">
              <div className="input-group">
                <label>Device 2</label>
                <select 
                  className="select-input" 
                  value={phone2Id} 
                  onChange={(e) => {
                    setPhone2Id(e.target.value);
                    setIsComparing(false);
                  }}
                >
                  <option value="">Select a smartphone...</option>
                  {phones.map(phone => (
                    <option key={phone.id || phone.name} value={phone.id || phone.name}>{phone.name}</option>
                  ))}
                </select>
              </div>
              {phone2 && isComparing && (
                <div className="device-preview animate-fade-in delay-1" style={{ textAlign: 'center', marginTop: '1rem' }}>
                  <div style={{ width: '120px', height: '240px', background: 'linear-gradient(180deg, #1e293b, #0f172a)', margin: '0 auto 1rem', borderRadius: '24px', border: '4px solid #334155' }}></div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: '600' }}>{phone2.name}</h3>
                </div>
              )}
            </div>
          </div>

          {!isComparing && (
            <div style={{ textAlign: 'center', marginTop: '3rem' }}>
              <button 
                className="btn btn-primary" 
                onClick={handleCompare}
                disabled={!phone1Id || !phone2Id}
                style={{ opacity: (!phone1Id || !phone2Id) ? 0.5 : 1, cursor: (!phone1Id || !phone2Id) ? 'not-allowed' : 'pointer', fontSize: '1.25rem', padding: '1rem 3rem' }}
              >
                Compare Now
              </button>
            </div>
          )}

          {/* Comparison Results */}
          {isComparing && phone1 && phone2 && (
            <div className="results-panel glass-panel animate-fade-in delay-2" style={{ marginTop: '3rem', padding: '2rem' }}>
              <h2 style={{ textAlign: 'center', marginBottom: '2rem', fontSize: '1.5rem' }}>Detailed Specifications</h2>
              
              <div style={{ overflowX: 'auto' }}>
                <table className="specs-table">
                  <thead>
                    <tr>
                      <th>Feature</th>
                      <th>{phone1.name}</th>
                      <th>{phone2.name}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <th>OS</th>
                      <td>{phone1.os}</td>
                      <td>{phone2.os}</td>
                    </tr>
                    <tr>
                      <th>Processor (Chipset)</th>
                      <td>{phone1.chipset}</td>
                      <td>{phone2.chipset}</td>
                    </tr>
                    <tr>
                      <th>RAM</th>
                      <td>{phone1.ram} GB</td>
                      <td>{phone2.ram} GB</td>
                    </tr>
                    <tr>
                      <th>Storage</th>
                      <td>{phone1.storage} GB</td>
                      <td>{phone2.storage} GB</td>
                    </tr>
                    <tr>
                      <th>Battery</th>
                      <td>{phone1.battery} mAh</td>
                      <td>{phone2.battery} mAh</td>
                    </tr>
                    <tr>
                      <th>Main Camera</th>
                      <td>{phone1.camera} MP</td>
                      <td>{phone2.camera} MP</td>
                    </tr>
                    <tr>
                      <th>Price</th>
                      <td>₹{phone1.price?.toLocaleString('en-IN') || 'N/A'}</td>
                      <td>₹{phone2.price?.toLocaleString('en-IN') || 'N/A'}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Compare;
