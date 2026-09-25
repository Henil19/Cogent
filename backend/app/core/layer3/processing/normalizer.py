"""
Sub-Module 3.4: Technical Content Normalizer
Research Basis: TechDocRAG (AI 2026)
Normalizes text while strictly preserving:
1. Mathematical notation and LaTeX formulas ($...$, \\frac, \\alpha)
2. Markdown tables (| Col | Col |)
3. Code blocks and algorithmic variables
4. Section numbers and clause identifiers (e.g. 1.2.3)
"""

import re


class ContentNormalizer:
    """Structure-aware text normalizer preserving mathematical and tabular notation."""

    @classmethod
    def normalize(cls, text: str) -> str:
        """Clean whitespace and formatting while preserving math, code, and tables."""
        if not text:
            return ""

        # Strip unprintable control characters and zero-width artifacts (except tab, newline, carriage return)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200b\u200c\u200d\ufeff]", "", text)

        lines = text.splitlines()
        normalized_lines = []

        in_table = False
        in_code = False

        for line in lines:
            stripped = line.strip()

            # Preserve code fences
            if stripped.startswith("```"):
                in_code = not in_code
                normalized_lines.append(stripped)
                continue

            if in_code:
                normalized_lines.append(line)  # Preserve code formatting as-is
                continue

            # Check for Markdown table line
            if stripped.startswith("|") and stripped.endswith("|"):
                in_table = True
                normalized_lines.append(stripped)
                continue
            else:
                in_table = False

            # Normalize standard prose line
            if stripped:
                # Remove hyphens at line breaks (e.g., "imple- \n mentation" -> "implementation")
                line_clean = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", stripped)
                # Collapse redundant horizontal spaces while preserving newlines
                line_clean = re.sub(r"[ \t]+", " ", line_clean)
                normalized_lines.append(line_clean)
            else:
                normalized_lines.append("")

        result = "\n".join(normalized_lines)
        # Collapse more than two consecutive newlines
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()

    # Convenience alias
    normalize_text = normalize
