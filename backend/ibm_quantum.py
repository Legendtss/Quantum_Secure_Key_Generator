"""
IBM Quantum Backend Integration Module
Enables running quantum circuits on real IBM Quantum hardware
"""

import os
from typing import Dict, Optional, List
import hashlib
import secrets
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Try to import IBM Quantum provider.
# Treat runtime service import as the source of truth for "installed".
IBM_IMPORT_ERROR = None
SAMPLER_IMPORT_ERROR = None
SAMPLER_VARIANT = None

try:
    from qiskit_ibm_runtime import QiskitRuntimeService
    IBM_AVAILABLE = True
except ImportError as exc:
    IBM_AVAILABLE = False
    IBM_IMPORT_ERROR = str(exc)
    QiskitRuntimeService = None

Sampler = None
if IBM_AVAILABLE:
    try:
        from qiskit_ibm_runtime import SamplerV2 as Sampler
        SAMPLER_VARIANT = "SamplerV2"
    except ImportError:
        try:
            from qiskit_ibm_runtime import Sampler
            SAMPLER_VARIANT = "Sampler"
        except ImportError as exc:
            SAMPLER_IMPORT_ERROR = str(exc)


class IBMQuantumManager:
    """Manage IBM Quantum backend connections and circuit execution"""
    
    def __init__(self):
        self.service: Optional[QiskitRuntimeService] = None
        self.connected = False
        self.current_backend = None
        self.api_token = None
        self.simulator = AerSimulator()
    
    def check_availability(self) -> Dict:
        """Check if IBM Quantum libraries are available"""
        return {
            'ibm_runtime_available': IBM_AVAILABLE,
            'sampler_available': Sampler is not None,
            'sampler_variant': SAMPLER_VARIANT,
            'import_error': IBM_IMPORT_ERROR,
            'sampler_import_error': SAMPLER_IMPORT_ERROR,
            'message': 'IBM Quantum Runtime is available' if IBM_AVAILABLE else 
                      'Install qiskit-ibm-runtime: pip install qiskit-ibm-runtime'
        }
    
    def connect(self, api_token: str = None, channel: str = "ibm_quantum_platform") -> Dict:
        """
        Connect to IBM Quantum service.
        
        Args:
            api_token: IBM Quantum API token (or uses saved token)
            channel: 'ibm_quantum_platform' for free tier, 'ibm_cloud' for paid
            
        Returns:
            dict: Connection status and available backends
        """
        if not IBM_AVAILABLE:
            return {
                'success': False,
                'error': 'IBM Quantum Runtime not installed. Run: pip install qiskit-ibm-runtime',
                'detail': IBM_IMPORT_ERROR
            }
        
        try:
            if api_token:
                # Save credentials for future use
                QiskitRuntimeService.save_account(
                    channel=channel,
                    token=api_token,
                    overwrite=True
                )
                self.api_token = api_token
            
            # Connect to service
            self.service = QiskitRuntimeService(channel=channel)
            self.connected = True
            
            # Get available backends
            backends = self.get_available_backends()
            
            return {
                'success': True,
                'connected': True,
                'channel': channel,
                'backends': backends,
                'message': f'Connected to IBM Quantum. {len(backends)} backends available.'
            }
            
        except Exception as e:
            self.connected = False
            return {
                'success': False,
                'error': str(e),
                'hint': 'Get your API token from https://quantum.ibm.com/'
            }
    
    def disconnect(self) -> Dict:
        """Disconnect from IBM Quantum service"""
        self.service = None
        self.connected = False
        self.current_backend = None
        return {
            'success': True,
            'connected': False,
            'message': 'Disconnected from IBM Quantum'
        }
    
    def get_available_backends(self) -> List[Dict]:
        """Get list of available IBM Quantum backends"""
        if not self.connected or not self.service:
            return []
        
        try:
            backends = self.service.backends()
            backend_info = []
            
            for backend in backends:
                try:
                    status = backend.status()
                    config = backend.configuration() if hasattr(backend, 'configuration') else None
                    
                    backend_info.append({
                        'name': backend.name,
                        'num_qubits': getattr(config, 'n_qubits', None) if config else getattr(backend, 'num_qubits', 'N/A'),
                        'operational': status.operational if status else True,
                        'pending_jobs': status.pending_jobs if status else 0,
                        'status': 'online' if (status and status.operational) else 'offline'
                    })
                except Exception:
                    backend_info.append({
                        'name': backend.name,
                        'num_qubits': 'N/A',
                        'operational': True,
                        'pending_jobs': 0,
                        'status': 'unknown'
                    })
            
            return backend_info
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def select_backend(self, backend_name: str) -> Dict:
        """Select a specific IBM Quantum backend"""
        if not self.connected or not self.service:
            return {
                'success': False,
                'error': 'Not connected to IBM Quantum'
            }
        
        try:
            self.current_backend = self.service.backend(backend_name)
            return {
                'success': True,
                'backend': backend_name,
                'message': f'Selected backend: {backend_name}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_least_busy_backend(self, min_qubits: int = 5) -> Dict:
        """Get the least busy backend with minimum qubit requirement"""
        if not self.connected or not self.service:
            return {
                'success': False,
                'error': 'Not connected to IBM Quantum'
            }
        
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
            
            # Get backends that are operational and have enough qubits
            backends = self.service.backends(
                filters=lambda x: x.status().operational and 
                                 getattr(x, 'num_qubits', 0) >= min_qubits
            )
            
            if not backends:
                return {
                    'success': False,
                    'error': f'No operational backends with {min_qubits}+ qubits available'
                }
            
            # Find least busy
            least_busy = min(backends, key=lambda x: x.status().pending_jobs)
            self.current_backend = least_busy
            
            return {
                'success': True,
                'backend': least_busy.name,
                'pending_jobs': least_busy.status().pending_jobs,
                'message': f'Selected least busy backend: {least_busy.name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_circuit(self, circuit: QuantumCircuit, shots: int = 1024, 
                    use_ibm: bool = False) -> Dict:
        """
        Run a quantum circuit on simulator or IBM Quantum hardware.
        
        Args:
            circuit: Qiskit QuantumCircuit
            shots: Number of measurements
            use_ibm: If True, run on IBM hardware; else use simulator
            
        Returns:
            dict: Execution results
        """
        if use_ibm:
            return self._run_on_ibm(circuit, shots)
        else:
            return self._run_on_simulator(circuit, shots)

    def _sample_bitstring_from_counts(self, counts: Dict, expected_bits: int) -> Optional[str]:
        """Sample one measured bitstring from counts using secure randomness."""
        if not counts:
            return None

        normalized = []
        total = 0

        for key, value in counts.items():
            try:
                weight = int(value)
            except Exception:
                continue
            if weight <= 0:
                continue

            # Keys are usually bitstrings ("01010101"), but keep a robust fallback.
            if isinstance(key, str):
                bitstring = key.replace(" ", "")
            elif isinstance(key, int):
                bitstring = format(key, f"0{expected_bits}b")
            else:
                bitstring = str(key).replace(" ", "")

            if not bitstring or any(ch not in "01" for ch in bitstring):
                continue

            if len(bitstring) < expected_bits:
                bitstring = bitstring.zfill(expected_bits)
            elif len(bitstring) > expected_bits:
                bitstring = bitstring[-expected_bits:]

            normalized.append((bitstring, weight))
            total += weight

        if total <= 0:
            return None

        pick = secrets.randbelow(total)
        cumulative = 0
        for bitstring, weight in normalized:
            cumulative += weight
            if pick < cumulative:
                return bitstring

        return normalized[-1][0]

    def _expand_bitstrings_from_counts(self, counts: Dict, expected_bits: int) -> List[str]:
        """Expand counts into a pool of measured bitstrings."""
        pool: List[str] = []
        if not counts:
            return pool

        for key, value in counts.items():
            try:
                repeats = int(value)
            except Exception:
                continue
            if repeats <= 0:
                continue

            if isinstance(key, str):
                bitstring = key.replace(" ", "")
            elif isinstance(key, int):
                bitstring = format(key, f"0{expected_bits}b")
            else:
                bitstring = str(key).replace(" ", "")

            if not bitstring or any(ch not in "01" for ch in bitstring):
                continue

            if len(bitstring) < expected_bits:
                bitstring = bitstring.zfill(expected_bits)
            elif len(bitstring) > expected_bits:
                bitstring = bitstring[-expected_bits:]

            pool.extend([bitstring] * repeats)

        return pool

    def generate_secure_key(self, key_length: int = 256, shots: int = 100) -> Dict:
        """
        Generate a secure key using real IBM Quantum hardware.

        Returns:
            dict: Same key payload structure as simulator generator
        """
        if not self.connected or not self.service:
            return {
                "success": False,
                "error": "Not connected to IBM Quantum. Please connect first."
            }

        if not self.current_backend:
            selected = self.get_least_busy_backend(min_qubits=5)
            if not selected.get("success"):
                return selected

        chunk_bits = 8
        chunks = (key_length + chunk_bits - 1) // chunk_bits
        shots = min(max(int(shots), 1), 4000)

        all_bits = []
        job_ids = []
        remaining = chunks

        while remaining > 0:
            qc = QuantumCircuit(chunk_bits, chunk_bits)
            for q in range(chunk_bits):
                qc.h(q)
            qc.measure(range(chunk_bits), range(chunk_bits))

            run = self.run_circuit(qc, shots=shots, use_ibm=True)
            if not run.get("success"):
                run["chunk_failed"] = chunks - remaining + 1
                run["chunks_total"] = chunks
                return run

            counts = run.get("counts", {})
            pool = self._expand_bitstrings_from_counts(counts, expected_bits=chunk_bits)
            if not pool:
                return {
                    "success": False,
                    "error": "Failed to extract measured bitstring from IBM Sampler result.",
                    "chunk_failed": chunks - remaining + 1,
                    "chunks_total": chunks,
                    "counts": counts
                }

            if run.get("job_id"):
                job_ids.append(run["job_id"])

            # Pull as many 8-bit chunks as needed from this job's measured pool.
            take = min(remaining, len(pool))
            for _ in range(take):
                idx = secrets.randbelow(len(pool))
                all_bits.append(pool.pop(idx))
            remaining -= take

        full_binary = "".join(all_bits)[:key_length]
        hex_key = hex(int(full_binary, 2))[2:].upper().zfill(key_length // 4)
        key_hash = hashlib.sha256(full_binary.encode()).hexdigest()

        # Sample circuit shape for UI parity with simulator response.
        qc = QuantumCircuit(chunk_bits, chunk_bits)
        for q in range(chunk_bits):
            qc.h(q)
        qc.measure(range(chunk_bits), range(chunk_bits))

        return {
            "success": True,
            "binary": full_binary,
            "hex": hex_key,
            "length": key_length,
            "hash": key_hash,
            "circuit": str(qc.draw("text", fold=-1)),
            "chunks_generated": chunks,
            "shots_per_chunk": shots,
            "backend_type": "ibm_quantum",
            "backend": self.current_backend.name if self.current_backend else None,
            "job_ids": job_ids
        }
    
    def _run_on_simulator(self, circuit: QuantumCircuit, shots: int) -> Dict:
        """Run circuit on local Aer simulator"""
        try:
            compiled = transpile(circuit, self.simulator)
            result = self.simulator.run(compiled, shots=shots).result()
            counts = result.get_counts()
            
            return {
                'success': True,
                'counts': counts,
                'backend': 'aer_simulator',
                'shots': shots,
                'backend_type': 'simulator'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _run_on_ibm(self, circuit: QuantumCircuit, shots: int) -> Dict:
        """Run circuit on IBM Quantum hardware"""
        if not self.connected or not self.service:
            return {
                'success': False,
                'error': 'Not connected to IBM Quantum. Please connect first.'
            }
        
        if not self.current_backend:
            # Try to get least busy backend
            result = self.get_least_busy_backend(min_qubits=circuit.num_qubits)
            if not result['success']:
                return result
        
        try:
            if Sampler is None:
                return {
                    'success': False,
                    'error': 'IBM Runtime Sampler primitive not available in this qiskit-ibm-runtime version.',
                    'detail': SAMPLER_IMPORT_ERROR
                }

            # Transpile for the specific backend
            transpiled = transpile(circuit, self.current_backend)
            
            # qiskit-ibm-runtime >=0.2x uses mode= for backend/session binding.
            sampler = Sampler(mode=self.current_backend)
            
            # Submit job
            job = sampler.run([transpiled], shots=shots)
            
            # Wait for result (this can take a while on real hardware)
            result = job.result()
            
            # Extract counts from SamplerV2 result.
            # For current runtime versions, counts are stored under classical
            # register names (e.g. pub_result.data.c.get_counts()).
            counts = {}
            if hasattr(result, "__getitem__") and len(result) > 0:
                pub_result = result[0]
                data_bin = getattr(pub_result, "data", None)

                if data_bin is not None:
                    # First, look for counts in classical registers present on the
                    # transpiled circuit (typically register name "c").
                    creg_names = [creg.name for creg in transpiled.cregs]
                    for reg_name in creg_names:
                        reg_data = getattr(data_bin, reg_name, None)
                        if reg_data is not None and hasattr(reg_data, "get_counts"):
                            counts = reg_data.get_counts()
                            if counts:
                                break

                    # Backward/alternative compatibility: some examples use "meas".
                    if not counts and hasattr(data_bin, "meas"):
                        meas = getattr(data_bin, "meas")
                        if hasattr(meas, "get_counts"):
                            counts = meas.get_counts()

            if not counts and hasattr(result, "quasi_dists"):
                counts = result.quasi_dists[0]
            
            return {
                'success': True,
                'counts': dict(counts),
                'backend': self.current_backend.name,
                'shots': shots,
                'backend_type': 'ibm_quantum',
                'job_id': job.job_id() if hasattr(job, 'job_id') else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'hint': 'IBM Quantum jobs can take several minutes. Try reducing shots or use simulator.'
            }
    
    def get_connection_status(self) -> Dict:
        """Get current connection status"""
        return {
            'ibm_available': IBM_AVAILABLE,
            'ibm_import_error': IBM_IMPORT_ERROR,
            'sampler_available': Sampler is not None,
            'sampler_variant': SAMPLER_VARIANT,
            'sampler_import_error': SAMPLER_IMPORT_ERROR,
            'connected': self.connected,
            'current_backend': self.current_backend.name if self.current_backend else None,
            'has_saved_credentials': self._check_saved_credentials()
        }
    
    def _check_saved_credentials(self) -> bool:
        """Check if IBM Quantum credentials are saved"""
        if not IBM_AVAILABLE:
            return False
        try:
            accounts = QiskitRuntimeService.saved_accounts()
            return bool(accounts)
        except:
            return False
    
    def try_auto_connect(self) -> Dict:
        """Try to connect using saved credentials"""
        if not IBM_AVAILABLE:
            return {
                'success': False,
                'error': 'IBM Quantum Runtime not installed'
            }
        
        try:
            self.service = QiskitRuntimeService()
            self.connected = True
            backends = self.get_available_backends()
            
            return {
                'success': True,
                'connected': True,
                'message': 'Connected using saved credentials',
                'backends': backends
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'No saved credentials found. Please provide API token.',
                'detail': str(e)
            }


# Global instance
ibm_manager = IBMQuantumManager()


# Example usage
if __name__ == "__main__":
    manager = IBMQuantumManager()
    
    print("=== IBM Quantum Manager ===")
    print(f"IBM Runtime Available: {IBM_AVAILABLE}")
    
    status = manager.get_connection_status()
    print(f"Connection Status: {status}")
    
    # Test simulator
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    
    result = manager.run_circuit(qc, shots=1000, use_ibm=False)
    print(f"\nSimulator Result: {result}")
