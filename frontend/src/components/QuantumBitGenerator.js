import React, { useState } from 'react';
import './QuantumBitGenerator.css';

const API_URL = process.env.REACT_APP_API_URL || 'https://quantum-secure-key-generator.onrender.com/api';

function QuantumBitGenerator() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [shots, setShots] = useState(1000);
  const [error, setError] = useState(null);

  const generateBit = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/generate-bit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ shots }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setResult(data.data);
      } else {
        setError(data.error || 'Failed to generate bit');
      }
    } catch (err) {
      setError('Failed to connect to quantum backend. Make sure the server is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="generator-container">
      <div className="generator-card">
        <div className="card-header">
          <h2 className="card-title">Single Quantum Bit Generator</h2>
          <p className="card-description">
            Generate a truly random bit using quantum superposition
          </p>
        </div>

        <div className="controls">
          <div className="input-group">
            <label htmlFor="shots">Number of Measurements (Shots)</label>
            <input
              id="shots"
              type="number"
              min="100"
              max="10000"
              step="100"
              value={shots}
              onChange={(e) => setShots(parseInt(e.target.value))}
              className="input-field"
            />
            <span className="input-hint">Higher shots = more accurate statistics</span>
          </div>

          <button 
            onClick={generateBit} 
            disabled={loading}
            className="generate-button"
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Measuring Quantum State...
              </>
            ) : (
              <>
                <span className="button-icon">⚡</span>
                Generate Quantum Bit
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        {result && (
          <div className="results-section">
            {/* Big Bit Display */}
            <div className="bit-display">
              <div className="bit-label">Measured Bit</div>
              <div className="bit-value" data-bit={result.bit}>
                {result.bit}
              </div>
              <div className="bit-state">
                {result.bit === '0' ? '|0⟩ state' : '|1⟩ state'}
              </div>
            </div>

            {/* Measurement Statistics */}
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Total Shots</div>
                <div className="stat-value">{result.shots.toLocaleString()}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">|0⟩ Count</div>
                <div className="stat-value">{(result.counts['0'] || 0).toLocaleString()}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">|1⟩ Count</div>
                <div className="stat-value">{(result.counts['1'] || 0).toLocaleString()}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Distribution</div>
                <div className="stat-value">
                  {result.counts['0'] && result.counts['1'] 
                    ? `${((result.counts['0'] / result.shots) * 100).toFixed(1)}% / ${((result.counts['1'] / result.shots) * 100).toFixed(1)}%`
                    : 'N/A'}
                </div>
              </div>
            </div>

            {/* Circuit Diagram */}
            <div className="circuit-section">
              <h3 className="section-title">Quantum Circuit</h3>
              <pre className="circuit-display">{result.circuit}</pre>
              <div className="circuit-explanation">
                <p><strong>H</strong> = Hadamard gate creates superposition: |0⟩ → (|0⟩ + |1⟩)/√2</p>
                <p>Upon measurement, the qubit collapses to either |0⟩ or |1⟩ with equal probability</p>
              </div>
            </div>

            {/* Histogram */}
            {result.histogram && (
              <div className="histogram-section">
                <h3 className="section-title">Measurement Results Distribution</h3>
                <img 
                  src={result.histogram} 
                  alt="Measurement Histogram" 
                  className="histogram-image"
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Info Panel */}
      <div className="info-panel">
        <h3 className="info-title">How It Works</h3>
        <div className="info-steps">
          <div className="step">
            <div className="step-number">1</div>
            <div className="step-content">
              <h4>Initialize</h4>
              <p>Start with qubit in |0⟩ state</p>
            </div>
          </div>
          <div className="step">
            <div className="step-number">2</div>
            <div className="step-content">
              <h4>Superposition</h4>
              <p>Apply Hadamard gate to create equal superposition</p>
            </div>
          </div>
          <div className="step">
            <div className="step-number">3</div>
            <div className="step-content">
              <h4>Measure</h4>
              <p>Quantum state collapses to 0 or 1 randomly</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default QuantumBitGenerator;
