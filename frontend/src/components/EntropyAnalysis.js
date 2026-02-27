import React, { useState } from 'react';
import './EntropyAnalysis.css';

const API_URL = process.env.REACT_APP_API_URL || 'https://quantum-secure-key-generator.onrender.com/api';

function EntropyAnalysis() {
  const [bitString, setBitString] = useState('');
  const [bitLength, setBitLength] = useState(256);
  const [loading, setLoading] = useState({ generate: false, analyze: false });
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);

  const generateTestSequence = async () => {
    setLoading(prev => ({ ...prev, generate: true }));
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/generate-key`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key_length: bitLength, shots: 1024 }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setBitString(data.data.binary);
        setAnalysisResult(null);
      } else {
        setError(data.error || 'Failed to generate sequence');
      }
    } catch (err) {
      setError('Failed to connect to quantum backend');
    } finally {
      setLoading(prev => ({ ...prev, generate: false }));
    }
  };

  const analyzeEntropy = async () => {
    if (!bitString || bitString.length < 20) {
      setError('Please enter at least 20 bits for meaningful analysis');
      return;
    }
    
    setLoading(prev => ({ ...prev, analyze: true }));
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/analyze-entropy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bit_string: bitString }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setAnalysisResult(data.data);
      } else {
        setError(data.error || 'Analysis failed');
      }
    } catch (err) {
      setError('Failed to analyze entropy');
    } finally {
      setLoading(prev => ({ ...prev, analyze: false }));
    }
  };

  const getStatusClass = (passed) => passed ? 'pass' : 'fail';
  const getQualityClass = (quality) => {
    const q = quality?.toLowerCase() || '';
    if (q === 'excellent') return 'excellent';
    if (q === 'good') return 'good';
    if (q === 'acceptable') return 'acceptable';
    return 'poor';
  };

  return (
    <div className="entropy-container">
      <div className="entropy-card">
        <div className="card-header">
          <h2 className="card-title">Entropy Analysis</h2>
          <p className="card-description">
            Statistical tests to validate quantum randomness quality
          </p>
        </div>

        {/* Input Section */}
        <div className="input-section">
          <div className="generate-controls">
            <div className="input-group">
              <label htmlFor="bitLength">Bit Length</label>
              <select
                id="bitLength"
                value={bitLength}
                onChange={(e) => setBitLength(parseInt(e.target.value))}
                className="input-field"
              >
                <option value={128}>128 bits</option>
                <option value={256}>256 bits</option>
                <option value={512}>512 bits</option>
              </select>
            </div>
            
            <button 
              onClick={generateTestSequence}
              disabled={loading.generate}
              className="generate-button gen-btn"
            >
              {loading.generate ? (
                <><span className="spinner"></span> Generating...</>
              ) : (
                <><span className="button-icon">⚛</span> Generate Quantum Sequence</>
              )}
            </button>
          </div>

          <div className="input-group">
            <label htmlFor="bitString">Bit String to Analyze</label>
            <textarea
              id="bitString"
              value={bitString}
              onChange={(e) => {
                const val = e.target.value.replace(/[^01]/g, '');
                setBitString(val);
              }}
              placeholder="Enter binary string (0s and 1s only) or generate one above..."
              className="input-textarea bit-input"
              rows={4}
            />
            <span className="input-hint">
              {bitString.length} bits entered | Min: 20 bits recommended
            </span>
          </div>

          <button 
            onClick={analyzeEntropy}
            disabled={loading.analyze || bitString.length < 20}
            className="generate-button analyze-btn"
          >
            {loading.analyze ? (
              <><span className="spinner"></span> Analyzing...</>
            ) : (
              <><span className="button-icon">📊</span> Run Entropy Analysis</>
            )}
          </button>
        </div>

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        {/* Results Section */}
        {analysisResult && (
          <div className="analysis-results">
            {/* Overall Score */}
            <div className="score-section">
              <div className="score-display">
                <div className={`score-circle ${getQualityClass(analysisResult.verdict?.split(' ')[0])}`}>
                  <span className="score-value">{analysisResult.overall_score}%</span>
                </div>
                <div className="score-info">
                  <h3 className="verdict">{analysisResult.verdict}</h3>
                  <p className="score-detail">
                    {analysisResult.passed_tests}/{analysisResult.total_tests} tests passed
                  </p>
                  <p className="bit-count">{analysisResult.bit_string_length} bits analyzed</p>
                </div>
              </div>
            </div>

            {/* Individual Tests */}
            <div className="tests-section">
              <h3 className="section-title">Test Results</h3>
              
              {Object.entries(analysisResult.tests).map(([testKey, test]) => (
                <div key={testKey} className={`test-card ${getStatusClass(test.passed)}`}>
                  <div className="test-header">
                    <span className={`status-badge ${test.passed ? 'pass' : 'fail'}`}>
                      {test.passed ? '✓ PASS' : '✗ FAIL'}
                    </span>
                    <span className={`quality-badge ${getQualityClass(test.quality)}`}>
                      {test.quality || 'N/A'}
                    </span>
                  </div>
                  
                  <h4 className="test-name">{test.test_name}</h4>
                  <p className="test-description">{test.description}</p>
                  
                  <div className="test-details">
                    {/* Frequency Test */}
                    {testKey === 'frequency' && (
                      <>
                        <div className="detail-row">
                          <span className="detail-label">0s / 1s:</span>
                          <span className="detail-value">
                            {test.zeros_count} ({test.proportion_zeros}%) / {test.ones_count} ({test.proportion_ones}%)
                          </span>
                        </div>
                        <div className="detail-row">
                          <span className="detail-label">Deviation from 50%:</span>
                          <span className="detail-value">{test.deviation_from_50}%</span>
                        </div>
                        <div className="detail-row">
                          <span className="detail-label">Chi-Square:</span>
                          <span className="detail-value">{test.chi_square} (threshold: {test.threshold})</span>
                        </div>
                      </>
                    )}
                    
                    {/* Runs Test */}
                    {testKey === 'runs' && (
                      <>
                        <div className="detail-row">
                          <span className="detail-label">Total Runs:</span>
                          <span className="detail-value">{test.total_runs}</span>
                        </div>
                        <div className="detail-row">
                          <span className="detail-label">Expected Runs:</span>
                          <span className="detail-value">{test.expected_runs}</span>
                        </div>
                        <div className="detail-row">
                          <span className="detail-label">Z-Score:</span>
                          <span className="detail-value">{test.z_score} (threshold: ±{test.threshold})</span>
                        </div>
                      </>
                    )}
                    
                    {/* Shannon Entropy */}
                    {testKey === 'shannon_entropy' && (
                      <>
                        <div className="detail-row">
                          <span className="detail-label">Entropy:</span>
                          <span className="detail-value">{test.entropy} / {test.max_entropy}</span>
                        </div>
                        <div className="entropy-bar">
                          <div 
                            className="entropy-fill" 
                            style={{ width: `${test.entropy_percentage}%` }}
                          ></div>
                        </div>
                        <p className="interpretation">{test.interpretation}</p>
                      </>
                    )}
                    
                    {/* Serial Test */}
                    {testKey === 'serial' && (
                      <>
                        <div className="pattern-grid">
                          {Object.entries(test.pattern_proportions).map(([pattern, percentage]) => (
                            <div key={pattern} className="pattern-item">
                              <span className="pattern-label">{pattern}</span>
                              <div className="pattern-bar">
                                <div 
                                  className="pattern-fill" 
                                  style={{ width: `${percentage / 0.5}%` }}
                                ></div>
                              </div>
                              <span className="pattern-value">{percentage}%</span>
                            </div>
                          ))}
                        </div>
                        <div className="detail-row">
                          <span className="detail-label">Expected:</span>
                          <span className="detail-value">25% each</span>
                        </div>
                      </>
                    )}
                    
                    {/* Longest Run */}
                    {testKey === 'longest_run' && (
                      <>
                        <div className="detail-row">
                          <span className="detail-label">Longest Run (1s):</span>
                          <span className="detail-value">{test.longest_run_ones}</span>
                        </div>
                        <div className="detail-row">
                          <span className="detail-label">Longest Run (0s):</span>
                          <span className="detail-value">{test.longest_run_zeros}</span>
                        </div>
                        <div className="detail-row">
                          <span className="detail-label">Expected Max:</span>
                          <span className="detail-value">~{test.expected_max_run}</span>
                        </div>
                      </>
                    )}
                    
                    {/* Autocorrelation */}
                    {testKey === 'autocorrelation' && (
                      <>
                        <div className="detail-row">
                          <span className="detail-label">Autocorrelation:</span>
                          <span className="detail-value">{test.autocorrelation}</span>
                        </div>
                        <div className="detail-row">
                          <span className="detail-label">Z-Score:</span>
                          <span className="detail-value">{test.z_score} (threshold: ±{test.threshold})</span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Info Panel */}
      <div className="info-panel">
        <h3 className="panel-title">About Randomness Tests</h3>
        
        <div className="test-info">
          <h4>Frequency Test</h4>
          <p>Checks if 0s and 1s appear equally. True randomness should have ~50% each.</p>
        </div>
        
        <div className="test-info">
          <h4>Runs Test</h4>
          <p>Counts consecutive sequences. Too many or too few runs indicate patterns.</p>
        </div>
        
        <div className="test-info">
          <h4>Shannon Entropy</h4>
          <p>Measures information density. Perfect randomness = 1.0 bits per bit.</p>
        </div>
        
        <div className="test-info">
          <h4>Serial Test</h4>
          <p>Checks 2-bit patterns (00, 01, 10, 11). Each should appear ~25%.</p>
        </div>
        
        <div className="test-info">
          <h4>Longest Run Test</h4>
          <p>Detects unusually long sequences of identical bits.</p>
        </div>
        
        <div className="test-info">
          <h4>Autocorrelation</h4>
          <p>Checks if bits are correlated with their neighbors. Should be ~0.</p>
        </div>

        <div className="nist-note">
          <strong>NIST-Inspired Tests</strong>
          <p>These tests are based on NIST SP 800-22 statistical test suite for random number generators.</p>
        </div>
      </div>
    </div>
  );
}

export default EntropyAnalysis;
