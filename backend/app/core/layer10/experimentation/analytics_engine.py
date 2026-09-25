"""
Sub-Module 10.8: System Analytics & KPI Aggregator
Calculates global performance metrics, grounding ratios, latency profiles,
and failure category distributions for executive monitoring.
"""

from typing import List, Dict, Any
from app.schemas.layer10 import (
    Layer10AnalyticsOverview,
    EvaluationMetricsReport,
    CalibrationDriftReport,
    RootCauseDiagnosis,
    CogentExecutionTrace,
)


class SystemAnalyticsEngine:
    """Aggregates high-level telemetry and KPI statistics across all executed traces."""

    def __init__(self):
        pass

    def compute_overview(
        self,
        traces: List[CogentExecutionTrace],
        evaluations: List[EvaluationMetricsReport],
        calibration_report: CalibrationDriftReport,
        diagnoses: List[RootCauseDiagnosis],
        learning_signals_count: int = 0,
        dpo_pairs_count: int = 0
    ) -> Layer10AnalyticsOverview:
        """Assembles executive analytics dashboard data."""
        total = len(traces)
        if total == 0:
            return Layer10AnalyticsOverview()

        mean_grounding = (
            sum(e.grounding_score for e in evaluations) / len(evaluations)
            if evaluations else 0.0
        )
        mean_citation_prec = (
            sum(e.citation_precision for e in evaluations) / len(evaluations)
            if evaluations else 0.0
        )
        mean_latency = (
            sum(t.total_latency_ms for t in traces) / total
        )

        failure_counts: Dict[str, int] = {}
        for d in diagnoses:
            cat = d.failure_category.value
            failure_counts[cat] = failure_counts.get(cat, 0) + 1

        return Layer10AnalyticsOverview(
            total_executions=total,
            mean_grounding_score=round(mean_grounding, 3),
            mean_citation_precision=round(mean_citation_prec, 3),
            mean_latency_ms=round(mean_latency, 1),
            current_ece=calibration_report.ece,
            calibration_status=calibration_report.calibration_status,
            active_learning_signals_count=learning_signals_count,
            curated_dpo_pairs_count=dpo_pairs_count,
            top_failure_categories=failure_counts,
        )
