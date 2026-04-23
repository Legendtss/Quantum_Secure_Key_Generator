"""Train and serve a lightweight ML classifier for quantum key quality."""

import json
import os
import time
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler


class QuantumKeyQualityClassifier:
    """Train ML model to classify quantum key quality."""

    def __init__(self, model_dir="backend/models"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.isabs(model_dir):
            resolved_model_dir = model_dir
        elif model_dir.startswith("backend/"):
            resolved_model_dir = os.path.join(base_dir, model_dir.split("backend/", 1)[1])
        else:
            resolved_model_dir = os.path.join(base_dir, model_dir)

        self.model_dir = resolved_model_dir
        self.model_path = os.path.join(model_dir, "quantum_key_classifier.pkl")
        self.scaler_path = os.path.join(model_dir, "feature_scaler.pkl")
        self.metadata_path = os.path.join(model_dir, "model_metadata.json")

        self.model_path = os.path.join(self.model_dir, "quantum_key_classifier.pkl")
        self.scaler_path = os.path.join(self.model_dir, "feature_scaler.pkl")
        self.metadata_path = os.path.join(self.model_dir, "model_metadata.json")

        self.model = None
        self.scaler = None
        self.metadata = {}
        self.training_samples = 0
        self.latest_metrics = {}
        self.feature_names = [
            "generation_time_ms",
            "shots_used",
            "num_qubits",
            "bit_distribution",
        ]
        self.threshold = 0.98

        self._ensure_model_dir()

    def _ensure_model_dir(self):
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir, exist_ok=True)

    def _resolve_path(self, csv_path):
        if os.path.exists(csv_path):
            return csv_path

        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(base_dir, "data", "training_data.csv"),
            os.path.join(base_dir, "backend", "data", "training_data.csv"),
            os.path.join(os.path.dirname(base_dir), "backend", "data", "training_data.csv"),
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate

        raise FileNotFoundError(f"Training data CSV not found. Checked: {csv_path}, {candidates}")

    def prepare_data(self, csv_path="backend/data/training_data.csv"):
        """Load, clean, and prepare training data."""
        resolved_path = self._resolve_path(csv_path)
        df = pd.read_csv(resolved_path)

        if "source" in df.columns:
            # Keep both real and synthetic quantum samples for bootstrap training.
            df = df[df["source"].astype(str).str.contains("quantum", case=False, na=False)]

        required_columns = self.feature_names + ["entropy_score", "shannon_entropy"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        df = df.dropna(subset=required_columns).copy()
        if df.empty:
            raise ValueError("No usable rows after cleaning")

        # Clip extreme generation latency outliers to improve model stability.
        p95 = float(df["generation_time_ms"].quantile(0.95))
        p01 = float(df["generation_time_ms"].quantile(0.01))
        df["generation_time_ms"] = df["generation_time_ms"].clip(lower=p01, upper=p95)

        # Label definition: strong entropy and Shannon entropy both required for "good".
        y = ((df["entropy_score"] >= 0.98) & (df["shannon_entropy"] >= 0.99)).astype(int)
        X = df[self.feature_names].copy()

        class_counts = y.value_counts().to_dict()
        if len(class_counts) < 2:
            print("[ML] Warning: only one class in training data; model quality may be poor.")

        self.training_samples = len(df)
        return X, y, df

    def train(self, X, y, test_size=0.2, random_state=42):
        """Train RandomForest model and return metrics."""
        if len(X) < 20:
            raise ValueError("Not enough samples for training")

        stratify_target = y if len(np.unique(y)) > 1 else None
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state,
            stratify=stratify_target,
        )

        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        self.model = RandomForestClassifier(
            n_estimators=50,
            max_depth=10,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        )
        self.model.fit(X_train_scaled, y_train)

        metrics = self.evaluate(X_test_scaled, y_test)

        # Cross-validation fallback for highly imbalanced/small class counts.
        try:
            min_class_count = int(np.min(np.bincount(np.asarray(y, dtype=int)))) if len(np.unique(y)) > 1 else 1
            cv_folds = max(2, min(5, min_class_count))
            if len(np.unique(y)) > 1 and cv_folds >= 2:
                X_all_scaled = self.scaler.transform(X)
                cv_scores = cross_val_score(self.model, X_all_scaled, y, cv=cv_folds, scoring="accuracy")
                metrics["cross_val_mean"] = float(np.mean(cv_scores))
                metrics["cross_val_std"] = float(np.std(cv_scores))
                metrics["cross_val_folds"] = int(cv_folds)
            else:
                metrics["cross_val_mean"] = 0.0
                metrics["cross_val_std"] = 0.0
                metrics["cross_val_folds"] = 0
        except Exception as exc:
            metrics["cross_val_mean"] = 0.0
            metrics["cross_val_std"] = 0.0
            metrics["cross_val_folds"] = 0
            metrics["cross_val_error"] = str(exc)

        self.latest_metrics = metrics
        return metrics

    def evaluate(self, X_test, y_test):
        """Evaluate trained model and return detailed metrics."""
        if self.model is None:
            raise RuntimeError("Model is not trained")

        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1] if hasattr(self.model, "predict_proba") else None

        accuracy = accuracy_score(y_test, y_pred)
        precision_by_class, recall_by_class, f1_by_class, _ = precision_recall_fscore_support(
            y_test,
            y_pred,
            labels=[0, 1],
            zero_division=0,
        )

        metrics = {
            "accuracy": float(accuracy),
            "precision_bad": float(precision_by_class[0]),
            "recall_bad": float(recall_by_class[0]),
            "f1_bad": float(f1_by_class[0]),
            "f1_weighted": float(f1_score(y_test, y_pred, average="weighted", zero_division=0)),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "classification_report": classification_report(y_test, y_pred, zero_division=0, output_dict=True),
            "feature_importance": {
                name: float(importance)
                for name, importance in zip(self.feature_names, self.model.feature_importances_)
            },
        }

        if y_proba is not None and len(np.unique(y_test)) > 1:
            metrics["roc_auc"] = float(roc_auc_score(y_test, y_proba))
        else:
            metrics["roc_auc"] = 0.0

        metrics["meets_targets"] = {
            "accuracy_ge_85": metrics["accuracy"] >= 0.85,
            "recall_bad_ge_75": metrics["recall_bad"] >= 0.75,
            "precision_bad_ge_70": metrics["precision_bad"] >= 0.70,
        }

        return metrics

    def predict_quality(self, generation_time_ms, shots_used, num_qubits, bit_distribution):
        """Predict if a generated key is good or noisy."""
        if self.model is None or self.scaler is None:
            return {
                "prediction": None,
                "confidence": 0.0,
                "model_version": "unavailable",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "error": "Model not loaded",
            }

        try:
            features = np.array(
                [[
                    float(generation_time_ms),
                    float(shots_used),
                    float(num_qubits),
                    float(bit_distribution),
                ]]
            )
        except (TypeError, ValueError) as exc:
            return {
                "prediction": None,
                "confidence": 0.0,
                "model_version": self.metadata.get("model_version", "v1"),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "error": f"Invalid feature input: {exc}",
            }

        feature_df = pd.DataFrame(features, columns=self.feature_names)
        scaled = self.scaler.transform(feature_df)
        predicted_class = int(self.model.predict(scaled)[0])

        confidence = 0.5
        if hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba(scaled)[0]
            confidence = float(np.max(probabilities))

        return {
            "prediction": "good" if predicted_class == 1 else "bad",
            "confidence": round(confidence, 4),
            "model_version": self.metadata.get("model_version", "v1"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def save_model(self):
        """Save model, scaler, and metadata to disk."""
        if self.model is None or self.scaler is None:
            raise RuntimeError("Cannot save before training")

        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)

        model_size_mb = os.path.getsize(self.model_path) / (1024 * 1024)
        scaler_size_mb = os.path.getsize(self.scaler_path) / (1024 * 1024)

        metadata = {
            "training_date": datetime.now(timezone.utc).isoformat(),
            "training_samples": int(self.training_samples),
            "accuracy": float(self.latest_metrics.get("accuracy", 0.0)),
            "precision_bad": float(self.latest_metrics.get("precision_bad", 0.0)),
            "recall_bad": float(self.latest_metrics.get("recall_bad", 0.0)),
            "f1_bad": float(self.latest_metrics.get("f1_bad", 0.0)),
            "roc_auc": float(self.latest_metrics.get("roc_auc", 0.0)),
            "cross_val_mean": float(self.latest_metrics.get("cross_val_mean", 0.0)),
            "cross_val_std": float(self.latest_metrics.get("cross_val_std", 0.0)),
            "model_size_mb": round(model_size_mb, 4),
            "scaler_size_mb": round(scaler_size_mb, 4),
            "feature_names": self.feature_names,
            "feature_importance": self.latest_metrics.get("feature_importance", {}),
            "threshold": self.threshold,
            "model_version": "v1",
        }

        with open(self.metadata_path, "w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2)

        self.metadata = metadata

        if model_size_mb > 5.0:
            print(f"[ML] Warning: model size {model_size_mb:.2f}MB exceeds 5MB target")

        # Quick sanity check that artifacts are loadable.
        _ = joblib.load(self.model_path)
        _ = joblib.load(self.scaler_path)

        return metadata

    def load_model(self):
        """Load model from disk. Returns True on success."""
        try:
            if not (os.path.exists(self.model_path) and os.path.exists(self.scaler_path)):
                return False

            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)

            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, "r", encoding="utf-8") as handle:
                    self.metadata = json.load(handle)
            else:
                self.metadata = {
                    "model_version": "v1",
                    "training_date": None,
                    "training_samples": 0,
                    "accuracy": 0.0,
                }

            return True
        except Exception as exc:
            print(f"[ML] Failed to load model: {exc}")
            self.model = None
            self.scaler = None
            self.metadata = {}
            return False

    def get_metadata(self):
        """Return model metadata plus live latency estimate."""
        metadata = dict(self.metadata) if self.metadata else {
            "model_loaded": self.model is not None and self.scaler is not None,
            "model_version": "v1",
        }

        metadata["model_loaded"] = self.model is not None and self.scaler is not None

        if metadata["model_loaded"]:
            # Measure average prediction latency using representative inputs.
            sample_features = pd.DataFrame(
                [[300.0, 256.0, 16.0, 0.5]],
                columns=self.feature_names,
            )
            scaled = self.scaler.transform(sample_features)
            start = time.perf_counter()
            for _ in range(100):
                _ = self.model.predict(scaled)
            elapsed_ms = (time.perf_counter() - start) * 1000.0 / 100.0
            metadata["prediction_latency_ms"] = round(elapsed_ms, 4)
        else:
            metadata["prediction_latency_ms"] = None

        return metadata
