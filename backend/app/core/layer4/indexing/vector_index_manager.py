"""
Sub-Module 4.2: Vector Index Manager
Research basis: DPR (Karpukhin et al. EMNLP 2020) + Master Architecture Blueprint

Manages FAISS IndexFlatIP (exact inner product / cosine similarity) indexes.
Maintains bidirectional coordinate mappings:
    int64 faiss_id <-> str chunk_id <-> AcquiredDocumentChunk
Supports disk persistence (data/faiss/) and multi-source index partitioning.
Includes pure NumPy vector matrix fallback if FAISS library is unavailable.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from app.schemas.layer3 import AcquiredDocumentChunk

logger = logging.getLogger(__name__)

DEFAULT_INDEX_DIR = "data/faiss"
EMBEDDING_DIM = 384


class VectorIndexManager:
    """
    FAISS IndexFlatIP manager with bidirectional chunk mapping and persistence.
    """

    def __init__(self, index_dir: str = DEFAULT_INDEX_DIR, dimension: int = EMBEDDING_DIM):
        self.index_dir = Path(index_dir)
        self.dimension = dimension
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # In-memory mapping stores
        # faiss_id (int) -> chunk_id (str)
        self._id_to_chunk_id: Dict[int, str] = {}
        # chunk_id (str) -> faiss_id (int)
        self._chunk_id_to_id: Dict[str, int] = {}
        # chunk_id (str) -> AcquiredDocumentChunk
        self._chunk_store: Dict[str, AcquiredDocumentChunk] = {}
        # partition_name -> list of faiss_ids
        self._partitions: Dict[str, List[int]] = {
            "LOCAL_DOCS": [],
            "LIVE_WEB": [],
            "ALL": []
        }

        # Vector storage: FAISS Index or NumPy fallback
        self._faiss_index = None
        self._numpy_vectors: Optional[np.ndarray] = None
        self._faiss_available = False
        self._next_id = 0

        self._init_index()

    def _init_index(self):
        """Initialize FAISS IndexFlatIP or NumPy vector matrix."""
        try:
            import faiss
            self._faiss_index = faiss.IndexFlatIP(self.dimension)
            self._faiss_available = True
            logger.info(f"Initialized FAISS IndexFlatIP with dimension {self.dimension}")
        except Exception as e:
            self._faiss_available = False
            self._numpy_vectors = np.empty((0, self.dimension), dtype=np.float32)
            logger.warning(f"FAISS unavailable ({e}). Running in high-performance NumPy fallback mode.")

    @property
    def total_vectors(self) -> int:
        return self._next_id

    def add_chunks(
        self,
        chunks: List[AcquiredDocumentChunk],
        embeddings: np.ndarray,
        partition: str = "ALL"
    ) -> int:
        """
        Add document chunks and their normalized embedding vectors to the index.
        """
        if not chunks or len(chunks) == 0:
            return 0

        if len(chunks) != embeddings.shape[0]:
            raise ValueError(
                f"Mismatch between chunk count ({len(chunks)}) and embedding rows ({embeddings.shape[0]})"
            )

        # Verify float32
        vectors = embeddings.astype(np.float32)

        start_id = self._next_id
        for i, chunk in enumerate(chunks):
            current_id = start_id + i
            self._id_to_chunk_id[current_id] = chunk.chunk_id
            self._chunk_id_to_id[chunk.chunk_id] = current_id
            self._chunk_store[chunk.chunk_id] = chunk

            # Route to partitions
            self._partitions["ALL"].append(current_id)
            if "WEB" in chunk.source_type.value or "URL" in chunk.source_type.value:
                self._partitions["LIVE_WEB"].append(current_id)
            else:
                self._partitions["LOCAL_DOCS"].append(current_id)

        self._next_id += len(chunks)

        if self._faiss_available and self._faiss_index is not None:
            self._faiss_index.add(vectors)
        else:
            if self._numpy_vectors is None or self._numpy_vectors.shape[0] == 0:
                self._numpy_vectors = vectors
            else:
                self._numpy_vectors = np.vstack([self._numpy_vectors, vectors])

        logger.info(f"Added {len(chunks)} chunks to vector index. Total vectors: {self.total_vectors}")
        return len(chunks)

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        partition: str = "ALL",
        min_similarity: float = -1.0
    ) -> List[Tuple[AcquiredDocumentChunk, float, int]]:
        """
        Perform exact inner product (cosine similarity) nearest neighbor search.
        
        Returns:
            List of (AcquiredDocumentChunk, similarity_score, dense_rank)
        """
        if self.total_vectors == 0:
            return []

        q_vec = query_vector.astype(np.float32)
        if len(q_vec.shape) == 1:
            q_vec = q_vec.reshape(1, -1)

        # Normalize query vector if not already normalized
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        target_ids = self._partitions.get(partition, self._partitions["ALL"])
        if not target_ids:
            # Fallback to ALL if specific partition has no elements
            target_ids = self._partitions["ALL"]
            if not target_ids:
                return []

        k = min(top_k, len(target_ids))

        # FAISS search path
        if self._faiss_available and self._faiss_index is not None:
            # If searching across ALL and all elements are included, query FAISS directly
            if partition == "ALL" or len(target_ids) == self.total_vectors:
                scores, indices = self._faiss_index.search(q_vec, k)
                results = []
                for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), start=1):
                    if idx < 0:
                        continue
                    # Filter results strictly below min_similarity
                    if float(score) < min_similarity:
                        continue
                    chunk_id = self._id_to_chunk_id.get(int(idx))
                    if chunk_id and chunk_id in self._chunk_store:
                        chunk = self._chunk_store[chunk_id]
                        results.append((chunk, float(score), rank))
                return results

        # Partition-filtered or NumPy search path
        # Gather vectors for target_ids
        if self._faiss_available and self._faiss_index is not None:
            # Reconstruct vectors from FAISS index
            vectors = np.vstack([self._faiss_index.reconstruct(int(fid)) for fid in target_ids])
        else:
            vectors = self._numpy_vectors[target_ids]

        # Inner product computation
        scores = np.atleast_1d(np.dot(vectors, q_vec.T).squeeze())

        # Top-K sorting
        sorted_order = np.atleast_1d(np.argsort(-scores)[:k])

        results = []
        for rank, order_idx in enumerate(sorted_order, start=1):
            faiss_id = target_ids[order_idx]
            chunk_id = self._id_to_chunk_id.get(faiss_id)
            if chunk_id and chunk_id in self._chunk_store:
                chunk = self._chunk_store[chunk_id]
                score = float(scores[order_idx])
                # Filter results strictly below min_similarity
                if score < min_similarity:
                    continue
                results.append((chunk, score, rank))

        return results

    def save_index(self, index_name: str = "default") -> Tuple[str, str]:
        """Persist index and mapping metadata to disk."""
        index_file = self.index_dir / f"{index_name}.index"
        mapping_file = self.index_dir / f"{index_name}.mapping.json"

        # Save mappings
        meta = {
            "total_vectors": self._next_id,
            "dimension": self.dimension,
            "id_to_chunk_id": {str(k): v for k, v in self._id_to_chunk_id.items()},
            "partitions": self._partitions
        }
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        # Save index binary
        if self._faiss_available and self._faiss_index is not None:
            import faiss
            faiss.write_index(self._faiss_index, str(index_file))
        elif self._numpy_vectors is not None:
            np.save(str(self.index_dir / f"{index_name}.npy"), self._numpy_vectors)

        logger.info(f"Saved index {index_name} to {self.index_dir}")
        return str(index_file), str(mapping_file)

    def clear(self):
        """Reset index and stores."""
        self._id_to_chunk_id.clear()
        self._chunk_id_to_id.clear()
        self._chunk_store.clear()
        self._partitions = {"LOCAL_DOCS": [], "LIVE_WEB": [], "ALL": []}
        self._next_id = 0
        self._init_index()
