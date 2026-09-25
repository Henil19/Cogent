"""
Sub-Module 6.7: Layer 6 Pipeline Orchestrator
Connects Layer 5 VerifiedEvidenceSet, Layer 2 KnowledgeRetrievalPlan, and Layer 1 StructuredUserInput.
Executes Evidence-to-Claim Chaining, Multi-Hop Inference, Dialectical Conflict Reconciliation (Zero Winner Forcing),
Comparative Decision Matrices, Epistemic Gap Bounding, and Structured Trace Building.
Emits standardized SynthesizedReasoningTrace strictly to Layer 7.
"""

import time
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional

from app.core.layer6.chainer.claim_chainer import ClaimChainer
from app.core.layer6.multihop.multihop_engine import MultiHopEngine
from app.core.layer6.reconciliation.conflict_reconciler import ConflictReconciler
from app.core.layer6.comparative.comparative_engine import ComparativeEngine
from app.core.layer6.epistemic.epistemic_evaluator import EpistemicEvaluator
from app.core.layer6.trace.trace_builder import TraceBuilder

from app.core.llm_client import LLMClient
from app.schemas.layer1 import StructuredUserInput
from app.schemas.layer2 import KnowledgeRetrievalPlan
from app.schemas.layer5 import VerifiedEvidenceSet
from app.schemas.layer6 import (
    SynthesizedReasoningTrace,
    SynthesizedClaim,
    SynthesisStatus,
    ReasoningStepType
)

logger = logging.getLogger(__name__)


class Layer6Pipeline:
    """
    Orchestrates evidence-grounded transparent reasoning, multi-hop premise chaining,
    dialectical conflict reconciliation, and proof trace assembly.
    """

    def __init__(
        self,
        chainer: Optional[ClaimChainer] = None,
        multihop: Optional[MultiHopEngine] = None,
        reconciler: Optional[ConflictReconciler] = None,
        comparative: Optional[ComparativeEngine] = None,
        epistemic: Optional[EpistemicEvaluator] = None,
        trace_builder: Optional[TraceBuilder] = None,
        llm_client: Optional[LLMClient] = None
    ):
        client = llm_client or LLMClient()
        self.chainer = chainer or ClaimChainer(llm_client=client)
        self.multihop = multihop or MultiHopEngine(llm_client=client)
        self.reconciler = reconciler or ConflictReconciler(llm_client=client)
        self.comparative = comparative or ComparativeEngine(llm_client=client)
        self.epistemic = epistemic or EpistemicEvaluator()
        self.trace_builder = trace_builder or TraceBuilder()

    def execute(
        self,
        evidence_set: VerifiedEvidenceSet,
        plan: KnowledgeRetrievalPlan,
        user_input: Optional[StructuredUserInput] = None
    ) -> SynthesizedReasoningTrace:
        """
        Execute full Layer 6 transparent reasoning workflow.
        """
        start_time = time.time()
        query_intent = user_input.intent.value if (user_input and hasattr(user_input.intent, "value")) else (
            str(user_input.intent) if user_input and user_input.intent else "FACTUAL"
        )

        # 1. Sub-Module 6.1: Evidence-to-Claim Chaining (TRACE 2024)
        leaf_nodes, sub_query_claims = self.chainer.build_premise_nodes(
            evidence_set=evidence_set,
            plan=plan
        )

        # 2. Sub-Module 6.2: Multi-Hop Inference Engine (Dalvi et al. 2021, SR-RAG 2026)
        multihop_nodes = self.multihop.execute_multihop_reasoning(
            leaf_nodes=leaf_nodes,
            sub_query_claims=sub_query_claims,
            plan=plan,
            start_step_index=len(leaf_nodes)
        )

        # 3. Sub-Module 6.3: Dialectical Conflict Reconciler (MAGIC 2025, ConfRAG 2026 - Zero Winner Forcing)
        reconciliations, conflict_nodes = self.reconciler.reconcile_conflicts(
            evidence_set=evidence_set,
            start_step_index=len(leaf_nodes) + len(multihop_nodes)
        )

        # 4. Sub-Module 6.4: Comparative & Decision Engine (Graph-of-Thoughts 2024)
        comparative_matrix, comp_nodes, comp_claims = self.comparative.build_comparison_matrix(
            evidence_set=evidence_set,
            plan=plan,
            user_input=user_input,
            start_step_index=len(leaf_nodes) + len(multihop_nodes) + len(conflict_nodes)
        )

        # 5. Sub-Module 6.5: Epistemic Gap & Insufficiency Evaluator (S2G-RAG 2026)
        unresolved_hedges, hedge_nodes, hedge_claims, is_complete = self.epistemic.evaluate_gaps_and_hedges(
            evidence_set=evidence_set,
            plan=plan,
            sub_query_claims=sub_query_claims,
            start_step_index=len(leaf_nodes) + len(multihop_nodes) + len(conflict_nodes) + len(comp_nodes)
        )

        # 6. Aggregate Step Nodes and Synthesized Claims
        all_steps = leaf_nodes + multihop_nodes + conflict_nodes + comp_nodes + hedge_nodes

        synthesized_claims: List[SynthesizedClaim] = []
        synthesized_claims.extend(comp_claims)
        synthesized_claims.extend(hedge_claims)

        # If multihop steps produced intermediate conclusions, add substantive synthesized claims
        for step in multihop_nodes:
            syn_claim = SynthesizedClaim(
                claim_id=f"syn_hop_{step.step_id}",
                statement=step.intermediate_claim,
                status=SynthesisStatus.GROUNDED_DEDUCTION,
                source_claim_ids=step.premise_claim_ids,
                supporting_evidence_ids=step.evidence_ids,
                opposing_evidence_ids=[],
                derivation_step_ids=[step.step_id],
                caveats=[]
            )
            synthesized_claims.append(syn_claim)

        # Always prioritize grounded factual deductions from leaf premise steps
        if leaf_nodes:
            for leaf in leaf_nodes:
                syn_claim = SynthesizedClaim(
                    claim_id=f"syn_leaf_{leaf.step_id}",
                    statement=leaf.intermediate_claim,
                    status=SynthesisStatus.GROUNDED_DEDUCTION,
                    source_claim_ids=leaf.premise_claim_ids,
                    supporting_evidence_ids=leaf.evidence_ids,
                    opposing_evidence_ids=[],
                    derivation_step_ids=[leaf.step_id],
                    caveats=leaf.unresolved_issues
                )
                synthesized_claims.append(syn_claim)

        # If dialectical conflict reconciliations exist and have valid content, add dialectical claims
        for rec in reconciliations:
            if "Claim B statement" in rec.reconciliation_analysis or "Direct divergence observed between claim" in rec.reconciliation_analysis:
                continue
            dial_claim = SynthesizedClaim(
                claim_id=f"syn_dial_{rec.reconciliation_id}",
                statement=rec.reconciliation_analysis,
                status=SynthesisStatus.DIALECTICAL_SYNTHESIS,
                source_claim_ids=[rec.claim_a_id, rec.claim_b_id],
                supporting_evidence_ids=rec.supporting_evidence_ids,
                opposing_evidence_ids=[],
                derivation_step_ids=[],
                caveats=rec.contextual_factors
            )
            synthesized_claims.append(dial_claim)

        # 7. Sub-Module 6.6: Trace Builder & Integrity Metrics (ROSCOE 2023, Weakest Link 2026)
        metrics, final_statement = self.trace_builder.compile_trace_and_metrics(
            all_steps=all_steps,
            synthesized_claims=synthesized_claims,
            reconciliations=reconciliations,
            unresolved_hedges=unresolved_hedges,
            evidence_set=evidence_set
        )

        latency_ms = (time.time() - start_time) * 1000.0

        trace = SynthesizedReasoningTrace(
            reasoning_trace_id=f"trace_{uuid.uuid4().hex[:12]}",
            plan_id=plan.plan_id,
            session_id=plan.session_id,
            evidence_set_id=evidence_set.evidence_set_id,
            query_intent=query_intent,
            reasoning_steps=all_steps,
            synthesized_claims=synthesized_claims,
            conflict_reconciliations=reconciliations,
            has_conflicts=evidence_set.has_conflicts,
            comparative_matrix=comparative_matrix,
            unresolved_hedges=unresolved_hedges,
            unresolved_information_gaps=evidence_set.unresolved_information_gaps,
            final_synthesis_statement=final_statement,
            is_reasoning_complete=is_complete,
            integrity_metrics=metrics,
            processing_time_ms=round(latency_ms, 2),
            created_at=datetime.now(timezone.utc).isoformat()
        )

        logger.info(
            f"Layer 6 reasoning completed for plan {plan.plan_id}: "
            f"{len(all_steps)} steps, {len(synthesized_claims)} claims, {len(reconciliations)} conflict reconciliations, "
            f"chain depth={metrics.logical_chain_depth}, weakest link={metrics.weakest_link_score:.2f} in {latency_ms:.1f}ms."
        )

        return trace
