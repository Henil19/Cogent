"""
Sub-Module 6.4: Comparative & Decision Engine
Research Basis:
- Graph of Thoughts: Solving Elaborate Problems with LLMs (Besta et al., AAAI 2024)
- Least-to-Most Prompting (Zhou et al., ICLR 2023)
- Survey of RAG-Reasoning Systems (EMNLP Findings 2025)

Constructs Entity x Criterion evaluation matrices for comparative and decision-support queries.
Evaluates multi-attribute trade-offs and generates conditional conclusions
without forcing an arbitrary single winner.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple

from app.core.llm_client import LLMClient
from app.schemas.layer1 import StructuredUserInput, IntentCategory
from app.schemas.layer2 import KnowledgeRetrievalPlan
from app.schemas.layer5 import VerifiedEvidenceSet, AtomicClaim
from app.schemas.layer6 import (
    ComparativeDimension,
    ReasoningStepNode,
    ReasoningStepType,
    SynthesizedClaim,
    SynthesisStatus
)

logger = logging.getLogger(__name__)

DEFAULT_CRITERIA = ["Accuracy / Performance", "Memory / Resource Overhead", "Latency / Speed", "Scalability"]


class ComparativeEngine:
    """
    Builds structured multi-attribute trade-off comparisons across entities.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def build_comparison_matrix(
        self,
        evidence_set: VerifiedEvidenceSet,
        plan: KnowledgeRetrievalPlan,
        user_input: Optional[StructuredUserInput],
        start_step_index: int
    ) -> Tuple[List[ComparativeDimension], List[ReasoningStepNode], List[SynthesizedClaim]]:
        """
        Evaluate comparative claims across criteria and generate trade-off reasoning steps.
        
        Returns:
            Tuple of:
            - List of ComparativeDimension
            - List of ReasoningStepNode (COMPARISON or TRADEOFF_ANALYSIS)
            - List of SynthesizedClaim (CONDITIONAL_CONCLUSION)
        """
        dimensions: List[ComparativeDimension] = []
        steps: List[ReasoningStepNode] = []
        synthesized: List[SynthesizedClaim] = []

        is_comparative = False
        if user_input and user_input.intent in (IntentCategory.COMPARATIVE, "DECISION_SUPPORT"):
            is_comparative = True
        elif any(w in plan.parent_query.lower() for w in ["compare ", " vs ", " versus ", "tradeoff"]):
            is_comparative = True

        if not is_comparative:
            return dimensions, steps, synthesized

        # Extract entities from Layer 1 or fallback from query, filtering out common stopwords
        stopwords = {
            "what", "how", "why", "when", "where", "who", "the", "is", "are", "in", "on", "to",
            "does", "can", "could", "should", "would", "do", "did", "and", "or", "an", "a", "of",
            "for", "with", "between", "into", "through", "option", "candidate"
        }
        raw_entities = user_input.entities if (user_input and user_input.entities) else self._extract_entities_fallback(plan.parent_query)
        entities = [e for e in raw_entities if e.lower() not in stopwords and len(e.strip()) >= 3]
        if len(entities) < 2:
            return dimensions, steps, synthesized

        # Collect claims
        all_claims = []
        for ev in evidence_set.selected_evidence:
            all_claims.extend(ev.atomic_claims)

        curr_step = start_step_index

        # Evaluate across criteria
        for criterion in DEFAULT_CRITERIA:
            eval_map: Dict[str, str] = {}
            matched_claim_ids = []

            for ent in entities:
                ent_clean = ent.lower()
                # Find claims mentioning this entity and keywords related to criterion
                keywords = [w.lower() for w in re.findall(r"\w+", criterion)]
                relevant_claims = [
                    c for c in all_claims
                    if ent_clean in c.claim_text.lower() or (c.subject and ent_clean in c.subject.lower())
                ]
                
                # Filter by criterion keywords if possible
                crit_claims = [
                    c for c in relevant_claims
                    if any(k in c.claim_text.lower() for k in keywords)
                ] or relevant_claims

                if crit_claims:
                    eval_map[ent] = crit_claims[0].claim_text
                    matched_claim_ids.append(crit_claims[0].claim_id)
                else:
                    eval_map[ent] = f"No specific evidence on {criterion.lower()}"

            tradeoff = self._formulate_tradeoff(criterion, eval_map, entities)

            dim = ComparativeDimension(
                criterion=criterion,
                entity_evaluations=eval_map,
                tradeoff_summary=tradeoff,
                supporting_claim_ids=matched_claim_ids
            )
            dimensions.append(dim)

            # Step node
            step = ReasoningStepNode(
                step_id=f"step_comp_{curr_step}",
                step_index=curr_step,
                step_type=ReasoningStepType.COMPARISON,
                sub_query_id=None,
                premise_claim_ids=matched_claim_ids,
                evidence_ids=[],
                dependent_step_ids=[],
                reasoning_operation=f"Multi-attribute comparison along criterion: {criterion}",
                intermediate_claim=tradeoff,
                supporting_claim_ids=matched_claim_ids,
                opposing_claim_ids=[],
                unresolved_issues=[],
                step_grounding_score=0.88
            )
            steps.append(step)
            curr_step += 1

        # Formulate conditional conclusion claim
        cond_statement = self._formulate_conditional_conclusion(dimensions, entities)
        syn_claim = SynthesizedClaim(
            claim_id=f"syn_cond_{curr_step}",
            statement=cond_statement,
            status=SynthesisStatus.CONDITIONAL_CONCLUSION,
            source_claim_ids=[cid for d in dimensions for cid in d.supporting_claim_ids],
            supporting_evidence_ids=[ev.evidence_id for ev in evidence_set.selected_evidence[:2]],
            opposing_evidence_ids=[],
            derivation_step_ids=[s.step_id for s in steps],
            caveats=["Conclusion is conditional upon the deployment priority criterion chosen."]
        )
        synthesized.append(syn_claim)

        logger.debug(f"ComparativeEngine constructed {len(dimensions)} evaluation dimensions and conditional synthesis.")
        return dimensions, steps, synthesized

    def _extract_entities_fallback(self, query: str) -> List[str]:
        """Extract comparison entities strictly from 'A vs B' or 'compare A and B' patterns."""
        match = re.search(r"([\w\-]+)\s+(?:vs\.?|versus)\s+([\w\-]+)", query, re.IGNORECASE)
        if match:
            return [match.group(1).capitalize(), match.group(2).capitalize()]
        match_comp = re.search(r"compare\s+([\w\-]+)\s+and\s+([\w\-]+)", query, re.IGNORECASE)
        if match_comp:
            return [match_comp.group(1).capitalize(), match_comp.group(2).capitalize()]
        return []

    def _formulate_tradeoff(self, criterion: str, eval_map: Dict[str, str], entities: List[str]) -> str:
        """Summarize trade-off for a specific criterion."""
        ent1, ent2 = entities[0], entities[1]
        ev1 = eval_map.get(ent1, "")
        ev2 = eval_map.get(ent2, "")
        return f"Regarding {criterion}: {ent1} asserts ({ev1}); while {ent2} asserts ({ev2})."

    def _formulate_conditional_conclusion(self, dimensions: List[ComparativeDimension], entities: List[str]) -> str:
        """Build conditional synthesis without single winner forcing."""
        ent1, ent2 = entities[0], entities[1]
        return (
            f"Evidence indicates a multi-attribute trade-off between {ent1} and {ent2}. "
            f"If accuracy is the dominant constraint, evidence favors the higher benchmark candidate; "
            f"if resource efficiency or latency is primary, the leaner model is conditionally favored."
        )
