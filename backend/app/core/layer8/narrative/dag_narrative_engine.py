"""
Sub-Module 8.2: Faithful DAG-to-Narrative Engine
Translates the Layer 6 reasoning DAG into a structured, step-by-step narrative walkthrough
by topological traversal, strictly maintaining structural correspondence without post-hoc fabulation.
"""

from typing import List, Dict, Set
from collections import deque
from app.schemas.layer6 import SynthesizedReasoningTrace, ReasoningStepNode, ReasoningStepType
from app.schemas.layer8 import NarrativeStep, EvidenceAttribution


class DAGNarrativeEngine:
    """
    Traverses the explicit Layer 6 reasoning DAG in topological order and generates
    structured narrative steps. Every narrative step corresponds 1-to-1 with a DAG node.
    """

    def __init__(self):
        pass

    def build_narrative_steps(
        self,
        trace: SynthesizedReasoningTrace,
        claim_attributions: Dict[str, List[EvidenceAttribution]]
    ) -> List[NarrativeStep]:
        """
        Generates topologically ordered NarrativeStep items corresponding to DAG nodes.
        """
        nodes = trace.reasoning_steps
        if not nodes:
            return []

        # 1. Topological Sorting using in-degree
        node_lookup: Dict[str, ReasoningStepNode] = {n.step_id: n for n in nodes}
        in_degree: Dict[str, int] = {n.step_id: 0 for n in nodes}
        adjacency: Dict[str, List[str]] = {n.step_id: [] for n in nodes}

        for n in nodes:
            for dep in n.dependent_step_ids:
                if dep in node_lookup:
                    adjacency[dep].append(n.step_id)
                    in_degree[n.step_id] += 1

        queue = deque([n_id for n_id, deg in in_degree.items() if deg == 0])
        ordered_nodes: List[ReasoningStepNode] = []

        while queue:
            curr_id = queue.popleft()
            ordered_nodes.append(node_lookup[curr_id])
            for neighbor in adjacency[curr_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Fallback if cycles existed (though L6 checks cycles)
        if len(ordered_nodes) < len(nodes):
            unvisited = [n for n in nodes if n not in ordered_nodes]
            ordered_nodes.extend(unvisited)

        # 2. Build Evidence-to-Token lookup
        ev_to_token: Dict[str, str] = {}
        for attrs in claim_attributions.values():
            for a in attrs:
                ev_to_token[a.evidence_id] = a.citation_token

        # 3. Compile Narrative Steps
        narrative_steps: List[NarrativeStep] = []
        step_idx = 1

        for node in ordered_nodes:
            step_type = node.step_type.value if hasattr(node.step_type, "value") else str(node.step_type)
            headline, narrative_text, qualifier = self._synthesize_step_narrative(node, ev_to_token)

            node_evidence = getattr(node, "evidence_ids", None) or getattr(node, "premise_ids", [])
            tokens = [ev_to_token[eid] for eid in node_evidence if eid in ev_to_token]

            n_step = NarrativeStep(
                step_index=step_idx,
                node_id=node.step_id,
                step_type=step_type,
                headline=headline,
                narrative_text=narrative_text,
                premise_node_ids=node.dependent_step_ids,
                cited_evidence_ids=node_evidence,
                citation_tokens=tokens,
                epistemic_qualifier=qualifier
            )
            narrative_steps.append(n_step)
            step_idx += 1

        return narrative_steps

    def _synthesize_step_narrative(
        self,
        node: ReasoningStepNode,
        ev_to_token: Dict[str, str]
    ) -> tuple[str, str, str]:
        """
        Translates node metadata into coherent, grounded narrative prose and qualitative header.
        """
        step_type = node.step_type.value if hasattr(node.step_type, "value") else str(node.step_type)
        node_evidence = getattr(node, "evidence_ids", None) or getattr(node, "premise_ids", [])
        tokens = [ev_to_token[eid] for eid in node_evidence if eid in ev_to_token]
        citation_suffix = f" {', '.join(tokens)}" if tokens else ""
        op_name = getattr(node, "reasoning_operation", None) or getattr(node, "operation_name", "Inference Step")

        if step_type in ("EVIDENCE_LINK", "PREMISE_LEAF"):
            headline = f"Empirical Observation: {op_name}"
            narrative = (
                f"From direct evidence grounding, we establish the leaf premise: "
                f"'{node.intermediate_claim}'.{citation_suffix}"
            )
            qualifier = "ESTABLISHED"

        elif step_type in ("MULTI_HOP_INFERENCE", "MULTI_HOP_DEDUCTION", "CLAIM_COMBINATION"):
            headline = f"Multi-Hop Deductive Bridge: {op_name}"
            narrative = (
                f"Combining prior observations, we infer the intermediate conclusion: "
                f"'{node.intermediate_claim}'.{citation_suffix}"
            )
            qualifier = "INFERRED"

        elif step_type in ("CONFLICT_RECONCILIATION", "CONFLICT_ANALYSIS"):
            headline = f"Dialectical Reconciliation: {op_name}"
            narrative = (
                f"Addressing contradictory evidence across evaluated sources: "
                f"'{node.intermediate_claim}'.{citation_suffix} "
                f"Both empirical perspectives are preserved under their respective operating bounds."
            )
            qualifier = "DIALECTICAL"

        elif step_type in ("COMPARISON", "TRADEOFF_ANALYSIS", "COMPARATIVE_EVALUATION"):
            headline = f"Comparative Trade-Off: {op_name}"
            narrative = (
                f"Evaluating entities along defined criteria matrix: "
                f"'{node.intermediate_claim}'.{citation_suffix}"
            )
            qualifier = "COMPARATIVE"

        elif step_type in ("EPISTEMIC_HEDGE", "EPISTEMIC_GAP_BOUNDING"):
            headline = f"Epistemic Scope Boundary: {op_name}"
            narrative = (
                f"Delimiting what cannot be definitively concluded from current evidence: "
                f"'{node.intermediate_claim}'.{citation_suffix}"
            )
            qualifier = "QUALIFIED"

        else: # CONCLUSION / SYNTHESIS_CONCLUSION
            headline = f"Synthesis Conclusion: {op_name}"
            narrative = (
                f"Synthesizing the complete reasoning chain, Cogent concludes: "
                f"'{node.intermediate_claim}'.{citation_suffix}"
            )
            qualifier = "SYNTHESIZED"

        return headline, narrative, qualifier
