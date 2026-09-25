"""
Sub-Module 10.3: Post-Hoc Multi-Gate Evaluation Engine (RAGEval, GaRAGe, GroUSE, Park et al.)
Coordinates factual, citation, reasoning, and alignment evaluation dimensions,
enforcing length regularization and unanswerability / abstention quality auditing.
"""

from typing import Dict, Any, Optional
from app.schemas.layer10 import CogentExecutionTrace, EvaluationMetricsReport
from app.core.layer10.evaluation.grounding_evaluator import GroundingEvaluator
from app.core.layer10.evaluation.citation_evaluator import CitationEvaluator
from app.core.layer10.evaluation.reasoning_evaluator import ReasoningEvaluator


class PostHocEvaluationEngine:
    """
    Central evaluation engine executing reference-free and reference-guided audits.
    Combines rule-based checks, NLI grounding, and structural reasoning integrity.
    """

    def __init__(self):
        self.grounding_evaluator = GroundingEvaluator()
        self.citation_evaluator = CitationEvaluator()
        self.reasoning_evaluator = ReasoningEvaluator()

    def evaluate_trace(
        self,
        trace: CogentExecutionTrace
    ) -> EvaluationMetricsReport:
        """Runs the complete multi-gate post-hoc evaluation suite on an execution trace."""
        l9_data = trace.layer9_response_payload or {}
        l8_data = trace.layer8_explanation_meta or {}
        l7_data = trace.layer7_trust_meta or {}
        l6_data = trace.layer6_reasoning_meta or {}
        l5_data = trace.layer5_evidence_meta or {}

        rendered_sections = l9_data.get("sections", [])
        citation_registry = l9_data.get("citation_registry", {})
        claims = l8_data.get("claim_explanations", []) or l6_data.get("synthesized_claims", [])
        conflicts = l8_data.get("conflict_explanations", []) or l5_data.get("conflict_clusters", [])

        evidence_items = (
            l5_data.get("selected_evidence", [])
            or l5_data.get("verified_evidence", [])
        )

        # 1. Grounding & Factual Consistency (RAGEval + GaRAGe)
        grounding_score, hallucination_score, completeness_score, irrelevance_score = (
            self.grounding_evaluator.evaluate_grounding(
                rendered_sections=rendered_sections,
                citation_registry=citation_registry,
                raw_query=trace.raw_query,
                evidence_items=evidence_items
            )
        )

        # 2. Citation Fidelity (CiteBench)
        citation_precision, citation_coverage, orphan_citations = (
            self.citation_evaluator.evaluate_citations(
                rendered_sections=rendered_sections,
                citation_registry=citation_registry,
                claims=claims
            )
        )

        # 3. Structural Reasoning & Dialectical Balance
        reasoning_soundness = self.reasoning_evaluator.evaluate_reasoning_soundness(l6_data)
        dialectical_balance = self.reasoning_evaluator.evaluate_dialectical_balance(conflicts, rendered_sections)

        # 4. Length-Regularized Quality (Park et al., ACL 2024)
        # Disentangle length from quality: penalize excessive word count if grounding is weak
        total_words = sum(
            len((sec.get("content_markdown", "") if isinstance(sec, dict) else getattr(sec, "content_markdown", "")).split())
            for sec in rendered_sections
        )
        if total_words > 1200 and grounding_score < 0.8:
            length_regularized_quality = max(0.2, grounding_score * 0.8)
        elif total_words < 100 and completeness_score < 0.6:
            length_regularized_quality = max(0.3, completeness_score)
        else:
            length_regularized_quality = min(1.0, (grounding_score * 0.6 + completeness_score * 0.4))

        # 5. Abstention / Unanswerability Quality (GaRAGe)
        # Check if the system correctly expressed calibrated uncertainty when evidence was scarce
        overall_confidence = l7_data.get("overall_confidence", 1.0)
        is_refusal_section = any(
            "insufficient" in (sec.get("content_markdown", "") if isinstance(sec, dict) else getattr(sec, "content_markdown", "")).lower() or
            "limited evidence" in (sec.get("content_markdown", "") if isinstance(sec, dict) else getattr(sec, "content_markdown", "")).lower()
            for sec in rendered_sections
        )

        if len(evidence_items) == 0 or overall_confidence < 0.4:
            # System should abstain or heavily hedge
            abstention_quality = 1.0 if (is_refusal_section or overall_confidence < 0.45) else 0.3
        else:
            abstention_quality = 1.0

        # Composite Score Synthesis
        composite_score = round(
            (
                grounding_score * 0.30 +
                completeness_score * 0.15 +
                citation_precision * 0.15 +
                citation_coverage * 0.10 +
                reasoning_soundness * 0.10 +
                dialectical_balance * 0.10 +
                abstention_quality * 0.10
            ) - (hallucination_score * 0.20 + irrelevance_score * 0.10),
            3
        )
        composite_score = max(0.0, min(1.0, composite_score))

        is_gold_candidate = (
            grounding_score >= 0.85 and
            citation_precision >= 0.90 and
            hallucination_score <= 0.05 and
            len(orphan_citations) == 0 and
            reasoning_soundness >= 0.85
        )

        notes = []
        if orphan_citations:
            notes.extend(orphan_citations)
        if hallucination_score > 0.15:
            notes.append(f"Elevated ungrounded assertion rate: {hallucination_score}")
        if dialectical_balance < 0.8:
            notes.append(f"Imbalanced dialectical coverage: {dialectical_balance}")

        return EvaluationMetricsReport(
            execution_id=trace.execution_id,
            completeness_score=completeness_score,
            hallucination_score=hallucination_score,
            irrelevance_score=irrelevance_score,
            grounding_score=grounding_score,
            citation_precision=citation_precision,
            citation_coverage=citation_coverage,
            reasoning_soundness_score=reasoning_soundness,
            dialectical_balance_score=dialectical_balance,
            length_regularized_quality_score=round(length_regularized_quality, 3),
            abstention_quality_score=round(abstention_quality, 3),
            composite_quality_score=composite_score,
            is_high_quality_gold_candidate=is_gold_candidate,
            evaluation_notes=notes,
        )
