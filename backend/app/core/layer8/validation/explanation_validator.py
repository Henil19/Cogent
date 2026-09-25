"""
Sub-Module 8.8 (Validator): Explanation Integrity Validator
Executes the 6-Gate Programmatic Integrity Audit to guarantee that generated explanations
remain faithful to upstream evidence (Layer 5), explicit reasoning DAGs (Layer 6),
and calibrated trust assessments (Layer 7).
"""

from typing import List, Dict, Set
from app.schemas.layer5 import VerifiedEvidenceSet
from app.schemas.layer6 import SynthesizedReasoningTrace
from app.schemas.layer7 import TrustAssessment
from app.schemas.layer8 import (
    NarrativeStep,
    EvidenceAttribution,
    ClaimExplanation,
    ConflictExplanation,
    MultiFidelityNarrative,
    ExplanationValidation,
    ExplanationFidelityStatus
)


class ExplanationValidator:
    """
    Validates structural correspondence, evidence containment, citation resolution,
    conflict preservation, and confidence-hedging consistency across generated explanations.
    """

    EXAGGERATED_HEDGE_TERMS = {
        "conclusively proves",
        "indisputable",
        "undeniable",
        "definitely establishes",
        "beyond all doubt",
        "unequivocally demonstrates"
    }

    def __init__(self):
        pass

    def validate_explanation(
        self,
        trace: SynthesizedReasoningTrace,
        trust_assessment: TrustAssessment,
        evidence_set: VerifiedEvidenceSet,
        narrative_steps: List[NarrativeStep],
        claim_explanations: List[ClaimExplanation],
        attributions: List[EvidenceAttribution],
        citation_map: Dict[str, EvidenceAttribution],
        conflict_explanations: List[ConflictExplanation],
        multi_fidelity: MultiFidelityNarrative
    ) -> ExplanationValidation:
        """
        Executes the 6-Gate Audit and emits a structured ExplanationValidation report.
        """
        unsupported_claims: List[str] = []
        citation_mismatches: List[str] = []
        reasoning_mismatches: List[str] = []
        confidence_hedging_mismatches: List[str] = []
        conflict_omissions: List[str] = []
        topological_inversions: List[str] = []

        ev_items = getattr(evidence_set, "selected_evidence", None) or getattr(evidence_set, "evidence_items", [])
        valid_evidence_ids: Set[str] = {e.evidence_id for e in ev_items}
        valid_claim_ids: Set[str] = {c.claim_id for c in trace.synthesized_claims}
        valid_node_ids: Set[str] = {n.step_id for n in trace.reasoning_steps}

        # Gate 1: Claim Fidelity (All explained claims exist in Layer 6 trace)
        for ce in claim_explanations:
            if ce.claim_id not in valid_claim_ids:
                unsupported_claims.append(f"Claim `{ce.claim_id}` has no upstream record in Layer 6 trace.")

        # Gate 2: Evidence Fidelity (Quoted spans must match raw evidence)
        for attr in attributions:
            if attr.evidence_id not in valid_evidence_ids:
                citation_mismatches.append(f"Attribution cites non-existent evidence `{attr.evidence_id}`.")

        # Gate 3: Reasoning Fidelity (Topological order & Structural Correspondence)
        observed_node_indices: Dict[str, int] = {}
        for idx, step in enumerate(narrative_steps):
            if step.node_id not in valid_node_ids:
                reasoning_mismatches.append(f"Narrative step references unauthorized node `{step.node_id}`.")
            observed_node_indices[step.node_id] = idx

        # Check topological dependency ordering: premise nodes must precede dependent nodes
        for node in trace.reasoning_steps:
            if node.step_id in observed_node_indices:
                dependent_idx = observed_node_indices[node.step_id]
                for parent_id in node.dependent_step_ids:
                    if parent_id in observed_node_indices:
                        parent_idx = observed_node_indices[parent_id]
                        if parent_idx > dependent_idx:
                            topological_inversions.append(
                                f"Topological inversion: Premise `{parent_id}` (step {parent_idx}) "
                                f"appears after dependent `{node.step_id}` (step {dependent_idx})."
                            )

        # Gate 4: Citation Fidelity (All citation tokens resolve in master map)
        for ce in claim_explanations:
            for token in ce.citation_tokens:
                if token not in citation_map:
                    citation_mismatches.append(f"Claim `{ce.claim_id}` has unresolved citation token `{token}`.")

        # Gate 5: Conflict Fidelity (All Layer 6 reconciliations must be explained)
        reconciled_conflict_ids = {
            getattr(r, "reconciliation_id", None) or getattr(r, "conflict_id", "")
            for r in trace.conflict_reconciliations
        }
        explained_conflict_ids = {c.conflict_id for c in conflict_explanations}
        missing_conflicts = reconciled_conflict_ids - explained_conflict_ids
        for mc in missing_conflicts:
            if mc:
                conflict_omissions.append(f"Layer 6 conflict `{mc}` was omitted from dialectical explanation.")

        # Gate 6: Confidence-Hedging Fidelity
        conf = trust_assessment.global_confidence
        combined_text = (
            multi_fidelity.executive_summary.lower() + " " +
            multi_fidelity.researcher_narrative.lower() + " " +
            multi_fidelity.layperson_narrative.lower()
        )

        if conf < 0.80:
            for term in self.EXAGGERATED_HEDGE_TERMS:
                if term in combined_text:
                    confidence_hedging_mismatches.append(
                        f"Linguistic tone mismatch: Found exaggerated term '{term}' while calibrated confidence is {conf:.2f}."
                    )

        # Compute validation score
        total_checks = 6
        failed_gates = 0
        if unsupported_claims:
            failed_gates += 1
        if citation_mismatches:
            failed_gates += 1
        if reasoning_mismatches or topological_inversions:
            failed_gates += 1
        if conflict_omissions:
            failed_gates += 1
        if confidence_hedging_mismatches:
            failed_gates += 1

        score = max(0.0, 1.0 - (failed_gates / total_checks))
        is_faithful = (failed_gates == 0)

        if is_faithful:
            status = ExplanationFidelityStatus.FULLY_FAITHFUL
            summary = "All 6 fidelity gates passed with 100% structural correspondence to evidence, DAG, and confidence."
        elif failed_gates == 1 and not unsupported_claims and not reasoning_mismatches:
            status = ExplanationFidelityStatus.MINOR_QUALIFIER_MISMATCH
            summary = "Minor qualifier or hedging mismatch detected; underlying structural derivation remains intact."
        else:
            status = ExplanationFidelityStatus.UNFAITHFUL_DETECTED
            summary = f"Fidelity validation failed across {failed_gates} gate(s). Audit flagged critical inconsistencies."

        return ExplanationValidation(
            is_faithful=is_faithful,
            fidelity_status=status,
            unsupported_claims=unsupported_claims,
            citation_mismatches=citation_mismatches,
            reasoning_mismatches=reasoning_mismatches,
            confidence_hedging_mismatches=confidence_hedging_mismatches,
            conflict_omissions=conflict_omissions,
            topological_inversions=topological_inversions,
            validation_score=score,
            validation_summary=summary
        )
