"""
Sub-Module 10.6: Adaptive Policy & Optimization Engine (BERGEN, EMNLP 2024)
Evaluates execution history and failure diagnoses to generate structured learning signals.
Recommends controlled policy updates for L2 routing, L4 retrieval strategies (dense/sparse/hybrid RRF),
L7 calibration vectors, and L8/L9 presentation modes without unconstrained weight drift.
"""

from typing import List, Dict, Any, Optional
from app.schemas.layer10 import (
    CogentExecutionTrace,
    EvaluationMetricsReport,
    RootCauseDiagnosis,
    LearningSignal,
    LearningSignalType,
    FailureCategory,
)


class AdaptivePolicyOptimizationEngine:
    """
    Synthesizes actionable, validated learning proposals targeting upstream layers.
    Does not apply automatic runtime mutation; produces candidate configurations for offline validation.
    """

    def __init__(self):
        self._learning_signals: List[LearningSignal] = []

    def generate_learning_signals(
        self,
        trace: CogentExecutionTrace,
        diagnosis: RootCauseDiagnosis,
        eval_report: Optional[EvaluationMetricsReport] = None
    ) -> List[LearningSignal]:
        """
        Analyzes diagnosed failure points and evaluation metrics to produce
        targeted learning signals for upstream pipeline optimization.
        """
        signals: List[LearningSignal] = []

        # 1. L4 Retrieval Policy Recommendation
        if diagnosis.failure_category == FailureCategory.L4_RETRIEVAL_MISS:
            signals.append(
                LearningSignal(
                    source_execution_ids=[trace.execution_id],
                    target_layer=4,
                    target_component="HybridRetrievalStrategy",
                    signal_type=LearningSignalType.L4_RETRIEVAL_POLICY_ADAPTATION,
                    observed_pattern=f"Hybrid retrieval missed relevant candidates for query '{trace.raw_query}'",
                    supporting_metrics={
                        "total_candidates_found": 0,
                        "query": trace.raw_query,
                    },
                    recommended_change={
                        "retrieval_policy": "HYBRID_RRF_EXPANDED_TOP_K",
                        "suggested_top_k": 20,
                        "fallback_channel": "LIVE_WEB_SEARCH",
                    },
                    validation_status="PENDING_OFFLINE_VALIDATION"
                )
            )

        # 2. L2 Query Decomposition Recommendation
        if diagnosis.failure_category == FailureCategory.L2_DECOMPOSITION_FAILURE:
            signals.append(
                LearningSignal(
                    source_execution_ids=[trace.execution_id],
                    target_layer=2,
                    target_component="QueryDecompositionEngine",
                    signal_type=LearningSignalType.L2_ROUTING_OPTIMIZATION,
                    observed_pattern=f"Comparative query generated insufficient sub-queries",
                    supporting_metrics={
                        "sub_query_count": len(trace.layer2_plan.get("sub_queries", [])) if trace.layer2_plan else 1,
                        "query": trace.raw_query,
                    },
                    recommended_change={
                        "decomposition_policy": "MANDATORY_MULTI_ENTITY_BRANCHING",
                        "min_sub_queries": 2,
                        "source_routing_prior": "HYBRID",
                    },
                    validation_status="PENDING_OFFLINE_VALIDATION"
                )
            )

        # 3. L7 Calibration Reweighting Recommendation
        if diagnosis.failure_category == FailureCategory.L7_TRUST_MISCALIBRATION:
            signals.append(
                LearningSignal(
                    source_execution_ids=[trace.execution_id],
                    target_layer=7,
                    target_component="ConfidenceCalibrationEngine",
                    signal_type=LearningSignalType.L7_CALIBRATION_REWEIGHTING,
                    observed_pattern="Severe overconfidence gap detected between L7 trust and empirical grounding",
                    supporting_metrics={
                        "confidence": trace.layer7_trust_meta.get("overall_confidence", 0.8) if trace.layer7_trust_meta else 0.8,
                        "grounding_score": eval_report.grounding_score if eval_report else 0.5,
                    },
                    recommended_change={
                        "temperature_scaling_proposal": 1.25,
                        "increase_epistemic_penalty_weight": 0.15,
                    },
                    validation_status="PENDING_OFFLINE_VALIDATION"
                )
            )

        # 4. L8/L9 Presentation Policy Adaptation (when audience switching frequency is high)
        l9_data = trace.layer9_response_payload or {}
        if eval_report and eval_report.length_regularized_quality_score < 0.7:
            signals.append(
                LearningSignal(
                    source_execution_ids=[trace.execution_id],
                    target_layer=9,
                    target_component="ResponseGenerator",
                    signal_type=LearningSignalType.L8_L9_PRESENTATION_POLICY_ADAPTATION,
                    observed_pattern="Response penalized for low grounding relative to length",
                    supporting_metrics={
                        "length_regularized_score": eval_report.length_regularized_quality_score,
                    },
                    recommended_change={
                        "conciseness_regularization": True,
                        "max_paragraph_length": 150,
                    },
                    validation_status="PENDING_OFFLINE_VALIDATION"
                )
            )

        for sig in signals:
            self._learning_signals.append(sig)

        return signals

    def list_active_signals(self) -> List[LearningSignal]:
        """Returns all collected learning signals pending offline validation."""
        return list(self._learning_signals)
