"""Bootstrap script to generate enough data and train the ML model."""

from ml_data_collector import MLDataPreprocessor
from ml_model_trainer import QuantumKeyQualityClassifier


def bootstrap_model(target_samples=1000):
    """Generate synthetic data if needed, then train and persist model."""
    preprocessor = MLDataPreprocessor()
    df, _ = preprocessor.load_data()
    current_samples = len(df) if df is not None else 0

    if current_samples < target_samples:
        needed = target_samples - current_samples
        print(f"[Bootstrap] Generating {needed} synthetic samples...")
        ok = preprocessor.generate_synthetic_data(num_samples=needed)
        if not ok:
            raise RuntimeError("Synthetic data generation failed")

    classifier = QuantumKeyQualityClassifier()
    X, y, prepared_df = classifier.prepare_data()
    print(f"[Bootstrap] Training with {len(prepared_df)} samples")

    metrics = classifier.train(X, y)
    metadata = classifier.save_model()

    print("[Bootstrap] Training complete")
    print(f"[Bootstrap] Accuracy: {metrics.get('accuracy', 0.0):.4f}")
    print(f"[Bootstrap] Recall (bad class): {metrics.get('recall_bad', 0.0):.4f}")
    print(f"[Bootstrap] Precision (bad class): {metrics.get('precision_bad', 0.0):.4f}")
    print(f"[Bootstrap] Cross-val mean: {metrics.get('cross_val_mean', 0.0):.4f}")
    print(f"[Bootstrap] Model size (MB): {metadata.get('model_size_mb', 0.0):.4f}")

    return {
        "metrics": metrics,
        "metadata": metadata,
        "samples_used": len(prepared_df),
    }


if __name__ == "__main__":
    bootstrap_model()
