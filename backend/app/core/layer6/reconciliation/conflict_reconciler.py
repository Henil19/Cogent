"""
Sub-Module 6.3: Dialectical Conflict Reconciler
Research Basis:
- MAGIC: Inter-Context Conflicts in RAG (EMNLP Findings 2025)
- ConfRAG: Reasoning over Conflicting References (ACL 2026)
- ReAgent: Reversible Reasoning & Epistemic Revision (EMNLP 2025)

Analyzes contradiction edges detected by Layer 5 without arbitrarily declaring a winner (Zero Winner Forcing).
Explains why discrepancies arise (benchmark dataset differences, temporal updates, evaluation conditions)
and produces formal ConflictReconciliation records and dialectical reasoning steps.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple

from app.core.llm_client import LLMClient
from app.schemas.layer5 import VerifiedEvidenceSet, ConflictEdge, ConflictSeverity, EvidenceItem
from app.schemas.layer6 import (
    ConflictReconciliation,
    ResolutionStatus,
    ReasoningStepNode,
    ReasoningStepType
)

logger = logging.getLogger(__name__)


class ConflictReconciler:
    """
    Reconciles conflicting claims through dialectical contextualization
    preserving opposing evidence without winner forcing.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def reconcile_conflicts(
        self,
        evidence_set: VerifiedEvidenceSet,
        start_step_index: int
    ) -> Tuple[List[ConflictReconciliation], List[ReasoningStepNode]]:
        """
        Evaluate all conflict edges from Layer 5 and construct reconciliation records and reasoning steps.
        
        Returns:
            Tuple of:
            - List of ConflictReconciliation contracts
            - List of ReasoningStepNode (type=CONFLICT_RECONCILIATION)
        """
        reconciliations: List[ConflictReconciliation] = []
        reasoning_steps: List[ReasoningStepNode] = []
        curr_step = start_step_index

        if not evidence_set.has_conflicts or not evidence_set.conflict_edges:
            return reconciliations, reasoning_steps

        # Build evidence lookup
        ev_map: Dict[str, EvidenceItem] = {ev.evidence_id: ev for ev in evidence_set.selected_evidence}

        for idx, edge in enumerate(evidence_set.conflict_edges):
            ev_a = ev_map.get(edge.evidence_a_id)
            ev_b = ev_map.get(edge.evidence_b_id)

            # Retrieve text of conflicting claims
            claim_a_text = self._find_claim_text(ev_a, edge.claim_a_id)
            claim_b_text = self._find_claim_text(ev_b, edge.claim_b_id)

            if not claim_a_text or not claim_b_text:
                continue

            # Diagnose resolution category and contextual factors
            status, factors, analysis = self._diagnose_conflict(
                claim_a_text=claim_a_text,
                claim_b_text=claim_b_text,
                ev_a=ev_a,
                ev_b=ev_b,
                severity=edge.severity
            )

            edge_id = getattr(edge, "conflict_id", getattr(edge, "conflict_edge_id", f"cfl_{idx}"))
            rec_id = f"rec_{idx}_{edge_id[:8]}"
            reconciliation = ConflictReconciliation(
                reconciliation_id=rec_id,
                conflict_edge_id=edge_id,
                claim_a_id=edge.claim_a_id,
                claim_b_id=edge.claim_b_id,
                claim_a_text=claim_a_text,
                claim_b_text=claim_b_text,
                severity=edge.severity,
                resolution_status=status,
                contextual_factors=factors,
                reconciliation_analysis=analysis,
                supporting_evidence_ids=[edge.evidence_a_id, edge.evidence_b_id],
                source_a_title=getattr(ev_a, "title", None) or "Empirical Study A",
                source_b_title=getattr(ev_b, "title", None) or "Empirical Study B"
            )
            reconciliations.append(reconciliation)

            # Build formal ReasoningStepNode for this dialectical reconciliation
            step_node = ReasoningStepNode(
                step_id=f"step_conflict_{curr_step}",
                step_index=curr_step,
                step_type=ReasoningStepType.CONFLICT_RECONCILIATION,
                sub_query_id=ev_a.sub_query_id if ev_a else None,
                premise_claim_ids=[edge.claim_a_id, edge.claim_b_id],
                evidence_ids=[edge.evidence_a_id, edge.evidence_b_id],
                dependent_step_ids=[],
                reasoning_operation=f"Dialectical reconciliation ({status.value}): Zero Winner Forcing",
                intermediate_claim=analysis,
                supporting_claim_ids=[edge.claim_a_id, edge.claim_b_id],
                opposing_claim_ids=[],
                unresolved_issues=[f"Status: {status.value}"],
                step_grounding_score=0.85
            )
            reasoning_steps.append(step_node)
            curr_step += 1

        logger.debug(f"ConflictReconciler generated {len(reconciliations)} dialectical conflict reconciliations.")
        return reconciliations, reasoning_steps

    def _find_claim_text(self, ev: Optional[EvidenceItem], claim_id: str) -> Optional[str]:
        if not ev:
            return None
        for clm in ev.atomic_claims:
            if clm.claim_id == claim_id:
                return clm.claim_text
        if getattr(ev, "quoted_text", None):
            return ev.quoted_text
        if getattr(ev, "content", None):
            return ev.content[:150]
        return None

    def _diagnose_conflict(
        self,
        claim_a_text: str,
        claim_b_text: str,
        ev_a: Optional[EvidenceItem],
        ev_b: Optional[EvidenceItem],
        severity: ConflictSeverity
    ) -> Tuple[ResolutionStatus, List[str], str]:
        """
        Diagnose the reason for contradiction using metadata, numeric extraction, and conditions.
        """
        # Deterministic diagnostic logic (Zero Winner Forcing)
        factors = []
        
        # 1. Temporal Analysis
        date_a = getattr(ev_a, "publication_date", None) if ev_a else None
        date_b = getattr(ev_b, "publication_date", None) if ev_b else None

        if date_a and date_b and date_a != date_b:
            factors.append(f"Publication dates diverge: Source A ({date_a}) vs Source B ({date_b})")
            if date_a > date_b:
                newer, older = "Source A", "Source B"
                newer_date, older_date = date_a, date_b
            else:
                newer, older = "Source B", "Source A"
                newer_date, older_date = date_b, date_a

            analysis = (
                f"{newer} ({newer_date}) provides updated findings compared to {older} ({older_date}). "
                f"In accordance with Zero Winner Forcing, both findings are retained and documented to reflect temporal evolution without discarding prior baseline."
            )
            return ResolutionStatus.TEMPORAL_SUPERSEDENCE, factors, analysis

        # 2. Contextual / Benchmark Dataset Variance
        title_a = getattr(ev_a, "title", "Source A") if ev_a else "Source A"
        title_b = getattr(ev_b, "title", "Source B") if ev_b else "Source B"
        factors.append(f"Source context: '{title_a}' vs '{title_b}'")

        # Check numerical metric clash (e.g. 92% vs 88%)
        nums_a = re.findall(r"\b\d+(?:\.\d+)?\%?\b", claim_a_text)
        nums_b = re.findall(r"\b\d+(?:\.\d+)?\%?\b", claim_b_text)

        if nums_a and nums_b and nums_a != nums_b:
            val_a = nums_a[0]
            val_b = nums_b[0]
            factors.append(f"Opposing quantitative metrics: {val_a} vs {val_b}")
            analysis = (
                f"{title_a} reports {val_a}, whereas {title_b} reports {val_b}. "
                f"The variance indicates evaluation under differing test conditions or benchmark distributions. "
                f"In accordance with Zero Winner Forcing, both empirical measurements are retained."
            )
            return ResolutionStatus.CONTEXTUAL_DIFFERENCE, factors, analysis

        # 3. Direct Qualitative Contradiction
        factors.append("Direct factual polarity divergence")
        analysis = (
            f"Direct divergence observed between claim '{claim_a_text}' and '{claim_b_text}'. "
            f"Evidence does not provide sufficient metadata to adjudicate superiority; both viewpoints are preserved."
        )
        return ResolutionStatus.GENUINE_CONTRADICTION, factors, analysis

    def _diagnose_with_llm(
        self,
        claim_a: str,
        claim_b: str,
        ev_a: Optional[EvidenceItem],
        ev_b: Optional[EvidenceItem]
    ) -> Optional[Tuple[ResolutionStatus, List[str], str]]:
        """Diagnose conflict via LLM structured JSON generation."""
        system_prompt = (
            "You are a dialectical conflict analyst in an explainable AI system (MAGIC 2025, ConfRAG 2026). "
            "You must follow Zero Winner Forcing: do NOT pick an arbitrary winner. "
            "Analyze why two claims diverge based on their context, dates, and methodologies. "
            "Return JSON: {"
            "'status': 'CONTEXTUAL_DIFFERENCE'|'TEMPORAL_SUPERSEDENCE'|'GENUINE_CONTRADICTION'|'PARTIALLY_RECONCILED', "
            "'contextual_factors': list[str], "
            "'analysis': str"
            "}"
        )
        user_prompt = (
            f"Claim A: {claim_a} (Source: {ev_a.title if ev_a else 'A'}, Date: {getattr(ev_a, 'publication_date', 'N/A')})\n"
            f"Claim B: {claim_b} (Source: {ev_b.title if ev_b else 'B'}, Date: {getattr(ev_b, 'publication_date', 'N/A')})"
        )
        data = self.llm_client.generate_structured_json(system_prompt, user_prompt)
        if not data or "status" not in data:
            return None

        status_str = str(data.get("status", "")).upper()
        status_map = {
            "CONTEXTUAL_DIFFERENCE": ResolutionStatus.CONTEXTUAL_DIFFERENCE,
            "TEMPORAL_SUPERSEDENCE": ResolutionStatus.TEMPORAL_SUPERSEDENCE,
            "GENUINE_CONTRADICTION": ResolutionStatus.GENUINE_CONTRADICTION,
            "PARTIALLY_RECONCILED": ResolutionStatus.PARTIALLY_RECONCILED,
            "RECONCILED": ResolutionStatus.RECONCILED
        }
        res_status = status_map.get(status_str, ResolutionStatus.CONTEXTUAL_DIFFERENCE)
        factors = data.get("contextual_factors", [])
        analysis = data.get("analysis", "")
        if analysis:
            return res_status, factors, analysis
        return None
