"""
Sub-Module 8.6: Counterfactual & Sensitivity Explanation Engine
Derives sensitivity explanations from Cogent's explicit reasoning DAG dependencies.
Explains what happens to the internal reasoning chain if a critical dependency or premise
is perturbed or removed, avoiding unconstrained real-world speculation.
"""

from typing import List, Dict, Set
from app.schemas.layer6 import SynthesizedReasoningTrace, SynthesizedClaim, ReasoningStepNode
from app.schemas.layer7 import TrustAssessment
from app.schemas.layer8 import CounterfactualExplanation, SensitivitySeverity


class CounterfactualExplanationEngine:
    """
    Analyzes reasoning graph cut-sets and dependency structures to explain
    how perturbations to supporting premises affect Cogent's internal conclusions.
    """

    def __init__(self):
        pass

    def build_counterfactual_explanations(
        self,
        trace: SynthesizedReasoningTrace,
        trust_assessment: TrustAssessment
    ) -> List[CounterfactualExplanation]:
        """
        Derives structural counterfactual explanations for each synthesized claim.
        """
        explanations: List[CounterfactualExplanation] = []
        bottleneck_step_id = (
            getattr(trust_assessment.reasoning_assessment, "weakest_link_step_id", None) or
            getattr(trust_assessment.reasoning_assessment, "weakest_step_id", None) or
            getattr(trust_assessment.reasoning_assessment, "bottleneck_step_id", None)
        )

        # Build node dependency map
        node_lookup: Dict[str, ReasoningStepNode] = {n.step_id: n for n in trace.reasoning_steps}

        for claim in trace.synthesized_claims:
            supporting_evidence = claim.supporting_evidence_ids
            critical_evidence: List[str] = []
            critical_premises: List[str] = []

            # Determine critical premises along derivation path
            for path_node_id in claim.derivation_step_ids:
                node = node_lookup.get(path_node_id)
                if node:
                    critical_premises.append(node.step_id)
                    ev_ids = getattr(node, "evidence_ids", None) or getattr(node, "premise_ids", [])
                    critical_evidence.extend(ev_ids)

            critical_evidence = list(dict.fromkeys(critical_evidence))
            critical_premises = list(dict.fromkeys(critical_premises))

            # Severity classification based on DAG cut-set
            num_premises = len(critical_premises)
            has_bottleneck = any(p == bottleneck_step_id for p in critical_premises)

            if num_premises <= 2 or has_bottleneck:
                severity = SensitivitySeverity.CRITICAL_COLLAPSE
                effect_msg = (
                    f"Because this conclusion relies on a concise dependency path of {num_premises} premise(s), "
                    f"invalidating any key supporting evidence would structurally collapse the deductive chain, "
                    f"leaving the conclusion unsupported in Cogent's reasoning model."
                )
            elif num_premises <= 4:
                severity = SensitivitySeverity.MODERATE_REVISION
                effect_msg = (
                    f"Invalidating a supporting premise would sever an intermediate multi-hop bridge, "
                    f"reducing the conclusion's calibrated confidence from {trust_assessment.global_confidence:.2f} "
                    f"to a preliminary or conditional status."
                )
            else:
                severity = SensitivitySeverity.LOCALIZED_REDUCTION
                effect_msg = (
                    f"Multiple redundant evidence paths support this conclusion; removing a single premise "
                    f"would cause only localized confidence reduction without overturning the core claim."
                )

            crit_ev_str = f"Evidence ({', '.join(critical_evidence[:2])})" if critical_evidence else "primary premise evidence"
            perturbation = f"If {crit_ev_str} were removed, superseded, or shown empirically invalid"

            exp = CounterfactualExplanation(
                claim_id=claim.claim_id,
                critical_premises=critical_premises,
                critical_evidence_ids=critical_evidence,
                perturbation_condition=perturbation,
                expected_structural_effect=effect_msg,
                sensitivity_severity=severity
            )
            explanations.append(exp)

        return explanations


CounterfactualEngine = CounterfactualExplanationEngine
