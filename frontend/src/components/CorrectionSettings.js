import React from 'react';
import './CorrectionSettings.css';

function CorrectionSettings({
  keyLength,
  shots,
  maxAttempts,
  enableCorrection,
  hardwareConnected,
  onKeyLength,
  onShots,
  onMaxAttempts,
  onEnableCorrection,
}) {
  return (
    <div className="correction-settings">
      <label>
        Key Length
        <select value={keyLength} onChange={(e) => onKeyLength(Number(e.target.value))}>
          <option value={128}>128-bit</option>
          <option value={256}>256-bit</option>
          <option value={512}>512-bit</option>
        </select>
      </label>

      <label>
        Shots
        <input
          type="number"
          min="100"
          max="10000"
          step="1"
          value={shots}
          onChange={(e) => onShots(Number(e.target.value) || 1024)}
        />
      </label>

      <label>
        Max Attempts
        <input
          type="number"
          min="1"
          max="10"
          step="1"
          value={maxAttempts}
          disabled={!enableCorrection || hardwareConnected}
          onChange={(e) => onMaxAttempts(Number(e.target.value) || 3)}
        />
      </label>

      <label className="correction-toggle">
        <input
          type="checkbox"
          checked={enableCorrection}
          disabled={hardwareConnected}
          onChange={(e) => onEnableCorrection(e.target.checked)}
        />
        Enable ML quality correction
      </label>
    </div>
  );
}

export default CorrectionSettings;
