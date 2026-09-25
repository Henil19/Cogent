"""
Sub-Module 4.3b: Reciprocal Rank Fusion (RRF) Engine
Research basis: Cormack, Clarke & Buettcher (SIGIR 2009) & Modern Hybrid RAG Studies (2025)

Implements non-parametric Reciprocal Rank Fusion to merge dense FAISS and sparse BM25
rankings without score calibration or normalization distortion:
    RRF(d) = sum_{m in {dense, sparse}} 1 / (k + rank_m(d))
Standard smoothing constant k = 60.
"""

import re
from typing import Dict, List, Optional, Tuple
from app.schemas.layer3 import AcquiredDocumentChunk
from app.schemas.layer4 import RetrievalMethod

RRF_K_CONSTANT = 60


class FusedCandidate:
    def __init__(
        self,
        chunk: AcquiredDocumentChunk,
        rrf_score: float,
        final_rank: int,
        dense_rank: Optional[int],
        sparse_rank: Optional[int],
        similarity_score: float,
        sparse_score: Optional[float],
        retrieval_method: RetrievalMethod
    ):
        self.chunk = chunk
        self.rrf_score = rrf_score
        self.final_rank = final_rank
        self.dense_rank = dense_rank
        self.sparse_rank = sparse_rank
        self.similarity_score = similarity_score
        self.sparse_score = sparse_score
        self.retrieval_method = retrieval_method


class RankFusionEngine:
    """
    Combines dense similarity rankings and sparse lexical rankings via Reciprocal Rank Fusion.
    """

    def __init__(self, k_constant: int = RRF_K_CONSTANT):
        self.k = k_constant

    def fuse(
        self,
        dense_results: List[Tuple[AcquiredDocumentChunk, float, int]],
        sparse_results: List[Tuple[AcquiredDocumentChunk, float, int]],
        top_k: int = 5
    ) -> List[FusedCandidate]:
        """
        Merge dense and sparse candidates using RRF.
        
        Args:
            dense_results: List of (chunk, cosine_similarity, dense_rank)
            sparse_results: List of (chunk, bm25_score, sparse_rank)
            top_k: Number of final candidates to retain
            
        Returns:
            List of FusedCandidate sorted by rrf_score descending.
        """
        # Map chunk_id to tracking record
        scores: Dict[str, float] = {}
        chunk_map: Dict[str, AcquiredDocumentChunk] = {}
        dense_ranks: Dict[str, int] = {}
        dense_scores: Dict[str, float] = {}
        sparse_ranks: Dict[str, int] = {}
        sparse_scores: Dict[str, float] = {}

        # 1. Accumulate dense ranks
        for chunk, sim_score, rank in dense_results:
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            dense_ranks[cid] = rank
            dense_scores[cid] = sim_score
            scores[cid] = scores.get(cid, 0.0) + (1.0 / (self.k + rank))

        # 2. Accumulate sparse ranks
        for chunk, bm25_val, rank in sparse_results:
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            sparse_ranks[cid] = rank
            sparse_scores[cid] = bm25_val
            scores[cid] = scores.get(cid, 0.0) + (1.0 / (self.k + rank))

        # 3. Sort chunk IDs by fused RRF score descending
        sorted_chunk_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

        # 4. Source Diversity Selection (guarantee representation across multiple distinct documents)
        max_per_doc = 2
        selected_cids: List[str] = []
        doc_counts: Dict[str, int] = {}
        deferred_cids: List[str] = []

        # Pass 1: Select up to max_per_doc per document to ensure cross-source diversity
        for cid in sorted_chunk_ids:
            chunk = chunk_map[cid]
            clean_t = re.sub(r"\[[\d\.\sA-Za-z]+\]", "", chunk.title or "")
            clean_t = re.sub(r"[^\w\s]", "", clean_t.lower()).strip()
            words = [w for w in clean_t.split() if len(w) > 2]
            doc_key = " ".join(words[:6]) if words else (chunk.document_id or "default_doc")
            if doc_counts.get(doc_key, 0) < max_per_doc:
                selected_cids.append(cid)
                doc_counts[doc_key] = doc_counts.get(doc_key, 0) + 1
            else:
                deferred_cids.append(cid)

            if len(selected_cids) >= top_k:
                break

        # Pass 2: If top_k not reached, fill with remaining highest scoring chunks
        if len(selected_cids) < top_k:
            for cid in deferred_cids:
                selected_cids.append(cid)
                if len(selected_cids) >= top_k:
                    break

        results: List[FusedCandidate] = []
        for final_rank, cid in enumerate(selected_cids, start=1):
            chunk = chunk_map[cid]
            rrf_score = scores[cid]
            d_rank = dense_ranks.get(cid)
            s_rank = sparse_ranks.get(cid)
            d_score = dense_scores.get(cid, 0.0)
            s_score = sparse_scores.get(cid)

            # Determine retrieval method tag
            if d_rank is not None and s_rank is not None:
                method = RetrievalMethod.HYBRID_RRF
            elif d_rank is not None:
                method = RetrievalMethod.DENSE_FAISS
            else:
                method = RetrievalMethod.SPARSE_BM25

            results.append(
                FusedCandidate(
                    chunk=chunk,
                    rrf_score=rrf_score,
                    final_rank=final_rank,
                    dense_rank=d_rank,
                    sparse_rank=s_rank,
                    similarity_score=d_score,
                    sparse_score=s_score,
                    retrieval_method=method
                )
            )

        return results
