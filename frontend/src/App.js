import React, { useState } from 'react';
import './App.css';
import QuantumBitGenerator from './components/QuantumBitGenerator';
import QuantumKeyGenerator from './components/QuantumKeyGenerator';
import QuantumInfo from './components/QuantumInfo';

function App() {
  const [activeTab, setActiveTab] = useState('bit');

  return (
    <div className="app">
      {/* Animated quantum background */}
      <div className="quantum-bg">
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
      </div>

      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo-section">
            <div className="quantum-icon">⚛</div>
            <div>
              <h1 className="title">Quantum Key Generator</h1>
              <p className="subtitle">True Randomness Through Superposition</p>
            </div>
          </div>
          <div className="header-badge">
            <span className="badge-text">Educational Demo</span>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="nav-tabs">
        <button 
          className={`tab ${activeTab === 'bit' ? 'active' : ''}`}
          onClick={() => setActiveTab('bit')}
        >
          <span className="tab-icon">🎲</span>
          Single Bit
        </button>
        <button 
          className={`tab ${activeTab === 'key' ? 'active' : ''}`}
          onClick={() => setActiveTab('key')}
        >
          <span className="tab-icon">🔐</span>
          Secure Key
        </button>
        <button 
          className={`tab ${activeTab === 'info' ? 'active' : ''}`}
          onClick={() => setActiveTab('info')}
        >
          <span className="tab-icon">📚</span>
          Learn More
        </button>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        <div className="content-wrapper">
          {activeTab === 'bit' && <QuantumBitGenerator />}
          {activeTab === 'key' && <QuantumKeyGenerator />}
          {activeTab === 'info' && <QuantumInfo />}
        </div>
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>Built with Qiskit • Simulated on AerSimulator • For Educational Purposes</p>
      </footer>
    </div>
  );
}

export default App;
