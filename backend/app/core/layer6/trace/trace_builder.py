"""
Sub-Module 6.6: Structured Reasoning Trace Builder & Integrity Metrics
Research Basis:
- ROSCOE: A Suite of Metrics for Scoring Step-by-Step Reasoning (Golovneva et al., ICLR 2023)
- Failure Modes in Multi-Hop QA: The Weakest Link Effect (ACL 2026)
- Graph of Thoughts (Besta et al., AAAI 2024)

Validates the directed reasoning DAG, calculates structural reasoning integrity diagnostics
strictly for Layer 7 Trust Intelligence, and compiles the final logical synthesis statement.
"""

import logging
from typing import Dict, List, Optional, Tuple
import networkx as nx

from app.schemas.layer5 import VerifiedEvidenceSet
from app.schemas.layer6 import (
    ReasoningStepNode,
    SynthesizedClaim,
    ConflictReconciliation,
    ResolutionStatus,
    ReasoningIntegrityMetrics,
    ReasoningStepType
)

logger = logging.getLogger(__name__)


class TraceBuilder:
    """
    Assembles the complete proof-like reasoning graph and computes
    diagnostic telemetry features for Layer 7 confidence calibration.
    """

    def compile_trace_and_metrics(
        self,
        all_steps: List[ReasoningStepNode],
        synthesized_claims: List[SynthesizedClaim],
        reconciliations: List[ConflictReconciliation],
        unresolved_hedges: List[str],
        evidence_set: VerifiedEvidenceSet
    ) -> Tuple[ReasoningIntegrityMetrics, str]:
        """
        Validate DAG connectivity, compute ROSCOE-aligned diagnostics, and formulate final synthesis.
        
        Returns:
            Tuple of:
            - ReasoningIntegrityMetrics
            - final_synthesis_statement (formal deduction for Layer 7/8)
        """
        # 1. Build NetworkX DiGraph to validate DAG properties
        G = nx.DiGraph()
        for s in all_steps:
            G.add_node(s.step_id, step=s)
            for dep_id in s.dependent_step_ids:
                G.add_edge(dep_id, s.step_id)

        # Check for cycles; break if any cycle exists
        if not nx.is_directed_acyclic_graph(G):
            logger.warning("Reasoning graph contains a cycle! Enforcing topological tree order.")
            # Break cycles deterministically by keeping only edges to lower step_indexes
            edges_to_remove = [(u, v) for u, v in G.edges() if G.nodes[u]["step"].step_index >= G.nodes[v]["step"].step_index]
            G.remove_edges_from(edges_to_remove)

        # 2. Compute Longest Path / Logical Chain Depth
        chain_depth = 1
        try:
            if G.number_of_nodes() > 0:
                chain_depth = max(1, nx.dag_longest_path_length(G) + 1)
        except Exception as e:
            logger.warning(f"Failed to compute DAG longest path: {e}")
            chain_depth = 1

        # 3. Compute ROSCOE & Weakest Link Diagnostics
        # a. Premises grounded ratio
        all_premises_count = sum(len(s.premise_claim_ids) for s in all_steps)
        grounded_premises_count = sum(
            len(s.premise_claim_ids) for s in all_steps if s.step_grounding_score >= 0.50
        )
        premises_grounded_ratio = (
            grounded_premises_count / all_premises_count if all_premises_count > 0 else 1.0
        )

        # b. Claim support ratio (Descriptive evidence balance diagnostic, NOT proof of truth)
        total_supp = sum(len(c.supporting_evidence_ids) for c in synthesized_claims)
        total_opp = sum(len(c.opposing_evidence_ids) for c in synthesized_claims)
        claim_support_ratio = (
            total_supp / (total_supp + total_opp) if (total_supp + total_opp) > 0 else 1.0
        )

        # c. Conflict reconciliation ratio
        total_conflicts = len(reconciliations)
        reconciled_count = sum(
            1 for r in reconciliations
            if r.resolution_status in (ResolutionStatus.RECONCILED, ResolutionStatus.CONTEXTUAL_DIFFERENCE, ResolutionStatus.TEMPORAL_SUPERSEDENCE)
        )
        conflict_ratio = (
            reconciled_count / total_conflicts if total_conflicts > 0 else 1.0
        )

        # d. Weakest Link Score (minimum premise grounding score along entire DAG)
        step_scores = [s.step_grounding_score for s in all_steps if s.step_type != ReasoningStepType.EPISTEMIC_HEDGE]
        weakest_link = min(step_scores) if step_scores else 1.0

        # e. Unresolved contradictions check
        has_unresolved = any(
            r.resolution_status in (ResolutionStatus.GENUINE_CONTRADICTION, ResolutionStatus.INSUFFICIENT_EVIDENCE)
            for r in reconciliations
        )

        metrics = ReasoningIntegrityMetrics(
            total_reasoning_steps=len(all_steps),
            premises_grounded_ratio=round(float(premises_grounded_ratio), 4),
            claim_support_ratio=round(float(claim_support_ratio), 4),
            conflict_reconciliation_ratio=round(float(conflict_ratio), 4),
            weakest_link_score=round(float(weakest_link), 4),
            epistemic_gap_count=len(unresolved_hedges),
            logical_chain_depth=chain_depth,
            has_unresolved_contradictions=has_unresolved
        )

        # 4. Formulate Final Logical Synthesis Statement
        final_statement = self._formulate_synthesis_statement(
            all_steps=all_steps,
            synthesized_claims=synthesized_claims,
            reconciliations=reconciliations,
            unresolved_hedges=unresolved_hedges
        )

        logger.debug(f"TraceBuilder finalized trace: depth={chain_depth}, weakest_link={weakest_link:.2f}")
        return metrics, final_statement

    def _formulate_synthesis_statement(
        self,
        all_steps: List[ReasoningStepNode],
        synthesized_claims: List[SynthesizedClaim],
        reconciliations: List[ConflictReconciliation],
        unresolved_hedges: List[str]
    ) -> str:
        """Construct the unified formal deductive synthesis statement."""
        components = []

        # 1. Primary deductions from synthesized claims
        substantive_claims = [c.statement for c in synthesized_claims if c.status != "EPISTEMIC_HEDGE"]
        if substantive_claims:
            components.append(f"Derived Deductions: {' '.join(substantive_claims)}")
        elif all_steps:
            # Fallback to last intermediate conclusion
            components.append(f"Deduction: {all_steps[-1].intermediate_claim}")

        # 2. Conflict reconciliations
        if reconciliations:
            rec_texts = [f"[{r.resolution_status.value}] {r.reconciliation_analysis}" for r in reconciliations]
            components.append(f"Dialectical Reconciliations: {' '.join(rec_texts)}")

        # 3. Epistemic hedges
        if unresolved_hedges:
            components.append(f"Epistemic Boundaries: {' '.join(unresolved_hedges)}")

        return " | ".join(components) if components else "Evidence processed; no formal deduction possible."
