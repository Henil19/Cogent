"""
Layer 4: Hybrid Knowledge Retrieval Layer
Dense FAISS + Sparse BM25 + Reciprocal Rank Fusion (RRF)
"""
from app.core.layer4.pipeline import Layer4Pipeline

__all__ = ["Layer4Pipeline"]
