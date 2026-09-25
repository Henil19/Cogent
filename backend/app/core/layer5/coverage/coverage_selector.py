"""
Sub-Module 5.6: Evidence Coverage, Sufficiency & Set Selection
Research basis:
- Lee et al. (SetR, ACL 2025): Set-Wise Collective Passage Selection for Multi-Hop RAG
- S2G-RAG (ACL 2026): Structured Sufficiency and Gap Judging for Retrieval Gaps
- DRUID (ACL 2025): Context Utilization & Sufficiency Verification

Performs collective set selection to maximize coverage over Layer 2's InformationNeedProfile.
Diagnoses missing information dimensions (S2G-RAG) and builds the final structured evidence set.
"""

import logging
from typing import Dict, List, Set, Tuple

from app.schemas.layer2 import KnowledgeRetrievalPlan
from app.schemas.layer5 import EvidenceItem, CoverageDimension, ConflictEdge

logger = logging.getLogger(__name__)


class CoverageSelector:
    """
    Sub-modular evidence set selector with S2G-RAG structured gap diagnostics.
    """

    def __init__(self, sufficiency_threshold: float = 0.60):
        self.sufficiency_threshold = sufficiency_threshold

    def evaluate_coverage_and_select(
        self,
        candidate_items: List[EvidenceItem],
        plan: KnowledgeRetrievalPlan,
        conflict_edges: List[ConflictEdge],
        max_evidence: int = 10
    ) -> Tuple[List[EvidenceItem], Dict[str, CoverageDimension], List[str], float, bool]:
        """
        Evaluate information coverage and select the optimal non-redundant evidence set.
        
        Returns:
            Tuple of:
            - selected_evidence: List[EvidenceItem]
            - coverage_map: Dict[str, CoverageDimension]
            - unresolved_gaps: List[str]
            - overall_coverage_ratio: float
            - is_sufficient: bool
        """
        # 1. Gather target dimensions from Layer 2 plan
        target_dimensions: List[str] = []
        if plan.information_need:
            target_dimensions.extend(plan.information_need.unknown_targets)
            target_dimensions.extend(plan.information_need.evaluation_criteria)

        # If plan had no explicit targets, fall back to sub-query descriptions
        if not target_dimensions:
            target_dimensions = [sq.raw_sub_query for sq in plan.sub_queries]

        if not target_dimensions:
            target_dimensions = ["core_information_need"]

        # Deduplicate dimension names
        dim_list = list(dict.fromkeys(target_dimensions))

        # 2. Build coverage map across all candidate items
        coverage_map: Dict[str, CoverageDimension] = {}
        covered_count = 0

        import re

        for dim in dim_list:
            dim_tokens = set(re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", dim.lower()))
            covering_ids: List[str] = []

            for item in candidate_items:
                item_tokens = set(re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", f"{item.title} {item.content}".lower()))
                # Check overlap
                overlap = len(dim_tokens.intersection(item_tokens))
                if overlap >= 1 or (len(dim_tokens) > 2 and overlap >= 2):
                    covering_ids.append(item.evidence_id)

            is_cov = len(covering_ids) > 0
            if is_cov:
                covered_count += 1
                conf = min(1.0, 0.5 + 0.15 * len(covering_ids))
            else:
                conf = 0.0

            coverage_map[dim] = CoverageDimension(
                dimension_name=dim,
                is_covered=is_cov,
                covering_evidence_ids=covering_ids,
                confidence_score=round(conf, 4)
            )

        # 3. S2G-RAG Gap Analysis (Structured missing dimensions)
        unresolved_gaps: List[str] = [
            f"Missing evidence for target dimension: '{dim}'"
            for dim, cov in coverage_map.items()
            if not cov.is_covered
        ]

        overall_ratio = covered_count / len(dim_list) if dim_list else 1.0
        is_sufficient = overall_ratio >= self.sufficiency_threshold

        # 4. SetR Collective Set Selection
        # Prioritize:
        # A. Items that participate in contradictions (Zero Winner Forcing: never drop conflicts!)
        # B. Items that cover previously uncovered dimensions
        # C. Items with highest cross-encoder rerank score
        conflict_evidence_ids: Set[str] = set()
        for edge in conflict_edges:
            conflict_evidence_ids.add(edge.evidence_a_id)
            conflict_evidence_ids.add(edge.evidence_b_id)

        selected: List[EvidenceItem] = []
        covered_by_selected: Set[str] = set()

        # Sort candidate items: conflict participants first, then by rerank score descending
        sorted_candidates = sorted(
            candidate_items,
            key=lambda x: (x.evidence_id in conflict_evidence_ids, x.rerank_score),
            reverse=True
        )

        # Multi-Source Diversity Budgeting (Chen et al. ACL 2024; Izacard & Grave EACL 2021)
        # Prevents single-document/monoculture domination of the evidence set.
        # High authority / highly reliable sources can contribute up to 2 chunks.
        # Standard web / secondary sources can contribute at most 1 chunk.
        doc_selection_counts: Dict[str, int] = {}

        def get_source_quota(ev_item: EvidenceItem) -> int:
            uri_lower = (ev_item.source_uri or "").lower()
            is_peer_reviewed_or_primary = any(
                dom in uri_lower for dom in [
                    "arxiv.org", "nature.com", "science.org", "ncbi.nlm.nih.gov",
                    "openreview.net", "proceedings.mlr.press", "jmlr.org", "acm.org", "ieee.org"
                ]
            )
            # High authority: strong rerank score (>= 0.70) or verified academic domain
            if ev_item.rerank_score >= 0.70 or is_peer_reviewed_or_primary:
                return 2
            return 1

        # Phase 1: Diversified selection enforcing stratified source quotas
        for item in sorted_candidates:
            if len(selected) >= max_evidence:
                break

            clean_t = re.sub(r"\[[\d\.\sA-Za-z]+\]", "", item.title or "")
            clean_t = re.sub(r"[^\w\s]", "", clean_t.lower()).strip()
            words = [w for w in clean_t.split() if len(w) > 2]
            doc_key = " ".join(words[:6]) if words else (item.document_id or item.source_uri or "default")
            quota = get_source_quota(item)
            current_count = doc_selection_counts.get(doc_key, 0)

            # Strictly enforce source quota unless this specific item is an indispensable conflict participant
            if current_count >= quota and item.evidence_id not in conflict_evidence_ids:
                continue

            # Check what dimensions this item contributes
            item_tokens = set(re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", f"{item.title} {item.content}".lower()))
            contributed_new_dim = False
            for dim in dim_list:
                if dim not in covered_by_selected:
                    dim_tokens = set(re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", dim.lower()))
                    if dim_tokens.intersection(item_tokens):
                        covered_by_selected.add(dim)
                        contributed_new_dim = True

            # Keep if item is part of conflict, contributes new dimension, or slots remain
            if (
                item.evidence_id in conflict_evidence_ids
                or contributed_new_dim
                or len(selected) < max_evidence
            ):
                selected.append(item)
                doc_selection_counts[doc_key] = current_count + 1

        # Phase 2: If distinct sources were fewer than minimum target and slots remain, backfill candidates
        if len(selected) < min(max_evidence, 3):
            for item in sorted_candidates:
                if len(selected) >= max_evidence:
                    break
                if item not in selected:
                    selected.append(item)

        # Fallback if selection was overly strict
        if not selected and candidate_items:
            selected = candidate_items[:max_evidence]

        logger.info(
            f"Coverage evaluated across {len(dim_list)} dimensions ({covered_count}/{len(dim_list)} covered). "
            f"Selected {len(selected)} high-utility evidence items. Gaps: {len(unresolved_gaps)}."
        )

        return selected, coverage_map, unresolved_gaps, round(overall_ratio, 4), is_sufficient
