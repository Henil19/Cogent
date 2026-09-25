"""
Sub-Module 6.5: Epistemic Gap & Insufficiency Evaluator
Research Basis:
- S2G-RAG: Structured Sufficiency and Gap Judging for Iterative RAG (ACL 2026)
- Self-RAG: Factual Grounding Tokens & Gap Reflection (Asai et al., ICLR 2024)

Audits evidence sufficiency against the query plan.
When information gaps are detected, generates explicit EPISTEMIC_HEDGE reasoning nodes
and bounded caveats, preventing ungrounded hallucinations.
"""

import logging
from typing import Dict, List, Optional, Tuple

from app.schemas.layer2 import KnowledgeRetrievalPlan
from app.schemas.layer5 import VerifiedEvidenceSet, AtomicClaim
from app.schemas.layer6 import (
    ReasoningStepNode,
    ReasoningStepType,
    SynthesizedClaim,
    SynthesisStatus
)

logger = logging.getLogger(__name__)


class EpistemicEvaluator:
    """
    Evaluates epistemic gaps and formulates explicit deductive hedges
    when evidence is incomplete.
    """

    def evaluate_gaps_and_hedges(
        self,
        evidence_set: VerifiedEvidenceSet,
        plan: KnowledgeRetrievalPlan,
        sub_query_claims: Dict[str, List[AtomicClaim]],
        start_step_index: int
    ) -> Tuple[List[str], List[ReasoningStepNode], List[SynthesizedClaim], bool]:
        """
        Check for missing information gaps and construct epistemic hedge nodes.
        
        Returns:
            Tuple of:
            - List of unresolved_hedges (textual caveat strings)
            - List of ReasoningStepNode (type=EPISTEMIC_HEDGE)
            - List of SynthesizedClaim (status=EPISTEMIC_HEDGE)
            - is_reasoning_complete (boolean)
        """
        hedges: List[str] = []
        hedge_steps: List[ReasoningStepNode] = []
        hedge_claims: List[SynthesizedClaim] = []
        is_complete = True

        curr_step = start_step_index

        # 1. Check inherited gaps from Layer 5
        inherited_gaps = evidence_set.unresolved_information_gaps or []
        for gap in inherited_gaps:
            hedge_text = (
                f"Epistemic Boundary: Available evidence lacks data regarding '{gap}'. "
                f"No definitive conclusion can be drawn along this dimension without ungrounded assumption."
            )
            hedges.append(hedge_text)
            is_complete = False

            step = ReasoningStepNode(
                step_id=f"step_hedge_{curr_step}",
                step_index=curr_step,
                step_type=ReasoningStepType.EPISTEMIC_HEDGE,
                sub_query_id=None,
                premise_claim_ids=[],
                evidence_ids=[],
                dependent_step_ids=[],
                reasoning_operation=f"Epistemic gap bounding (S2G-RAG 2026): {gap}",
                intermediate_claim=hedge_text,
                supporting_claim_ids=[],
                opposing_claim_ids=[],
                unresolved_issues=[f"Missing gap: {gap}"],
                step_grounding_score=0.0
            )
            hedge_steps.append(step)
            curr_step += 1

        # 2. Check for sub-queries in Layer 2 plan with zero retrieved claims
        for sq in plan.sub_queries:
            claims = sub_query_claims.get(sq.id, [])
            if not claims:
                sq_gap = (
                    f"Sub-question '{sq.description}' could not be answered from retrieved evidence. "
                    f"Conclusions requiring this sub-objective are strictly bounded."
                )
                hedges.append(sq_gap)
                is_complete = False

                step = ReasoningStepNode(
                    step_id=f"step_hedge_{curr_step}",
                    step_index=curr_step,
                    step_type=ReasoningStepType.EPISTEMIC_HEDGE,
                    sub_query_id=sq.id,
                    premise_claim_ids=[],
                    evidence_ids=[],
                    dependent_step_ids=[],
                    reasoning_operation=f"Sub-query gap bounding: '{sq.id}'",
                    intermediate_claim=sq_gap,
                    supporting_claim_ids=[],
                    opposing_claim_ids=[],
                    unresolved_issues=[f"Uncovered sub-query: {sq.id}"],
                    step_grounding_score=0.0
                )
                hedge_steps.append(step)
                curr_step += 1

        # If sufficiency gate failed in Layer 5
        if not evidence_set.is_sufficient_for_reasoning and not hedges:
            general_hedge = "Evidence sufficiency is below reasoning threshold; conclusions are strictly provisional."
            hedges.append(general_hedge)
            is_complete = False

        # Build synthesized hedge claim if any hedges exist
        if hedges:
            syn_hedge = SynthesizedClaim(
                claim_id=f"syn_hedge_{curr_step}",
                statement="; ".join(hedges),
                status=SynthesisStatus.EPISTEMIC_HEDGE,
                source_claim_ids=[],
                supporting_evidence_ids=[],
                opposing_evidence_ids=[],
                derivation_step_ids=[s.step_id for s in hedge_steps],
                caveats=hedges
            )
            hedge_claims.append(syn_hedge)

        logger.debug(f"EpistemicEvaluator identified {len(hedges)} epistemic hedges. Reasoning complete: {is_complete}")
        return hedges, hedge_steps, hedge_claims, is_complete
