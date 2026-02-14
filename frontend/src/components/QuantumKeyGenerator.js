import React, { useState } from 'react';
import './QuantumKeyGenerator.css';

const API_URL = process.env.NODE_ENV === 'production'
  ? '/api'
  : (process.env.REACT_APP_API_URL || 'http://localhost:5000/api');

function QuantumKeyGenerator() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [keyLength, setKeyLength] = useState(256);
  const [shots, setShots] = useState(1024);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  const generateKey = async () => {
    setLoading(true);
    setError(null);
    setCopied(false);
    
    try {
      const response = await fetch(`${API_URL}/generate-key`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ key_length: keyLength, shots }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setResult(data.data);
      } else {
        setError(data.error || 'Failed to generate key');
      }
    } catch (err) {
      setError('Failed to connect to quantum backend. Make sure the server is running.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="key-generator-container">
      <div className="key-card">
        <div className="card-header">
          <h2 className="card-title">Quantum Secure Key Generator</h2>
          <p className="card-description">
            Generate cryptographically secure keys using quantum randomness
          </p>
        </div>

        <div className="controls-grid">
          <div className="input-group">
            <label htmlFor="keyLength">Key Length (bits)</label>
            <select
              id="keyLength"
              value={keyLength}
              onChange={(e) => setKeyLength(parseInt(e.target.value))}
              className="input-field"
            >
              <option value={128}>128-bit (AES-128)</option>
              <option value={256}>256-bit (AES-256)</option>
              <option value={512}>512-bit (Extra Secure)</option>
            </select>
            <span className="input-hint">Higher bit length = stronger encryption</span>
          </div>

          <div className="input-group">
            <label htmlFor="keyShots">Shots per Chunk</label>
            <input
              id="keyShots"
              type="number"
              min="100"
              max="10000"
              step="128"
              value={shots}
              onChange={(e) => setShots(parseInt(e.target.value))}
              className="input-field"
            />
            <span className="input-hint">Measurements per 8-qubit circuit</span>
          </div>
        </div>

        <button 
          onClick={generateKey} 
          disabled={loading}
          className="generate-button key-button"
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              Generating Quantum Key...
            </>
          ) : (
            <>
              <span className="button-icon">🔐</span>
              Generate Secure Key
            </>
          )}
        </button>

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        {result && (
          <div className="key-results">
            {/* Key Display */}
            <div className="key-display-section">
              <div className="key-header">
                <h3 className="section-title">Generated Quantum Key</h3>
                <div className="key-badge">{result.length}-bit</div>
              </div>
              
              <div className="key-output">
                <div className="key-format">
                  <span className="format-label">HEX:</span>
                  <div className="key-value-container">
                    <code className="key-value">{result.hex}</code>
                    <button 
                      onClick={() => copyToClipboard(result.hex)}
                      className="copy-button"
                      title="Copy to clipboard"
                    >
                      {copied ? '✓' : '📋'}
                    </button>
                  </div>
                </div>
                
                <div className="key-format">
                  <span className="format-label">Binary:</span>
                  <div className="key-value-container">
                    <code className="key-value binary-value">{result.binary}</code>
                    <button 
                      onClick={() => copyToClipboard(result.binary)}
                      className="copy-button"
                      title="Copy to clipboard"
                    >
                      {copied ? '✓' : '📋'}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Key Metadata */}
            <div className="key-metadata">
              <div className="meta-item">
                <span className="meta-label">SHA-256 Hash:</span>
                <code className="meta-value">{result.hash}</code>
              </div>
              <div className="meta-item">
                <span className="meta-label">Chunks Generated:</span>
                <span className="meta-value">{result.chunks_generated}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Shots per Chunk:</span>
                <span className="meta-value">{result.shots_per_chunk.toLocaleString()}</span>
              </div>
            </div>

            {/* Circuit Diagram */}
            <div className="circuit-section">
              <h3 className="section-title">Sample Quantum Circuit (8-qubit)</h3>
              <pre className="circuit-display">{result.circuit}</pre>
              <div className="circuit-info">
                <p>Each chunk uses 8 qubits with Hadamard gates in superposition</p>
                <p>Total quantum circuits executed: {result.chunks_generated}</p>
              </div>
            </div>

            {/* Security Info */}
            <div className="security-info">
              <h3 className="section-title">Security Properties</h3>
              <div className="security-grid">
                <div className="security-item">
                  <div className="security-icon">🔒</div>
                  <div>
                    <h4>True Randomness</h4>
                    <p>Based on quantum mechanical uncertainty, not algorithms</p>
                  </div>
                </div>
                <div className="security-item">
                  <div className="security-icon">🎲</div>
                  <div>
                    <h4>Unpredictable</h4>
                    <p>Impossible to predict or reproduce without measurement</p>
                  </div>
                </div>
                <div className="security-item">
                  <div className="security-icon">🛡️</div>
                  <div>
                    <h4>Cryptographic Grade</h4>
                    <p>{result.length}-bit key suitable for encryption protocols</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Use Cases Panel */}
      <div className="use-cases-panel">
        <h3 className="panel-title">Use Cases</h3>
        <div className="use-case-list">
          <div className="use-case">
            <div className="use-case-icon">🔐</div>
            <div>
              <h4>Encryption Keys</h4>
              <p>Generate keys for AES, RSA, and other cryptographic algorithms</p>
            </div>
          </div>
          <div className="use-case">
            <div className="use-case-icon">🔑</div>
            <div>
              <h4>One-Time Pads</h4>
              <p>Create perfectly secure one-time pad encryption keys</p>
            </div>
          </div>
          <div className="use-case">
            <div className="use-case-icon">🌐</div>
            <div>
              <h4>Secure Protocols</h4>
              <p>Use in TLS/SSL, VPNs, and secure communication protocols</p>
            </div>
          </div>
          <div className="use-case">
            <div className="use-case-icon">🎯</div>
            <div>
              <h4>Session Tokens</h4>
              <p>Generate unique session identifiers and authentication tokens</p>
            </div>
          </div>
        </div>

        <div className="warning-box">
          <div className="warning-icon">⚠️</div>
          <div>
            <h4>Educational Demo Only</h4>
            <p>This is a simulated quantum system for learning purposes. For production cryptography, use certified hardware quantum random number generators or vetted cryptographic libraries.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default QuantumKeyGenerator;
