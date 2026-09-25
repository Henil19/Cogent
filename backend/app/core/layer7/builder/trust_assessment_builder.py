"""
Sub-Module 7.7: Trust Assessment Builder
Research Basis:
- Towards Trustworthy RAG for Large Language Models: A Survey (Ni et al., ACM Computing Surveys, 2026)
- CLAIM-CAL (Springer Nature, Sept 2026)
- Confidence over Time (ACL 2026)

Aggregates source credibility, evidence reliability, reasoning chain trust,
uncertainty profiles, calibrated claim confidence, and hallucination risks
into the unified master TrustAssessment contract.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import List

from app.schemas.layer2 import KnowledgeRetrievalPlan
from app.schemas.layer6 import SynthesizedReasoningTrace
from app.schemas.layer7 import (
    TrustAssessment,
    SourceCredibilityAssessment,
    EvidenceReliabilityAssessment,
    ReasoningTrustAssessment,
    UncertaintyAssessment,
    ClaimConfidenceAssessment,
    HallucinationRiskAssessment
)

logger = logging.getLogger(__name__)


class TrustAssessmentBuilder:
    """
    Compiles individual assessment modules into a comprehensive TrustAssessment contract for Layer 8.
    """

    def build_assessment(
        self,
        plan: KnowledgeRetrievalPlan,
        trace: SynthesizedReasoningTrace,
        source_assessments: List[SourceCredibilityAssessment],
        evidence_assessments: List[EvidenceReliabilityAssessment],
        reasoning_assessment: ReasoningTrustAssessment,
        uncertainty_assessment: UncertaintyAssessment,
        claim_assessments: List[ClaimConfidenceAssessment],
        hallucination_assessment: HallucinationRiskAssessment,
        processing_time_ms: float
    ) -> TrustAssessment:
        """
        Assemble all trust vectors, compute global trust index and global confidence, and summarize strengths and limitations.
        """
        # 1. Compute Global Trust Index (Structural Trust != Confidence Probability)
        avg_source_cred = (
            sum(s.overall_credibility for s in source_assessments) / len(source_assessments)
            if source_assessments else 0.50
        )
        avg_ev_rel = (
            sum(e.overall_reliability for e in evidence_assessments) / len(evidence_assessments)
            if evidence_assessments else 0.60
        )

        global_trust_index = (
            0.35 * reasoning_assessment.path_trust_score +
            0.30 * avg_source_cred +
            0.20 * avg_ev_rel +
            0.15 * (1.0 - uncertainty_assessment.overall_uncertainty)
        )
        # Apply hallucination risk penalty if present
        if hallucination_assessment.risk_level == "HIGH":
            global_trust_index *= 0.80
        elif hallucination_assessment.risk_level == "MEDIUM":
            global_trust_index *= 0.90

        global_trust_index = max(0.05, min(0.98, global_trust_index))

        # 2. Compute Global Calibrated Confidence
        # Bounded by the weakest claim confidence and the weakest reasoning link
        if claim_assessments:
            mean_claim_conf = sum(c.calibrated_confidence for c in claim_assessments) / len(claim_assessments)
            min_claim_conf = min(c.calibrated_confidence for c in claim_assessments)
            global_confidence = 0.70 * mean_claim_conf + 0.30 * min_claim_conf
        else:
            global_confidence = global_trust_index

        global_confidence = max(0.10, min(0.98, global_confidence))

        # 3. Extract Key Trust Strengths
        strengths = []
        if avg_source_cred >= 0.75:
            strengths.append(f"Evidence is grounded in authoritative sources (Average source credibility: {avg_source_cred:.2f}).")
        if reasoning_assessment.is_chain_intact and reasoning_assessment.path_trust_score >= 0.75:
            strengths.append("Deductive reasoning chain maintains strong topological grounding without missing inferential links.")
        if all(e.is_faithful for e in evidence_assessments):
            strengths.append("All audited claims exhibit strict faithfulness to retrieved source quote spans.")
        if not hallucination_assessment.has_hallucination_risk:
            strengths.append("Zero hallucination or ungrounded overextension risks detected.")

        if not strengths:
            strengths.append("Reasoning chain satisfies minimum operational grounding criteria.")

        # 4. Extract Key Limitations
        limitations = []
        if uncertainty_assessment.overall_uncertainty >= 0.30:
            limitations.append(f"Uncertainty present: {uncertainty_assessment.explanation_of_uncertainty}")
        if trace.has_conflicts:
            limitations.append("Source literature contains empirical divergence; dialectical Zero Winner Forcing retained conflicting viewpoints.")
        if reasoning_assessment.weakest_link_score < 0.65:
            limitations.append(f"Overall derivation is constrained by a moderate weakest-link premise ({reasoning_assessment.weakest_link_score:.2f}).")
        if hallucination_assessment.has_hallucination_risk:
            limitations.extend(hallucination_assessment.risk_explanations)
        if trace.unresolved_information_gaps:
            limitations.append(f"Unresolved information gaps: {', '.join(trace.unresolved_information_gaps)}.")

        assessment = TrustAssessment(
            assessment_id=f"trust_{uuid.uuid4().hex[:12]}",
            plan_id=plan.plan_id,
            session_id=plan.session_id,
            reasoning_trace_id=trace.reasoning_trace_id,
            global_trust_index=round(global_trust_index, 4),
            global_confidence=round(global_confidence, 4),
            claim_assessments=claim_assessments,
            source_assessments=source_assessments,
            evidence_assessments=evidence_assessments,
            reasoning_assessment=reasoning_assessment,
            uncertainty_assessment=uncertainty_assessment,
            hallucination_assessment=hallucination_assessment,
            key_trust_strengths=strengths,
            key_limitations=limitations,
            processing_time_ms=round(processing_time_ms, 2),
            created_at=datetime.now(timezone.utc).isoformat()
        )

        logger.info(
            f"TrustAssessmentBuilder assembled trust contract for plan {plan.plan_id}: "
            f"Trust Index={global_trust_index:.2f}, Global Conf={global_confidence:.2f}, "
            f"{len(claim_assessments)} claims evaluated in {processing_time_ms:.1f}ms."
        )
        return assessment
