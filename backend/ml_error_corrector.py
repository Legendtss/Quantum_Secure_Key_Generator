import csv
import json
import os
import time
import uuid
from datetime import datetime, timezone

import pandas as pd

from entropy_analyzer import EntropyAnalyzer


class QuantumKeyErrorCorrector:
    """Entropy-maximizing correction loop plus strict A/B analytics."""

    def __init__(self, ml_classifier, logger, log_dir="backend/data"):
        self.classifier = ml_classifier
        self.logger = logger
        self.log_dir = log_dir
        self.ab_test_log_path = os.path.join(log_dir, "ab_test_log.csv")

        self.max_attempts = 5
        self.min_correction_attempts = 2
        self.target_entropy_score = 0.985
        self.entropy_tail_threshold = 0.95
        self.min_expected_gain = 0.0015
        self.max_total_time_ms = 20000

        self.entropy_analyzer = EntropyAnalyzer()
        self._ensure_ab_test_file()

    def _ensure_ab_test_file(self):
        os.makedirs(self.log_dir, exist_ok=True)
        if os.path.exists(self.ab_test_log_path):
            return

        headers = [
            "timestamp",
            "session_id",
            "variant",
            "attempt",
            "selected_final",
            "entropy_score",
            "predicted_entropy",
            "ranking_score",
            "expected_gain",
            "generation_time_ms",
            "correction_applied",
            "key_length",
            "shots",
            "below_tail_threshold",
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

        if shannon is not None:
            shannon_val = float(shannon)
            if block_entropy is not None:
                return max(0.0, min(1.0, (0.8 * shannon_val) + (0.2 * float(block_entropy))))
            return max(0.0, min(1.0, shannon_val))

        overall = entropy_result.get("overall_score", None)
        if overall is not None:
            return max(0.0, min(1.0, float(overall) / 100.0))
        return 0.0

    def _attempt_single_generation(self, key_generator, key_length, shots):
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
                "predicted_entropy_score": entropy_score,
                "ranking_score": entropy_score,
                "expected_entropy_gain": 0.0,
                "objective": "entropy_maximization",
                "model_version": "unavailable",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "error": "Model not loaded",
            }
            return {
                "key": key,
                "quality": quality,
                "entropy": float(entropy_score),
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

        return {
            "key": key,
            "quality": quality,
            "entropy": float(entropy_score),
            "time_ms": generation_time_ms,
        }

    def _select_best_key(self, key_attempts):
        """Rank by measured entropy first, then ML ranking score, then lower latency."""
        if not key_attempts:
            return None

        def sort_tuple(item):
            quality = item.get("quality") or {}
            measured_entropy = float(item.get("entropy", 0.0) or 0.0)
            ranking_score = float(quality.get("ranking_score", 0.0) or 0.0)
            predicted_entropy = float(quality.get("predicted_entropy_score", 0.0) or 0.0)
            duration_ms = float(item.get("time_ms", 0.0) or 0.0)
            return (measured_entropy, ranking_score, predicted_entropy, -duration_ms)

        return sorted(key_attempts, key=sort_tuple, reverse=True)[0]

    def log_ab_test_event(
        self,
        session_id,
        variant,
        attempt_num,
        entropy_score,
        predicted_entropy,
        ranking_score,
        expected_gain,
        generation_time_ms,
        correction_applied,
        key_length,
        shots,
        selected_final=False,
    ):
        try:
            entropy_val = float(entropy_score or 0.0)
            row = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": session_id,
                "variant": variant,
                "attempt": int(attempt_num),
                "selected_final": bool(selected_final),
                "entropy_score": round(entropy_val, 6),
                "predicted_entropy": round(float(predicted_entropy or 0.0), 6),
                "ranking_score": round(float(ranking_score or 0.0), 6),
                "expected_gain": round(float(expected_gain or 0.0), 6),
                "generation_time_ms": round(float(generation_time_ms or 0.0), 2),
                "correction_applied": bool(correction_applied),
                "key_length": int(key_length),
                "shots": int(shots),
                "below_tail_threshold": bool(entropy_val < self.entropy_tail_threshold),
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
        """Generate key and optimize for highest entropy score using ML-guided ranking."""
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

            quality = single.get("quality") or {}
            entropy_score = float(single.get("entropy", 0.0) or 0.0)
            predicted_entropy = float(quality.get("predicted_entropy_score", entropy_score) or entropy_score)
            ranking_score = float(quality.get("ranking_score", predicted_entropy) or predicted_entropy)
            expected_gain = float(quality.get("expected_entropy_gain", 0.0) or 0.0)

            self.log_ab_test_event(
                session_id=session_id,
                variant=variant,
                attempt_num=attempt,
                entropy_score=entropy_score,
                predicted_entropy=predicted_entropy,
                ranking_score=ranking_score,
                expected_gain=expected_gain,
                generation_time_ms=single.get("time_ms", 0.0),
                correction_applied=enable_correction and attempt > 1,
                key_length=key_length,
                shots=shots,
                selected_final=False,
            )

            if not enable_correction:
                break

            min_attempts_met = attempt >= min(attempts_limit, self.min_correction_attempts)
            if min_attempts_met and entropy_score >= self.target_entropy_score and expected_gain <= self.min_expected_gain:
                break

        best = self._select_best_key(key_attempts)
        if best is None:
            raise RuntimeError("No key attempt could be generated")

        initial_entropy = float(key_attempts[0].get("entropy", 0.0) or 0.0)
        final_entropy = float(best.get("entropy", 0.0) or 0.0)
        entropy_improvement = ((final_entropy - initial_entropy) / initial_entropy * 100.0) if initial_entropy > 0 else 0.0
        total_generation_time_ms = sum(float(item.get("time_ms", 0.0) or 0.0) for item in key_attempts)

        final_key = dict(best.get("key", {}))
        final_key["generation_time_ms"] = round(total_generation_time_ms, 2)
        final_key["ml_quality_assessment"] = best.get("quality", {})
        final_key["correction_applied"] = bool(enable_correction and len(key_attempts) > 1)
        final_key["attempts"] = len(key_attempts)
        final_key["attempt_limit"] = attempts_limit
        final_key["correction_timeout_hit"] = (time.perf_counter() - start_total) * 1000.0 >= self.max_total_time_ms
        final_key["ml_objective"] = "entropy_maximization"
        final_key["tail_threshold"] = float(self.entropy_tail_threshold)
        final_key["improvement"] = {
            "initial_entropy": round(initial_entropy, 6),
            "final_entropy": round(final_entropy, 6),
            "entropy_improvement_percent": round(entropy_improvement, 4),
            "tail_risk_reduced": bool(initial_entropy < self.entropy_tail_threshold and final_entropy >= self.entropy_tail_threshold),
        }
        final_key["correction_warning"] = None

        selected_attempt_idx = key_attempts.index(best) + 1
        selected_quality = best.get("quality") or {}
        self.log_ab_test_event(
            session_id=session_id,
            variant=variant,
            attempt_num=selected_attempt_idx,
            entropy_score=best.get("entropy", 0.0),
            predicted_entropy=selected_quality.get("predicted_entropy_score", best.get("entropy", 0.0)),
            ranking_score=selected_quality.get("ranking_score", best.get("entropy", 0.0)),
            expected_gain=selected_quality.get("expected_entropy_gain", 0.0),
            generation_time_ms=best.get("time_ms", 0.0),
            correction_applied=bool(enable_correction and len(key_attempts) > 1),
            key_length=key_length,
            shots=shots,
            selected_final=True,
        )

        return final_key

    def run_strict_ab_test(
        self,
        key_generator,
        key_length,
        shots,
        samples_per_variant=500,
        max_attempts=None,
        reset_log=False,
    ):
        """Run paired control/treated generation with identical settings."""
        samples = max(1, int(samples_per_variant))
        attempt_cap = max(1, int(max_attempts or self.max_attempts))

        if reset_log and os.path.exists(self.ab_test_log_path):
            os.remove(self.ab_test_log_path)
            self._ensure_ab_test_file()

        for _ in range(samples):
            self.generate_with_quality_improvement(
                key_generator=key_generator,
                key_length=key_length,
                shots=shots,
                enable_correction=False,
                max_attempts=1,
            )
            self.generate_with_quality_improvement(
                key_generator=key_generator,
                key_length=key_length,
                shots=shots,
                enable_correction=True,
                max_attempts=attempt_cap,
            )

        results = self.get_ab_test_results()
        results["strict_ab_run"] = {
            "samples_per_variant_requested": samples,
            "settings": {
                "key_length": int(key_length),
                "shots": int(shots),
                "max_attempts": int(attempt_cap),
            },
        }
        return results

    def get_ab_test_results(self, output_path=None):
        """Analyze A/B logs with tail metrics and ROI guidance."""
        empty_payload = {
            "control": {
                "samples": 0,
                "avg_entropy": 0.0,
                "p5_entropy": 0.0,
                "avg_time_ms": 0.0,
                "pct_below_threshold": 0.0,
            },
            "treated": {
                "samples": 0,
                "avg_entropy": 0.0,
                "p5_entropy": 0.0,
                "avg_time_ms": 0.0,
                "pct_below_threshold": 0.0,
                "avg_attempts": 0.0,
            },
            "improvement": {
                "entropy_gain_percent": 0.0,
                "p5_entropy_gain_percent": 0.0,
                "tail_risk_reduction_percent": 0.0,
                "latency_cost_percent": 0.0,
                "roi": 0.0,
                "recommendation": "Insufficient data",
            },
            "thresholds": {
                "tail_entropy_threshold": float(self.entropy_tail_threshold),
                "strict_ab_min_samples_per_variant": 500,
            },
        }

        if not os.path.exists(self.ab_test_log_path):
            return empty_payload

        df = pd.read_csv(self.ab_test_log_path)
        if df.empty:
            return empty_payload

        finals = df[df["selected_final"].astype(str).str.lower().isin(["true", "1"])]
        attempts = df[df["selected_final"].astype(str).str.lower().isin(["false", "0"])]

        def variant_metrics(name):
            sub = finals[finals["variant"] == name]
            if sub.empty:
                base = {
                    "samples": 0,
                    "avg_entropy": 0.0,
                    "p5_entropy": 0.0,
                    "avg_time_ms": 0.0,
                    "pct_below_threshold": 0.0,
                }
                if name == "treated":
                    base["avg_attempts"] = 0.0
                return base

            entropy_series = sub["entropy_score"].astype(float)
            pct_below = (entropy_series < self.entropy_tail_threshold).mean() * 100.0
            base = {
                "samples": int(len(sub)),
                "avg_entropy": float(entropy_series.mean()),
                "p5_entropy": float(entropy_series.quantile(0.05)),
                "avg_time_ms": float(sub["generation_time_ms"].astype(float).mean()),
                "pct_below_threshold": float(pct_below),
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

        p5_gain = 0.0
        if control["p5_entropy"] > 0:
            p5_gain = ((treated["p5_entropy"] - control["p5_entropy"]) / control["p5_entropy"]) * 100.0

        tail_risk_reduction = control["pct_below_threshold"] - treated["pct_below_threshold"]

        latency_cost = 0.0
        if control["avg_time_ms"] > 0:
            latency_cost = ((treated["avg_time_ms"] - control["avg_time_ms"]) / control["avg_time_ms"]) * 100.0

        gain_blend = (0.6 * entropy_gain) + (0.4 * tail_risk_reduction)
        roi = gain_blend / max(abs(latency_cost), 1.0)

        strict_min = 500
        strict_ready = control["samples"] >= strict_min and treated["samples"] >= strict_min
        recommendation = "Collect at least 500 samples per variant for strict A/B confidence"
        if strict_ready:
            recommendation = "Keep ML correction: positive entropy/tail ROI" if roi > 1 else "Disable/tune ML: latency outweighs entropy benefit"

        results = {
            "control": {
                "samples": control["samples"],
                "avg_entropy": round(control["avg_entropy"], 6),
                "p5_entropy": round(control["p5_entropy"], 6),
                "avg_time_ms": round(control["avg_time_ms"], 4),
                "pct_below_threshold": round(control["pct_below_threshold"], 2),
            },
            "treated": {
                "samples": treated["samples"],
                "avg_entropy": round(treated["avg_entropy"], 6),
                "p5_entropy": round(treated["p5_entropy"], 6),
                "avg_time_ms": round(treated["avg_time_ms"], 4),
                "pct_below_threshold": round(treated["pct_below_threshold"], 2),
                "avg_attempts": round(treated.get("avg_attempts", 0.0), 4),
            },
            "improvement": {
                "entropy_gain_percent": round(entropy_gain, 4),
                "p5_entropy_gain_percent": round(p5_gain, 4),
                "tail_risk_reduction_percent": round(tail_risk_reduction, 4),
                "latency_cost_percent": round(latency_cost, 4),
                "roi": round(roi, 4),
                "recommendation": recommendation,
                "strict_ab_ready": strict_ready,
                "tradeoff": {
                    "gain_blend_percent": round(gain_blend, 4),
                    "latency_cost_percent": round(latency_cost, 4),
                },
            },
            "thresholds": {
                "tail_entropy_threshold": float(self.entropy_tail_threshold),
                "strict_ab_min_samples_per_variant": strict_min,
            },
        }

        if output_path:
            with open(output_path, "w", encoding="utf-8") as handle:
                json.dump(results, handle, indent=2)

        return results

    def get_correction_stats(self):
        """Return correction usage plus tail-risk metrics."""
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
            "p5_entropy_gain_percent": results["improvement"].get("p5_entropy_gain_percent", 0.0),
            "tail_risk_reduction_percent": results["improvement"].get("tail_risk_reduction_percent", 0.0),
            "time_overhead_percent": results["improvement"].get("latency_cost_percent", 0.0),
            "roi": results["improvement"].get("roi", 0.0),
        }
