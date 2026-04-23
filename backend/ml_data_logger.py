"""
ML Data Logger - Collects quantum generation metrics for ML training
Intercepts each key generation to capture data without breaking existing functionality
"""

import json
import csv
import os
from datetime import datetime
import threading

class QuantumDataLogger:
    """
    Log quantum generation metrics for ML training.
    Thread-safe logging to support concurrent requests.
    """
    
    def __init__(self, log_dir='backend/data'):
        self.log_dir = log_dir
        self.csv_path = os.path.join(log_dir, 'training_data.csv')
        self.json_path = os.path.join(log_dir, 'generation_logs.json')
        self.lock = threading.Lock()
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Create data directory and files if they don't exist"""
        try:
            # Create directory if not exists
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)
            
            # Create CSV with headers if not exists
            if not os.path.exists(self.csv_path):
                with open(self.csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'timestamp', 'source', 'bits_length', 'entropy_score', 
                        'shannon_entropy', 'min_entropy', 'bit_distribution',
                        'generation_time_ms', 'shots_used', 'num_qubits'
                    ])
        except Exception as e:
            print(f"Warning: Could not create logging files: {e}")
    
    def log_generation(self, generation_result, entropy_result, source='quantum'):
        """
        Log a single key generation with entropy metrics.
        
        Args:
            generation_result: Dict from quantum_generator.generate_secure_key()
            entropy_result: Dict from entropy_analyzer.analyze_randomness()
            source: 'quantum' or 'classical'
        
        Returns:
            bool: Success of logging operation (non-blocking)
        """
        try:
            # Use thread lock for safe concurrent writes
            with self.lock:
                # Extract bits - try binary first, then hex
                bits_str = generation_result.get('binary') or generation_result.get('bits', '')
                if not bits_str:
                    return False
                
                bits_length = len(bits_str)
                
                # Extract entropy metrics
                entropy_score = entropy_result.get('entropy_score', 0)
                shannon_entropy = entropy_result.get('shannon_entropy', 0)
                min_entropy = entropy_result.get('min_entropy', 0)
                
                # Calculate bit distribution (ratio of 1s)
                ones_count = bits_str.count('1')
                bit_distribution = ones_count / bits_length if bits_length > 0 else 0.5
                
                # Get generation metrics
                generation_time_ms = generation_result.get('generation_time_ms', 0)
                shots_used = generation_result.get('shots_used', 0)
                num_qubits = generation_result.get('length', bits_length // 8)
                
                # Create record
                record = {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'source': source,
                    'bits_length': bits_length,
                    'entropy_score': round(entropy_score, 4),
                    'shannon_entropy': round(shannon_entropy, 4),
                    'min_entropy': round(min_entropy, 4),
                    'bit_distribution': round(bit_distribution, 4),
                    'generation_time_ms': round(generation_time_ms, 2),
                    'shots_used': shots_used,
                    'num_qubits': num_qubits
                }
                
                # Append to CSV
                with open(self.csv_path, 'a', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=record.keys())
                    writer.writerow(record)
                
                # Also keep JSON backup (last 1000 entries)
                self._append_json_log(record)
                
                return True
        
        except Exception as e:
            # Log failures silently - don't break key generation
            print(f"[ML Logger] Non-blocking error: {e}")
            return False
    
    def _append_json_log(self, record):
        """Append to JSON log, keeping only last 1000 entries"""
        try:
            logs = []
            if os.path.exists(self.json_path):
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    try:
                        logs = json.load(f)
                    except:
                        logs = []
            
            logs.append(record)
            logs = logs[-1000:]  # Keep only last 1000
            
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            print(f"[ML Logger] JSON backup failed (non-blocking): {e}")
    
    def get_dataset_stats(self):
        """
        Return statistics about collected data.
        
        Returns:
            dict with stats or empty dict if no data
        """
        try:
            if not os.path.exists(self.csv_path):
                return {
                    'total_samples': 0,
                    'avg_entropy': 0,
                    'min_entropy': 0,
                    'max_entropy': 0,
                    'avg_generation_time': 0,
                    'samples_by_source': {},
                    'ready_for_training': False
                }
            
            import pandas as pd
            
            df = pd.read_csv(self.csv_path)
            
            if len(df) == 0:
                return {
                    'total_samples': 0,
                    'avg_entropy': 0,
                    'min_entropy': 0,
                    'max_entropy': 0,
                    'avg_generation_time': 0,
                    'samples_by_source': {},
                    'ready_for_training': False
                }
            
            stats = {
                'total_samples': len(df),
                'avg_entropy': round(df['entropy_score'].mean(), 4),
                'min_entropy': round(df['entropy_score'].min(), 4),
                'max_entropy': round(df['entropy_score'].max(), 4),
                'avg_generation_time': round(df['generation_time_ms'].mean(), 2),
                'samples_by_source': df['source'].value_counts().to_dict() if 'source' in df.columns else {},
                'ready_for_training': len(df) >= 500
            }
            
            return stats
        
        except Exception as e:
            print(f"[ML Logger] Stats calculation failed: {e}")
            return {'error': str(e)}
    
    def export_dataset(self, output_path=None):
        """Export training dataset for ML model training"""
        try:
            if output_path is None:
                output_path = os.path.join(self.log_dir, 'exported_data.csv')
            
            if os.path.exists(self.csv_path):
                import shutil
                shutil.copy(self.csv_path, output_path)
                return {'success': True, 'path': output_path}
            else:
                return {'success': False, 'error': 'No data to export'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
