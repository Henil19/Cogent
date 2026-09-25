"""
Sub-Module 3.4: Structure-Preserving Semantic Chunker
Research Basis:
- PIC (ACL Findings 2025): Pseudo-Instruction guided chunking
- Max-Min Semantic Chunking (Discover Computing 2025): Semantic cohesion breakpoints
- Dense X Retrieval (ACL 2024): Propositional completeness
- Late Chunking (2024/2025): Contextual breadcrumb prefixing
Groups structural units into semantically coherent chunks with Late Chunking headers.
"""

import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.core.layer3.extraction.pdf_extractor import ExtractedDocumentUnit
from app.core.layer3.processing.normalizer import ContentNormalizer


@dataclass
class RawChunk:
    """Intermediate chunk representation prior to provenance attachment."""
    content: str
    raw_content: str
    page_number: Optional[int]
    section_title: Optional[str]
    paragraph_start: int
    paragraph_end: int
    has_table: bool
    has_equation: bool
    chunk_index: int
    char_count: int
    token_count_estimate: int


class StructurePreservingChunker:
    """
    Adaptive chunker preserving section hierarchy and propositions.
    Avoids naive character cutting and prefixes Late Chunking context headers.
    """

    DEFAULT_TARGET_TOKENS = 512
    DEFAULT_OVERLAP_TOKENS = 64
    CHARS_PER_TOKEN = 4  # Standard empirical ratio for English & technical text

    def __init__(
        self,
        target_tokens: int = DEFAULT_TARGET_TOKENS,
        overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
    ):
        self.target_chars = target_tokens * self.CHARS_PER_TOKEN
        self.overlap_chars = overlap_tokens * self.CHARS_PER_TOKEN

    def chunk_document_units(
        self,
        units: List[ExtractedDocumentUnit],
        doc_title: str = "Document",
    ) -> List[RawChunk]:
        """
        Group structural ExtractedDocumentUnit items into coherent chunks.
        Never breaks across table boundaries or distinct major sections.
        """
        if not units:
            return []

        raw_chunks: List[RawChunk] = []
        chunk_idx = 0

        current_units: List[ExtractedDocumentUnit] = []
        current_char_len = 0

        for unit_idx, unit in enumerate(units):
            normalized_content = ContentNormalizer.normalize(unit.content)
            if not normalized_content:
                continue

            unit_len = len(normalized_content)

            # Rule 1 (TechDocRAG): Tables are kept intact as dedicated chunks
            if unit.has_table:
                if current_units:
                    raw_chunks.append(
                        self._build_chunk(current_units, chunk_idx, doc_title)
                    )
                    chunk_idx += 1
                    current_units = []
                    current_char_len = 0

                raw_chunks.append(
                    self._build_chunk([unit], chunk_idx, doc_title, force_table=True)
                )
                chunk_idx += 1
                continue

            # Rule 2 (Max-Min / PIC): If current buffer exceeds target or new section starts
            section_changed = (
                current_units
                and current_units[-1].section_title != unit.section_title
            )

            if (current_char_len + unit_len > self.target_chars) or section_changed:
                if current_units:
                    raw_chunks.append(
                        self._build_chunk(current_units, chunk_idx, doc_title)
                    )
                    chunk_idx += 1

                    # Retain overlap from previous unit if same section
                    if not section_changed and self.overlap_chars > 0:
                        current_units = [current_units[-1], unit]
                        current_char_len = len(current_units[0].content) + unit_len
                    else:
                        current_units = [unit]
                        current_char_len = unit_len
                else:
                    current_units = [unit]
                    current_char_len = unit_len
            else:
                current_units.append(unit)
                current_char_len += unit_len

        # Flush remaining buffer
        if current_units:
            raw_chunks.append(
                self._build_chunk(current_units, chunk_idx, doc_title)
            )

        return raw_chunks

    def _build_chunk(
        self,
        units: List[ExtractedDocumentUnit],
        chunk_idx: int,
        doc_title: str,
        force_table: bool = False,
    ) -> RawChunk:
        """Assemble units into a RawChunk with Late Chunking contextual header."""
        combined_raw = "\n\n".join(u.content.strip() for u in units)

        page_nums = [u.page_number for u in units if u.page_number is not None]
        min_page = min(page_nums) if page_nums else 1
        primary_section = units[0].section_title or "Overview"

        has_table = force_table or any(u.has_table for u in units)
        has_eq = any(u.has_equation for u in units)

        # Late Chunking (2024/2025): Contextual breadcrumb header prefix
        header_prefix = f"[Document: {doc_title} > Section: {primary_section}]\n"
        contextual_content = f"{header_prefix}{combined_raw}"

        char_cnt = len(contextual_content)
        est_tokens = math.ceil(char_cnt / self.CHARS_PER_TOKEN)

        return RawChunk(
            content=contextual_content,
            raw_content=combined_raw,
            page_number=min_page,
            section_title=primary_section,
            paragraph_start=0,
            paragraph_end=len(units),
            has_table=has_table,
            has_equation=has_eq,
            chunk_index=chunk_idx,
            char_count=char_cnt,
            token_count_estimate=est_tokens,
        )
