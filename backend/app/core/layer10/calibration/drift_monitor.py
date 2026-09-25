"""
Sub-Module 10.4: Trust & Calibration Drift Monitor (SGIC, ACL 2025)
Monitors sliding-window calibration, calculates ECE and Brier score,
and detects epistemic drift relative to empirical baselines.
"""

from typing import List, Dict, Tuple, Optional
from app.schemas.layer10 import CalibrationDriftReport, CogentExecutionTrace, EvaluationMetricsReport
from app.core.layer10.calibration.ece import CalibrationCalculator


class CalibrationDriftMonitor:
    """
    Monitors reliability curves over rolling evaluation windows.
    Detects when trust estimations deviate significantly from observed accuracy.
    Uses configurable baseline-relative drift parameters rather than arbitrary hardcoded cutoffs.
    """

    def __init__(
        self,
        baseline_ece: float = 0.08,
        drift_threshold: float = 0.06,  # Allowable delta above baseline before drift alert
        window_size: int = 50
    ):
        self.baseline_ece = baseline_ece
        self.drift_threshold = drift_threshold
        self.window_size = window_size
        self._sample_buffer: List[Tuple[float, bool]] = []
        self._calculator = CalibrationCalculator(num_bins=10)

    def record_sample(self, confidence: float, is_correct: bool) -> None:
        """Records a single prediction confidence and its empirical evaluation outcome."""
        self._sample_buffer.append((confidence, is_correct))
        if len(self._sample_buffer) > self.window_size * 4:
            self._sample_buffer = self._sample_buffer[-self.window_size * 2:]

    def ingest_trace_evaluation(
        self,
        trace: CogentExecutionTrace,
        eval_report: EvaluationMetricsReport
    ) -> None:
        """Extracts confidence from Layer 7 and accuracy from post-hoc evaluation."""
        l7_data = trace.layer7_trust_meta or {}
        confidence = float(l7_data.get("overall_confidence", 0.75))
        # Binary correctness proxy: grounding >= 0.75 and hallucination <= 0.10
        is_correct = (eval_report.grounding_score >= 0.75 and eval_report.hallucination_score <= 0.10)
        self.record_sample(confidence, is_correct)

    def evaluate_drift(self) -> CalibrationDriftReport:
        """
        Computes current ECE and tests for drift relative to the configured baseline.
        Generates non-destructive temperature recalibration recommendations.
        """
        active_samples = self._sample_buffer[-self.window_size:] if self._sample_buffer else []
        sample_count = len(active_samples)

        if sample_count < 5:
            # Insufficient samples for statistically sound calibration
            return CalibrationDriftReport(
                evaluation_window_size=self.window_size,
                sample_count=sample_count,
                ece=round(self.baseline_ece, 4),
                brier_score=0.05,
                baseline_ece=self.baseline_ece,
                drift_threshold=self.drift_threshold,
                drift_detected=False,
                calibration_status="WARMING_UP_COLLECTING_SAMPLES",
            )

        ece, brier, bins, overconf, underconf = self._calculator.compute_ece_and_brier(active_samples)

        # Baseline-relative drift test: drift if ECE exceeds baseline by more than threshold
        drift_delta = ece - self.baseline_ece
        drift_detected = (drift_delta > self.drift_threshold)

        # Propose temperature scaling candidate (SGIC)
        # T > 1.0 reduces overconfidence; T < 1.0 boosts underconfidence
        recommended_temp = None
        if drift_detected and sample_count >= 10:
            avg_conf = sum(c for c, _ in active_samples) / sample_count
            avg_acc = sum(1 for _, corr in active_samples if corr) / sample_count
            if avg_acc > 0.05:
                raw_t = avg_conf / avg_acc
                recommended_temp = round(max(0.5, min(2.0, raw_t)), 2)
            else:
                recommended_temp = 2.0  # Max temperature dampening for complete overconfidence

        status = "DRIFT_DETECTED_RECALIBRATION_RECOMMENDED" if drift_detected else "CALIBRATED_HEALTHY"

        return CalibrationDriftReport(
            evaluation_window_size=self.window_size,
            sample_count=sample_count,
            ece=ece,
            brier_score=brier,
            baseline_ece=self.baseline_ece,
            drift_threshold=self.drift_threshold,
            drift_detected=drift_detected,
            overconfidence_gap=overconf,
            underconfidence_gap=underconf,
            reliability_bins=bins,
            recommended_temperature=recommended_temp,
            calibration_status=status,
        )
