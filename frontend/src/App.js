import React, { useEffect, useMemo, useState } from 'react';
import './App.css';
import QuantumBitGenerator from './components/QuantumBitGenerator';
import QuantumKeyGenerator from './components/QuantumKeyGenerator';
import QuantumInfo from './components/QuantumInfo';
import EncryptionDemo from './components/EncryptionDemo';
import EntropyAnalysis from './components/EntropyAnalysis';
import ComparisonTable from './components/ComparisonTable';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function App() {
  const [activeTab, setActiveTab] = useState('bit');
  const [runtimeMode, setRuntimeMode] = useState('simulator');
  const [ibmStatus, setIbmStatus] = useState({
    connected: false,
    backend: null,
    backends: []
  });
  const [apiToken, setApiToken] = useState('');
  const [showToken, setShowToken] = useState(false);
  const [runtimeLoading, setRuntimeLoading] = useState(false);
  const [runtimeError, setRuntimeError] = useState(null);

  const sortedBackends = useMemo(() => {
    const list = Array.isArray(ibmStatus.backends) ? [...ibmStatus.backends] : [];
    return list.sort((a, b) => (a.pending_jobs ?? 999999) - (b.pending_jobs ?? 999999));
  }, [ibmStatus.backends]);

  const syncIBMStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/ibm/status`);
      const data = await response.json();
      const payload = data.data || {};
      setIbmStatus((prev) => ({
        ...prev,
        connected: !!payload.connected,
        backend: payload.current_backend || null
      }));
    } catch (err) {
      setRuntimeError('Failed to fetch IBM status');
    }
  };

  const refreshBackends = async () => {
    try {
      const response = await fetch(`${API_URL}/ibm/backends`);
      const data = await response.json();
      if (!data.success) {
        setRuntimeError(data.error || 'Failed to load backends');
        return;
      }
      const payload = data.data || {};
      setIbmStatus((prev) => ({
        ...prev,
        backends: payload.backends || []
      }));
    } catch (err) {
      setRuntimeError('Failed to load backends');
    }
  };

  useEffect(() => {
    syncIBMStatus();
  }, []);

  useEffect(() => {
    if (runtimeMode === 'hardware' && ibmStatus.connected) {
      refreshBackends();
    }
  }, [runtimeMode, ibmStatus.connected]);

  const connectIBM = async () => {
    if (!apiToken.trim()) {
      setRuntimeError('Please enter IBM Quantum API token');
      return;
    }

    setRuntimeLoading(true);
    setRuntimeError(null);
    try {
      const response = await fetch(`${API_URL}/ibm/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_token: apiToken })
      });
      const data = await response.json();
      if (!data.success) {
        setRuntimeError(data.error || 'Failed to connect IBM Quantum');
        return;
      }

      const payload = data.data || {};
      setIbmStatus({
        connected: true,
        backend: null,
        backends: payload.backends || []
      });
      setApiToken('');
      await syncIBMStatus();
    } catch (err) {
      setRuntimeError('Connection failed');
    } finally {
      setRuntimeLoading(false);
    }
  };

  const disconnectIBM = async () => {
    setRuntimeLoading(true);
    setRuntimeError(null);
    try {
      await fetch(`${API_URL}/ibm/disconnect`, { method: 'POST' });
      setIbmStatus({
        connected: false,
        backend: null,
        backends: []
      });
    } catch (err) {
      setRuntimeError('Disconnect failed');
    } finally {
      setRuntimeLoading(false);
    }
  };

  const selectBackend = async (backendName) => {
    if (!backendName) return;
    setRuntimeLoading(true);
    setRuntimeError(null);
    try {
      const response = await fetch(`${API_URL}/ibm/select-backend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ backend_name: backendName })
      });
      const data = await response.json();
      if (!data.success) {
        setRuntimeError(data.error || 'Failed to select backend');
        return;
      }
      const payload = data.data || {};
      setIbmStatus((prev) => ({
        ...prev,
        backend: payload.backend || backendName
      }));
    } catch (err) {
      setRuntimeError('Backend selection failed');
    } finally {
      setRuntimeLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="quantum-bg">
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
      </div>

      <header className="header">
        <div className="header-content">
          <div className="logo-section">
            <div className="quantum-icon">⚛</div>
            <div>
              <h1 className="title">Quantum Key Generator</h1>
              <p className="subtitle">Production-Grade Quantum Cryptographic Infrastructure</p>
            </div>
          </div>
          <div className="header-badge">
            <span className="badge-text">Enhanced Edition</span>
          </div>
        </div>

        <div className="runtime-switch">
          <label htmlFor="runtime-mode">Runtime Mode:</label>
          <select
            id="runtime-mode"
            value={runtimeMode}
            onChange={(e) => setRuntimeMode(e.target.value)}
            disabled={runtimeLoading}
          >
            <option value="simulator">Simulation</option>
            <option value="hardware">Real Hardware</option>
          </select>

          {runtimeMode === 'hardware' && !ibmStatus.connected && (
            <div className="runtime-inline-group">
              <input
                type={showToken ? 'text' : 'password'}
                value={apiToken}
                onChange={(e) => setApiToken(e.target.value)}
                placeholder="Enter IBM Quantum API token"
                disabled={runtimeLoading}
              />
              <button
                className="runtime-mini-btn"
                onClick={() => setShowToken((v) => !v)}
                disabled={runtimeLoading}
                type="button"
                title="Toggle token visibility"
              >
                {showToken ? '🙈' : '👁️'}
              </button>
              <button
                className="runtime-mini-btn"
                onClick={connectIBM}
                disabled={runtimeLoading || !apiToken.trim()}
                type="button"
              >
                {runtimeLoading ? 'Connecting...' : 'Connect'}
              </button>
            </div>
          )}

          {runtimeMode === 'hardware' && ibmStatus.connected && (
            <div className="runtime-inline-group">
              <select
                value={ibmStatus.backend || ''}
                onChange={(e) => selectBackend(e.target.value)}
                disabled={runtimeLoading}
              >
                <option value="" disabled>Select backend</option>
                {sortedBackends.map((backend) => (
                  <option key={backend.name} value={backend.name}>
                    {backend.name} • {backend.pending_jobs ?? 0} jobs
                  </option>
                ))}
              </select>
              <button
                className="runtime-mini-btn"
                onClick={refreshBackends}
                disabled={runtimeLoading}
                type="button"
              >
                Refresh
              </button>
              <button
                className="runtime-mini-btn danger"
                onClick={disconnectIBM}
                disabled={runtimeLoading}
                type="button"
              >
                Disconnect
              </button>
              <span className="runtime-status ok">
                Connected{ibmStatus.backend ? ` • ${ibmStatus.backend}` : ''}
              </span>
            </div>
          )}

          {runtimeError && <span className="runtime-status warn">{runtimeError}</span>}
        </div>
      </header>

      <nav className="nav-tabs">
        <button className={`tab ${activeTab === 'bit' ? 'active' : ''}`} onClick={() => setActiveTab('bit')}>
          <span className="tab-icon">🎲</span>
          Single Bit
        </button>
        <button className={`tab ${activeTab === 'key' ? 'active' : ''}`} onClick={() => setActiveTab('key')}>
          <span className="tab-icon">🔐</span>
          Secure Key
        </button>
        <button className={`tab ${activeTab === 'encrypt' ? 'active' : ''}`} onClick={() => setActiveTab('encrypt')}>
          <span className="tab-icon">🔒</span>
          Encryption
        </button>
        <button className={`tab ${activeTab === 'entropy' ? 'active' : ''}`} onClick={() => setActiveTab('entropy')}>
          <span className="tab-icon">📊</span>
          Entropy
        </button>
        <button className={`tab ${activeTab === 'compare' ? 'active' : ''}`} onClick={() => setActiveTab('compare')}>
          <span className="tab-icon">⚔️</span>
          Compare
        </button>
        <button className={`tab ${activeTab === 'info' ? 'active' : ''}`} onClick={() => setActiveTab('info')}>
          <span className="tab-icon">📚</span>
          Learn
        </button>
      </nav>

      <main className="main-content">
        <div className="content-wrapper">
          {activeTab === 'bit' && <QuantumBitGenerator runtimeMode={runtimeMode} ibmStatus={ibmStatus} />}
          {activeTab === 'key' && <QuantumKeyGenerator runtimeMode={runtimeMode} ibmStatus={ibmStatus} />}
          {activeTab === 'encrypt' && <EncryptionDemo />}
          {activeTab === 'entropy' && <EntropyAnalysis />}
          {activeTab === 'compare' && <ComparisonTable runtimeMode={runtimeMode} ibmStatus={ibmStatus} />}
          {activeTab === 'info' && <QuantumInfo />}
        </div>
      </main>

      <footer className="footer">
        <p>Built with Qiskit • AES-256 Encryption • IBM Quantum Support • NIST-Inspired Tests</p>
      </footer>
    </div>
  );
}

export default App;
