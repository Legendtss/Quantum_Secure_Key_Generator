"""Train and serve an entropy-maximizing ML regressor for quantum key quality."""

import json
import os
import time
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler


class QuantumKeyQualityClassifier:
    """Backward-compatible class name for entropy-maximization ML model."""

    def __init__(self, model_dir="backend/models"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.isabs(model_dir):
            resolved_model_dir = model_dir
        elif model_dir.startswith("backend/"):
            resolved_model_dir = os.path.join(base_dir, model_dir.split("backend/", 1)[1])
        else:
            resolved_model_dir = os.path.join(base_dir, model_dir)

        self.model_dir = resolved_model_dir
        self.model_path = os.path.join(self.model_dir, "quantum_key_regressor.pkl")
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
            "entropy_score",
            "bit_bias",
            "latency_per_shot",
        ]
        self.objective = "entropy_maximization"
        self.tail_threshold = 0.95
        self.good_entropy_threshold = 0.98

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
        """Load and prepare training data for entropy regression."""
        resolved_path = self._resolve_path(csv_path)
        df = pd.read_csv(resolved_path)

        if "source" in df.columns:
            df = df[df["source"].astype(str).str.contains("quantum", case=False, na=False)]

        required_columns = [
            "generation_time_ms",
            "shots_used",
            "num_qubits",
            "bit_distribution",
            "entropy_score",
            "shannon_entropy",
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        df = df.dropna(subset=required_columns).copy()
        if df.empty:
            raise ValueError("No usable rows after cleaning")

        if "min_entropy" not in df.columns:
            df["min_entropy"] = df["shannon_entropy"]

        p95 = float(df["generation_time_ms"].quantile(0.95))
        p01 = float(df["generation_time_ms"].quantile(0.01))
        df["generation_time_ms"] = df["generation_time_ms"].clip(lower=p01, upper=p95)

        df["bit_bias"] = (df["bit_distribution"] - 0.5).abs()
        df["latency_per_shot"] = df["generation_time_ms"] / df["shots_used"].clip(lower=1.0)

        # Continuous optimization target: entropy-rich composite.
        target_entropy = (
            0.45 * df["entropy_score"]
            + 0.40 * df["shannon_entropy"]
            + 0.15 * df["min_entropy"]
        ).clip(lower=0.0, upper=1.0)

        X = df[self.feature_names].copy()
        y = target_entropy.astype(float)

        self.training_samples = len(df)
        return X, y, df

    def train(self, X, y, test_size=0.2, random_state=42):
        """Train entropy regressor and return regression-focused metrics."""
        if len(X) < 20:
            raise ValueError("Not enough samples for training")

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state,
        )

        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        self.model = RandomForestRegressor(
            n_estimators=120,
            max_depth=12,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=-1,
        )
        self.model.fit(X_train_scaled, y_train)

        metrics = self.evaluate(X_test_scaled, y_test)

        try:
            kf = KFold(n_splits=5, shuffle=True, random_state=random_state)
            X_all_scaled = self.scaler.transform(X)
            cv_mae = -cross_val_score(
                self.model,
                X_all_scaled,
                y,
                cv=kf,
                scoring="neg_mean_absolute_error",
            )
            cv_r2 = cross_val_score(self.model, X_all_scaled, y, cv=kf, scoring="r2")
            metrics["cv_mae_mean"] = float(np.mean(cv_mae))
            metrics["cv_mae_std"] = float(np.std(cv_mae))
            metrics["cv_r2_mean"] = float(np.mean(cv_r2))
            metrics["cv_r2_std"] = float(np.std(cv_r2))
            metrics["cv_folds"] = 5
        except Exception as exc:
            metrics["cv_mae_mean"] = 0.0
            metrics["cv_mae_std"] = 0.0
            metrics["cv_r2_mean"] = 0.0
            metrics["cv_r2_std"] = 0.0
            metrics["cv_folds"] = 0
            metrics["cv_error"] = str(exc)

        self.latest_metrics = metrics
        return metrics

    def evaluate(self, X_test, y_test):
        """Evaluate trained regressor."""
        if self.model is None:
            raise RuntimeError("Model is not trained")

        y_pred = np.clip(self.model.predict(X_test), 0.0, 1.0)
        y_true = np.asarray(y_test, dtype=float)

        mae = mean_absolute_error(y_true, y_pred)
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2 = r2_score(y_true, y_pred)
        pearson = float(np.corrcoef(y_true, y_pred)[0, 1]) if len(y_true) > 1 else 0.0
        # Spearman via rank correlation without scipy.
        spearman = float(pd.Series(y_true).rank().corr(pd.Series(y_pred).rank(), method="pearson"))
        errors = np.abs(y_true - y_pred)

        metrics = {
            "objective": self.objective,
            "mae": float(mae),
            "rmse": float(rmse),
            "r2": float(r2),
            "pearson_corr": float(pearson if np.isfinite(pearson) else 0.0),
            "spearman_corr": float(spearman if np.isfinite(spearman) else 0.0),
            "p95_abs_error": float(np.quantile(errors, 0.95)),
            "p99_abs_error": float(np.quantile(errors, 0.99)),
            "feature_importance": {
                name: float(importance)
                for name, importance in zip(self.feature_names, self.model.feature_importances_)
            },
            "meets_targets": {
                "mae_le_0.02": mae <= 0.02,
                "rmse_le_0.03": rmse <= 0.03,
                "r2_ge_0.50": r2 >= 0.50,
            },
        }
        return metrics

    def predict_quality(self, generation_time_ms, shots_used, num_qubits, bit_distribution, entropy_score=None):
        """Return entropy-maximization prediction payload (legacy-compatible method name)."""
        if self.model is None or self.scaler is None:
            return {
                "prediction": None,
                "confidence": 0.0,
                "model_version": "unavailable",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "error": "Model not loaded",
                "objective": self.objective,
            }

        try:
            generation_time_ms = float(generation_time_ms)
            shots_used = float(shots_used)
            num_qubits = float(num_qubits)
            bit_distribution = float(bit_distribution)

            if entropy_score is None:
                entropy_score = max(0.0, 1.0 - (2.0 * abs(bit_distribution - 0.5)))
            entropy_score = float(np.clip(entropy_score, 0.0, 1.0))

            bit_bias = abs(bit_distribution - 0.5)
            latency_per_shot = generation_time_ms / max(1.0, shots_used)

            features = np.array(
                [[
                    generation_time_ms,
                    shots_used,
                    num_qubits,
                    bit_distribution,
                    entropy_score,
                    bit_bias,
                    latency_per_shot,
                ]]
            )
        except (TypeError, ValueError) as exc:
            return {
                "prediction": None,
                "confidence": 0.0,
                "model_version": self.metadata.get("model_version", "v2"),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "error": f"Invalid feature input: {exc}",
                "objective": self.objective,
            }

        feature_df = pd.DataFrame(features, columns=self.feature_names)
        scaled = self.scaler.transform(feature_df)
        predicted_entropy = float(np.clip(self.model.predict(scaled)[0], 0.0, 1.0))

        tree_std = 0.0
        if hasattr(self.model, "estimators_") and self.model.estimators_:
            per_tree = np.array([est.predict(scaled)[0] for est in self.model.estimators_], dtype=float)
            tree_std = float(np.std(per_tree))
        confidence = float(np.clip(1.0 - (tree_std / 0.08), 0.0, 1.0))

        expected_gain = max(0.0, predicted_entropy - entropy_score)
        ranking_score = float(np.clip((0.8 * predicted_entropy) + (0.2 * entropy_score), 0.0, 1.0))
        prediction = "good" if predicted_entropy >= self.good_entropy_threshold else "bad"

        return {
            "prediction": prediction,
            "confidence": round(confidence, 4),
            "predicted_entropy_score": round(predicted_entropy, 6),
            "baseline_entropy_score": round(entropy_score, 6),
            "expected_entropy_gain": round(expected_gain, 6),
            "ranking_score": round(ranking_score, 6),
            "quality_score": round(ranking_score, 6),
            "tail_threshold": float(self.tail_threshold),
            "objective": self.objective,
            "model_version": self.metadata.get("model_version", "v2"),
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
            "objective": self.objective,
            "mae": float(self.latest_metrics.get("mae", 0.0)),
            "rmse": float(self.latest_metrics.get("rmse", 0.0)),
            "r2": float(self.latest_metrics.get("r2", 0.0)),
            "pearson_corr": float(self.latest_metrics.get("pearson_corr", 0.0)),
            "spearman_corr": float(self.latest_metrics.get("spearman_corr", 0.0)),
            "cv_mae_mean": float(self.latest_metrics.get("cv_mae_mean", 0.0)),
            "cv_r2_mean": float(self.latest_metrics.get("cv_r2_mean", 0.0)),
            "model_size_mb": round(model_size_mb, 4),
            "scaler_size_mb": round(scaler_size_mb, 4),
            "feature_names": self.feature_names,
            "feature_importance": self.latest_metrics.get("feature_importance", {}),
            "tail_threshold": float(self.tail_threshold),
            "good_entropy_threshold": float(self.good_entropy_threshold),
            "model_version": "v2-entropy-regressor",
        }

        with open(self.metadata_path, "w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2)

        self.metadata = metadata
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
                self.metadata = {}

            # Reject legacy classification artifacts to force a retrain.
            if self.metadata.get("objective") not in [self.objective, None]:
                print("[ML] Legacy model objective detected. Retrain required for entropy-maximization.")
                self.model = None
                self.scaler = None
                self.metadata = {}
                return False

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
            "model_version": "v2-entropy-regressor",
            "objective": self.objective,
        }

        metadata["model_loaded"] = self.model is not None and self.scaler is not None
        metadata["objective"] = self.objective

        if metadata["model_loaded"]:
            sample_features = pd.DataFrame(
                [[300.0, 256.0, 16.0, 0.5, 0.97, 0.0, 1.171875]],
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
