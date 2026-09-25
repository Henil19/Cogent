"""
Sub-Module 9.1: Response Planning & Master Response Assembler
Determines which validated information should appear and assembles the structural response plan.
Incorporates selective refusal and unanswerability framing when evidence is insufficient.
Research: Attribute First (ACL 2024), Unanswerability Evaluation for RAG (ACL 2025), RAG+ (EMNLP 2025).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.schemas.layer1 import StructuredUserInput
from app.schemas.layer7 import TrustAssessment, ConfidenceTier
from app.schemas.layer8 import ExplanationPackage, ExplanationAudience
from app.schemas.layer9 import ResponseSectionType


class PlannedSectionBlueprint(BaseModel):
    """Specification for an individual section to be assembled in the response."""
    section_id: str
    title: str
    section_type: ResponseSectionType
    is_mandatory: bool = True
    claims_to_include: List[str] = Field(default_factory=list)


class ResponsePlan(BaseModel):
    """Master structural response plan produced by Sub-Module 9.1."""
    blueprint_type: str  # FACTUAL_DEDUCTIVE, COMPARATIVE_DIALECTICAL, DECISION_EXECUTIVE, INSUFFICIENT_EVIDENCE
    active_audience: ExplanationAudience
    sections: List[PlannedSectionBlueprint]
    enable_conflict_widget: bool = False
    enable_trust_badge: bool = True
    enable_dag_explorer: bool = True
    enable_counterfactual_controls: bool = True
    is_insufficient_evidence: bool = False
    refusal_advisory: Optional[str] = None


class ResponsePlanner:
    """
    Sub-Module 9.1: Plans response section order, audience framing, and structural components.
    Does not select new evidence or alter facts; plans presentation of validated Layer 8 content.
    """

    def __init__(self, confidence_insufficiency_threshold: float = 0.40):
        self.confidence_insufficiency_threshold = confidence_insufficiency_threshold

    def plan_response(
        self,
        explanation_pkg: ExplanationPackage,
        trust_assessment: TrustAssessment,
        user_input: Optional[StructuredUserInput] = None,
        target_audience: Optional[ExplanationAudience] = None
    ) -> ResponsePlan:
        """
        Derives the presentation blueprint based on query intent, audience, and epistemic state.
        """
        # 1. Determine active audience
        audience = target_audience or getattr(explanation_pkg, "active_audience", ExplanationAudience.TECHNICAL_RESEARCHER)
        if user_input and not target_audience:
            user_intent = getattr(user_input, "intent", None)
            user_intent_str = str(user_intent).upper() if user_intent else ""
            if "EXECUTIVE" in user_intent_str or "DECISION" in user_intent_str:
                audience = ExplanationAudience.EXECUTIVE
            elif "LAYPERSON" in user_intent_str or "GENERAL" in user_intent_str:
                audience = ExplanationAudience.LAYPERSON
            elif "EXPERT" in user_intent_str:
                audience = ExplanationAudience.DOMAIN_EXPERT

        # 2. Check for Insufficient Evidence / Unanswerability
        conf = trust_assessment.global_confidence
        conf_tier = getattr(trust_assessment, "confidence_tier", None)
        is_insufficient = (
            conf < self.confidence_insufficiency_threshold
            or conf_tier == ConfidenceTier.PROVISIONAL
            or not explanation_pkg.claim_explanations
        )

        has_conflicts = len(explanation_pkg.conflict_explanations) > 0
        all_claim_ids = [c.claim_id for c in explanation_pkg.claim_explanations]

        if is_insufficient:
            return self._plan_insufficient_evidence_response(
                audience=audience,
                trust_assessment=trust_assessment,
                all_claim_ids=all_claim_ids
            )

        # 3. Check for Executive / Decision Support
        user_intent_cat = getattr(user_input, "intent", None)
        intent_name = str(getattr(user_intent_cat, "category", user_intent_cat)).upper() if user_intent_cat else ""
        is_executive = audience == ExplanationAudience.EXECUTIVE or "DECISION" in intent_name

        if is_executive:
            return self._plan_executive_response(
                audience=audience,
                all_claim_ids=all_claim_ids,
                has_conflicts=has_conflicts
            )

        # 4. Detect Comparative / Dialectical Intent
        is_comparative = "COMPARATIVE" in intent_name or has_conflicts
        if is_comparative:
            return self._plan_comparative_response(
                audience=audience,
                all_claim_ids=all_claim_ids,
                has_conflicts=has_conflicts
            )

        # 5. Default: Factual Deductive Blueprint
        return self._plan_factual_deductive_response(
            audience=audience,
            all_claim_ids=all_claim_ids,
            has_conflicts=has_conflicts
        )

    def _plan_insufficient_evidence_response(
        self,
        audience: ExplanationAudience,
        trust_assessment: TrustAssessment,
        all_claim_ids: List[str]
    ) -> ResponsePlan:
        """Plans structured refusal/hedging when evidence is insufficient (Peng et al. ACL 2025)."""
        sections = [
            PlannedSectionBlueprint(
                section_id="sec_insufficiency_advisory",
                title="Epistemic Status: Insufficient Evidence",
                section_type=ResponseSectionType.UNCERTAINTY_CAVEATS,
                is_mandatory=True
            ),
            PlannedSectionBlueprint(
                section_id="sec_partial_observations",
                title="Verified Partial Observations",
                section_type=ResponseSectionType.KEY_FINDINGS,
                is_mandatory=True,
                claims_to_include=all_claim_ids
            ),
            PlannedSectionBlueprint(
                section_id="sec_information_gaps",
                title="Information Gaps & Required Verification",
                section_type=ResponseSectionType.UNCERTAINTY_CAVEATS,
                is_mandatory=True
            ),
            PlannedSectionBlueprint(
                section_id="sec_references",
                title="References & Analyzed Evidence",
                section_type=ResponseSectionType.REFERENCES_FOOTNOTES,
                is_mandatory=True
            )
        ]
        c_tier = getattr(trust_assessment, "confidence_tier", None)
        tier_label = c_tier.value if hasattr(c_tier, "value") else str(c_tier or "LOW")
        return ResponsePlan(
            blueprint_type="INSUFFICIENT_EVIDENCE",
            active_audience=audience,
            sections=sections,
            enable_conflict_widget=False,
            enable_trust_badge=True,
            enable_dag_explorer=True,
            enable_counterfactual_controls=False,
            is_insufficient_evidence=True,
            refusal_advisory=(
                f"The available acquired evidence is insufficient to reach a conclusive determination "
                f"(Global confidence: {trust_assessment.global_confidence:.2f} [{tier_label}]). "
                f"Cogent will not speculate beyond verified evidence."
            )
        )

    def _plan_comparative_response(
        self,
        audience: ExplanationAudience,
        all_claim_ids: List[str],
        has_conflicts: bool
    ) -> ResponsePlan:
        """Plans multi-document comparative/dialectical synthesis (DeYoung et al. TACL 2024)."""
        sections = [
            PlannedSectionBlueprint(
                section_id="sec_bluf",
                title="Executive Overview & Multi-Criteria Trade-Off",
                section_type=ResponseSectionType.BLUF_SUMMARY,
                is_mandatory=True
            ),
            PlannedSectionBlueprint(
                section_id="sec_consensus",
                title="Consensus Findings Across Literature",
                section_type=ResponseSectionType.KEY_FINDINGS,
                is_mandatory=True,
                claims_to_include=all_claim_ids
            )
        ]
        if has_conflicts:
            sections.append(
                PlannedSectionBlueprint(
                    section_id="sec_dialectic",
                    title="Diverging Empirical Evidence & Contextual Discrepancies",
                    section_type=ResponseSectionType.CONFLICTING_EVIDENCE,
                    is_mandatory=True
                )
            )
        if audience == ExplanationAudience.TECHNICAL_RESEARCHER:
            sections.append(
                PlannedSectionBlueprint(
                    section_id="sec_reasoning",
                    title="Formal Comparative Reasoning Path",
                    section_type=ResponseSectionType.DETAILED_REASONING,
                    is_mandatory=True,
                    claims_to_include=all_claim_ids
                )
            )

        sections.append(
            PlannedSectionBlueprint(
                section_id="sec_caveats",
                title="Epistemic Boundaries & Evaluation Limits",
                section_type=ResponseSectionType.UNCERTAINTY_CAVEATS,
                is_mandatory=True
            )
        )

        if audience == ExplanationAudience.TECHNICAL_RESEARCHER:
            sections.append(
                PlannedSectionBlueprint(
                    section_id="sec_sensitivity",
                    title="Structural Sensitivity Analysis",
                    section_type=ResponseSectionType.SENSITIVITY_ANALYSIS,
                    is_mandatory=True
                )
            )

        sections.append(
            PlannedSectionBlueprint(
                section_id="sec_references",
                title="References & Evidence Attribution",
                section_type=ResponseSectionType.REFERENCES_FOOTNOTES,
                is_mandatory=True
            )
        )
        return ResponsePlan(
            blueprint_type="COMPARATIVE_DIALECTICAL",
            active_audience=audience,
            sections=sections,
            enable_conflict_widget=has_conflicts,
            enable_trust_badge=True,
            enable_dag_explorer=True,
            enable_counterfactual_controls=True,
            is_insufficient_evidence=False
        )

    def _plan_executive_response(
        self,
        audience: ExplanationAudience,
        all_claim_ids: List[str],
        has_conflicts: bool
    ) -> ResponsePlan:
        """Plans BLUF executive decision brief."""
        sections = [
            PlannedSectionBlueprint(
                section_id="sec_bluf",
                title="Bottom Line Up Front (BLUF)",
                section_type=ResponseSectionType.BLUF_SUMMARY,
                is_mandatory=True
            ),
            PlannedSectionBlueprint(
                section_id="sec_key_findings",
                title="Key Evidence & Empirical Takeaways",
                section_type=ResponseSectionType.KEY_FINDINGS,
                is_mandatory=True,
                claims_to_include=all_claim_ids
            ),
            PlannedSectionBlueprint(
                section_id="sec_caveats",
                title="Primary Caveats & Risk Drivers",
                section_type=ResponseSectionType.UNCERTAINTY_CAVEATS,
                is_mandatory=True
            ),
            PlannedSectionBlueprint(
                section_id="sec_references",
                title="References",
                section_type=ResponseSectionType.REFERENCES_FOOTNOTES,
                is_mandatory=True
            )
        ]
        return ResponsePlan(
            blueprint_type="DECISION_EXECUTIVE",
            active_audience=audience,
            sections=sections,
            enable_conflict_widget=has_conflicts,
            enable_trust_badge=True,
            enable_dag_explorer=True,
            enable_counterfactual_controls=True,
            is_insufficient_evidence=False
        )

    def _plan_factual_deductive_response(
        self,
        audience: ExplanationAudience,
        all_claim_ids: List[str],
        has_conflicts: bool
    ) -> ResponsePlan:
        """Standard factual deduction response plan."""
        sections = [
            PlannedSectionBlueprint(
                section_id="sec_findings",
                title="Synthesized Finding & Verification",
                section_type=ResponseSectionType.KEY_FINDINGS,
                is_mandatory=True,
                claims_to_include=all_claim_ids
            ),
            PlannedSectionBlueprint(
                section_id="sec_reasoning",
                title="Deductive Reasoning Chain",
                section_type=ResponseSectionType.DETAILED_REASONING,
                is_mandatory=True,
                claims_to_include=all_claim_ids
            ),
            PlannedSectionBlueprint(
                section_id="sec_caveats",
                title="Caveats & Epistemic Boundaries",
                section_type=ResponseSectionType.UNCERTAINTY_CAVEATS,
                is_mandatory=True
            ),
            PlannedSectionBlueprint(
                section_id="sec_references",
                title="References & Evidence Attribution",
                section_type=ResponseSectionType.REFERENCES_FOOTNOTES,
                is_mandatory=True
            )
        ]
        return ResponsePlan(
            blueprint_type="FACTUAL_DEDUCTIVE",
            active_audience=audience,
            sections=sections,
            enable_conflict_widget=has_conflicts,
            enable_trust_badge=True,
            enable_dag_explorer=True,
            enable_counterfactual_controls=True,
            is_insufficient_evidence=False
        )
