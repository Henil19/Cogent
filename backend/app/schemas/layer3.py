"""
Layer 3 Pydantic Schemas
Contracts for Knowledge Acquisition & Pre-Retrieval Grounding Layer.
Research basis:
- PIC (ACL Findings 2025): Pseudo-Instruction guided chunking
- Max-Min Semantic Chunking (Discover Computing 2025): Semantic cohesion breakpoints
- SCAN (ACL/EACL 2025/2026): Coarse-grained semantic layout analysis
- TechDocRAG (AI 2026): Relation-preserving technical document structure (tables, equations)
- IEEE Access (2025): DOM-based main content extraction
- TROVE (ACL 2025): Fine-grained provenance via source sentence & coordinate tracing
- Provenance (EMNLP 2024): Unique chunk-level origin attribution
- Late Chunking (2024/2025): Contextual prefix retention
- Quality Gating (KDD 2024/2025): Pre-retrieval integrity and quality diagnostics
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from app.schemas.layer2 import KnowledgeRetrievalPlan


class SourceType(str, Enum):
    LOCAL_PDF = "LOCAL_PDF"
    LOCAL_TXT = "LOCAL_TXT"
    LOCAL_MD = "LOCAL_MD"
    LIVE_WEB = "LIVE_WEB"


class AcquisitionStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    VALIDATED = "VALIDATED"
    ACQUIRED = "ACQUIRED"
    EXTRACTED = "EXTRACTED"
    NORMALIZED = "NORMALIZED"
    CHUNKED = "CHUNKED"
    PROVENANCE_ATTACHED = "PROVENANCE_ATTACHED"
    READY_FOR_RETRIEVAL = "READY_FOR_RETRIEVAL"
    FAILED_ACQUISITION = "FAILED_ACQUISITION"
    FAILED_EXTRACTION = "FAILED_EXTRACTION"
    REJECTED_QUALITY = "REJECTED_QUALITY"


class DocumentMetadata(BaseModel):
    """Metadata extracted during ingestion & extraction."""
    document_id: str
    title: str
    source_uri: str
    source_type: SourceType
    author: Optional[str] = None
    publication_date: Optional[str] = None
    retrieved_at: str
    document_hash: str
    file_size_bytes: int
    page_count: Optional[int] = None
    section_count: Optional[int] = None
    language: str = "en"
    extraction_quality: float = Field(1.0, ge=0.0, le=1.0)
    processing_warnings: List[str] = Field(default_factory=list)


class AcquiredDocumentChunk(BaseModel):
    """
    Standardized traceable knowledge unit produced by Layer 3.
    Consumed by Layer 4 (Retrieval) and attributed by Layer 8/9.
    """
    chunk_id: str = Field(..., description="Unique chunk UUID, e.g. chk_7d8e9f")
    document_id: str = Field(..., description="Parent document identifier, e.g. doc_a1b2c3")
    source_type: SourceType = Field(..., description="Origin source category")
    title: str = Field(..., description="Document or page title")
    source_uri: str = Field(..., description="File path or URL")
    
    # Coherent proposition text with Late Chunking contextual prefix
    content: str = Field(..., description="Cleaned, readable chunk text with contextual header")
    raw_content: Optional[str] = Field(None, description="Raw text without contextual prefix")

    # Structural Provenance Breadcrumbs (TROVE ACL 2025)
    page_number: Optional[int] = Field(None, description="Page number in original document (1-indexed)")
    section_title: Optional[str] = Field(None, description="Section heading hierarchy, e.g. '3.2 Retrieval'")
    paragraph_start: Optional[int] = Field(None, description="Starting paragraph index")
    paragraph_end: Optional[int] = Field(None, description="Ending paragraph index")
    has_table: bool = Field(False, description="True if chunk preserves a markdown table")
    has_equation: bool = Field(False, description="True if chunk preserves math/equations")

    # Temporal Lineage
    author: Optional[str] = None
    publication_date: Optional[str] = None
    retrieved_at: str = Field(..., description="ISO 8601 acquisition timestamp")

    # Cryptographic Integrity & Versioning
    document_hash: str = Field(..., description="SHA-256 of raw document bytes")
    content_hash: str = Field(..., description="SHA-256 of cleaned chunk text")

    # Statistics & Quality Diagnostics
    chunk_index: int = Field(0, description="Sequential index within document")
    char_count: int
    token_count_estimate: int
    extraction_quality: float = Field(1.0, ge=0.0, le=1.0, description="Syntactic & layout integrity (0.0 to 1.0)")
    processing_warnings: List[str] = Field(default_factory=list)


class AcquiredCorpusBatch(BaseModel):
    """
    Standardized typed contract outputted by Layer 3
    and consumed directly by Layer 4 (Retrieval Layer).
    """
    batch_id: str = Field(..., description="Unique batch UUID")
    plan_id: str = Field(..., description="Inherited from Layer 2 KnowledgeRetrievalPlan")
    session_id: str = Field(..., description="User or conversation session UUID")
    total_documents: int
    total_chunks: int
    chunks: List[AcquiredDocumentChunk] = Field(default_factory=list)
    acquisition_time_ms: float
    status: AcquisitionStatus = AcquisitionStatus.READY_FOR_RETRIEVAL
    documents_metadata: List[DocumentMetadata] = Field(default_factory=list)
    rejected_documents: List[Dict[str, Any]] = Field(default_factory=list)


class DocumentUploadResponse(BaseModel):
    """Response returned when a user uploads a document."""
    document_id: str
    filename: str
    source_type: SourceType
    file_size_bytes: int
    document_hash: str
    status: AcquisitionStatus
    total_chunks: int
    extraction_quality: float
    message: str


class Layer3AcquisitionRequest(BaseModel):
    """Execution request accepting a Layer 2 KnowledgeRetrievalPlan."""
    plan: KnowledgeRetrievalPlan


class Layer3Response(BaseModel):
    status: str = "SUCCESS"
    batch: AcquiredCorpusBatch
