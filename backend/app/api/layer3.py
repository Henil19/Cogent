"""
Layer 3 FastAPI Router: Knowledge Acquisition & Pre-Retrieval Grounding
Endpoints for document upload, multi-modal ingestion, and plan-driven knowledge acquisition.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.schemas.layer3 import (
    DocumentUploadResponse,
    Layer3AcquisitionRequest,
    Layer3Response,
    AcquisitionStatus,
)
from app.core.layer3.pipeline import Layer3Pipeline

router = APIRouter(prefix="/layer3", tags=["Layer 3 - Knowledge Acquisition & Grounding"])
layer3_pipeline = Layer3Pipeline()


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    summary="Upload and ground a document (PDF, TXT, MD)",
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Ingest, structurally extract, clean, semantically chunk, and attach TROVE provenance
    to an uploaded user document.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    try:
        file_bytes = await file.read()
        response = layer3_pipeline.process_uploaded_document(
            filename=file.filename,
            file_bytes=file_bytes,
            db=db,
        )
        if response.status == AcquisitionStatus.FAILED_EXTRACTION:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=response.message,
            )
        return response
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload processing failed: {str(e)}",
        )


@router.post(
    "/acquire",
    response_model=Layer3Response,
    summary="Execute acquisition batch from Layer 2 plan",
)
async def acquire_knowledge_batch(
    request: Layer3AcquisitionRequest,
    db: Session = Depends(get_db),
):
    """
    Executes knowledge acquisition and pre-retrieval grounding for a Layer 2 KnowledgeRetrievalPlan.
    Acquires local and live web knowledge, generates structural chunks with provenance,
    and returns an AcquiredCorpusBatch for Layer 4.
    """
    try:
        batch = layer3_pipeline.execute_plan(request.plan, db=db)
        return Layer3Response(status="SUCCESS", batch=batch)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge acquisition batch failed: {str(e)}",
        )


@router.get(
    "/documents",
    summary="List all acquired and grounded documents",
)
async def list_documents(db: Session = Depends(get_db)):
    """List all documents currently ingested and registered in the database."""
    try:
        docs = db.query(Document).order_by(Document.upload_date.desc()).all()
        return {
            "total_documents": len(docs),
            "documents": [
                {
                    "document_id": d.id,
                    "filename": d.filename,
                    "file_type": d.file_type,
                    "file_size": d.file_size,
                    "status": d.status,
                    "chunk_count": d.chunk_count,
                    "total_characters": d.total_characters,
                    "upload_date": d.upload_date.isoformat() if d.upload_date else None,
                }
                for d in docs
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query documents: {str(e)}",
        )


@router.get(
    "/health",
    summary="Layer 3 diagnostic health check",
)
async def layer3_health():
    """Returns Layer 3 system status and supported modalities."""
    return {
        "status": "healthy",
        "layer": "Layer 3 - Knowledge Acquisition & Pre-Retrieval Grounding",
        "supported_extensions": [".pdf", ".txt", ".md"],
        "supported_sources": ["LOCAL_PDF", "LOCAL_TXT", "LOCAL_MD", "LIVE_WEB"],
        "provenance_standard": "TROVE ACL 2025",
        "chunking_method": "PIC + Max-Min Semantic Chunking + Late Chunking Headers",
    }
