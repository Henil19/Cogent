"""
Sub-Module 9.8d: Layer 9 Pipeline Orchestrator
Master pipeline coordinating response planning, grounded generation, citation resolution,
trust & conflict presentation, reasoning DAG exploration, counterfactual controls,
safety validation, and multi-format packaging.
Research: Attribute First (ACL 2024), Towards Trustworthy RAG (ACM CSUR 2026), MIRAGE (EMNLP 2024).
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.schemas.layer1 import StructuredUserInput
from app.schemas.layer2 import KnowledgeRetrievalPlan
from app.schemas.layer5 import VerifiedEvidenceSet
from app.schemas.layer6 import SynthesizedReasoningTrace
from app.schemas.layer7 import TrustAssessment
from app.schemas.layer8 import ExplanationPackage, ExplanationAudience
from app.schemas.layer9 import (
    UnifiedResponsePayload,
    PresentationFormat,
    ResponseValidationReport
)

from app.core.layer9.planner.response_planner import ResponsePlanner, ResponsePlan
from app.core.layer9.generator.response_generator import ResponseGenerator
from app.core.layer9.citations.citation_renderer import CitationRenderer
from app.core.layer9.trust_presentation.trust_presenter import TrustPresenter
from app.core.layer9.conflict_presentation.conflict_presenter import ConflictPresenter
from app.core.layer9.dag_explorer.dag_explorer import DAGExplorerPresenter
from app.core.layer9.counterfactual_presentation.counterfactual_presenter import CounterfactualPresenter
from app.core.layer9.validation.safety_validator import ResponseSafetyValidator
from app.core.layer9.packaging.packaging_engine import ResponsePackagingEngine


class Layer9Pipeline:
    """
    Layer 9 Master Pipeline Orchestrator.
    Consumes validated ExplanationPackage (L8), TrustAssessment (L7), and StructuredUserInput (L1),
    and emits the final UnifiedResponsePayload for the frontend user interface.
    Enforces Zero Epistemic Mutation across all operations.
    """

    def __init__(self, certainty_policy_threshold: float = 0.80, use_mock: bool = False):
        self.planner = ResponsePlanner()
        self.generator = ResponseGenerator(use_mock=use_mock)
        self.citation_renderer = CitationRenderer()
        self.trust_presenter = TrustPresenter()
        self.conflict_presenter = ConflictPresenter()
        self.dag_explorer = DAGExplorerPresenter()
        self.cf_presenter = CounterfactualPresenter()
        self.safety_validator = ResponseSafetyValidator(certainty_policy_threshold=certainty_policy_threshold)
        self.packaging_engine = ResponsePackagingEngine()

    def execute(
        self,
        explanation_pkg: ExplanationPackage,
        trust_assessment: TrustAssessment,
        user_input: Optional[StructuredUserInput] = None,
        trace: Optional[SynthesizedReasoningTrace] = None,
        plan: Optional[KnowledgeRetrievalPlan] = None,
        target_audience: Optional[ExplanationAudience] = None,
        format_type: PresentationFormat = PresentationFormat.MARKDOWN
    ) -> UnifiedResponsePayload:
        """
        Executes complete end-to-end Layer 9 response generation and presentation pipeline.
        """
        start_time = time.perf_counter()
        response_id = f"resp_{uuid.uuid4().hex[:12]}"

        session_id = getattr(explanation_pkg, "session_id", None) or (user_input.session_id if user_input else "sess_default")
        plan_id = getattr(explanation_pkg, "plan_id", None) or (plan.plan_id if plan else "plan_default")
        query_text = (
            getattr(user_input, "original_query", None)
            or getattr(user_input, "raw_query", None)
            or getattr(user_input, "processed_query", None)
            or "Scientific comparative inquiry."
        )

        # Step 1: Response Planning (Sub-Module 9.1)
        response_plan: ResponsePlan = self.planner.plan_response(
            explanation_pkg=explanation_pkg,
            trust_assessment=trust_assessment,
            user_input=user_input,
            target_audience=target_audience
        )

        # Step 2: Final Response Generation (Sub-Module 9.2)
        initial_sections = self.generator.generate_sections(
            plan=response_plan,
            explanation_pkg=explanation_pkg,
            trust_assessment=trust_assessment,
            query=query_text
        )

        # Step 3: Interactive Citation & Provenance Resolution (Sub-Module 9.3)
        final_sections, citation_registry, ref_section = self.citation_renderer.render_citations(
            sections=initial_sections,
            explanation_pkg=explanation_pkg
        )

        # Step 4: Trust & Epistemic Presentation (Sub-Module 9.4)
        trust_badges = self.trust_presenter.build_trust_badges(
            trust_assessment=trust_assessment,
            explanation_pkg=explanation_pkg
        )

        # Step 5: Dialectical Conflict Presentation (Sub-Module 9.5)
        conflict_widgets = []
        if response_plan.enable_conflict_widget:
            conflict_widgets = self.conflict_presenter.build_conflict_widgets(
                explanation_pkg=explanation_pkg,
                citation_registry=citation_registry
            )

        # Step 6: Interactive Reasoning DAG Explorer Contract (Sub-Module 9.6)
        if trace:
            reasoning_graph_ui = self.dag_explorer.build_graph_ui_contract(
                trace=trace,
                trust_assessment=trust_assessment,
                citation_registry=citation_registry
            )
        else:
            # Fallback construct from narrative steps if raw trace is omitted
            reasoning_graph_ui = self._fallback_dag_ui(explanation_pkg, trust_assessment, citation_registry)

        # Step 7: Counterfactual & Sensitivity Presentation (Sub-Module 9.7)
        cf_controls = []
        if response_plan.enable_counterfactual_controls:
            cf_controls = self.cf_presenter.build_counterfactual_controls(
                explanation_pkg=explanation_pkg
            )

        # Step 8: Safety & Consistency Validation (Sub-Module 9.8a)
        validation_report = self.safety_validator.validate_response(
            sections=final_sections,
            citation_registry=citation_registry,
            trust_assessment=trust_assessment,
            explanation_pkg=explanation_pkg,
            trust_badges=trust_badges,
            conflict_widgets=conflict_widgets
        )

        # Step 9: Multi-Fidelity Bundling & Formatting (Sub-Module 9.8b & 9.8c)
        multi_fidelity_views = self.packaging_engine.bundle_multi_fidelity_views(
            explanation_pkg=explanation_pkg
        )

        rendered_content = self.packaging_engine.export_content(
            sections=final_sections,
            citation_registry=citation_registry,
            trust_badges=trust_badges,
            format_type=format_type
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return UnifiedResponsePayload(
            response_id=response_id,
            session_id=session_id,
            plan_id=plan_id,
            query=query_text,
            active_audience=response_plan.active_audience,
            response_type=response_plan.blueprint_type,
            format=format_type,
            rendered_content=rendered_content,
            sections=final_sections,
            citation_registry=citation_registry,
            trust_badges=trust_badges,
            conflict_widgets=conflict_widgets,
            reasoning_graph_ui=reasoning_graph_ui,
            counterfactual_controls=cf_controls,
            multi_fidelity_views=multi_fidelity_views,
            validation_report=validation_report,
            presentation_metadata={
                "blueprint": response_plan.blueprint_type,
                "sections_count": len(final_sections),
                "citations_count": len(citation_registry),
                "conflicts_count": len(conflict_widgets),
                "pipeline_version": "1.0.0-layer9"
            },
            processing_time_ms=round(elapsed_ms, 2),
            created_at=datetime.now(timezone.utc).isoformat()
        )

    def _fallback_dag_ui(self, explanation_pkg, trust_assessment, citation_registry):
        """Constructs basic DAG UI contract from narrative steps when raw trace is unavailable."""
        from app.schemas.layer9 import DAGNodeUI, DAGEdgeUI, ReasoningGraphUIPayload
        nodes = []
        edges = []
        for i, step in enumerate(explanation_pkg.narrative_steps):
            node_id = getattr(step, "node_id", None) or getattr(step, "step_id", f"step_{i}")
            s_type = getattr(step, "step_type", "REASONING_STEP")
            headline = getattr(step, "headline", f"Step {i + 1}")
            claim_text = getattr(step, "narrative_text", None) or getattr(step, "prose_statement", "")
            nodes.append(
                DAGNodeUI(
                    id=node_id,
                    label=headline,
                    step_type=s_type,
                    intermediate_claim=claim_text,
                    grounding_score=1.0,
                    is_weakest_link=False,
                    citation_badges=[]
                )
            )
            if i > 0:
                prev_id = getattr(explanation_pkg.narrative_steps[i - 1], "node_id", None) or getattr(explanation_pkg.narrative_steps[i - 1], "step_id", f"step_{i - 1}")
                edges.append(
                    DAGEdgeUI(
                        source=prev_id,
                        target=node_id,
                        label="leads_to"
                    )
                )
        return ReasoningGraphUIPayload(
            nodes=nodes,
            edges=edges,
            root_claim_ids=[nodes[-1].id] if nodes else [],
            leaf_evidence_ids=[],
            weakest_link_step_id=None
        )
