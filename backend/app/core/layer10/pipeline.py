"""
Cogent Layer 10 Master Pipeline Orchestrator
Coordinates post-execution observation, multi-gate evaluation, calibration drift monitoring,
evidence-backed failure diagnosis, adaptive policy signal generation, and dataset curation.
Strictly enforces the Zero Epistemic Mutation invariant.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.schemas.layer10 import (
    CogentExecutionTrace,
    EvaluationMetricsReport,
    CalibrationDriftReport,
    RootCauseDiagnosis,
    LearningSignal,
    UserFeedbackPayload,
    Layer10AnalyticsOverview,
    DatasetCuratorExport,
    ExperimentRun,
    Layer10Response,
)
from app.core.layer10.telemetry.collector import CognitiveTelemetryCollector
from app.core.layer10.feedback.feedback_aggregator import UserFeedbackAggregator
from app.core.layer10.evaluation.evaluation_engine import PostHocEvaluationEngine
from app.core.layer10.calibration.drift_monitor import CalibrationDriftMonitor
from app.core.layer10.diagnosis.failure_analyzer import FailureAnalyzer
from app.core.layer10.optimization.policy_optimizer import AdaptivePolicyOptimizationEngine
from app.core.layer10.datasets.dataset_curator import DatasetCuratorEngine
from app.core.layer10.experimentation.analytics_engine import SystemAnalyticsEngine
from app.core.layer10.experimentation.experiment_manager import ExperimentManager


class Layer10Pipeline:
    """
    Master pipeline executing the Cogent Layer 10 continuous learning loop:
    Observe -> Evaluate -> Diagnose -> Learn -> Experiment.
    """

    def __init__(
        self,
        baseline_ece: float = 0.08,
        drift_threshold: float = 0.06,
        calibration_window_size: int = 50
    ):
        self.collector = CognitiveTelemetryCollector()
        self.feedback_aggregator = UserFeedbackAggregator()
        self.evaluator = PostHocEvaluationEngine()
        self.calibration_monitor = CalibrationDriftMonitor(
            baseline_ece=baseline_ece,
            drift_threshold=drift_threshold,
            window_size=calibration_window_size
        )
        self.failure_analyzer = FailureAnalyzer()
        self.policy_optimizer = AdaptivePolicyOptimizationEngine()
        self.dataset_curator = DatasetCuratorEngine()
        self.analytics_engine = SystemAnalyticsEngine()
        self.experiment_manager = ExperimentManager()

        # In-memory stores for fast analysis
        self._evaluations: Dict[str, EvaluationMetricsReport] = {}
        self._diagnoses: Dict[str, RootCauseDiagnosis] = {}

    def process_execution(
        self,
        trace: CogentExecutionTrace,
        include_failure_diagnosis: bool = True,
        include_evaluation: bool = True,
        include_learning_signals: bool = True
    ) -> Layer10Response:
        """
        Executes complete post-hoc analysis on an execution trace.
        Guarantees Zero Epistemic Mutation on trace artifacts.
        """
        # 1. Finalize trace in collector if not already finalized
        self.collector._traces[trace.execution_id] = trace
        if not trace.completed_at:
            trace = self.collector.finalize_trace(trace.execution_id) or trace

        eval_report: Optional[EvaluationMetricsReport] = None
        if include_evaluation:
            eval_report = self.evaluator.evaluate_trace(trace)
            self._evaluations[trace.execution_id] = eval_report

            # 2. Update calibration drift monitor
            self.calibration_monitor.ingest_trace_evaluation(trace, eval_report)

        # 3. Retrieve any associated feedback
        feedbacks = self.feedback_aggregator.get_feedback_for_execution(trace.execution_id)

        diagnosis: Optional[RootCauseDiagnosis] = None
        if include_failure_diagnosis:
            diagnosis = self.failure_analyzer.diagnose_execution(
                trace=trace,
                eval_report=eval_report,
                feedbacks=feedbacks
            )
            self._diagnoses[trace.execution_id] = diagnosis

        # 4. Generate candidate learning signals if failure or opportunity detected
        signals: List[LearningSignal] = []
        if include_learning_signals and diagnosis:
            signals = self.policy_optimizer.generate_learning_signals(
                trace=trace,
                diagnosis=diagnosis,
                eval_report=eval_report
            )

        # 5. Ingest into Dataset Curator
        if eval_report and diagnosis:
            self.dataset_curator.ingest_trace(
                trace=trace,
                eval_report=eval_report,
                diagnosis=diagnosis
            )

        cal_report = self.calibration_monitor.evaluate_drift()

        return Layer10Response(
            status="SUCCESS",
            execution_id=trace.execution_id,
            evaluation_report=eval_report,
            calibration_report=cal_report,
            failure_diagnosis=diagnosis,
            learning_signals=signals,
            processed_at=datetime.now(timezone.utc).isoformat()
        )

    def record_user_feedback(
        self,
        feedback: UserFeedbackPayload
    ) -> UserFeedbackPayload:
        """Records explicit or implicit feedback and maps attribution."""
        trace = self.collector.get_trace(feedback.execution_id)
        enriched = self.feedback_aggregator.record_feedback(feedback, trace)

        # If feedback is a dispute, update failure diagnosis if trace exists
        if trace and feedback.feedback_type.value in ("THUMBS_DOWN", "CLAIM_FLAG", "FACT_CORRECTION"):
            eval_report = self._evaluations.get(trace.execution_id)
            new_diag = self.failure_analyzer.diagnose_execution(
                trace=trace,
                eval_report=eval_report,
                feedbacks=self.feedback_aggregator.get_feedback_for_execution(trace.execution_id)
            )
            self._diagnoses[trace.execution_id] = new_diag
            self.policy_optimizer.generate_learning_signals(trace, new_diag, eval_report)

        return enriched

    def get_analytics_overview(self) -> Layer10AnalyticsOverview:
        """Calculates global operational KPIs across all traces."""
        traces = self.collector.list_recent_traces(limit=200)
        evals = list(self._evaluations.values())
        diags = list(self._diagnoses.values())
        cal_report = self.calibration_monitor.evaluate_drift()
        active_signals = self.policy_optimizer.list_active_signals()
        bundle = self.dataset_curator.export_curated_bundle()

        return self.analytics_engine.compute_overview(
            traces=traces,
            evaluations=evals,
            calibration_report=cal_report,
            diagnoses=diags,
            learning_signals_count=len(active_signals),
            dpo_pairs_count=len(bundle.dpo_pairs),
        )

    def get_calibration_report(self) -> CalibrationDriftReport:
        """Returns empirical calibration and ECE report."""
        return self.calibration_monitor.evaluate_drift()

    def export_curated_datasets(self) -> DatasetCuratorExport:
        """Exports accumulated Gold, DPO, and Regression datasets."""
        return self.dataset_curator.export_curated_bundle()

    def run_ab_experiment(
        self,
        experiment_name: str,
        baseline_config_hash: str,
        candidate_config_hash: str,
        baseline_evaluations: List[EvaluationMetricsReport],
        candidate_evaluations: List[EvaluationMetricsReport],
        baseline_latencies: List[float],
        candidate_latencies: List[float],
    ) -> ExperimentRun:
        """Executes a controlled A/B comparison per BERGEN guidelines."""
        return self.experiment_manager.run_ab_comparison(
            experiment_name=experiment_name,
            baseline_config_hash=baseline_config_hash,
            candidate_config_hash=candidate_config_hash,
            baseline_evaluations=baseline_evaluations,
            candidate_evaluations=candidate_evaluations,
            baseline_latencies=baseline_latencies,
            candidate_latencies=candidate_latencies,
        )


# Global singleton instance for application use
layer10_pipeline = Layer10Pipeline()
