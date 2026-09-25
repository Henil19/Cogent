"""
Sub-Module 10.8: Reproducible A/B Experiment Manager (BERGEN, EMNLP 2024)
Executes controlled head-to-head comparisons between baseline and candidate configurations
before candidate learning signals are promoted to production configurations.
"""

from typing import List, Dict, Any, Optional
from app.schemas.layer10 import ExperimentRun, EvaluationMetricsReport


class ExperimentManager:
    """
    Manages reproducible experimentation between system configurations.
    Tests whether candidate policy adjustments (e.g., expanded RRF top-k,
    mandatory comparative decomposition) yield statistically meaningful improvements.
    """

    def __init__(self):
        self._experiments: Dict[str, ExperimentRun] = {}

    def run_ab_comparison(
        self,
        experiment_name: str,
        baseline_config_hash: str,
        candidate_config_hash: str,
        baseline_evaluations: List[EvaluationMetricsReport],
        candidate_evaluations: List[EvaluationMetricsReport],
        baseline_latencies: List[float],
        candidate_latencies: List[float],
    ) -> ExperimentRun:
        """
        Compares baseline and candidate evaluation batches, computing deltas.
        """
        sample_count = min(len(baseline_evaluations), len(candidate_evaluations))
        if sample_count == 0:
            return ExperimentRun(
                experiment_name=experiment_name,
                baseline_config_hash=baseline_config_hash,
                candidate_config_hash=candidate_config_hash,
                sample_queries_count=0,
                baseline_composite_score=0.0,
                candidate_composite_score=0.0,
                grounding_delta=0.0,
                latency_delta_ms=0.0,
                is_candidate_statistically_superior=False,
                status="FAILED_INSUFFICIENT_DATA"
            )

        base_comp = sum(e.composite_quality_score for e in baseline_evaluations[:sample_count]) / sample_count
        cand_comp = sum(e.composite_quality_score for e in candidate_evaluations[:sample_count]) / sample_count

        base_grounding = sum(e.grounding_score for e in baseline_evaluations[:sample_count]) / sample_count
        cand_grounding = sum(e.grounding_score for e in candidate_evaluations[:sample_count]) / sample_count

        base_lat = sum(baseline_latencies[:sample_count]) / sample_count if baseline_latencies else 0.0
        cand_lat = sum(candidate_latencies[:sample_count]) / sample_count if candidate_latencies else 0.0

        comp_delta = round(cand_comp - base_comp, 3)
        grounding_delta = round(cand_grounding - base_grounding, 3)
        latency_delta = round(cand_lat - base_lat, 1)

        # Candidate is superior if composite score improves by >= 0.02 and grounding does not degrade
        is_superior = (comp_delta >= 0.02 and grounding_delta >= -0.01)

        run = ExperimentRun(
            experiment_name=experiment_name,
            baseline_config_hash=baseline_config_hash,
            candidate_config_hash=candidate_config_hash,
            sample_queries_count=sample_count,
            baseline_composite_score=round(base_comp, 3),
            candidate_composite_score=round(cand_comp, 3),
            grounding_delta=grounding_delta,
            latency_delta_ms=latency_delta,
            is_candidate_statistically_superior=is_superior,
            status="COMPLETED"
        )
        self._experiments[run.experiment_id] = run
        return run

    def get_experiment(self, experiment_id: str) -> Optional[ExperimentRun]:
        """Retrieves an experiment run by its ID."""
        return self._experiments.get(experiment_id)

    def list_experiments(self) -> List[ExperimentRun]:
        """Returns all completed experiment runs."""
        return list(self._experiments.values())
