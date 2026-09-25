"""
API Endpoints for Layer 8: Dynamic Explainability & Attribution Layer
Provides routes for generating faithful, audience-adapted, counterfactual explanations
and validating explanation integrity.
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.layer5 import VerifiedEvidenceSet
from app.schemas.layer6 import SynthesizedReasoningTrace
from app.schemas.layer7 import TrustAssessment
from app.schemas.layer8 import (
    Layer8DirectRequest,
    Layer8Response,
    ExplanationPackage
)
from app.core.layer8.pipeline import Layer8Pipeline

router = APIRouter(prefix="/layer8", tags=["Layer 8 - Dynamic Explainability & Attribution"])
pipeline = Layer8Pipeline()


@router.post(
    "/explain",
    response_model=Layer8Response,
    status_code=status.HTTP_200_OK,
    summary="Generate faithful, multi-fidelity, counterfactual explanation package"
)
async def generate_explanation(request: Layer8DirectRequest):
    """
    Synthesizes and validates an ExplanationPackage from upstream Layer 6 reasoning trace,
    Layer 7 trust assessment, and Layer 5 verified evidence.
    """
    try:
        trace = SynthesizedReasoningTrace(**request.reasoning_trace)
        trust = TrustAssessment(**request.trust_assessment)
        evidence = VerifiedEvidenceSet(**request.evidence_set)

        pkg = pipeline.execute(
            trace=trace,
            trust_assessment=trust,
            evidence_set=evidence,
            audience=request.audience
        )
        return Layer8Response(
            status="SUCCESS",
            explanation_package=pkg,
            message="Explanation package successfully synthesized and verified through 6-gate audit."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Layer 8 explanation synthesis failed: {str(e)}"
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Layer 8 Health Check"
)
async def layer8_health():
    """
    Returns operational readiness status for Layer 8 sub-engines.
    """
    return {
        "status": "healthy",
        "layer": "Layer 8: Dynamic Explainability & Attribution",
        "sub_modules": [
            "8.1 Claim Attribution Engine",
            "8.2 Faithful DAG-to-Narrative Engine",
            "8.3 Evidence & Citation Mapping Engine",
            "8.4 Trust, Conflict & Uncertainty Explanation Engine",
            "8.5 Dialectical & Contrastive Explanation Engine",
            "8.6 Counterfactual & Sensitivity Explanation Engine",
            "8.7 Multi-Fidelity & Audience Adaptation Engine",
            "8.8 Explanation Integrity Validator & Pipeline Orchestrator"
        ],
        "validation_gates": [
            "Claim Fidelity",
            "Evidence Fidelity",
            "Reasoning Fidelity",
            "Citation Fidelity",
            "Conflict Fidelity",
            "Confidence-Hedging Fidelity"
        ]
    }
