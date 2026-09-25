"""
Sub-Module 10.7: Curated Dataset & Benchmark Synthesizer
Packages high-trust executions into Gold Benchmarks, failure traces into Error Records,
and diagnosed issues into Automated Regression Test Cases for continuous verification.
"""

from typing import List, Dict, Any, Optional
from app.schemas.layer10 import (
    CogentExecutionTrace,
    EvaluationMetricsReport,
    RootCauseDiagnosis,
    DPOPreferencePair,
    RegressionTestCase,
    DatasetCuratorExport,
    FailureCategory,
)
from app.core.layer10.datasets.preference_builder import PreferencePairBuilder


class DatasetCuratorEngine:
    """
    Curates ML evaluation and alignment datasets from live execution telemetry.
    Strictly separates dataset creation from production model fine-tuning.
    """

    def __init__(self):
        self.preference_builder = PreferencePairBuilder()
        self._gold_traces: List[CogentExecutionTrace] = []
        self._dpo_pairs: List[DPOPreferencePair] = []
        self._regression_cases: List[RegressionTestCase] = []

    def ingest_trace(
        self,
        trace: CogentExecutionTrace,
        eval_report: EvaluationMetricsReport,
        diagnosis: RootCauseDiagnosis
    ) -> None:
        """Categorizes and curates an execution trace into the appropriate dataset track."""
        # 1. Gold benchmark candidate track
        if eval_report.is_high_quality_gold_candidate and diagnosis.failure_category == FailureCategory.NO_FAILURE_DETECTED:
            self._gold_traces.append(trace)

        # 2. Diagnosed failure track -> create DPO pair and Regression Test Case
        if diagnosis.failure_category != FailureCategory.NO_FAILURE_DETECTED:
            dpo_pair = self.preference_builder.synthesize_pair_from_failure(trace, eval_report, diagnosis)
            if dpo_pair:
                self._dpo_pairs.append(dpo_pair)

            # Generate regression test case
            l1_data = trace.layer1_input or {}
            intent = l1_data.get("intent", "FACTUAL")
            reg_case = RegressionTestCase(
                query=trace.raw_query,
                expected_intent=str(intent),
                minimum_grounding_score=0.80,
                created_from_execution_id=trace.execution_id,
            )
            self._regression_cases.append(reg_case)

    def export_curated_bundle(self) -> DatasetCuratorExport:
        """Exports the accumulated curated datasets."""
        return DatasetCuratorExport(
            gold_records_count=len(self._gold_traces),
            dpo_pairs=list(self._dpo_pairs),
            regression_tests=list(self._regression_cases),
        )
