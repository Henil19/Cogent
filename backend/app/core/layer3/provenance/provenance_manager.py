"""
Sub-Module 3.5: Provenance & Lineage Manager
Research Basis:
- TROVE (ACL 2025): Fine-grained source coordinate breadcrumbs (page, section, paragraph)
- Provenance (EMNLP 2024): Immutable chunk identifier attribution
- Source Attribution & CiteBench (ACL 2025/2026): Cryptographic hashes and temporal lineage
Attaches verifiable, traceable provenance to every generated chunk.
"""

import uuid
from typing import List, Optional
from datetime import datetime, timezone

from app.schemas.layer3 import AcquiredDocumentChunk, SourceType
from app.core.layer3.processing.chunker import RawChunk
from app.core.layer3.ingestion.hash_manager import HashManager
from app.core.layer3.validation.quality_checker import QualityChecker


class ProvenanceManager:
    """Attaches cryptographic, temporal, and structural provenance to raw chunks."""

    @classmethod
    def attach_provenance(
        cls,
        raw_chunk: RawChunk,
        document_id: str,
        document_hash: str,
        title: str,
        source_type: SourceType,
        source_uri: str,
        author: Optional[str] = None,
        publication_date: Optional[str] = None,
        retrieved_at: Optional[str] = None,
    ) -> AcquiredDocumentChunk:
        """
        Assemble complete AcquiredDocumentChunk with immutable lineage breadcrumbs.
        """
        chunk_uuid = f"chk_{uuid.uuid4().hex[:10]}"
        content_hash = HashManager.hash_text(raw_chunk.content)
        timestamp = retrieved_at or datetime.now(timezone.utc).isoformat()

        # Compute technical extraction quality
        quality_score = QualityChecker.compute_quality_score(raw_chunk.content)
        warnings: List[str] = []

        if quality_score < 0.75:
            warnings.append(f"Low extraction quality diagnostic ({quality_score:.2f}).")
        if raw_chunk.char_count < 60:
            warnings.append(f"Short chunk length ({raw_chunk.char_count} chars).")

        return AcquiredDocumentChunk(
            chunk_id=chunk_uuid,
            document_id=document_id,
            source_type=source_type,
            title=title,
            source_uri=source_uri,
            content=raw_chunk.content,
            raw_content=raw_chunk.raw_content,
            page_number=raw_chunk.page_number,
            section_title=raw_chunk.section_title,
            paragraph_start=raw_chunk.paragraph_start,
            paragraph_end=raw_chunk.paragraph_end,
            has_table=raw_chunk.has_table,
            has_equation=raw_chunk.has_equation,
            author=author,
            publication_date=publication_date,
            retrieved_at=timestamp,
            document_hash=document_hash,
            content_hash=content_hash,
            chunk_index=raw_chunk.chunk_index,
            char_count=raw_chunk.char_count,
            token_count_estimate=raw_chunk.token_count_estimate,
            extraction_quality=quality_score,
            processing_warnings=warnings,
        )
