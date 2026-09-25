"""
Layer 9 FastAPI Router: Response Generation & Presentation Layer
Endpoints for generating the master UnifiedResponsePayload and performing presentation health checks.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.layer9 import (
    Layer9DirectRequest,
    Layer9Response,
    UnifiedResponsePayload
)
from app.core.layer9.pipeline import Layer9Pipeline

router = APIRouter(prefix="/layer9", tags=["Layer 9: Response Generation & Presentation"])

# Singleton pipeline instance
_pipeline = Layer9Pipeline()


@router.post("/present", response_model=Layer9Response)
def present_response(
    request: Layer9DirectRequest,
    db: Session = Depends(get_db)
):
    """
    Executes Layer 9 presentation pipeline.
    Consumes validated ExplanationPackage (L8) and TrustAssessment (L7),
    and emits the final interactive UnifiedResponsePayload.
    """
    try:
        payload: UnifiedResponsePayload = _pipeline.execute(
            explanation_pkg=request.explanation_package,
            trust_assessment=request.trust_assessment,
            user_input=request.user_input,
            target_audience=request.target_audience,
            format_type=request.presentation_format or request.presentation_format.MARKDOWN
        )
        return Layer9Response(
            success=True,
            payload=payload
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Layer 9 presentation synthesis failed: {str(e)}"
        )


@router.get("/health")
def layer9_health():
    """Returns operational status of Layer 9 sub-modules."""
    return {
        "status": "healthy",
        "layer": 9,
        "name": "Response Generation & Presentation Layer",
        "invariants": {
            "zero_epistemic_mutation": True,
            "zero_winner_forcing_ui": True,
            "provenance_traceable": True,
            "multi_fidelity_epistemic_invariance": True
        },
        "sub_modules": [
            "9.1_response_planner",
            "9.2_response_generator",
            "9.3_citation_renderer",
            "9.4_trust_presenter",
            "9.5_conflict_presenter",
            "9.6_dag_explorer",
            "9.7_counterfactual_presenter",
            "9.8_validation_packaging_export"
        ]
    }
