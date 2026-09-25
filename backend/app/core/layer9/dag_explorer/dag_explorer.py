"""
Sub-Module 9.6: Interactive Reasoning DAG Explorer Contract
Converts the explicit Layer 6 reasoning trace into a rich graph UI contract (nodes and edges)
for interactive canvas renderers (React Flow, D3, Vis.js).
Research: Entailment Trees (EMNLP 2021), Weakest Link (ACL 2026), ROSCOE (ICLR 2023).
"""

from typing import List, Dict, Optional
from app.schemas.layer6 import SynthesizedReasoningTrace, ReasoningStepNode
from app.schemas.layer7 import TrustAssessment
from app.schemas.layer9 import DAGNodeUI, DAGEdgeUI, ReasoningGraphUIPayload, CitationBadgeEntry


class DAGExplorerPresenter:
    """
    Sub-Module 9.6: Generates visual tree/graph visualization contracts from reasoning DAG.
    Does NOT modify the reasoning DAG; visualizes the existing structure.
    """

    def __init__(self):
        pass

    def build_graph_ui_contract(
        self,
        trace: SynthesizedReasoningTrace,
        trust_assessment: TrustAssessment,
        citation_registry: List[CitationBadgeEntry]
    ) -> ReasoningGraphUIPayload:
        """
        Derives DAG nodes, edges, root claims, leaf evidence, and bottleneck markers.
        """
        weakest_step_id = (
            getattr(trust_assessment.reasoning_assessment, "weakest_link_step_id", None) or
            getattr(trust_assessment.reasoning_assessment, "weakest_step_id", None)
        )

        # Build evidence to citation badges map
        ev_to_badges: Dict[str, List[int]] = {}
        for c in citation_registry:
            ev_to_badges.setdefault(c.evidence_id, []).append(c.citation_number)

        nodes_ui: List[DAGNodeUI] = []
        edges_ui: List[DAGEdgeUI] = []
        leaf_evidence_ids: List[str] = []
        all_sources: set = set()
        all_targets: set = set()

        for step in trace.reasoning_steps:
            # Check citations associated with evidence_ids in this step
            badges = []
            ev_ids = getattr(step, "evidence_ids", [])
            for ev in ev_ids:
                badges.extend(ev_to_badges.get(ev, []))
                if ev not in leaf_evidence_ids:
                    leaf_evidence_ids.append(ev)

            is_weakest = (step.step_id == weakest_step_id)
            label = getattr(step, "reasoning_operation", step.step_type.value if hasattr(step.step_type, "value") else str(step.step_type))

            node_ui = DAGNodeUI(
                id=step.step_id,
                label=label,
                step_type=step.step_type.value if hasattr(step.step_type, "value") else str(step.step_type),
                intermediate_claim=step.intermediate_claim,
                grounding_score=round(getattr(step, "step_grounding_score", 1.0), 2),
                is_weakest_link=is_weakest,
                citation_badges=list(dict.fromkeys(badges))
            )
            nodes_ui.append(node_ui)

            # Build edges from dependent_step_ids
            dep_ids = getattr(step, "dependent_step_ids", [])
            for dep_id in dep_ids:
                edge = DAGEdgeUI(
                    source=dep_id,
                    target=step.step_id,
                    label="entails"
                )
                edges_ui.append(edge)
                all_sources.add(dep_id)
                all_targets.add(step.step_id)

        # If no explicit dependencies exist in upstream trace, synthesize sequential inferential edges
        if not edges_ui and len(nodes_ui) > 1:
            for i in range(len(nodes_ui) - 1):
                edges_ui.append(DAGEdgeUI(
                    source=nodes_ui[i].id,
                    target=nodes_ui[i + 1].id,
                    label="leads_to"
                ))
                all_sources.add(nodes_ui[i].id)
                all_targets.add(nodes_ui[i + 1].id)

        # Root claims: Nodes that are not dependencies of any other node
        root_claim_ids = [
            n.id for n in nodes_ui if n.id not in all_sources
        ]
        if not root_claim_ids and nodes_ui:
            root_claim_ids = [nodes_ui[-1].id]

        return ReasoningGraphUIPayload(
            nodes=nodes_ui,
            edges=edges_ui,
            root_claim_ids=root_claim_ids,
            leaf_evidence_ids=leaf_evidence_ids,
            weakest_link_step_id=weakest_step_id
        )
