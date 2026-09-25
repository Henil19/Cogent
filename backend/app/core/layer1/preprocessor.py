"""
Sub-Module 1.1: Request Preprocessor
Cleans, normalizes, sanitizes, validates, and performs language detection on user input.
Research basis: Standard NLP preprocessing pipeline.
"""

import re
import unicodedata
from typing import Tuple, Optional, Dict, Any


class RequestPreprocessor:
    """Preprocesses raw user input for downstream linguistic and ambiguity analysis."""

    def __init__(self, min_length: int = 3, max_length: int = 4000):
        self.min_length = min_length
        self.max_length = max_length

    def preprocess(self, raw_query: str) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """
        Normalize, sanitize, and detect language of user query.
        Returns:
            (cleaned_query, error_message, metadata)
        """
        metadata: Dict[str, Any] = {
            "is_english": True,
            "detected_language": "en",
            "original_length": len(raw_query) if raw_query else 0,
            "sanitized_length": 0,
        }

        if not raw_query or not raw_query.strip():
            return "", "Query cannot be empty or solely whitespace.", metadata

        text = raw_query.strip()
        if len(text) > self.max_length:
            text = text[:self.max_length].rstrip()

        # Unicode normalization (NFC as per W3C and NLP standards)
        text = unicodedata.normalize("NFC", text)

        # Remove null bytes and non-printable control characters (except newline, tab)
        text = "".join(ch for ch in text if ch in ("\n", "\t") or unicodedata.category(ch)[0] != "C")

        # Normalize whitespace (collapse multiple spaces/tabs into single space)
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
        text = "\n".join(line for line in lines if line)

        # Strip dangerous HTML and script tags
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<[^>]+>", "", text)

        metadata["sanitized_length"] = len(text)

        if len(text) < self.min_length:
            return "", f"Query is too short. Please provide at least {self.min_length} characters.", metadata

        # Language detection (ASCII / Latin script ratio check)
        # Identifies non-Latin/non-English scripts (e.g. Cyrillic, CJK, Arabic, Devanagari)
        total_alpha = sum(1 for ch in text if ch.isalpha())
        if total_alpha > 0:
            latin_chars = sum(1 for ch in text if "LATIN" in unicodedata.name(ch, ""))
            latin_ratio = latin_chars / total_alpha
            if latin_ratio < 0.65:
                metadata["is_english"] = False
                metadata["detected_language"] = "non-en"
                return (
                    text,
                    "Cogent currently requires English research queries. Please provide an English translation.",
                    metadata,
                )

        return text, None, metadata
