"""
Sub-Module 2.2: Coverage-Supervised Query Decomposer
Research Basis:
- Q-DREAM QDM (ACL 2025): Question Decomposition Module
- AtomRAG (2026): Atomic criteria preventing over-fragmentation
- PROGRESS (2026): Coverage supervision metric ensuring no entity or constraint is omitted
"""

import re
from typing import List, Dict, Any, Tuple
from app.schemas.layer1 import StructuredUserInput, IntentCategory, QueryTypeCategory
from app.schemas.layer2 import InformationNeedProfile, SubQueryPlan, CoverageReport, OutputExpectation
from app.core.llm_client import LLMClient


class QueryDecomposer:
    """Decomposes queries into atomic sub-questions with PROGRESS coverage guarantees."""

    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient()

    def decompose(
        self,
        user_input: StructuredUserInput,
        info_need: InformationNeedProfile
    ) -> Tuple[List[SubQueryPlan], CoverageReport]:
        """Decompose into sub-queries and compute PROGRESS coverage."""
        query = user_input.resolved_query

        # Check AtomRAG atomic criteria first:
        # If single-hop and <= 1 entity and no comparative markers, it is already atomic
        if self._is_already_atomic(user_input):
            single_subquery = SubQueryPlan(
                id="sq_1",
                description="Atomic primary fact retrieval",
                raw_sub_query=query,
                depends_on=[],
                stage_index=0,
                expected_output_type=OutputExpectation.FACT,
                is_atomic=True
            )
            coverage = CoverageReport(
                is_fully_covered=True,
                coverage_score=1.0,
                covered_elements=list(user_input.entities),
                missing_elements=[]
            )
            return [single_subquery], coverage

        # Use high-precision deterministic decomposition directly (<1ms)
        subqueries = self._decompose_deterministic(user_input, info_need)

        # PROGRESS (2026) Coverage Verification Gate
        coverage = self._verify_and_enforce_coverage(user_input, subqueries)
        return subqueries, coverage

    def _is_already_atomic(self, user_input: StructuredUserInput) -> bool:
        """AtomRAG criteria: single-hop, factual, and no comparative conjunctions."""
        if user_input.query_type == QueryTypeCategory.SINGLE_HOP and user_input.intent == IntentCategory.FACTUAL:
            lower = user_input.resolved_query.lower()
            comparative_cues = ["compare", "vs", "versus", "difference", "better", "while", "whereas"]
            if not any(cue in lower for cue in comparative_cues):
                return True
        return False

    def _decompose_with_llm(
        self,
        user_input: StructuredUserInput,
        info_need: InformationNeedProfile
    ) -> List[SubQueryPlan] | None:
        system_prompt = (
            "You are an expert Query Decomposition Planner (Q-DREAM QDM, ACL 2025).\n"
            "Break down the user's research inquiry into clear atomic sub-queries.\n"
            "For each sub-query, provide:\n"
            "- 'id': e.g. 'sq_1', 'sq_2'\n"
            "- 'description': semantic objective\n"
            "- 'raw_sub_query': clean atomic question\n"
            "- 'depends_on': list of IDs this sub-query requires results from (empty if independent)\n"
            "- 'expected_output_type': 'FACT', 'SUMMARY', 'COMPARISON_ROW', or 'CAUSAL_EXPLANATION'\n"
            "Ensure total coverage of all query entities and constraints."
        )
        user_prompt = (
            f"Query: {user_input.resolved_query}\n"
            f"Intent: {user_input.intent.value}\n"
            f"Query Type: {user_input.query_type.value}\n"
            f"Entities: {user_input.entities}\n"
            f"Criteria: {info_need.evaluation_criteria}\n"
            f"Constraints: {user_input.constraints}"
        )

        result = self.llm_client.generate_structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema_name="sub_queries_plan"
        )
        if result and isinstance(result, dict) and "sub_queries" in result:
            items = result.get("sub_queries", [])
            parsed = []
            for item in items:
                try:
                    exp_type = item.get("expected_output_type", "FACT")
                    if exp_type not in [e.value for e in OutputExpectation]:
                        exp_type = "FACT"
                    parsed.append(SubQueryPlan(
                        id=str(item.get("id", f"sq_{len(parsed)+1}")),
                        description=str(item.get("description", "Atomic sub-query")),
                        raw_sub_query=str(item.get("raw_sub_query", user_input.resolved_query)),
                        depends_on=[str(d) for d in item.get("depends_on", [])],
                        stage_index=0,
                        expected_output_type=OutputExpectation(exp_type),
                        is_atomic=True
                    ))
                except Exception:
                    continue
            if parsed:
                return parsed
        return None

    def _decompose_deterministic(
        self,
        user_input: StructuredUserInput,
        info_need: InformationNeedProfile
    ) -> List[SubQueryPlan]:
        query = user_input.resolved_query
        intent = user_input.intent
        entities = user_input.entities or info_need.known_anchors
        criteria_str = ", ".join(info_need.evaluation_criteria) if info_need.evaluation_criteria else "architecture and performance"

        subqueries = []

        # 1. Comparative Decomposition: Parallel branches for entities + 1 synthesis node
        stopwords = {"what", "how", "why", "when", "where", "who", "the", "is", "are", "in", "on", "to", "does", "can", "could", "should", "would", "do", "did", "and"}
        valid_entities = [e for e in entities if e.lower() not in stopwords and len(e.strip()) >= 3]

        is_explicit_comparison = (
            intent == IntentCategory.COMPARATIVE
            or any(w in query.lower() for w in ["compare ", " vs ", " versus ", "tradeoff", "differ between"])
        )

        if is_explicit_comparison and len(valid_entities) >= 2:
            e1, e2 = valid_entities[0], valid_entities[1]
            subqueries.append(SubQueryPlan(
                id="sq_1",
                description=f"Analyze {e1} properties and performance",
                raw_sub_query=f"What are the specifications, {criteria_str} of {e1}?",
                depends_on=[],
                expected_output_type=OutputExpectation.FACT,
                is_atomic=True
            ))
            subqueries.append(SubQueryPlan(
                id="sq_2",
                description=f"Analyze {e2} properties and performance",
                raw_sub_query=f"What are the specifications, {criteria_str} of {e2}?",
                depends_on=[],
                expected_output_type=OutputExpectation.FACT,
                is_atomic=True
            ))
            subqueries.append(SubQueryPlan(
                id="sq_3",
                description=f"Direct comparative synthesis between {e1} and {e2}",
                raw_sub_query=f"Compare {e1} and {e2} regarding {criteria_str} and key trade-offs",
                depends_on=["sq_1", "sq_2"],
                expected_output_type=OutputExpectation.COMPARISON_ROW,
                is_atomic=False
            ))
        elif is_explicit_comparison:
            # Single or implicit entity comparative
            primary = valid_entities[0] if valid_entities else query
            subqueries.append(SubQueryPlan(
                id="sq_1",
                description="Identify primary baseline entity properties",
                raw_sub_query=f"What are the key characteristics of {primary}?",
                depends_on=[],
                expected_output_type=OutputExpectation.FACT,
                is_atomic=True
            ))
            subqueries.append(SubQueryPlan(
                id="sq_2",
                description="Identify alternative comparative benchmarks",
                raw_sub_query=f"What are standard benchmarks and alternatives to {primary}?",
                depends_on=["sq_1"],
                expected_output_type=OutputExpectation.COMPARISON_ROW,
                is_atomic=True
            ))

        # 2. Multi-Hop / Synthesis Decomposition: Sequential stages
        elif user_input.query_type == QueryTypeCategory.MULTI_HOP or intent == IntentCategory.SYNTHESIS:
            # Check for multiple questions or conjunctions
            clauses = [c.strip() for c in re.split(r"\band\b|\bthen\b|\bafter\b|\bhow does\b", query, flags=re.IGNORECASE) if len(c.strip()) > 8]
            if len(clauses) >= 2:
                for idx, clause in enumerate(clauses):
                    sq_id = f"sq_{idx + 1}"
                    depends = [f"sq_{idx}"] if idx > 0 else []
                    subqueries.append(SubQueryPlan(
                        id=sq_id,
                        description=f"Examine stage {idx+1}: {clause[:40]}...",
                        raw_sub_query=clause if clause.endswith("?") else f"{clause}?",
                        depends_on=depends,
                        expected_output_type=OutputExpectation.CAUSAL_EXPLANATION if idx > 0 else OutputExpectation.FACT,
                        is_atomic=True
                    ))
            else:
                subqueries.append(SubQueryPlan(
                    id="sq_1",
                    description="Investigate baseline mechanism",
                    raw_sub_query=f"What is the underlying mechanism and definition of {query}?",
                    depends_on=[],
                    expected_output_type=OutputExpectation.FACT,
                    is_atomic=True
                ))
                subqueries.append(SubQueryPlan(
                    id="sq_2",
                    description="Evaluate causal impact and application",
                    raw_sub_query=f"What are the downstream effects, implications, and applications of {query}?",
                    depends_on=["sq_1"],
                    expected_output_type=OutputExpectation.CAUSAL_EXPLANATION,
                    is_atomic=True
                ))

        # 3. Default fallback: Single focused sub-query
        else:
            subqueries.append(SubQueryPlan(
                id="sq_1",
                description="Direct factual inquiry",
                raw_sub_query=query,
                depends_on=[],
                expected_output_type=OutputExpectation.FACT,
                is_atomic=True
            ))

        return subqueries

    def _verify_and_enforce_coverage(
        self,
        user_input: StructuredUserInput,
        subqueries: List[SubQueryPlan]
    ) -> CoverageReport:
        """
        PROGRESS (2026) Coverage Verification:
        Coverage = |Entities(Q) ∩ Union(Entities(subqueries))| / |Entities(Q)| == 1.0
        If any entity from Layer 1 is missing, append a dedicated atomic sub-query.
        """
        entities = set(e.strip().lower() for e in user_input.entities if len(e.strip()) > 1)
        if not entities:
            return CoverageReport(is_fully_covered=True, coverage_score=1.0, covered_elements=[], missing_elements=[])

        all_subquery_text = " ".join(sq.raw_sub_query.lower() + " " + sq.description.lower() for sq in subqueries)
        
        covered = []
        missing = []
        for ent in entities:
            if ent in all_subquery_text:
                covered.append(ent)
            else:
                missing.append(ent)

        coverage_score = len(covered) / len(entities) if entities else 1.0

        # Enforce 100% coverage by creating a targeted query for any missing element
        if missing:
            for m_idx, missing_entity in enumerate(missing):
                new_id = f"sq_cov_{m_idx+1}"
                subqueries.append(SubQueryPlan(
                    id=new_id,
                    description=f"PROGRESS coverage guard: Retrieve context for {missing_entity}",
                    raw_sub_query=f"What is the role and data regarding {missing_entity} in relation to {user_input.resolved_query}?",
                    depends_on=[],
                    expected_output_type=OutputExpectation.FACT,
                    is_atomic=True
                ))
                covered.append(missing_entity)
            coverage_score = 1.0
            missing = []

        return CoverageReport(
            is_fully_covered=len(missing) == 0,
            coverage_score=coverage_score,
            covered_elements=covered,
            missing_elements=missing
        )
