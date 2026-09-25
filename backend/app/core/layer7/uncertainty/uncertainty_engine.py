"""
Sub-Module 7.4: Uncertainty & Epistemic Risk Engine
Research Basis:
- FRANQ: Faithfulness-Aware Uncertainty Quantification for Fact-Checking RAG (Findings ACL 2026)
- S2G-RAG: Structured Sufficiency and Gap Judging for Iterative RAG (ACL 2026)
- A Survey of Confidence Estimation and Calibration in LLMs (Geng et al., NAACL 2024)

Tracks five separate uncertainty components without assuming mathematical independence:
coverage, conflict, source, reasoning, and temporal staleness.
Separates reducible epistemic uncertainty from observed outcome variability.
"""

import logging
from typing import List

from app.schemas.layer2 import KnowledgeRetrievalPlan
from app.schemas.layer5 import VerifiedEvidenceSet
from app.schemas.layer6 import SynthesizedReasoningTrace
from app.schemas.layer7 import (
    UncertaintyCategory,
    UncertaintyAssessment,
    SourceCredibilityAssessment,
    ReasoningTrustAssessment
)

logger = logging.getLogger(__name__)


class UncertaintyEngine:
    """
    Decomposes and assesses distinct epistemic and observed uncertainty drivers.
    """

    def assess_uncertainty(
        self,
        trace: SynthesizedReasoningTrace,
        evidence_set: VerifiedEvidenceSet,
        plan: KnowledgeRetrievalPlan,
        source_assessments: List[SourceCredibilityAssessment],
        reasoning_assessment: ReasoningTrustAssessment
    ) -> UncertaintyAssessment:
        """
        Evaluate coverage, conflict, source reliability, and reasoning chain depth.
        """
        active_uncertainties: List[UncertaintyCategory] = []
        explanation_parts: List[str] = []

        # 1. Coverage Deficit (Epistemic Gap)
        coverage_ratio = evidence_set.overall_coverage_ratio
        u_coverage = max(0.0, 1.0 - coverage_ratio)
        if evidence_set.unresolved_information_gaps or coverage_ratio < 0.80:
            active_uncertainties.append(UncertaintyCategory.INSUFFICIENT_EVIDENCE)
            gaps = ", ".join(f"'{g}'" for g in evidence_set.unresolved_information_gaps[:2])
            explanation_parts.append(f"Incomplete evidence coverage ({coverage_ratio:.0%}); missing data on {gaps or 'uncovered aspects'}.")

        # 2. Conflict Tension (Observed Discrepancy)
        u_conflict = 0.0
        if evidence_set.has_conflicts:
            total_conflicts = len(evidence_set.conflict_edges)
            reconciled = len([
                r for r in trace.conflict_reconciliations
                if r.resolution_status.value in ["RECONCILED", "CONTEXTUAL_DIFFERENCE", "TEMPORAL_SUPERSEDENCE"]
            ])
            u_conflict = (total_conflicts - reconciled) / (total_conflicts + 1.0)
            active_uncertainties.append(UncertaintyCategory.CONFLICTING_EVIDENCE)
            explanation_parts.append(f"Empirical conflict detected across {total_conflicts} source pair(s).")

        # 3. Source Credibility Deficit
        avg_cred = (
            sum(s.overall_credibility for s in source_assessments) / len(source_assessments)
            if source_assessments else 0.50
        )
        u_source = max(0.0, 1.0 - avg_cred)
        if avg_cred < 0.65:
            active_uncertainties.append(UncertaintyCategory.WEAK_SOURCE)
            explanation_parts.append(f"Moderate source authority (average credibility: {avg_cred:.2f}).")

        # 4. Reasoning Chain Vulnerability
        u_reasoning = max(0.0, 1.0 - reasoning_assessment.path_trust_score)
        if trace.integrity_metrics.logical_chain_depth >= 3:
            active_uncertainties.append(UncertaintyCategory.LONG_REASONING_CHAIN)
            explanation_parts.append(f"Multi-step inference depth ({trace.integrity_metrics.logical_chain_depth} hops) accumulates structural risk.")
        if reasoning_assessment.weakest_link_score < 0.60:
            active_uncertainties.append(UncertaintyCategory.MISSING_PREMISE)
            explanation_parts.append(f"Weakest derivation premise has low confidence ({reasoning_assessment.weakest_link_score:.2f}).")

        # 5. Temporal Staleness
        avg_recency = (
            sum(s.recency_score for s in source_assessments) / len(source_assessments)
            if source_assessments else 0.70
        )
        u_temporal = max(0.0, 1.0 - avg_recency)
        if avg_recency < 0.60:
            active_uncertainties.append(UncertaintyCategory.OUTDATED_EVIDENCE)
            explanation_parts.append(f"Evidence exhibits temporal staleness (recency score: {avg_recency:.2f}).")

        # Composite Aggregate Uncertainty
        composite_u = (
            0.30 * u_coverage +
            0.25 * u_conflict +
            0.20 * u_source +
            0.15 * u_reasoning +
            0.10 * u_temporal
        )
        overall_uncertainty = max(0.0, min(1.0, composite_u))

        # Epistemic vs Aleatoric decomposition:
        # Epistemic = coverage + weak sources + reasoning gaps (reducible by gathering more data)
        # Aleatoric / Observed variability = conflict + temporal changes (empirical variance between studies)
        epistemic_sum = u_coverage + u_source + u_reasoning
        aleatoric_sum = u_conflict + u_temporal
        total_sum = epistemic_sum + aleatoric_sum
        
        if total_sum > 0:
            epistemic_ratio = epistemic_sum / total_sum
            aleatoric_ratio = aleatoric_sum / total_sum
        else:
            epistemic_ratio = 0.50
            aleatoric_ratio = 0.50

        if not explanation_parts:
            explanation_str = "Evidence and reasoning chain exhibit high completeness, strong source agreement, and minimal uncertainty."
        else:
            explanation_str = " ".join(explanation_parts)

        assessment = UncertaintyAssessment(
            overall_uncertainty=round(overall_uncertainty, 4),
            active_uncertainties=active_uncertainties,
            epistemic_uncertainty_ratio=round(epistemic_ratio, 4),
            aleatoric_uncertainty_ratio=round(aleatoric_ratio, 4),
            explanation_of_uncertainty=explanation_str
        )

        logger.debug(f"UncertaintyEngine overall uncertainty: {overall_uncertainty:.2f} (Epistemic: {epistemic_ratio:.0%}, Aleatoric: {aleatoric_ratio:.0%})")
        return assessment
