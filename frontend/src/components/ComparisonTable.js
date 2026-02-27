import React, { useState } from 'react';
import './ComparisonTable.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function ComparisonTable({ runtimeMode = 'simulator', ibmStatus = {} }) {
  const [bitLength, setBitLength] = useState(256);
  const [shots, setShots] = useState(1024);
  const [loading, setLoading] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  const [error, setError] = useState(null);

  const runComparison = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const compareMode = runtimeMode === 'hardware' ? 'ibm_hardware' : 'simulator';
      if (compareMode === 'ibm_hardware' && !(ibmStatus.connected && ibmStatus.backend)) {
        setError('Real hardware mode requires IBM connection and backend selection.');
        setLoading(false);
        return;
      }

      const response = await fetch(
        `${API_URL}/compare?length=${bitLength}&mode=${compareMode}&shots=${shots}`,
        {
        method: 'GET'
        }
      );
      
      const data = await response.json();
      
      if (data.success) {
        setComparisonData(data.data);
      } else {
        setError(data.error || 'Comparison failed');
      }
    } catch (err) {
      setError('Failed to connect to backend');
    } finally {
      setLoading(false);
    }
  };

  const getWinnerClass = (winner) => {
    if (winner === 'quantum') return 'winner-quantum';
    if (winner === 'classical') return 'winner-classical';
    if (winner === 'tie' || winner === 'depends') return 'winner-tie';
    return '';
  };

  return (
    <div className="comparison-container">
      <div className="comparison-card">
        <div className="card-header">
          <h2 className="card-title">Classical vs Quantum</h2>
          <p className="card-description">
            Compare random number generation methods side-by-side
          </p>
        </div>

        {/* Controls */}
        <div className="comparison-controls">
          <div className="input-group">
            <label htmlFor="compLength">Bit Length</label>
            <select
              id="compLength"
              value={bitLength}
              onChange={(e) => setBitLength(parseInt(e.target.value))}
              className="input-field"
            >
              <option value={128}>128 bits</option>
              <option value={256}>256 bits</option>
              <option value={512}>512 bits</option>
              <option value={1024}>1024 bits</option>
            </select>
          </div>

          <div className="input-group">
            <label>Quantum Source</label>
            <div className="input-field" style={{ display: 'flex', alignItems: 'center' }}>
              {runtimeMode === 'hardware'
                ? `IBM Hardware${ibmStatus.backend ? ` (${ibmStatus.backend})` : ''}`
                : 'Simulator'}
            </div>
          </div>

          <div className="input-group">
            <label htmlFor="compShots">Shots</label>
            <input
              id="compShots"
              type="number"
              min="1"
              max="4000"
              value={shots}
              onChange={(e) => setShots(parseInt(e.target.value || '0', 10))}
              className="input-field"
            />
          </div>
          
          <button 
            onClick={runComparison}
            disabled={loading}
            className="generate-button compare-btn"
          >
            {loading ? (
              <><span className="spinner"></span> Running Comparison...</>
            ) : (
              <><span className="button-icon">⚔️</span> Run Comparison</>
            )}
          </button>
        </div>

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        {/* Results */}
        {comparisonData && (
          <div className="comparison-results">
            {/* Summary Table */}
            <div className="summary-section">
              <h3 className="section-title">Comparison Summary</h3>
              
              <div className="comparison-table">
                <div className="table-header">
                  <div className="header-cell metric">Metric</div>
                  <div className="header-cell classical">Classical PRNG</div>
                  <div className="header-cell quantum">Quantum RNG</div>
                  <div className="header-cell winner">Winner</div>
                </div>
                
                {comparisonData.summary?.metrics?.map((metric, index) => (
                  <div key={index} className="table-row">
                    <div className="cell metric">{metric.metric}</div>
                    <div className="cell classical">{metric.classical}</div>
                    <div className="cell quantum">{metric.quantum}</div>
                    <div className={`cell winner ${getWinnerClass(metric.winner)}`}>
                      {metric.winner === 'quantum' ? '🔮 Quantum' : 
                       metric.winner === 'classical' ? '💻 Classical' : 
                       metric.winner === 'depends' ? '🤷 Depends' : '🤝 Tie'}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Generation Details */}
            <div className="details-grid">
              <div className="detail-card classical-card">
                <h4 className="detail-title">
                  <span className="detail-icon">💻</span>
                  Classical PRNG
                </h4>
                <div className="detail-algorithm">
                  {comparisonData.classical_generation?.algorithm}
                </div>
                <div className="detail-stats">
                  <div className="stat">
                    <span className="stat-label">Time:</span>
                    <span className="stat-value">{comparisonData.classical_generation?.generation_time_ms} ms</span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Speed:</span>
                    <span className="stat-value">{comparisonData.classical_generation?.bits_per_ms} bits/ms</span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Deterministic:</span>
                    <span className="stat-value">{comparisonData.classical_generation?.deterministic ? 'Yes' : 'No'}</span>
                  </div>
                </div>
                <div className="generated-bits">
                  <span className="bits-label">Generated Bits (first 64):</span>
                  <code className="bits-value">
                    {comparisonData.classical_generation?.binary?.substring(0, 64)}...
                  </code>
                </div>
              </div>

              <div className="detail-card quantum-card">
                <h4 className="detail-title">
                  <span className="detail-icon">⚛️</span>
                  Quantum RNG
                </h4>
                <div className="detail-algorithm">
                  {comparisonData.quantum_generation?.algorithm}
                </div>
                <div className="detail-algorithm">
                  Source: {comparisonData.quantum_generation?.source}
                  {comparisonData.quantum_generation?.backend
                    ? ` (${comparisonData.quantum_generation.backend})`
                    : ''}
                </div>
                <div className="detail-stats">
                  <div className="stat">
                    <span className="stat-label">Time:</span>
                    <span className="stat-value">{comparisonData.quantum_generation?.generation_time_ms} ms</span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Speed:</span>
                    <span className="stat-value">{comparisonData.quantum_generation?.bits_per_ms} bits/ms</span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Deterministic:</span>
                    <span className="stat-value">{comparisonData.quantum_generation?.deterministic ? 'Yes' : 'No'}</span>
                  </div>
                </div>
                <div className="generated-bits">
                  <span className="bits-label">Generated Bits (first 64):</span>
                  <code className="bits-value quantum">
                    {comparisonData.quantum_generation?.binary?.substring(0, 64)}...
                  </code>
                </div>
              </div>
            </div>

            {/* Entropy Comparison */}
            {comparisonData.entropy_comparison && (
              <div className="entropy-section">
                <h3 className="section-title">Entropy Analysis Comparison</h3>
                
                <div className="entropy-bars">
                  <div className="entropy-item">
                    <span className="entropy-label">Classical PRNG</span>
                    <div className="entropy-bar-wrapper">
                      <div className="entropy-bar-container">
                        <div 
                          className="entropy-bar classical"
                          style={{ width: `${comparisonData.entropy_comparison.classical?.overall_score}%` }}
                        >
                        </div>
                      </div>
                      <span className="entropy-score-outside">
                        {comparisonData.entropy_comparison.classical?.overall_score}%
                      </span>
                    </div>
                    <span className="entropy-verdict">{comparisonData.entropy_comparison.classical?.verdict}</span>
                  </div>
                  
                  <div className="entropy-item">
                    <span className="entropy-label">Quantum RNG</span>
                    <div className="entropy-bar-wrapper">
                      <div className="entropy-bar-container">
                        <div 
                          className="entropy-bar quantum"
                          style={{ width: `${comparisonData.entropy_comparison.quantum?.overall_score}%` }}
                        >
                        </div>
                      </div>
                      <span className="entropy-score-outside quantum-score">
                        {comparisonData.entropy_comparison.quantum?.overall_score}%
                      </span>
                    </div>
                    <span className="entropy-verdict">{comparisonData.entropy_comparison.quantum?.verdict}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Speed Comparison */}
            {comparisonData.speed_comparison && (
              <div className="speed-section">
                <h3 className="section-title">Speed Analysis</h3>
                <div className="speed-info">
                  <div className="speed-stat">
                    <span className="speed-label">Speed Ratio:</span>
                    <span className="speed-value">
                      {comparisonData.speed_comparison.message}
                    </span>
                  </div>
                  <p className="speed-note">{comparisonData.speed_comparison.note}</p>
                </div>
              </div>
            )}

            {comparisonData.security_comparison && (
              <div className="speed-section">
                <h3 className="section-title">Security Risk Comparison</h3>
                <div className="speed-info">
                  <div className="speed-stat">
                    <span className="speed-label">Classical (MT19937):</span>
                    <span className="speed-value">{comparisonData.security_comparison.classical?.predictability}</span>
                  </div>
                  <p className="speed-note">
                    Attack model: {comparisonData.security_comparison.classical?.known_attack}
                  </p>
                  <p className="speed-note">
                    Impact: {comparisonData.security_comparison.classical?.impact}
                  </p>
                </div>

                <div className="speed-info" style={{ marginTop: '12px' }}>
                  <div className="speed-stat">
                    <span className="speed-label">Quantum:</span>
                    <span className="speed-value">{comparisonData.security_comparison.quantum?.predictability}</span>
                  </div>
                  <p className="speed-note">
                    Attack model: {comparisonData.security_comparison.quantum?.known_attack}
                  </p>
                  <p className="speed-note">
                    Impact: {comparisonData.security_comparison.quantum?.impact}
                  </p>
                </div>

                <div className="speed-info" style={{ marginTop: '12px' }}>
                  <div className="speed-stat">
                    <span className="speed-label">Conclusion:</span>
                    <span className="speed-value">Quantum entropy is safer for key generation</span>
                  </div>
                  <p className="speed-note">{comparisonData.security_comparison.conclusion}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Info Panel */}
      <div className="info-panel">
        <h3 className="panel-title">Understanding the Comparison</h3>
        
        <div className="info-section">
          <h4>Classical PRNG</h4>
          <p>Uses mathematical algorithms (like Mersenne Twister) that are <strong>deterministic</strong> - given the same seed, they produce the same sequence.</p>
          <ul>
            <li>Very fast</li>
            <li>Reproducible (useful for testing)</li>
            <li>Not truly random</li>
            <li>Not recommended for cryptographic key generation</li>
          </ul>
        </div>
        
        <div className="info-section">
          <h4>Quantum RNG</h4>
          <p>Uses quantum mechanical phenomena (superposition) that are <strong>inherently unpredictable</strong> - fundamentally impossible to predict.</p>
          <ul>
            <li>True randomness</li>
            <li>Unpredictable by nature</li>
            <li>Ideal for cryptography</li>
            <li>Variable speed (simulation is faster; hardware may queue)</li>
          </ul>
        </div>

        <div className="verdict-box">
          <h4>The Verdict</h4>
          <p>Speed and entropy score alone are not enough. For secure keys, unpredictability matters most, and quantum-generated entropy avoids PRNG state-recovery risks.</p>
        </div>
      </div>
    </div>
  );
}

export default ComparisonTable;
