import React, { useState } from 'react';
import './App.css';
import QuantumBitGenerator from './components/QuantumBitGenerator';
import QuantumKeyGenerator from './components/QuantumKeyGenerator';
import QuantumInfo from './components/QuantumInfo';
import EncryptionDemo from './components/EncryptionDemo';
import EntropyAnalysis from './components/EntropyAnalysis';
import ComparisonTable from './components/ComparisonTable';
import IBMQuantumToggle from './components/IBMQuantumToggle';

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
              <p className="subtitle">Production-Grade Quantum Cryptographic Infrastructure</p>
            </div>
          </div>
          <div className="header-badge">
            <span className="badge-text">Enhanced Edition</span>
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
          className={`tab ${activeTab === 'encrypt' ? 'active' : ''}`}
          onClick={() => setActiveTab('encrypt')}
        >
          <span className="tab-icon">🔒</span>
          Encryption
        </button>
        <button 
          className={`tab ${activeTab === 'entropy' ? 'active' : ''}`}
          onClick={() => setActiveTab('entropy')}
        >
          <span className="tab-icon">📊</span>
          Entropy
        </button>
        <button 
          className={`tab ${activeTab === 'compare' ? 'active' : ''}`}
          onClick={() => setActiveTab('compare')}
        >
          <span className="tab-icon">⚔️</span>
          Compare
        </button>
        <button 
          className={`tab ${activeTab === 'ibm' ? 'active' : ''}`}
          onClick={() => setActiveTab('ibm')}
        >
          <span className="tab-icon">🖥️</span>
          IBM Quantum
        </button>
        <button 
          className={`tab ${activeTab === 'info' ? 'active' : ''}`}
          onClick={() => setActiveTab('info')}
        >
          <span className="tab-icon">📚</span>
          Learn
        </button>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        <div className="content-wrapper">
          {activeTab === 'bit' && <QuantumBitGenerator />}
          {activeTab === 'key' && <QuantumKeyGenerator />}
          {activeTab === 'encrypt' && <EncryptionDemo />}
          {activeTab === 'entropy' && <EntropyAnalysis />}
          {activeTab === 'compare' && <ComparisonTable />}
          {activeTab === 'ibm' && <IBMQuantumToggle />}
          {activeTab === 'info' && <QuantumInfo />}
        </div>
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>Built with Qiskit • AES-256 Encryption • IBM Quantum Support • NIST-Inspired Tests</p>
      </footer>
    </div>
  );
}

export default App;
