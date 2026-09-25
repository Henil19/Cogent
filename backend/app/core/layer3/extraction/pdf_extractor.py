"""
Sub-Module 3.3a: Structural PDF Layout Extractor
Research Basis:
- SCAN (ACL/EACL 2025/2026): Coarse-grained semantic document layout analysis
- TechDocRAG (AI 2026): Relation-preserving technical document structure (tables, equations)
Extracts multi-page PDFs with page numbers, section headers, and markdown-formatted tables.
"""

import io
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ExtractedDocumentUnit:
    """A structural section, paragraph group, or table extracted from a document page."""
    content: str
    page_number: int
    section_title: str
    has_table: bool = False
    has_equation: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class PDFExtractor:
    """Layout-aware PDF extractor using pdfplumber with pypdf fallback."""

    HEADER_PATTERN = re.compile(
        r"^(?:\d+\.?\d*\.?\d*\s+[A-Z][A-Za-z0-9\s]{2,50}|[A-Z\s]{4,40})$"
    )

    def extract_from_bytes(self, pdf_bytes: bytes, doc_title: str = "") -> List[ExtractedDocumentUnit]:
        """Extract structural units from PDF bytes."""
        units = []
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                current_section = "Introduction"
                for page_idx, page in enumerate(pdf.pages):
                    page_num = page_idx + 1
                    page_units = self._extract_pdfplumber_page(page, page_num, current_section)
                    if page_units:
                        units.extend(page_units)
                        # Update current section title if a new one was detected
                        last_title = [u.section_title for u in page_units if u.section_title != current_section]
                        if last_title:
                            current_section = last_title[-1]
        except Exception:
            # Graceful fallback to pypdf
            units = self._extract_pypdf_fallback(pdf_bytes)

        if not units:
            # Fallback if both had issues or empty
            units = [ExtractedDocumentUnit(
                content="[Empty or unscannable PDF document]",
                page_number=1,
                section_title="Document Body"
            )]

        return units

    def _extract_pdfplumber_page(
        self, page, page_num: int, current_section: str
    ) -> List[ExtractedDocumentUnit]:
        """Extract text and tables from a single page via pdfplumber."""
        units = []
        active_section = current_section

        # 1. Extract and convert tables to clean Markdown grids (TechDocRAG 2026)
        tables = page.extract_tables() or []
        for table in tables:
            if not table or len(table) < 2:
                continue
            table_md = self._format_table_as_markdown(table)
            if table_md:
                units.append(ExtractedDocumentUnit(
                    content=table_md,
                    page_number=page_num,
                    section_title=f"{active_section} (Tabular Data)",
                    has_table=True,
                    metadata={"row_count": len(table)}
                ))

        # 2. Extract plain text with structural headings (SCAN 2025)
        raw_text = page.extract_text(layout=False) or ""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        current_para = []
        for line in lines:
            # Check if line resembles a section header
            if len(line) < 60 and (line.isupper() or self.HEADER_PATTERN.match(line)):
                if current_para:
                    para_text = " ".join(current_para)
                    has_eq = bool(re.search(r"[$=+\\_{}\[\]^]", para_text))
                    units.append(ExtractedDocumentUnit(
                        content=para_text,
                        page_number=page_num,
                        section_title=active_section,
                        has_equation=has_eq
                    ))
                    current_para = []
                active_section = line.title() if line.isupper() else line
            else:
                current_para.append(line)

        if current_para:
            para_text = " ".join(current_para)
            has_eq = bool(re.search(r"[$=+\\_{}\[\]^]", para_text))
            units.append(ExtractedDocumentUnit(
                content=para_text,
                page_number=page_num,
                section_title=active_section,
                has_equation=has_eq
            ))

        return units

    def _format_table_as_markdown(self, table: List[List[Any]]) -> Optional[str]:
        """Convert a 2D list into standard GitHub Flavored Markdown table."""
        clean_rows = []
        for row in table:
            clean_row = [re.sub(r"\s+", " ", str(cell or "")).strip() for cell in row]
            if any(len(c) > 0 for c in clean_row):
                clean_rows.append(clean_row)

        if len(clean_rows) < 2:
            return None

        # Normalize column count
        max_cols = max(len(r) for r in clean_rows)
        normalized = [r + [""] * (max_cols - len(r)) for r in clean_rows]

        headers = normalized[0]
        separator = ["---"] * max_cols
        rows = normalized[1:]

        md_lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(separator) + " |"
        ]
        for row in rows:
            md_lines.append("| " + " | ".join(row) + " |")

        return "\n".join(md_lines)

    def _extract_pypdf_fallback(self, pdf_bytes: bytes) -> List[ExtractedDocumentUnit]:
        """Fast fallback extractor using pypdf."""
        units = []
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    units.append(ExtractedDocumentUnit(
                        content=text.strip(),
                        page_number=idx + 1,
                        section_title="Document Body"
                    ))
        except Exception:
            pass
        return units
