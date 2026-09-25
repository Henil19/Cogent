"""
Sub-Module 4.3a: Sparse Lexical Retriever
Research basis: SPLADE (SIGIR 2021) & BM25 Okapi (Robertson et al.)

Builds an inverted index over document chunks and computes Okapi BM25 scores
using Layer 2's sparse_keywords to capture exact acronyms, numbers, and technical terms.
Includes a built-in pure-Python BM25 implementation alongside rank-bm25 support.
"""

import math
import re
import logging
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Set, Tuple

from app.schemas.layer3 import AcquiredDocumentChunk

logger = logging.getLogger(__name__)

STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with", "by",
    "from", "of", "about", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "this", "that", "these", "those"
}


def tokenize(text: str) -> List[str]:
    """Lowercase alphanumeric tokenization with stopword filtering."""
    words = re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", text.lower())
    return [w for w in words if len(w) > 1 and w not in STOPWORDS]


class BM25Retriever:
    """
    BM25 Okapi Inverted Index Retriever (k1=1.5, b=0.75).
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_chunks: List[AcquiredDocumentChunk] = []
        self.tokenized_corpus: List[List[str]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = defaultdict(int)
        self.idf: Dict[str, float] = {}
        self.chunk_id_to_idx: Dict[str, int] = {}
        self._rank_bm25_obj = None

    @property
    def total_documents(self) -> int:
        return len(self.corpus_chunks)

    def index_chunks(self, chunks: List[AcquiredDocumentChunk]):
        """Build the inverted index from acquired chunks."""
        self.corpus_chunks = chunks
        self.tokenized_corpus = []
        self.doc_lengths = []
        self.doc_freqs.clear()
        self.chunk_id_to_idx.clear()

        if not chunks:
            self.avg_doc_len = 0.0
            return

        total_len = 0
        for idx, chunk in enumerate(chunks):
            self.chunk_id_to_idx[chunk.chunk_id] = idx
            tokens = tokenize(f"{chunk.title} {chunk.content}")
            self.tokenized_corpus.append(tokens)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_len += doc_len

            # Update document frequencies
            for word in set(tokens):
                self.doc_freqs[word] += 1

        self.avg_doc_len = total_len / len(chunks) if chunks else 0.0

        # Compute Robertson-Sparck Jones IDF with smoothing
        N = len(chunks)
        self.idf.clear()
        for word, df in self.doc_freqs.items():
            self.idf[word] = math.log(1.0 + (N - df + 0.5) / (df + 0.5))

        # Try initializing rank_bm25 if installed
        try:
            from rank_bm25 import BM25Okapi
            self._rank_bm25_obj = BM25Okapi(self.tokenized_corpus, k1=self.k1, b=self.b)
        except Exception:
            self._rank_bm25_obj = None

        logger.info(f"Indexed {len(chunks)} chunks into BM25 retriever. Vocabulary: {len(self.idf)} terms.")

    def search(
        self,
        query_terms: List[str],
        top_k: int = 5
    ) -> List[Tuple[AcquiredDocumentChunk, float, int]]:
        """
        Score documents against query terms using BM25.
        
        Returns:
            List of (AcquiredDocumentChunk, bm25_score, sparse_rank)
        """
        if not self.corpus_chunks or not query_terms:
            return []

        # Tokenize query terms
        clean_terms: List[str] = []
        for term in query_terms:
            clean_terms.extend(tokenize(term))

        if not clean_terms:
            return []

        k = min(top_k, len(self.corpus_chunks))

        # Compute BM25 scores with Lucene-smoothed non-negative IDF
        doc_scores = self._score_internal(clean_terms)

        # Sort indices by score descending
        ranked_indices = sorted(
            range(len(doc_scores)),
            key=lambda i: doc_scores[i],
            reverse=True
        )

        results = []
        rank = 1
        for idx in ranked_indices[:k]:
            score = float(doc_scores[idx])
            # Only include candidates with non-zero or valid score
            if score > 0.0:
                results.append((self.corpus_chunks[idx], score, rank))
                rank += 1

        return results

    def _score_internal(self, query_terms: List[str]) -> List[float]:
        """Internal BM25 scoring algorithm."""
        scores = [0.0] * len(self.corpus_chunks)
        for term in query_terms:
            if term not in self.idf:
                continue
            idf_val = self.idf[term]

            for doc_idx, tokens in enumerate(self.tokenized_corpus):
                tf = tokens.count(term)
                if tf == 0:
                    continue
                doc_len = self.doc_lengths[doc_idx]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / (self.avg_doc_len + 1e-6)))
                scores[doc_idx] += idf_val * (numerator / denominator)

        return scores
