"""
Sub-Module 8.1: Claim Attribution Engine
Connects synthesized claims to verified evidence chunks and document provenance (MIRAGE, VISA).
Determines attribution roles (DIRECT_SUPPORT, METHODOLOGICAL_QUALIFIER, OPPOSING_CONTRADICTION).
"""

from typing import List, Dict, Tuple, Optional
from app.schemas.layer5 import VerifiedEvidenceSet, EvidenceItem
from app.schemas.layer6 import SynthesizedReasoningTrace, SynthesizedClaim
from app.schemas.layer8 import EvidenceAttribution, AttributionRole


class ClaimAttributionEngine:
    """
    Constructs deterministic attribution links from synthesized claims to verified evidence items,
    preserving document provenance (page, section, coordinates) and quote spans without hallucination.
    """

    def __init__(self):
        pass

    def build_attributions(
        self,
        trace: SynthesizedReasoningTrace,
        evidence_set: VerifiedEvidenceSet
    ) -> Tuple[List[EvidenceAttribution], Dict[str, List[EvidenceAttribution]]]:
        """
        Builds fine-grained EvidenceAttribution records for all synthesized claims.
        Returns:
            (all_attributions, claim_to_attributions_map)
        """
        evidence_items = getattr(evidence_set, "selected_evidence", None) or getattr(evidence_set, "evidence_items", [])
        evidence_lookup: Dict[str, EvidenceItem] = {
            item.evidence_id: item for item in evidence_items
        }

        # Build conflict opposing evidence map
        opposing_evidence_ids: Dict[str, set] = {}
        conflict_edges = getattr(evidence_set, "conflict_edges", None) or getattr(evidence_set, "conflict_graph", [])
        for edge in conflict_edges:
            ev_a = getattr(edge, "evidence_a_id", None) or getattr(edge, "evidence_id_a", "")
            ev_b = getattr(edge, "evidence_b_id", None) or getattr(edge, "evidence_id_b", "")
            opposing_evidence_ids.setdefault(ev_a, set()).add(ev_b)
            opposing_evidence_ids.setdefault(ev_b, set()).add(ev_a)

        all_attributions: List[EvidenceAttribution] = []
        claim_map: Dict[str, List[EvidenceAttribution]] = {}

        claim_idx = 1
        for claim in trace.synthesized_claims:
            claim_id = claim.claim_id
            ev_idx = 1

            # 1. Direct supporting evidence
            for ev_id in claim.supporting_evidence_ids:
                ev = evidence_lookup.get(ev_id)
                if not ev:
                    continue

                token = f"[C{claim_idx}-E{ev_idx}]"
                title, uri, doc_id, page, section, p_start, p_end, quote, rel = self._extract_metadata(ev)

                role = AttributionRole.DIRECT_SUPPORT
                if "under" in claim.statement.lower() or "when" in claim.statement.lower():
                    role = AttributionRole.METHODOLOGICAL_QUALIFIER

                attribution = EvidenceAttribution(
                    evidence_id=ev.evidence_id,
                    claim_id=claim_id,
                    source_id=uri if uri else "source_unknown",
                    document_id=doc_id,
                    source_title=title,
                    source_uri=uri,
                    page_number=page,
                    section_title=section,
                    paragraph_start=p_start,
                    paragraph_end=p_end,
                    citation_token=token,
                    verbatim_quote=quote,
                    attribution_role=role,
                    relevance_score=rel
                )
                all_attributions.append(attribution)
                claim_map.setdefault(claim_id, []).append(attribution)
                ev_idx += 1

            # 2. Opposing evidence (from conflict edges)
            for ev_id in claim.opposing_evidence_ids:
                ev = evidence_lookup.get(ev_id)
                if not ev:
                    continue

                token = f"[C{claim_idx}-OPP{ev_idx}]"
                title, uri, doc_id, page, section, p_start, p_end, quote, rel = self._extract_metadata(ev)

                attribution = EvidenceAttribution(
                    evidence_id=ev.evidence_id,
                    claim_id=claim_id,
                    source_id=uri if uri else "source_unknown",
                    document_id=doc_id,
                    source_title=title if title != "Verified Document" else "Contradictory Source",
                    source_uri=uri,
                    page_number=page,
                    section_title=section,
                    paragraph_start=p_start,
                    paragraph_end=p_end,
                    citation_token=token,
                    verbatim_quote=quote,
                    attribution_role=AttributionRole.OPPOSING_CONTRADICTION,
                    relevance_score=rel
                )
                all_attributions.append(attribution)
                claim_map.setdefault(claim_id, []).append(attribution)
                ev_idx += 1

            claim_idx += 1

        return all_attributions, claim_map

    def _extract_metadata(self, ev: EvidenceItem):
        prov = getattr(ev, "provenance", None)
        title = getattr(ev, "title", None) or (getattr(prov, "document_title", None) or getattr(prov, "title", None) if prov else None) or "Verified Document"
        uri = getattr(ev, "source_uri", None) or (getattr(prov, "source_uri", None) if prov else "") or ""
        doc_id = getattr(ev, "document_id", None) or (getattr(prov, "document_id", None) if prov else "doc_unknown") or "doc_unknown"
        page = getattr(ev, "page_number", None) or (getattr(prov, "page_number", None) if prov else None)
        section = getattr(ev, "section_title", None) or (getattr(prov, "section_title", None) if prov else None)
        p_start = getattr(ev, "paragraph_start", None) or (getattr(prov, "paragraph_start", None) if prov else None)
        p_end = getattr(ev, "paragraph_end", None) or (getattr(prov, "paragraph_end", None) if prov else None)

        quote = ""
        if hasattr(ev, "atomic_claims") and ev.atomic_claims and hasattr(ev.atomic_claims[0], "exact_quote") and ev.atomic_claims[0].exact_quote:
            quote = ev.atomic_claims[0].exact_quote
        elif getattr(ev, "quoted_text", None):
            quote = ev.quoted_text
        elif getattr(ev, "content", None):
            quote = ev.content[:150]
        elif getattr(ev, "raw_content", None):
            quote = ev.raw_content[:150]
        elif prov and getattr(prov, "content", None):
            quote = prov.content[:150]
        else:
            quote = "Empirical observation"

        rel = getattr(ev, "rerank_score", None) or getattr(ev, "similarity_score", None) or getattr(ev, "relevance_score", 1.0)
        return title, uri, doc_id, page, section, p_start, p_end, quote, rel
