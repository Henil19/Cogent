"""
Sub-Module 10.4: Expected Calibration Error & Brier Score Calculator (SGIC, ACL 2025)
Computes empirical ECE, Brier score, and reliability diagram bins across confidence intervals.
"""

from typing import List, Dict, Any, Tuple
from app.schemas.layer10 import CalibrationBin


class CalibrationCalculator:
    """
    Evaluates how closely predicted confidence corresponds to empirical accuracy.
    Groups predictions into M=10 equidistant confidence bins.
    """

    def __init__(self, num_bins: int = 10):
        self.num_bins = num_bins

    def compute_ece_and_brier(
        self,
        predictions: List[Tuple[float, bool]]
    ) -> Tuple[float, float, List[CalibrationBin], float, float]:
        """
        Args:
            predictions: List of (predicted_confidence, is_correct) tuples.
        Returns:
            (ece, brier_score, bins, overconfidence_gap, underconfidence_gap)
        """
        if not predictions:
            return 0.0, 0.0, [], 0.0, 0.0

        n = len(predictions)
        bins_data: List[List[Tuple[float, bool]]] = [[] for _ in range(self.num_bins)]

        total_squared_error = 0.0
        for conf, correct in predictions:
            total_squared_error += (conf - (1.0 if correct else 0.0)) ** 2
            # Determine bin index [0, num_bins-1]
            bin_idx = min(self.num_bins - 1, int(conf * self.num_bins))
            bins_data[bin_idx].append((conf, correct))

        brier_score = round(total_squared_error / n, 4)

        ece = 0.0
        overconfidence_gap = 0.0
        underconfidence_gap = 0.0
        calibration_bins: List[CalibrationBin] = []

        for i in range(self.num_bins):
            bin_items = bins_data[i]
            lower = i / self.num_bins
            upper = (i + 1) / self.num_bins

            if not bin_items:
                calibration_bins.append(
                    CalibrationBin(
                        bin_index=i,
                        confidence_lower=round(lower, 2),
                        confidence_upper=round(upper, 2),
                        average_confidence=round((lower + upper) / 2.0, 2),
                        empirical_accuracy=0.0,
                        sample_count=0
                    )
                )
                continue

            bin_size = len(bin_items)
            avg_conf = sum(c for c, _ in bin_items) / bin_size
            acc = sum(1 for _, corr in bin_items if corr) / bin_size

            gap = abs(acc - avg_conf)
            ece += (bin_size / n) * gap

            if avg_conf > acc:
                overconfidence_gap = max(overconfidence_gap, avg_conf - acc)
            else:
                underconfidence_gap = max(underconfidence_gap, acc - avg_conf)

            calibration_bins.append(
                CalibrationBin(
                    bin_index=i,
                    confidence_lower=round(lower, 2),
                    confidence_upper=round(upper, 2),
                    average_confidence=round(avg_conf, 4),
                    empirical_accuracy=round(acc, 4),
                    sample_count=bin_size
                )
            )

        return (
            round(ece, 4),
            brier_score,
            calibration_bins,
            round(overconfidence_gap, 4),
            round(underconfidence_gap, 4)
        )
