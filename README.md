# Quantum-Based Secure Random Key Generator

An educational full-stack web application demonstrating how quantum gates (specifically the Hadamard gate) can be used to generate true random numbers for secure cryptographic keys.

![Quantum Key Generator](https://img.shields.io/badge/Quantum-Computing-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-green?style=for-the-badge)
![React](https://img.shields.io/badge/React-18.2-blue?style=for-the-badge)
![Qiskit](https://img.shields.io/badge/Qiskit-1.0-purple?style=for-the-badge)

## 🎯 Project Overview

This project demonstrates the fundamental difference between classical pseudo-random number generation and quantum true randomness. It provides:

- **Single Quantum Bit Generator**: Visualize how a single qubit in superposition collapses to a random state
- **Secure Key Generator**: Create 128-bit, 256-bit, or 512-bit cryptographic keys using quantum randomness
- **Educational Interface**: Learn about quantum superposition, Hadamard gates, and quantum measurements
- **Visual Demonstrations**: See quantum circuits, measurement histograms, and statistical distributions

## 🧠 What is Quantum Randomness?

### Classical vs Quantum Randomness

**Classical (Pseudo-Random)**:
- Uses deterministic algorithms (e.g., Mersenne Twister, Linear Congruential Generator)
- Same seed → same sequence
- Predictable with knowledge of algorithm and state
- Fast and efficient, but theoretically breakable

**Quantum (True Random)**:
- Based on quantum mechanical uncertainty principle
- Fundamentally unpredictable
- Cannot be reproduced or predicted
- Physically secure - based on laws of nature

### The Hadamard Gate

The Hadamard gate (H) is the key to quantum random number generation:

```
H|0⟩ = (|0⟩ + |1⟩) / √2
```

When applied to a qubit in state |0⟩, it creates an **equal superposition** where:
- 50% probability of measuring |0⟩
- 50% probability of measuring |1⟩

Upon measurement, the quantum state **collapses** randomly to either 0 or 1. This collapse is the source of true quantum randomness.

## 🏗️ Architecture

### Tech Stack

**Backend**:
- Python 3.9+
- Qiskit 1.0 (Quantum computing framework)
- Flask (REST API)
- Matplotlib (Visualization)

**Frontend**:
- React 18.2
- Custom CSS with quantum-inspired design
- Responsive UI with modern aesthetics

### Project Structure

```
quantum-key-generator/
├── backend/
│   ├── quantum_generator.py    # Core quantum logic
│   ├── app.py                  # Flask REST API
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── QuantumBitGenerator.js     # Single bit UI
│   │   │   ├── QuantumKeyGenerator.js     # Key generation UI
│   │   │   └── QuantumInfo.js             # Educational content
│   │   ├── App.js
│   │   ├── App.css
│   │   └── index.js
│   └── package.json
└── README.md
```

## 🚀 Installation & Setup

### Prerequisites

- Python 3.9 or higher
- Node.js 14 or higher
- npm or yarn

### Backend Setup

1. **Navigate to backend directory**:
```bash
cd quantum-key-generator/backend
```

2. **Create virtual environment** (recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Run the Flask server**:
```bash
python app.py
```

The backend API will start on `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory**:
```bash
cd quantum-key-generator/frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Start the React development server**:
```bash
npm start
```

The frontend will open at `http://localhost:3000`

## 🎮 Usage

### Single Quantum Bit Generation

1. Navigate to the "Single Bit" tab
2. Adjust the number of measurements (shots) - higher values give better statistics
3. Click "Generate Quantum Bit"
4. View the result, circuit diagram, and measurement distribution

### Secure Key Generation

1. Navigate to the "Secure Key" tab
2. Select key length (128, 256, or 512 bits)
3. Adjust shots per chunk (affects accuracy)
4. Click "Generate Secure Key"
5. Copy the generated key in hex or binary format
6. View the SHA-256 hash for verification

### Learning Mode

1. Navigate to the "Learn More" tab
2. Explore explanations of:
   - Quantum randomness fundamentals
   - Hadamard gate operation
   - Classical vs quantum comparison
   - Security applications
   - Technical implementation details

## 🔌 API Endpoints

### `POST /api/generate-bit`

Generate a single quantum random bit.

**Request Body**:
```json
{
  "shots": 1000
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "bit": "0",
    "counts": {"0": 502, "1": 498},
    "circuit": "...",
    "histogram": "data:image/png;base64,...",
    "shots": 1000
  }
}
```

### `POST /api/generate-random`

Generate multiple quantum random bits.

**Request Body**:
```json
{
  "num_qubits": 8,
  "shots": 1000
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "binary": "10110010",
    "hex": "B2",
    "length": 8,
    "counts": {...},
    "circuit": "...",
    "histogram": "data:image/png;base64,...",
    "shots": 1000
  }
}
```

### `POST /api/generate-key`

Generate a secure cryptographic key.

**Request Body**:
```json
{
  "key_length": 256,
  "shots": 1024
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "binary": "1010101...",
    "hex": "A5C3F9...",
    "length": 256,
    "hash": "sha256_hash...",
    "circuit": "...",
    "chunks_generated": 32,
    "shots_per_chunk": 1024
  }
}
```

### `GET /api/info`

Get educational information about quantum randomness.

## 🧪 How It Works

### Step-by-Step Process

1. **Initialize Quantum Circuit**
   - Create a quantum circuit with N qubits
   - All qubits start in the |0⟩ state

2. **Apply Hadamard Gates**
   - Apply H gate to each qubit
   - Creates equal superposition: (|0⟩ + |1⟩) / √2

3. **Measurement**
   - Measure all qubits
   - Quantum state collapses to random 0s and 1s

4. **Statistical Collection**
   - Repeat measurement many times (shots)
   - Collect distribution data

5. **Key Formation**
   - Combine random bits into binary string
   - Convert to hexadecimal for cryptographic key format
   - Generate SHA-256 hash for verification

### Why Hadamard Gates?

The Hadamard gate is perfect for random number generation because:

- **Perfect Equiprobability**: Creates exactly 50/50 probability
- **Single-Qubit Operation**: Simple and efficient
- **Universal Gate**: Part of universal quantum gate set
- **Fast Implementation**: Quick on quantum hardware

## 🔐 Security Applications

### Cryptographic Use Cases

1. **Encryption Keys**: Generate keys for AES, RSA, ChaCha20
2. **One-Time Pads**: Create information-theoretically secure keys
3. **Session Tokens**: Generate unique authentication tokens
4. **Nonces & IVs**: Create initialization vectors for encryption
5. **Quantum Key Distribution**: Enable QKD protocols (BB84, E91)

### Why It's Secure

- **Unpredictable**: Based on quantum uncertainty principle
- **Irreproducible**: Cannot recreate the same sequence
- **Verifiable**: Can prove randomness using Bell tests
- **Future-Proof**: Resistant to quantum computer attacks

## ⚠️ Important Notes

### Educational Demo

This is a **simulated** quantum system for educational purposes. For production cryptography:

- Use certified hardware quantum random number generators
- Use vetted cryptographic libraries (OpenSSL, libsodium)
- Follow industry standards (NIST, FIPS)

### Real vs Simulated

- **This Project**: Uses Qiskit's AerSimulator (software simulation)
- **Real Quantum**: Would use actual quantum hardware (IBM Quantum, IonQ, Rigetti)
- **Difference**: Real hardware provides genuine quantum randomness from physical qubits

## 📊 Performance

- **Single Bit**: ~0.1-0.5 seconds
- **8-Bit Random**: ~0.2-0.8 seconds
- **256-Bit Key**: ~2-5 seconds (32 chunks × 8 qubits)
- **512-Bit Key**: ~4-10 seconds (64 chunks × 8 qubits)

Times vary based on:
- Number of shots (measurements)
- System performance
- Simulation overhead

## 🎨 UI Design Philosophy

The interface uses a **quantum-inspired aesthetic**:

- **Color Palette**: Cyan (#00d4ff) and purple (#7c3aed) gradients
- **Typography**: Orbitron (display) + IBM Plex Mono (body)
- **Animations**: Floating particles, smooth transitions
- **Dark Theme**: Matches quantum computing aesthetic
- **Visual Clarity**: Clear information hierarchy

## 📚 Further Learning

### Recommended Resources

- [Qiskit Textbook](https://qiskit.org/textbook/) - Learn quantum computing
- [IBM Quantum Experience](https://quantum-computing.ibm.com/) - Run on real hardware
- [Quantum Randomness Paper](https://arxiv.org/abs/1908.08171) - Academic research
- [NIST Randomness Testing](https://csrc.nist.gov/projects/random-bit-generation) - Standards

### Topics to Explore

- Quantum superposition and entanglement
- Bell's theorem and Bell inequalities
- Quantum cryptography protocols
- Randomness extraction and testing
- Quantum advantage demonstrations

## 🤝 Contributing

This is an educational project. Suggestions for improvements:

- Add more quantum gates (X, Z, CNOT)
- Implement Bell test verification
- Add real quantum hardware integration
- Create additional visualizations
- Improve performance with caching

## 📜 License

This project is for educational purposes. Feel free to use and modify.

## 🙏 Acknowledgments

- **Qiskit Team**: For the amazing quantum computing framework
- **IBM Quantum**: For accessible quantum computing resources
- **Anthropic**: For Claude's assistance in development

## 📧 Contact

For questions or feedback about this educational project, please open an issue.

---

**Built with ⚛️ Quantum Computing • 🔐 Cryptography • 💻 Modern Web Tech**
