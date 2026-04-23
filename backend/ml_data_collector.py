"""
ML Data Preprocessor - Prepare logged data for ML training
Handles data cleaning, validation, normalization, and feature engineering
"""

import pandas as pd
import numpy as np
import os
from ml_data_logger import QuantumDataLogger

class MLDataPreprocessor:
    """
    Prepare logged data for ML training.
    Handles cleaning, normalization, and feature engineering.
    """
    
    def __init__(self):
        self.logger = QuantumDataLogger()
        self.df = None
        self.feature_names = ['generation_time_ms', 'shots_used', 'num_qubits', 'bit_distribution']
    
    def load_data(self):
        """
        Load training_data.csv into pandas DataFrame with preprocessing.
        
        Returns:
            (DataFrame, dict) - processed data and quality report
        """
        try:
            csv_path = os.path.join('backend/data', 'training_data.csv')
            
            if not os.path.exists(csv_path):
                return None, {'error': 'No training data found', 'samples': 0}
            
            df = pd.read_csv(csv_path)
            
            if len(df) == 0:
                return None, {'error': 'Training data is empty', 'samples': 0}
            
            original_size = len(df)
            
            # Remove rows with NaN in critical columns
            critical_cols = ['entropy_score', 'shannon_entropy', 'bit_distribution']
            df = df.dropna(subset=critical_cols)
            
            # Filter out obviously bad data (entropy < 0.5 indicates error)
            df = df[df['entropy_score'] >= 0.5]
            
            # Remove duplicates based on bits (unlikely but possible)
            df = df.drop_duplicates(subset=['bits_length', 'entropy_score'], keep='first')
            
            self.df = df.reset_index(drop=True)
            
            # Generate quality report
            quality_report = {
                'original_samples': original_size,
                'cleaned_samples': len(self.df),
                'removed_rows': original_size - len(self.df),
                'has_quantum': (self.df['source'] == 'quantum').sum() if 'source' in self.df.columns else 0,
                'has_classical': (self.df['source'] == 'classical').sum() if 'source' in self.df.columns else 0,
                'avg_entropy': round(self.df['entropy_score'].mean(), 4),
                'entropy_std': round(self.df['entropy_score'].std(), 4),
                'ready_for_training': len(self.df) >= 500
            }
            
            return self.df, quality_report
        
        except Exception as e:
            return None, {'error': str(e), 'samples': 0}
    
    def get_features_and_labels(self, threshold=0.98):
        """
        Convert raw data to ML-ready format for classification.
        
        Binary classification:
        - "Good" (1): entropy_score >= threshold
        - "Bad" (0): entropy_score < threshold
        
        Args:
            threshold: Entropy threshold for "good" classification
        
        Returns:
            (X, y, feature_names) or (None, None, None) if insufficient data
        """
        try:
            if self.df is None or len(self.df) < 50:
                return None, None, None
            
            df = self.df.copy()
            
            # Create binary labels
            y = (df['entropy_score'] >= threshold).astype(int)
            
            # Select features
            X = df[self.feature_names].copy()
            
            # Handle any missing values in features
            X = X.fillna(X.mean())
            
            # Normalize features to 0-1 range
            X_normalized = (X - X.min()) / (X.max() - X.min() + 1e-8)
            
            return X_normalized.values, y.values, self.feature_names
        
        except Exception as e:
            print(f"Error in get_features_and_labels: {e}")
            return None, None, None
    
    def validate_data_quality(self):
        """
        Check if dataset is suitable for ML training.
        
        Returns:
            dict with validation results
        """
        try:
            if self.df is None:
                self.load_data()
            
            if self.df is None or len(self.df) == 0:
                return {
                    'is_valid': False,
                    'num_samples': 0,
                    'min_for_training': 500,
                    'quality_score': 0,
                    'issues': ['No data available']
                }
            
            issues = []
            
            # Check minimum sample count
            num_samples = len(self.df)
            if num_samples < 500:
                issues.append(f'Insufficient samples: {num_samples}/500')
            
            # Check class balance
            if 'entropy_score' in self.df.columns:
                good_samples = (self.df['entropy_score'] >= 0.98).sum()
                bad_samples = len(self.df) - good_samples
                
                if good_samples == 0 or bad_samples == 0:
                    issues.append('No class balance: all samples same quality')
                
                balance_ratio = min(good_samples, bad_samples) / max(good_samples, bad_samples) if max(good_samples, bad_samples) > 0 else 0
                if balance_ratio < 0.2:
                    issues.append(f'Poor class balance ratio: {balance_ratio:.2f}')
            
            # Check feature variance
            for feat in self.feature_names:
                if feat in self.df.columns:
                    variance = self.df[feat].var()
                    if variance < 1e-8:
                        issues.append(f'No variance in feature: {feat}')
            
            # Check for missing values
            missing = self.df[self.feature_names].isnull().sum().sum()
            if missing > 0:
                issues.append(f'Missing values found: {missing}')
            
            # Calculate quality score (0-100)
            quality_score = 100
            quality_score -= max(0, (500 - num_samples) / 5)  # Penalize low samples
            quality_score -= len(issues) * 10  # Penalize issues
            quality_score = max(0, min(100, quality_score))
            
            return {
                'is_valid': len(issues) == 0 and num_samples >= 500,
                'num_samples': num_samples,
                'min_for_training': 500,
                'quality_score': round(quality_score, 1),
                'issues': issues
            }
        
        except Exception as e:
            return {
                'is_valid': False,
                'error': str(e),
                'quality_score': 0
            }
    
    def generate_synthetic_data(self, num_samples=500):
        """
        Generate synthetic training data to bootstrap ML model.
        Creates realistic quantum generation patterns.
        
        Args:
            num_samples: Number of synthetic samples to generate
        
        Returns:
            bool: Success of generation
        """
        try:
            import random
            from datetime import datetime, timedelta
            
            csv_path = os.path.join('backend/data', 'training_data.csv')
            
            synthetic_data = []
            base_time = datetime.utcnow()
            
            for i in range(num_samples):
                # Create realistic parameters
                shots = random.choice([256, 512, 1024])
                num_qubits = random.randint(8, 32)
                
                # Simulate generation time (faster with more qubits, more shots)
                generation_time = random.uniform(50, 2000)
                generation_time *= (num_qubits / 20)  # Scale with qubits
                generation_time *= (shots / 512)  # Scale with shots
                
                # Simulate entropy (usually good, sometimes bad)
                if random.random() < 0.8:
                    # 80% chance of good entropy
                    entropy = random.uniform(0.95, 0.998)
                else:
                    # 20% chance of poor entropy
                    entropy = random.uniform(0.50, 0.94)
                
                shannon_entropy = entropy * random.uniform(0.98, 1.0)
                min_entropy = entropy * random.uniform(0.85, 0.99)
                bit_distribution = random.uniform(0.45, 0.55)  # ~50% 1s, 50% 0s
                
                timestamp = base_time + timedelta(seconds=i * random.uniform(0.5, 2))
                
                synthetic_data.append({
                    'timestamp': timestamp.isoformat() + 'Z',
                    'source': 'synthetic_quantum',
                    'bits_length': num_qubits * random.randint(16, 64),
                    'entropy_score': round(entropy, 4),
                    'shannon_entropy': round(shannon_entropy, 4),
                    'min_entropy': round(min_entropy, 4),
                    'bit_distribution': round(bit_distribution, 4),
                    'generation_time_ms': round(generation_time, 2),
                    'shots_used': shots,
                    'num_qubits': num_qubits
                })
            
            # Write to CSV
            if os.path.exists(csv_path):
                # Append to existing
                df_existing = pd.read_csv(csv_path)
                df_synthetic = pd.DataFrame(synthetic_data)
                df_combined = pd.concat([df_existing, df_synthetic], ignore_index=True)
            else:
                df_combined = pd.DataFrame(synthetic_data)
            
            df_combined.to_csv(csv_path, index=False, encoding='utf-8-sig')
            return True
        
        except Exception as e:
            print(f"Error generating synthetic data: {e}")
            return False
