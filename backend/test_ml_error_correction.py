import os
import shutil
import tempfile
import time
import unittest

from ml_data_logger import QuantumDataLogger
from ml_error_corrector import QuantumKeyErrorCorrector


class FakeQualityClassifier:
    """Deterministic entropy predictor for correction-flow tests."""

    def __init__(self):
        self.model = object()
        self.scaler = object()

    def predict_quality(self, generation_time_ms, shots_used, num_qubits, bit_distribution, entropy_score=None):
        entropy_score = float(entropy_score or 0.0)
        predicted = min(1.0, entropy_score + 0.02)
        ranking = min(1.0, (0.8 * predicted) + (0.2 * entropy_score))
        return {
            "prediction": "good" if predicted >= 0.98 else "bad",
            "confidence": 0.9,
            "predicted_entropy_score": predicted,
            "ranking_score": ranking,
            "expected_entropy_gain": max(0.0, predicted - entropy_score),
            "objective": "entropy_maximization",
            "model_version": "test-v2",
        }


class NoModelClassifier:
    model = None
    scaler = None

    def predict_quality(self, *args, **kwargs):
        return {
            "prediction": None,
            "confidence": 0.0,
            "predicted_entropy_score": 0.0,
            "ranking_score": 0.0,
            "expected_entropy_gain": 0.0,
            "model_version": "unavailable",
        }


class FakeKeyGenerator:
    def __init__(self, binaries):
        self.binaries = binaries
        self.idx = 0

    def generate_secure_key(self, key_length=256, shots=1024):
        binary = self.binaries[min(self.idx, len(self.binaries) - 1)]
        self.idx += 1
        hex_value = hex(int(binary, 2))[2:].upper().zfill(len(binary) // 4)
        return {
            "binary": binary,
            "hex": hex_value,
            "length": key_length,
            "shots_per_chunk": shots,
        }


class SlowKeyGenerator(FakeKeyGenerator):
    def generate_secure_key(self, key_length=256, shots=1024):
        time.sleep(0.02)
        return super().generate_secure_key(key_length=key_length, shots=shots)


class TestErrorCorrection(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="ml_corrector_test_")
        self.logger = QuantumDataLogger(log_dir=self.temp_dir)
        self.classifier = FakeQualityClassifier()
        self.corrector = QuantumKeyErrorCorrector(
            self.classifier,
            self.logger,
            log_dir=self.temp_dir,
        )
        self.bad_binary = ("1" * 100) + ("0" * 28)
        self.good_binary = ("10" * 64)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_single_generation(self):
        generator = FakeKeyGenerator([self.good_binary])
        result = self.corrector._attempt_single_generation(generator, key_length=128, shots=256)
        self.assertIn("key", result)
        self.assertIn("quality", result)
        self.assertIn("predicted_entropy_score", result["quality"])
        self.assertGreaterEqual(result["quality"]["predicted_entropy_score"], 0.0)
        self.assertLessEqual(result["quality"]["predicted_entropy_score"], 1.0)

    def test_correction_improves_entropy(self):
        control_generator = FakeKeyGenerator([self.bad_binary, self.good_binary])
        treated_generator = FakeKeyGenerator([self.bad_binary, self.good_binary])

        control = self.corrector.generate_with_quality_improvement(
            key_generator=control_generator,
            key_length=128,
            shots=256,
            enable_correction=False,
            max_attempts=3,
        )
        treated = self.corrector.generate_with_quality_improvement(
            key_generator=treated_generator,
            key_length=128,
            shots=256,
            enable_correction=True,
            max_attempts=3,
        )

        self.assertGreaterEqual(treated["improvement"]["final_entropy"], control["improvement"]["final_entropy"])
        self.assertGreaterEqual(treated["attempts"], 1)

    def test_correction_completes_in_time(self):
        generator = SlowKeyGenerator([self.bad_binary, self.good_binary, self.good_binary])
        start = time.perf_counter()
        result = self.corrector.generate_with_quality_improvement(
            key_generator=generator,
            key_length=128,
            shots=256,
            enable_correction=True,
            max_attempts=3,
        )
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 20.0)
        self.assertIn("generation_time_ms", result)

    def test_ab_test_logging(self):
        control_generator = FakeKeyGenerator([self.bad_binary])
        treated_generator = FakeKeyGenerator([self.bad_binary, self.good_binary])

        self.corrector.generate_with_quality_improvement(
            key_generator=control_generator,
            key_length=128,
            shots=256,
            enable_correction=False,
        )
        self.corrector.generate_with_quality_improvement(
            key_generator=treated_generator,
            key_length=128,
            shots=256,
            enable_correction=True,
            max_attempts=3,
        )

        self.assertTrue(os.path.exists(self.corrector.ab_test_log_path))
        with open(self.corrector.ab_test_log_path, "r", encoding="utf-8-sig") as handle:
            lines = [line.strip() for line in handle if line.strip()]
        self.assertGreaterEqual(len(lines), 3)

    def test_ab_test_analysis_with_tail_metrics(self):
        for _ in range(4):
            control_generator = FakeKeyGenerator([self.bad_binary])
            treated_generator = FakeKeyGenerator([self.bad_binary, self.good_binary])

            self.corrector.generate_with_quality_improvement(
                key_generator=control_generator,
                key_length=128,
                shots=256,
                enable_correction=False,
            )
            self.corrector.generate_with_quality_improvement(
                key_generator=treated_generator,
                key_length=128,
                shots=256,
                enable_correction=True,
                max_attempts=3,
            )

        results = self.corrector.get_ab_test_results()
        self.assertIn("control", results)
        self.assertIn("treated", results)
        self.assertIn("improvement", results)
        self.assertIn("p5_entropy", results["control"])
        self.assertIn("tail_risk_reduction_percent", results["improvement"])

    def test_strict_ab_runner(self):
        generator = FakeKeyGenerator([self.bad_binary, self.good_binary, self.good_binary])
        results = self.corrector.run_strict_ab_test(
            key_generator=generator,
            key_length=128,
            shots=256,
            samples_per_variant=10,
            max_attempts=3,
            reset_log=True,
        )
        self.assertGreaterEqual(results["control"]["samples"], 10)
        self.assertGreaterEqual(results["treated"]["samples"], 10)

    def test_graceful_degradation(self):
        no_ml_corrector = QuantumKeyErrorCorrector(NoModelClassifier(), self.logger, log_dir=self.temp_dir)
        generator = FakeKeyGenerator([self.good_binary])
        result = no_ml_corrector.generate_with_quality_improvement(
            key_generator=generator,
            key_length=128,
            shots=256,
            enable_correction=True,
            max_attempts=3,
        )
        self.assertIn("binary", result)
        self.assertFalse(result.get("correction_applied", False))


if __name__ == '__main__':
    unittest.main()
