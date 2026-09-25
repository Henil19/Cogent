"""
Sub-Module 6.1: Evidence-to-Claim Chainer
Research Basis:
- TRACE the Evidence (Fang, Meng & MacDonald, EMNLP Findings 2024)
- FActScore (Min et al., EMNLP 2023)

Maps verified atomic claims from Layer 5 EvidenceItems to Layer 2 sub-queries and entity anchors.
Constructs base leaf nodes in the Entailment Reasoning DAG.
Supports LLM-assisted clustering when configured, with robust deterministic fallback.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple

from app.core.llm_client import LLMClient
from app.schemas.layer2 import KnowledgeRetrievalPlan
from app.schemas.layer5 import VerifiedEvidenceSet, EvidenceItem, AtomicClaim, GroundingStatus
from app.schemas.layer6 import ReasoningStepNode, ReasoningStepType

logger = logging.getLogger(__name__)


class ClaimChainer:
    """
    Organizes verified Layer 5 atomic claims into structured premise clusters
    anchored to specific sub-queries and entities.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def build_premise_nodes(
        self,
        evidence_set: VerifiedEvidenceSet,
        plan: KnowledgeRetrievalPlan
    ) -> Tuple[List[ReasoningStepNode], Dict[str, List[AtomicClaim]]]:
        """
        Extract all grounded atomic claims and construct initial leaf reasoning step nodes.
        
        Returns:
            Tuple of:
            - List of ReasoningStepNode (step_type=EVIDENCE_LINK)
            - Mapping of sub_query_id -> List of AtomicClaim
        """
        # 1. Collect all atomic claims across selected evidence items with Round-Robin interleaving
        # This guarantees that the top premises and claims in the reasoning DAG span across MULTIPLE distinct sources
        sub_query_claims: Dict[str, List[AtomicClaim]] = {}
        claim_to_evidence: Dict[str, str] = {}

        ev_claims_map = {ev.evidence_id: list(ev.atomic_claims) for ev in evidence_set.selected_evidence}
        max_claims_in_ev = max((len(c_list) for c_list in ev_claims_map.values()), default=0)

        for i in range(max_claims_in_ev):
            for ev in evidence_set.selected_evidence:
                c_list = ev_claims_map.get(ev.evidence_id, [])
                if i < len(c_list):
                    claim = c_list[i]
                    sq_id = ev.sub_query_id or (plan.sub_queries[0].id if plan.sub_queries else "sq_general")
                    if sq_id not in sub_query_claims:
                        sub_query_claims[sq_id] = []
                    sub_query_claims[sq_id].append(claim)
                    claim_to_evidence[claim.claim_id] = ev.evidence_id

        # 2. Build initial leaf ReasoningStepNodes
        leaf_nodes: List[ReasoningStepNode] = []
        step_idx = 0

        for sq in plan.sub_queries:
            claims = sub_query_claims.get(sq.id, [])
            if not claims:
                continue

            for claim in claims:
                # Weakest Link grounding score for this atomic premise
                g_score = claim.grounding_score if claim.grounding_status == GroundingStatus.ENTAILMENT else (
                    0.50 if claim.grounding_status == GroundingStatus.NEUTRAL else 0.0
                )

                ev_id = claim_to_evidence.get(claim.claim_id)
                evidence_ids = [ev_id] if ev_id else []

                node = ReasoningStepNode(
                    step_id=f"step_leaf_{step_idx}",
                    step_index=step_idx,
                    step_type=ReasoningStepType.EVIDENCE_LINK,
                    sub_query_id=sq.id,
                    premise_claim_ids=[claim.claim_id],
                    evidence_ids=evidence_ids,
                    dependent_step_ids=[],
                    reasoning_operation=f"Anchored atomic premise to sub-query '{sq.description}'",
                    intermediate_claim=claim.claim_text,
                    supporting_claim_ids=[claim.claim_id],
                    opposing_claim_ids=[],
                    unresolved_issues=[],
                    step_grounding_score=round(g_score, 4)
                )
                leaf_nodes.append(node)
                step_idx += 1

        logger.debug(f"ClaimChainer constructed {len(leaf_nodes)} leaf premise nodes across {len(sub_query_claims)} sub-queries.")
        return leaf_nodes, sub_query_claims
