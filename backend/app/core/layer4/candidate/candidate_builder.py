"""
Sub-Module 4.5: Candidate Set Builder
Research basis: RAG (Lewis et al. NeurIPS 2020), TROVE (ACL 2025), ANCE (ICLR 2021)

Transforms ranked fused candidates into standardized RetrievedCandidate and
RetrievedCandidateSet models while strictly preserving 100% of Layer 3 TROVE
provenance breadcrumbs (page numbers, section titles, cryptographic hashes).

CRITICAL INVARIANT: Zero evidence pruning. Layer 4 does NOT evaluate truth or credibility;
all candidate filtering, contradiction resolution, and cross-encoder reranking belong strictly
downstream in Layer 5 (Evidence Intelligence) and Layer 7 (Confidence Calibration).
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.core.layer4.fusion.rank_fusion import FusedCandidate
from app.schemas.layer2 import SourceTarget
from app.schemas.layer3 import AcquiredDocumentChunk
from app.schemas.layer4 import (
    IndexStatistics,
    RetrievedCandidate,
    RetrievedCandidateSet,
    SubQueryCandidateResult,
    RetrievalMethod,
)


class CandidateBuilder:
    """
    Constructs standardized Layer 4 contracts with unbroken TROVE provenance.
    """

    @staticmethod
    def build_candidate(
        fused: FusedCandidate,
        sub_query_id: str,
        retrieval_latency_ms: float = 0.0
    ) -> RetrievedCandidate:
        """
        Build a single RetrievedCandidate from a FusedCandidate and its underlying chunk.
        """
        chunk: AcquiredDocumentChunk = fused.chunk
        candidate_id = f"cand_{chunk.chunk_id}_{sub_query_id}"

        return RetrievedCandidate(
            candidate_id=candidate_id,
            sub_query_id=sub_query_id,
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            content=chunk.content,
            title=chunk.title,
            source_uri=chunk.source_uri,
            source_type=chunk.source_type,
            similarity_score=round(fused.similarity_score, 4),
            sparse_score=round(fused.sparse_score, 4) if fused.sparse_score is not None else None,
            rrf_score=round(fused.rrf_score, 6) if fused.rrf_score is not None else None,
            dense_rank=fused.dense_rank,
            sparse_rank=fused.sparse_rank,
            final_rank=fused.final_rank,
            retrieval_method=fused.retrieval_method,
            retrieval_time_ms=round(retrieval_latency_ms, 2),
            page_number=chunk.page_number,
            section_title=chunk.section_title,
            paragraph_start=chunk.paragraph_start,
            paragraph_end=chunk.paragraph_end,
            has_table=chunk.has_table,
            has_equation=chunk.has_equation,
            document_hash=chunk.document_hash,
            content_hash=chunk.content_hash,
            retrieved_at=chunk.retrieved_at,
            author=chunk.author,
            publication_date=chunk.publication_date
        )

    @staticmethod
    def build_sub_query_result(
        sub_query_id: str,
        raw_sub_query: str,
        target_source: SourceTarget,
        candidates: List[RetrievedCandidate],
        dense_count: int,
        sparse_count: int,
        latency_ms: float
    ) -> SubQueryCandidateResult:
        """Build SubQueryCandidateResult for a single sub-query."""
        return SubQueryCandidateResult(
            sub_query_id=sub_query_id,
            raw_sub_query=raw_sub_query,
            target_source=target_source,
            candidates=candidates,
            dense_count=dense_count,
            sparse_count=sparse_count,
            fused_count=len(candidates),
            sub_query_latency_ms=round(latency_ms, 2)
        )

    @staticmethod
    def build_candidate_set(
        plan_id: str,
        session_id: str,
        top_k_requested: int,
        sub_query_results: List[SubQueryCandidateResult],
        index_stats: IndexStatistics,
        total_latency_ms: float
    ) -> RetrievedCandidateSet:
        """Assemble the complete RetrievedCandidateSet for Layer 5."""
        all_candidates: List[RetrievedCandidate] = []
        for sq_res in sub_query_results:
            all_candidates.extend(sq_res.candidates)

        return RetrievedCandidateSet(
            candidate_set_id=f"cset_{uuid.uuid4().hex[:12]}",
            plan_id=plan_id,
            session_id=session_id,
            top_k_requested=top_k_requested,
            total_candidates_returned=len(all_candidates),
            sub_query_results=sub_query_results,
            all_candidates=all_candidates,
            index_stats=index_stats,
            retrieval_latency_ms=round(total_latency_ms, 2),
            created_at=datetime.now(timezone.utc).isoformat()
        )
