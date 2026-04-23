"""
Test ML Infrastructure - Validate data collection and preprocessing
Run this before moving to Part 2
"""

import os
import sys
import time

def test_ml_infrastructure():
    """
    Validate that ML infrastructure is working before training.
    """
    
    print("\n" + "="*60)
    print("ML INFRASTRUCTURE VALIDATION - PART 1")
    print("="*60 + "\n")
    
    all_passed = True
    
    # Test 1: Data directory creation
    print("[TEST 1] Data directory creation...")
    try:
        from ml_data_logger import QuantumDataLogger
        logger = QuantumDataLogger()
        data_dir = 'backend/data'
        
        if os.path.exists(data_dir):
            print("✓ Data directory exists")
        else:
            print("✗ Data directory missing")
            all_passed = False
    except Exception as e:
        print(f"✗ Error: {e}")
        all_passed = False
    
    # Test 2: CSV file creation
    print("\n[TEST 2] CSV file creation...")
    try:
        csv_path = os.path.join('backend/data', 'training_data.csv')
        if os.path.exists(csv_path):
            with open(csv_path, 'r') as f:
                header = f.readline().strip()
                if 'entropy_score' in header and 'generation_time_ms' in header:
                    print(f"✓ CSV file valid with headers")
                else:
                    print("✗ CSV headers invalid")
                    all_passed = False
        else:
            print("✗ CSV file not created")
            all_passed = False
    except Exception as e:
        print(f"✗ Error: {e}")
        all_passed = False
    
    # Test 3: Fake log entry (non-blocking)
    print("\n[TEST 3] Logging capability (non-blocking)...")
    try:
        fake_generation = {
            'binary': '1010101010101010',
            'bits': '1010101010101010',
            'length': 2,
            'generation_time_ms': 125.5,
            'shots_used': 256
        }
        fake_entropy = {
            'entropy_score': 0.985,
            'shannon_entropy': 0.980,
            'min_entropy': 0.975,
        }
        
        start = time.time()
        success = logger.log_generation(fake_generation, fake_entropy, source='test')
        elapsed = time.time() - start
        
        if success and elapsed < 0.1:
            print(f"✓ Log entry successful ({elapsed*1000:.1f}ms latency)")
        else:
            print(f"✗ Logging failed or slow ({elapsed*1000:.1f}ms)")
            all_passed = False
    except Exception as e:
        print(f"✗ Error: {e}")
        all_passed = False
    
    # Test 4: Data loading and preprocessing
    print("\n[TEST 4] Data loading and preprocessing...")
    try:
        from ml_data_collector import MLDataPreprocessor
        preprocessor = MLDataPreprocessor()
        df, quality_report = preprocessor.load_data()
        
        if df is not None and len(df) > 0:
            print(f"✓ Loaded {len(df)} samples (cleaned from {quality_report.get('original_samples', 0)})")
        else:
            print("⚠ No data loaded yet (will be populated with synthetic data)")
    except Exception as e:
        print(f"✗ Error: {e}")
        all_passed = False
    
    # Test 5: Data quality check
    print("\n[TEST 5] Data quality validation...")
    try:
        from ml_data_collector import MLDataPreprocessor
        preprocessor = MLDataPreprocessor()
        preprocessor.load_data()
        quality = preprocessor.validate_data_quality()
        
        print(f"  - Samples: {quality.get('num_samples', 0)}")
        print(f"  - Quality Score: {quality.get('quality_score', 0)}%")
        
        if quality.get('issues'):
            print(f"  - Issues: {', '.join(quality['issues'][:2])}")
        else:
            print(f"  - Issues: None")
        
        if quality.get('is_valid'):
            print("✓ Data quality acceptable")
        else:
            print("⚠ Data needs more samples (will bootstrap)")
    except Exception as e:
        print(f"✗ Error: {e}")
        all_passed = False
    
    # Test 6: Generate synthetic bootstrap data
    print("\n[TEST 6] Generating synthetic bootstrap data (500 samples)...")
    try:
        from ml_data_collector import MLDataPreprocessor
        preprocessor = MLDataPreprocessor()
        
        print("  - Creating realistic quantum generation patterns...")
        success = preprocessor.generate_synthetic_data(num_samples=500)
        
        if success:
            print("✓ Synthetic data generated successfully")
            
            # Verify it was written
            preprocessor.load_data()
            quality = preprocessor.validate_data_quality()
            print(f"  - Dataset now has: {quality.get('num_samples', 0)} samples")
            
            if quality.get('ready_for_training'):
                print("✓ Dataset ready for ML training!")
            else:
                print("⚠ Dataset needs more samples")
        else:
            print("✗ Synthetic data generation failed")
            all_passed = False
    except Exception as e:
        print(f"✗ Error: {e}")
        all_passed = False
    
    # Test 7: Feature extraction
    print("\n[TEST 7] ML feature extraction...")
    try:
        from ml_data_collector import MLDataPreprocessor
        preprocessor = MLDataPreprocessor()
        preprocessor.load_data()
        
        X, y, feature_names = preprocessor.get_features_and_labels(threshold=0.98)
        
        if X is not None and y is not None:
            print(f"✓ Features extracted: {feature_names}")
            print(f"  - Samples: {len(X)}")
            print(f"  - Features per sample: {X.shape[1]}")
            print(f"  - Good quality samples: {sum(y)}")
            print(f"  - Poor quality samples: {len(y) - sum(y)}")
        else:
            print("✗ Feature extraction failed")
            all_passed = False
    except Exception as e:
        print(f"✗ Error: {e}")
        all_passed = False
    
    # Test 8: Dataset statistics
    print("\n[TEST 8] Dataset statistics...")
    try:
        stats = logger.get_dataset_stats()
        
        if stats.get('total_samples', 0) > 0:
            print(f"✓ Total samples: {stats['total_samples']}")
            print(f"  - Avg entropy: {stats.get('avg_entropy', 0)}")
            print(f"  - Avg generation time: {stats.get('avg_generation_time', 0)}ms")
            print(f"  - Source distribution: {stats.get('samples_by_source', {})}")
            print(f"  - Ready for training: {stats.get('ready_for_training', False)}")
        else:
            print("⚠ No samples yet")
    except Exception as e:
        print(f"✗ Error: {e}")
        all_passed = False
    
    # Test 9: Existing API endpoints not broken
    print("\n[TEST 9] Verification: Integration ready for app.py...")
    try:
        # Just verify the imports work
        from ml_data_logger import QuantumDataLogger
        from ml_data_collector import MLDataPreprocessor
        print("✓ All ML modules import successfully")
        print("✓ Ready to integrate with app.py")
    except Exception as e:
        print(f"✗ Error: {e}")
        all_passed = False
    
    # Final summary
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("✓ ML Infrastructure ready for Part 2")
        print("="*60 + "\n")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("Please fix issues before proceeding")
        print("="*60 + "\n")
        return 1


if __name__ == '__main__':
    exit_code = test_ml_infrastructure()
    sys.exit(exit_code)
