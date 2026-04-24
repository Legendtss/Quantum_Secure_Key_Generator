import React from 'react';
import './ImprovementSummary.css';

function ImprovementSummary({ summary, stats }) {
  const entropy = Number(summary?.entropy_improvement_percent || 0);
  const p5Entropy = Number(summary?.p5_entropy_gain_percent || 0);
  const tailRisk = Number(summary?.tail_risk_reduction_percent || 0);
  const latency = Number(summary?.latency_cost_percent || 0);
  const roi = Number(summary?.roi_ratio || 0);

  return (
    <section className="improvement-summary-card">
      <h3>Improvement Summary</h3>
      <div className="improvement-grid">
        <div>
          <span>Entropy Improvement</span>
          <strong className={entropy >= 0 ? 'positive' : 'negative'}>{entropy.toFixed(2)}%</strong>
        </div>
        <div>
          <span>P5 Entropy Gain</span>
          <strong className={p5Entropy >= 0 ? 'positive' : 'negative'}>{p5Entropy.toFixed(2)}%</strong>
        </div>
        <div>
          <span>Tail Risk Reduction</span>
          <strong className={tailRisk >= 0 ? 'positive' : 'negative'}>{tailRisk.toFixed(2)}%</strong>
        </div>
        <div>
          <span>Latency Cost</span>
          <strong className={latency <= 50 ? 'positive' : 'negative'}>{latency.toFixed(2)}%</strong>
        </div>
        <div>
          <span>ROI Ratio</span>
          <strong className={roi > 1 ? 'positive' : 'negative'}>{roi.toFixed(2)}x</strong>
        </div>
        <div>
          <span>Correction Adoption</span>
          <strong>{Number(stats?.correction_rate || 0).toFixed(2)}%</strong>
        </div>
      </div>
      <p>{summary?.recommendation || 'No recommendation available yet.'}</p>
    </section>
  );
}

export default ImprovementSummary;
