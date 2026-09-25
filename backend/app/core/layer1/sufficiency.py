"""
Sub-Module 1.5: Sufficiency Assessment Gate
Exact 4-term research formulation deciding whether to proceed to Layer 2 or trigger targeted clarification.
Research basis:
- P1 (IntentSim - NAACL 2025): Clarification utility scoring
- P3 (Uncertainty Calibration - TrustNLP 2025): Calibrated decision boundaries
- P7 (CLAIM - arXiv 2026): Entropy-driven thresholding
"""

import math
from typing import List
from app.config import settings
from app.schemas.layer1 import AmbiguityReport, SufficiencyReport


class SufficiencyAssessmentGate:
    """
    Computes calibrated sufficiency score using the 4-component weighted formulation:
    S = w1 * (1 - max_ambiguity) + w2 * completeness + w3 * coherence + w4 * intent_clarity
    Where:
      w1 = 0.35 (ambiguity signal)
      w2 = 0.30 (completeness signal)
      w3 = 0.15 (logical/temporal coherence signal)
      w4 = 0.20 (intent clarity signal)
    """

    def __init__(
        self,
        base_threshold: float = 0.70,
        w1: float = 0.35,
        w2: float = 0.30,
        w3: float = 0.15,
        w4: float = 0.20,
    ):
        self.base_threshold = getattr(settings, "SUFFICIENCY_THRESHOLD", base_threshold)
        self.w1 = w1
        self.w2 = w2
        self.w3 = w3
        self.w4 = w4

    def evaluate(
        self,
        query: str,
        entities: List[str],
        ambiguity: AmbiguityReport,
        intent_clarity_score: float = 0.85,
        clarification_turn_count: int = 0,
    ) -> SufficiencyReport:
        """
        Evaluate query sufficiency according to the exact research formula.
        Enforces graceful degradation: relaxes threshold across clarification turns.
        """
        max_ambiguity = max(ambiguity.ambiguity_types.values()) if ambiguity.ambiguity_types else ambiguity.overall_ambiguity_score
        completeness = ambiguity.completeness_score
        coherence = ambiguity.coherence_score
        intent_clarity = min(max(intent_clarity_score, 0.10), 1.0)

        # 4-term research formula
        raw_score = (
            self.w1 * (1.0 - max_ambiguity)
            + self.w2 * completeness
            + self.w3 * coherence
            + self.w4 * intent_clarity
        )

        # Grounded in P3 (TrustNLP 2025 Uncertainty Calibration) & P7 (CLAIM arXiv 2026):
        # 1. Contradiction Veto: A query with an unresolved contradiction (coherence < 0.50) cannot be sufficient
        if coherence < 0.50:
            raw_score = min(raw_score, coherence)

        # 2. Dominant Ambiguity Gating: If any CLAMBER dimension has severe ambiguity (>= 0.60),
        # fluency, grammatical completeness, or default intent clarity must not override it.
        if max_ambiguity >= 0.60:
            raw_score = min(raw_score, round(max(1.0 - max_ambiguity, 0.15), 3))

        calibrated_sufficiency = round(min(max(raw_score, 0.02), 0.99), 3)

        # Shannon entropy representation of uncertainty
        p = min(max(calibrated_sufficiency, 0.01), 0.99)
        entropy = -(p * math.log2(p) + (1.0 - p) * math.log2(1.0 - p))
        calibrated_uncertainty = round(entropy, 3)

        # Adaptive thresholding based on prior clarification turns
        effective_threshold = self.base_threshold
        if clarification_turn_count == 1:
            effective_threshold = max(self.base_threshold - 0.15, 0.45)
        elif clarification_turn_count >= 2:
            effective_threshold = 0.10  # Force proceed after max 2 rounds

        is_sufficient = (calibrated_sufficiency >= effective_threshold) or (clarification_turn_count >= 2)

        if clarification_turn_count >= 2:
            reason = "Maximum clarification rounds (2) reached. Proceeding with best-effort domain assumptions."
        elif is_sufficient:
            reason = (
                f"Query meets sufficiency threshold ({calibrated_sufficiency:.2f} >= {effective_threshold:.2f}) "
                f"across completeness ({completeness:.2f}) and coherence ({coherence:.2f})."
            )
        else:
            reason = (
                f"Sufficiency score ({calibrated_sufficiency:.2f}) is below threshold ({effective_threshold:.2f}). "
                f"Highest ambiguity: {ambiguity.primary_ambiguity_type or 'vagueness'} ({max_ambiguity:.2f}). "
                f"Missing: {', '.join(ambiguity.missing_elements[:2])}."
            )

        return SufficiencyReport(
            is_sufficient=is_sufficient,
            sufficiency_score=calibrated_sufficiency,
            uncertainty_score=calibrated_uncertainty,
            decision_reason=reason,
        )
