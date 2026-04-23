"""Unit tests for Part 2 ML model training and inference."""

import os
import time
import unittest

from ml_model_trainer import QuantumKeyQualityClassifier


class TestMLModel(unittest.TestCase):
    """Validate model training and predictions."""

    def setUp(self):
        self.classifier = QuantumKeyQualityClassifier()

    def test_data_loading(self):
        X, y, df = self.classifier.prepare_data()
        self.assertGreaterEqual(len(df), 500)
        self.assertFalse(df[self.classifier.feature_names].isna().any().any())
        self.assertGreaterEqual(len(set(y.tolist())), 2)
        self.assertEqual(X.shape[1], len(self.classifier.feature_names))

    def test_model_training(self):
        X, y, _ = self.classifier.prepare_data()
        start = time.perf_counter()
        metrics = self.classifier.train(X, y)
        elapsed = time.perf_counter() - start

        self.assertIn("accuracy", metrics)
        self.assertGreaterEqual(metrics["accuracy"], 0.80)
        self.assertLess(elapsed, 10.0)

    def test_model_prediction(self):
        X, y, _ = self.classifier.prepare_data()
        self.classifier.train(X, y)

        prediction = self.classifier.predict_quality(
            generation_time_ms=250.0,
            shots_used=256,
            num_qubits=16,
            bit_distribution=0.5,
            entropy_score=0.97,
        )
        self.assertIn(prediction["prediction"], ["good", "bad"])
        self.assertGreaterEqual(prediction["confidence"], 0.0)
        self.assertLessEqual(prediction["confidence"], 1.0)

    def test_model_persistence(self):
        X, y, _ = self.classifier.prepare_data()
        self.classifier.train(X, y)
        self.classifier.save_model()

        loaded = QuantumKeyQualityClassifier()
        self.assertTrue(loaded.load_model())

        original = self.classifier.predict_quality(300.0, 256, 16, 0.52, entropy_score=0.96)
        restored = loaded.predict_quality(300.0, 256, 16, 0.52, entropy_score=0.96)
        self.assertEqual(original["prediction"], restored["prediction"])

    def test_model_size(self):
        X, y, _ = self.classifier.prepare_data()
        self.classifier.train(X, y)
        self.classifier.save_model()

        model_size_mb = os.path.getsize(self.classifier.model_path) / (1024 * 1024)
        self.assertLess(model_size_mb, 5.0)

    def test_prediction_latency(self):
        X, y, _ = self.classifier.prepare_data()
        self.classifier.train(X, y)

        start = time.perf_counter()
        for _ in range(100):
            _ = self.classifier.predict_quality(250.0, 256, 16, 0.5, entropy_score=0.97)
        avg_ms = ((time.perf_counter() - start) * 1000.0) / 100
        self.assertLess(avg_ms, 50.0)

    def test_feature_importance(self):
        X, y, _ = self.classifier.prepare_data()
        metrics = self.classifier.train(X, y)

        importance = metrics["feature_importance"]
        self.assertAlmostEqual(sum(importance.values()), 1.0, places=5)
        self.assertEqual(set(importance.keys()), set(self.classifier.feature_names))


if __name__ == "__main__":
    unittest.main()
