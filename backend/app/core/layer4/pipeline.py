"""
Sub-Module 4.7: Layer 4 Pipeline Orchestrator
Connects Layer 2 KnowledgeRetrievalPlan and Layer 3 AcquiredCorpusBatch.
Executes Dense FAISS + Sparse BM25 + Reciprocal Rank Fusion retrieval.
Emits standardized RetrievedCandidateSet strictly to Layer 5.
"""

import time
import logging
from typing import Dict, List, Optional

from app.core.layer4.embedding.embedding_engine import EmbeddingEngine
from app.core.layer4.indexing.vector_index_manager import VectorIndexManager
from app.core.layer4.sparse.bm25_retriever import BM25Retriever
from app.core.layer4.fusion.rank_fusion import RankFusionEngine, FusedCandidate
from app.core.layer4.strategy.strategy_manager import StrategyManager
from app.core.layer4.candidate.candidate_builder import CandidateBuilder
from app.core.layer4.telemetry.feature_logger import RetrievalTelemetryLogger

from app.schemas.layer2 import KnowledgeRetrievalPlan, SubQueryPlan, SourceTarget
from app.schemas.layer3 import AcquiredCorpusBatch, AcquiredDocumentChunk
from app.schemas.layer4 import (
    IndexStatistics,
    RetrievedCandidate,
    RetrievedCandidateSet,
    SubQueryCandidateResult,
    RetrievalMethod,
)

logger = logging.getLogger(__name__)


class Layer4Pipeline:
    """
    Orchestrates hybrid knowledge retrieval across indexed corpus batches.
    """

    def __init__(
        self,
        embedding_engine: Optional[EmbeddingEngine] = None,
        index_manager: Optional[VectorIndexManager] = None,
        bm25_retriever: Optional[BM25Retriever] = None,
        fusion_engine: Optional[RankFusionEngine] = None,
        use_mock_embeddings: bool = False
    ):
        self.embedding_engine = embedding_engine or EmbeddingEngine(use_mock=use_mock_embeddings)
        self.index_manager = index_manager or VectorIndexManager()
        self.bm25_retriever = bm25_retriever or BM25Retriever()
        self.fusion_engine = fusion_engine or RankFusionEngine()
        self._indexed_batch_id: Optional[str] = None

    def index_corpus(self, corpus_batch: AcquiredCorpusBatch):
        """
        Embed and index document chunks into both FAISS vector index and BM25 inverted index.
        """
        if not corpus_batch.chunks:
            logger.warning(f"Corpus batch {corpus_batch.batch_id} contains 0 chunks to index.")
            return

        logger.info(f"Indexing {len(corpus_batch.chunks)} chunks from batch {corpus_batch.batch_id}...")

        # Clear previous query vectors to prevent cross-inquiry corpus contamination
        self.index_manager.clear()

        # 1. Dense Embedding & FAISS Indexing
        chunk_texts = [f"{c.title}\n{c.content}" for c in corpus_batch.chunks]
        embeddings = self.embedding_engine.embed_texts(chunk_texts)
        self.index_manager.add_chunks(corpus_batch.chunks, embeddings)

        # 2. Sparse BM25 Inverted Indexing
        self.bm25_retriever.index_chunks(corpus_batch.chunks)

        self._indexed_batch_id = corpus_batch.batch_id
        logger.info(
            f"Successfully indexed batch {corpus_batch.batch_id}. "
            f"Vectors: {self.index_manager.total_vectors}, BM25 docs: {self.bm25_retriever.total_documents}"
        )

    def execute(
        self,
        plan: KnowledgeRetrievalPlan,
        corpus_batch: AcquiredCorpusBatch,
        top_k: int = 5,
        use_hybrid: bool = True,
        sparse_only: bool = False,
    ) -> RetrievedCandidateSet:
        """
        Execute retrieval for all sub-queries in the plan.
        """
        start_time = time.time()

        # Index corpus if not already indexed
        if self._indexed_batch_id != corpus_batch.batch_id or self.index_manager.total_vectors == 0:
            self.index_corpus(corpus_batch)

        # Count partition documents
        local_count = len(self.index_manager._partitions.get("LOCAL_DOCS", []))
        web_count = len(self.index_manager._partitions.get("LIVE_WEB", []))

        sub_query_results: List[SubQueryCandidateResult] = []
        candidate_multiplier = 2 if use_hybrid and not sparse_only else 1

        # Execute retrieval for each sub-query
        for sq in plan.sub_queries:
            sq_start = time.time()

            # 1. Strategy & Partition Resolution
            partition, warning = StrategyManager.resolve_partition(
                sq.target_source,
                local_count=local_count,
                web_count=web_count
            )

            # 2. Dense FAISS Retrieval
            # Combine raw sub-query and dense phrasings
            dense_search_texts = [sq.raw_sub_query]
            if sq.dense_phrasings:
                dense_search_texts.extend(sq.dense_phrasings[:2])

            query_vecs = self.embedding_engine.embed_texts(dense_search_texts)
            # Average vector if multiple phrasings
            mean_query_vec = query_vecs.mean(axis=0, keepdims=True)

            dense_matches = self.index_manager.search(
                mean_query_vec,
                top_k=top_k * candidate_multiplier,
                partition=partition
            )

            # 3. Sparse BM25 Retrieval
            # Combine sparse keywords with terms from raw query
            sparse_terms = list(sq.sparse_keywords) if sq.sparse_keywords else []
            sparse_terms.append(sq.raw_sub_query)

            sparse_matches = self.bm25_retriever.search(
                sparse_terms,
                top_k=top_k * candidate_multiplier
            )

            # 4. Rank Fusion or Dense Selection or Sparse Selection
            if use_hybrid and not sparse_only:
                fused_candidates = self.fusion_engine.fuse(
                    dense_results=dense_matches,
                    sparse_results=sparse_matches,
                    top_k=top_k
                )
            elif sparse_only:
                fused_candidates = [
                    FusedCandidate(
                        chunk=chunk,
                        rrf_score=None,
                        final_rank=rank,
                        dense_rank=None,
                        sparse_rank=rank,
                        similarity_score=score,
                        sparse_score=score,
                        retrieval_method=RetrievalMethod.SPARSE_BM25
                    )
                    for chunk, score, rank in sparse_matches[:top_k]
                ]
            else:
                fused_candidates = [
                    FusedCandidate(
                        chunk=chunk,
                        rrf_score=None,
                        final_rank=rank,
                        dense_rank=rank,
                        sparse_rank=None,
                        similarity_score=score,
                        sparse_score=None,
                        retrieval_method=RetrievalMethod.DENSE_FAISS
                    )
                    for chunk, score, rank in dense_matches[:top_k]
                ]

            sq_latency_ms = (time.time() - sq_start) * 1000.0

            # 5. Build RetrievedCandidate objects with full TROVE provenance
            candidates: List[RetrievedCandidate] = []
            for fc in fused_candidates:
                cand = CandidateBuilder.build_candidate(
                    fused=fc,
                    sub_query_id=sq.id,
                    retrieval_latency_ms=sq_latency_ms
                )
                candidates.append(cand)

            sq_res = CandidateBuilder.build_sub_query_result(
                sub_query_id=sq.id,
                raw_sub_query=sq.raw_sub_query,
                target_source=sq.target_source,
                candidates=candidates,
                dense_count=len(dense_matches),
                sparse_count=len(sparse_matches),
                latency_ms=sq_latency_ms
            )
            sub_query_results.append(sq_res)

        total_latency_ms = (time.time() - start_time) * 1000.0

        index_stats = IndexStatistics(
            total_vectors_indexed=self.index_manager.total_vectors,
            vector_dimensions=self.embedding_engine.dimension,
            index_type="IndexFlatIP" if self.index_manager._faiss_available else "NumPyExactIP",
            sparse_documents_indexed=self.bm25_retriever.total_documents,
            partition_name=f"local:{local_count}_web:{web_count}"
        )

        candidate_set = CandidateBuilder.build_candidate_set(
            plan_id=plan.plan_id,
            session_id=plan.session_id,
            top_k_requested=top_k,
            sub_query_results=sub_query_results,
            index_stats=index_stats,
            total_latency_ms=total_latency_ms
        )

        logger.info(
            f"Layer 4 completed retrieval for plan {plan.plan_id}: "
            f"{candidate_set.total_candidates_returned} candidates across {len(plan.sub_queries)} sub-queries "
            f"in {candidate_set.retrieval_latency_ms:.1f}ms."
        )

        return candidate_set
