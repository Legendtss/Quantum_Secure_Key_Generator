# Technical Documentation

## Quantum Key Generator - Deep Dive

This document provides in-depth technical information about the implementation of the Quantum-Based Secure Random Key Generator.

---

## Table of Contents

1. [Quantum Circuit Design](#quantum-circuit-design)
2. [Backend Implementation](#backend-implementation)
3. [API Architecture](#api-architecture)
4. [Frontend Architecture](#frontend-architecture)
5. [Quantum Algorithms](#quantum-algorithms)
6. [Performance Optimization](#performance-optimization)
7. [Testing & Validation](#testing--validation)

---

## Quantum Circuit Design

### Single-Qubit Circuit

The simplest quantum random number generator uses a single qubit:

```
      ┌───┐┌─┐
q_0: ─┤ H ├┤M├
      └───┘└╥┘
c_0: ══════╩═
```

**Process**:
1. Initialize qubit in |0⟩ state
2. Apply Hadamard gate: H|0⟩ = (|0⟩ + |1⟩)/√2
3. Measure qubit → collapses to |0⟩ or |1⟩ with equal probability

### Multi-Qubit Circuit (8-bit example)

For generating multiple random bits efficiently:

```
      ┌───┐┌─┐
q_0: ─┤ H ├┤M├─
      ├───┤└╥┘
q_1: ─┤ H ├─╫──
      ├───┤ ║
q_2: ─┤ H ├─╫──
      ├───┤ ║
q_3: ─┤ H ├─╫──
      ├───┤ ║
q_4: ─┤ H ├─╫──
      ├───┤ ║
q_5: ─┤ H ├─╫──
      ├───┤ ║
q_6: ─┤ H ├─╫──
      ├───┤ ║
q_7: ─┤ H ├─╫──
      └───┘ ║
c_0: ═══════╩═════
c_1: ═════════════
...
```

**Advantages**:
- Parallel generation of multiple random bits
- Efficient use of quantum resources
- Better statistical properties with multiple shots

---

## Backend Implementation

### Core Class: `QuantumRandomGenerator`

```python
class QuantumRandomGenerator:
    def __init__(self):
        self.simulator = AerSimulator()
```

**Key Methods**:

#### 1. `generate_single_bit(shots=1000)`

Generates a single quantum random bit with statistical verification.

**Parameters**:
- `shots`: Number of circuit executions (default: 1000)

**Returns**:
- `bit`: Most common outcome ('0' or '1')
- `counts`: Dictionary of measurement results
- `circuit`: Text representation of quantum circuit
- `histogram`: Base64-encoded PNG of results distribution
- `shots`: Number of measurements performed

**Implementation Details**:
```python
# Create 1-qubit circuit
qc = QuantumCircuit(1, 1)

# Apply Hadamard gate
qc.h(0)

# Measure
qc.measure(0, 0)

# Execute
result = self.simulator.run(transpile(qc, self.simulator), shots=shots).result()
counts = result.get_counts()

# Determine outcome
bit_value = max(counts, key=counts.get)
```

#### 2. `generate_random_bits(num_qubits=8, shots=1000)`

Generates multiple random bits using a multi-qubit circuit.

**Parameters**:
- `num_qubits`: Number of bits to generate (1-16)
- `shots`: Measurements per circuit

**Returns**:
- `binary`: Binary string of random bits
- `hex`: Hexadecimal representation
- `length`: Number of qubits used
- `counts`: Measurement distribution
- `circuit`: Circuit diagram
- `histogram`: Visualization
- `shots`: Measurements performed

**Implementation Details**:
```python
# Create multi-qubit circuit
qc = QuantumCircuit(num_qubits, num_qubits)

# Apply Hadamard to all qubits
for i in range(num_qubits):
    qc.h(i)

# Measure all qubits
qc.measure(range(num_qubits), range(num_qubits))

# Execute and get most common result
result = self.simulator.run(transpile(qc, self.simulator), shots=shots).result()
counts = result.get_counts()
binary_string = max(counts, key=counts.get)

# Convert to hex
hex_key = hex(int(binary_string, 2))[2:].upper()
```

#### 3. `generate_secure_key(key_length=256, shots=1024)`

Generates cryptographically-sized keys by combining multiple quantum circuits.

**Parameters**:
- `key_length`: Desired key size in bits (128, 256, 512)
- `shots`: Measurements per 8-qubit chunk

**Returns**:
- `binary`: Full binary key
- `hex`: Hexadecimal key
- `length`: Key length in bits
- `hash`: SHA-256 hash for verification
- `circuit`: Sample circuit diagram
- `chunks_generated`: Number of 8-bit chunks
- `shots_per_chunk`: Measurements per chunk

**Implementation Strategy**:
```python
# Calculate number of 8-bit chunks needed
chunks = (key_length + 7) // 8

# Generate each chunk
all_bits = []
for _ in range(chunks):
    result = self.generate_random_bits(num_qubits=8, shots=shots)
    all_bits.append(result['binary'])

# Combine and truncate to exact length
full_binary = ''.join(all_bits)[:key_length]

# Generate SHA-256 hash
key_hash = hashlib.sha256(full_binary.encode()).hexdigest()
```

---

## API Architecture

### Flask REST API Design

**Base URL**: `http://localhost:5000/api`

**CORS**: Enabled for frontend communication

### Endpoints

#### 1. `GET /api/health`

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "service": "Quantum Random Key Generator API",
  "version": "1.0.0"
}
```

#### 2. `POST /api/generate-bit`

Generate single quantum random bit.

**Request**:
```json
{
  "shots": 1000  // Optional, default: 1000
}
```

**Validation**:
- `shots`: Integer between 1 and 10,000

**Response**:
```json
{
  "success": true,
  "data": {
    "bit": "0",
    "counts": {"0": 502, "1": 498},
    "circuit": "quantum circuit text...",
    "histogram": "data:image/png;base64,...",
    "shots": 1000
  }
}
```

#### 3. `POST /api/generate-random`

Generate multiple quantum random bits.

**Request**:
```json
{
  "num_qubits": 8,  // Optional, default: 8
  "shots": 1000      // Optional, default: 1000
}
```

**Validation**:
- `num_qubits`: Integer between 1 and 16
- `shots`: Integer between 1 and 10,000

**Response**:
```json
{
  "success": true,
  "data": {
    "binary": "10110010",
    "hex": "B2",
    "length": 8,
    "counts": {"10110010": 523, ...},
    "circuit": "quantum circuit text...",
    "histogram": "data:image/png;base64,...",
    "shots": 1000
  }
}
```

#### 4. `POST /api/generate-key`

Generate secure cryptographic key.

**Request**:
```json
{
  "key_length": 256,  // 128, 256, or 512
  "shots": 1024       // Optional, default: 1024
}
```

**Validation**:
- `key_length`: Must be 128, 256, or 512
- `shots`: Integer between 1 and 10,000

**Response**:
```json
{
  "success": true,
  "data": {
    "binary": "1010101010...",
    "hex": "AAF3C9D2...",
    "length": 256,
    "hash": "sha256_hash_of_key...",
    "circuit": "sample circuit...",
    "chunks_generated": 32,
    "shots_per_chunk": 1024
  }
}
```

#### 5. `GET /api/info`

Get educational information.

**Response**: JSON object with quantum computing education content

### Error Handling

All endpoints return consistent error format:

```json
{
  "success": false,
  "error": "Error message description"
}
```

**HTTP Status Codes**:
- `200`: Success
- `400`: Bad Request (validation errors)
- `500`: Internal Server Error

---

## Frontend Architecture

### Component Structure

```
App (Main Container)
├── QuantumBitGenerator (Single Bit Tab)
│   ├── Input Controls
│   ├── Results Display
│   ├── Circuit Visualization
│   ├── Histogram
│   └── Info Panel
├── QuantumKeyGenerator (Secure Key Tab)
│   ├── Configuration Controls
│   ├── Key Display
│   ├── Metadata
│   ├── Security Info
│   └── Use Cases Panel
└── QuantumInfo (Educational Tab)
    ├── Concept Explanations
    ├── Comparisons
    ├── Step-by-Step Process
    └── Resources
```

### State Management

**Local Component State** (React Hooks):

```javascript
// QuantumBitGenerator
const [loading, setLoading] = useState(false);
const [result, setResult] = useState(null);
const [shots, setShots] = useState(1000);
const [error, setError] = useState(null);

// QuantumKeyGenerator
const [keyLength, setKeyLength] = useState(256);
const [copied, setCopied] = useState(false);
```

### API Communication

**Fetch Pattern**:
```javascript
const generateKey = async () => {
  setLoading(true);
  setError(null);
  
  try {
    const response = await fetch(`${API_URL}/generate-key`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key_length: keyLength, shots })
    });
    
    const data = await response.json();
    
    if (data.success) {
      setResult(data.data);
    } else {
      setError(data.error);
    }
  } catch (err) {
    setError('Failed to connect to backend');
  } finally {
    setLoading(false);
  }
};
```

### Design System

**Color Palette**:
```css
--quantum-primary: #00d4ff;    /* Cyan */
--quantum-secondary: #ff00ff;   /* Magenta */
--quantum-accent: #7c3aed;      /* Purple */
--quantum-dark: #0a0e27;        /* Deep blue-black */
--success-green: #00ff88;       /* Neon green */
```

**Typography**:
- Display: Orbitron (sci-fi, quantum-inspired)
- Body: IBM Plex Mono (technical, readable)

**Animations**:
- Floating particles (infinite loop)
- Fade-in on mount
- Slide-up on results
- Hover transitions (transform, box-shadow)

---

## Quantum Algorithms

### Hadamard Transform Mathematics

**Single Qubit**:

```
H|0⟩ = 1/√2 (|0⟩ + |1⟩)
H|1⟩ = 1/√2 (|0⟩ - |1⟩)
```

**Matrix Representation**:
```
H = 1/√2 [ 1   1 ]
          [ 1  -1 ]
```

**Multiple Qubits**:

For n qubits, the Hadamard transform creates 2^n equally probable states:

```
H⊗n|00...0⟩ = 1/√(2^n) ∑(x∈{0,1}^n) |x⟩
```

Example with 3 qubits:
```
H⊗3|000⟩ = 1/√8 (|000⟩ + |001⟩ + |010⟩ + |011⟩ + 
                 |100⟩ + |101⟩ + |110⟩ + |111⟩)
```

### Measurement Collapse

Upon measurement, the superposition state collapses to a single eigenstate with probability determined by the Born rule:

```
P(|x⟩) = |⟨x|ψ⟩|²
```

For equal superposition:
```
P(|x⟩) = 1/2^n  (for all x)
```

---

## Performance Optimization

### Backend Optimizations

1. **Circuit Reuse**:
   - Circuits are transpiled once
   - Reused across multiple shots

2. **Parallel Execution**:
   - Simulator can run shots in parallel
   - Utilizes multiple CPU cores

3. **Histogram Caching**:
   - Generate once per request
   - Return as base64 PNG

### Frontend Optimizations

1. **Lazy Loading**:
   - Components load on-demand
   - Reduces initial bundle size

2. **Debouncing**:
   - Input changes debounced
   - Prevents excessive re-renders

3. **Memoization**:
   - Results cached in state
   - Avoid redundant API calls

### Scalability Considerations

**Current Limits**:
- Max qubits: 16 (to keep simulation fast)
- Max shots: 10,000 (balance accuracy vs speed)
- Max key length: 512 bits

**Potential Improvements**:
- Add caching layer (Redis)
- Implement request queuing
- Use quantum cloud providers (IBM Quantum, AWS Braket)
- Pre-generate random number pools

---

## Testing & Validation

### Statistical Tests

**Chi-Square Test** for uniformity:
```python
def chi_square_test(counts, shots):
    expected = shots / len(counts)
    chi_square = sum((observed - expected)**2 / expected 
                    for observed in counts.values())
    return chi_square
```

**Entropy Calculation**:
```python
def calculate_entropy(binary_string):
    counts = Counter(binary_string)
    total = len(binary_string)
    entropy = -sum((count/total) * math.log2(count/total) 
                   for count in counts.values())
    return entropy
```

### Unit Tests (Recommended)

```python
# Test single bit generation
def test_single_bit():
    qrng = QuantumRandomGenerator()
    result = qrng.generate_single_bit(shots=1000)
    assert result['bit'] in ['0', '1']
    assert sum(result['counts'].values()) == 1000

# Test distribution
def test_bit_distribution():
    qrng = QuantumRandomGenerator()
    results = [qrng.generate_single_bit(shots=100)['bit'] 
               for _ in range(1000)]
    zeros = results.count('0')
    ones = results.count('1')
    # Should be roughly 50/50 (±10%)
    assert 400 < zeros < 600
    assert 400 < ones < 600
```

### Integration Tests

```python
# Test API endpoints
def test_generate_bit_endpoint():
    response = requests.post('http://localhost:5000/api/generate-bit',
                            json={'shots': 1000})
    assert response.status_code == 200
    assert response.json()['success'] == True
```

### Randomness Validation

**NIST Test Suite** (optional advanced validation):
- Frequency test
- Block frequency test
- Runs test
- Longest run test
- Binary matrix rank test

---

## Future Enhancements

1. **Real Quantum Hardware Integration**
   - IBM Quantum
   - AWS Braket
   - Google Cirq

2. **Advanced Algorithms**
   - Quantum entropy sources
   - Post-processing for bias correction
   - Multi-gate random circuits

3. **Performance**
   - Background key generation
   - Key pool management
   - Distributed quantum circuits

4. **Security**
   - Randomness certification
   - Bell test verification
   - Quantum random number pools

---

## References

1. Qiskit Documentation: https://qiskit.org/documentation/
2. Quantum Random Number Generation: https://arxiv.org/abs/1908.08171
3. NIST Randomness Tests: https://csrc.nist.gov/projects/random-bit-generation
4. Quantum Computing Stack Exchange: https://quantumcomputing.stackexchange.com/

---

**Last Updated**: 2024
**Version**: 1.0.0
