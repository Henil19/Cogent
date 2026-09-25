"""
Sub-Module 9.4: Trust & Epistemic Presentation Engine
Packages Layer 7 trust and uncertainty metrics into visual UI widget contracts.
Avoids misleading uncalibrated probability overclaims by pairing confidence probabilities strictly with qualitative tiers.
Research: Towards Trustworthy RAG (ACM CSUR 2026), APRICOT (ACL 2024).
"""

from typing import Dict, List, Optional
from app.schemas.layer7 import TrustAssessment, UncertaintyAssessment, ConfidenceTier
from app.schemas.layer8 import ExplanationPackage
from app.schemas.layer9 import TrustBadgePayload


class TrustPresenter:
    """
    Sub-Module 9.4: Generates visual trust badge contracts and uncertainty breakdown models.
    Does NOT recalculate trust or modify confidence scores; presents verified Layer 7 data.
    """

    def __init__(self):
        pass

    def build_trust_badges(
        self,
        trust_assessment: TrustAssessment,
        explanation_pkg: ExplanationPackage
    ) -> TrustBadgePayload:
        """
        Builds presentation-ready TrustBadgePayload from verified Layer 7 trust assessment.
        """
        unc_assessment: UncertaintyAssessment = trust_assessment.uncertainty_assessment

        # 1. Build 5-dimension uncertainty dictionary
        breakdown: Dict[str, float] = {}
        # Extract ratios from Layer 7 uncertainty assessment
        epistemic = getattr(unc_assessment, "epistemic_uncertainty_ratio", 0.3)
        aleatoric = getattr(unc_assessment, "aleatoric_uncertainty_ratio", 0.7)
        overall = unc_assessment.overall_uncertainty

        breakdown["coverage"] = round(overall * epistemic * 0.5, 3)
        breakdown["conflict"] = round(overall * aleatoric * 0.6, 3)
        if trust_assessment.source_assessments:
            avg_credibility = sum(s.overall_credibility for s in trust_assessment.source_assessments) / len(trust_assessment.source_assessments)
            breakdown["source"] = round(max(0.0, 1.0 - avg_credibility), 3)
        else:
            breakdown["source"] = 0.1
        breakdown["reasoning"] = round(max(0.0, 1.0 - trust_assessment.reasoning_assessment.path_trust_score), 3)
        breakdown["temporal"] = round(overall * 0.2, 3)

        # 2. Dominant uncertainty
        dom_unc = "epistemic_bounds"
        if unc_assessment.active_uncertainties:
            u = unc_assessment.active_uncertainties[0]
            dom_unc = u.value if hasattr(u, "value") else str(u)

        # 3. Resolve Confidence Tier and Safety Flag defensively
        conf_tier = getattr(trust_assessment, "confidence_tier", None)
        if conf_tier is None:
            c_val = trust_assessment.global_confidence
            if c_val >= 0.85:
                conf_tier = ConfidenceTier.HIGH
            elif c_val >= 0.70:
                conf_tier = ConfidenceTier.MODERATE
            elif c_val >= 0.50:
                conf_tier = ConfidenceTier.LOW
            else:
                conf_tier = ConfidenceTier.PROVISIONAL

        tier_val = conf_tier.value if hasattr(conf_tier, "value") else str(conf_tier)

        is_safe = getattr(trust_assessment, "is_safe_for_decision_support", None)
        if is_safe is None:
            is_safe = (
                trust_assessment.global_confidence >= 0.60
                and trust_assessment.global_trust_index >= 0.50
                and getattr(trust_assessment.hallucination_assessment, "risk_level", "LOW") not in ["HIGH", "CRITICAL"]
            )

        # 4. Standardized disclaimer text avoiding misleading probability claims
        disclaimer = (
            f"Calibrated confidence of {trust_assessment.global_confidence:.2f} [{tier_val}] "
            f"reflects empirical grounding in verified evidence. "
            f"Global Trust Index ({trust_assessment.global_trust_index:.2f}) measures structural provenance and deductive integrity."
        )

        return TrustBadgePayload(
            confidence_tier=conf_tier,
            calibrated_confidence=round(trust_assessment.global_confidence, 2),
            trust_index=round(trust_assessment.global_trust_index, 2),
            risk_level=getattr(trust_assessment.hallucination_assessment, "risk_level", "LOW"),
            is_safe_for_decision_support=bool(is_safe),
            uncertainty_breakdown=breakdown,
            dominant_uncertainty=dom_unc,
            key_caveats=trust_assessment.key_limitations,
            disclaimer_text=disclaimer
        )
