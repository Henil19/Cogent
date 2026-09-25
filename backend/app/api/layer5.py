"""
Layer 5 API Endpoints
Provides HTTP interfaces for evidence intelligence, factual grounding, and conflict graph mapping.
"""

import os
import logging
from fastapi import APIRouter, HTTPException, status
from app.config import Settings
from app.schemas.layer5 import Layer5DirectRequest, Layer5Response
from app.core.layer5.pipeline import Layer5Pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/layer5", tags=["Layer 5: Evidence Intelligence & Conflict Resolution"])

_settings = Settings()
_pipeline: Layer5Pipeline = None


def get_pipeline() -> Layer5Pipeline:
    global _pipeline
    if _pipeline is None:
        use_mock = (
            _settings.ENVIRONMENT == "test"
            or os.environ.get("TESTING", "").lower() in ("1", "true", "yes")
            or _settings.LLM_PROVIDER == "offline"
        )
        _pipeline = Layer5Pipeline(use_mock=use_mock)
    return _pipeline


def set_pipeline(pipeline: Layer5Pipeline):
    global _pipeline
    _pipeline = pipeline


@router.post(
    "/process",
    response_model=Layer5Response,
    status_code=status.HTTP_200_OK,
    summary="Execute Evidence Intelligence & Conflict Resolution",
    description=(
        "Consumes a Layer 4 RetrievedCandidateSet and Layer 2 KnowledgeRetrievalPlan, "
        "executes cross-encoder reranking, atomic claim extraction, NLI grounding, "
        "4-tier deduplication, contradiction detection (Conflict Graph with Zero Winner Forcing), "
        "and S2G-RAG coverage analysis, returning a standardized VerifiedEvidenceSet for Layer 6."
    )
)
async def process_evidence(request: Layer5DirectRequest) -> Layer5Response:
    try:
        pipeline = get_pipeline()
        evidence_set = pipeline.execute(
            candidate_set=request.candidate_set,
            plan=request.plan,
            max_evidence=request.max_evidence_count,
            rerank_threshold=request.rerank_threshold
        )
        return Layer5Response(
            status="SUCCESS",
            evidence_set=evidence_set,
            warnings=[]
        )
    except Exception as e:
        logger.error(f"Layer 5 processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Layer 5 processing failed: {str(e)}"
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Layer 5 Health Check"
)
async def layer5_health():
    try:
        pipeline = get_pipeline()
        return {
            "status": "HEALTHY",
            "layer": "Layer 5: Evidence Intelligence & Conflict Resolution",
            "reranker_mock_mode": pipeline.reranker.use_mock,
            "sub_modules": [
                "5.1 Cross-Encoder Re-Ranking",
                "5.2 Atomic Claim Extraction",
                "5.3 Factual Grounding & Entailment Verification",
                "5.4 Evidence Deduplication & Consolidation",
                "5.5 Contradiction Detection & Conflict Graph",
                "5.6 Evidence Coverage, Sufficiency & Set Selection",
                "5.7 Pipeline Orchestrator"
            ]
        }
    except Exception as e:
        logger.error(f"Layer 5 health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Layer 5 health check failed: {str(e)}"
        )
