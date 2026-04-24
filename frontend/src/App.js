import React, { useEffect, useMemo, useState } from 'react';
import './App.css';
import QuantumBitGenerator from './components/QuantumBitGenerator';
import QuantumKeyGenerator from './components/QuantumKeyGenerator';
import QuantumInfo from './components/QuantumInfo';
import EncryptionDemo from './components/EncryptionDemo';
import EntropyAnalysis from './components/EntropyAnalysis';
import ComparisonTable from './components/ComparisonTable';
import MLKeyGenerator from './components/MLKeyGenerator';
import ABTestResults from './components/ABTestResults';

const API_URL = process.env.REACT_APP_API_URL || 'https://quantum-secure-key-generator.onrender.com/api';
const SUPPORT_UPI_ID = 'shashankts2004@oksbi';
const SUPPORT_UPI_LINK = `upi://pay?pa=${encodeURIComponent(SUPPORT_UPI_ID)}&pn=${encodeURIComponent('Shashank T S')}&tn=${encodeURIComponent('Support Quantum Key Generator')}`;

const NAV_SECTIONS = [
  {
    id: 'core',
    title: 'Core Tools',
    emoji: '🔐',
    items: [
      { key: 'bit', icon: 'BIT', label: 'Bit Simulator', hint: 'Single quantum bit generation' },
      { key: 'key', icon: 'KEY', label: 'Key Generator', hint: 'Secure multi-bit key generation' },
      { key: 'encrypt', icon: 'ENC', label: 'Encryption Suite', hint: 'Encrypt and decrypt data/files' },
      { key: 'entropy', icon: 'RND', label: 'Randomness Test', hint: 'Entropy and statistical quality checks' },
    ],
  },
  {
    id: 'ml',
    title: 'ML Workflow',
    emoji: '🤖',
    items: [
      { key: 'ml-gen', icon: 'ML', label: 'ML Generator', hint: 'Generate with correction loop', primary: true },
      { key: 'ab-test', icon: 'AB', label: 'A/B Results', hint: 'Control vs treated comparison' },
    ],
  },
  {
    id: 'analysis',
    title: 'Analysis',
    emoji: '📊',
    items: [
      { key: 'compare', icon: 'CMP', label: 'Output Comparison', hint: 'Classical vs quantum quality' },
    ],
  },
  {
    id: 'learn',
    title: 'Learn',
    emoji: '📚',
    items: [
      { key: 'info', icon: 'DOC', label: 'Learning Center', hint: 'Concepts and documentation' },
    ],
  },
];

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
  const [supportCopied, setSupportCopied] = useState(false);

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

  const activeItem = useMemo(() => {
    for (const section of NAV_SECTIONS) {
      for (const item of section.items) {
        if (item.key === activeTab) {
          return { ...item, sectionTitle: section.title, sectionEmoji: section.emoji };
        }
      }
    }
    return null;
  }, [activeTab]);

  const copySupportUpi = async () => {
    try {
      await navigator.clipboard.writeText(SUPPORT_UPI_ID);
      setSupportCopied(true);
      setTimeout(() => setSupportCopied(false), 1800);
    } catch (err) {
      setRuntimeError('Unable to copy UPI ID on this browser.');
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
          <div className="header-actions">
            <div className="header-badge">
              <span className="badge-text">Enhanced Edition</span>
            </div>
            <div className="support-card">
              <p className="support-title">Support This Project</p>
              <p className="support-upi">{SUPPORT_UPI_ID}</p>
              <div className="support-actions">
                <button type="button" className="support-btn" onClick={copySupportUpi}>
                  {supportCopied ? 'Copied' : 'Copy UPI'}
                </button>
                <a className="support-btn pay" href={SUPPORT_UPI_LINK}>
                  Pay via UPI
                </a>
              </div>
            </div>
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
                {showToken ? 'Hide' : 'Show'}
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
                    {backend.name} - {backend.pending_jobs ?? 0} jobs
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
                Connected{ibmStatus.backend ? ` - ${ibmStatus.backend}` : ''}
              </span>
            </div>
          )}

          {runtimeError && <span className="runtime-status warn">{runtimeError}</span>}
        </div>
      </header>

      <main className="main-content">
        <div className="workspace-grid">
          <aside className="sidebar-nav" aria-label="Tool navigation">
            {NAV_SECTIONS.map((section) => (
              <section className="nav-group" key={section.id}>
                <h3 className="nav-group-title">
                  <span>{section.emoji}</span>
                  {section.title}
                </h3>
                <div className="nav-group-items">
                  {section.items.map((item) => (
                    <button
                      key={item.key}
                      className={`tab ${activeTab === item.key ? 'active' : ''} ${item.primary ? 'primary' : ''}`}
                      onClick={() => setActiveTab(item.key)}
                    >
                      <span className="tab-icon">{item.icon}</span>
                      <span className="tab-text-wrap">
                        <span className="tab-label">{item.label}</span>
                        <span className="tab-hint">{item.hint}</span>
                      </span>
                    </button>
                  ))}
                </div>
              </section>
            ))}
          </aside>

          <div className="content-panel">
            {activeItem && (
              <div className="panel-headline">
                <div className="panel-headline-title">
                  <span>{activeItem.sectionEmoji}</span>
                  <h2>{activeItem.label}</h2>
                </div>
                <p>{activeItem.hint}</p>
              </div>
            )}

            <div className="content-wrapper">
              {activeTab === 'bit' && <QuantumBitGenerator runtimeMode={runtimeMode} ibmStatus={ibmStatus} />}
              {activeTab === 'key' && <QuantumKeyGenerator runtimeMode={runtimeMode} ibmStatus={ibmStatus} />}
              {activeTab === 'encrypt' && <EncryptionDemo />}
              {activeTab === 'entropy' && <EntropyAnalysis />}
              {activeTab === 'compare' && <ComparisonTable runtimeMode={runtimeMode} ibmStatus={ibmStatus} />}
              {activeTab === 'info' && <QuantumInfo />}
              {activeTab === 'ml-gen' && <MLKeyGenerator runtimeMode={runtimeMode} ibmStatus={ibmStatus} />}
              {activeTab === 'ab-test' && <ABTestResults />}
            </div>
          </div>
        </div>
      </main>

      <footer className="footer">
        <p>Built with Qiskit, AES-256 Encryption, IBM Quantum Support, and ML Quality Correction</p>
      </footer>
    </div>
  );
}

export default App;

