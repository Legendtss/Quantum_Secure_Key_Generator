import React, { useState } from 'react';
import './EncryptionDemo.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function EncryptionDemo() {
  const [plaintext, setPlaintext] = useState('');
  const [quantumKey, setQuantumKey] = useState('');
  const [keySize, setKeySize] = useState(256);
  const [ciphertext, setCiphertext] = useState('');
  const [iv, setIv] = useState('');
  const [decryptedText, setDecryptedText] = useState('');
  const [encryptionResult, setEncryptionResult] = useState(null);
  const [decryptionResult, setDecryptionResult] = useState(null);
  const [loading, setLoading] = useState({ key: false, encrypt: false, decrypt: false });
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState('');

  const generateQuantumKey = async () => {
    setLoading(prev => ({ ...prev, key: true }));
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/generate-key`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key_length: keySize, shots: 1024 }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setQuantumKey(data.data.hex);
        // Reset encryption results when new key is generated
        setCiphertext('');
        setIv('');
        setDecryptedText('');
        setEncryptionResult(null);
        setDecryptionResult(null);
      } else {
        setError(data.error || 'Failed to generate key');
      }
    } catch (err) {
      setError('Failed to connect to quantum backend');
    } finally {
      setLoading(prev => ({ ...prev, key: false }));
    }
  };

  const encryptMessage = async () => {
    if (!plaintext || !quantumKey) {
      setError('Please enter text and generate a quantum key first');
      return;
    }
    
    setLoading(prev => ({ ...prev, encrypt: true }));
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/encrypt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text: plaintext, 
          key: quantumKey,
          key_size: keySize
        }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setCiphertext(data.data.ciphertext);
        setIv(data.data.iv);
        setEncryptionResult(data.data);
        setDecryptedText('');
        setDecryptionResult(null);
      } else {
        setError(data.error || 'Encryption failed');
      }
    } catch (err) {
      setError('Failed to encrypt message');
    } finally {
      setLoading(prev => ({ ...prev, encrypt: false }));
    }
  };

  const decryptMessage = async () => {
    if (!ciphertext || !quantumKey || !iv) {
      setError('Please encrypt a message first');
      return;
    }
    
    setLoading(prev => ({ ...prev, decrypt: true }));
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/decrypt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          ciphertext, 
          key: quantumKey, 
          iv,
          key_size: keySize
        }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setDecryptedText(data.data.plaintext);
        setDecryptionResult(data.data);
      } else {
        setError(data.error || 'Decryption failed');
      }
    } catch (err) {
      setError('Failed to decrypt message');
    } finally {
      setLoading(prev => ({ ...prev, decrypt: false }));
    }
  };

  const copyToClipboard = (text, field) => {
    navigator.clipboard.writeText(text);
    setCopied(field);
    setTimeout(() => setCopied(''), 2000);
  };

  return (
    <div className="encryption-container">
      <div className="encryption-card">
        <div className="card-header">
          <h2 className="card-title">AES Encryption Demo</h2>
          <p className="card-description">
            Real cryptography using quantum-generated keys
          </p>
        </div>

        {/* Key Generation Section */}
        <div className="key-section">
          <h3 className="section-title">Step 1: Generate Quantum Key</h3>
          
          <div className="key-controls">
            <div className="input-group">
              <label htmlFor="keySize">Key Size</label>
              <select
                id="keySize"
                value={keySize}
                onChange={(e) => setKeySize(parseInt(e.target.value))}
                className="input-field"
              >
                <option value={128}>AES-128 (128 bits)</option>
                <option value={256}>AES-256 (256 bits)</option>
              </select>
            </div>
            
            <button 
              onClick={generateQuantumKey}
              disabled={loading.key}
              className="generate-button quantum-key-btn"
            >
              {loading.key ? (
                <><span className="spinner"></span> Generating...</>
              ) : (
                <><span className="button-icon">⚛</span> Generate Quantum Key</>
              )}
            </button>
          </div>

          {quantumKey && (
            <div className="key-display">
              <span className="key-label">Quantum Key (Hex):</span>
              <div className="key-value-container">
                <code className="key-value">{quantumKey}</code>
                <button 
                  onClick={() => copyToClipboard(quantumKey, 'key')}
                  className="copy-button"
                >
                  {copied === 'key' ? '✓' : '📋'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Encryption Section */}
        <div className="encrypt-section">
          <h3 className="section-title">Step 2: Encrypt Message</h3>
          
          <div className="input-group">
            <label htmlFor="plaintext">Message to Encrypt</label>
            <textarea
              id="plaintext"
              value={plaintext}
              onChange={(e) => setPlaintext(e.target.value)}
              placeholder="Enter your secret message here..."
              className="input-textarea"
              rows={4}
            />
          </div>

          <button 
            onClick={encryptMessage}
            disabled={loading.encrypt || !quantumKey || !plaintext}
            className="generate-button encrypt-btn"
          >
            {loading.encrypt ? (
              <><span className="spinner"></span> Encrypting...</>
            ) : (
              <><span className="button-icon">🔒</span> Encrypt with AES-{keySize}</>
            )}
          </button>

          {encryptionResult && (
            <div className="encryption-result">
              <div className="result-item">
                <span className="result-label">Ciphertext (Base64):</span>
                <div className="result-value-container">
                  <code className="result-value ciphertext">{ciphertext}</code>
                  <button 
                    onClick={() => copyToClipboard(ciphertext, 'cipher')}
                    className="copy-button"
                  >
                    {copied === 'cipher' ? '✓' : '📋'}
                  </button>
                </div>
              </div>
              
              <div className="result-item">
                <span className="result-label">IV (Initialization Vector):</span>
                <code className="result-value iv-value">{iv}</code>
              </div>

              <div className="encryption-meta">
                <span className="meta-badge">{encryptionResult.algorithm}</span>
                <span className="meta-info">Time: {encryptionResult.encryption_time_ms}ms</span>
                <span className="meta-info">Size: {encryptionResult.plaintext_length} → {encryptionResult.ciphertext_length} bytes</span>
              </div>
            </div>
          )}
        </div>

        {/* Decryption Section */}
        {ciphertext && (
          <div className="decrypt-section">
            <h3 className="section-title">Step 3: Decrypt Message</h3>
            
            <button 
              onClick={decryptMessage}
              disabled={loading.decrypt}
              className="generate-button decrypt-btn"
            >
              {loading.decrypt ? (
                <><span className="spinner"></span> Decrypting...</>
              ) : (
                <><span className="button-icon">🔓</span> Decrypt Message</>
              )}
            </button>

            {decryptedText && (
              <div className="decryption-result">
                <span className="result-label">Decrypted Message:</span>
                <div className="decrypted-message">{decryptedText}</div>
                
                <div className="verification-badge success">
                  {plaintext === decryptedText ? (
                    <>✓ Perfect Match - Encryption & Decryption Verified</>
                  ) : (
                    <>⚠ Warning: Decrypted text differs from original</>
                  )}
                </div>
                
                {decryptionResult && (
                  <span className="meta-info">Decryption Time: {decryptionResult.decryption_time_ms}ms</span>
                )}
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}
      </div>

      {/* Info Panel */}
      <div className="info-panel">
        <h3 className="panel-title">How It Works</h3>
        
        <div className="info-item">
          <div className="info-icon">⚛</div>
          <div>
            <h4>Quantum Key Generation</h4>
            <p>Keys are generated using quantum superposition, providing true randomness impossible to predict or reproduce.</p>
          </div>
        </div>

        <div className="info-item">
          <div className="info-icon">🔐</div>
          <div>
            <h4>AES Encryption</h4>
            <p>Advanced Encryption Standard (AES) in CBC mode - the same algorithm used by governments and banks worldwide.</p>
          </div>
        </div>

        <div className="info-item">
          <div className="info-icon">🔑</div>
          <div>
            <h4>Initialization Vector</h4>
            <p>A random IV ensures the same plaintext encrypts differently each time, preventing pattern analysis.</p>
          </div>
        </div>

        <div className="security-note">
          <strong>Security Note:</strong> This demo shows the complete encryption flow. In production, never expose keys in the browser.
        </div>
      </div>
    </div>
  );
}

export default EncryptionDemo;
