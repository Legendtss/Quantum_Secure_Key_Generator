import React, { useEffect, useState } from 'react';
import './ABTestResults.css';

const API_URL = process.env.REACT_APP_API_URL || 'https://quantum-secure-key-generator.onrender.com/api';

function ABTestResults() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [results, setResults] = useState(null);

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

  useEffect(() => {
    fetchResults();
  }, []);

  if (loading) {
    return <section className="ab-panel">Loading A/B results...</section>;
  }

  const control = results?.control || {};
  const treated = results?.treated || {};
  const improvement = results?.improvement || {};

  return (
    <section className="ab-panel">
      <header className="ab-head">
        <div>
          <h2>A/B Test Results</h2>
          <p>Compare baseline key generation against ML-corrected generation.</p>
        </div>
        <button type="button" onClick={fetchResults}>Refresh</button>
      </header>

      <section className="ab-description" aria-label="A/B testing details">
        <article>
          <h3>Experiment Design</h3>
          <p>
            Control runs use standard single-pass generation. Treated runs enable ML correction, allowing
            controlled retries before selecting the best candidate. This isolates correction impact from core
            generator behavior.
          </p>
        </article>
        <article>
          <h3>Metric Meaning</h3>
          <ul>
            <li><strong>Good Quality:</strong> percentage of final keys classified as good.</li>
            <li><strong>Avg Entropy:</strong> average randomness score of selected final keys.</li>
            <li><strong>Avg Attempts:</strong> average retries used in treated sessions.</li>
            <li><strong>Latency Cost:</strong> time overhead introduced by correction flow.</li>
          </ul>
        </article>
        <article>
          <h3>Decision Rule</h3>
          <p>
            Prefer ML correction when entropy gain remains positive while latency cost stays acceptable for your
            deployment target. A positive ROI indicates correction is yielding meaningful quality benefit.
          </p>
        </article>
      </section>

      {error && <div className="ab-error">{error}</div>}

      {results && (
        <>
          <div className="ab-columns">
            <article className="ab-card">
              <h3>Control</h3>
              <dl>
                <div><dt>Samples</dt><dd>{control.samples || 0}</dd></div>
                <div><dt>Avg Entropy</dt><dd>{Number(control.avg_entropy || 0).toFixed(4)}</dd></div>
                <div><dt>Avg Time</dt><dd>{Number(control.avg_time_ms || 0).toFixed(2)} ms</dd></div>
                <div><dt>Good Quality</dt><dd>{Number(control.pct_good_quality || 0).toFixed(2)}%</dd></div>
              </dl>
            </article>

            <article className="ab-card treated">
              <h3>Treated (ML Correction)</h3>
              <dl>
                <div><dt>Samples</dt><dd>{treated.samples || 0}</dd></div>
                <div><dt>Avg Entropy</dt><dd>{Number(treated.avg_entropy || 0).toFixed(4)}</dd></div>
                <div><dt>Avg Time</dt><dd>{Number(treated.avg_time_ms || 0).toFixed(2)} ms</dd></div>
                <div><dt>Good Quality</dt><dd>{Number(treated.pct_good_quality || 0).toFixed(2)}%</dd></div>
                <div><dt>Avg Attempts</dt><dd>{Number(treated.avg_attempts || 0).toFixed(2)}</dd></div>
              </dl>
            </article>
          </div>

          <div className="ab-improvement">
            <div>
              <span>Entropy Gain</span>
              <strong>{Number(improvement.entropy_gain_percent || 0).toFixed(2)}%</strong>
            </div>
            <div>
              <span>Latency Cost</span>
              <strong>{Number(improvement.latency_cost_percent || 0).toFixed(2)}%</strong>
            </div>
            <div>
              <span>ROI</span>
              <strong>{Number(improvement.roi || 0).toFixed(2)}x</strong>
            </div>
          </div>
        </>
      )}
    </section>
  );
}

export default ABTestResults;
