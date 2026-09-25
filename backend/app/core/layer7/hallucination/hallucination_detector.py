"""
Sub-Module 7.6: Hallucination & Unsupported-Claim Risk Detector
Research Basis:
- RAGTruth: A Hallucination Corpus for Developing Trustworthy RAG Models (Niu et al., ACL 2024)
- Evidence-Aligned Entity Verification for Hallucination Detection in RAG (Jia et al., Findings ACL 2026)
- Assessing the Reasoning Capabilities of LLMs in Evidence-Based Claim Verification (RECV, ACL 2025)

Audits synthesized claims against underlying evidence to detect scope overextensions,
unsupported universal generalizations, entity misattributions, and reasoning leaps.
"""

import re
import logging
from typing import List

from app.schemas.layer5 import VerifiedEvidenceSet
from app.schemas.layer6 import SynthesizedReasoningTrace, SynthesizedClaim, ReasoningStepType
from app.schemas.layer7 import HallucinationRiskType, HallucinationRiskAssessment

logger = logging.getLogger(__name__)

# Linguistic patterns indicative of scope overextension when evidence is narrow
UNIVERSAL_GENERALIZATION_PATTERNS = [
    r"\balways\b",
    r"\buniversally\b",
    r"\bproves definitively\b",
    r"\bcompletely outperforms\b",
    r"\bin all cases\b",
    r"\bindisputable\b",
    r"\bflawless\b"
]


class HallucinationDetector:
    """
    Detects ungrounded inferences, scope mismatches, and evidence overextensions.
    """

    def audit_hallucination_risk(
        self,
        trace: SynthesizedReasoningTrace,
        evidence_set: VerifiedEvidenceSet
    ) -> HallucinationRiskAssessment:
        """
        Scan all synthesized claims and reasoning steps for hallucination failure modes.
        """
        detected_risks: List[HallucinationRiskType] = []
        risk_explanations: List[str] = []

        all_evidence_text = " ".join(ev.content for ev in evidence_set.selected_evidence).lower()

        # 1. Check for Unsupported Generalizations (RECV 2025, RAGTruth 2024)
        for claim in trace.synthesized_claims:
            claim_lower = claim.statement.lower()
            for pat in UNIVERSAL_GENERALIZATION_PATTERNS:
                if re.search(pat, claim_lower):
                    # Check if evidence actually contains absolute proof words
                    if not re.search(pat, all_evidence_text):
                        if HallucinationRiskType.UNSUPPORTED_GENERALIZATION not in detected_risks:
                            detected_risks.append(HallucinationRiskType.UNSUPPORTED_GENERALIZATION)
                        risk_explanations.append(
                            f"Claim '{claim.statement[:65]}...' asserts an absolute universal quantifier matching '{pat.strip(r'\b')}', "
                            "which is ungrounded in the narrow empirical benchmark evidence."
                        )

        # 2. Check for Reasoning Leaps (RLSeek 2026)
        # Any non-hedge step with grounding < 0.40 that feeds into a final conclusion
        for step in trace.reasoning_steps:
            if step.step_type not in (ReasoningStepType.EPISTEMIC_HEDGE, ReasoningStepType.CONFLICT_RECONCILIATION):
                if step.step_grounding_score < 0.35:
                    if HallucinationRiskType.REASONING_LEAP not in detected_risks:
                        detected_risks.append(HallucinationRiskType.REASONING_LEAP)
                    risk_explanations.append(
                        f"Reasoning step '{step.step_id}' ({step.reasoning_operation}) has severe grounding deficit "
                        f"({step.step_grounding_score:.2f}) creating an inferential leap."
                    )

        # 3. Check for Ignored Conflicts (CONFACT 2025)
        if evidence_set.has_conflicts and not trace.conflict_reconciliations:
            if HallucinationRiskType.CONFLICT_IGNORED not in detected_risks:
                detected_risks.append(HallucinationRiskType.CONFLICT_IGNORED)
            risk_explanations.append(
                "Evidence contains documented contradictions, but the reasoning trace bypassed dialectical reconciliation."
            )

        # 4. Check for Citation Mismatches (RAGTruth 2024)
        ev_id_set = {ev.evidence_id for ev in evidence_set.selected_evidence}
        for claim in trace.synthesized_claims:
            for eid in claim.supporting_evidence_ids:
                if eid not in ev_id_set:
                    if HallucinationRiskType.CITATION_MISMATCH not in detected_risks:
                        detected_risks.append(HallucinationRiskType.CITATION_MISMATCH)
                    risk_explanations.append(
                        f"Claim '{claim.claim_id}' cites non-existent evidence ID '{eid}'."
                    )

        # Classify overall risk level
        has_risk = len(detected_risks) > 0
        if not has_risk:
            risk_level = "NONE"
        elif any(r in [HallucinationRiskType.REASONING_LEAP, HallucinationRiskType.CITATION_MISMATCH] for r in detected_risks):
            risk_level = "HIGH"
        elif HallucinationRiskType.UNSUPPORTED_GENERALIZATION in detected_risks:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        assessment = HallucinationRiskAssessment(
            has_hallucination_risk=has_risk,
            risk_level=risk_level,
            detected_risks=detected_risks,
            risk_explanations=risk_explanations
        )

        logger.debug(f"HallucinationDetector completed audit: risk_level={risk_level}, detected={len(detected_risks)}")
        return assessment
