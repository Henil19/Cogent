"""
Sub-Module 10.5: Evidence-Backed Failure Analyzer & Root Cause Diagnoser (GroUSE, Li et al.)
Diagnoses the exact culprit layer across the 9-layer stack using factual metrics,
telemetry footprints, and execution graph artifacts rather than unconstrained LLM guesses.
"""

from typing import List, Optional
from app.schemas.layer10 import (
    CogentExecutionTrace,
    EvaluationMetricsReport,
    UserFeedbackPayload,
    RootCauseDiagnosis,
    FailureCategory,
    FailureSeverity,
)
from app.core.layer10.diagnosis.failure_taxonomy import TAXONOMY_DESCRIPTIONS


class FailureAnalyzer:
    """
    Traverses the cognitive execution pipeline from L1 to L9 to isolate
    the origin point of factual, structural, or presentation defects.
    """

    def __init__(self):
        pass

    def diagnose_execution(
        self,
        trace: CogentExecutionTrace,
        eval_report: Optional[EvaluationMetricsReport] = None,
        feedbacks: Optional[List[UserFeedbackPayload]] = None
    ) -> RootCauseDiagnosis:
        """
        Executes a deterministic, evidence-backed diagnostic tree across all 9 layers.
        """
        l1_data = trace.layer1_input or {}
        l2_data = trace.layer2_plan or {}
        l3_data = trace.layer3_corpus_meta or {}
        l4_data = trace.layer4_retrieval_meta or {}
        l5_data = trace.layer5_evidence_meta or {}
        l6_data = trace.layer6_reasoning_meta or {}
        l7_data = trace.layer7_trust_meta or {}
        l8_data = trace.layer8_explanation_meta or {}
        l9_data = trace.layer9_response_payload or {}

        # 1. Check L9 Presentation Defects (Orphan citations, unrendered registry)
        citation_registry = l9_data.get("citation_registry", {})
        validation_report = l9_data.get("validation_report", {})
        orphan_citations = validation_report.get("orphan_citations", [])
        if eval_report and eval_report.evaluation_notes:
            orphan_citations = orphan_citations or [n for n in eval_report.evaluation_notes if "Orphan" in n]

        if orphan_citations:
            return RootCauseDiagnosis(
                execution_id=trace.execution_id,
                failed_layer_id=9,
                failure_category=FailureCategory.L9_PRESENTATION_INVARIANCE_FAILURE,
                severity=FailureSeverity.HIGH,
                root_cause_explanation=(
                    f"Layer 9 rendered orphan citation tags not backed by verified TROVE coordinates: "
                    f"{', '.join(orphan_citations)}"
                ),
                contributing_factors=["Citation token resolution mismatch", "Orphan citation tags in body text"],
                recommended_action="Update CitationRenderer regex and audit token mapping in ResponseGenerator."
            )

        # 2. Check L8 Explanation Fidelity Failure
        l8_val = l8_data.get("validation", {})
        l8_val_rep = l8_data.get("validation_report", {})
        if (isinstance(l8_val, dict) and l8_val.get("is_faithful") is False) or l8_val_rep.get("topological_inversions") or l8_data.get("is_fidelity_failure"):
            return RootCauseDiagnosis(
                execution_id=trace.execution_id,
                failed_layer_id=8,
                failure_category=FailureCategory.L8_EXPLANATION_FIDELITY_FAILURE,
                severity=FailureSeverity.HIGH,
                root_cause_explanation="Layer 8 explanation narrative failed fidelity gates or inverted reasoning DAG ordering.",
                contributing_factors=["Topological narrative inversion", "Unfaithful claim expansion in explanation"],
                recommended_action="Audit ExplanationGenerator topological walk and enforce strict DAG node alignment."
            )

        # 3. Check L7 Trust Miscalibration (Overconfidence when grounding is low)
        confidence = float(l7_data.get("overall_confidence", 0.75))
        grounding = eval_report.grounding_score if eval_report else 1.0
        hallucination = eval_report.hallucination_score if eval_report else 0.0

        if confidence >= 0.80 and grounding < 0.65:
            return RootCauseDiagnosis(
                execution_id=trace.execution_id,
                failed_layer_id=7,
                failure_category=FailureCategory.L7_TRUST_MISCALIBRATION,
                severity=FailureSeverity.HIGH,
                root_cause_explanation=(
                    f"Layer 7 assigned HIGH confidence ({confidence}) despite low empirical "
                    f"grounding ({grounding}) and elevated hallucination ({hallucination})."
                ),
                contributing_factors=["Overconfidence gap", "Heuristic trust overestimation in L7"],
                recommended_action="Trigger temperature recalibration and increase epistemic uncertainty penalty."
            )

        # 4. Check L6 Reasoning Gap (Unsound DAG or ungrounded deduction)
        reasoning_soundness = eval_report.reasoning_soundness_score if eval_report else 1.0
        if reasoning_soundness < 0.70:
            return RootCauseDiagnosis(
                execution_id=trace.execution_id,
                failed_layer_id=6,
                failure_category=FailureCategory.L6_REASONING_DEDUCTION_GAP,
                severity=FailureSeverity.HIGH,
                root_cause_explanation=(
                    f"Layer 6 synthesized claims with broken dependency links or missing premise nodes. "
                    f"Reasoning soundness score: {reasoning_soundness}."
                ),
                contributing_factors=["Broken DAG topological links", "Missing supporting premise steps"],
                recommended_action="Enforce strict topological premise validation in MultihopReasoningEngine."
            )

        # 5. Check L4 Retrieval Miss vs. L5 Verification Gap
        retrieved_candidates = (
            l4_data.get("total_candidates_returned", 0)
            or l4_data.get("total_candidates_found", 0)
            or len(l4_data.get("all_candidates", []))
            or len(l4_data.get("candidate_chunks", []))
        )
        selected_evidence = (
            len(l5_data.get("selected_evidence", []))
            or len(l5_data.get("verified_evidence", []))
            or l5_data.get("selected_evidence_count", 0)
            or l5_data.get("total_selected", 0)
        )

        if retrieved_candidates == 0 and not l4_data.get("is_empty_retrieval_intended", False):
            # Check if query required external retrieval
            sub_queries = l2_data.get("sub_queries", [])
            if sub_queries:
                return RootCauseDiagnosis(
                    execution_id=trace.execution_id,
                    failed_layer_id=4,
                    failure_category=FailureCategory.L4_RETRIEVAL_MISS,
                    severity=FailureSeverity.CRITICAL,
                    root_cause_explanation=(
                        f"Layer 4 failed to retrieve any candidate passages for query: '{trace.raw_query}'. "
                        f"Recall@K failure in hybrid vector/BM25 index."
                    ),
                    contributing_factors=["Index empty or vocabulary mismatch", "Dense embedding distance above threshold"],
                    recommended_action="Switch sub-query routing to LIVE_WEB or lower hybrid RRF rank cutoff."
                )

        if retrieved_candidates > 0 and selected_evidence == 0:
            return RootCauseDiagnosis(
                execution_id=trace.execution_id,
                failed_layer_id=5,
                failure_category=FailureCategory.L5_VERIFICATION_SELECTION_GAP,
                severity=FailureSeverity.HIGH,
                root_cause_explanation=(
                    f"Layer 4 retrieved {retrieved_candidates} candidates, but Layer 5 cross-encoder "
                    f"or NLI stance verifier rejected all candidates as irrelevant or unentailed."
                ),
                contributing_factors=["Cross-encoder relevance threshold too strict", "NLI entailment filter over-pruning"],
                recommended_action="Calibrate S2G-RAG coverage threshold and verify cross-encoder score normalization."
            )

        # 6. Check L2 Decomposition Failure (e.g. comparative query with only 1 sub-query)
        raw_q_lower = trace.raw_query.lower()
        sub_queries = l2_data.get("sub_queries", [])
        is_comparative = "compare" in raw_q_lower or "versus" in raw_q_lower or " vs " in raw_q_lower

        if (is_comparative and len(sub_queries) < 2) or l2_data.get("is_decomposition_failure"):
            return RootCauseDiagnosis(
                execution_id=trace.execution_id,
                failed_layer_id=2,
                failure_category=FailureCategory.L2_DECOMPOSITION_FAILURE,
                severity=FailureSeverity.MEDIUM,
                root_cause_explanation=(
                    f"Layer 2 failed to decompose comparative query into separate entity branches. "
                    f"Generated only {len(sub_queries)} sub-queries for query: '{trace.raw_query}'."
                ),
                contributing_factors=["Comparative DAG planner skipped entity splitting"],
                recommended_action="Update L2 decomposition policy to mandate multi-entity branching on comparative intents."
            )

        # 7. Check L3 Acquisition Failure
        extraction_failures = l3_data.get("extraction_failures", 0)
        docs_acquired = l3_data.get("documents_acquired", 1)
        if extraction_failures > 0 or docs_acquired == 0:
            return RootCauseDiagnosis(
                execution_id=trace.execution_id,
                failed_layer_id=3,
                failure_category=FailureCategory.L3_ACQUISITION_EXTRACTION_FAILURE,
                severity=FailureSeverity.MEDIUM,
                root_cause_explanation=f"Layer 3 encountered {extraction_failures} document extraction/parsing errors (acquired {docs_acquired} docs).",
                contributing_factors=["Document parser format error", "Unreadable text chunks"],
                recommended_action="Inspect document parser fallback and PDF text extractor."
            )

        # 8. Check L1 Ambiguity Misclassification
        ambiguity_rep = l1_data.get("ambiguity_report", {})
        ambiguity_score = ambiguity_rep.get("overall_ambiguity_score", 0.0) if isinstance(ambiguity_rep, dict) else 0.0
        if (ambiguity_score > 0.60 and not l1_data.get("was_clarified")) or l1_data.get("is_ambiguity_misclassification"):
            return RootCauseDiagnosis(
                execution_id=trace.execution_id,
                failed_layer_id=1,
                failure_category=FailureCategory.L1_AMBIGUITY_MISCLASSIFICATION,
                severity=FailureSeverity.MEDIUM,
                root_cause_explanation="Layer 1 failed to clarify an ambiguous query before routing to downstream planning.",
                contributing_factors=["Ambiguity score above threshold without user clarification", "Premature intent dispatch"],
                recommended_action="Enforce strict clarification threshold in AmbiguityEngine."
            )

        # 7. Check User Dispute from Feedback
        if feedbacks:
            disputes = [fb for fb in feedbacks if fb.feedback_type.value in ("THUMBS_DOWN", "CLAIM_FLAG", "FACT_CORRECTION")]
            if disputes and grounding < 0.75:
                first_disp = disputes[0]
                return RootCauseDiagnosis(
                    execution_id=trace.execution_id,
                    failed_layer_id=5,
                    failure_category=FailureCategory.L5_VERIFICATION_SELECTION_GAP,
                    severity=FailureSeverity.MEDIUM,
                    root_cause_explanation=(
                        f"User explicitly disputed factual claim '{first_disp.target_claim_id or 'statement'}'. "
                        f"Comment: '{first_disp.user_comment or 'Factual inaccuracy'}'. Grounding was {grounding}."
                    ),
                    evidence_ids=[first_disp.target_evidence_id] if first_disp.target_evidence_id else [],
                    contributing_factors=["User-flagged factual divergence", "Weak evidence support"],
                    recommended_action="Add to curated regression benchmark and review evidence verification threshold."
                )

        # Default: Clean execution
        return RootCauseDiagnosis(
            execution_id=trace.execution_id,
            failed_layer_id=None,
            failure_category=FailureCategory.NO_FAILURE_DETECTED,
            severity=FailureSeverity.LOW,
            root_cause_explanation=TAXONOMY_DESCRIPTIONS[FailureCategory.NO_FAILURE_DETECTED],
            recommended_action="No corrective action required. Eligible for Gold Evaluation benchmark."
        )
