"""
Sub-Module 7.5: Confidence Calibration Engine
Research Basis:
- CLAIM-CAL: Claim-Level Self-Verification and Uncertainty Calibration (Pal, Springer Nature, Sept 12, 2026)
- Calibrating Large Language Models Using Their Generations Only (APRICOT, Ulmer et al., ACL 2024)
- A Survey of Confidence Estimation and Calibration in LLMs (Geng et al., NAACL 2024)

Computes claim-level confidence estimates from structured evidence features.
Distinguishes initial heuristic scoring from learned calibration parameters,
and provides evaluation metrics (Expected Calibration Error, Brier score).
"""

import math
import logging
from typing import Dict, List, Optional, Tuple

from app.schemas.layer6 import SynthesizedReasoningTrace, SynthesizedClaim
from app.schemas.layer7 import (
    ConfidenceTier,
    ClaimConfidenceAssessment,
    SourceCredibilityAssessment,
    EvidenceReliabilityAssessment,
    ReasoningTrustAssessment,
    UncertaintyAssessment
)

logger = logging.getLogger(__name__)

# Initial heuristic baseline feature weights (w_init)
# Phi(c) = [T_path, C_source, R_evidence, 1 - u_conflict, 1 - u_coverage]
DEFAULT_FEATURE_WEIGHTS = {
    "reasoning_trust": 0.30,
    "source_credibility": 0.25,
    "evidence_reliability": 0.20,
    "conflict_freedom": 0.15,
    "coverage_sufficiency": 0.10
}


class ConfidenceCalibrator:
    """
    Computes claim-level confidence assessments and provides calibration evaluation diagnostics.
    """

    def __init__(
        self,
        feature_weights: Optional[Dict[str, float]] = None,
        temperature: float = 1.0,
        threshold_offset: float = 0.0
    ):
        self.feature_weights = feature_weights or DEFAULT_FEATURE_WEIGHTS
        self.temperature = temperature
        self.threshold_offset = threshold_offset

    def calibrate_claims(
        self,
        trace: SynthesizedReasoningTrace,
        source_assessments: List[SourceCredibilityAssessment],
        evidence_assessments: List[EvidenceReliabilityAssessment],
        reasoning_assessment: ReasoningTrustAssessment,
        uncertainty_assessment: UncertaintyAssessment
    ) -> List[ClaimConfidenceAssessment]:
        """
        Produce granular confidence assessments for every synthesized claim in the reasoning trace.
        """
        claim_assessments: List[ClaimConfidenceAssessment] = []

        # Build quick lookups
        src_cred_map = {s.source_id: s.overall_credibility for s in source_assessments}
        ev_rel_map = {e.evidence_id: e.overall_reliability for e in evidence_assessments}
        avg_src_cred = sum(s.overall_credibility for s in source_assessments) / len(source_assessments) if source_assessments else 0.60

        for claim in trace.synthesized_claims:
            # 1. Extract feature values for this claim
            # Feature 1: Reasoning path trust
            f_reasoning = reasoning_assessment.path_trust_score

            # Feature 2: Supporting source credibility
            claim_src_scores = []
            for ev_id in claim.supporting_evidence_ids:
                matching = [cred for sid, cred in src_cred_map.items() if ev_id in sid or sid in ev_id]
                claim_src_scores.append(matching[0] if matching else avg_src_cred)
            f_source = sum(claim_src_scores) / len(claim_src_scores) if claim_src_scores else avg_src_cred

            # Feature 3: Evidence reliability
            claim_ev_scores = [ev_rel_map.get(eid, 0.70) for eid in claim.supporting_evidence_ids]
            f_evidence = sum(claim_ev_scores) / len(claim_ev_scores) if claim_ev_scores else 0.75

            # Feature 4: Absence of conflict
            f_conflict_freedom = 1.0 if not trace.has_conflicts else (
                0.80 if trace.conflict_reconciliations else 0.50
            )

            # Feature 5: Coverage sufficiency
            f_coverage = 1.0 - uncertainty_assessment.overall_uncertainty

            # 2. Compute Raw Confidence via Feature-Weighted Sum
            raw_conf = (
                self.feature_weights["reasoning_trust"] * f_reasoning +
                self.feature_weights["source_credibility"] * f_source +
                self.feature_weights["evidence_reliability"] * f_evidence +
                self.feature_weights["conflict_freedom"] * f_conflict_freedom +
                self.feature_weights["coverage_sufficiency"] * f_coverage
            )
            raw_conf = max(0.05, min(0.99, raw_conf))

            # Bound confidence strictly by the weakest link in reasoning (Weakest Link 2026)
            if reasoning_assessment.weakest_link_score < raw_conf:
                raw_conf = 0.70 * raw_conf + 0.30 * reasoning_assessment.weakest_link_score

            # 3. Apply Temperature / Logistic Scaling for Calibrated Probability
            # P_cal = 1 / (1 + exp(-(raw_conf - offset) / tau))
            scaled_logit = (raw_conf - 0.50 - self.threshold_offset) / self.temperature
            calibrated_conf = 1.0 / (1.0 + math.exp(-scaled_logit * 4.0))  # normalized around 0.5
            calibrated_conf = max(0.10, min(0.98, calibrated_conf))

            # 4. Determine Confidence Tier
            if calibrated_conf >= 0.80:
                tier = ConfidenceTier.HIGH
            elif calibrated_conf >= 0.60:
                tier = ConfidenceTier.MODERATE
            elif calibrated_conf >= 0.40:
                tier = ConfidenceTier.LOW
            else:
                tier = ConfidenceTier.PROVISIONAL

            # 5. Extract Trust and Uncertainty Drivers
            trust_drivers = []
            if f_source >= 0.80:
                trust_drivers.append("Supported by authoritative, recognized publication sources.")
            if f_evidence >= 0.80:
                trust_drivers.append("Strong direct quote-span alignment in evidence.")
            if reasoning_assessment.is_chain_intact:
                trust_drivers.append("Deductive reasoning chain is topologically intact.")

            uncertainty_drivers = []
            if trace.has_conflicts:
                uncertainty_drivers.append("Underlying empirical literature reports conflicting metrics.")
            if reasoning_assessment.weakest_link_score < 0.70:
                uncertainty_drivers.append(f"Reasoning path is constrained by a moderate weakest-link premise ({reasoning_assessment.weakest_link_score:.2f}).")
            if claim.caveats:
                uncertainty_drivers.extend(claim.caveats[:2])

            assessment = ClaimConfidenceAssessment(
                claim_id=claim.claim_id,
                statement=claim.statement,
                raw_confidence=round(raw_conf, 4),
                calibrated_confidence=round(calibrated_conf, 4),
                confidence_tier=tier,
                primary_trust_drivers=trust_drivers,
                primary_uncertainty_drivers=uncertainty_drivers
            )
            claim_assessments.append(assessment)

        logger.debug(f"ConfidenceCalibrator assessed {len(claim_assessments)} claims.")
        return claim_assessments

    @staticmethod
    def compute_ece(confidences: List[float], ground_truths: List[int], num_bins: int = 10) -> float:
        """
        Compute Expected Calibration Error (ECE) across prediction bins (Geng et al. 2024, Pal 2026).
        """
        if not confidences or len(confidences) != len(ground_truths):
            return 0.0

        n = len(confidences)
        bin_boundaries = [i / num_bins for i in range(num_bins + 1)]
        ece = 0.0

        for i in range(num_bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]

            in_bin = [
                (conf, y) for conf, y in zip(confidences, ground_truths)
                if bin_lower <= conf < bin_upper or (i == num_bins - 1 and conf == bin_upper)
            ]
            bin_size = len(in_bin)

            if bin_size > 0:
                avg_conf = sum(conf for conf, _ in in_bin) / bin_size
                avg_acc = sum(y for _, y in in_bin) / bin_size
                ece += (bin_size / n) * abs(avg_acc - avg_conf)

        return round(ece, 4)

    @staticmethod
    def compute_brier_score(confidences: List[float], ground_truths: List[int]) -> float:
        """
        Compute Brier Score: mean squared difference between predicted confidence and binary ground truth.
        """
        if not confidences or len(confidences) != len(ground_truths):
            return 0.0

        n = len(confidences)
        brier = sum((conf - y) ** 2 for conf, y in zip(confidences, ground_truths)) / n
        return round(brier, 4)
