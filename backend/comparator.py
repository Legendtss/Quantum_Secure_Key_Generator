"""
Comparator Module - Classical vs Quantum Random Number Generation Comparison
Benchmarks and compares different random number generation methods
"""

import time
import random
import hashlib
from typing import Dict, List
from entropy_analyzer import EntropyAnalyzer


class RandomnessComparator:
    """Compare classical PRNG with quantum random number generation"""
    
    def __init__(self, quantum_generator=None, ibm_manager=None):
        """
        Initialize comparator with optional quantum generator.
        
        Args:
            quantum_generator: Instance of QuantumRandomGenerator
        """
        self.quantum_generator = quantum_generator
        self.ibm_manager = ibm_manager
        self.entropy_analyzer = EntropyAnalyzer()
        self.classical_rng = random.Random()
    
    def generate_classical_random(self, length: int, seed: int = None) -> Dict:
        """
        Generate random bits using Python's Mersenne Twister PRNG.
        
        Args:
            length: Number of bits to generate
            seed: Optional seed for reproducibility
            
        Returns:
            dict: Generated bits and metadata
        """
        start_time = time.perf_counter()
        
        if seed is not None:
            self.classical_rng.seed(seed)
        
        # Generate bits
        bits = ''.join(str(self.classical_rng.randint(0, 1)) for _ in range(length))
        
        generation_time = (time.perf_counter() - start_time) * 1000
        generation_time = max(generation_time, 0.001)
        
        # Convert to hex
        hex_value = hex(int(bits, 2))[2:].upper().zfill(length // 4) if length >= 4 else ''
        
        return {
            'method': 'Classical PRNG',
            'algorithm': 'Mersenne Twister (MT19937)',
            'binary': bits,
            'hex': hex_value,
            'length': length,
            'generation_time_ms': round(generation_time, 3),
            'bits_per_ms': round(length / generation_time, 2) if generation_time > 0 else 0,
            'seed_used': seed is not None,
            'deterministic': True,
            'source': 'Mathematical algorithm',
            'cryptographic_strength': 'weak'
        }
    
    def generate_quantum_random(self, length: int, mode: str = 'simulator', shots: int = 1024) -> Dict:
        """
        Generate random bits using quantum circuit simulation.
        
        Args:
            length: Number of bits to generate
            
        Returns:
            dict: Generated bits and metadata
        """
        if mode == 'ibm_hardware':
            return self._generate_quantum_random_ibm(length=length, shots=shots)
        return self._generate_quantum_random_simulator(length=length, shots=shots)

    def _generate_quantum_random_simulator(self, length: int, shots: int = 1024) -> Dict:
        """Generate random bits using local quantum circuit simulation."""
        if self.quantum_generator is None:
            return {
                'error': 'Quantum simulator generator not available',
                'method': 'Quantum'
            }

        start_time = time.perf_counter()

        all_bits = []
        chunks = (length + 7) // 8

        for _ in range(chunks):
            bits = self.quantum_generator._generate_raw_bits(num_qubits=8, shots=shots)
            all_bits.append(bits)

        binary = ''.join(all_bits)[:length]
        generation_time = (time.perf_counter() - start_time) * 1000
        generation_time = max(generation_time, 0.001)
        hex_value = hex(int(binary, 2))[2:].upper().zfill(length // 4) if length >= 4 else ''

        return {
            'method': 'Quantum RNG',
            'algorithm': 'Hadamard Gate Superposition (Qiskit Aer Simulator)',
            'binary': binary,
            'hex': hex_value,
            'length': length,
            'generation_time_ms': round(generation_time, 3),
            'bits_per_ms': round(length / generation_time, 2),
            'chunks_generated': chunks,
            'shots_per_chunk': shots,
            'deterministic': False,
            'source': 'Quantum mechanical uncertainty (simulated)',
            'backend_type': 'simulator',
            'cryptographic_strength': 'strong'
        }

    def _generate_quantum_random_ibm(self, length: int, shots: int = 100) -> Dict:
        """Generate random bits using real IBM Quantum hardware."""
        if self.ibm_manager is None:
            return {
                'error': 'IBM manager not available',
                'method': 'Quantum'
            }

        start_time = time.perf_counter()
        ibm_result = self.ibm_manager.generate_secure_key(key_length=length, shots=shots)
        generation_time = (time.perf_counter() - start_time) * 1000
        generation_time = max(generation_time, 0.001)

        if not ibm_result.get('success'):
            return {
                'error': ibm_result.get('error', 'IBM hardware generation failed'),
                'method': 'Quantum',
                'detail': ibm_result.get('detail'),
                'hint': ibm_result.get('hint'),
                'backend_type': 'ibm_quantum'
            }

        return {
            'method': 'Quantum RNG',
            'algorithm': 'IBM Quantum Runtime Sampler (Real Hardware)',
            'binary': ibm_result.get('binary', ''),
            'hex': ibm_result.get('hex', ''),
            'length': length,
            'generation_time_ms': round(generation_time, 3),
            'bits_per_ms': round(length / generation_time, 2),
            'chunks_generated': ibm_result.get('chunks_generated'),
            'shots_per_chunk': ibm_result.get('shots_per_chunk', shots),
            'deterministic': False,
            'source': 'IBM Quantum hardware',
            'backend_type': 'ibm_quantum',
            'backend': ibm_result.get('backend'),
            'job_ids': ibm_result.get('job_ids', []),
            'cryptographic_strength': 'strong'
        }
    
    def benchmark_speed(self, method: str, length: int, iterations: int = 10) -> Dict:
        """
        Benchmark the speed of a random generation method.
        
        Args:
            method: 'classical' or 'quantum'
            length: Number of bits per generation
            iterations: Number of iterations for averaging
            
        Returns:
            dict: Benchmark results
        """
        times = []
        
        for _ in range(iterations):
            start = time.time()
            
            if method == 'classical':
                self.generate_classical_random(length)
            elif method == 'quantum':
                if self.quantum_generator:
                    self.generate_quantum_random(length)
                else:
                    return {'error': 'Quantum generator not available'}
            else:
                return {'error': f'Unknown method: {method}'}
            
            times.append((time.time() - start) * 1000)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        return {
            'method': method,
            'bits_per_generation': length,
            'iterations': iterations,
            'average_time_ms': round(avg_time, 3),
            'min_time_ms': round(min_time, 3),
            'max_time_ms': round(max_time, 3),
            'bits_per_second': round((length * 1000) / avg_time, 0) if avg_time > 0 else 0,
            'times_ms': [round(t, 3) for t in times]
        }
    
    def compare_entropy(self, classical_bits: str, quantum_bits: str) -> Dict:
        """
        Compare entropy analysis of classical and quantum bit strings.
        
        Args:
            classical_bits: Classical PRNG generated bits
            quantum_bits: Quantum generated bits
            
        Returns:
            dict: Comparative entropy analysis
        """
        classical_analysis = self.entropy_analyzer.analyze_randomness(classical_bits)
        quantum_analysis = self.entropy_analyzer.analyze_randomness(quantum_bits)
        
        # Extract key metrics for comparison
        comparison = {
            'classical': {
                'overall_score': classical_analysis.get('overall_score', 0),
                'verdict': classical_analysis.get('verdict', 'Unknown'),
                'entropy': classical_analysis.get('tests', {}).get('shannon_entropy', {}).get('entropy', 0),
                'passed_tests': classical_analysis.get('passed_tests', 0),
                'total_tests': classical_analysis.get('total_tests', 0)
            },
            'quantum': {
                'overall_score': quantum_analysis.get('overall_score', 0),
                'verdict': quantum_analysis.get('verdict', 'Unknown'),
                'entropy': quantum_analysis.get('tests', {}).get('shannon_entropy', {}).get('entropy', 0),
                'passed_tests': quantum_analysis.get('passed_tests', 0),
                'total_tests': quantum_analysis.get('total_tests', 0)
            },
            'full_classical_analysis': classical_analysis,
            'full_quantum_analysis': quantum_analysis
        }
        
        # Determine winner for each test
        test_winners = {}
        if 'tests' in classical_analysis and 'tests' in quantum_analysis:
            for test_name in classical_analysis['tests'].keys():
                c_passed = classical_analysis['tests'][test_name].get('passed', False)
                q_passed = quantum_analysis['tests'].get(test_name, {}).get('passed', False)
                
                if c_passed and q_passed:
                    test_winners[test_name] = 'tie'
                elif c_passed:
                    test_winners[test_name] = 'classical'
                elif q_passed:
                    test_winners[test_name] = 'quantum'
                else:
                    test_winners[test_name] = 'neither'
        
        comparison['test_winners'] = test_winners
        
        return comparison
    
    def full_comparison(self, length: int = 256, mode: str = 'simulator', shots: int = 1024) -> Dict:
        """
        Perform a comprehensive comparison between classical and quantum RNG.
        
        Args:
            length: Number of bits to generate for comparison
            
        Returns:
            dict: Complete comparison data
        """
        results = {
            'comparison_parameters': {
                'bit_length': length,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'mode': mode,
                'shots': shots
            }
        }
        
        # Generate bits from both methods
        classical_result = self.generate_classical_random(length)
        results['classical_generation'] = classical_result
        
        quantum_result = self.generate_quantum_random(length=length, mode=mode, shots=shots)
        if quantum_result.get('error'):
            # Fallback for demo mode only when simulator path is unavailable.
            if mode == 'simulator':
                quantum_result = self._simulate_quantum_random(length)
            results['quantum_generation'] = quantum_result
        else:
            results['quantum_generation'] = quantum_result
        
        # Run entropy comparison
        classical_bits = classical_result.get('binary', '')
        quantum_bits = quantum_result.get('binary', '')
        
        if classical_bits and quantum_bits:
            results['entropy_comparison'] = self.compare_entropy(classical_bits, quantum_bits)
        
        # Speed comparison
        classical_time = classical_result.get('generation_time_ms', 0)
        quantum_time = quantum_result.get('generation_time_ms', 0)
        # Guard against rounded near-zero classical times that inflate ratio.
        safe_classical_time = max(classical_time, 0.1)
        safe_quantum_time = max(quantum_time, 0.1)
        ratio = round(safe_quantum_time / safe_classical_time, 2)
        if classical_time < quantum_time:
            faster = 'classical'
            speed_message = f'Classical is {ratio}x faster'
        elif quantum_time < classical_time:
            faster = 'quantum'
            speed_message = f'Quantum is {round(safe_classical_time / safe_quantum_time, 2)}x faster'
        else:
            faster = 'tie'
            speed_message = 'Both methods have similar speed'

        note = 'Quantum simulator includes local circuit execution overhead'
        if mode == 'ibm_hardware':
            note = 'IBM hardware includes remote queue + execution latency'

        results['speed_comparison'] = {
            'classical_time_ms': classical_result.get('generation_time_ms', 0),
            'quantum_time_ms': quantum_result.get('generation_time_ms', 0),
            'speed_ratio': ratio,
            'faster': faster,
            'message': speed_message,
            'note': note
        }
        
        # Summary table data
        results['summary'] = {
            'metrics': [
                {
                    'metric': 'Generation Speed',
                    'classical': f"{classical_result.get('generation_time_ms', 0):.3f} ms",
                    'quantum': f"{quantum_result.get('generation_time_ms', 0):.3f} ms",
                    'winner': 'classical' if classical_result.get('generation_time_ms', float('inf')) < quantum_result.get('generation_time_ms', float('inf')) else 'quantum'
                },
                {
                    'metric': 'Entropy Score',
                    'classical': f"{results.get('entropy_comparison', {}).get('classical', {}).get('overall_score', 0):.1f}%",
                    'quantum': f"{results.get('entropy_comparison', {}).get('quantum', {}).get('overall_score', 0):.1f}%",
                    'winner': 'quantum' if results.get('entropy_comparison', {}).get('quantum', {}).get('overall_score', 0) >= results.get('entropy_comparison', {}).get('classical', {}).get('overall_score', 0) else 'classical'
                },
                {
                    'metric': 'Deterministic',
                    'classical': 'Yes (same seed = same output)',
                    'quantum': 'No (true randomness)',
                    'winner': 'quantum'
                },
                {
                    'metric': 'Cryptographic Use',
                    'classical': 'Not suitable (MT19937 is predictable)',
                    'quantum': 'Strong entropy source for keys',
                    'winner': 'quantum'
                },
                {
                    'metric': 'Reproducibility',
                    'classical': 'Yes (useful for testing)',
                    'quantum': 'No',
                    'winner': 'depends'
                }
            ]
        }

        results['security_comparison'] = {
            'classical': {
                'model': 'Algorithmic PRNG (MT19937)',
                'predictability': 'Predictable if internal state is recovered',
                'known_attack': 'State recovery from 624 observed 32-bit outputs',
                'impact': 'Future outputs become predictable after state compromise',
                'recommendation': 'Do not use MT19937 directly for key generation'
            },
            'quantum': {
                'model': 'Physical quantum measurement outcomes',
                'predictability': 'No deterministic PRNG state to clone or rewind',
                'known_attack': 'No MT-style state-recovery shortcut on randomness source',
                'impact': 'Attacker is limited to brute force by key length',
                'recommendation': 'Preferred entropy source for key material'
            },
            'conclusion': (
                'For equal key length, brute-force complexity is similar, but MT19937 adds '
                'predictability risk through state recovery. Quantum entropy removes that '
                'PRNG-state attack path, so generated keys are harder to predict.'
            )
        }
        
        return results
    
    def _simulate_quantum_random(self, length: int) -> Dict:
        """
        Simulate quantum random generation (for when real generator unavailable).
        Uses os.urandom for cryptographic randomness as simulation.
        """
        import os
        
        start_time = time.time()
        
        # Generate using cryptographic random
        num_bytes = (length + 7) // 8
        random_bytes = os.urandom(num_bytes)
        binary = bin(int.from_bytes(random_bytes, 'big'))[2:].zfill(num_bytes * 8)[:length]
        
        generation_time = (time.time() - start_time) * 1000
        
        hex_value = hex(int(binary, 2))[2:].upper().zfill(length // 4) if length >= 4 else ''
        
        return {
            'method': 'Quantum RNG (Simulated)',
            'algorithm': 'Hadamard Gate Superposition (Simulated with os.urandom)',
            'binary': binary,
            'hex': hex_value,
            'length': length,
            'generation_time_ms': round(generation_time, 3),
            'bits_per_ms': round(length / generation_time, 2),
            'deterministic': False,
            'source': 'Quantum mechanical uncertainty (simulated)',
            'note': 'Simulated using cryptographic random when quantum simulator unavailable',
            'cryptographic_strength': 'strong'
        }


# Example usage for testing
if __name__ == "__main__":
    comparator = RandomnessComparator()
    
    print("=== Classical vs Quantum Comparison ===")
    
    # Test classical generation
    classical = comparator.generate_classical_random(256)
    print(f"\nClassical ({classical['algorithm']}):")
    print(f"  Time: {classical['generation_time_ms']}ms")
    print(f"  Bits: {classical['binary'][:64]}...")
    
    # Test simulated quantum
    print("\n=== Full Comparison (256 bits) ===")
    comparison = comparator.full_comparison(256)
    
    print("\nSummary:")
    for metric in comparison['summary']['metrics']:
        print(f"  {metric['metric']}:")
        print(f"    Classical: {metric['classical']}")
        print(f"    Quantum: {metric['quantum']}")
        print(f"    Winner: {metric['winner']}")
