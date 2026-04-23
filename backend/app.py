"""
Flask REST API for Quantum Random Key Generator
Provides endpoints for quantum random number generation
Enhanced with cryptography, entropy analysis, classical comparison, and IBM Quantum hardware
"""

from flask import Flask, jsonify, request, send_from_directory, g
from flask_cors import CORS
from quantum_generator import QuantumRandomGenerator
from crypto_engine import CryptoEngine
from entropy_analyzer import EntropyAnalyzer
from comparator import RandomnessComparator
from ibm_quantum import ibm_manager, IBM_AVAILABLE
import traceback
import os
import base64
import time
from ml_data_logger import QuantumDataLogger
from ml_model_trainer import QuantumKeyQualityClassifier
from ml_error_corrector import QuantumKeyErrorCorrector
from monitoring_setup import (
    HealthCheck,
    alert_manager,
    performance_monitor,
    production_logger,
)

# Get the directory path for frontend build files
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build')

app = Flask(__name__, static_folder=FRONTEND_BUILD_DIR, static_url_path='')
CORS(app)  # Enable CORS for frontend communication


@app.before_request
def _begin_request_timing():
    g.request_start = time.perf_counter()


@app.after_request
def _record_request_metrics(response):
    try:
        if request.path.startswith('/api/'):
            start = getattr(g, 'request_start', None)
            duration_ms = ((time.perf_counter() - start) * 1000.0) if start else 0.0
            success = response.status_code < 400
            performance_monitor.record_request(request.path, duration_ms, success=success)
            production_logger.log_api_call(
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

            snapshot = performance_monitor.get_metrics()
            alert_manager.check_error_rate(
                snapshot.get('total_errors', 0),
                snapshot.get('total_requests', 0),
            )
            alert_manager.check_response_time(snapshot.get('avg_response_time_ms', 0.0))
    except Exception as exc:
        production_logger.log_error(
            error_type=type(exc).__name__,
            error_message=str(exc),
            traceback_str=traceback.format_exc(),
            endpoint='/internal/request-metrics',
        )
    return response

# Initialize quantum generator
qrng = QuantumRandomGenerator()

# Initialize new modules
crypto_engine = CryptoEngine()
entropy_analyzer = EntropyAnalyzer()
comparator = RandomnessComparator(quantum_generator=qrng, ibm_manager=ibm_manager)

# Initialize ML data logger for training data collection
ml_logger = QuantumDataLogger()

# Initialize ML classifier (optional enhancement)
ml_classifier = QuantumKeyQualityClassifier()
ml_classifier_loaded = ml_classifier.load_model()
ml_corrector = QuantumKeyErrorCorrector(ml_classifier, ml_logger)

def _extract_entropy_score_for_ml(entropy_analysis):
    """Map entropy analyzer output to a smooth 0..1 score for ML inference."""
    if not isinstance(entropy_analysis, dict):
        return None

    tests = entropy_analysis.get('tests', {}) if isinstance(entropy_analysis.get('tests', {}), dict) else {}
    shannon_test = tests.get('shannon_entropy', {}) if isinstance(tests.get('shannon_entropy', {}), dict) else {}
    shannon = shannon_test.get('entropy', None)
    block_entropy = shannon_test.get('block_entropy', None)

    try:
        if shannon is not None:
            shannon_val = max(0.0, min(1.0, float(shannon)))
            if block_entropy is not None:
                block_val = max(0.0, min(1.0, float(block_entropy)))
                return (0.8 * shannon_val) + (0.2 * block_val)
            return shannon_val

        overall_score = entropy_analysis.get('overall_score', None)
        if overall_score is not None:
            return max(0.0, min(1.0, float(overall_score) / 100.0))
    except Exception:
        return None

    return None


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
        enable_ml_correction (optional): Regenerate on bad ML quality (default: False)
        max_attempts (optional): Max regeneration attempts when correction enabled (default: 3)

    Returns:
        JSON with secure key in binary and hex formats, plus quantum metadata
    """
    try:
        data = request.get_json() or {}
        key_length = data.get('key_length', 256)
        shots = data.get('shots', 1024)
        enable_ml_correction = bool(data.get('enable_ml_correction', False))
        max_attempts = data.get('max_attempts', 3)

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
        
        if not isinstance(max_attempts, int) or max_attempts < 1 or max_attempts > 10:
            return jsonify({
                'error': 'max_attempts must be an integer between 1 and 10'
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
            # For IBM mode, keep single-run behavior to avoid queue amplification.
            if enable_ml_correction:
                result['ml_correction_note'] = 'ML correction loop is only available for simulator mode'
        else:
            if enable_ml_correction and ml_classifier_loaded:
                try:
                    result = ml_corrector.generate_with_quality_improvement(
                        key_generator=qrng,
                        key_length=key_length,
                        shots=shots,
                        enable_correction=True,
                        max_attempts=max_attempts
                    )
                except Exception as correction_error:
                    print(f"ML correction failed, falling back to standard generation: {correction_error}")
                    result = qrng.generate_secure_key(key_length=key_length, shots=shots)
            else:
                result = qrng.generate_secure_key(key_length=key_length, shots=shots)

        entropy_analysis = None
        entropy_score_for_ml = None
        try:
            entropy_analysis = entropy_analyzer.analyze_randomness(result.get('binary', ''))
            entropy_score_for_ml = _extract_entropy_score_for_ml(entropy_analysis)
        except Exception:
            entropy_analysis = None
            entropy_score_for_ml = None

        # Optional ML quality assessment (non-blocking)
        try:
            if ml_classifier_loaded and result.get('binary'):
                bit_distribution = result['binary'].count('1') / max(1, len(result['binary']))
                result['ml_quality_assessment'] = ml_classifier.predict_quality(
                    generation_time_ms=result.get('generation_time_ms', 0),
                    shots_used=shots,
                    num_qubits=max(1, key_length // 16),
                    bit_distribution=bit_distribution,
                    entropy_score=entropy_score_for_ml,
                )
        except Exception as ml_error:
            print(f"ML assessment failed (non-blocking): {ml_error}")

        # Log generation for ML training (non-blocking, silently fails)
        try:
            if entropy_analysis is not None:
                ml_logger.log_generation(result, entropy_analysis, source='quantum')
        except Exception as ml_error:
            pass  # Silently ignore logging errors - don't break key generation

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


@app.route('/api/decrypt-file', methods=['POST'])
def decrypt_file():
    """
    Decrypt file data using AES with a quantum-generated key.

    Request body:
        encrypted_data: Base64 encoded encrypted file content
        key: Hex string key (same as used for encryption)
        iv: Base64 encoded IV from encryption response
        key_size (optional): 128 or 256 (default: 256)

    Returns:
        JSON with decrypted file data and metadata
    """
    try:
        data = request.get_json() or {}

        encrypted_data_b64 = data.get('encrypted_data')
        key = data.get('key')
        iv = data.get('iv')
        key_size = data.get('key_size', 256)

        if not encrypted_data_b64:
            return jsonify({'success': False, 'error': 'encrypted_data is required'}), 400
        if not key:
            return jsonify({'success': False, 'error': 'Key is required'}), 400
        if not iv:
            return jsonify({'success': False, 'error': 'IV is required'}), 400

        result = crypto_engine.decrypt_file(encrypted_data_b64, key, iv, key_size)

        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result
            })

        return jsonify({
            'success': False,
            'error': result.get('error', 'File decryption failed')
        }), 400

    except Exception as e:
        print(f"Error in decrypt_file: {traceback.format_exc()}")
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
        shots (optional): Number of shots (default: 256 for hosted, max: 4000)
    
    Returns:
        JSON with comprehensive comparison data
    """
    try:
        length = request.args.get('length', 256, type=int)
        mode = request.args.get('mode', 'simulator', type=str)
        shots = request.args.get('shots', 256, type=int)  # Reduced from 1024 to 256 for hosted environments
        
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

        # Log comparison data for ML training (non-blocking)
        try:
            quantum_data = result.get('quantum_generation', {})
            classical_data = result.get('classical_generation', {})
            comparison_stats = result.get('comparison', {})
            
            if quantum_data and not quantum_data.get('error'):
                quantum_entropy = {
                    'entropy_score': comparison_stats.get('quantum_randomness_quality', 0),
                    'shannon_entropy': comparison_stats.get('quantum_shannon_entropy', 0),
                    'min_entropy': comparison_stats.get('quantum_min_entropy', 0)
                }
                ml_logger.log_generation(quantum_data, quantum_entropy, source='quantum')
            
            if classical_data and not classical_data.get('error'):
                classical_entropy = {
                    'entropy_score': comparison_stats.get('classical_randomness_quality', 0),
                    'shannon_entropy': comparison_stats.get('classical_shannon_entropy', 0),
                    'min_entropy': comparison_stats.get('classical_min_entropy', 0)
                }
                ml_logger.log_generation(classical_data, classical_entropy, source='classical')
        except Exception as ml_error:
            pass  # Silently ignore logging errors - don't break comparison

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
        channel (optional): 'ibm_quantum' (free) or 'ibm_cloud' (paid)
    
    Returns:
        JSON with connection status and available backends
    """
    try:
        data = request.get_json() or {}
        api_token = data.get('api_token')
        channel = data.get('channel', 'ibm_quantum')
        
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


@app.route('/api/ml/status', methods=['GET'])
def ml_status():
    """Get ML model status, metadata, and dataset readiness."""
    try:
        stats = ml_logger.get_dataset_stats()

        from ml_data_collector import MLDataPreprocessor
        preprocessor = MLDataPreprocessor()
        quality = preprocessor.validate_data_quality()

        if not ml_classifier_loaded:
            return jsonify({
                'success': True,
                'data': {
                    'model_loaded': False,
                    'message': 'ML model not yet trained. Train with /api/ml/train',
                    'dataset': stats,
                    'quality': quality,
                    'infrastructure': {
                        'logging_active': True,
                        'bootstrap_complete': quality.get('num_samples', 0) >= 500,
                        'ready_for_training': quality.get('is_valid', False)
                    }
                }
            })

        metadata = ml_classifier.get_metadata()

        return jsonify({
            'success': True,
            'data': {
                'model_loaded': True,
                'model': metadata,
                'dataset': stats,
                'quality': quality,
                'infrastructure': {
                    'logging_active': True,
                    'bootstrap_complete': quality.get('num_samples', 0) >= 500,
                    'ready_for_training': quality.get('is_valid', False)
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ml/train', methods=['POST'])
def train_ml_model():
    """Train or retrain ML model from collected dataset."""
    global ml_classifier_loaded

    try:
        data = request.get_json() or {}
        force_retrain = data.get('force', False)

        if ml_classifier_loaded and not force_retrain:
            return jsonify({
                'success': False,
                'error': 'Model already trained. Use force:true to retrain'
            }), 400

        X, y, df = ml_classifier.prepare_data()
        if len(df) < 500:
            return jsonify({
                'success': False,
                'error': f'Need at least 500 samples, have {len(df)}'
            }), 400

        metrics = ml_classifier.train(X, y)
        metadata = ml_classifier.save_model()
        ml_classifier_loaded = True

        return jsonify({
            'success': True,
            'data': {
                'message': 'Model trained successfully',
                'metrics': metrics,
                'metadata': metadata,
                'samples_used': len(df)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ml/init-bootstrap', methods=['POST'])
def ml_init_bootstrap():
    """Initialize ML infrastructure with bootstrap data (one-time setup)"""
    try:
        from ml_data_collector import MLDataPreprocessor
        preprocessor = MLDataPreprocessor()
        
        success = preprocessor.generate_synthetic_data(num_samples=500)
        
        if success:
            stats = ml_logger.get_dataset_stats()
            return jsonify({
                'success': True,
                'message': 'Bootstrap data generated successfully',
                'data': stats
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate bootstrap data'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ml/generate-key-improved', methods=['POST'])
def generate_key_improved():
    """
    Generate quantum key with automatic ML-based quality improvement.
    """
    try:
        data = request.get_json() or {}
        key_length = data.get('key_length', 256)
        shots = data.get('shots', 1024)
        max_attempts = data.get('max_attempts', 3)

        if key_length not in [128, 256, 512]:
            return jsonify({'success': False, 'error': 'key_length must be 128, 256, or 512'}), 400
        if not isinstance(shots, int) or shots < 1 or shots > 10000:
            return jsonify({'success': False, 'error': 'shots must be an integer between 1 and 10000'}), 400
        if not isinstance(max_attempts, int) or max_attempts < 1 or max_attempts > 10:
            return jsonify({'success': False, 'error': 'max_attempts must be an integer between 1 and 10'}), 400

        if not ml_classifier_loaded:
            return jsonify({
                'success': False,
                'error': 'ML model not trained yet',
                'hint': 'Call /api/ml/train first'
            }), 400

        result = ml_corrector.generate_with_quality_improvement(
            key_generator=qrng,
            key_length=key_length,
            shots=shots,
            enable_correction=True,
            max_attempts=max_attempts
        )

        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ml/ab-test-results', methods=['GET'])
def get_ab_test_results():
    """Get A/B test analysis for control vs ML-corrected generation."""
    try:
        results = ml_corrector.get_ab_test_results()
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ml/correction-stats', methods=['GET'])
def get_correction_stats():
    """Get correction usage and impact statistics."""
    try:
        stats = ml_corrector.get_correction_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ml/improvement-summary', methods=['GET'])
def ml_improvement_summary():
    """Get summary of ML correction gain vs latency cost."""
    try:
        ab_results = ml_corrector.get_ab_test_results()
        control = ab_results.get('control', {})
        treated = ab_results.get('treated', {})

        control_entropy = float(control.get('avg_entropy', 0.0) or 0.0)
        treated_entropy = float(treated.get('avg_entropy', 0.0) or 0.0)
        control_time = float(control.get('avg_time_ms', 0.0) or 0.0)
        treated_time = float(treated.get('avg_time_ms', 0.0) or 0.0)

        entropy_improvement = 0.0
        if control_entropy > 0:
            entropy_improvement = ((treated_entropy - control_entropy) / control_entropy) * 100.0

        latency_increase = 0.0
        if control_time > 0:
            latency_increase = ((treated_time - control_time) / control_time) * 100.0

        roi = entropy_improvement / max(abs(latency_increase), 1.0)
        recommendation = 'Yes, use ML correction' if roi > 1 else 'Latency may outweigh benefit'

        return jsonify({
            'success': True,
            'data': {
                'entropy_improvement_percent': round(entropy_improvement, 2),
                'latency_cost_percent': round(latency_increase, 2),
                'roi_ratio': round(roi, 2),
                'recommendation': recommendation,
                'ab_results': ab_results
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/system-health', methods=['GET'])
def system_health():
    """Comprehensive system health check for admin monitoring dashboards."""
    try:
        health = HealthCheck.full_system_health()
        storage_usage = health.get('checks', {}).get('storage', {}).get('usage_percent', 0.0)
        alert_manager.check_storage_usage(storage_usage)
        return jsonify({
            'success': True,
            'data': health
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/performance-metrics', methods=['GET'])
def performance_metrics():
    """Get cumulative API performance metrics collected in-process."""
    try:
        metrics = performance_monitor.get_metrics()
        return jsonify({
            'success': True,
            'data': metrics
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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
    print('  POST /api/decrypt-file    - Decrypt file data')
    print('  POST /api/analyze-entropy - Analyze randomness quality')
    print('  GET  /api/compare         - Classical vs Quantum comparison')
    print('  POST /api/generate-classical - Generate classical random bits')
    print('\nMonitoring & Admin:')
    print('  GET  /api/admin/system-health - Full system health snapshot')
    print('  GET  /api/admin/performance-metrics - API performance metrics')
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
