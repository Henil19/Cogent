"""
Sub-Module 5.1: Cross-Encoder Evidence Re-Ranking
Research basis:
- Malviya & Katsigiannis (EMNLP 2024): Multi-stage reranking for fact verification
- Alt et al. (EACL 2026): User-Centric Evidence Ranking
- NEST (ACL 2026): Precision survival selection after recall amplification

Performs deep query-passage joint cross-attention scoring on Layer 4 candidates:
    Score_rerank(q, c) = sigma(CrossEncoder(q, c)) in [0.0, 1.0]
Supports sentence_transformers.CrossEncoder in live mode and deterministic
joint-interaction mock scoring for fast, hermetic testing.
"""

import os
import math
import logging
from typing import List, Optional, Tuple

from app.schemas.layer4 import RetrievedCandidate

logger = logging.getLogger(__name__)

DEFAULT_CROSS_ENCODER = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReranker:
    """
    Reranks candidate passages using joint query-passage cross-attention.
    """

    def __init__(self, model_name: str = DEFAULT_CROSS_ENCODER, use_mock: Optional[bool] = None):
        self.model_name = model_name
        if use_mock is None:
            self.use_mock = (
                os.environ.get("COGENT_USE_MOCK_EMBEDDINGS", "").lower() in ("1", "true", "yes")
                or os.environ.get("TESTING", "").lower() in ("1", "true", "yes")
            )
        else:
            self.use_mock = use_mock

        self._model = None
        if not self.use_mock:
            self._init_model()

    def _init_model(self):
        """Lazy load sentence_transformers CrossEncoder."""
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.model_name)
            logger.info(f"Loaded CrossEncoder model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Failed to load CrossEncoder ({e}). Falling back to deterministic mock reranker.")
            self.use_mock = True

    def rerank(
        self,
        query: str,
        candidates: List[RetrievedCandidate],
        top_k: Optional[int] = None,
        sub_queries: Optional[dict] = None
    ) -> List[Tuple[RetrievedCandidate, float, int]]:
        """
        Score and rank candidates using joint query-passage cross-attention.
        If sub_queries is provided and candidate has sub_query_id, evaluates joint relevance
        with respect to both the granular sub-query intent and global parent query (Alt et al. EACL 2026).
        
        Returns:
            List of (RetrievedCandidate, rerank_score, rank) sorted descending by rerank_score.
        """
        if not candidates:
            return []

        # Evaluate candidate scores
        if sub_queries:
            scores = self._score_with_subqueries(query, candidates, sub_queries)
        elif self.use_mock or self._model is None:
            scores = self._score_mock(query, candidates)
        else:
            scores = self._score_model(query, candidates)

        # Pair with candidates and sort descending
        scored_pairs = list(zip(candidates, scores))
        scored_pairs.sort(key=lambda x: x[1], reverse=True)

        k = top_k or len(scored_pairs)
        results: List[Tuple[RetrievedCandidate, float, int]] = []
        for rank, (cand, score) in enumerate(scored_pairs[:k], start=1):
            results.append((cand, round(float(score), 4), rank))

        return results

    def _score_with_subqueries(
        self,
        parent_query: str,
        candidates: List[RetrievedCandidate],
        sub_queries: dict
    ) -> List[float]:
        """
        Sub-query aware scoring: blends granular sub-intent score (70%) with parent query score (30%).
        """
        final_scores = []
        for cand in candidates:
            sq_id = cand.sub_query_id
            target_query = sub_queries.get(sq_id) if sq_id else None

            if self.use_mock or self._model is None:
                parent_s = self._score_mock(parent_query, [cand])[0]
                if target_query and target_query != parent_query:
                    sub_s = self._score_mock(target_query, [cand])[0]
                    blended = 0.70 * sub_s + 0.30 * parent_s
                else:
                    blended = parent_s
            else:
                parent_s = self._score_model(parent_query, [cand])[0]
                if target_query and target_query != parent_query:
                    sub_s = self._score_model(target_query, [cand])[0]
                    blended = 0.70 * sub_s + 0.30 * parent_s
                else:
                    blended = parent_s
            final_scores.append(blended)
        return final_scores

    def _score_model(self, query: str, candidates: List[RetrievedCandidate]) -> List[float]:
        """Score pairs using live CrossEncoder model."""
        try:
            pairs = [[query, f"{c.title}\n{c.content}"] for c in candidates]
            raw_scores = self._model.predict(pairs)
            # Sigmoid normalization if scores are unnormalized logits
            normalized_scores = []
            for s in raw_scores:
                val = float(s)
                # Apply sigmoid: 1 / (1 + e^-val)
                sig = 1.0 / (1.0 + math.exp(-val)) if -15.0 < val < 15.0 else (1.0 if val >= 15.0 else 0.0)
                normalized_scores.append(sig)
            return normalized_scores
        except Exception as e:
            logger.error(f"Cross-encoder predict failed: {e}. Falling back to mock scoring.")
            return self._score_mock(query, candidates)

    def _score_mock(self, query: str, candidates: List[RetrievedCandidate]) -> List[float]:
        """
        Deterministic mock cross-attention scoring based on query-passage term interactions,
        exact technical matches, title relevance, and prior retrieval similarity.
        """
        q_tokens = set(query.lower().split())
        scores = []

        for cand in candidates:
            c_text = f"{cand.title} {cand.content}".lower()
            c_tokens = set(c_text.split())

            if not q_tokens:
                overlap_ratio = 0.5
            else:
                overlap = len(q_tokens.intersection(c_tokens))
                overlap_ratio = overlap / len(q_tokens)

            # Blend term interaction (60%) with Layer 4 mathematical similarity (40%)
            sim_normalized = (cand.similarity_score + 1.0) / 2.0  # map [-1, 1] to [0, 1]
            blended = 0.60 * overlap_ratio + 0.40 * sim_normalized

            # Boost if title contains query keywords
            title_tokens = set(cand.title.lower().split())
            if q_tokens.intersection(title_tokens):
                blended = min(1.0, blended + 0.10)

            # Bound strictly to [0.05, 0.99]
            final_score = max(0.05, min(0.99, blended))
            scores.append(final_score)

        return scores
