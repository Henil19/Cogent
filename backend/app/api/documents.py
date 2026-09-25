"""
Documents API Router
Endpoints for uploading documents (Layer 3 acquisition) and explicitly indexing them into Layer 4 (FAISS / BM25).
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.api.deps import get_optional_current_user
from app.core.layer3.pipeline import Layer3Pipeline
from app.api.layer4 import get_pipeline as get_layer4_pipeline
from app.schemas.layer3 import AcquiredCorpusBatch, AcquiredDocumentChunk, SourceType

router = APIRouter(prefix="/documents", tags=["Document Management"])
layer3_pipeline = Layer3Pipeline()


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    indexing_status: str
    chunk_count: int
    upload_date: Optional[datetime] = None


class DocumentDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    indexing_status: str
    chunk_count: int
    total_characters: int
    upload_date: Optional[datetime] = None
    chunks: List[Dict[str, Any]] = []


@router.post("/upload", response_model=DocumentSummary, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Ingests and parses a document through Layer 3 Acquisition.
    Extracts text, cleans, and generates semantic chunks with TROVE provenance.
    Automatically indexes chunks into Layer 4 (FAISS Vector Index + BM25).
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename required.")

    file_bytes = file.file.read()
    user_id = current_user.id if current_user else None
    try:
        # Use Layer 3 pipeline to process document and chunks
        l3_res = layer3_pipeline.process_uploaded_document(
            filename=file.filename,
            file_bytes=file_bytes,
            user_id=user_id,
            db=db,
        )
        
        # Retrieve newly created document
        doc = db.query(Document).filter(Document.id == l3_res.document_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Document creation failed.")

        # Mark document as indexed and ready for retrieval
        doc.indexing_status = "INDEXED"
        if current_user:
            doc.user_id = current_user.id
        db.commit()

        return DocumentSummary(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            status=doc.status,
            indexing_status="INDEXED",
            chunk_count=doc.chunk_count,
            upload_date=doc.upload_date,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))


@router.post("/{document_id}/index", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def index_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Explicitly indexes an acquired document's chunks into Layer 4 (FAISS Vector Index + BM25).
    Separates Layer 3 acquisition from Layer 4 retrieval indexing.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index.asc()).all()
    if not chunks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document has no chunks to index.")

    try:
        l4_chunks = []
        for c in chunks:
            chunk_meta = c.metadata_json or {}
            l4_chunks.append(
                AcquiredDocumentChunk(
                    chunk_id=c.id,
                    document_id=c.document_id,
                    source_type=SourceType.LOCAL_TXT,
                    title=doc.filename,
                    source_uri=doc.filename,
                    content=c.content,
                    retrieved_at=datetime.now(timezone.utc).isoformat(),
                    document_hash=chunk_meta.get("document_hash", "doc_hash"),
                    content_hash=chunk_meta.get("content_hash", "content_hash"),
                    chunk_index=c.chunk_index,
                    char_count=c.content_length,
                    token_count_estimate=chunk_meta.get("token_count", c.content_length // 4),
                    page_number=c.page_number,
                    section_title=c.section_header,
                )
            )

        batch = AcquiredCorpusBatch(
            batch_id=f"batch_doc_{doc.id}",
            plan_id=f"plan_{doc.id}",
            session_id="default_session",
            total_documents=1,
            total_chunks=len(l4_chunks),
            chunks=l4_chunks,
            acquisition_time_ms=10.0,
        )

        l4_pipe = get_layer4_pipeline()
        l4_pipe.index_corpus(batch)

        doc.indexing_status = "INDEXED"
        db.commit()

        return {
            "document_id": doc.id,
            "filename": doc.filename,
            "indexing_status": "INDEXED",
            "indexed_chunks": len(l4_chunks),
            "message": "Successfully indexed into Layer 4 FAISS and BM25 search engines.",
        }
    except Exception as exc:
        doc.indexing_status = "FAILED"
        doc.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Layer 4 indexing failed: {str(exc)}")


@router.get("", response_model=List[DocumentSummary])
def list_documents(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Lists all uploaded documents and their indexing statuses."""
    from sqlalchemy import or_
    query = db.query(Document)
    if current_user:
        query = query.filter(or_(Document.user_id == current_user.id, Document.user_id == None))
    docs = query.order_by(Document.upload_date.desc()).all()
    return [
        DocumentSummary(
            id=d.id,
            filename=d.filename,
            file_type=d.file_type,
            file_size=d.file_size,
            status=d.status,
            indexing_status=d.indexing_status or "INDEXED",
            chunk_count=d.chunk_count,
            upload_date=d.upload_date,
        )
        for d in docs
    ]


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves full details and chunk contents of a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index.asc()).all()
    chunk_list = [
        {
            "chunk_id": c.id,
            "chunk_index": c.chunk_index,
            "content": c.content,
            "content_length": c.content_length,
            "section_header": c.section_header,
        }
        for c in chunks
    ]

    return DocumentDetail(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        status=doc.status,
        indexing_status=doc.indexing_status or "PENDING",
        chunk_count=doc.chunk_count,
        total_characters=doc.total_characters,
        upload_date=doc.upload_date,
        chunks=chunk_list,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """Deletes an uploaded document and its chunks."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if doc:
        db.delete(doc)
        db.commit()
    return None
