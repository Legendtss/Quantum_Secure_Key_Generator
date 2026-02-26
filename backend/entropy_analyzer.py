"""
Entropy Analyzer Module - Statistical Randomness Analysis for Quantum Keys
Implements NIST-inspired randomness tests to validate quantum randomness
"""

import math
from collections import Counter
from typing import Dict, List, Tuple
import random


class EntropyAnalyzer:
    """Analyze entropy and randomness quality of bit strings"""
    
    def __init__(self):
        self.test_results = {}
    
    def analyze_randomness(self, bit_string: str) -> Dict:
        """
        Run comprehensive randomness analysis on a bit string.
        
        Args:
            bit_string: String of '0's and '1's
            
        Returns:
            dict: Results of all randomness tests
        """
        # Validate input
        if not bit_string or not all(c in '01' for c in bit_string):
            return {'error': 'Invalid bit string. Must contain only 0s and 1s.'}
        
        if len(bit_string) < 20:
            return {'error': 'Bit string too short. Need at least 20 bits for meaningful analysis.'}
        
        results = {
            'bit_string_length': len(bit_string),
            'tests': {}
        }
        
        # Run all tests
        results['tests']['frequency'] = self.frequency_test(bit_string)
        results['tests']['runs'] = self.runs_test(bit_string)
        results['tests']['shannon_entropy'] = self.shannon_entropy_test(bit_string)
        results['tests']['serial'] = self.serial_test(bit_string)
        results['tests']['longest_run'] = self.longest_run_test(bit_string)
        results['tests']['autocorrelation'] = self.autocorrelation_test(bit_string)
        
        # Calculate overall score
        passed_tests = sum(1 for test in results['tests'].values() if test.get('passed', False))
        total_tests = len(results['tests'])
        results['overall_score'] = round((passed_tests / total_tests) * 100, 1)
        results['passed_tests'] = passed_tests
        results['total_tests'] = total_tests
        results['verdict'] = 'HIGH QUALITY' if results['overall_score'] >= 80 else 'MODERATE QUALITY' if results['overall_score'] >= 50 else 'LOW QUALITY'
        
        return results
    
    def frequency_test(self, bit_string: str) -> Dict:
        """
        Monobit frequency test - Check if 0s and 1s are roughly equal.
        
        For true randomness, we expect ~50% 0s and ~50% 1s.
        """
        n = len(bit_string)
        ones = bit_string.count('1')
        zeros = n - ones
        
        # Calculate proportions
        proportion_ones = ones / n
        proportion_zeros = zeros / n
        
        # Calculate deviation from 50%
        deviation = abs(proportion_ones - 0.5)
        
        # Chi-square statistic
        expected = n / 2
        chi_square = ((ones - expected) ** 2 / expected) + ((zeros - expected) ** 2 / expected)
        
        # For randomness, deviation should be within ~5% of 50%
        # This corresponds to chi-square < 3.84 (p > 0.05) for 1 degree of freedom
        passed = chi_square < 3.84
        
        return {
            'test_name': 'Frequency (Monobit) Test',
            'description': 'Checks if 0s and 1s appear with equal probability',
            'ones_count': ones,
            'zeros_count': zeros,
            'proportion_ones': round(proportion_ones * 100, 2),
            'proportion_zeros': round(proportion_zeros * 100, 2),
            'deviation_from_50': round(deviation * 100, 2),
            'chi_square': round(chi_square, 4),
            'threshold': 3.84,
            'passed': passed,
            'quality': 'Excellent' if deviation < 0.02 else 'Good' if deviation < 0.05 else 'Acceptable' if passed else 'Poor'
        }
    
    def runs_test(self, bit_string: str) -> Dict:
        """
        Runs test - Check for proper frequency of consecutive bit sequences.
        
        A 'run' is a maximal sequence of consecutive identical bits.
        Too many or too few runs suggests non-randomness.
        """
        n = len(bit_string)
        ones = bit_string.count('1')
        
        # Count runs
        runs = 1
        for i in range(1, n):
            if bit_string[i] != bit_string[i-1]:
                runs += 1
        
        # Expected number of runs
        pi = ones / n
        if pi == 0 or pi == 1:
            return {
                'test_name': 'Runs Test',
                'passed': False,
                'error': 'Bit string is all 0s or all 1s'
            }
        
        expected_runs = 1 + 2 * ones * (n - ones) / n
        variance = (2 * ones * (n - ones) * (2 * ones * (n - ones) - n)) / (n * n * (n - 1))
        
        if variance <= 0:
            variance = 0.001  # Avoid division by zero
        
        # Z-score
        z_score = (runs - expected_runs) / math.sqrt(variance) if variance > 0 else 0
        
        # Pass if Z-score is within ±1.96 (95% confidence)
        passed = abs(z_score) < 1.96
        
        return {
            'test_name': 'Runs Test',
            'description': 'Checks for proper distribution of consecutive bit sequences',
            'total_runs': runs,
            'expected_runs': round(expected_runs, 2),
            'deviation': round(abs(runs - expected_runs), 2),
            'z_score': round(z_score, 4),
            'threshold': 1.96,
            'passed': passed,
            'quality': 'Excellent' if abs(z_score) < 1.0 else 'Good' if abs(z_score) < 1.5 else 'Acceptable' if passed else 'Poor'
        }
    
    def shannon_entropy_test(self, bit_string: str) -> Dict:
        """
        Shannon Entropy calculation - Measure information content.
        
        Formula: H = -Σ(p(x) * log2(p(x)))
        Perfect randomness yields H = 1.0 for binary data.
        """
        n = len(bit_string)
        
        # Calculate probabilities
        ones = bit_string.count('1')
        zeros = n - ones
        
        p1 = ones / n if ones > 0 else 0
        p0 = zeros / n if zeros > 0 else 0
        
        # Calculate entropy
        entropy = 0
        if p1 > 0:
            entropy -= p1 * math.log2(p1)
        if p0 > 0:
            entropy -= p0 * math.log2(p0)
        
        # Also calculate block entropy (2-bit patterns)
        if len(bit_string) >= 2:
            pairs = [bit_string[i:i+2] for i in range(0, len(bit_string)-1)]
            pair_counts = Counter(pairs)
            total_pairs = len(pairs)
            
            block_entropy = 0
            for count in pair_counts.values():
                p = count / total_pairs
                if p > 0:
                    block_entropy -= p * math.log2(p)
            block_entropy /= 2  # Normalize to per-bit entropy
        else:
            block_entropy = entropy
        
        # Perfect entropy is 1.0, we consider > 0.95 as excellent
        passed = entropy > 0.9
        
        return {
            'test_name': 'Shannon Entropy Test',
            'description': 'Measures information content per bit',
            'entropy': round(entropy, 6),
            'max_entropy': 1.0,
            'entropy_percentage': round(entropy * 100, 2),
            'block_entropy': round(block_entropy, 6),
            'passed': passed,
            'quality': 'Excellent' if entropy > 0.99 else 'Good' if entropy > 0.95 else 'Acceptable' if passed else 'Poor',
            'interpretation': f"Each bit carries {round(entropy * 100, 1)}% of maximum possible information"
        }
    
    def serial_test(self, bit_string: str) -> Dict:
        """
        Serial Test - Check 2-bit pattern distribution.
        
        For random data, patterns 00, 01, 10, 11 should each appear ~25%.
        """
        n = len(bit_string)
        if n < 4:
            return {
                'test_name': 'Serial Test',
                'passed': False,
                'error': 'Need at least 4 bits for serial test'
            }
        
        # Count 2-bit patterns
        patterns = {'00': 0, '01': 0, '10': 0, '11': 0}
        for i in range(n - 1):
            pattern = bit_string[i:i+2]
            patterns[pattern] += 1
        
        total_patterns = n - 1
        expected = total_patterns / 4
        
        # Calculate chi-square
        chi_square = sum((count - expected) ** 2 / expected for count in patterns.values())
        
        # Proportions
        proportions = {k: round(v / total_patterns * 100, 2) for k, v in patterns.items()}
        
        # Chi-square with 3 df: threshold 7.81 for p > 0.05
        passed = chi_square < 7.81
        
        # Calculate max deviation from 25%
        max_deviation = max(abs(p - 25) for p in proportions.values())
        
        return {
            'test_name': 'Serial (2-bit Pattern) Test',
            'description': 'Checks if 2-bit patterns (00, 01, 10, 11) appear equally',
            'pattern_counts': patterns,
            'pattern_proportions': proportions,
            'expected_proportion': 25.0,
            'max_deviation': round(max_deviation, 2),
            'chi_square': round(chi_square, 4),
            'threshold': 7.81,
            'passed': passed,
            'quality': 'Excellent' if max_deviation < 3 else 'Good' if max_deviation < 5 else 'Acceptable' if passed else 'Poor'
        }
    
    def longest_run_test(self, bit_string: str) -> Dict:
        """
        Longest Run Test - Check for unusually long runs of the same bit.
        
        Very long runs suggest non-randomness.
        """
        n = len(bit_string)
        
        # Find longest runs of 1s and 0s
        max_run_ones = 0
        max_run_zeros = 0
        current_run = 1
        
        for i in range(1, n):
            if bit_string[i] == bit_string[i-1]:
                current_run += 1
            else:
                if bit_string[i-1] == '1':
                    max_run_ones = max(max_run_ones, current_run)
                else:
                    max_run_zeros = max(max_run_zeros, current_run)
                current_run = 1
        
        # Don't forget the last run
        if bit_string[-1] == '1':
            max_run_ones = max(max_run_ones, current_run)
        else:
            max_run_zeros = max(max_run_zeros, current_run)
        
        # Expected longest run is approximately log2(n)
        expected_max_run = math.log2(n) if n > 0 else 0
        
        max_run = max(max_run_ones, max_run_zeros)
        
        # Allow up to 2x expected for randomness
        threshold = max(expected_max_run * 2.5, 10)
        passed = max_run <= threshold
        
        return {
            'test_name': 'Longest Run Test',
            'description': 'Checks for unusually long sequences of consecutive identical bits',
            'longest_run_ones': max_run_ones,
            'longest_run_zeros': max_run_zeros,
            'longest_run_overall': max_run,
            'expected_max_run': round(expected_max_run, 2),
            'threshold': round(threshold, 2),
            'passed': passed,
            'quality': 'Excellent' if max_run <= expected_max_run * 1.5 else 'Good' if max_run <= expected_max_run * 2 else 'Acceptable' if passed else 'Poor'
        }
    
    def autocorrelation_test(self, bit_string: str, lag: int = 1) -> Dict:
        """
        Autocorrelation Test - Check for correlation between bits at different positions.
        
        For random data, there should be no significant correlation.
        """
        n = len(bit_string)
        if n < lag + 10:
            return {
                'test_name': 'Autocorrelation Test',
                'passed': False,
                'error': f'Need at least {lag + 10} bits for autocorrelation test'
            }
        
        # Convert to numeric
        bits = [int(b) for b in bit_string]
        
        # Calculate autocorrelation
        mean = sum(bits) / n
        
        # Variance
        variance = sum((b - mean) ** 2 for b in bits) / n
        
        if variance == 0:
            return {
                'test_name': 'Autocorrelation Test',
                'passed': False,
                'error': 'Zero variance in bit string'
            }
        
        # Autocorrelation at specified lag
        autocorr_sum = sum((bits[i] - mean) * (bits[i + lag] - mean) for i in range(n - lag))
        autocorrelation = autocorr_sum / ((n - lag) * variance)
        
        # For random data, autocorrelation should be close to 0
        # Expected standard error is approximately 1/sqrt(n)
        std_error = 1 / math.sqrt(n)
        z_score = autocorrelation / std_error if std_error > 0 else 0
        
        passed = abs(z_score) < 1.96
        
        return {
            'test_name': f'Autocorrelation Test (lag={lag})',
            'description': 'Checks for correlation between bits at different positions',
            'autocorrelation': round(autocorrelation, 6),
            'z_score': round(z_score, 4),
            'threshold': 1.96,
            'lag': lag,
            'passed': passed,
            'quality': 'Excellent' if abs(z_score) < 1.0 else 'Good' if abs(z_score) < 1.5 else 'Acceptable' if passed else 'Poor'
        }
    
    def compare_with_classical(self, length: int) -> Dict:
        """
        Generate a classical PRNG bit string and compare analysis.
        
        Args:
            length: Number of bits to generate
            
        Returns:
            dict: Classical bit string and its analysis
        """
        # Generate using Python's random module (Mersenne Twister PRNG)
        classical_bits = ''.join(str(random.randint(0, 1)) for _ in range(length))
        
        analysis = self.analyze_randomness(classical_bits)
        analysis['generator'] = 'Python random.Random() (Mersenne Twister PRNG)'
        analysis['bit_string'] = classical_bits[:100] + '...' if length > 100 else classical_bits
        
        return analysis


# Example usage for testing
if __name__ == "__main__":
    analyzer = EntropyAnalyzer()
    
    # Test with a sample quantum-like bit string
    test_bits = '10110010110100110101010011010110101001101001011010100110100101011010011010'
    
    print("=== Entropy Analysis Test ===")
    results = analyzer.analyze_randomness(test_bits)
    
    print(f"\nBit string length: {results['bit_string_length']}")
    print(f"Overall Score: {results['overall_score']}%")
    print(f"Verdict: {results['verdict']}")
    
    print("\n=== Individual Tests ===")
    for test_name, test_result in results['tests'].items():
        status = "✓ PASS" if test_result.get('passed', False) else "✗ FAIL"
        print(f"{status} - {test_result.get('test_name', test_name)}")
