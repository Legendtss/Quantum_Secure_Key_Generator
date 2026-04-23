import csv
import json
import os
import time
import uuid
from datetime import datetime, timezone

import pandas as pd

from entropy_analyzer import EntropyAnalyzer


class QuantumKeyErrorCorrector:
    """Use ML predictions to improve quantum key quality via controlled regeneration."""

    def __init__(self, ml_classifier, logger, log_dir="backend/data"):
        self.classifier = ml_classifier
        self.logger = logger
        self.log_dir = log_dir
        self.ab_test_log_path = os.path.join(log_dir, "ab_test_log.csv")
        self.max_attempts = 3
        self.max_total_time_ms = 20000
        self.entropy_analyzer = EntropyAnalyzer()
        self._ensure_ab_test_file()

    def _ensure_ab_test_file(self):
        """Create AB test log CSV with headers if it does not exist."""
        os.makedirs(self.log_dir, exist_ok=True)
        if os.path.exists(self.ab_test_log_path):
            return

        headers = [
            "timestamp",
            "session_id",
            "variant",
            "attempt",
            "selected_final",
            "quality_prediction",
            "confidence",
            "entropy_score",
            "generation_time_ms",
            "correction_applied",
            "key_length",
            "shots",
        ]
        with open(self.ab_test_log_path, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)

    def _classifier_available(self):
        return (
            self.classifier is not None
            and getattr(self.classifier, "model", None) is not None
            and getattr(self.classifier, "scaler", None) is not None
        )

    def _extract_entropy_score(self, entropy_result):
        if not isinstance(entropy_result, dict):
            return 0.0
        tests = entropy_result.get("tests", {})
        shannon = tests.get("shannon_entropy", {}).get("entropy", None)
        block_entropy = tests.get("shannon_entropy", {}).get("block_entropy", None)

        # Prefer entropy-based measurements for smoother ML quality separation.
        if shannon is not None:
            shannon_val = float(shannon)
            if block_entropy is not None:
                return max(0.0, min(1.0, (shannon_val * 0.8) + (float(block_entropy) * 0.2)))
            return max(0.0, min(1.0, shannon_val))

        overall = entropy_result.get("overall_score", None)
        if overall is not None:
            return max(0.0, min(1.0, float(overall) / 100.0))

        return 0.0

    def _attempt_single_generation(self, key_generator, key_length, shots):
        """Generate one key and attach ML quality prediction and entropy metrics."""
        start = time.perf_counter()
        key = key_generator.generate_secure_key(key_length=key_length, shots=shots)
        generation_time_ms = (time.perf_counter() - start) * 1000.0

        key["generation_time_ms"] = round(generation_time_ms, 2)
        key["shots_used"] = int(shots)

        bit_string = key.get("binary", "")

        entropy_score = 0.0
        try:
            entropy_result = self.entropy_analyzer.analyze_randomness(bit_string)
            entropy_score = self._extract_entropy_score(entropy_result)
        except Exception:
            entropy_score = 0.0

        if not self._classifier_available():
            quality = {
                "prediction": None,
                "confidence": 0.0,
                "model_version": "unavailable",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "error": "Model not loaded",
            }
            return {
                "key": key,
                "quality": quality,
                "confidence": 0.0,
                "entropy": entropy_score,
                "time_ms": generation_time_ms,
            }

        bit_distribution = bit_string.count("1") / max(1, len(bit_string))
        quality = self.classifier.predict_quality(
            generation_time_ms=generation_time_ms,
            shots_used=shots,
            num_qubits=max(1, key_length // 16),
            bit_distribution=bit_distribution,
            entropy_score=entropy_score,
        )

        confidence = float(quality.get("confidence", 0.0) or 0.0)

        return {
            "key": key,
            "quality": quality,
            "confidence": confidence,
            "entropy": float(entropy_score),
            "time_ms": generation_time_ms,
        }

    def _select_best_key(self, key_attempts):
        """Select best candidate: good quality first, then confidence, then entropy."""
        if not key_attempts:
            return None

        def sort_tuple(item):
            quality_pred = (item.get("quality") or {}).get("prediction")
            is_good = 1 if quality_pred == "good" else 0
            confidence = float(item.get("confidence", 0.0) or 0.0)
            entropy = float(item.get("entropy", 0.0) or 0.0)
            return (is_good, confidence, entropy)

        return sorted(key_attempts, key=sort_tuple, reverse=True)[0]

    def log_ab_test_event(
        self,
        session_id,
        variant,
        attempt_num,
        quality_prediction,
        confidence,
        entropy_score,
        generation_time_ms,
        correction_applied,
        key_length,
        shots,
        selected_final=False,
    ):
        """Append one attempt event to AB test log CSV."""
        try:
            row = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": session_id,
                "variant": variant,
                "attempt": int(attempt_num),
                "selected_final": bool(selected_final),
                "quality_prediction": quality_prediction,
                "confidence": round(float(confidence or 0.0), 4),
                "entropy_score": round(float(entropy_score or 0.0), 6),
                "generation_time_ms": round(float(generation_time_ms or 0.0), 2),
                "correction_applied": bool(correction_applied),
                "key_length": int(key_length),
                "shots": int(shots),
            }
            with open(self.ab_test_log_path, "a", newline="", encoding="utf-8-sig") as handle:
                writer = csv.DictWriter(handle, fieldnames=row.keys())
                writer.writerow(row)
        except Exception as exc:
            print(f"[ML Corrector] AB log write failed (non-blocking): {exc}")

    def generate_with_quality_improvement(
        self,
        key_generator,
        key_length,
        shots,
        enable_correction=True,
        max_attempts=None,
    ):
        """Generate key with optional ML-based correction loop and timeout protection."""
        attempts_limit = max(1, int(max_attempts or self.max_attempts))
        session_id = str(uuid.uuid4())
        start_total = time.perf_counter()
        key_attempts = []

        classifier_available = self._classifier_available()
        if not classifier_available:
            enable_correction = False

        variant = "treated" if enable_correction else "control"

        for attempt in range(1, attempts_limit + 1):
            elapsed_total_ms = (time.perf_counter() - start_total) * 1000.0
            if elapsed_total_ms >= self.max_total_time_ms:
                break

            single = self._attempt_single_generation(
                key_generator=key_generator,
                key_length=key_length,
                shots=shots,
            )
            key_attempts.append(single)

            prediction = (single.get("quality") or {}).get("prediction")
            self.log_ab_test_event(
                session_id=session_id,
                variant=variant,
                attempt_num=attempt,
                quality_prediction=prediction,
                confidence=single.get("confidence", 0.0),
                entropy_score=single.get("entropy", 0.0),
                generation_time_ms=single.get("time_ms", 0.0),
                correction_applied=enable_correction and attempt > 1,
                key_length=key_length,
                shots=shots,
                selected_final=False,
            )

            if not enable_correction:
                break

            if prediction == "good":
                break

        best = self._select_best_key(key_attempts)
        if best is None:
            raise RuntimeError("No key attempt could be generated")

        initial_entropy = float(key_attempts[0].get("entropy", 0.0) or 0.0)
        final_entropy = float(best.get("entropy", 0.0) or 0.0)

        entropy_improvement = 0.0
        if initial_entropy > 0:
            entropy_improvement = ((final_entropy - initial_entropy) / initial_entropy) * 100.0

        total_generation_time_ms = sum(float(item.get("time_ms", 0.0) or 0.0) for item in key_attempts)

        final_key = dict(best.get("key", {}))
        final_key["generation_time_ms"] = round(total_generation_time_ms, 2)
        final_key["ml_quality_assessment"] = best.get("quality", {})
        final_key["correction_applied"] = bool(enable_correction and len(key_attempts) > 1)
        final_key["attempts"] = len(key_attempts)
        final_key["attempt_limit"] = attempts_limit
        final_key["correction_timeout_hit"] = (time.perf_counter() - start_total) * 1000.0 >= self.max_total_time_ms
        final_key["improvement"] = {
            "initial_entropy": round(initial_entropy, 6),
            "final_entropy": round(final_entropy, 6),
            "entropy_improvement_percent": round(entropy_improvement, 4),
        }
        final_key["correction_warning"] = None

        if enable_correction and (best.get("quality") or {}).get("prediction") != "good":
            final_key["correction_warning"] = "No 'good' key found within attempt/time limits; returned best candidate"

        selected_attempt_idx = key_attempts.index(best) + 1
        self.log_ab_test_event(
            session_id=session_id,
            variant=variant,
            attempt_num=selected_attempt_idx,
            quality_prediction=(best.get("quality") or {}).get("prediction"),
            confidence=best.get("confidence", 0.0),
            entropy_score=best.get("entropy", 0.0),
            generation_time_ms=best.get("time_ms", 0.0),
            correction_applied=bool(enable_correction and len(key_attempts) > 1),
            key_length=key_length,
            shots=shots,
            selected_final=True,
        )

        return final_key

    def get_ab_test_results(self, output_path=None):
        """Analyze AB test logs and return control vs treated metrics."""
        if not os.path.exists(self.ab_test_log_path):
            return {
                "control": {"samples": 0, "avg_entropy": 0.0, "avg_time_ms": 0.0, "pct_good_quality": 0.0},
                "treated": {
                    "samples": 0,
                    "avg_entropy": 0.0,
                    "avg_time_ms": 0.0,
                    "pct_good_quality": 0.0,
                    "avg_attempts": 0.0,
                },
                "improvement": {"entropy_gain_percent": 0.0, "latency_cost_percent": 0.0, "roi": 0.0},
            }

        df = pd.read_csv(self.ab_test_log_path)
        if df.empty:
            return {
                "control": {"samples": 0, "avg_entropy": 0.0, "avg_time_ms": 0.0, "pct_good_quality": 0.0},
                "treated": {
                    "samples": 0,
                    "avg_entropy": 0.0,
                    "avg_time_ms": 0.0,
                    "pct_good_quality": 0.0,
                    "avg_attempts": 0.0,
                },
                "improvement": {"entropy_gain_percent": 0.0, "latency_cost_percent": 0.0, "roi": 0.0},
            }

        finals = df[df["selected_final"].astype(str).str.lower().isin(["true", "1"])]
        attempts = df[df["selected_final"].astype(str).str.lower().isin(["false", "0"])]

        def variant_metrics(name):
            sub = finals[finals["variant"] == name]
            if sub.empty:
                base = {
                    "samples": 0,
                    "avg_entropy": 0.0,
                    "avg_time_ms": 0.0,
                    "pct_good_quality": 0.0,
                }
                if name == "treated":
                    base["avg_attempts"] = 0.0
                return base

            pct_good = (sub["quality_prediction"].astype(str).str.lower() == "good").mean() * 100.0
            base = {
                "samples": int(len(sub)),
                "avg_entropy": float(sub["entropy_score"].mean()),
                "avg_time_ms": float(sub["generation_time_ms"].mean()),
                "pct_good_quality": float(pct_good),
            }
            if name == "treated":
                treated_attempts = attempts[attempts["variant"] == "treated"]
                if treated_attempts.empty:
                    base["avg_attempts"] = 1.0
                else:
                    attempts_by_session = treated_attempts.groupby("session_id")["attempt"].max()
                    base["avg_attempts"] = float(attempts_by_session.mean())
            return base

        control = variant_metrics("control")
        treated = variant_metrics("treated")

        entropy_gain = 0.0
        if control["avg_entropy"] > 0:
            entropy_gain = ((treated["avg_entropy"] - control["avg_entropy"]) / control["avg_entropy"]) * 100.0

        latency_cost = 0.0
        if control["avg_time_ms"] > 0:
            latency_cost = ((treated["avg_time_ms"] - control["avg_time_ms"]) / control["avg_time_ms"]) * 100.0

        roi = 0.0
        if abs(latency_cost) > 1e-9:
            roi = entropy_gain / latency_cost

        results = {
            "control": {
                "samples": control["samples"],
                "avg_entropy": round(control["avg_entropy"], 6),
                "avg_time_ms": round(control["avg_time_ms"], 4),
                "pct_good_quality": round(control["pct_good_quality"], 2),
            },
            "treated": {
                "samples": treated["samples"],
                "avg_entropy": round(treated["avg_entropy"], 6),
                "avg_time_ms": round(treated["avg_time_ms"], 4),
                "pct_good_quality": round(treated["pct_good_quality"], 2),
                "avg_attempts": round(treated.get("avg_attempts", 0.0), 4),
            },
            "improvement": {
                "entropy_gain_percent": round(entropy_gain, 4),
                "latency_cost_percent": round(latency_cost, 4),
                "roi": round(roi, 4),
            },
        }

        if output_path:
            with open(output_path, "w", encoding="utf-8") as handle:
                json.dump(results, handle, indent=2)

        return results

    def get_correction_stats(self):
        """Return practical correction usage statistics for dashboard/API usage."""
        results = self.get_ab_test_results()

        control_samples = results["control"]["samples"]
        treated_samples = results["treated"]["samples"]
        total_samples = control_samples + treated_samples

        correction_rate = (treated_samples / total_samples * 100.0) if total_samples else 0.0

        return {
            "total_keys_generated": total_samples,
            "keys_with_correction": treated_samples,
            "correction_rate": round(correction_rate, 2),
            "avg_attempts_per_key": results["treated"].get("avg_attempts", 0.0),
            "entropy_improvement_percent": results["improvement"].get("entropy_gain_percent", 0.0),
            "time_overhead_percent": results["improvement"].get("latency_cost_percent", 0.0),
        }
