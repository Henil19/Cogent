"""
Sub-Module 7.2: Evidence Reliability Analyzer
Research Basis:
- FRANQ: Faithfulness-Aware Uncertainty Quantification for Fact-Checking RAG (Fadeeva et al., Findings ACL 2026)
- Generate but Verify: Answering with Faithfulness in RAG-based QA (Filice et al., IJCNLP 2025)
- RLSeek: Evidence-Grounded Reasoning for RAG Hallucination Detection (ACL 2026)

Evaluates whether claims are directly and faithfully supported by specific retrieved evidence passages,
decoupling real-world factuality from evidence faithfulness.
"""

import re
import logging
from typing import List, Optional

from app.schemas.layer5 import VerifiedEvidenceSet, EvidenceItem, AtomicClaim, GroundingStatus
from app.schemas.layer6 import SynthesizedReasoningTrace, SynthesizedClaim
from app.schemas.layer7 import EvidenceReliabilityAssessment

logger = logging.getLogger(__name__)


class EvidenceReliabilityAnalyzer:
    """
    Audits the faithfulness and directness of evidence supporting individual claims.
    """

    def analyze_reliability(
        self,
        evidence_set: VerifiedEvidenceSet,
        trace: SynthesizedReasoningTrace
    ) -> List[EvidenceReliabilityAssessment]:
        """
        Audit evidence items supporting both atomic claims and synthesized conclusions.
        """
        assessments: List[EvidenceReliabilityAssessment] = []
        ev_map = {ev.evidence_id: ev for ev in evidence_set.selected_evidence}

        # 1. Audit atomic claims within evidence items
        for ev in evidence_set.selected_evidence:
            for claim in ev.atomic_claims:
                assessment = self._evaluate_claim_evidence_pair(
                    claim_id=claim.claim_id,
                    claim_text=claim.claim_text,
                    ev=ev,
                    quote_span=claim.quote_span,
                    grounding_status=claim.grounding_status,
                    grounding_score=claim.grounding_score
                )
                assessments.append(assessment)

        # 2. Audit synthesized claims from Layer 6
        for syn_claim in trace.synthesized_claims:
            for ev_id in syn_claim.supporting_evidence_ids:
                if ev_id in ev_map:
                    ev = ev_map[ev_id]
                    assessment = self._evaluate_claim_evidence_pair(
                        claim_id=syn_claim.claim_id,
                        claim_text=syn_claim.statement,
                        ev=ev,
                        quote_span=None,
                        grounding_status=GroundingStatus.ENTAILMENT,
                        grounding_score=0.85
                    )
                    assessments.append(assessment)

        logger.debug(f"EvidenceReliabilityAnalyzer audited {len(assessments)} claim-evidence pairs.")
        return assessments

    def _evaluate_claim_evidence_pair(
        self,
        claim_id: str,
        claim_text: str,
        ev: EvidenceItem,
        quote_span: Optional[str],
        grounding_status: GroundingStatus,
        grounding_score: float
    ) -> EvidenceReliabilityAssessment:
        """
        Evaluate alignment, directness, and faithfulness of evidence for a specific claim.
        """
        passage = (ev.content or "").lower()
        clean_claim = claim_text.lower()

        # 1. Alignment Score based on quote span and lexical entailment
        if quote_span and quote_span.lower() in passage:
            alignment_score = max(0.85, grounding_score)
        else:
            # Token overlap alignment
            claim_tokens = [w for w in re.findall(r"\w+", clean_claim) if len(w) > 3]
            if claim_tokens:
                matches = sum(1 for t in claim_tokens if t in passage)
                alignment_score = matches / len(claim_tokens)
            else:
                alignment_score = 0.50

        # 2. Directness Score (checking for speculative/hypothetical hedge markers in passage)
        speculative_markers = ["might", "could", "may", "suggests", "hypothesize", "potentially", "future work"]
        is_speculative = any(m in passage for m in speculative_markers)
        directness_score = 0.65 if is_speculative else 0.95

        # Penalize if evidence is involved in active conflict
        conflict_penalty = 0.20 if ev.conflict_group_ids else 0.0

        # Composite Reliability
        composite = (0.55 * alignment_score + 0.45 * directness_score) - conflict_penalty
        overall_reliability = max(0.0, min(1.0, composite))

        # 3. Faithfulness Determination (FRANQ 2026)
        is_faithful = True
        unfaithfulness_details = None

        if alignment_score < 0.40 or grounding_status == GroundingStatus.CONTRADICTION:
            is_faithful = False
            unfaithfulness_details = (
                f"Claim '{claim_text[:60]}...' lacks direct grounding in evidence passage '{ev.title}' "
                f"(Alignment: {alignment_score:.2f}, Status: {grounding_status.value})"
            )
        elif is_speculative and any(strong in clean_claim for strong in ["proves", "demonstrates definitely", "always"]):
            is_faithful = False
            unfaithfulness_details = "Evidence passage is speculative/hedged but claim asserts definitive certainty."

        return EvidenceReliabilityAssessment(
            evidence_id=ev.evidence_id,
            claim_id=claim_id,
            directness_score=round(directness_score, 4),
            alignment_score=round(alignment_score, 4),
            overall_reliability=round(overall_reliability, 4),
            is_faithful=is_faithful,
            unfaithfulness_details=unfaithfulness_details
        )
