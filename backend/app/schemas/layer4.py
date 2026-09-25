"""
Layer 4 Pydantic Schemas
Contracts for Hybrid Knowledge Retrieval Layer.
Research basis:
- DPR (EMNLP 2020): Bi-encoder dense representation & cosine similarity retrieval
- RAG (Lewis et al. NeurIPS 2020): Parametric + non-parametric memory candidate interface
- SPLADE (SIGIR 2021) & BM25: Sparse lexical retrieval via exact keywords
- RRF (Cormack et al. 2009 / 2025 Hybrid Studies): Non-parametric Reciprocal Rank Fusion
- ANCE (ICLR 2021): Hard negative & candidate pool generation
- TROVE (ACL 2025): Strict preservation of fine-grained provenance breadcrumbs
- BERGEN (EMNLP 2024): Feature logging & retrieval telemetry for calibration
- RAG Evaluation Survey (Yu et al. 2024): Standardized Recall@K and MRR retrieval metrics
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime, timezone

from app.schemas.layer2 import SourceTarget, KnowledgeRetrievalPlan
from app.schemas.layer3 import SourceType, AcquiredCorpusBatch, AcquiredDocumentChunk


class RetrievalMethod(str, Enum):
    DENSE_FAISS = "DENSE_FAISS"
    SPARSE_BM25 = "SPARSE_BM25"
    HYBRID_RRF = "HYBRID_RRF"


class RetrievedCandidate(BaseModel):
    """
    Individual knowledge candidate retrieved by Layer 4.
    Preserves raw mathematical similarity scores, ranking positions,
    and all unbroken TROVE provenance breadcrumbs from Layer 3.
    
    IMPORTANT: No evidence truth/credibility filtering is performed here;
    that is strictly the domain of Layer 5 (Evidence Intelligence).
    """
    candidate_id: str = Field(..., description="Unique candidate identifier, e.g. cand_chk_123_sq_1")
    sub_query_id: str = Field(..., description="Target sub-query ID from Layer 2 plan")
    chunk_id: str = Field(..., description="Corpus chunk ID from Layer 3")
    document_id: str = Field(..., description="Origin document ID from Layer 3")
    content: str = Field(..., description="Cleaned chunk text content")
    title: str = Field(..., description="Document or section title")
    source_uri: str = Field(..., description="Source URL or file path")
    source_type: SourceType = Field(..., description="Source category (e.g. LOCAL_PDF, LIVE_WEB)")

    # Mathematical Similarity & Ranking Features
    similarity_score: float = Field(..., description="Dense cosine similarity score [-1.0, 1.0]")
    sparse_score: Optional[float] = Field(None, description="BM25 lexical matching score")
    rrf_score: Optional[float] = Field(None, description="Reciprocal Rank Fusion score")
    dense_rank: Optional[int] = Field(None, description="Rank in dense FAISS retrieval (1-indexed)")
    sparse_rank: Optional[int] = Field(None, description="Rank in sparse BM25 retrieval (1-indexed)")
    final_rank: int = Field(..., description="Final rank position in candidate set (1-indexed)")
    retrieval_method: RetrievalMethod = Field(..., description="Method used to retrieve/rank candidate")
    retrieval_time_ms: float = Field(0.0, description="Latency of retrieving this candidate")

    # TROVE Provenance Breadcrumbs (ACL 2025)
    page_number: Optional[int] = Field(None, description="1-indexed page number in source")
    section_title: Optional[str] = Field(None, description="Hierarchical section heading")
    paragraph_start: Optional[int] = Field(None, description="Starting paragraph index")
    paragraph_end: Optional[int] = Field(None, description="Ending paragraph index")
    has_table: bool = Field(False, description="Whether chunk contains structured table")
    has_equation: bool = Field(False, description="Whether chunk contains math/equation")

    # Cryptographic Integrity & Lineage
    document_hash: str = Field(..., description="SHA-256 hash of original document")
    content_hash: str = Field(..., description="SHA-256 hash of chunk content")
    retrieved_at: str = Field(..., description="ISO 8601 acquisition timestamp")
    author: Optional[str] = None
    publication_date: Optional[str] = None


class SubQueryCandidateResult(BaseModel):
    """Retrieved candidate pool for a specific sub-query in the execution plan."""
    sub_query_id: str = Field(..., description="Sub-query ID, e.g. sq_1")
    raw_sub_query: str = Field(..., description="Formulated sub-question")
    target_source: SourceTarget = Field(..., description="Source target from Layer 2")
    candidates: List[RetrievedCandidate] = Field(default_factory=list, description="Top-K candidates")
    dense_count: int = Field(0, description="Number of dense candidates retrieved")
    sparse_count: int = Field(0, description="Number of sparse candidates retrieved")
    fused_count: int = Field(0, description="Number of unique candidates after fusion")
    sub_query_latency_ms: float = Field(0.0, description="Sub-query retrieval latency in ms")


class IndexStatistics(BaseModel):
    """Diagnostics and telemetry for the underlying vector and lexical indexes."""
    total_vectors_indexed: int = Field(0, description="Total vectors in FAISS index")
    vector_dimensions: int = Field(384, description="Embedding vector dimensionality")
    index_type: str = Field("IndexFlatIP", description="FAISS index type (exact inner product)")
    sparse_documents_indexed: int = Field(0, description="Total documents in BM25 inverted index")
    partition_name: Optional[str] = Field(None, description="Index partition or corpus identifier")


class RetrievedCandidateSet(BaseModel):
    """
    Standardized typed contract outputted by Layer 4
    and consumed directly by Layer 5 (Evidence Intelligence).
    """
    candidate_set_id: str = Field(..., description="Unique candidate set UUID")
    plan_id: str = Field(..., description="Associated Layer 2 plan ID")
    session_id: str = Field(..., description="User session UUID")
    top_k_requested: int = Field(..., description="Configured Top-K parameter (e.g. 3, 5, 10)")
    total_candidates_returned: int = Field(..., description="Total unique candidates across all sub-queries")
    sub_query_results: List[SubQueryCandidateResult] = Field(default_factory=list)
    all_candidates: List[RetrievedCandidate] = Field(default_factory=list)
    index_stats: IndexStatistics = Field(default_factory=IndexStatistics)
    retrieval_latency_ms: float = Field(..., description="Total retrieval duration in ms")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Layer4DirectRequest(BaseModel):
    """Direct request payload for invoking Layer 4."""
    plan: KnowledgeRetrievalPlan = Field(..., description="Layer 2 KnowledgeRetrievalPlan")
    corpus_batch: AcquiredCorpusBatch = Field(..., description="Layer 3 AcquiredCorpusBatch")
    top_k: int = Field(5, ge=1, le=50, description="Number of candidates to retrieve per sub-query")
    use_hybrid: bool = Field(True, description="Whether to execute hybrid FAISS+BM25 with RRF fusion")


class Layer4Response(BaseModel):
    """Response envelope for Layer 4 API endpoints."""
    status: str = "SUCCESS"
    candidate_set: RetrievedCandidateSet
    warnings: List[str] = Field(default_factory=list)
