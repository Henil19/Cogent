"""
Sub-Module 5.4: Evidence Deduplication & Consolidation
Research basis:
- Alt et al. (EACL 2026): User-Centric Evidence Ranking & Minimizing Redundancy
- Verma et al. (ReflectiveRAG, EACL 2026): Contrastive Noise Removal & Duplicate Clustering
- DF-RAG (EACL 2026): Query-Aware Diversity

Prevents evidence inflation and echo-chamber consensus by detecting duplicate evidence
across 4 tiers: EXACT, NEAR, SEMANTIC, and OVERLAPPING_CHUNK.
Consolidates duplicates into an EvidenceGroup with a designated canonical primary.
"""

import uuid
import logging
from typing import Dict, List, Set, Tuple, Optional

from app.schemas.layer5 import EvidenceItem, EvidenceGroup, DuplicateType

logger = logging.getLogger(__name__)


import re

def tokenize_clean(text: str) -> Set[str]:
    """Clean alphanumeric tokenization without punctuation."""
    return set(re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", text.lower()))


def token_jaccard(text1: str, text2: str) -> float:
    """Calculate token-level Jaccard similarity between two texts."""
    tokens1 = tokenize_clean(text1)
    tokens2 = tokenize_clean(text2)
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    return intersection / union if union > 0 else 0.0


def token_containment(text1: str, text2: str) -> float:
    """Calculate asymmetric containment ratio between shorter and longer texts."""
    tokens1 = tokenize_clean(text1)
    tokens2 = tokenize_clean(text2)
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1.intersection(tokens2))
    min_len = min(len(tokens1), len(tokens2))
    return intersection / min_len if min_len > 0 else 0.0


class EvidenceConsolidator:
    """
    Groups and deduplicates evidence items to prevent evidence inflation.
    """

    def __init__(self, near_threshold: float = 0.85, semantic_threshold: float = 0.90):
        self.near_threshold = near_threshold
        self.semantic_threshold = semantic_threshold

    def consolidate(self, evidence_items: List[EvidenceItem]) -> Tuple[List[EvidenceItem], List[EvidenceGroup]]:
        """
        Detect duplicates among evidence items and consolidate into groups.
        
        Returns:
            Tuple of (retained_evidence_items, duplicate_groups)
        """
        if not evidence_items:
            return [], []

        duplicate_groups: List[EvidenceGroup] = []
        visited_ids: Set[str] = set()
        retained_items: List[EvidenceItem] = []

        for i, item_a in enumerate(evidence_items):
            if item_a.evidence_id in visited_ids:
                continue

            current_group_members = [item_a.evidence_id]
            detected_type = None

            for j in range(i + 1, len(evidence_items)):
                item_b = evidence_items[j]
                if item_b.evidence_id in visited_ids:
                    continue

                dup_type = self._check_duplicate(item_a, item_b)
                if dup_type:
                    current_group_members.append(item_b.evidence_id)
                    visited_ids.add(item_b.evidence_id)
                    if detected_type is None:
                        detected_type = dup_type

            if len(current_group_members) > 1:
                group_id = f"grp_{uuid.uuid4().hex[:8]}"
                # Designate canonical primary: highest rerank score
                group_items = [e for e in evidence_items if e.evidence_id in current_group_members]
                group_items.sort(key=lambda x: x.rerank_score, reverse=True)
                canonical_item = group_items[0]

                # Tag all members
                for m_item in group_items:
                    m_item.duplicate_group_id = group_id

                duplicate_groups.append(
                    EvidenceGroup(
                        group_id=group_id,
                        canonical_evidence_id=canonical_item.evidence_id,
                        member_evidence_ids=current_group_members,
                        duplicate_type=detected_type or DuplicateType.NEAR,
                        claim_summary=canonical_item.title
                    )
                )
                retained_items.append(canonical_item)
                visited_ids.add(item_a.evidence_id)
            else:
                retained_items.append(item_a)
                visited_ids.add(item_a.evidence_id)

        logger.info(
            f"Consolidated {len(evidence_items)} evidence items into {len(retained_items)} unique items "
            f"and {len(duplicate_groups)} duplicate groups."
        )
        return retained_items, duplicate_groups

    def _check_duplicate(self, a: EvidenceItem, b: EvidenceItem) -> Optional[DuplicateType]:
        """Check duplicate relationship between two evidence items."""
        # 1. EXACT hash match
        if a.content_hash == b.content_hash:
            return DuplicateType.EXACT

        # 2. OVERLAPPING_CHUNK match
        if a.document_id == b.document_id:
            if (
                a.paragraph_start is not None and a.paragraph_end is not None and
                b.paragraph_start is not None and b.paragraph_end is not None
            ):
                # Check overlap: max(start) <= min(end)
                if max(a.paragraph_start, b.paragraph_start) <= min(a.paragraph_end, b.paragraph_end):
                    return DuplicateType.OVERLAPPING_CHUNK

        # Check if items contain conflicting numbers - conflicting claims CANNOT be duplicates!
        nums_a = set(re.findall(r"\b\d+(?:\.\d+)?\%?\b", a.content.lower()))
        nums_b = set(re.findall(r"\b\d+(?:\.\d+)?\%?\b", b.content.lower()))
        if nums_a and nums_b and not nums_a.intersection(nums_b):
            return None  # Opposing numerical assertions are candidates for contradiction, not duplicate

        # 3. NEAR duplicate (token Jaccard or containment)
        jaccard = token_jaccard(a.content, b.content)
        containment = token_containment(a.content, b.content)
        if jaccard >= self.near_threshold or containment >= 0.85:
            return DuplicateType.NEAR

        # 4. SEMANTIC duplicate (compare atomic claims)
        if a.atomic_claims and b.atomic_claims:
            a_claim_texts = " ".join([c.claim_text for c in a.atomic_claims])
            b_claim_texts = " ".join([c.claim_text for c in b.atomic_claims])
            claim_jaccard = token_jaccard(a_claim_texts, b_claim_texts)
            claim_cont = token_containment(a_claim_texts, b_claim_texts)
            if claim_jaccard >= self.semantic_threshold or claim_cont >= 0.85:
                return DuplicateType.SEMANTIC

        return None
