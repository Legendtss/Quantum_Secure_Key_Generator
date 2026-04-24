import React, { useEffect, useState } from 'react';
import './ABTestResults.css';

const API_URL = process.env.REACT_APP_API_URL || 'https://quantum-secure-key-generator.onrender.com/api';

function ABTestResults() {
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState(null);
  const [samplesPerVariant, setSamplesPerVariant] = useState(500);
  const [keyLength, setKeyLength] = useState(256);
  const [shots, setShots] = useState(1024);
  const [maxAttempts, setMaxAttempts] = useState(5);
  const [resetLog, setResetLog] = useState(false);

  const fetchResults = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/ml/ab-test-results`);
      const data = await response.json();
      if (!response.ok || !data.success) {
        setError(data.error || 'No A/B test data available yet');
        setResults(null);
        return;
      }
      setResults(data.data);
    } catch (err) {
      setError('Failed to fetch A/B test results');
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const runStrictAB = async () => {
    setRunning(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/ml/run-ab-test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          samples_per_variant: Number(samplesPerVariant),
          key_length: Number(keyLength),
          shots: Number(shots),
          max_attempts: Number(maxAttempts),
          reset_log: Boolean(resetLog),
        }),
      });
      const data = await response.json();
      if (!response.ok || !data.success) {
        setError(data.error || 'Failed to run strict A/B benchmark');
        return;
      }
      setResults(data.data);
      setResetLog(false);
    } catch (err) {
      setError('Failed to run strict A/B benchmark');
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, []);

  const control = results?.control || {};
  const treated = results?.treated || {};
  const improvement = results?.improvement || {};
  const thresholds = results?.thresholds || {};

  const barChart = [
    { name: 'Avg Entropy', control: Number(control.avg_entropy || 0), treated: Number(treated.avg_entropy || 0), scale: 1 },
    { name: 'P5 Entropy', control: Number(control.p5_entropy || 0), treated: Number(treated.p5_entropy || 0), scale: 1 },
    { name: 'Tail Risk %', control: Number(control.pct_below_threshold || 0), treated: Number(treated.pct_below_threshold || 0), scale: 100 },
  ].map((row) => {
    const c = Math.max(0, Math.min(100, (row.control / row.scale) * 100));
    const t = Math.max(0, Math.min(100, (row.treated / row.scale) * 100));
    return { ...row, controlWidth: c, treatedWidth: t };
  });

  if (loading) {
    return <section className="ab-panel">Loading A/B results...</section>;
  }

  return (
    <section className="ab-panel">
      <header className="ab-head">
        <div>
          <h2>Strict A/B Test Results</h2>
          <p>Entropy-maximization evaluation with tail metrics and latency tradeoff.</p>
        </div>
        <button type="button" onClick={fetchResults}>Refresh</button>
      </header>

      <section className="ab-runner">
        <h3>Run Strict A/B Benchmark</h3>
        <div className="ab-runner-grid">
          <label>
            Samples / Variant
            <input type="number" min="10" max="2000" value={samplesPerVariant} onChange={(e) => setSamplesPerVariant(e.target.value)} />
          </label>
          <label>
            Key Length
            <select value={keyLength} onChange={(e) => setKeyLength(e.target.value)}>
              <option value={128}>128-bit</option>
              <option value={256}>256-bit</option>
              <option value={512}>512-bit</option>
            </select>
          </label>
          <label>
            Shots
            <input type="number" min="1" max="10000" value={shots} onChange={(e) => setShots(e.target.value)} />
          </label>
          <label>
            Max Attempts
            <input type="number" min="1" max="10" value={maxAttempts} onChange={(e) => setMaxAttempts(e.target.value)} />
          </label>
          <label className="ab-checkbox">
            <input type="checkbox" checked={resetLog} onChange={(e) => setResetLog(e.target.checked)} />
            Reset Existing A/B Log
          </label>
        </div>
        <button type="button" className="ab-run-btn" onClick={runStrictAB} disabled={running}>
          {running ? 'Running Benchmark...' : 'Run Strict A/B'}
        </button>
      </section>

      {error && <div className="ab-error">{error}</div>}

      {results && (
        <>
          <div className="ab-columns">
            <article className="ab-card">
              <h3>Control (ML Off)</h3>
              <dl>
                <div><dt>Samples</dt><dd>{control.samples || 0}</dd></div>
                <div><dt>Avg Entropy</dt><dd>{Number(control.avg_entropy || 0).toFixed(4)}</dd></div>
                <div><dt>P5 Entropy</dt><dd>{Number(control.p5_entropy || 0).toFixed(4)}</dd></div>
                <div><dt>Tail Risk</dt><dd>{Number(control.pct_below_threshold || 0).toFixed(2)}%</dd></div>
                <div><dt>Avg Time</dt><dd>{Number(control.avg_time_ms || 0).toFixed(2)} ms</dd></div>
              </dl>
            </article>

            <article className="ab-card treated">
              <h3>Treated (ML On)</h3>
              <dl>
                <div><dt>Samples</dt><dd>{treated.samples || 0}</dd></div>
                <div><dt>Avg Entropy</dt><dd>{Number(treated.avg_entropy || 0).toFixed(4)}</dd></div>
                <div><dt>P5 Entropy</dt><dd>{Number(treated.p5_entropy || 0).toFixed(4)}</dd></div>
                <div><dt>Tail Risk</dt><dd>{Number(treated.pct_below_threshold || 0).toFixed(2)}%</dd></div>
                <div><dt>Avg Time</dt><dd>{Number(treated.avg_time_ms || 0).toFixed(2)} ms</dd></div>
                <div><dt>Avg Attempts</dt><dd>{Number(treated.avg_attempts || 0).toFixed(2)}</dd></div>
              </dl>
            </article>
          </div>

          <div className="ab-improvement">
            <div><span>Entropy Gain</span><strong>{Number(improvement.entropy_gain_percent || 0).toFixed(2)}%</strong></div>
            <div><span>P5 Entropy Gain</span><strong>{Number(improvement.p5_entropy_gain_percent || 0).toFixed(2)}%</strong></div>
            <div><span>Tail Risk Reduction</span><strong>{Number(improvement.tail_risk_reduction_percent || 0).toFixed(2)}%</strong></div>
            <div><span>Latency Cost</span><strong>{Number(improvement.latency_cost_percent || 0).toFixed(2)}%</strong></div>
            <div><span>ROI</span><strong>{Number(improvement.roi || 0).toFixed(2)}x</strong></div>
          </div>

          <section className="ab-chart">
            <h3>Control vs Treated Tradeoff Chart</h3>
            {barChart.map((row) => (
              <div className="ab-chart-row" key={row.name}>
                <span>{row.name}</span>
                <div className="ab-chart-bars">
                  <div className="bar control" style={{ width: `${row.controlWidth}%` }}>
                    C {row.control.toFixed(row.scale === 100 ? 2 : 4)}
                  </div>
                  <div className="bar treated" style={{ width: `${row.treatedWidth}%` }}>
                    T {row.treated.toFixed(row.scale === 100 ? 2 : 4)}
                  </div>
                </div>
              </div>
            ))}
          </section>

          <div className="ab-summary-note">
            Tail threshold: {Number(thresholds.tail_entropy_threshold || 0.95).toFixed(2)} |
            Strict readiness target: {Number(thresholds.strict_ab_min_samples_per_variant || 500)} samples/variant |
            {improvement.recommendation || 'No recommendation yet'}
          </div>
        </>
      )}
    </section>
  );
}

export default ABTestResults;
