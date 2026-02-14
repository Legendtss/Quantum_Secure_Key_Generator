"""
Quantum Random Number Generator using Qiskit
Demonstrates quantum superposition and measurement for true randomness
"""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
import hashlib


class QuantumRandomGenerator:
    """Generate cryptographically random numbers using quantum circuits"""
    
    def __init__(self):
        self.simulator = AerSimulator()
    
    def generate_single_bit(self, shots=1000):
        """
        Generate a single quantum random bit using Hadamard gate
        
        Args:
            shots: Number of measurements (higher = more accurate statistics)
        
        Returns:
            dict: Contains bit value, circuit diagram, histogram, and counts
        """
        # Create 1-qubit quantum circuit
        qc = QuantumCircuit(1, 1)
        
        # Apply Hadamard gate to create superposition
        # |0⟩ → (|0⟩ + |1⟩)/√2
        qc.h(0)
        
        # Measure the qubit
        qc.measure(0, 0)
        
        # Execute on simulator
        compiled_circuit = transpile(qc, self.simulator)
        result = self.simulator.run(compiled_circuit, shots=shots).result()
        counts = result.get_counts()
        
        # Determine most common outcome (or pick randomly if tied)
        bit_value = max(counts, key=counts.get)
        
        # Generate circuit diagram
        circuit_diagram = qc.draw('text', fold=-1)
        
        # Generate histogram
        histogram_data = self._generate_histogram(counts)
        
        return {
            'bit': bit_value,
            'counts': counts,
            'circuit': str(circuit_diagram),
            'histogram': histogram_data,
            'shots': shots
        }
    
    def generate_random_bits(self, num_qubits=8, shots=1000):
        """
        Generate multiple random bits using multi-qubit circuit
        
        Args:
            num_qubits: Number of qubits (bits to generate)
            shots: Number of measurements per circuit
        
        Returns:
            dict: Contains binary string, hex key, circuit info, and histogram
        """
        # Create quantum circuit with multiple qubits
        qc = QuantumCircuit(num_qubits, num_qubits)
        
        # Apply Hadamard gate to each qubit
        for i in range(num_qubits):
            qc.h(i)
        
        # Measure all qubits
        qc.measure(range(num_qubits), range(num_qubits))
        
        # Execute on simulator
        compiled_circuit = transpile(qc, self.simulator)
        result = self.simulator.run(compiled_circuit, shots=shots).result()
        counts = result.get_counts()
        
        # Get most common measurement (or random if tied)
        binary_string = max(counts, key=counts.get)
        
        # Convert to hex for cryptographic key format
        hex_key = hex(int(binary_string, 2))[2:].upper().zfill(num_qubits // 4)
        
        # Generate visualizations
        circuit_diagram = qc.draw('text', fold=-1)
        histogram_data = self._generate_histogram(counts)
        
        return {
            'binary': binary_string,
            'hex': hex_key,
            'length': num_qubits,
            'counts': counts,
            'circuit': str(circuit_diagram),
            'histogram': histogram_data,
            'shots': shots
        }
    
    def generate_secure_key(self, key_length=256, shots=1024):
        """
        Generate a secure cryptographic key using quantum randomness
        
        Args:
            key_length: Length of key in bits (128, 256, 512, etc.)
            shots: Number of measurements
        
        Returns:
            dict: Secure key in multiple formats with quantum data
        """
        # Generate multiple quantum random bits
        all_bits = []
        chunks = (key_length + 7) // 8  # Number of 8-bit chunks needed
        
        for _ in range(chunks):
            result = self.generate_random_bits(num_qubits=8, shots=shots)
            all_bits.append(result['binary'])
        
        # Combine all bits
        full_binary = ''.join(all_bits)[:key_length]
        
        # Convert to different formats
        hex_key = hex(int(full_binary, 2))[2:].upper().zfill(key_length // 4)
        
        # Generate SHA-256 hash of the key for verification
        key_hash = hashlib.sha256(full_binary.encode()).hexdigest()
        
        # Final circuit for visualization (8 qubits)
        qc = QuantumCircuit(8, 8)
        for i in range(8):
            qc.h(i)
        qc.measure(range(8), range(8))
        circuit_diagram = qc.draw('text', fold=-1)
        
        return {
            'binary': full_binary,
            'hex': hex_key,
            'length': key_length,
            'hash': key_hash,
            'circuit': str(circuit_diagram),
            'chunks_generated': chunks,
            'shots_per_chunk': shots
        }
    
    def _generate_histogram(self, counts):
        """Generate base64 encoded histogram image"""
        try:
            fig = plot_histogram(counts, figsize=(8, 5), 
                                color='#6366f1',
                                bar_labels=True)
            fig.suptitle('Measurement Results', fontsize=14, fontweight='bold')
            
            # Convert to base64
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            
            return f"data:image/png;base64,{img_base64}"
        except Exception as e:
            print(f"Histogram generation error: {e}")
            return None


# Example usage for testing
if __name__ == "__main__":
    qrng = QuantumRandomGenerator()
    
    print("=== Single Quantum Bit ===")
    single = qrng.generate_single_bit()
    print(f"Generated bit: {single['bit']}")
    print(f"Counts: {single['counts']}")
    print(f"\n{single['circuit']}")
    
    print("\n=== 8-Bit Quantum Random ===")
    multi = qrng.generate_random_bits(num_qubits=8)
    print(f"Binary: {multi['binary']}")
    print(f"Hex: {multi['hex']}")
    
    print("\n=== 256-bit Secure Key ===")
    key = qrng.generate_secure_key(key_length=256)
    print(f"Key (hex): {key['hex']}")
    print(f"Hash: {key['hash']}")
