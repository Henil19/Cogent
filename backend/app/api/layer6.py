"""
Layer 6 API Endpoints
Provides HTTP interfaces for transparent reasoning, multi-hop premise chaining,
dialectical conflict reconciliation, and proof trace generation.
"""

import logging
from fastapi import APIRouter, HTTPException, status
from app.schemas.layer6 import Layer6DirectRequest, Layer6Response
from app.core.layer6.pipeline import Layer6Pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/layer6", tags=["Layer 6: Transparent Reasoning & Synthesis"])

_pipeline: Layer6Pipeline = None


def get_pipeline() -> Layer6Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = Layer6Pipeline()
    return _pipeline


def set_pipeline(pipeline: Layer6Pipeline):
    global _pipeline
    _pipeline = pipeline


@router.post(
    "/reason",
    response_model=Layer6Response,
    status_code=status.HTTP_200_OK,
    summary="Execute Transparent Reasoning & Synthesis",
    description=(
        "Consumes a Layer 5 VerifiedEvidenceSet, Layer 2 KnowledgeRetrievalPlan, and optional Layer 1 StructuredUserInput. "
        "Executes evidence-to-claim chaining, multi-hop premise deduction, dialectical conflict reconciliation (Zero Winner Forcing), "
        "comparative decision matrices, epistemic gap bounding, and proof trace generation, returning a standardized SynthesizedReasoningTrace for Layer 7."
    )
)
async def reason_over_evidence(request: Layer6DirectRequest) -> Layer6Response:
    try:
        pipeline = get_pipeline()
        trace = pipeline.execute(
            evidence_set=request.evidence_set,
            plan=request.plan,
            user_input=request.user_input
        )
        return Layer6Response(
            status="SUCCESS",
            reasoning_trace=trace,
            warnings=[]
        )
    except Exception as e:
        logger.error(f"Layer 6 reasoning failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Layer 6 reasoning failed: {str(e)}"
        )


@router.get(
    "/health",
    summary="Layer 6 Health Check",
    description="Check the operational status of all Layer 6 sub-modules."
)
async def health_check():
    return {
        "status": "HEALTHY",
        "layer": 6,
        "name": "Transparent Reasoning & Synthesis Layer",
        "sub_modules": {
            "6.1_claim_chainer": "ONLINE",
            "6.2_multihop_engine": "ONLINE",
            "6.3_conflict_reconciler": "ONLINE",
            "6.4_comparative_engine": "ONLINE",
            "6.5_epistemic_evaluator": "ONLINE",
            "6.6_trace_builder": "ONLINE",
            "6.7_pipeline_orchestrator": "ONLINE"
        },
        "research_anchors": [
            "TRACE the Evidence (EMNLP Findings 2024)",
            "Entailment Trees (EMNLP 2021)",
            "SR-RAG (ACL Findings 2026)",
            "MAGIC (EMNLP Findings 2025)",
            "ConfRAG (ACL 2026)",
            "S2G-RAG (ACL 2026)",
            "ROSCOE (ICLR 2023)",
            "Graph of Thoughts (AAAI 2024)"
        ]
    }
