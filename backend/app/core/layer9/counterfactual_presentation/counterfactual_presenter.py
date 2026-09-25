"""
Sub-Module 9.7: Counterfactual & 'What-If' Presentation Engine
Formats Layer 8's precomputed structural DAG cut-set sensitivity into interactive premise simulation controls.
Visualizes structural dependency impacts without recalculating confidence in the UI presentation layer.
Research: Counterfactual Explanations Survey (ACM CSUR 2024).
"""

from typing import List
from app.schemas.layer8 import ExplanationPackage, CounterfactualExplanation
from app.schemas.layer9 import CounterfactualControlPayload


class CounterfactualPresenter:
    """
    Sub-Module 9.7: Prepares interactive premise invalidation control contracts for the UI.
    Does NOT recalculate trust; presents precomputed Layer 8 structural sensitivity.
    """

    def __init__(self):
        pass

    def build_counterfactual_controls(
        self,
        explanation_pkg: ExplanationPackage
    ) -> List[CounterfactualControlPayload]:
        """
        Transforms Layer 8 counterfactual explanations into frontend toggle controls.
        """
        controls: List[CounterfactualControlPayload] = []

        for idx, cf in enumerate(explanation_pkg.counterfactual_explanations):
            # Format human-friendly toggle label without raw backend hash codes
            prem_label = f"Primary Supporting Premise {idx + 1}"
            prem_id = f"premise_{idx + 1}"

            # Clean perturbation condition of raw ev_chk / step_leaf hashes
            perturbation = cf.perturbation_condition
            if "ev_chk_" in perturbation or "step_leaf" in perturbation or "syn_leaf" in perturbation:
                perturbation = f"If primary literature premise {idx + 1} were questioned, revised, or unsupported"

            control = CounterfactualControlPayload(
                premise_id=prem_id,
                label=prem_label,
                perturbation_condition=perturbation,
                structural_impact_description=cf.expected_structural_effect,
                sensitivity_severity=cf.sensitivity_severity,
                affected_claim_ids=[f"conclusion_{idx + 1}"]
            )
            controls.append(control)

        return controls
