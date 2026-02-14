# Quick Start Guide

Get the Quantum Key Generator up and running in 5 minutes!

## Prerequisites

- Python 3.9+
- Node.js 14+
- npm or yarn

## Installation

### Option 1: Automated Setup (Recommended)

```bash
# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

### Option 2: Manual Setup

**Backend**:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend**:
```bash
cd frontend
npm install
```

## Running the Application

### Start Backend (Terminal 1)

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```

You should see:
```
🔬 Quantum Random Key Generator API
==================================================
Starting Flask server on http://localhost:5000
...
```

### Start Frontend (Terminal 2)

```bash
cd frontend
npm start
```

The browser will automatically open to `http://localhost:3000`

## First Steps

### 1. Generate Your First Quantum Bit

1. The app opens on the "Single Bit" tab
2. Keep default settings (1000 shots)
3. Click **"Generate Quantum Bit"**
4. Watch as the quantum circuit executes
5. See the result: 0 or 1
6. View the histogram showing measurement distribution

### 2. Create a Secure Key

1. Click the **"Secure Key"** tab
2. Select key length: 128, 256, or 512 bits
3. Adjust shots if desired (higher = more accurate)
4. Click **"Generate Secure Key"**
5. Copy the hex or binary key
6. Note the SHA-256 hash for verification

### 3. Learn the Science

1. Click the **"Learn More"** tab
2. Read about quantum randomness
3. Understand the Hadamard gate
4. Compare classical vs quantum randomness
5. Explore security applications

## Understanding the Output

### Single Bit Generation

**What you'll see**:
- **Measured Bit**: The result (0 or 1)
- **Counts**: Distribution of measurements
  - Example: `{'0': 502, '1': 498}` means nearly 50/50
- **Circuit Diagram**: Text visualization of the quantum circuit
- **Histogram**: Visual bar chart of results

**What it means**:
- The closer to 50/50, the better the randomness
- With 1000 shots, expect ±2-3% variation
- Perfect 500/500 is unlikely due to quantum randomness

### Key Generation

**What you'll see**:
- **Hex Key**: E.g., `A5C3F9D2E1B4...` (cryptographic format)
- **Binary Key**: E.g., `10100101110000111...` (raw bits)
- **SHA-256 Hash**: Verification hash of the key
- **Chunks Generated**: How many 8-qubit circuits were used

**What it means**:
- 256-bit key = 32 chunks of 8 bits
- Each chunk is independently random
- Hash proves key uniqueness

## Common Questions

### Q: The histogram isn't exactly 50/50. Is it working?

**A**: Yes! Perfect 50/50 is statistically unlikely. Quantum randomness produces natural variation. With 1000 shots, expect results like 48/52 or 51/49. This is normal and correct.

### Q: Can I use these keys for real encryption?

**A**: This is a **simulated** system for education. For production:
- Use certified hardware quantum RNGs
- Use vetted libraries (OpenSSL, libsodium)
- Follow security standards (NIST, FIPS)

### Q: Why does key generation take a few seconds?

**A**: The simulator runs multiple quantum circuits:
- 256-bit key = 32 circuits × 8 qubits × 1024 shots
- That's 32,768 quantum measurements!
- Real quantum hardware is faster

### Q: What's the difference between this and random.org?

**A**:
- **This**: Quantum superposition → true randomness
- **random.org**: Atmospheric noise → true randomness
- **Random library**: Algorithm → pseudo-randomness

All three serve different purposes. This demonstrates quantum computing concepts.

## Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'qiskit'`

**Solution**:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend shows "Failed to connect to backend"

**Check**:
1. Is backend running? (Should see Flask messages)
2. Check backend URL in frontend code (default: `http://localhost:5000`)
3. Check CORS settings in backend

**Solution**:
```bash
# Make sure backend is running in separate terminal
cd backend
source venv/bin/activate
python app.py
```

### Histogram not showing

**Cause**: Matplotlib backend issue

**Solution**: Already configured in code with `matplotlib.use('Agg')`

### Slow performance

**Causes**:
- High shot count
- Many qubits
- System resources

**Solutions**:
- Reduce shots (500-1000 is usually sufficient)
- Keep qubits ≤ 12 for faster simulation
- Close other applications

## Next Steps

### Experiment

1. **Try different shot counts**: Compare 100 vs 10,000 shots
2. **Test randomness**: Generate 100 bits, count 0s and 1s
3. **Compare key lengths**: See performance difference

### Learn More

1. Read `TECHNICAL_DOCUMENTATION.md` for deep dive
2. Explore Qiskit tutorials: https://qiskit.org/textbook/
3. Try IBM Quantum Experience: https://quantum-computing.ibm.com/

### Modify & Extend

Ideas for enhancement:
- Add different quantum gates (X, Y, Z)
- Implement Bell state measurements
- Create custom circuit visualizations
- Add key export formats (PEM, JWK)

## API Usage Example

You can also use the API directly:

```bash
# Generate a single bit
curl -X POST http://localhost:5000/api/generate-bit \
  -H "Content-Type: application/json" \
  -d '{"shots": 1000}'

# Generate a 256-bit key
curl -X POST http://localhost:5000/api/generate-key \
  -H "Content-Type: application/json" \
  -d '{"key_length": 256, "shots": 1024}'
```

## System Requirements

**Minimum**:
- 4GB RAM
- 2 CPU cores
- 500MB disk space

**Recommended**:
- 8GB RAM
- 4 CPU cores
- 1GB disk space

## Performance Expectations

| Operation | Time | Notes |
|-----------|------|-------|
| Single Bit (1000 shots) | 0.1-0.5s | Very fast |
| 8-bit Random (1000 shots) | 0.2-0.8s | Quick |
| 256-bit Key (1024 shots) | 2-5s | 32 circuits |
| 512-bit Key (1024 shots) | 4-10s | 64 circuits |

*Times on MacBook Pro M1. May vary.*

## Support

For issues, questions, or suggestions:
1. Check `README.md` for detailed documentation
2. Review `TECHNICAL_DOCUMENTATION.md` for implementation details
3. Open an issue on the project repository

---

**Ready to explore quantum randomness? Let's go!** 🚀⚛️🔐
