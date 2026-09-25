"""
Sub-Module 7.3: Reasoning Chain Trust Evaluator
Research Basis:
- Confidence over Time: Confidence Calibration with Temporal Logic for LLM Reasoning (Findings ACL 2026)
- Failure Modes in Multi-Hop QA: The Weakest Link Effect (ACL 2026)
- RLSeek: Evidence-Grounded Reasoning for RAG Hallucination Detection (ACL 2026)

Traverses the Layer 6 reasoning DAG to evaluate premise grounding continuity,
propagates weakest-link vulnerabilities, and models step-by-step trust decay.
"""

import logging
from typing import Dict, List, Optional
import networkx as nx

from app.schemas.layer6 import SynthesizedReasoningTrace, ReasoningStepNode, ReasoningStepType
from app.schemas.layer7 import SourceCredibilityAssessment, StepTrustScore, ReasoningTrustAssessment

logger = logging.getLogger(__name__)

DEFAULT_DEPTH_DISCOUNT = 0.95  # Gamma step-transition discount factor


class ReasoningTrustEvaluator:
    """
    Evaluates step-by-step and path-level structural trust across the reasoning DAG.
    """

    def __init__(self, depth_discount: float = DEFAULT_DEPTH_DISCOUNT):
        self.depth_discount = depth_discount

    def evaluate_reasoning_trust(
        self,
        trace: SynthesizedReasoningTrace,
        source_assessments: List[SourceCredibilityAssessment]
    ) -> ReasoningTrustAssessment:
        """
        Compute step-level trust and overall path trust across all reasoning steps.
        """
        # Map source IDs / URIs to credibility scores
        source_cred_map = {src.source_id: src.overall_credibility for src in source_assessments}
        uri_cred_map = {src.source_uri: src.overall_credibility for src in source_assessments}

        # Build NetworkX DiGraph to model dependencies
        G = nx.DiGraph()
        step_map: Dict[str, ReasoningStepNode] = {}
        for s in trace.reasoning_steps:
            step_map[s.step_id] = s
            G.add_node(s.step_id, step=s)
            for dep_id in s.dependent_step_ids:
                G.add_edge(dep_id, s.step_id)

        step_scores: List[StepTrustScore] = []
        step_trust_lookup: Dict[str, float] = {}

        # 1. Evaluate individual step trust in topological order
        sorted_step_ids = list(nx.topological_sort(G)) if nx.is_directed_acyclic_graph(G) else [s.step_id for s in trace.reasoning_steps]

        avg_src_cred = (
            sum(src.overall_credibility for src in source_assessments) / len(source_assessments)
            if source_assessments else 0.85
        )

        for s_id in sorted_step_ids:
            step = step_map[s_id]
            grounding = step.step_grounding_score

            # Compute source credibility weight for this step's evidence
            ev_creds = []
            for ev_id in step.evidence_ids:
                # Find matching source score
                matching = [c for s_key, c in source_cred_map.items() if ev_id in s_key or s_key in ev_id]
                ev_creds.append(matching[0] if matching else avg_src_cred)

            source_weight = sum(ev_creds) / len(ev_creds) if ev_creds else avg_src_cred

            # Calculate upstream vulnerability from parent dependencies
            parent_trusts = [step_trust_lookup.get(p_id, 1.0) for p_id in step.dependent_step_ids]
            upstream_min = min(parent_trusts) if parent_trusts else 1.0
            dependency_vuln = max(0.0, 1.0 - upstream_min)

            # Step trust formula (Weakest Link + Source Credibility + Upstream Propagation)
            if step.step_type == ReasoningStepType.EPISTEMIC_HEDGE:
                computed_trust = 0.50  # Neutral trust for explicit hedges
            else:
                raw_trust = (0.50 * grounding + 0.35 * source_weight + 0.15 * upstream_min)
                # Penalize steps with unresolved issues
                if step.unresolved_issues:
                    raw_trust *= 0.90
                computed_trust = max(0.0, min(1.0, raw_trust))

            step_trust_lookup[s_id] = computed_trust

            score_item = StepTrustScore(
                step_id=s_id,
                step_type=step.step_type.value if hasattr(step.step_type, "value") else str(step.step_type),
                step_grounding_score=round(grounding, 4),
                source_credibility_weight=round(source_weight, 4),
                computed_step_trust=round(computed_trust, 4),
                dependency_vulnerability=round(dependency_vuln, 4)
            )
            step_scores.append(score_item)

        # 2. Identify Weakest Link in Reasoning Graph
        non_hedge_scores = [s for s in step_scores if s.step_type != "EPISTEMIC_HEDGE"]
        if non_hedge_scores:
            weakest_step = min(non_hedge_scores, key=lambda s: s.computed_step_trust)
            weakest_link_id = weakest_step.step_id
            weakest_link_score = weakest_step.computed_step_trust
        else:
            weakest_link_id = step_scores[0].step_id if step_scores else "none"
            weakest_link_score = 0.50

        # 3. Path-Level Trust with Depth Decay (Confidence over Time 2026)
        chain_depth = max(1, trace.integrity_metrics.logical_chain_depth)
        decay_factor = self.depth_discount ** (chain_depth - 1)
        path_trust = weakest_link_score * decay_factor

        avg_trust = sum(s.computed_step_trust for s in step_scores) / len(step_scores) if step_scores else 0.50
        is_intact = weakest_link_score >= 0.40 and not trace.integrity_metrics.has_unresolved_contradictions

        assessment = ReasoningTrustAssessment(
            step_trust_scores=step_scores,
            weakest_link_step_id=weakest_link_id,
            weakest_link_score=round(weakest_link_score, 4),
            average_chain_trust=round(avg_trust, 4),
            path_trust_score=round(path_trust, 4),
            is_chain_intact=is_intact
        )

        logger.debug(f"ReasoningTrustEvaluator evaluated {len(step_scores)} steps. Weakest link: {weakest_link_score:.2f}, Path trust: {path_trust:.2f}")
        return assessment
