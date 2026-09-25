"""
Sub-Module 3.2: Technical Quality Diagnostic Checker
Research Basis: Acquisition Quality Gating (KDD 2024/2025)
Calculates extraction_quality score (0.0 to 1.0) evaluating syntactic & formatting hygiene.
Note: Evaluates technical extraction cleanliness, NOT factual truth or credibility.
"""

import re


class QualityChecker:
    """Computes technical extraction quality diagnostics for documents and chunks."""

    @classmethod
    def compute_quality_score(cls, text: str) -> float:
        """
        Calculate technical extraction quality (0.0 to 1.0).
        Evaluates text completeness, punctuation balance, character distribution,
        and formatting integrity based on KDD 2024/2025 quality gating principles.
        """
        if not text or len(text.strip()) == 0:
            return 0.0

        cleaned = text.strip()
        total_len = len(cleaned)

        # 1. Printable character ratio (0.0 - 0.35 weight)
        # Any control characters (ord < 32 except newline/tab) strictly penalize printable score
        control_chars = sum(1 for c in cleaned if (ord(c) < 32 and c not in "\n\r\t") or c == "\ufffd")
        if control_chars > 0:
            score_printable = max(0.0, 0.35 - (control_chars * 0.10))
        else:
            printable_count = sum(1 for c in cleaned if c.isprintable() or c in "\n\r\t")
            p_ratio = printable_count / total_len
            score_printable = min(max(p_ratio, 0.0), 1.0) * 0.35

        # 2. Word structure sanity & alphanumeric ratio (0.0 - 0.35 weight)
        words = re.findall(r"\b[A-Za-z0-9\-_]+\b", cleaned)
        if not words:
            return 0.05

        avg_word_len = sum(len(w) for w in words) / len(words)
        alnum_chars = sum(len(w) for w in words)
        alnum_ratio = alnum_chars / total_len

        # Healthy English/technical text has avg word length 3.8 - 11.0 and alnum_ratio >= 0.65
        if 3.8 <= avg_word_len <= 11.0 and alnum_ratio >= 0.65:
            score_word = 0.35
        elif 3.0 <= avg_word_len <= 14.0 and alnum_ratio >= 0.45:
            score_word = 0.20
        else:
            score_word = 0.05

        # 3. Punctuation sanity & excessive repetition check (0.0 - 0.15 weight)
        # Check for excessive noise symbols like @#$%^&* or repeated punctuation ?????
        noisy_symbols = len(re.findall(r"[%^&*\$#@~`+=|<>{}\[\]]", cleaned))
        symbol_ratio = noisy_symbols / total_len
        has_excessive_repeat = bool(re.search(r"([?!.]{3,})", cleaned))

        if symbol_ratio > 0.15 or has_excessive_repeat:
            score_punct = 0.02
        elif total_len >= 50 and re.search(r"[.!?]\s+[A-Z0-9]", cleaned):
            score_punct = 0.15
        elif total_len < 50 and re.search(r"[.!?]", cleaned):
            score_punct = 0.10
        else:
            score_punct = 0.08

        # 4. Absence of replacement/corruption artifacts (0.0 - 0.15 weight)
        if control_chars == 0 and "\ufffd" not in cleaned:
            score_clean = 0.15
        else:
            score_clean = 0.0

        total_quality = score_printable + score_word + score_punct + score_clean
        return round(min(max(total_quality, 0.0), 1.0), 3)
