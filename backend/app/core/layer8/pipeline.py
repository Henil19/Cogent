"""
Sub-Module 8.8 (Orchestrator): Layer 8 Pipeline Orchestrator
Coordinates sub-modules 8.1 through 8.7 and executes the 8.8 integrity audit,
compiling the complete, verified ExplanationPackage for Layer 9.
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, List

from app.schemas.layer1 import StructuredUserInput
from app.schemas.layer2 import KnowledgeRetrievalPlan
from app.schemas.layer5 import VerifiedEvidenceSet
from app.schemas.layer6 import SynthesizedReasoningTrace
from app.schemas.layer7 import TrustAssessment
from app.schemas.layer8 import (
    ExplanationPackage,
    ClaimExplanation,
    ExplanationAudience
)
from app.core.layer8.attribution.claim_attribution_engine import ClaimAttributionEngine
from app.core.layer8.narrative.dag_narrative_engine import DAGNarrativeEngine
from app.core.layer8.citations.citation_mapping_engine import CitationMappingEngine
from app.core.layer8.uncertainty_explanation.uncertainty_explanation_engine import UncertaintyExplanationEngine
from app.core.layer8.dialectical.dialectical_explanation_engine import DialecticalExplanationEngine
from app.core.layer8.counterfactual.counterfactual_engine import CounterfactualExplanationEngine
from app.core.layer8.adaptation.audience_adaptation_engine import AudienceAdaptationEngine
from app.core.layer8.validation.explanation_validator import ExplanationValidator


class Layer8Pipeline:
    """
    Master pipeline for Layer 8 (Dynamic Explainability & Attribution).
    Orchestrates fine-grained claim attribution, structured DAG narrative compilation,
    citation mapping, uncertainty explanation, dialectical reconciliation narration,
    counterfactual sensitivity analysis, multi-fidelity adaptation, and the 6-gate audit.
    """

    def __init__(self):
        self.attribution_engine = ClaimAttributionEngine()
        self.narrative_engine = DAGNarrativeEngine()
        self.citation_engine = CitationMappingEngine()
        self.uncertainty_engine = UncertaintyExplanationEngine()
        self.dialectical_engine = DialecticalExplanationEngine()
        self.counterfactual_engine = CounterfactualExplanationEngine()
        self.adaptation_engine = AudienceAdaptationEngine()
        self.validator = ExplanationValidator()

    def execute(
        self,
        trace: SynthesizedReasoningTrace,
        trust_assessment: TrustAssessment,
        evidence_set: VerifiedEvidenceSet,
        plan: Optional[KnowledgeRetrievalPlan] = None,
        user_input: Optional[StructuredUserInput] = None,
        audience: Optional[ExplanationAudience] = ExplanationAudience.TECHNICAL_RESEARCHER
    ) -> ExplanationPackage:
        """
        Executes the end-to-end Layer 8 explanation and attribution pipeline.
        """
        start_time = time.perf_counter()
        explanation_id = f"exp_{uuid.uuid4().hex[:12]}"

        # Step 1: Claim Attribution (Sub-Module 8.1)
        attributions, claim_attr_map = self.attribution_engine.build_attributions(
            trace=trace,
            evidence_set=evidence_set
        )

        # Step 2: Faithful DAG-to-Narrative (Sub-Module 8.2)
        narrative_steps = self.narrative_engine.build_narrative_steps(
            trace=trace,
            claim_attributions=claim_attr_map
        )

        # Step 3: Citation Mapping (Sub-Module 8.3)
        citation_map = self.citation_engine.build_citation_map(attributions=attributions)

        # Step 4: Uncertainty & Trust Explanation (Sub-Module 8.4)
        uncertainty_narrative, limitations = self.uncertainty_engine.explain_uncertainty(
            trust_assessment=trust_assessment
        )

        # Step 5: Dialectical & Contrastive Conflict Explanation (Sub-Module 8.5)
        conflict_explanations = self.dialectical_engine.build_conflict_explanations(
            trace=trace,
            evidence_set=evidence_set
        )

        # Step 6: Counterfactual & Sensitivity Analysis (Sub-Module 8.6)
        counterfactual_explanations = self.counterfactual_engine.build_counterfactual_explanations(
            trace=trace,
            trust_assessment=trust_assessment
        )

        # Step 7: Multi-Fidelity & Audience Adaptation (Sub-Module 8.7)
        multi_fidelity = self.adaptation_engine.build_multi_fidelity_narrative(
            trace=trace,
            trust_assessment=trust_assessment,
            narrative_steps=narrative_steps,
            conflict_explanations=conflict_explanations
        )

        # Build comprehensive claim explanations
        claim_explanations: List[ClaimExplanation] = []
        cf_lookup = {cf.claim_id: cf for cf in counterfactual_explanations}

        for claim in trace.synthesized_claims:
            c_id = claim.claim_id
            tokens = self.citation_engine.get_claim_citations(c_id, attributions)
            cf = cf_lookup.get(c_id)

            why_text = f"Supported directly by {len(claim.supporting_evidence_ids)} empirical evidence items."
            if claim.opposing_evidence_ids:
                why_text += f" Subject to {len(claim.opposing_evidence_ids)} contested observations under alternate parameters."

            cf_sens_text = cf.expected_structural_effect if cf else "No critical single-point failure premise identified."

            dom = getattr(trust_assessment.uncertainty_assessment, "dominant_uncertainty", None)
            if not dom and getattr(trust_assessment.uncertainty_assessment, "active_uncertainties", None):
                dom = trust_assessment.uncertainty_assessment.active_uncertainties[0]
            dom_name = dom.value if hasattr(dom, "value") else (str(dom) if dom else "identified epistemic factors")

            claim_status = claim.status.value if hasattr(claim.status, "value") else str(getattr(claim, "status", "DERIVED"))
            claim_exp = ClaimExplanation(
                claim_id=c_id,
                statement=claim.statement,
                why_this_claim=why_text,
                supporting_evidence_ids=claim.supporting_evidence_ids,
                opposing_evidence_ids=claim.opposing_evidence_ids,
                citation_tokens=tokens,
                reasoning_path_summary=f"Derivation path spans {len(claim.derivation_step_ids)} DAG reasoning step(s).",
                trust_explanation=f"Calibrated with status: {claim_status}.",
                uncertainty_explanation=f"Dominant uncertainty: {dom_name}.",
                counterfactual_sensitivity=cf_sens_text,
                limitations=limitations
            )
            claim_explanations.append(claim_exp)

        # Step 8: Explanation Integrity Validation (Sub-Module 8.8)
        validation_report = self.validator.validate_explanation(
            trace=trace,
            trust_assessment=trust_assessment,
            evidence_set=evidence_set,
            narrative_steps=narrative_steps,
            claim_explanations=claim_explanations,
            attributions=attributions,
            citation_map=citation_map,
            conflict_explanations=conflict_explanations,
            multi_fidelity=multi_fidelity
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        trust_id = getattr(trust_assessment, "assessment_id", None) or getattr(trust_assessment, "trust_assessment_id", "trust_unknown")

        return ExplanationPackage(
            explanation_id=explanation_id,
            session_id=trace.session_id,
            plan_id=trace.plan_id,
            reasoning_trace_id=trace.reasoning_trace_id,
            trust_assessment_id=trust_id,
            primary_audience=audience or ExplanationAudience.TECHNICAL_RESEARCHER,
            narrative_steps=narrative_steps,
            multi_fidelity=multi_fidelity,
            claim_explanations=claim_explanations,
            evidence_attributions=attributions,
            citation_map=citation_map,
            conflict_explanations=conflict_explanations,
            uncertainty_narrative=uncertainty_narrative,
            counterfactual_explanations=counterfactual_explanations,
            limitations=limitations,
            validation=validation_report,
            generated_at=datetime.now(timezone.utc).isoformat(),
            processing_time_ms=elapsed_ms
        )
