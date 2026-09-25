"""
Layer 4 API Endpoints
Provides HTTP interfaces for hybrid knowledge retrieval, FAISS indexing, and health diagnostics.
"""

import logging
from fastapi import APIRouter, HTTPException, status
from app.schemas.layer4 import Layer4DirectRequest, Layer4Response, IndexStatistics
from app.core.layer4.pipeline import Layer4Pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/layer4", tags=["Layer 4: Hybrid Knowledge Retrieval"])

import os
from app.config import Settings

_settings = Settings()

# Singleton pipeline instance for live API serving
_pipeline: Layer4Pipeline = None


def get_pipeline() -> Layer4Pipeline:
    global _pipeline
    if _pipeline is None:
        use_mock = (
            _settings.ENVIRONMENT == "test"
            or os.environ.get("TESTING", "").lower() in ("1", "true", "yes")
            or _settings.LLM_PROVIDER == "offline"
        )
        _pipeline = Layer4Pipeline(use_mock_embeddings=use_mock)
    return _pipeline


def set_pipeline(pipeline: Layer4Pipeline):
    global _pipeline
    _pipeline = pipeline


@router.post(
    "/retrieve",
    response_model=Layer4Response,
    status_code=status.HTTP_200_OK,
    summary="Execute Hybrid Knowledge Retrieval",
    description=(
        "Consumes a Layer 2 KnowledgeRetrievalPlan and Layer 3 AcquiredCorpusBatch, "
        "indexes chunks in FAISS and BM25, performs topological sub-query retrieval with RRF fusion, "
        "and emits a standardized RetrievedCandidateSet for Layer 5."
    )
)
async def retrieve_candidates(request: Layer4DirectRequest) -> Layer4Response:
    try:
        pipeline = get_pipeline()
        candidate_set = pipeline.execute(
            plan=request.plan,
            corpus_batch=request.corpus_batch,
            top_k=request.top_k,
            use_hybrid=request.use_hybrid
        )
        return Layer4Response(
            status="SUCCESS",
            candidate_set=candidate_set,
            warnings=[]
        )
    except Exception as e:
        logger.error(f"Layer 4 retrieval failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Layer 4 retrieval failed: {str(e)}"
        )


@router.get(
    "/health",
    response_model=IndexStatistics,
    status_code=status.HTTP_200_OK,
    summary="Layer 4 Health & Index Statistics"
)
async def layer4_health() -> IndexStatistics:
    try:
        pipeline = get_pipeline()
        return IndexStatistics(
            total_vectors_indexed=pipeline.index_manager.total_vectors,
            vector_dimensions=pipeline.embedding_engine.dimension,
            index_type="IndexFlatIP" if pipeline.index_manager._faiss_available else "NumPyExactIP",
            sparse_documents_indexed=pipeline.bm25_retriever.total_documents,
            partition_name=f"local:{len(pipeline.index_manager._partitions.get('LOCAL_DOCS', []))}_web:{len(pipeline.index_manager._partitions.get('LIVE_WEB', []))}"
        )
    except Exception as e:
        logger.error(f"Layer 4 health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Layer 4 health check failed: {str(e)}"
        )
