"""
Cogent Layer 8: Dynamic Explainability & Attribution Layer
Orchestrates claim attribution, DAG narrative synthesis, citation mapping,
uncertainty explanation, dialectical reconciliation, counterfactuals,
and 6-gate explanation integrity auditing.
"""

from app.core.layer8.pipeline import Layer8Pipeline
from app.core.layer8.attribution.claim_attribution_engine import ClaimAttributionEngine
from app.core.layer8.narrative.dag_narrative_engine import DAGNarrativeEngine
from app.core.layer8.citations.citation_mapping_engine import CitationMappingEngine
from app.core.layer8.uncertainty_explanation.uncertainty_explanation_engine import UncertaintyExplanationEngine
from app.core.layer8.dialectical.dialectical_explanation_engine import DialecticalExplanationEngine
from app.core.layer8.counterfactual.counterfactual_engine import CounterfactualExplanationEngine
from app.core.layer8.adaptation.audience_adaptation_engine import AudienceAdaptationEngine
from app.core.layer8.validation.explanation_validator import ExplanationValidator

__all__ = [
    "Layer8Pipeline",
    "ClaimAttributionEngine",
    "DAGNarrativeEngine",
    "CitationMappingEngine",
    "UncertaintyExplanationEngine",
    "DialecticalExplanationEngine",
    "CounterfactualExplanationEngine",
    "AudienceAdaptationEngine",
    "ExplanationValidator",
]
