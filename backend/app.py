"""
Flask REST API for Quantum Random Key Generator
Provides endpoints for quantum random number generation
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from quantum_generator import QuantumRandomGenerator
import traceback
import os

# Get the directory path for frontend build files
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build')

app = Flask(__name__, static_folder=FRONTEND_BUILD_DIR, static_url_path='')
CORS(app)  # Enable CORS for frontend communication

# Initialize quantum generator
qrng = QuantumRandomGenerator()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Quantum Random Key Generator API',
        'version': '1.0.0'
    })


@app.route('/api/generate-bit', methods=['POST'])
def generate_bit():
    """
    Generate a single quantum random bit

    Request body:
        shots (optional): Number of measurements (default: 1000)

    Returns:
        JSON with bit value, counts, circuit diagram, and histogram
    """
    try:
        data = request.get_json() or {}
        shots = data.get('shots', 1000)

        # Validate shots parameter
        if not isinstance(shots, int) or shots < 1 or shots > 10000:
            return jsonify({
                'error': 'Shots must be an integer between 1 and 10000'
            }), 400

        # Generate quantum random bit
        result = qrng.generate_single_bit(shots=shots)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        print(f"Error in generate_bit: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/generate-random', methods=['POST'])
def generate_random():
    """
    Generate multiple quantum random bits

    Request body:
        num_qubits (optional): Number of qubits/bits (default: 8, max: 16)
        shots (optional): Number of measurements (default: 1000)

    Returns:
        JSON with binary string, hex value, circuit, and histogram
    """
    try:
        data = request.get_json() or {}
        num_qubits = data.get('num_qubits', 8)
        shots = data.get('shots', 1000)

        # Validate parameters
        if not isinstance(num_qubits, int) or num_qubits < 1 or num_qubits > 16:
            return jsonify({
                'error': 'num_qubits must be an integer between 1 and 16'
            }), 400

        if not isinstance(shots, int) or shots < 1 or shots > 10000:
            return jsonify({
                'error': 'shots must be an integer between 1 and 10000'
            }), 400

        # Generate quantum random bits
        result = qrng.generate_random_bits(num_qubits=num_qubits, shots=shots)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        print(f"Error in generate_random: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/generate-key', methods=['POST'])
def generate_key():
    """
    Generate a secure cryptographic key using quantum randomness

    Request body:
        key_length (optional): Length in bits - 128, 256, or 512 (default: 256)
        shots (optional): Number of measurements (default: 1024)

    Returns:
        JSON with secure key in binary and hex formats, plus quantum metadata
    """
    try:
        data = request.get_json() or {}
        key_length = data.get('key_length', 256)
        shots = data.get('shots', 1024)

        # Validate parameters
        valid_lengths = [128, 256, 512]
        if key_length not in valid_lengths:
            return jsonify({
                'error': f'key_length must be one of {valid_lengths}'
            }), 400

        if not isinstance(shots, int) or shots < 1 or shots > 10000:
            return jsonify({
                'error': 'shots must be an integer between 1 and 10000'
            }), 400

        # Generate secure quantum key
        result = qrng.generate_secure_key(key_length=key_length, shots=shots)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        print(f"Error in generate_key: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/info', methods=['GET'])
def get_info():
    """
    Get information about quantum random number generation

    Returns:
        Educational information about quantum randomness
    """
    return jsonify({
        'quantum_randomness': {
            'description': 'Quantum randomness is fundamentally different from classical randomness. '
            'It arises from the inherent unpredictability of quantum measurements.',
            'hadamard_gate': {
                'description': 'The Hadamard gate creates an equal superposition state',
                'operation': 'H|0> = (|0> + |1>)/sqrt(2)',
                'result': 'Upon measurement, the qubit collapses to |0> or |1> with equal probability'
            },
            'classical_vs_quantum': {
                'classical': 'Pseudo-random: deterministic algorithms that appear random',
                'quantum': 'True random: based on quantum mechanical uncertainty principle'
            },
            'security_applications': [
                'Cryptographic key generation',
                'One-time pads',
                'Random number generation for protocols',
                'Quantum key distribution (QKD)'
            ]
        }
    })


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve React frontend - handles SPA routing"""
    # If path starts with 'api/', let Flask handle it as an API route
    if path.startswith('api/'):
        return jsonify({'error': 'API endpoint not found'}), 404

    # Try to serve the file from static folder
    if path and os.path.exists(os.path.join(FRONTEND_BUILD_DIR, path)):
        return send_from_directory(FRONTEND_BUILD_DIR, path)

    # Return index.html for SPA routing (enables React Router)
    if os.path.exists(os.path.join(FRONTEND_BUILD_DIR, 'index.html')):
        return send_from_directory(FRONTEND_BUILD_DIR, 'index.html')

    return jsonify({'error': 'Frontend not built. Run: cd frontend && npm run build'}), 404


if __name__ == '__main__':
    print('Quantum Random Key Generator API')
    print('=' * 50)
    print('Starting Flask server on http://localhost:5000')
    print('Available endpoints:')
    print('  POST /api/generate-bit    - Generate single quantum bit')
    print('  POST /api/generate-random - Generate multi-bit random number')
    print('  POST /api/generate-key    - Generate secure cryptographic key')
    print('  GET  /api/info            - Get quantum randomness information')
    print('=' * 50)

    app.run(debug=True, host='0.0.0.0', port=5000)
