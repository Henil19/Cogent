"""
Sub-Module 5.5: Contradiction Detection & Conflict Graph
Research basis:
- Yuan et al. (ConfRAG, ACL 2026): Reasoning over Conflicting Web References
- Ge et al. (CONFACT, IJCAI 2025): Resolving Conflicting Evidence without Winner Selection
- Hwang et al. (RA-RAG, EMNLP 2025): Exposing Source Reliability & Conflict Metadata
- Jeon & Lee (GraphCheck, EMNLP 2025): Multipath Entity-Relationship Conflict Paths

Detects pairwise contradictions between claims and builds an explicit conflict graph:
    G_conflict = (V_evidence, E_contradiction)

CRITICAL INVARIANT: Zero Winner Forcing. Layer 5 NEVER deletes a conflicting claim or
arbitrarily picks a winner. Both perspectives are mapped with their provenance attributes
and deferred to Layer 6 (Reasoning) and Layer 7 (Trust Intelligence).
"""

import re
import uuid
import logging
from typing import Dict, List, Optional, Tuple, Set

from app.schemas.layer5 import (
    EvidenceItem,
    AtomicClaim,
    ConflictEdge,
    ConflictSeverity,
)

logger = logging.getLogger(__name__)

OPPOSING_POLARITY_PAIRS = [
    ("outperform", "underperform"),
    ("improv", "degrad"),
    ("reduc", "increas"),
    ("faster", "slower"),
    ("superior", "inferior"),
    ("higher", "lower"),
    ("linear", "quadratic"),
    ("scalable", "unscalable")
]


STOP_WORDS = {
    "the", "and", "a", "an", "in", "to", "of", "for", "on", "with", "at", "by", "from",
    "was", "were", "is", "are", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "it", "its", "that", "this", "these", "those", "reports", "reported", "held",
    "final", "finals", "match", "matches", "tournament", "cup", "league", "champions", "uefa",
    "versus", "vs", "against", "after", "before", "during", "while", "whereas", "also", "both",
    "source", "sources", "according", "primary", "document", "article", "page", "news", "retained",
    "over", "under", "into", "through", "between", "out"
}


class ConflictGraphBuilder:
    """
    Constructs the contradiction graph between opposing evidence items.
    """

    def build_conflict_graph(
        self,
        evidence_items: List[EvidenceItem]
    ) -> Tuple[List[ConflictEdge], bool]:
        """
        Scan all pairwise claims across evidence items and construct conflict edges.
        
        Returns:
            Tuple of (conflict_edges, has_conflicts)
        """
        if len(evidence_items) < 2:
            return [], False

        raw_conflict_edges: List[ConflictEdge] = []

        # Compare pairs of evidence items
        for i in range(len(evidence_items)):
            item_a = evidence_items[i]
            for j in range(i + 1, len(evidence_items)):
                item_b = evidence_items[j]

                # Don't compare evidence items from the exact same document
                if item_a.document_id == item_b.document_id:
                    continue

                edges = self._detect_pairwise_conflicts(item_a, item_b)
                for edge in edges:
                    raw_conflict_edges.append(edge)

        # Deduplicate and cap to at most 5 top distinct conflicts to avoid spam
        conflict_edges: List[ConflictEdge] = []
        seen_keys = set()
        for edge in raw_conflict_edges:
            key = (edge.conflicting_aspect, edge.evidence_a_id, edge.evidence_b_id)
            if key not in seen_keys:
                seen_keys.add(key)
                conflict_edges.append(edge)
                for item in evidence_items:
                    if item.evidence_id in (edge.evidence_a_id, edge.evidence_b_id):
                        if edge.conflict_id not in item.conflict_group_ids:
                            item.conflict_group_ids.append(edge.conflict_id)
            if len(conflict_edges) >= 5:
                break

        has_conflicts = len(conflict_edges) > 0
        logger.info(
            f"Evaluated {len(evidence_items)} evidence items. "
            f"Detected {len(conflict_edges)} contradiction edges across sources."
        )
        return conflict_edges, has_conflicts

    def _detect_pairwise_conflicts(
        self,
        item_a: EvidenceItem,
        item_b: EvidenceItem
    ) -> List[ConflictEdge]:
        """Examine atomic claims of two evidence items for mutually exclusive assertions."""
        edges: List[ConflictEdge] = []

        if not item_a.atomic_claims:
            item_a.atomic_claims = [self._synthetic_claim(item_a)]
        if not item_b.atomic_claims:
            item_b.atomic_claims = [self._synthetic_claim(item_b)]

        claims_a = item_a.atomic_claims
        claims_b = item_b.atomic_claims

        for ca in claims_a:
            for cb in claims_b:
                conflict = self._evaluate_claim_contradiction(ca, cb, item_a, item_b)
                if conflict:
                    edges.append(conflict)

        return edges

    def _evaluate_claim_contradiction(
        self,
        ca: AtomicClaim,
        cb: AtomicClaim,
        item_a: EvidenceItem,
        item_b: EvidenceItem
    ) -> Optional[ConflictEdge]:
        """Check if claim A and claim B assert contradictory facts on the same entity."""
        text_a = ca.claim_text.lower()
        text_b = cb.claim_text.lower()

        # 1. Check shared entity / subject anchor (filtering out stop words and numbers)
        words_a = {w for w in re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", text_a) if w not in STOP_WORDS and len(w) > 2 and not w.isdigit()}
        words_b = {w for w in re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", text_b) if w not in STOP_WORDS and len(w) > 2 and not w.isdigit()}
        common_words = words_a.intersection(words_b)

        # Must share at least 2 key semantic content terms (e.g. 'mamba', 'latency')
        if len(common_words) < 2:
            return None

        # 2. Check Direct Numeric Contradiction with matching units (e.g. 92% vs 88%, 15ms vs 45ms)
        # Plain integers (dates, minutes, scorelines) without shared units are NOT metric clashes
        unit_pat = r"\b(\d+(?:\.\d+)?)\s*(%|ms|s|x|gb|mb|ghz|fps|kb|tflops|tokens/s|tok/s|tokens per second)(?![a-zA-Z0-9])"
        raw_units_a = re.findall(unit_pat, text_a)
        raw_units_b = re.findall(unit_pat, text_b)

        if raw_units_a and raw_units_b:
            for val_a, unit_a in raw_units_a:
                for val_b, unit_b in raw_units_b:
                    if unit_a == unit_b and val_a != val_b:
                        aspect = list(common_words)[0] if common_words else f"metric_{unit_a}"
                        cid = f"cfl_{uuid.uuid4().hex[:8]}"
                        return ConflictEdge(
                            conflict_id=cid,
                            claim_a_id=ca.claim_id,
                            claim_b_id=cb.claim_id,
                            evidence_a_id=item_a.evidence_id,
                            evidence_b_id=item_b.evidence_id,
                            conflict_description=(
                                f"Numerical discrepancy on '{aspect}': "
                                f"'{ca.claim_text}' reports {val_a}{unit_a} while '{cb.claim_text}' reports {val_b}{unit_b}"
                            ),
                            severity=ConflictSeverity.DIRECT_FACTUAL,
                            conflicting_aspect=aspect
                        )

        # 3. Check Opposing Polarity (e.g. 'reduces' vs 'increases', 'outperforms' vs 'underperforms')
        for pos, neg in OPPOSING_POLARITY_PAIRS:
            if (pos in text_a and neg in text_b) or (neg in text_a and pos in text_b):
                aspect = list(common_words)[0]
                cid = f"cfl_{uuid.uuid4().hex[:8]}"
                return ConflictEdge(
                    conflict_id=cid,
                    claim_a_id=ca.claim_id,
                    claim_b_id=cb.claim_id,
                    evidence_a_id=item_a.evidence_id,
                    evidence_b_id=item_b.evidence_id,
                    conflict_description=(
                        f"Opposing polarity contradiction on '{aspect}': "
                        f"'{ca.claim_text}' opposes '{cb.claim_text}'"
                    ),
                    severity=ConflictSeverity.DIRECT_FACTUAL,
                    conflicting_aspect=aspect
                )

        # 4. Check Temporal Divergence (e.g. different publication years with conflicting claims)
        if item_a.publication_date and item_b.publication_date and item_a.publication_date[:4] != item_b.publication_date[:4]:
            if len(common_words) >= 3 and not words_a.issubset(words_b) and not words_b.issubset(words_a):
                cid = f"cfl_{uuid.uuid4().hex[:8]}"
                return ConflictEdge(
                    conflict_id=cid,
                    claim_a_id=ca.claim_id,
                    claim_b_id=cb.claim_id,
                    evidence_a_id=item_a.evidence_id,
                    evidence_b_id=item_b.evidence_id,
                    conflict_description=(
                        f"Temporal divergence between {item_a.publication_date[:4]} and {item_b.publication_date[:4]} "
                        f"regarding '{list(common_words)[0]}'"
                    ),
                    severity=ConflictSeverity.TEMPORAL_DIVERGENCE,
                    conflicting_aspect=list(common_words)[0]
                )

        return None

    def _synthetic_claim(self, item: EvidenceItem) -> AtomicClaim:
        """Create fallback claim representation if atomic claims were not pre-extracted."""
        return AtomicClaim(
            claim_id=f"clm_{item.chunk_id[:8]}_syn",
            parent_chunk_id=item.chunk_id,
            candidate_id=item.candidate_id,
            claim_text=item.content[:150],
            quote_span=item.content[:150],
            is_atomic=True
        )
