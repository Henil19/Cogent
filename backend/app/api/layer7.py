"""
Layer 7: Trust Intelligence Layer API Router
Exposes endpoints for computing trust assessments, source credibility, and calibrated confidence.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.core.layer7.pipeline import Layer7Pipeline
from app.schemas.layer7 import Layer7DirectRequest, Layer7Response

router = APIRouter(prefix="/layer7", tags=["Layer 7 - Trust Intelligence"])

# Global pipeline instance
_pipeline_instance: Optional[Layer7Pipeline] = None


def get_pipeline() -> Layer7Pipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = Layer7Pipeline()
    return _pipeline_instance


def set_pipeline(pipeline: Layer7Pipeline):
    global _pipeline_instance
    _pipeline_instance = pipeline


@router.post("/assess", response_model=Layer7Response)
async def assess_trust(
    request: Layer7DirectRequest,
    pipeline: Layer7Pipeline = Depends(get_pipeline)
) -> Layer7Response:
    """
    Execute Layer 7 Trust Intelligence pipeline on a Layer 6 reasoning trace and Layer 5 evidence set.
    """
    try:
        assessment = pipeline.execute(
            trace=request.reasoning_trace,
            evidence_set=request.evidence_set,
            plan=request.plan
        )
        return Layer7Response(
            status="SUCCESS",
            trust_assessment=assessment,
            warnings=[]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Layer 7 trust assessment failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check for Layer 7 Trust Intelligence service."""
    return {
        "status": "HEALTHY",
        "layer": 7,
        "layer_name": "Trust Intelligence Layer",
        "sub_modules": [
            "7.1 Source Credibility & Authority Evaluator",
            "7.2 Evidence Reliability Analyzer",
            "7.3 Reasoning Chain Trust Evaluator",
            "7.4 Uncertainty & Epistemic Risk Engine",
            "7.5 Confidence Calibration Engine",
            "7.6 Hallucination & Unsupported-Claim Detector",
            "7.7 Trust Assessment Builder",
            "7.8 Pipeline Orchestrator"
        ]
    }
