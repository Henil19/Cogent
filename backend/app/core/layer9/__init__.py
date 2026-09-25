"""
Cogent Layer 9: Response Generation & Presentation Layer
Transforms verified Layer 8 ExplanationPackage into an interactive, citation-linked,
multi-fidelity, and exportable UnifiedResponsePayload.
Enforces Zero Epistemic Mutation.
"""

from app.core.layer9.pipeline import Layer9Pipeline
from app.core.layer9.planner.response_planner import ResponsePlanner, ResponsePlan
from app.core.layer9.generator.response_generator import ResponseGenerator
from app.core.layer9.citations.citation_renderer import CitationRenderer
from app.core.layer9.trust_presentation.trust_presenter import TrustPresenter
from app.core.layer9.conflict_presentation.conflict_presenter import ConflictPresenter
from app.core.layer9.dag_explorer.dag_explorer import DAGExplorerPresenter
from app.core.layer9.counterfactual_presentation.counterfactual_presenter import CounterfactualPresenter
from app.core.layer9.validation.safety_validator import ResponseSafetyValidator
from app.core.layer9.packaging.packaging_engine import ResponsePackagingEngine

__all__ = [
    "Layer9Pipeline",
    "ResponsePlanner",
    "ResponsePlan",
    "ResponseGenerator",
    "CitationRenderer",
    "TrustPresenter",
    "ConflictPresenter",
    "DAGExplorerPresenter",
    "CounterfactualPresenter",
    "ResponseSafetyValidator",
    "ResponsePackagingEngine",
]
