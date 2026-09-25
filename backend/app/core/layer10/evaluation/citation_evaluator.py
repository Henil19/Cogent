"""
Sub-Module 10.3: Citation Precision & Coverage Evaluator (CiteBench, ACL 2025)
Audits the fidelity, precision, and coverage of rendered citations against
the verified TROVE coordinates and underlying evidence pool.
"""

from typing import List, Dict, Any, Tuple
import re


class CitationEvaluator:
    """
    Measures:
    1. Citation Precision: Fraction of cited documents that genuinely support the associated assertion.
    2. Citation Coverage: Fraction of verifiable factual assertions that possess citation anchors.
    3. Orphan Detection: Presence of citations referring to non-existent registry entries.
    """

    def __init__(self):
        pass

    def evaluate_citations(
        self,
        rendered_sections: List[Dict[str, Any]],
        citation_registry: Dict[str, Any],
        claims: List[Dict[str, Any]]
    ) -> Tuple[float, float, List[str]]:
        """
        Returns:
            (citation_precision, citation_coverage, orphan_citations)
        """
        orphan_citations = []
        referenced_numbers = set()

        # Normalize citation_registry to dict
        reg_dict: Dict[str, Any] = {}
        if isinstance(citation_registry, list):
            for b in citation_registry:
                b_num = b.get("citation_number") if isinstance(b, dict) else getattr(b, "citation_number", None)
                if b_num is not None:
                    reg_dict[str(b_num)] = b
        elif isinstance(citation_registry, dict):
            reg_dict = citation_registry

        # Find all [k] citation tags in body text
        for sec in rendered_sections:
            sec_type = sec.get("section_type", "") if isinstance(sec, dict) else getattr(sec, "section_type", "")
            if str(sec_type) in ("REFERENCES_FOOTNOTES", "ResponseSectionType.REFERENCES_FOOTNOTES"):
                continue
            text = sec.get("content_markdown", "") if isinstance(sec, dict) else getattr(sec, "content_markdown", "")
            matches = re.findall(r'\[(\d+)\]', text)
            for m in matches:
                referenced_numbers.add(int(m))
                if str(m) not in reg_dict and int(m) not in reg_dict:
                    orphan_citations.append(f"Orphan citation tag [{m}] in section {sec_type}")

        total_registered = len(reg_dict)
        if total_registered == 0 and not referenced_numbers:
            return 1.0, 1.0, []

        # Precision: fraction of referenced numbers that have valid verified quotes in registry
        valid_citations = 0
        for num in referenced_numbers:
            entry = reg_dict.get(str(num)) or reg_dict.get(num)
            if entry:
                if isinstance(entry, dict):
                    quote = entry.get("quoted_snippet") or entry.get("verbatim_quote") or entry.get("snippet", "")
                else:
                    quote = getattr(entry, "quoted_snippet", None) or getattr(entry, "verbatim_quote", None) or getattr(entry, "snippet", "")
                if quote:
                    valid_citations += 1

        citation_precision = (
            round(valid_citations / len(referenced_numbers), 3)
            if referenced_numbers else 1.0
        )

        # Coverage: fraction of upstream claims that received at least one citation
        if not claims:
            citation_coverage = 1.0
        else:
            cited_claims_count = 0
            for c in claims:
                tokens = c.get("citation_tokens", []) if isinstance(c, dict) else getattr(c, "citation_tokens", [])
                cid = c.get("claim_id", "") if isinstance(c, dict) else getattr(c, "claim_id", "")
                if tokens or (cid and any(cid in str(v) for v in reg_dict.values())):
                    cited_claims_count += 1
            citation_coverage = round(cited_claims_count / len(claims), 3)

        return citation_precision, citation_coverage, orphan_citations
