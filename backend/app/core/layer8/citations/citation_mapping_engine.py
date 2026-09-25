"""
Sub-Module 8.3: Evidence & Citation Mapping Engine
Compiles standardized citation tokens ([C{i}-E{j}]) and maintains a citation lookup map
with complete TROVE provenance coordinates and verbatim quotes for Layer 9.
"""

from typing import List, Dict
from app.schemas.layer8 import EvidenceAttribution


class CitationMappingEngine:
    """
    Manages citation tokens and builds citation maps for frontend attribution chips and popovers.
    """

    def __init__(self):
        pass

    def build_citation_map(
        self,
        attributions: List[EvidenceAttribution]
    ) -> Dict[str, EvidenceAttribution]:
        """
        Builds a dictionary mapping citation tokens to their full EvidenceAttribution metadata.
        """
        citation_map: Dict[str, EvidenceAttribution] = {}
        for attr in attributions:
            citation_map[attr.citation_token] = attr
        return citation_map

    def get_claim_citations(
        self,
        claim_id: str,
        attributions: List[EvidenceAttribution]
    ) -> List[str]:
        """
        Returns all citation tokens associated with a given claim.
        """
        tokens: List[str] = []
        for attr in attributions:
            if attr.claim_id == claim_id:
                tokens.append(attr.citation_token)
        return tokens
