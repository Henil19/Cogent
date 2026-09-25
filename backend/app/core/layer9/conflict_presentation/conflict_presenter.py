"""
Sub-Module 9.5: Dialectical Conflict Presentation Engine
Transforms Layer 8's dialectical conflict explanations into side-by-side comparison widget contracts.
Strictly upholds Cogent's Zero Winner Forcing invariant in user-facing presentation.
Research: ConfRAG (ACL 2026), Do Multi-Document Summarization Models Synthesize? (TACL 2024).
"""

import re
from typing import List, Dict
from app.schemas.layer8 import ExplanationPackage, ConflictExplanation
from app.schemas.layer9 import ConflictWidgetPayload, CitationBadgeEntry


def clean_dialectical_statement(text: str) -> str:
    """Cleans raw manuscript citations, table/figure references, and filler openers for clear UX."""
    if not text:
        return ""
    s = text.strip()

    # Remove leading editorial ellipses and brackets: '[...]', '(...)'
    s = re.sub(r"^\s*\[(?:\.\.\.|\s)*\]\s*", "", s)
    s = re.sub(r"^\s*\((?:\.\.\.|\s)*\)\s*", "", s)
    s = re.sub(r"\[(?:\.\.\.|\s)*\]", " ", s)

    # Remove internal manuscript table/figure references: (Table 3), (Figure 1), (see Table 2), etc.
    s = re.sub(r"\s*\((?:see\s+)?(?:Table|Figure|Fig\.|Box|Supplementary\s+Table)\s*[\dA-Za-z\s,\.-]*\)", "", s, flags=re.IGNORECASE)

    # Remove bracketed citation numbers: [12], [12,21,22], [38, 66], [13, 195, 205-207]
    s = re.sub(r"\s*\[[\d\s,–\-\+]+\]", "", s)

    # Remove unclosed or messy author-year parentheticals: (Desbrow and Leveritt, 2006, 2007. or (Jodra et al., 2020)
    s = re.sub(r"\s*\([A-Z][a-zA-Z\s,–\-]+(?:et\s+al\.?)?,?\s*\d{4}[^\)]*\)?", "", s)

    # Clean conversational / editorial filler openers
    s = re.sub(r"^(?:And,?\s+if\s+that\s+isn't\s+enough,?\s*)", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^Likewise,?\s+when\s+considering\s+", "When considering ", s, flags=re.IGNORECASE)
    s = re.sub(r"^Overall,?\s+it\s+is\s+established\s+that\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^However,?\s+in\s+experiments\s+about\s+[^,]+,\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^Notably,?\s+", "", s, flags=re.IGNORECASE)

    # Clean spacing around punctuation
    s = re.sub(r"\s+([,\.\?!;:])", r"\1", s)
    s = re.sub(r"\s{2,}", " ", s).strip()

    # Capitalize first letter
    if s and s[0].islower():
        s = s[0].upper() + s[1:]
    if s and not s.endswith((".", "!", "?")):
        s += "."
    return s


class ConflictPresenter:
    """
    Sub-Module 9.5: Prepares structured comparison contracts for contradictory evidence.
    Does NOT choose a winner; presents thesis and antithesis neutrally with divergence context.
    """

    def __init__(self):
        pass

    def build_conflict_widgets(
        self,
        explanation_pkg: ExplanationPackage,
        citation_registry: List[CitationBadgeEntry]
    ) -> List[ConflictWidgetPayload]:
        """
        Builds side-by-side comparison widget payloads from Layer 8 conflict explanations.
        """
        widgets: List[ConflictWidgetPayload] = []
        ev_to_badges: Dict[str, List[int]] = {}
        for entry in citation_registry:
            ev_to_badges.setdefault(entry.evidence_id, []).append(entry.citation_number)

        for conf in explanation_pkg.conflict_explanations:
            aspect = getattr(conf, "aspect", None)
            if not aspect or "clm_chk" in str(aspect) or " vs " in str(aspect):
                aspect = "Reported Discrepancy"

            raw_thesis = getattr(conf, "thesis_statement", None) or getattr(conf, "thesis_explanation", "Position A")
            if str(raw_thesis).startswith("clm_chk_"):
                raw_thesis = getattr(conf, "thesis_explanation", "Position A")

            raw_antithesis = getattr(conf, "antithesis_statement", None) or getattr(conf, "antithesis_explanation", "Position B")
            if str(raw_antithesis).startswith("clm_chk_"):
                raw_antithesis = getattr(conf, "antithesis_explanation", "Position B")

            thesis_stmt = clean_dialectical_statement(str(raw_thesis))
            antithesis_stmt = clean_dialectical_statement(str(raw_antithesis))

            context_div = getattr(conf, "contextual_divergence_explanation", None) or getattr(conf, "contextual_distinction", "Divergence under distinct empirical regimes.")
            res_status = getattr(conf, "resolution_status", "CONTEXTUAL_DIFFERENCE")

            t_ev_id = getattr(conf, "thesis_evidence_id", None) or getattr(conf, "claim_a", "")
            a_ev_id = getattr(conf, "antithesis_evidence_id", None) or getattr(conf, "claim_b", "")

            thesis_ev = [t_ev_id] if t_ev_id else []
            antithesis_ev = [a_ev_id] if a_ev_id else []

            thesis_badges = []
            for ev in thesis_ev:
                thesis_badges.extend(ev_to_badges.get(ev, []))

            antithesis_badges = []
            for ev in antithesis_ev:
                antithesis_badges.extend(ev_to_badges.get(ev, []))

            # Retrieve source title: first check if explicitly attached on ConflictExplanation
            t_title = getattr(conf, "thesis_source_title", None)
            a_title = getattr(conf, "antithesis_source_title", None)

            # If not provided, match against citation registry
            if not t_title:
                for entry in citation_registry:
                    if entry.evidence_id == t_ev_id or entry.claim_id == t_ev_id or (t_ev_id and entry.evidence_id in t_ev_id):
                        t_title = entry.source_title
                        break
            if not a_title:
                for entry in citation_registry:
                    if entry.evidence_id == a_ev_id or entry.claim_id == a_ev_id or (a_ev_id and entry.evidence_id in a_ev_id):
                        a_title = entry.source_title
                        break

            # Fallback to clear neutral academic study titles
            t_title = t_title or "Empirical Study A"
            a_title = a_title or "Empirical Study B"

            widget = ConflictWidgetPayload(
                conflict_id=conf.conflict_id,
                aspect=aspect,
                thesis_statement=thesis_stmt,
                thesis_evidence_ids=thesis_ev,
                thesis_citation_badges=list(dict.fromkeys(thesis_badges)),
                thesis_source_title=t_title,
                antithesis_statement=antithesis_stmt,
                antithesis_evidence_ids=antithesis_ev,
                antithesis_citation_badges=list(dict.fromkeys(antithesis_badges)),
                antithesis_source_title=a_title,
                contextual_divergence_explanation=context_div,
                resolution_status=res_status
            )
            widgets.append(widget)

        return widgets
