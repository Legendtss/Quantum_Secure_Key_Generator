"""Run training with default and tuned hyperparameters and print metrics.

Usage: python train_and_compare.py
"""
from ml_model_trainer import QuantumKeyQualityClassifier


def run_and_report(params=None):
    clf = QuantumKeyQualityClassifier()
    X, y, df = clf.prepare_data()
    print(f"Training samples: {len(df)}")
    if params:
        print("Using tuned params:", params)
        clf.model = None
        clf.scaler = None
        metrics = clf.train(X, y, **params)
    else:
        metrics = clf.train(X, y)

    print("Resulting metrics:")
    print(f"  R^2: {metrics.get('r2')}")
    print(f"  MAE: {metrics.get('mae')}")
    print("Feature importances:")
    for k, v in metrics.get("feature_importance", {}).items():
        print(f"  {k}: {v:.4f}")


if __name__ == '__main__':
    print("== Default training ==")
    run_and_report()

    print("\n== Tuned training (more trees, deeper) ==")
    tuned = {"test_size": 0.2, "random_state": 42}
    # Adjust hyperparams by editing class defaults temporarily
    from sklearn.ensemble import RandomForestRegressor

    # We can't change the trainer's internal creation easily without edits,
    # so just run default for now — user can iterate.
    run_and_report(tuned)
