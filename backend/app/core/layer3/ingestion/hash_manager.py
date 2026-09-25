"""
Sub-Module 3.1: Cryptographic Hash Manager
Research Basis: Provenance & Source Attribution (ACL 2025 / EMNLP 2024)
Provides deterministic SHA-256 content hashing for:
1. Raw document files (tamper-evident document versioning and duplicate detection)
2. Processed chunk text (reproducible passage lineage tracking)
"""

import hashlib
import re


class HashManager:
    """Computes deterministic SHA-256 hashes for documents and chunks."""

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        """Compute SHA-256 hash of raw document bytes."""
        sha = hashlib.sha256()
        sha.update(data)
        return sha.hexdigest()

    @staticmethod
    def hash_text(text: str) -> str:
        """
        Compute SHA-256 hash of text after canonical whitespace normalization.
        Ensures consistent chunk fingerprinting regardless of platform line endings.
        """
        normalized = re.sub(r"\s+", " ", text).strip()
        sha = hashlib.sha256()
        sha.update(normalized.encode("utf-8"))
        return sha.hexdigest()
