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
        self.log_dir = self._resolve_log_dir(log_dir)
        self.ab_test_log_path = os.path.join(self.log_dir, "ab_test_log.csv")

        self.max_attempts = 5
        self.min_correction_attempts = 2
        self.target_entropy_score = 0.985
        self.entropy_tail_threshold = 0.95
        self.min_expected_gain = 0.0015
        self.max_total_time_ms = 20000

        self.entropy_analyzer = EntropyAnalyzer()
        self._ensure_ab_test_file()

    def _resolve_log_dir(self, log_dir):
        """Resolve correction log directory to stable absolute backend/data."""
        if os.path.isabs(log_dir):
            return log_dir

        base_dir = os.path.dirname(os.path.abspath(__file__))
        if log_dir.startswith("backend/"):
            return os.path.join(base_dir, log_dir.split("backend/", 1)[1])
        return os.path.join(base_dir, log_dir)

    def _ensure_ab_test_file(self):
        os.makedirs(self.log_dir, exist_ok=True)
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

        if os.path.exists(self.ab_test_log_path):
            try:
                with open(self.ab_test_log_path, "r", encoding="utf-8-sig") as handle:
                    first_line = handle.readline().strip()
                existing = [col.strip() for col in first_line.split(",")] if first_line else []
                if existing == headers:
                    return

                backup_path = f"{self.ab_test_log_path}.legacy_{int(time.time())}.bak"
                os.replace(self.ab_test_log_path, backup_path)
                print(f"[ML Corrector] Archived legacy A/B log to {backup_path}")
            except Exception as exc:
                print(f"[ML Corrector] Failed header check, recreating A/B log: {exc}")

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
        # Generate candidate and compute fast features + ML prediction only
        start = time.perf_counter()
        key = key_generator.generate_secure_key(key_length=key_length, shots=shots)
        generation_time_ms = (time.perf_counter() - start) * 1000.0
        key["generation_time_ms"] = round(generation_time_ms, 2)
        key["shots_used"] = int(shots)

        bit_string = key.get("binary", "")

        # If classifier is not available, fall back to computing full entropy immediately
        if not self._classifier_available():
            entropy_score = 0.0
            try:
                entropy_result = self.entropy_analyzer.analyze_randomness(bit_string)
                entropy_score = self._extract_entropy_score(entropy_result)
            except Exception:
                entropy_score = 0.0

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

        # Extract fast features and predict
        feature_dict, _ = self.classifier.extract_fast_features_from_generation(key)
        bit_distribution = feature_dict.get("bit_balance_ratio", 0.5)
        quality = self.classifier.predict_quality(
            generation_time_ms=feature_dict.get("generation_time_ms", 0.0),
            shots_used=feature_dict.get("shots_used", 0.0),
            num_qubits=feature_dict.get("num_qubits", 1.0),
            bit_distribution=bit_distribution,
            entropy_score=None,
        )

        # Return candidate with predicted quality but without expensive full entropy yet
        return {
            "key": key,
            "quality": quality,
            "entropy": None,
            "time_ms": generation_time_ms,
            "fast_features": feature_dict,
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
        time_budget_ms=None,
    ):
        """Generate key and optimize for highest entropy score using ML-guided ranking."""
        attempts_limit = max(1, int(max_attempts or self.max_attempts))
        session_id = str(uuid.uuid4())
        start_total = time.perf_counter()
        effective_time_budget_ms = float(time_budget_ms if time_budget_ms is not None else self.max_total_time_ms)
        key_attempts = []

        classifier_available = self._classifier_available()
        if not classifier_available:
            enable_correction = False

        variant = "treated" if enable_correction else "control"

        for attempt in range(1, attempts_limit + 1):
            elapsed_total_ms = (time.perf_counter() - start_total) * 1000.0
            if elapsed_total_ms >= effective_time_budget_ms:
                break
            single = self._attempt_single_generation(
                key_generator=key_generator,
                key_length=key_length,
                shots=shots,
            )
            key_attempts.append(single)

            # Log ML prediction (entropy unknown until we run full analyzer on top K)
            quality = single.get("quality") or {}
            predicted_entropy = float(quality.get("predicted_entropy_score", 0.0) or 0.0)
            ranking_score = float(quality.get("ranking_score", predicted_entropy) or predicted_entropy)

            self.log_ab_test_event(
                session_id=session_id,
                variant=variant,
                attempt_num=attempt,
                entropy_score=0.0,
                predicted_entropy=predicted_entropy,
                ranking_score=ranking_score,
                expected_gain=quality.get("expected_entropy_gain", 0.0),
                generation_time_ms=single.get("time_ms", 0.0),
                correction_applied=enable_correction and attempt > 1,
                key_length=key_length,
                shots=shots,
                selected_final=False,
            )

            if not enable_correction:
                break

            # Continue generating candidates until attempts_limit; full entropy tests will be run on top K below
            continue

        # Run full entropy analysis only on top-K predicted candidates to save work.
        top_k = min(3, max(1, len(key_attempts)))
        # sort by predicted ranking_score
        ranked = sorted(
            [k for k in key_attempts if k.get("quality")],
            key=lambda x: float(x.get("quality", {}).get("ranking_score", 0.0)),
            reverse=True,
        )
        to_evaluate = ranked[:top_k]

        for cand in to_evaluate:
            try:
                bit_string = cand.get("key", {}).get("binary", "")
                entropy_result = self.entropy_analyzer.analyze_randomness(bit_string)
                entropy_score = self._extract_entropy_score(entropy_result)
            except Exception:
                entropy_score = 0.0

            cand["entropy"] = float(entropy_score)
            # Recompute the quality payload now that we have measured entropy
            quality = cand.get("quality") or {}
            # Use measured entropy as baseline to compute expected gain and ranking
            updated_quality = self.classifier.predict_quality(
                generation_time_ms=cand.get("time_ms", 0.0),
                shots_used=cand.get("key", {}).get("shots_per_chunk", cand.get("key", {}).get("shots", 0)),
                num_qubits=max(1, key_length // 16),
                bit_distribution=cand.get("fast_features", {}).get("bit_balance_ratio", 0.5),
                entropy_score=entropy_score,
            )
            cand["quality"] = updated_quality

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
        final_key["correction_timeout_hit"] = (time.perf_counter() - start_total) * 1000.0 >= effective_time_budget_ms
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
        max_wall_time_ms=7000,
        per_key_time_budget_ms=3000,
    ):
        """Run paired control/treated generation with identical settings."""
        samples = max(1, int(samples_per_variant))
        attempt_cap = max(1, int(max_attempts or self.max_attempts))
        start = time.perf_counter()
        executed_pairs = 0

        if reset_log and os.path.exists(self.ab_test_log_path):
            os.remove(self.ab_test_log_path)
            self._ensure_ab_test_file()

        for _ in range(samples):
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            if elapsed_ms >= float(max_wall_time_ms):
                break

            self.generate_with_quality_improvement(
                key_generator=key_generator,
                key_length=key_length,
                shots=shots,
                enable_correction=False,
                max_attempts=1,
                time_budget_ms=per_key_time_budget_ms,
            )
            self.generate_with_quality_improvement(
                key_generator=key_generator,
                key_length=key_length,
                shots=shots,
                enable_correction=True,
                max_attempts=attempt_cap,
                time_budget_ms=per_key_time_budget_ms,
            )
            executed_pairs += 1

        results = self.get_ab_test_results()
        results["strict_ab_run"] = {
            "samples_per_variant_requested": samples,
            "samples_per_variant_executed": int(executed_pairs),
            "settings": {
                "key_length": int(key_length),
                "shots": int(shots),
                "max_attempts": int(attempt_cap),
                "max_wall_time_ms": float(max_wall_time_ms),
                "per_key_time_budget_ms": float(per_key_time_budget_ms),
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

        try:
            df = pd.read_csv(self.ab_test_log_path)
        except Exception as exc:
            print(f"[ML Corrector] Failed reading A/B log, resetting file: {exc}")
            self._ensure_ab_test_file()
            return empty_payload
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
