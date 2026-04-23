import React, { useEffect, useState } from 'react';
import './MLMetricsDashboard.css';
import ImprovementSummary from './ImprovementSummary';

const API_URL = process.env.REACT_APP_API_URL || 'https://quantum-secure-key-generator.onrender.com/api';

function MLMetricsDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [status, setStatus] = useState(null);
  const [summary, setSummary] = useState(null);
  const [stats, setStats] = useState(null);
  const [lastUpdated, setLastUpdated] = useState('');

  const fetchMetrics = async () => {
    setLoading(true);
    setError('');

    try {
      const [statusRes, summaryRes, statsRes] = await Promise.all([
        fetch(`${API_URL}/ml/status`),
        fetch(`${API_URL}/ml/improvement-summary`),
        fetch(`${API_URL}/ml/correction-stats`),
      ]);

      const statusJson = await statusRes.json();
      const summaryJson = await summaryRes.json();
      const statsJson = await statsRes.json();

      setStatus(statusJson?.data || null);
      setSummary(summaryJson?.success ? summaryJson.data : null);
      setStats(statsJson?.success ? statsJson.data : null);

      if (!statusJson?.data?.model_loaded) {
        setError('ML model is not loaded yet. Train the model first to unlock correction analytics.');
      }

      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      setError('Failed to fetch ML dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  if (loading) {
    return <section className="ml-dashboard-shell">Loading ML metrics...</section>;
  }

  return (
    <section className="ml-dashboard-shell">
      <header className="ml-dashboard-head">
        <div>
          <h2>ML Metrics Dashboard</h2>
          <p>Track correction impact, latency overhead, and recommendation quality.</p>
        </div>
        <button type="button" onClick={fetchMetrics}>Refresh</button>
      </header>

      {error && <div className="ml-dashboard-error">{error}</div>}

      <div className="ml-dashboard-grid">
        <article>
          <h3>Model Status</h3>
          <p className="value">{status?.model_loaded ? 'Loaded' : 'Not Loaded'}</p>
          <small>Version: {status?.model?.model_version || 'n/a'}</small>
        </article>

        <article>
          <h3>Entropy Improvement</h3>
          <p className="value positive">{Number(summary?.entropy_improvement_percent || 0).toFixed(2)}%</p>
          <small>From treated vs control generation</small>
        </article>

        <article>
          <h3>Latency Cost</h3>
          <p className="value">{Number(summary?.latency_cost_percent || 0).toFixed(2)}%</p>
          <small>ML correction overhead percentage</small>
        </article>

        <article>
          <h3>ROI Ratio</h3>
          <p className="value">{Number(summary?.roi_ratio || 0).toFixed(2)}x</p>
          <small>{summary?.recommendation || 'No recommendation yet'}</small>
        </article>

        <article>
          <h3>Correction Rate</h3>
          <p className="value">{Number(stats?.correction_rate || 0).toFixed(2)}%</p>
          <small>{stats?.keys_with_correction || 0} corrected / {stats?.total_keys_generated || 0} total</small>
        </article>

        <article>
          <h3>Average Attempts</h3>
          <p className="value">{Number(stats?.avg_attempts_per_key || 0).toFixed(2)}</p>
          <small>Higher means more retries before final key</small>
        </article>
      </div>

      <ImprovementSummary summary={summary} stats={stats} />

      <footer className="ml-dashboard-foot">Last updated: {lastUpdated || 'n/a'}</footer>
    </section>
  );
}

export default MLMetricsDashboard;
