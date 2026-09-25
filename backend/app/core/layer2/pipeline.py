"""
Layer 2 Orchestration Pipeline: Query Understanding & Planning
Accepts StructuredUserInput from Layer 1, executes sub-modules 2.1 to 2.5,
and emits KnowledgeRetrievalPlan for Layer 3 (Knowledge Acquisition) and Layer 4 (Retrieval).
"""

import time
from typing import Optional, List
from app.schemas.layer1 import StructuredUserInput
from app.schemas.layer2 import KnowledgeRetrievalPlan
from app.core.layer2.information_need import InformationNeedAnalyzer
from app.core.layer2.decomposer import QueryDecomposer
from app.core.layer2.graph_optimizer import GraphOptimizer
from app.core.layer2.expander import MultiRepresentationExpander
from app.core.layer2.router import SourceRouter
from app.core.llm_client import LLMClient


class Layer2Pipeline:
    """End-to-end orchestrator for Cogent Layer 2."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        self.info_analyzer = InformationNeedAnalyzer(self.llm_client)
        self.decomposer = QueryDecomposer(self.llm_client)
        self.graph_optimizer = GraphOptimizer()
        self.expander = MultiRepresentationExpander(self.llm_client)
        self.router = SourceRouter(self.llm_client)

    def process(self, user_input: StructuredUserInput) -> KnowledgeRetrievalPlan:
        """
        Execute the complete Layer 2 planning pipeline.
        Consumes StructuredUserInput contract from Layer 1.
        """
        start_time = time.time() * 1000

        # Step 2.1: Analyze Information Need (AGR ACL'24)
        info_need = self.info_analyzer.analyze(user_input)

        # Step 2.2: Decompose Query with PROGRESS (2026) Coverage Verification
        subqueries, coverage = self.decomposer.decompose(user_input, info_need)

        # Step 2.3: Optimize Execution DAG into Parallel Stages (Q-DREAM SDOM ACL'25)
        execution_stages, optimized_subqueries = self.graph_optimizer.optimize_dag(subqueries)

        # Step 2.4: Multi-Representation Expansion (MuGI, DeCoR, Knowledge-Aware)
        expanded_subqueries = [self.expander.expand(sq) for sq in optimized_subqueries]

        # Step 2.5: Dynamic Source Routing & Plan Assembly (Adaptive-RAG, RealRoute)
        end_time = time.time() * 1000
        plan = self.router.route_and_assemble(
            user_input=user_input,
            info_need=info_need,
            coverage=coverage,
            subqueries=expanded_subqueries,
            execution_stages=execution_stages,
            start_time_ms=start_time,
            end_time_ms=end_time
        )

        return plan


# Global pipeline singleton instance
layer2_pipeline = Layer2Pipeline()
