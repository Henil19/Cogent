"""
Sub-Module 8.5: Dialectical & Contrastive Explanation Engine
Explains empirical contradictions and opposing viewpoints adhering strictly to the
Zero Winner Forcing principle. Explains thesis, antithesis, contextual variance,
and provides contrastive justifications (Why X rather than Y?).
"""

from typing import List, Dict
from app.schemas.layer5 import VerifiedEvidenceSet, EvidenceItem
from app.schemas.layer6 import SynthesizedReasoningTrace, ConflictReconciliation
from app.schemas.layer8 import ConflictExplanation


class DialecticalExplanationEngine:
    """
    Generates balanced, non-winner-forced explanations of empirical conflicts and
    contrastive analyses derived from Layer 6 reconciliations and Layer 5 conflict graphs.
    """

    def __init__(self):
        pass

    def build_conflict_explanations(
        self,
        trace: SynthesizedReasoningTrace,
        evidence_set: VerifiedEvidenceSet
    ) -> List[ConflictExplanation]:
        """
        Translates Layer 6 conflict reconciliations into explicit, balanced ConflictExplanation structures.
        """
        explanations: List[ConflictExplanation] = []
        evidence_items = getattr(evidence_set, "selected_evidence", None) or getattr(evidence_set, "evidence_items", [])
        ev_lookup: Dict[str, EvidenceItem] = {
            e.evidence_id: e for e in evidence_items
        }

        for rec in trace.conflict_reconciliations:
            # Thesis: Claim A and its supporting evidence
            ev_a = ev_lookup.get(rec.claim_a_id)
            ev_b = ev_lookup.get(rec.claim_b_id)

            prov_a = getattr(ev_a, "provenance", None)
            title_a = getattr(ev_a, "title", None) or (getattr(prov_a, "document_title", None) if prov_a else None) or "Primary Source"
            quote_a = getattr(ev_a, "quoted_text", None) or getattr(ev_a, "content", None) or "Direct benchmark observation"
            if len(quote_a) > 140:
                quote_a = quote_a[:140] + "..."

            stmt_a = getattr(rec, "claim_a_text", None) or quote_a
            if stmt_a.startswith("clm_chk_") or stmt_a == rec.claim_a_id:
                stmt_a = quote_a

            thesis_text = (
                f"Position A asserts that {stmt_a}, as supported by empirical findings "
                f"in '{title_a}': \"{quote_a}\"."
            )

            prov_b = getattr(ev_b, "provenance", None)
            title_b = getattr(ev_b, "title", None) or (getattr(prov_b, "document_title", None) if prov_b else None) or "Alternative Source"
            quote_b = getattr(ev_b, "quoted_text", None) or getattr(ev_b, "content", None) or "Contradictory evaluation observation"
            if len(quote_b) > 140:
                quote_b = quote_b[:140] + "..."

            stmt_b = getattr(rec, "claim_b_text", None) or quote_b
            if stmt_b.startswith("clm_chk_") or stmt_b == rec.claim_b_id:
                stmt_b = quote_b

            antithesis_text = (
                f"Position B counter-asserts that {stmt_b}, as supported by empirical findings "
                f"in '{title_b}': \"{quote_b}\"."
            )

            res_status_str = rec.resolution_status.value if hasattr(rec.resolution_status, "value") else str(rec.resolution_status)

            rec_analysis = (
                getattr(rec, "reconciliation_analysis", None) or
                getattr(rec, "reconciliation_explanation", None) or
                getattr(rec, "synthesized_perspective", "Empirical variance explained by distinct evaluation conditions.")
            )

            context_distinction = (
                f"The observed divergence is explained by {res_status_str.lower().replace('_', ' ')}: "
                f"{rec_analysis}"
            )

            why_no_winner = (
                "Cogent upholds the Zero Winner Forcing principle: neither position is arbitrarily "
                "discarded because both derive from verified primary literature under distinct experimental regimes."
            )

            conf_id = getattr(rec, "reconciliation_id", None) or getattr(rec, "conflict_id", "conf_unknown")
            aspect_val = getattr(rec, "conflicting_aspect", None)
            if not aspect_val or aspect_val.startswith("clm_chk_") or " vs " in aspect_val:
                aspect_val = "Empirical Variance"

            conflict_exp = ConflictExplanation(
                conflict_id=conf_id,
                claim_a=stmt_a,
                claim_b=stmt_b,
                thesis_explanation=thesis_text,
                antithesis_explanation=antithesis_text,
                contextual_distinction=context_distinction,
                resolution_status=res_status_str,
                why_no_winner_forced=why_no_winner,
                aspect=aspect_val,
                thesis_statement=stmt_a,
                antithesis_statement=stmt_b,
                thesis_evidence_id=getattr(rec, "supporting_evidence_ids", [rec.claim_a_id])[0] if getattr(rec, "supporting_evidence_ids", None) else rec.claim_a_id,
                antithesis_evidence_id=getattr(rec, "supporting_evidence_ids", [rec.claim_b_id])[-1] if getattr(rec, "supporting_evidence_ids", None) else rec.claim_b_id,
                contextual_divergence_explanation=rec_analysis,
                thesis_source_title=getattr(rec, "source_a_title", None),
                antithesis_source_title=getattr(rec, "source_b_title", None),
            )
            explanations.append(conflict_exp)

        return explanations
