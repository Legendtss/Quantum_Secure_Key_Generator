import React from 'react';
import './QualityIndicator.css';

function normalizeConfidence(confidence) {
  const value = Number(confidence);
  if (Number.isNaN(value) || value < 0) return 0;
  if (value <= 1) return Math.round(value * 100);
  return Math.round(Math.min(value, 100));
}

function QualityIndicator({ quality = 'unknown', confidence = 0 }) {
  const qualityKey = String(quality || 'unknown').toLowerCase();
  const confidencePct = normalizeConfidence(confidence);

  let label = 'Unknown';
  let toneClass = 'neutral';

  if (qualityKey === 'good') {
    label = 'High Quality';
    toneClass = 'good';
  } else if (qualityKey === 'bad') {
    label = 'Low Quality';
    toneClass = 'bad';
  }

  return (
    <div className={`quality-indicator ${toneClass}`} aria-live="polite">
      <div className="quality-ring" role="img" aria-label={`Model confidence ${confidencePct} percent`}>
        <span className="quality-percent">{confidencePct}%</span>
      </div>

      <div className="quality-meta">
        <div className="quality-label">{label}</div>
        <div className="quality-bar" aria-hidden="true">
          <div className="quality-bar-fill" style={{ width: `${confidencePct}%` }} />
        </div>
      </div>
    </div>
  );
}

export default QualityIndicator;
