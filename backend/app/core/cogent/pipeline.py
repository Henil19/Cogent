"""
Cogent Master Pipeline Orchestrator
Coordinates Layers 1 through 10 into a cohesive, research-ready cognitive loop.
Enforces explicit error boundaries, non-blocking post-hoc telemetry, and Zero Epistemic Mutation.
"""

from typing import Optional, Dict, Any, List
import copy
from datetime import datetime, timezone

from app.schemas.layer1 import Layer1Request, StructuredUserInput, Layer1Status
from app.schemas.layer2 import KnowledgeRetrievalPlan, SourceTarget
from app.schemas.layer3 import AcquiredCorpusBatch, AcquisitionStatus
from app.schemas.layer4 import RetrievedCandidateSet
from app.schemas.layer5 import VerifiedEvidenceSet, EvidenceItem, GroundingStatus
from app.schemas.layer6 import SynthesizedReasoningTrace, ReasoningIntegrityMetrics
from app.schemas.layer7 import (
    TrustAssessment,
    ReasoningTrustAssessment,
    UncertaintyAssessment,
    HallucinationRiskAssessment,
)
from app.schemas.layer8 import (
    ExplanationPackage,
    ExplanationAudience,
    MultiFidelityNarrative,
    ExplanationValidation,
    ExplanationFidelityStatus,
)
from app.schemas.layer9 import UnifiedResponsePayload, PresentationFormat

from app.core.layer1.pipeline import Layer1Pipeline
from app.core.layer2.pipeline import Layer2Pipeline
from app.core.layer3.pipeline import Layer3Pipeline
from app.core.layer4.pipeline import Layer4Pipeline
from app.core.layer5.pipeline import Layer5Pipeline
from app.core.layer6.pipeline import Layer6Pipeline
from app.core.layer7.pipeline import Layer7Pipeline
from app.core.layer8.pipeline import Layer8Pipeline
from app.core.layer9.pipeline import Layer9Pipeline
from app.core.layer10.pipeline import Layer10Pipeline, layer10_pipeline

from app.core.cogent.contracts import (
    CogentQueryRequest,
    CogentQueryResponse,
    ExecutionMetrics,
    PipelineStatus,
)
from app.core.cogent.execution_context import ExecutionContext


class CogentPipeline:
    """
    Master orchestrator executing the 10-layer Cogent cognitive pipeline:
    L1 (Understand) -> L2 (Plan) -> L3 (Acquire) -> L4 (Retrieve) ->
    L5 (Verify) -> L6 (Reason) -> L7 (Trust) -> L8 (Explain) ->
    L9 (Present) -> L10 (Learn - Post-Hoc).
    """

    def __init__(
        self,
        use_mock_embeddings: bool = True,
        use_mock_verification: bool = True,
        layer1: Optional[Layer1Pipeline] = None,
        layer2: Optional[Layer2Pipeline] = None,
        layer3: Optional[Layer3Pipeline] = None,
        layer4: Optional[Layer4Pipeline] = None,
        layer5: Optional[Layer5Pipeline] = None,
        layer6: Optional[Layer6Pipeline] = None,
        layer7: Optional[Layer7Pipeline] = None,
        layer8: Optional[Layer8Pipeline] = None,
        layer9: Optional[Layer9Pipeline] = None,
        layer10: Optional[Layer10Pipeline] = None,
    ):
        self.layer1 = layer1 or Layer1Pipeline()
        self.layer2 = layer2 or Layer2Pipeline()
        self.layer3 = layer3 or Layer3Pipeline()
        self.layer4 = layer4 or Layer4Pipeline(use_mock_embeddings=use_mock_embeddings)
        self.layer5 = layer5 or Layer5Pipeline(use_mock=use_mock_verification)
        self.layer6 = layer6 or Layer6Pipeline()
        self.layer7 = layer7 or Layer7Pipeline()
        self.layer8 = layer8 or Layer8Pipeline()
        self.layer9 = layer9 or Layer9Pipeline()
        self.layer10 = layer10 or Layer10Pipeline()

    def execute(
        self,
        request: CogentQueryRequest,
        db: Any = None,
    ) -> CogentQueryResponse:
        """
        Executes the full 10-layer cognitive loop for an incoming research query.
        """
        ctx = ExecutionContext(
            raw_query=request.query,
            session_id=request.session_id,
            user_id=request.user_id,
        )

        # ---------------------------------------------------------------------
        # Layer 1: User Interaction & Ambiguity Resolution Gate
        # ---------------------------------------------------------------------
        ctx.start_layer(1)
        # Extract clarification response if provided (either direct string or dictionary of responses from UI)
        clarification_ans = request.clarification_response
        if not clarification_ans and request.clarification_responses:
            vals = [str(v).strip() for v in request.clarification_responses.values() if v and str(v).strip()]
            if vals:
                clarification_ans = " | ".join(vals)

        l1_req = Layer1Request(
            query=request.query,
            conversation_id=request.session_id,
            clarification_response=clarification_ans,
        )
        l1_res = self.layer1.process(db=db, request=l1_req)

        # Early return boundary on ambiguity or sufficiency deficit
        if l1_res.status == Layer1Status.CLARIFICATION_NEEDED or not l1_res.contract_for_layer2:
            ctx.end_layer(1, l1_res.contract_for_layer2)
            for lid in range(2, 10):
                ctx.skip_layer(lid, "Ambiguity threshold triggered; early return")

            # Record non-blocking telemetry for Layer 1
            self._record_layer10_telemetry_safe(ctx, request)
            total_duration = ctx.finalize()

            clarification_data = (
                l1_res.clarification.model_dump()
                if l1_res.clarification
                else {"message": "Query under-specified. Please clarify."}
            )
            if l1_res.clarification and l1_res.clarification.clarification_questions:
                clarification_data["clarification_question"] = l1_res.clarification.clarification_questions[0]
                clarification_data["targeted_aspect"] = (
                    l1_res.clarification.aspects_to_clarify[0]
                    if l1_res.clarification.aspects_to_clarify
                    else None
                )
                clarification_data["options"] = l1_res.clarification.suggested_options
            return CogentQueryResponse(
                execution_id=ctx.execution_id,
                status=PipelineStatus.CLARIFICATION_REQUIRED,
                clarification_prompt=clarification_data,
                metrics=ExecutionMetrics(
                    total_duration_ms=total_duration,
                    layer_durations_ms=ctx.layer_timings_ms,
                ),
                warnings=ctx.warnings,
            )

        structured_input = StructuredUserInput(**l1_res.contract_for_layer2)
        ctx.end_layer(1, structured_input)

        # ---------------------------------------------------------------------
        # Layer 2: Query Understanding & Strategic Planning
        # ---------------------------------------------------------------------
        ctx.start_layer(2)
        l2_plan: KnowledgeRetrievalPlan = self.layer2.process(structured_input)
        if request.retrieval_target:
            if request.retrieval_target != SourceTarget.HYBRID:
                l2_plan.target_sources_summary = [request.retrieval_target]
                for sq in l2_plan.sub_queries:
                    sq.target_source = request.retrieval_target
            else:
                if SourceTarget.HYBRID not in l2_plan.target_sources_summary:
                    l2_plan.target_sources_summary.append(SourceTarget.HYBRID)
        ctx.end_layer(2, l2_plan)

        # ---------------------------------------------------------------------
        # Layer 3: Knowledge Acquisition & Pre-Retrieval Grounding
        # ---------------------------------------------------------------------
        ctx.start_layer(3)
        if request.corpus_batch is not None:
            corpus_batch = request.corpus_batch
        else:
            corpus_batch = self.layer3.execute_plan(plan=l2_plan, db=db)
            if not corpus_batch or len(corpus_batch.chunks) == 0:
                # Build fallback empty corpus batch to trigger calibrated evidence deficit
                corpus_batch = AcquiredCorpusBatch(
                    batch_id=f"batch_{ctx.execution_id}",
                    plan_id=l2_plan.plan_id,
                    session_id=l2_plan.session_id,
                    chunks=[],
                    total_documents=0,
                    total_chunks=0,
                    total_tokens=0,
                    acquisition_time_ms=0.0,
                    status=AcquisitionStatus.READY_FOR_RETRIEVAL,
                )
        ctx.end_layer(3, corpus_batch)

        # ---------------------------------------------------------------------
        # Layer 4: Hybrid Knowledge Retrieval (FAISS Dense + BM25 Sparse + RRF)
        # ---------------------------------------------------------------------
        ctx.start_layer(4)
        dense_only = (request.ablation_mode == "dense_only")
        sparse_only = (request.ablation_mode == "sparse_only")
        use_hybrid = not (dense_only or sparse_only)
        candidate_set: RetrievedCandidateSet = self.layer4.execute(
            plan=l2_plan,
            corpus_batch=corpus_batch,
            top_k=request.max_evidence_count,
            use_hybrid=use_hybrid,
            sparse_only=sparse_only,
        )
        ctx.end_layer(4, candidate_set)

        # ---------------------------------------------------------------------
        # Layer 5: Evidence Intelligence & Conflict Resolution
        # ---------------------------------------------------------------------
        ctx.start_layer(5)
        if request.ablation_mode == "no_l5":
            # Bypass L5: pass raw L4 candidates directly into verified evidence set
            cands = candidate_set.all_candidates
            selected_ev = []
            for c in cands[:request.max_evidence_count]:
                selected_ev.append(
                    EvidenceItem(
                        evidence_id=f"ev_{c.candidate_id}",
                        candidate_id=c.candidate_id,
                        chunk_id=c.chunk_id,
                        document_id=c.document_id,
                        sub_query_id=c.sub_query_id,
                        content=c.content,
                        title=c.title,
                        source_uri=c.source_uri,
                        source_type=c.source_type,
                        similarity_score=c.similarity_score,
                        rerank_score=0.5,
                        atomic_claims=[],
                        overall_grounding=GroundingStatus.NEUTRAL,
                        document_hash=c.document_hash,
                        content_hash=c.content_hash,
                        retrieved_at=c.retrieved_at,
                    )
                )
            evidence_set = VerifiedEvidenceSet(
                evidence_set_id=f"ev_abl_{ctx.execution_id}",
                plan_id=l2_plan.plan_id,
                session_id=l2_plan.session_id,
                selected_evidence=selected_ev,
                total_candidates_evaluated=len(cands),
                selected_evidence_count=len(selected_ev),
                conflict_edges=[],
                has_conflicts=False,
                duplicate_groups=[],
                coverage_map={},
                overall_coverage_ratio=1.0,
                unresolved_information_gaps=[],
                is_sufficient_for_reasoning=True,
                processing_time_ms=0.0
            )
        else:
            evidence_set = self.layer5.execute(
                candidate_set=candidate_set,
                plan=l2_plan,
                max_evidence=request.max_evidence_count,
                rerank_threshold=0.10,
            )
        ctx.end_layer(5, evidence_set)

        # ---------------------------------------------------------------------
        # Layer 6: Transparent Reasoning & Synthesis
        # ---------------------------------------------------------------------
        ctx.start_layer(6)
        if request.ablation_mode == "no_l6":
            # L6-disabled generation receives the same selected evidence without L6 structured reasoning synthesis
            flat_summary = "\n\n".join(e.content for e in evidence_set.selected_evidence)
            trace_l6 = SynthesizedReasoningTrace(
                reasoning_trace_id=f"trace_abl_{ctx.execution_id}",
                plan_id=l2_plan.plan_id,
                session_id=l2_plan.session_id,
                evidence_set_id=evidence_set.evidence_set_id,
                query_intent=structured_input.intent.value if structured_input.intent else "FACTUAL",
                reasoning_steps=[],
                synthesized_claims=[],
                conflict_reconciliations=[],
                has_conflicts=False,
                comparative_matrix=[],
                unresolved_hedges=[],
                unresolved_information_gaps=[],
                final_synthesis_statement=flat_summary[:1000] if flat_summary else "No reasoning generated.",
                is_reasoning_complete=True,
                integrity_metrics=ReasoningIntegrityMetrics(
                    total_reasoning_steps=0,
                    premises_grounded_ratio=0.0,
                    claim_support_ratio=0.0,
                    conflict_reconciliation_ratio=0.0,
                    weakest_link_score=0.0,
                    epistemic_gap_count=0,
                    logical_chain_depth=0,
                    has_unresolved_contradictions=False,
                ),
                processing_time_ms=0.0
            )
        else:
            trace_l6 = self.layer6.execute(
                evidence_set=evidence_set,
                plan=l2_plan,
                user_input=structured_input,
            )
        ctx.end_layer(6, trace_l6)

        # ---------------------------------------------------------------------
        # Layer 7: Trust Intelligence & Confidence Calibration
        # ---------------------------------------------------------------------
        ctx.start_layer(7)
        if request.ablation_mode == "no_l7":
            # Disables L7 trust assessment and confidence calibration.
            # Uses predefined uncalibrated baseline behavior (uncalibrated 0.50 heuristic)
            trust_assessment = TrustAssessment(
                assessment_id=f"trust_abl_{ctx.execution_id}",
                plan_id=l2_plan.plan_id,
                session_id=l2_plan.session_id,
                reasoning_trace_id=trace_l6.reasoning_trace_id,
                global_trust_index=0.50,
                global_confidence=0.50,
                confidence_tier=None,
                is_safe_for_decision_support=None,
                claim_assessments=[],
                source_assessments=[],
                evidence_assessments=[],
                reasoning_assessment=ReasoningTrustAssessment(
                    step_trust_scores=[],
                    weakest_link_step_id="none",
                    weakest_link_score=0.50,
                    average_chain_trust=0.50,
                    path_trust_score=0.50,
                    is_chain_intact=True
                ),
                uncertainty_assessment=UncertaintyAssessment(
                    overall_uncertainty=0.50,
                    active_uncertainties=[],
                    epistemic_uncertainty_ratio=0.50,
                    aleatoric_uncertainty_ratio=0.50,
                    explanation_of_uncertainty="Uncalibrated baseline policy."
                ),
                hallucination_assessment=HallucinationRiskAssessment(
                    has_hallucination_risk=False,
                    risk_level="NONE",
                    detected_risks=[],
                    risk_explanations=[]
                ),
                key_trust_strengths=[],
                key_limitations=[],
                processing_time_ms=0.0
            )
        else:
            trust_assessment = self.layer7.execute(
                trace=trace_l6,
                evidence_set=evidence_set,
                plan=l2_plan,
            )
        ctx.end_layer(7, trust_assessment)

        # ---------------------------------------------------------------------
        # Layer 8: Dynamic Explainability & Attribution
        # ---------------------------------------------------------------------
        ctx.start_layer(8)
        if request.ablation_mode == "no_l8":
            # Removes L8 attribution/explanation processing while preserving underlying response/evidence inputs
            explanation_pkg = ExplanationPackage(
                explanation_id=f"expl_abl_{ctx.execution_id}",
                session_id=l2_plan.session_id,
                plan_id=l2_plan.plan_id,
                reasoning_trace_id=trace_l6.reasoning_trace_id,
                trust_assessment_id=trust_assessment.assessment_id,
                primary_audience=request.target_audience,
                narrative_steps=[],
                multi_fidelity=MultiFidelityNarrative(
                    executive_summary="",
                    researcher_narrative="",
                    layperson_narrative="",
                    domain_expert_narrative=""
                ),
                claim_explanations=[],
                evidence_attributions=[],
                citation_map={},
                conflict_explanations=[],
                uncertainty_narrative="",
                counterfactual_explanations=[],
                limitations=[],
                validation=ExplanationValidation(
                    is_faithful=True,
                    fidelity_status=ExplanationFidelityStatus.FULLY_FAITHFUL,
                    validation_score=1.0,
                    validation_summary="L8 ablated"
                ),
                generated_at=datetime.now(timezone.utc).isoformat(),
                processing_time_ms=0.0
            )
        else:
            explanation_pkg = self.layer8.execute(
                trace=trace_l6,
                trust_assessment=trust_assessment,
                evidence_set=evidence_set,
                plan=l2_plan,
                user_input=structured_input,
                audience=request.target_audience,
            )
        ctx.end_layer(8, explanation_pkg)

        # ---------------------------------------------------------------------
        # Layer 9: Response Generation & Presentation
        # ---------------------------------------------------------------------
        ctx.start_layer(9)
        unified_response: UnifiedResponsePayload = self.layer9.execute(
            explanation_pkg=explanation_pkg,
            trust_assessment=trust_assessment,
            user_input=structured_input,
            trace=trace_l6,
            plan=l2_plan,
            target_audience=request.target_audience,
            format_type=PresentationFormat.MARKDOWN,
        )
        ctx.end_layer(9, unified_response)

        # Capture frozen copy of epistemic output prior to Layer 10 execution
        epistemic_before = {
            "rendered_content": unified_response.rendered_content,
            "sections": copy.deepcopy(unified_response.sections),
            "citation_registry": copy.deepcopy(unified_response.citation_registry),
            "global_confidence": trust_assessment.global_confidence,
            "global_trust_index": trust_assessment.global_trust_index,
        }

        # ---------------------------------------------------------------------
        # Layer 10: Analytics, Telemetry & Continuous Learning (Post-Hoc Isolation)
        # ---------------------------------------------------------------------
        grounding_score: Optional[float] = None
        ctx.start_layer(10)
        try:
            trace = self.layer10.collector.start_trace(raw_query=request.query)
            for lid, artifact in ctx.layer_artifacts.items():
                self.layer10.collector.attach_layer_artifact(
                    trace.execution_id,
                    lid,
                    artifact,
                    duration_ms=ctx.layer_timings_ms.get(lid, 0.0),
                )
            l10_res = self.layer10.process_execution(trace)
            ctx.end_layer(10, l10_res)
            if l10_res.evaluation_report:
                grounding_score = l10_res.evaluation_report.grounding_score
        except Exception as exc:
            ctx.fail_layer(10, str(exc))
            ctx.add_warning(f"Non-fatal Layer 10 telemetry recording failure: {str(exc)}")

        # Zero Epistemic Mutation verification
        assert unified_response.rendered_content == epistemic_before["rendered_content"], (
            "CRITICAL: Zero Epistemic Mutation invariant violated! Layer 10 mutated response markdown."
        )

        total_duration = ctx.finalize()

        # Determine outcome status: check if qualified abstention occurred
        is_evidence_deficit = (
            candidate_set.total_candidates_returned == 0
            or evidence_set.selected_evidence_count == 0
            or trust_assessment.global_confidence < 0.45
        )
        final_status = (
            PipelineStatus.INSUFFICIENT_EVIDENCE_QUALIFIED
            if is_evidence_deficit
            else PipelineStatus.SUCCESS
        )

        metrics = ExecutionMetrics(
            total_duration_ms=total_duration,
            layer_durations_ms=ctx.layer_timings_ms,
            global_trust_index=trust_assessment.global_trust_index,
            calibrated_confidence=trust_assessment.global_confidence,
            grounding_score=grounding_score,
            candidates_retrieved=candidate_set.total_candidates_returned,
            evidence_selected=evidence_set.selected_evidence_count,
            claims_synthesized=len(trace_l6.synthesized_claims),
            citation_badges_count=len(unified_response.citation_registry),
        )

        return CogentQueryResponse(
            execution_id=ctx.execution_id,
            status=final_status,
            unified_response=unified_response,
            retrieved_chunk_ids=[c.chunk_id for c in candidate_set.all_candidates],
            metrics=metrics,
            warnings=ctx.warnings,
        )

    def _record_layer10_telemetry_safe(
        self,
        ctx: ExecutionContext,
        request: CogentQueryRequest,
    ) -> None:
        """Safely records early-exit Layer 1 telemetry without raising exceptions."""
        try:
            ctx.start_layer(10)
            trace = self.layer10.collector.start_trace(raw_query=request.query)
            for lid, art in ctx.layer_artifacts.items():
                self.layer10.collector.attach_layer_artifact(
                    trace.execution_id,
                    lid,
                    art,
                    duration_ms=ctx.layer_timings_ms.get(lid, 0.0),
                )
            self.layer10.process_execution(trace)
            ctx.end_layer(10)
        except Exception as exc:
            ctx.fail_layer(10, str(exc))
            ctx.add_warning(f"Non-fatal telemetry recording error: {str(exc)}")


# Singleton instance for general use
cogent_pipeline = CogentPipeline()
