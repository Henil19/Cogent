"""
Sub-Module 9.8a: Response Safety & Consistency Validator
Performs lightweight post-generation consistency audits on the final assembled text.
Detects unsupported or weakly grounded assertions, orphan citation badges, and tone mismatches.
Research: Provenance (EMNLP 2024 Industry), RAG-Zeval (EMNLP 2025), Rationale-Aware Verification (EMNLP 2024).
"""

import re
from typing import List, Set, Optional
from app.schemas.layer7 import TrustAssessment
from app.schemas.layer8 import ExplanationPackage
from app.schemas.layer9 import RenderedSection, CitationBadgeEntry, ResponseValidationReport


class ResponseSafetyValidator:
    """
    Sub-Module 9.8a: Validates final assembled response text before user presentation.
    Detects ungrounded assertions, orphan citations, and tone policy violations.
    """

    OVERCONFIDENT_POLICY_TERMS = [
        "conclusively proves",
        "indisputable fact",
        "absolute certainty",
        "100% guaranteed",
        "beyond all doubt",
        "incontestable proof",
        "this is definitely true",
        "definitely true",
        "definitely causes",
        "undeniably true",
        "proven beyond doubt"
    ]

    def __init__(self, certainty_policy_threshold: float = 0.80):
        """
        Initializes validator with a configurable certainty presentation policy threshold.
        """
        self.certainty_policy_threshold = certainty_policy_threshold

    def validate_response(
        self,
        sections: List[RenderedSection],
        citation_registry: List[CitationBadgeEntry],
        trust_assessment: TrustAssessment,
        explanation_pkg: ExplanationPackage,
        trust_badges: Optional[Any] = None,
        conflict_widgets: Optional[List[Any]] = None
    ) -> ResponseValidationReport:
        """
        Executes post-generation consistency and safety audit.
        Catches:
          - Unsupported claims
          - Confidence / tone inflation
          - Citation badge orphans
          - Conflict suppression
          - Trust / confidence mutation
        """
        # Aggregate full rendered markdown text
        full_text = "\n\n".join(s.content_markdown for s in sections)
        
        # 1. Sentence splitting
        sentences = [
            s.strip() for s in re.split(r"(?<=[.!?])\s+", full_text)
            if len(s.strip()) > 10 and not s.strip().startswith("#") and not s.strip().startswith("-")
        ]
        sentence_count = len(sentences)

        # 2. Check for orphan citation badges in text
        all_text_badges = set(int(b) for b in re.findall(r"\[(\d+)\]", full_text))
        registry_badges = set(entry.citation_number for entry in citation_registry)
        orphan_badges = list(all_text_badges - registry_badges)

        # 3. Tone Policy & Confidence Inflation Check
        tone_violations: List[str] = []
        conf = trust_assessment.global_confidence
        if conf < self.certainty_policy_threshold:
            lower_text = full_text.lower()
            for term in self.OVERCONFIDENT_POLICY_TERMS:
                if term in lower_text:
                    tone_violations.append(
                        f"Tone policy violation: Found overconfident phrase '{term}' "
                        f"while calibrated confidence is {conf:.2f} (below policy threshold {self.certainty_policy_threshold})."
                    )

        # 4. Detect unsupported or weakly grounded assertions
        unsupported_assertions: List[str] = []
        valid_evidence_quotes = [
            (getattr(attr, "verbatim_quote", None) or getattr(attr, "quoted_text", "")).lower()
            for attr in explanation_pkg.evidence_attributions
            if (getattr(attr, "verbatim_quote", None) or getattr(attr, "quoted_text", None))
        ]
        
        # Check claim sentences against attributed premise text
        for claim in explanation_pkg.claim_explanations:
            c_text = claim.statement.lower()
            tokens = c_text.split()
            if len(tokens) > 4:
                has_sub_grounding = any(tokens[0] in q for q in valid_evidence_quotes) if valid_evidence_quotes else True
                if not has_sub_grounding and not claim.supporting_evidence_ids:
                    unsupported_assertions.append(f"Assertion '{claim.statement[:60]}...' lacks explicit supporting evidence IDs.")

        penalty = 0.0
        if orphan_badges:
            penalty += 0.4 * len(orphan_badges)
        if tone_violations:
            penalty += 0.4 * len(tone_violations)
        if unsupported_assertions:
            penalty += 0.3 * len(unsupported_assertions)

        # 5. Conflict Suppression Audit
        if explanation_pkg.conflict_explanations:
            has_conflict_display = (
                (conflict_widgets is not None and len(conflict_widgets) > 0) or
                any(
                    s.section_type.value == "conflicting_evidence" or
                    "diverging" in s.content_markdown.lower() or
                    "discrepanc" in s.content_markdown.lower() or
                    "divergence" in s.content_markdown.lower()
                    for s in sections
                )
            )
            if not has_conflict_display:
                unsupported_assertions.append(
                    f"Conflict suppression violation: {len(explanation_pkg.conflict_explanations)} dialectical contradictions exist in Layer 8 but were suppressed in presentation."
                )
                penalty += 0.5

        # 6. Trust Mutation Audit
        if trust_badges is not None:
            expected_conf = round(trust_assessment.global_confidence, 2)
            expected_gti = round(trust_assessment.global_trust_index, 2)
            if abs(trust_badges.calibrated_confidence - expected_conf) > 1e-4:
                unsupported_assertions.append(
                    f"Trust mutation violation: Confidence mutated from L7 {expected_conf} to L9 {trust_badges.calibrated_confidence}."
                )
                penalty += 0.5
            if abs(trust_badges.trust_index - expected_gti) > 1e-4:
                unsupported_assertions.append(
                    f"Trust mutation violation: GTI mutated from L7 {expected_gti} to L9 {trust_badges.trust_index}."
                )
                penalty += 0.5

        safety_score = max(0.0, round(1.0 - penalty, 2))
        is_safe = (safety_score >= 0.70 and len(orphan_badges) == 0 and len(tone_violations) == 0)

        attributed_ratio = 1.0
        if sentence_count > 0:
            cited_sentences = sum(1 for s in sentences if re.search(r"\[\d+\]", s))
            attributed_ratio = min(1.0, round((cited_sentences + 1) / sentence_count, 2))

        return ResponseValidationReport(
            is_safe_for_presentation=is_safe,
            sentence_count=sentence_count,
            attributed_sentence_ratio=attributed_ratio,
            unsupported_assertions=unsupported_assertions,
            orphan_citation_badges=orphan_badges,
            tone_policy_violations=tone_violations,
            validation_score=safety_score
        )
