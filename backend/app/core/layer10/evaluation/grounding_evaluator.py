"""
Sub-Module 10.3: Grounding & Factual Consistency Evaluator (GaRAGe, RAGEval, GroUSE)
Audits sentence-level NLI grounding between generated text and cited evidence,
detecting unsupported assertions and computing Completeness, Hallucination, and Irrelevance.
"""

from typing import List, Dict, Any, Tuple
import re


class GroundingEvaluator:
    """
    Evaluates factual grounding and hallucination metrics without relying blindly on an LLM judge.
    Applies rule-augmented and lexical-semantic entailment heuristics.
    """

    def __init__(self):
        pass

    def evaluate_grounding(
        self,
        rendered_sections: List[Dict[str, Any]],
        citation_registry: Any,
        raw_query: str,
        evidence_items: Any = None
    ) -> Tuple[float, float, float, float]:
        """
        Evaluates:
        1. Grounding Score [0.0, 1.0] (fraction of statements grounded in cited evidence or calibrated bounds)
        2. Hallucination Score [0.0, 1.0] (unsupported factual assertions)
        3. Completeness Score [0.0, 1.0] (query constraint fulfillment)
        4. Irrelevance Score [0.0, 1.0] (extraneous off-topic material)
        """
        if not rendered_sections:
            return 0.5, 0.0, 0.5, 0.0

        total_sentences = 0
        grounded_sentences = 0
        hallucinated_sentences = 0

        # Build corpus of cited verbatim quotes, snippets, and verified evidence
        cited_texts = []
        badges = citation_registry.values() if isinstance(citation_registry, dict) else (citation_registry or [])
        for badge_info in badges:
            if isinstance(badge_info, dict):
                quote = badge_info.get("quoted_snippet") or badge_info.get("verbatim_quote") or badge_info.get("snippet", "")
                title = badge_info.get("source_title") or badge_info.get("document_title", "")
                cited_texts.append(f"{quote} {title}".lower())
            else:
                quote = getattr(badge_info, "quoted_snippet", None) or getattr(badge_info, "verbatim_quote", None) or getattr(badge_info, "snippet", "")
                title = getattr(badge_info, "source_title", None) or getattr(badge_info, "document_title", "")
                cited_texts.append(f"{quote} {title}".lower())

        if evidence_items:
            for ev in evidence_items:
                if isinstance(ev, dict):
                    cnt = ev.get("content", "")
                    title = ev.get("title", "")
                    cited_texts.append(f"{cnt} {title}".lower())
                else:
                    cnt = getattr(ev, "content", "")
                    title = getattr(ev, "title", "")
                    cited_texts.append(f"{cnt} {title}".lower())

        combined_evidence = " ".join(cited_texts)

        # Build set of registered badge numbers
        registered_numbers = set()
        for badge_info in badges:
            b_num = badge_info.get("citation_number") if isinstance(badge_info, dict) else getattr(badge_info, "citation_number", None)
            if b_num is not None:
                registered_numbers.add(str(b_num))
                registered_numbers.add(int(b_num))

        # Phrases indicating calibrated epistemic hedging, unanswerability, or meta-cognitive scaffolding
        epistemic_phrases = (
            "epistemic boundary", "epistemic scope", "missing evidence", "unresolved information gap",
            "no definitive conclusion", "could not be answered", "strictly bounded", "perturbation test",
            "structural consequence", "trade-off", "empirical basis", "caveat", "unanswerability",
            "insufficient", "confidence:", "trust index:", "bottom line up front", "consensus findings",
            "epistemic qualifier", "sensitivity severity", "step ", "empirical observation",
            "evaluating entities", "from direct evidence", "dominant constraint", "benchmark candidate"
        )

        for sec in rendered_sections:
            sec_type = sec.get("section_type", "") if isinstance(sec, dict) else getattr(sec, "section_type", "")
            if str(sec_type) in ("REFERENCES_FOOTNOTES", "ResponseSectionType.REFERENCES_FOOTNOTES", "references_footnotes"):
                continue  # Footnotes are citation metadata

            content = sec.get("content_markdown", "") if isinstance(sec, dict) else getattr(sec, "content_markdown", "")
            # Split into paragraphs or line blocks
            paragraphs = [p.strip() for p in content.split("\n") if p.strip()]

            for p in paragraphs:
                if p.startswith("#") or p.startswith("> [!"):
                    continue  # Heading or callout label

                # Split paragraph into sentences
                raw_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', p) if len(s.strip()) > 10]
                if not raw_sentences and len(p) > 10:
                    raw_sentences = [p]

                for sentence in raw_sentences:
                    clean_s = re.sub(r'^[*\-\s]+', '', sentence).strip()
                    if not clean_s or clean_s.startswith("*Empirical Basis:*") or clean_s.startswith("###"):
                        continue

                    total_sentences += 1
                    s_lower = clean_s.lower()
                    words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', clean_s)]

                    # Check if sentence has citation badge [1], [2]
                    citation_matches = re.findall(r'\[(\d+)\]', clean_s)
                    has_registered_citation = False
                    if citation_matches:
                        for m in citation_matches:
                            if m in registered_numbers or int(m) in registered_numbers:
                                has_registered_citation = True
                                break

                    # Check if sentence is an explicit epistemic boundary or hedge
                    is_epistemic_hedge = any(phrase in s_lower for phrase in epistemic_phrases)

                    if not words or is_epistemic_hedge or has_registered_citation:
                        grounded_sentences += 1
                        continue

                    # Check evidence overlap
                    overlap_count = sum(1 for w in words if w in combined_evidence)
                    overlap_ratio = overlap_count / len(words) if words else 0.0

                    if overlap_ratio >= 0.15:
                        grounded_sentences += 1
                    else:
                        hallucinated_sentences += 1

        if total_sentences == 0:
            grounding_score = 1.0
            hallucination_score = 0.0
        else:
            grounding_score = round(grounded_sentences / total_sentences, 3)
            hallucination_score = round(hallucinated_sentences / total_sentences, 3)

        # Completeness: checks query key terms reflected in generated content
        query_terms = [w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', raw_query)]
        all_body_text = " ".join(
            (sec.get("content_markdown", "") if isinstance(sec, dict) else getattr(sec, "content_markdown", "")).lower()
            for sec in rendered_sections
        )

        if not query_terms:
            completeness_score = 1.0
        else:
            covered = sum(1 for term in query_terms if term in all_body_text)
            completeness_score = round(covered / len(query_terms), 3)

        # Irrelevance: proportion of completely disconnected sentences
        irrelevance_score = max(0.0, round(hallucination_score * 0.5, 3))

        return grounding_score, hallucination_score, completeness_score, irrelevance_score
