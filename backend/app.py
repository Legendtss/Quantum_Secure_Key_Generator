"""
Flask REST API for Quantum Random Key Generator
Provides endpoints for quantum random number generation
Enhanced with cryptography, entropy analysis, classical comparison, and IBM Quantum hardware
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from quantum_generator import QuantumRandomGenerator
from crypto_engine import CryptoEngine
from entropy_analyzer import EntropyAnalyzer
from comparator import RandomnessComparator
from ibm_quantum import ibm_manager, IBM_AVAILABLE
import traceback
import os
import base64

# Get the directory path for frontend build files
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build')

app = Flask(__name__, static_folder=FRONTEND_BUILD_DIR, static_url_path='')
CORS(app)  # Enable CORS for frontend communication

# Initialize quantum generator
qrng = QuantumRandomGenerator()

# Initialize new modules
crypto_engine = CryptoEngine()
entropy_analyzer = EntropyAnalyzer()
comparator = RandomnessComparator(quantum_generator=qrng, ibm_manager=ibm_manager)


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

        # If user is connected to IBM and has selected a backend, default to
        # real hardware generation without requiring frontend changes.
        use_ibm = data.get('use_ibm')
        if use_ibm is None:
            use_ibm = bool(ibm_manager.connected and ibm_manager.current_backend)

        if use_ibm:
            result = ibm_manager.generate_secure_key(key_length=key_length, shots=shots)
            if not result.get('success', False):
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'IBM hardware key generation failed'),
                    'hint': result.get('hint', 'Try a different backend or reduce shots'),
                    'detail': result.get('detail'),
                    'chunk_failed': result.get('chunk_failed'),
                    'chunks_total': result.get('chunks_total')
                }), 400
        else:
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


# ============================================================================
# NEW FEATURE 1: AES ENCRYPTION ENDPOINTS
# ============================================================================

@app.route('/api/encrypt', methods=['POST'])
def encrypt_text():
    """
    Encrypt text using AES with a quantum-generated key.
    
    Request body:
        text: Plaintext to encrypt
        key: Hex string key (from quantum generator)
        key_size (optional): 128 or 256 (default: 256)
    
    Returns:
        JSON with ciphertext, IV, and encryption metadata
    """
    try:
        data = request.get_json() or {}
        
        text = data.get('text')
        key = data.get('key')
        key_size = data.get('key_size', 256)
        
        if not text:
            return jsonify({'success': False, 'error': 'Text is required'}), 400
        if not key:
            return jsonify({'success': False, 'error': 'Key is required'}), 400
        if key_size not in [128, 256]:
            return jsonify({'success': False, 'error': 'key_size must be 128 or 256'}), 400
        
        result = crypto_engine.encrypt_text(text, key, key_size)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        print(f"Error in encrypt_text: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/decrypt', methods=['POST'])
def decrypt_text():
    """
    Decrypt text using AES with a quantum-generated key.
    
    Request body:
        ciphertext: Base64 encoded ciphertext
        key: Hex string key (same as used for encryption)
        iv: Base64 encoded IV (from encryption)
        key_size (optional): 128 or 256 (default: 256)
    
    Returns:
        JSON with decrypted plaintext
    """
    try:
        data = request.get_json() or {}
        
        ciphertext = data.get('ciphertext')
        key = data.get('key')
        iv = data.get('iv')
        key_size = data.get('key_size', 256)
        
        if not ciphertext:
            return jsonify({'success': False, 'error': 'Ciphertext is required'}), 400
        if not key:
            return jsonify({'success': False, 'error': 'Key is required'}), 400
        if not iv:
            return jsonify({'success': False, 'error': 'IV is required'}), 400
        
        result = crypto_engine.decrypt_text(ciphertext, key, iv, key_size)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Decryption failed')
            }), 400
        
    except Exception as e:
        print(f"Error in decrypt_text: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/encrypt-file', methods=['POST'])
def encrypt_file():
    """
    Encrypt file data using AES with a quantum-generated key.
    
    Request body:
        file_data: Base64 encoded file content
        key: Hex string key (from quantum generator)
        key_size (optional): 128 or 256 (default: 256)
    
    Returns:
        JSON with encrypted file data and metadata
    """
    try:
        data = request.get_json() or {}
        
        file_data_b64 = data.get('file_data')
        key = data.get('key')
        key_size = data.get('key_size', 256)
        
        if not file_data_b64:
            return jsonify({'success': False, 'error': 'file_data is required'}), 400
        if not key:
            return jsonify({'success': False, 'error': 'Key is required'}), 400
        
        # Decode file data
        file_bytes = base64.b64decode(file_data_b64)
        
        result = crypto_engine.encrypt_file(file_bytes, key, key_size)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        print(f"Error in encrypt_file: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# NEW FEATURE 2: ENTROPY ANALYSIS ENDPOINT
# ============================================================================

@app.route('/api/analyze-entropy', methods=['POST'])
def analyze_entropy():
    """
    Analyze the randomness quality of a bit string.
    
    Request body:
        bit_string: String of 0s and 1s to analyze
    
    Returns:
        JSON with comprehensive randomness test results
    """
    try:
        data = request.get_json() or {}
        
        bit_string = data.get('bit_string')
        
        if not bit_string:
            return jsonify({'success': False, 'error': 'bit_string is required'}), 400
        
        # Validate bit string
        if not all(c in '01' for c in bit_string):
            return jsonify({'success': False, 'error': 'bit_string must contain only 0s and 1s'}), 400
        
        result = entropy_analyzer.analyze_randomness(bit_string)
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        print(f"Error in analyze_entropy: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# NEW FEATURE 3: CLASSICAL VS QUANTUM COMPARISON ENDPOINT
# ============================================================================

@app.route('/api/compare', methods=['GET'])
def compare_random():
    """
    Compare classical PRNG with quantum random number generation.
    
    Query parameters:
        length (optional): Number of bits to generate (default: 256, max: 1024)
    
    Returns:
        JSON with comprehensive comparison data
    """
    try:
        length = request.args.get('length', 256, type=int)
        mode = request.args.get('mode', 'simulator', type=str)
        shots = request.args.get('shots', 1024, type=int)
        
        # Validate length
        if length < 32 or length > 1024:
            return jsonify({
                'success': False,
                'error': 'Length must be between 32 and 1024 bits'
            }), 400

        if mode not in ['simulator', 'ibm_hardware']:
            return jsonify({
                'success': False,
                'error': "mode must be 'simulator' or 'ibm_hardware'"
            }), 400

        if not isinstance(shots, int) or shots < 1 or shots > 4000:
            return jsonify({
                'success': False,
                'error': 'shots must be an integer between 1 and 4000'
            }), 400

        if mode == 'ibm_hardware':
            if not (ibm_manager.connected and ibm_manager.current_backend):
                return jsonify({
                    'success': False,
                    'error': 'IBM hardware mode requires active IBM connection and selected backend',
                    'hint': 'Connect in IBM tab and select a backend first'
                }), 400
            if 'shots' not in request.args:
                shots = 100

        result = comparator.full_comparison(length=length, mode=mode, shots=shots)

        if result.get('quantum_generation', {}).get('error'):
            return jsonify({
                'success': False,
                'error': result['quantum_generation'].get('error'),
                'detail': result['quantum_generation'].get('detail'),
                'hint': result['quantum_generation'].get('hint')
            }), 400
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        print(f"Error in compare_random: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/generate-classical', methods=['POST'])
def generate_classical():
    """
    Generate random bits using classical PRNG (for comparison).
    
    Request body:
        length (optional): Number of bits (default: 256)
        seed (optional): Seed for reproducible results
    
    Returns:
        JSON with generated bits and metadata
    """
    try:
        data = request.get_json() or {}
        
        length = data.get('length', 256)
        seed = data.get('seed')
        
        if length < 1 or length > 1024:
            return jsonify({
                'success': False,
                'error': 'Length must be between 1 and 1024'
            }), 400
        
        result = comparator.generate_classical_random(length, seed)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        print(f"Error in generate_classical: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# NEW FEATURE: IBM QUANTUM HARDWARE INTEGRATION
# ============================================================================

@app.route('/api/ibm/status', methods=['GET'])
def ibm_status():
    """
    Get IBM Quantum connection status.
    
    Returns:
        JSON with IBM availability and connection status
    """
    status = ibm_manager.get_connection_status()
    status['ibm_runtime_installed'] = IBM_AVAILABLE
    return jsonify({
        'success': True,
        'data': status
    })


@app.route('/api/ibm/connect', methods=['POST'])
def ibm_connect():
    """
    Connect to IBM Quantum service.
    
    Request body:
        api_token (optional): IBM Quantum API token
        channel (optional): 'ibm_quantum_platform' (free) or 'ibm_cloud' (paid)
    
    Returns:
        JSON with connection status and available backends
    """
    try:
        data = request.get_json() or {}
        api_token = data.get('api_token')
        channel = data.get('channel', 'ibm_quantum_platform')
        
        # First try auto-connect with saved credentials
        if not api_token:
            result = ibm_manager.try_auto_connect()
            if result['success']:
                return jsonify({
                    'success': True,
                    'data': result
                })
        
        # Connect with provided token
        result = ibm_manager.connect(api_token=api_token, channel=channel)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Connection failed'),
                'hint': result.get('hint', 'Get your API token from https://quantum.ibm.com/')
            }), 400
            
    except Exception as e:
        print(f"Error in ibm_connect: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ibm/disconnect', methods=['POST'])
def ibm_disconnect():
    """Disconnect from IBM Quantum service."""
    result = ibm_manager.disconnect()
    return jsonify({
        'success': True,
        'data': result
    })


@app.route('/api/ibm/backends', methods=['GET'])
def ibm_backends():
    """
    Get list of available IBM Quantum backends.
    
    Returns:
        JSON with list of backends and their status
    """
    if not ibm_manager.connected:
        return jsonify({
            'success': False,
            'error': 'Not connected to IBM Quantum',
            'hint': 'Call /api/ibm/connect first'
        }), 400
    
    backends = ibm_manager.get_available_backends()
    return jsonify({
        'success': True,
        'data': {
            'backends': backends,
            'count': len(backends)
        }
    })


@app.route('/api/ibm/select-backend', methods=['POST'])
def ibm_select_backend():
    """
    Select a specific IBM Quantum backend.
    
    Request body:
        backend_name: Name of the backend (e.g., 'ibm_brisbane')
        auto_select (optional): If true, select least busy backend
    
    Returns:
        JSON with selected backend info
    """
    try:
        data = request.get_json() or {}
        backend_name = data.get('backend_name')
        auto_select = data.get('auto_select', False)
        
        if auto_select:
            result = ibm_manager.get_least_busy_backend(min_qubits=5)
        elif backend_name:
            result = ibm_manager.select_backend(backend_name)
        else:
            return jsonify({
                'success': False,
                'error': 'Provide backend_name or set auto_select: true'
            }), 400
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error')
            }), 400
            
    except Exception as e:
        print(f"Error in ibm_select_backend: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/generate-bit-ibm', methods=['POST'])
def generate_bit_ibm():
    """
    Generate a single quantum random bit using IBM Quantum hardware.
    
    Request body:
        shots (optional): Number of measurements (default: 1000, max: 4000 for free tier)
        use_ibm (optional): If true, use IBM hardware; else use simulator
    
    Returns:
        JSON with bit value, counts, and backend info
    """
    try:
        data = request.get_json() or {}
        shots = min(data.get('shots', 1000), 4000)  # IBM free tier limit
        use_ibm = data.get('use_ibm', False)
        
        from qiskit import QuantumCircuit
        
        # Create simple 1-qubit circuit
        qc = QuantumCircuit(1, 1)
        qc.h(0)
        qc.measure(0, 0)
        
        # Run on selected backend
        result = ibm_manager.run_circuit(qc, shots=shots, use_ibm=use_ibm)
        
        if not result['success']:
            return jsonify({
                'success': False,
                'error': result.get('error'),
                'hint': result.get('hint')
            }), 400
        
        counts = result['counts']
        bit_value = max(counts, key=counts.get) if counts else '0'
        
        return jsonify({
            'success': True,
            'data': {
                'bit': bit_value,
                'counts': counts,
                'shots': shots,
                'backend': result['backend'],
                'backend_type': result['backend_type'],
                'job_id': result.get('job_id')
            }
        })
        
    except Exception as e:
        print(f"Error in generate_bit_ibm: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
    print('Quantum Random Key Generator API - Enhanced Edition')
    print('=' * 60)
    print('Starting Flask server on http://localhost:5000')
    print('\nCore Endpoints:')
    print('  POST /api/generate-bit    - Generate single quantum bit')
    print('  POST /api/generate-random - Generate multi-bit random number')
    print('  POST /api/generate-key    - Generate secure cryptographic key')
    print('  GET  /api/info            - Get quantum randomness information')
    print('\nCryptography & Analysis:')
    print('  POST /api/encrypt         - AES encrypt with quantum key')
    print('  POST /api/decrypt         - AES decrypt with quantum key')
    print('  POST /api/encrypt-file    - Encrypt file data')
    print('  POST /api/analyze-entropy - Analyze randomness quality')
    print('  GET  /api/compare         - Classical vs Quantum comparison')
    print('  POST /api/generate-classical - Generate classical random bits')
    print('\nIBM Quantum Hardware:')
    print('  GET  /api/ibm/status      - Check IBM connection status')
    print('  POST /api/ibm/connect     - Connect to IBM Quantum')
    print('  POST /api/ibm/disconnect  - Disconnect from IBM Quantum')
    print('  GET  /api/ibm/backends    - List available backends')
    print('  POST /api/ibm/select-backend - Select a backend')
    print('  POST /api/generate-bit-ibm - Generate bit on IBM hardware')
    print(f'\nIBM Quantum Runtime: {"AVAILABLE" if IBM_AVAILABLE else "NOT INSTALLED"}')
    print('=' * 60)

    app.run(debug=False, host='0.0.0.0', port=5000)
