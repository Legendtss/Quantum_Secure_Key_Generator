import React, { useState, useEffect, useCallback } from 'react';
import './IBMQuantumToggle.css';

const API_BASE = 'http://localhost:5000/api';

function IBMQuantumToggle({ onStatusChange }) {
    const [status, setStatus] = useState({
        connected: false,
        available: false,
        backend: null,
        backends: []
    });
    const [apiToken, setApiToken] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [showToken, setShowToken] = useState(false);
    const [testResult, setTestResult] = useState(null);

    const fetchStatus = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE}/ibm/status`);
            const data = await response.json();
            const payload = data.data || {};
            setStatus(prev => ({
                ...prev,
                connected: payload.connected,
                available: payload.ibm_available,
                backend: payload.current_backend
            }));
            if (onStatusChange) {
                onStatusChange(payload.connected, payload.current_backend);
            }
        } catch (err) {
            console.error('Failed to fetch IBM status:', err);
        }
    }, [onStatusChange]);

    useEffect(() => {
        fetchStatus();
    }, [fetchStatus]);

    const handleConnect = async () => {
        if (!apiToken.trim()) {
            setError('Please enter your IBM Quantum API token');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE}/ibm/connect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_token: apiToken })
            });

            const data = await response.json();
            const payload = data.data || {};

            if (data.success) {
                setStatus(prev => ({
                    ...prev,
                    connected: true,
                    backends: payload.backends || []
                }));
                setApiToken(''); // Clear token from memory
                if (onStatusChange) {
                    onStatusChange(true, status.backend);
                }
            } else {
                setError(data.error || 'Failed to connect');
            }
        } catch (err) {
            setError('Connection failed: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDisconnect = async () => {
        setLoading(true);
        try {
            await fetch(`${API_BASE}/ibm/disconnect`, { method: 'POST' });
            setStatus({
                connected: false,
                available: status.available,
                backend: null,
                backends: []
            });
            setTestResult(null);
            if (onStatusChange) {
                onStatusChange(false, null);
            }
        } catch (err) {
            setError('Disconnect failed: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSelectBackend = async (backendName) => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE}/ibm/select-backend`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ backend_name: backendName })
            });

            const data = await response.json();
            const payload = data.data || {};

            if (data.success) {
                setStatus(prev => ({
                    ...prev,
                    backend: payload.backend || backendName
                }));
                if (onStatusChange) {
                    onStatusChange(true, payload.backend || backendName);
                }
            } else {
                setError(data.error || 'Failed to select backend');
            }
        } catch (err) {
            setError('Backend selection failed: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleTestGeneration = async () => {
        if (!status.connected || !status.backend) {
            setError('Please connect and select a backend first');
            return;
        }

        setLoading(true);
        setError(null);
        setTestResult(null);

        try {
            const response = await fetch(`${API_BASE}/generate-bit-ibm`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ shots: 100, use_ibm: true })
            });

            const data = await response.json();
            const payload = data.data || {};

            if (data.success) {
                setTestResult({
                    bit: payload.bit,
                    backend: payload.backend,
                    shots: payload.shots,
                    counts: payload.counts || {}
                });
            } else {
                setError(data.error || 'Generation failed');
            }
        } catch (err) {
            setError('Test generation failed: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    const refreshBackends = async () => {
        if (!status.connected) return;

        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/ibm/backends`);
            const data = await response.json();
            const payload = data.data || {};

            if (data.success) {
                setStatus(prev => ({
                    ...prev,
                    backends: payload.backends || []
                }));
            }
        } catch (err) {
            setError('Failed to refresh backends');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="ibm-quantum-toggle">
            <div className="ibm-header">
                <h2>IBM Quantum Hardware</h2>
                <div className={`status-indicator ${status.connected ? 'connected' : 'disconnected'}`}>
                    <span className="status-dot"></span>
                    {status.connected ? 'Connected' : 'Disconnected'}
                </div>
            </div>

            {error && (
                <div className="error-banner">
                    <span className="error-icon">❌</span>
                    {error}
                    <button className="dismiss-btn" onClick={() => setError(null)}>×</button>
                </div>
            )}

            {!status.connected ? (
                <div className="connect-section">
                    <div className="info-text">
                        <p>Connect to IBM Quantum to run circuits on real quantum hardware.</p>
                        <p className="hint">
                            Get your API token from <a 
                                href="https://quantum.ibm.com/" 
                                target="_blank" 
                                rel="noopener noreferrer"
                            >quantum.ibm.com</a>
                        </p>
                    </div>

                    <div className="token-input-group">
                        <label>IBM Quantum API Token</label>
                        <div className="token-input-wrapper">
                            <input
                                type={showToken ? 'text' : 'password'}
                                value={apiToken}
                                onChange={(e) => setApiToken(e.target.value)}
                                placeholder="Enter your IBM Quantum API token"
                                disabled={loading}
                            />
                            <button 
                                className="toggle-visibility"
                                onClick={() => setShowToken(!showToken)}
                                type="button"
                            >
                                {showToken ? '🙈' : '👁️'}
                            </button>
                        </div>
                    </div>

                    <button 
                        className="connect-btn"
                        onClick={handleConnect}
                        disabled={loading || !apiToken.trim()}
                    >
                        {loading ? 'Connecting...' : 'Connect to IBM Quantum'}
                    </button>
                </div>
            ) : (
                <div className="connected-section">
                    <div className="backend-selection">
                        <div className="backend-header">
                            <label>Select Backend</label>
                            <button 
                                className="refresh-btn" 
                                onClick={refreshBackends}
                                disabled={loading}
                                title="Refresh backend list"
                            >
                                🔄
                            </button>
                        </div>

                        {status.backends.length > 0 ? (
                            <div className="backend-grid">
                                {status.backends.map((backend) => (
                                    <button
                                        key={backend.name}
                                        className={`backend-card ${status.backend === backend.name ? 'selected' : ''}`}
                                        onClick={() => handleSelectBackend(backend.name)}
                                        disabled={loading}
                                    >
                                        <div className="backend-name">{backend.name}</div>
                                        <div className="backend-info">
                                            <span className="qubits">{backend.num_qubits} qubits</span>
                                            <span className={`backend-status ${backend.status}`}>
                                                {backend.status}
                                            </span>
                                        </div>
                                        {backend.simulator && (
                                            <span className="simulator-badge">Simulator</span>
                                        )}
                                    </button>
                                ))}
                            </div>
                        ) : (
                            <p className="no-backends">No backends available. Click refresh to load.</p>
                        )}
                    </div>

                    {status.backend && (
                        <div className="test-section">
                            <h3>Test Quantum Generation</h3>
                            <p>Generate a quantum random bit using {status.backend}</p>
                            <button 
                                className="test-btn"
                                onClick={handleTestGeneration}
                                disabled={loading}
                            >
                                {loading ? 'Generating...' : 'Generate Test Bit'}
                            </button>

                            {testResult && (
                                <div className="test-result">
                                    <div className="result-item">
                                        <span className="label">Generated Bit:</span>
                                        <span className="value quantum-bit">{testResult.bit}</span>
                                    </div>
                                    <div className="result-item">
                                        <span className="label">Counts:</span>
                                        <span className="value">{JSON.stringify(testResult.counts)}</span>
                                    </div>
                                    <div className="result-item">
                                        <span className="label">Backend:</span>
                                        <span className="value">{testResult.backend}</span>
                                    </div>
                                    <div className="result-item">
                                        <span className="label">Shots:</span>
                                        <span className="value">{testResult.shots}</span>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    <button 
                        className="disconnect-btn"
                        onClick={handleDisconnect}
                        disabled={loading}
                    >
                        Disconnect
                    </button>
                </div>
            )}

            <div className="ibm-footer">
                <div className="info-box">
                    <h4>About IBM Quantum</h4>
                    <p>
                        IBM Quantum provides access to real quantum computers via the cloud.
                        When connected, you can generate truly quantum random numbers using 
                        physical quantum hardware instead of local simulation.
                    </p>
                    <ul>
                        <li><strong>Simulators:</strong> Fast, ideal quantum behavior (no noise)</li>
                        <li><strong>Real Hardware:</strong> Actual quantum computers with queue times</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}

export default IBMQuantumToggle;
