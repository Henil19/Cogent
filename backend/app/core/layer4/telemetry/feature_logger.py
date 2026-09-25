"""
Sub-Module 4.6: Telemetry & Retrieval Feature Logger
Research basis: BERGEN (EMNLP 2024) & RAG Evaluation Survey (Yu et al. 2024)

Extracts and logs fine-grained retrieval signals for downstream calibration in Layer 7
and computes formal academic retrieval metrics (Recall@K, Hit@K, MRR@K, NDCG@K).
"""

import math
import logging
from typing import Dict, List, Optional, Set, Any
from app.schemas.layer4 import RetrievedCandidate, RetrievedCandidateSet

logger = logging.getLogger(__name__)


class RetrievalTelemetryLogger:
    """
    Computes retrieval evaluation metrics and logs calibration signals for Layer 7.
    """

    @staticmethod
    def extract_calibration_features(candidate_set: RetrievedCandidateSet) -> Dict[str, Any]:
        """
        Extract statistical and distributional features of retrieved candidates.
        Consumed by Layer 7 to evaluate retrieval confidence and epistemic certainty.
        """
        if not candidate_set.all_candidates:
            return {
                "candidate_count": 0,
                "mean_dense_similarity": 0.0,
                "max_dense_similarity": 0.0,
                "min_dense_similarity": 0.0,
                "similarity_spread": 0.0,
                "dense_sparse_agreement_ratio": 0.0,
                "total_latency_ms": candidate_set.retrieval_latency_ms
            }

        sim_scores = [c.similarity_score for c in candidate_set.all_candidates]
        mean_sim = sum(sim_scores) / len(sim_scores)
        max_sim = max(sim_scores)
        min_sim = min(sim_scores)
        spread = max_sim - min_sim

        # Dense-sparse agreement: ratio of candidates retrieved by both dense and sparse (HYBRID_RRF)
        hybrid_count = sum(1 for c in candidate_set.all_candidates if c.dense_rank is not None and c.sparse_rank is not None)
        agreement_ratio = hybrid_count / len(candidate_set.all_candidates)

        return {
            "candidate_count": len(candidate_set.all_candidates),
            "mean_dense_similarity": round(mean_sim, 4),
            "max_dense_similarity": round(max_sim, 4),
            "min_dense_similarity": round(min_sim, 4),
            "similarity_spread": round(spread, 4),
            "dense_sparse_agreement_ratio": round(agreement_ratio, 4),
            "total_latency_ms": candidate_set.retrieval_latency_ms
        }

    @staticmethod
    def compute_metrics_at_k(
        retrieved_ids: List[str],
        ground_truth_ids: Set[str],
        k: int = 5
    ) -> Dict[str, float]:
        """
        Compute standard IR evaluation metrics for Top-K candidates.
        
        Args:
            retrieved_ids: Ordered list of retrieved chunk_ids or doc_ids
            ground_truth_ids: Set of known relevant IDs
            k: Top-K cutoff
            
        Returns:
            Dict containing recall, precision, mrr, hit, ndcg at K.
        """
        top_k = retrieved_ids[:k]
        if not top_k or not ground_truth_ids:
            return {
                f"Recall@{k}": 0.0,
                f"Precision@{k}": 0.0,
                f"MRR@{k}": 0.0,
                f"Hit@{k}": 0.0,
                f"NDCG@{k}": 0.0
            }

        relevant_in_top_k = [doc_id for doc_id in top_k if doc_id in ground_truth_ids]
        hits = len(relevant_in_top_k)

        # Recall@K
        recall = hits / len(ground_truth_ids)

        # Precision@K
        precision = hits / k

        # Hit@K
        hit = 1.0 if hits > 0 else 0.0

        # MRR@K (Mean Reciprocal Rank)
        mrr = 0.0
        for rank, doc_id in enumerate(top_k, start=1):
            if doc_id in ground_truth_ids:
                mrr = 1.0 / rank
                break

        # NDCG@K
        dcg = 0.0
        for rank, doc_id in enumerate(top_k, start=1):
            if doc_id in ground_truth_ids:
                dcg += 1.0 / math.log2(rank + 1)

        idcg = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(ground_truth_ids), k) + 1))
        ndcg = dcg / idcg if idcg > 0 else 0.0

        return {
            f"Recall@{k}": round(recall, 4),
            f"Precision@{k}": round(precision, 4),
            f"MRR@{k}": round(mrr, 4),
            f"Hit@{k}": round(hit, 4),
            f"NDCG@{k}": round(ndcg, 4)
        }
