"""
Sub-Module 5.7: Layer 5 Pipeline Orchestrator
Connects Layer 4 RetrievedCandidateSet and Layer 2 KnowledgeRetrievalPlan.
Executes Cross-Encoder Re-Ranking, Atomic Claim Extraction, NLI Grounding,
4-Tier Deduplication, Contradiction Detection (Conflict Graph with Zero Winner Forcing),
and S2G-RAG Coverage & Set Selection.
Emits standardized VerifiedEvidenceSet strictly to Layer 6.
"""

import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from app.core.layer5.reranking.cross_encoder_reranker import CrossEncoderReranker
from app.core.layer5.claims.atomic_claim_extractor import AtomicClaimExtractor
from app.core.layer5.grounding.entailment_verifier import EntailmentVerifier
from app.core.layer5.deduplication.evidence_consolidator import EvidenceConsolidator
from app.core.layer5.conflicts.conflict_graph_builder import ConflictGraphBuilder
from app.core.layer5.coverage.coverage_selector import CoverageSelector

from app.schemas.layer2 import KnowledgeRetrievalPlan
from app.schemas.layer4 import RetrievedCandidateSet, RetrievedCandidate
from app.schemas.layer5 import (
    EvidenceItem,
    VerifiedEvidenceSet,
    GroundingStatus
)

logger = logging.getLogger(__name__)


class Layer5Pipeline:
    """
    Orchestrates evidence intelligence, factual grounding, and conflict graph mapping.
    """

    def __init__(
        self,
        reranker: Optional[CrossEncoderReranker] = None,
        claim_extractor: Optional[AtomicClaimExtractor] = None,
        verifier: Optional[EntailmentVerifier] = None,
        consolidator: Optional[EvidenceConsolidator] = None,
        conflict_builder: Optional[ConflictGraphBuilder] = None,
        coverage_selector: Optional[CoverageSelector] = None,
        use_mock: bool = False
    ):
        self.reranker = reranker or CrossEncoderReranker(use_mock=use_mock)
        self.claim_extractor = claim_extractor or AtomicClaimExtractor()
        self.verifier = verifier or EntailmentVerifier()
        self.consolidator = consolidator or EvidenceConsolidator()
        self.conflict_builder = conflict_builder or ConflictGraphBuilder()
        self.coverage_selector = coverage_selector or CoverageSelector()

    def execute(
        self,
        candidate_set: RetrievedCandidateSet,
        plan: KnowledgeRetrievalPlan,
        max_evidence: int = 10,
        rerank_threshold: float = 0.20
    ) -> VerifiedEvidenceSet:
        """
        Execute full Layer 5 evidence intelligence workflow.
        """
        start_time = time.time()
        candidates = candidate_set.all_candidates

        if not candidates:
            logger.warning("Layer 5 received empty candidate pool from Layer 4.")
            return VerifiedEvidenceSet(
                evidence_set_id=f"evset_{uuid.uuid4().hex[:12]}",
                plan_id=plan.plan_id,
                session_id=plan.session_id,
                selected_evidence=[],
                total_candidates_evaluated=0,
                selected_evidence_count=0,
                conflict_edges=[],
                has_conflicts=False,
                duplicate_groups=[],
                coverage_map={},
                overall_coverage_ratio=0.0,
                unresolved_information_gaps=["No candidates retrieved from Layer 4"],
                is_sufficient_for_reasoning=False,
                processing_time_ms=(time.time() - start_time) * 1000.0,
                created_at=datetime.now(timezone.utc).isoformat()
            )

        # 1. Cross-Encoder Re-Ranking (Sub-Module 5.1 - Alt et al. EACL 2026)
        query = plan.parent_query
        sub_query_map = {sq.id: sq.raw_sub_query for sq in plan.sub_queries} if plan.sub_queries else {}
        reranked_tuples = self.reranker.rerank(
            query=query,
            candidates=candidates,
            sub_queries=sub_query_map
        )

        # Survival selection: filter items below threshold, keeping at least 3
        filtered_tuples = [t for t in reranked_tuples if t[1] >= rerank_threshold]
        if len(filtered_tuples) < min(3, len(reranked_tuples)):
            filtered_tuples = reranked_tuples[:3]

        # 2. Atomic Claim Extraction & NLI Grounding (Sub-Modules 5.2 & 5.3)
        evidence_items: List[EvidenceItem] = []
        seen_chunk_ids: Set[str] = set()

        for cand, rerank_score, rank in filtered_tuples:
            if cand.chunk_id in seen_chunk_ids:
                continue
            seen_chunk_ids.add(cand.chunk_id)

            # Extract atomic claims with quality gating
            claims = self.claim_extractor.extract_claims(cand)

            # Ground each claim against candidate content
            grounded_claims = []
            grounding_statuses = []
            for claim in claims:
                verified_claim = self.verifier.verify_claim(claim, cand.content)
                grounded_claims.append(verified_claim)
                grounding_statuses.append(verified_claim.grounding_status)

            # Aggregate chunk overall grounding
            if GroundingStatus.CONTRADICTION in grounding_statuses:
                overall = GroundingStatus.CONTRADICTION
            elif GroundingStatus.ENTAILMENT in grounding_statuses:
                overall = GroundingStatus.ENTAILMENT
            else:
                overall = GroundingStatus.NEUTRAL

            evidence_id = f"ev_{cand.chunk_id[:10]}_{uuid.uuid4().hex[:4]}"
            item = EvidenceItem(
                evidence_id=evidence_id,
                candidate_id=cand.candidate_id,
                chunk_id=cand.chunk_id,
                document_id=cand.document_id,
                sub_query_id=cand.sub_query_id,
                content=cand.content,
                title=cand.title,
                source_uri=cand.source_uri,
                source_type=cand.source_type,
                similarity_score=cand.similarity_score,
                rerank_score=rerank_score,
                atomic_claims=grounded_claims,
                overall_grounding=overall,
                duplicate_group_id=None,
                conflict_group_ids=[],
                page_number=cand.page_number,
                section_title=cand.section_title,
                paragraph_start=cand.paragraph_start,
                paragraph_end=cand.paragraph_end,
                has_table=cand.has_table,
                has_equation=cand.has_equation,
                document_hash=cand.document_hash,
                content_hash=cand.content_hash,
                retrieved_at=cand.retrieved_at,
                author=cand.author,
                publication_date=cand.publication_date
            )
            evidence_items.append(item)

        # 3. Deduplication & Evidence Consolidation (Sub-Module 5.4)
        consolidated_items, duplicate_groups = self.consolidator.consolidate(evidence_items)

        # 4. Contradiction Detection & Conflict Graph (Sub-Module 5.5 - Zero Winner Forcing)
        conflict_edges, has_conflicts = self.conflict_builder.build_conflict_graph(consolidated_items)

        # 5. Evidence Coverage, Sufficiency & Set Selection (Sub-Module 5.6)
        (
            selected_evidence,
            coverage_map,
            unresolved_gaps,
            coverage_ratio,
            is_sufficient
        ) = self.coverage_selector.evaluate_coverage_and_select(
            candidate_items=consolidated_items,
            plan=plan,
            conflict_edges=conflict_edges,
            max_evidence=max_evidence
        )

        total_latency_ms = (time.time() - start_time) * 1000.0

        evidence_set = VerifiedEvidenceSet(
            evidence_set_id=f"evset_{uuid.uuid4().hex[:12]}",
            plan_id=plan.plan_id,
            session_id=plan.session_id,
            selected_evidence=selected_evidence,
            total_candidates_evaluated=len(candidates),
            selected_evidence_count=len(selected_evidence),
            conflict_edges=conflict_edges,
            has_conflicts=has_conflicts,
            duplicate_groups=duplicate_groups,
            coverage_map=coverage_map,
            overall_coverage_ratio=coverage_ratio,
            unresolved_information_gaps=unresolved_gaps,
            is_sufficient_for_reasoning=is_sufficient,
            processing_time_ms=round(total_latency_ms, 2),
            created_at=datetime.now(timezone.utc).isoformat()
        )

        logger.info(
            f"Layer 5 completed for plan {plan.plan_id}: "
            f"{evidence_set.selected_evidence_count} evidence items selected from {len(candidates)} candidates. "
            f"Conflicts: {len(conflict_edges)}, Duplicates: {len(duplicate_groups)}, Gaps: {len(unresolved_gaps)} "
            f"in {evidence_set.processing_time_ms:.1f}ms."
        )

        return evidence_set
