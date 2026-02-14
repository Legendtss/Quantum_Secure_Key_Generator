import React from 'react';
import './QuantumInfo.css';

function QuantumInfo() {
  return (
    <div className="info-container">
      <div className="info-hero">
        <h2 className="info-hero-title">Understanding Quantum Randomness</h2>
        <p className="info-hero-subtitle">
          Explore how quantum mechanics enables true randomness for cryptographic security
        </p>
      </div>

      <div className="info-grid">
        {/* What is Quantum Randomness */}
        <div className="info-section">
          <div className="section-icon">🌌</div>
          <h3 className="section-heading">What is Quantum Randomness?</h3>
          <p className="section-text">
            Quantum randomness arises from the fundamental uncertainty principle in quantum mechanics. 
            Unlike classical random number generators that use deterministic algorithms, quantum 
            randomness is based on the inherent unpredictability of quantum measurements.
          </p>
          <div className="highlight-box">
            <strong>Key Principle:</strong> When a quantum particle is in superposition (existing in 
            multiple states simultaneously), the measurement outcome is fundamentally random and 
            cannot be predicted, even with perfect knowledge of the system.
          </div>
        </div>

        {/* The Hadamard Gate */}
        <div className="info-section">
          <div className="section-icon">⚡</div>
          <h3 className="section-heading">The Hadamard Gate</h3>
          <p className="section-text">
            The Hadamard gate (H) is a fundamental quantum gate that creates an equal superposition 
            state. It's the key to generating quantum random numbers.
          </p>
          <div className="equation-box">
            <div className="equation">H|0⟩ = (|0⟩ + |1⟩) / √2</div>
            <div className="equation">H|1⟩ = (|0⟩ - |1⟩) / √2</div>
          </div>
          <p className="section-text">
            When applied to a qubit in state |0⟩, the Hadamard gate creates a superposition where 
            the qubit has a 50% probability of being measured as 0 and 50% as 1. This perfect 
            equiprobability is the foundation of quantum random number generation.
          </p>
        </div>

        {/* Classical vs Quantum */}
        <div className="info-section comparison">
          <div className="section-icon">⚔️</div>
          <h3 className="section-heading">Classical vs Quantum Randomness</h3>
          
          <div className="comparison-grid">
            <div className="comparison-card classical">
              <h4>🖥️ Classical (Pseudo-Random)</h4>
              <ul>
                <li><strong>Algorithm-based:</strong> Uses mathematical formulas</li>
                <li><strong>Deterministic:</strong> Same seed = same sequence</li>
                <li><strong>Predictable:</strong> Can be reproduced if algorithm is known</li>
                <li><strong>Fast:</strong> Very efficient computation</li>
                <li><strong>Examples:</strong> Linear congruential generator, Mersenne Twister</li>
              </ul>
            </div>
            
            <div className="comparison-card quantum">
              <h4>⚛️ Quantum (True Random)</h4>
              <ul>
                <li><strong>Physics-based:</strong> Uses quantum measurement</li>
                <li><strong>Non-deterministic:</strong> Cannot be reproduced</li>
                <li><strong>Unpredictable:</strong> Fundamentally impossible to predict</li>
                <li><strong>Secure:</strong> Based on laws of physics</li>
                <li><strong>Examples:</strong> Photon detection, quantum superposition</li>
              </ul>
            </div>
          </div>
        </div>

        {/* How It Works - Step by Step */}
        <div className="info-section">
          <div className="section-icon">🔄</div>
          <h3 className="section-heading">How This Generator Works</h3>
          
          <div className="steps-container">
            <div className="step-card">
              <div className="step-num">1</div>
              <div className="step-content">
                <h4>Initialization</h4>
                <p>Create a quantum circuit with N qubits, all starting in the |0⟩ state</p>
              </div>
            </div>
            
            <div className="step-card">
              <div className="step-num">2</div>
              <div className="step-content">
                <h4>Superposition</h4>
                <p>Apply Hadamard gates to all qubits, creating equal superposition states</p>
              </div>
            </div>
            
            <div className="step-card">
              <div className="step-num">3</div>
              <div className="step-content">
                <h4>Measurement</h4>
                <p>Measure all qubits, causing quantum state collapse to random 0s and 1s</p>
              </div>
            </div>
            
            <div className="step-card">
              <div className="step-num">4</div>
              <div className="step-content">
                <h4>Collection</h4>
                <p>Repeat measurements (shots) to collect statistical data and generate bits</p>
              </div>
            </div>
            
            <div className="step-card">
              <div className="step-num">5</div>
              <div className="step-content">
                <h4>Key Formation</h4>
                <p>Combine random bits into a cryptographic key in hex or binary format</p>
              </div>
            </div>
          </div>
        </div>

        {/* Security Applications */}
        <div className="info-section">
          <div className="section-icon">🔐</div>
          <h3 className="section-heading">Security Applications</h3>
          
          <div className="applications-grid">
            <div className="app-card">
              <div className="app-icon">🔑</div>
              <h4>Cryptographic Keys</h4>
              <p>Generate keys for AES, RSA, and other encryption algorithms with true randomness</p>
            </div>
            
            <div className="app-card">
              <div className="app-icon">📡</div>
              <h4>Quantum Key Distribution</h4>
              <p>Enable secure communication protocols like BB84 and E91 for unbreakable encryption</p>
            </div>
            
            <div className="app-card">
              <div className="app-icon">🎲</div>
              <div>
                <h4>Random Number Generation</h4>
                <p>Provide true randomness for simulations, gaming, and statistical sampling</p>
              </div>
            </div>
            
            <div className="app-card">
              <div className="app-icon">🛡️</div>
              <h4>One-Time Pads</h4>
              <p>Create perfectly secure one-time pad keys that are information-theoretically secure</p>
            </div>
          </div>
        </div>

        {/* Why It Matters */}
        <div className="info-section importance">
          <div className="section-icon">💡</div>
          <h3 className="section-heading">Why Quantum Randomness Matters</h3>
          
          <div className="importance-content">
            <div className="importance-item">
              <strong>Fundamental Security:</strong> Classical random number generators can 
              theoretically be predicted if the algorithm and seed are known. Quantum randomness 
              is based on the laws of physics and cannot be predicted even with unlimited 
              computational power.
            </div>
            
            <div className="importance-item">
              <strong>Future-Proof:</strong> As quantum computers become more powerful, they may 
              be able to break classical encryption. Quantum random number generators provide 
              security based on quantum mechanics itself, making them resistant to quantum attacks.
            </div>
            
            <div className="importance-item">
              <strong>Verifiable Randomness:</strong> Quantum randomness can be verified using 
              Bell inequality tests, providing mathematical proof that the randomness is genuine 
              and not predetermined.
            </div>
          </div>
        </div>

        {/* Technical Notes */}
        <div className="info-section technical">
          <div className="section-icon">⚙️</div>
          <h3 className="section-heading">Technical Implementation</h3>
          
          <div className="tech-details">
            <div className="tech-item">
              <h4>Simulator Used</h4>
              <p><code>qiskit-aer</code> - AerSimulator for quantum circuit simulation</p>
            </div>
            
            <div className="tech-item">
              <h4>Shot Count</h4>
              <p>Number of times the circuit is executed. Higher shots provide better 
              statistical accuracy but take more time.</p>
            </div>
            
            <div className="tech-item">
              <h4>Qubit Count</h4>
              <p>Each qubit generates one random bit. An 8-qubit circuit generates 8 bits 
              of randomness per execution.</p>
            </div>
            
            <div className="tech-item">
              <h4>Real vs Simulated</h4>
              <p>This demo uses a simulator. Real quantum hardware (like IBM Quantum or 
              IonQ systems) provides genuine quantum randomness from physical qubits.</p>
            </div>
          </div>
        </div>

        {/* Further Learning */}
        <div className="info-section resources">
          <div className="section-icon">📚</div>
          <h3 className="section-heading">Further Learning</h3>
          
          <div className="resources-list">
            <a href="https://qiskit.org/" target="_blank" rel="noopener noreferrer" className="resource-link">
              <span className="link-icon">🔗</span>
              <div>
                <strong>Qiskit Documentation</strong>
                <p>Learn quantum computing with IBM's open-source framework</p>
              </div>
            </a>
            
            <a href="https://quantum-computing.ibm.com/" target="_blank" rel="noopener noreferrer" className="resource-link">
              <span className="link-icon">🔗</span>
              <div>
                <strong>IBM Quantum Experience</strong>
                <p>Run quantum circuits on real quantum hardware</p>
              </div>
            </a>
            
            <div className="resource-info">
              <strong>Recommended Topics:</strong>
              <ul>
                <li>Quantum superposition and measurement</li>
                <li>Bell's theorem and quantum entanglement</li>
                <li>Quantum cryptography and QKD protocols</li>
                <li>Randomness testing and statistical analysis</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default QuantumInfo;
