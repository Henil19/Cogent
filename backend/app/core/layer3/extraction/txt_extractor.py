"""
Sub-Module 3.3a: Plain Text & Markdown Structural Extractor
Parses .txt and .md files into structural ExtractedDocumentUnit items,
preserving Markdown headings, lists, and code blocks.
"""

import re
from typing import List
from app.core.layer3.extraction.pdf_extractor import ExtractedDocumentUnit


class TxtExtractor:
    """Extracts structural sections and code blocks from Markdown and plain text."""

    @staticmethod
    def _is_table_content(text: str) -> bool:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        table_lines = [l for l in lines if l.startswith("|") and "|" in l[1:]]
        return len(table_lines) >= 2 and any("-" in l for l in table_lines)

    @staticmethod
    def _is_equation_content(text: str) -> bool:
        return bool(re.search(r"(\$\$.*?\$\$|\\\[.*?\\\]|\\begin\{equation\}|\\mathcal|\\lambda|\\theta|\\mu|\\rho|\\nabla)", text, re.DOTALL))

    def _create_unit(self, paragraphs: List[str], current_section: str) -> ExtractedDocumentUnit:
        para_text = "\n\n".join(paragraphs)
        has_table = self._is_table_content(para_text)
        has_equation = self._is_equation_content(para_text)
        return ExtractedDocumentUnit(
            content=para_text,
            page_number=1,
            section_title=current_section,
            has_table=has_table,
            has_equation=has_equation
        )

    def extract_from_text(self, text: str, doc_title: str = "Document") -> List[ExtractedDocumentUnit]:
        """Parse text or Markdown into structural units."""
        if not text or not text.strip():
            return []

        from app.core.layer3.processing.normalizer import ContentNormalizer
        text = ContentNormalizer.normalize(text)

        units = []
        lines = text.splitlines()

        current_section = doc_title or "Overview"
        current_paragraphs: List[str] = []
        in_code_block = False
        code_block_lines: List[str] = []

        for line in lines:
            stripped = line.strip()

            # Handle code block fences
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                code_block_lines.append(line)
                if not in_code_block:
                    # Closing code block -> flush as dedicated unit
                    full_code = "\n".join(code_block_lines)
                    units.append(ExtractedDocumentUnit(
                        content=full_code,
                        page_number=1,
                        section_title=f"{current_section} (Code Block)",
                        has_equation=False,
                        metadata={"type": "code"}
                    ))
                    code_block_lines = []
                continue

            if in_code_block:
                code_block_lines.append(line)
                continue

            # Detect Markdown headings (# Header, ## Subheader)
            header_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            if header_match:
                if current_paragraphs:
                    units.append(self._create_unit(current_paragraphs, current_section))
                    current_paragraphs = []
                current_section = header_match.group(2).strip()
                continue

            # Paragraph accumulation
            if stripped:
                current_paragraphs.append(stripped)
            elif current_paragraphs:
                units.append(self._create_unit(current_paragraphs, current_section))
                current_paragraphs = []

        if current_paragraphs:
            units.append(self._create_unit(current_paragraphs, current_section))

        return units
