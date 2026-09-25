"""
Sub-Module 2.5: Dynamic Source Router & Plan Assembler
Research Basis:
- Adaptive-RAG (NAACL 2024): Complexity-driven strategy selection
- RealRoute (2026): Dynamic query routing across heterogeneous knowledge repositories
Routes sub-queries to LOCAL_DOCS, LIVE_WEB, or HYBRID and compiles KnowledgeRetrievalPlan.
"""

import re
import uuid
from typing import List, Dict, Any, Tuple
from app.schemas.layer1 import StructuredUserInput, IntentCategory
from app.schemas.layer2 import (
    SubQueryPlan,
    InformationNeedProfile,
    CoverageReport,
    KnowledgeRetrievalPlan,
    SourceTarget
)
from app.core.llm_client import LLMClient


class SourceRouter:
    """Routes sub-queries to local corpus vs live web search and assembles retrieval plan."""

    # Cues that suggest live external web search (Adaptive-RAG / RealRoute)
    WEB_INDICATORS = [
        "recent", "latest", "2024", "2025", "2026", "news", "today", "released", "announced",
        "arxiv", "preprint", "github", "trending", "current", "state of the art", "sota",
        "this year", "winner", "who won", "champions league", "final", "score", "game",
        "match", "when did", "price", "stock", "what happened", "who is", "tell me about"
    ]

    # Cues that suggest internal/local private corpus
    LOCAL_INDICATORS = [
        "uploaded", "document", "pdf", "file", "internal", "our", "my", "codebase",
        "repository", "dataset", "handbook", "manual", "report", "confidential"
    ]

    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient()

    def route_and_assemble(
        self,
        user_input: StructuredUserInput,
        info_need: InformationNeedProfile,
        coverage: CoverageReport,
        subqueries: List[SubQueryPlan],
        execution_stages: List[List[str]],
        start_time_ms: float,
        end_time_ms: float
    ) -> KnowledgeRetrievalPlan:
        """Route each sub-query and assemble the complete KnowledgeRetrievalPlan."""
        # Route each sub-query
        for sq in subqueries:
            target, reason = self._determine_source(sq, user_input)
            sq.target_source = target
            sq.routing_reason = reason

        # Determine overall target sources
        active_sources = sorted(list(set(sq.target_source for sq in subqueries)), key=lambda x: x.value)

        # Multi-stage verification
        is_parallel = any(len(stage) > 1 for stage in execution_stages)

        plan = KnowledgeRetrievalPlan(
            plan_id=f"plan_{uuid.uuid4().hex[:12]}",
            session_id=user_input.session_id,
            parent_query=user_input.resolved_query,
            intent=user_input.intent,
            query_type=user_input.query_type,
            information_need=info_need,
            coverage=coverage,
            sub_queries=subqueries,
            execution_stages=execution_stages,
            is_parallel_executable=is_parallel,
            total_stages=len(execution_stages),
            target_sources_summary=active_sources,
            global_constraints=user_input.constraints,
            planning_time_ms=round(end_time_ms - start_time_ms, 2)
        )
        return plan

    def _determine_source(self, sq: SubQueryPlan, user_input: StructuredUserInput) -> Tuple[SourceTarget, str]:
        """Classify optimal knowledge source using Adaptive-RAG & RealRoute heuristics or LLM."""
        combined_text = f"{sq.raw_sub_query} {sq.description} {user_input.resolved_query} {' '.join(user_input.constraints)}".lower()

        has_web_cue = any(re.search(r"\b" + re.escape(cue) + r"\b", combined_text) for cue in self.WEB_INDICATORS)
        has_local_cue = any(re.search(r"\b" + re.escape(cue) + r"\b", combined_text) for cue in self.LOCAL_INDICATORS)

        # If both local corpus and external web cues are present
        if has_web_cue and has_local_cue:
            return SourceTarget.HYBRID, "Cross-domain verification between internal document corpus and external web search."

        # If explicit local indicators are present
        if has_local_cue:
            return SourceTarget.LOCAL_DOCS, "Sub-query specifically references user documents or internal corpus."

        # If recent temporal horizons, preprints, or external benchmarks are requested
        if has_web_cue:
            return SourceTarget.LIVE_WEB, "Sub-query requires real-time, external web, or recent (2025-2026) preprint data."

        # Comparative research across entities benefits from hybrid retrieval
        if user_input.intent in [IntentCategory.COMPARATIVE, IntentCategory.SYNTHESIS]:
            return SourceTarget.HYBRID, "Comparative research benefits from cross-referencing local literature and live web benchmarks."

        return SourceTarget.HYBRID, "Defaulting to hybrid cross-retrieval across domain documents and live web knowledge."

