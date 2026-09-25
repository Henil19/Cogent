"""
Sub-Module 3.2: Acquisition Validation & Integrity Engine
Research Basis: Acquisition Quality Gating for RAG (KDD 2024/2025)
Enforces pre-retrieval validation gates to prevent error cascades:
1. Verifies non-empty extracted text
2. Detects OCR artifacts, replacement characters, and corrupted encodings
3. Verifies web response validity and readability
4. Assigns explicit lifecycle acquisition states (VALIDATED, REJECTED_QUALITY)
"""

import re
from typing import Tuple, List, Optional
from app.schemas.layer3 import AcquisitionStatus, SourceType


class IntegrityValidator:
    """Pre-retrieval validation gate for local documents and live web pages."""

    MIN_TEXT_LENGTH = 30  # Minimum meaningful character count

    @classmethod
    def validate_bytes(cls, file_bytes: bytes, filename: str) -> Tuple[bool, Optional[str], Optional[SourceType]]:
        """
        Validate file raw bytes, extension, and integrity before extraction.
        Returns (is_valid, error_message, source_type).
        """
        if not file_bytes or len(file_bytes) == 0:
            return False, "File is completely empty (0 bytes).", None

        if len(file_bytes) > 50 * 1024 * 1024:
            return False, "File exceeds maximum allowed size (50 MB).", None

        lower_fn = filename.lower()
        if lower_fn.endswith(".pdf"):
            stype = SourceType.LOCAL_PDF
            if b"%PDF" not in file_bytes[:1024]:
                return False, "File header does not match valid PDF magic bytes.", None
        elif lower_fn.endswith(".txt"):
            stype = SourceType.LOCAL_TXT
            if b"\x00" in file_bytes[:4096]:
                return False, "Binary null bytes detected in plain text file.", None
        elif lower_fn.endswith(".md"):
            stype = SourceType.LOCAL_MD
            if b"\x00" in file_bytes[:4096]:
                return False, "Binary null bytes detected in markdown file.", None
        else:
            return False, f"Unsupported file extension in '{filename}'. Allowed: .pdf, .txt, .md", None

        return True, None, stype

    @classmethod
    def validate_extracted_text(cls, text: str, source_uri: str = "") -> Tuple[bool, AcquisitionStatus, List[str]]:
        """
        Validates text extracted from PDFs, TXT, or Web.
        Returns (is_valid, status, list_of_warnings).
        """
        warnings = []
        if not text or len(text.strip()) == 0:
            return False, AcquisitionStatus.REJECTED_QUALITY, ["Extracted text is completely empty."]

        cleaned = text.strip()
        if len(cleaned) < cls.MIN_TEXT_LENGTH:
            return False, AcquisitionStatus.REJECTED_QUALITY, [
                f"Extracted content ({len(cleaned)} chars) is below minimum meaningful threshold ({cls.MIN_TEXT_LENGTH} chars)."
            ]

        # Check for corrupted replacement characters (common in bad OCR / bad PDF extraction)
        replacement_count = cleaned.count("\ufffd")
        if replacement_count > 10 and (replacement_count / len(cleaned)) > 0.05:
            return False, AcquisitionStatus.REJECTED_QUALITY, [
                f"Severe encoding corruption detected: {replacement_count} replacement characters found."
            ]
        elif replacement_count > 0:
            warnings.append(f"Minor encoding artifacts: {replacement_count} replacement characters detected.")

        # Check printable character ratio
        printable_chars = sum(1 for c in cleaned if c.isprintable() or c in "\n\r\t")
        printable_ratio = printable_chars / len(cleaned)
        if printable_ratio < 0.85:
            return False, AcquisitionStatus.REJECTED_QUALITY, [
                f"Low printable character density ({printable_ratio:.2%}). Likely binary or corrupted stream."
            ]

        # Check for abnormal average token length (run-on binary strings)
        words = re.findall(r"\b\w+\b", cleaned)
        if words:
            avg_word_len = sum(len(w) for w in words) / len(words)
            if avg_word_len > 35:
                warnings.append(f"Unusually high average word length ({avg_word_len:.1f} chars). Potential OCR concat issue.")

        return True, AcquisitionStatus.VALIDATED, warnings

    @classmethod
    def validate_web_content(
        cls, status_code: int, html_body: str, url: str
    ) -> Tuple[bool, AcquisitionStatus, List[str]]:
        """Validate live web response before parsing."""
        if status_code != 200:
            return False, AcquisitionStatus.FAILED_ACQUISITION, [
                f"Web request failed with HTTP status code {status_code} for URL: {url}"
            ]

        if not html_body or len(html_body.strip()) < 100:
            return False, AcquisitionStatus.REJECTED_QUALITY, [
                f"Web response payload from {url} is empty or near-empty."
            ]

        return True, AcquisitionStatus.ACQUIRED, []
