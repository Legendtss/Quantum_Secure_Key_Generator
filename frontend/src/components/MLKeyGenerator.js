import React, { useMemo, useState } from 'react';
import './MLKeyGenerator.css';
import QualityIndicator from './QualityIndicator';
import CorrectionSettings from './CorrectionSettings';

const API_URL = process.env.REACT_APP_API_URL || 'https://quantum-secure-key-generator.onrender.com/api';

function MLKeyGenerator({ runtimeMode = 'simulator', ibmStatus = { connected: false, backend: null } }) {
  const [keyLength, setKeyLength] = useState(256);
  const [shots, setShots] = useState(1024);
  const [maxAttempts, setMaxAttempts] = useState(3);
  const [enableCorrection, setEnableCorrection] = useState(true);
  const [loading, setLoading] = useState(false);
  const [generatedKey, setGeneratedKey] = useState(null);
  const [error, setError] = useState('');

  const hardwareConnected = runtimeMode === 'hardware' && Boolean(ibmStatus?.connected && ibmStatus?.backend);

  const endpoint = useMemo(() => {
    if (enableCorrection && !hardwareConnected) {
      return '/ml/generate-key-improved';
    }
    return '/generate-key';
  }, [enableCorrection, hardwareConnected]);

  const qualityMetrics = useMemo(() => {
    if (!generatedKey) return null;
    const qa = generatedKey.ml_quality_assessment || {};
    const qualityScore = Number(qa.quality_score);
    const confidenceScore = Number(qa.confidence || 0);
    return {
      quality: qa.prediction || 'unknown',
      confidence: Number.isFinite(qualityScore) ? qualityScore : confidenceScore,
      attempts: Number(generatedKey.attempts || 1),
      improvement: Number(generatedKey?.improvement?.entropy_improvement_percent || 0),
      generationTimeMs: Number(generatedKey.generation_time_ms || 0),
      correctionApplied: Boolean(generatedKey.correction_applied),
    };
  }, [generatedKey]);

  const generateKey = async () => {
    setLoading(true);
    setError('');
    setGeneratedKey(null);

    try {
      const payload = {
        key_length: keyLength,
        shots,
      };

      if (endpoint === '/generate-key') {
        payload.enable_ml_correction = Boolean(enableCorrection && !hardwareConnected);
        payload.max_attempts = maxAttempts;
        payload.use_ibm = hardwareConnected;
      } else {
        payload.max_attempts = maxAttempts;
      }

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok || !data.success) {
        setError(data.error || 'Key generation failed');
        return;
      }

      setGeneratedKey(data.data);
    } catch (err) {
      setError('Failed to connect to backend service');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      setError('Clipboard copy failed on this browser');
    }
  };

  return (
    <section className="ml-key-generator-card">
      <header className="ml-key-generator-head">
        <h2>ML-Enhanced Key Generation</h2>
        <p>Generate quantum keys with optional ML entropy optimization, retry controls, and tail-risk reduction.</p>
      </header>

      <section className="ml-description-grid" aria-label="ML generator details">
        <article className="ml-description-card">
          <h3>What This Feature Does</h3>
          <p>
            This generator uses a trained entropy-regression model to estimate expected entropy and rank generated
            candidates. Instead of stopping at the first sample, the correction loop can explore multiple attempts
            and return the strongest entropy candidate within attempt and time limits.
          </p>
        </article>

        <article className="ml-description-card">
          <h3>Generation Flow</h3>
          <ol>
            <li>Generate an initial quantum key and compute core features.</li>
            <li>Predict entropy score and expected gain using the loaded ML regressor.</li>
            <li>Retry and rank candidates by measured entropy plus ML ranking score.</li>
            <li>Return the best candidate with entropy gain, attempts, and correction policy details.</li>
          </ol>
        </article>

        <article className="ml-description-card">
          <h3>How To Read Results</h3>
          <ul>
            <li><strong>Quality Ring:</strong> Entropy-oriented ranking score for the selected key.</li>
            <li><strong>Attempts:</strong> Number of candidates evaluated before final selection.</li>
            <li><strong>Correction:</strong> Whether multi-attempt optimization was applied.</li>
            <li><strong>Entropy Gain:</strong> Percent lift from first candidate to final selected key.</li>
          </ul>
        </article>
      </section>

      <CorrectionSettings
        keyLength={keyLength}
        shots={shots}
        maxAttempts={maxAttempts}
        enableCorrection={enableCorrection}
        hardwareConnected={hardwareConnected}
        onKeyLength={setKeyLength}
        onShots={setShots}
        onMaxAttempts={setMaxAttempts}
        onEnableCorrection={setEnableCorrection}
      />

      {hardwareConnected && (
        <div className="ml-inline-note">
          Hardware mode is active. ML correction loop is simulator-only, but quality scoring still appears in response.
        </div>
      )}

      <button className="ml-generate-btn" onClick={generateKey} disabled={loading} type="button">
        {loading ? 'Generating...' : 'Generate Key'}
      </button>

      {error && <div className="ml-error-box">{error}</div>}

      {generatedKey && qualityMetrics && (
        <article className="ml-results-panel" aria-live="polite">
          <div className="ml-results-top">
            <QualityIndicator quality={qualityMetrics.quality} confidence={qualityMetrics.confidence} />

            <div className="ml-metrics-list">
              <div><span>Time</span><strong>{qualityMetrics.generationTimeMs.toFixed(2)} ms</strong></div>
              <div><span>Attempts</span><strong>{qualityMetrics.attempts}</strong></div>
              <div><span>Correction</span><strong>{qualityMetrics.correctionApplied ? 'Applied' : 'Not Applied'}</strong></div>
              <div><span>Entropy Gain</span><strong>{qualityMetrics.improvement.toFixed(2)}%</strong></div>
            </div>
          </div>

          <div className="ml-key-grid">
            <div>
              <h4>Hex Key</h4>
              <pre>{generatedKey.hex}</pre>
              <button type="button" onClick={() => copyToClipboard(generatedKey.hex)}>Copy Hex</button>
            </div>
            <div>
              <h4>Binary Key (Preview)</h4>
              <pre>{`${generatedKey.binary?.slice(0, 128) || ''}${generatedKey.binary?.length > 128 ? '...' : ''}`}</pre>
              <button type="button" onClick={() => copyToClipboard(generatedKey.binary || '')}>Copy Binary</button>
            </div>
          </div>
        </article>
      )}
    </section>
  );
}

export default MLKeyGenerator;
