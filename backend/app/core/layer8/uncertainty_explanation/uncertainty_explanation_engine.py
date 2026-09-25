"""
Sub-Module 8.4: Trust, Conflict & Uncertainty Explanation Engine
Translates Layer 7's trust and uncertainty assessments into human-understandable explanations.
Explains why confidence is calibrated as it is, what remains uncertain across the 5 dimensions,
and what actions would reduce epistemic uncertainty.
"""

from typing import Tuple, List
from app.schemas.layer7 import TrustAssessment, UncertaintyCategory


class UncertaintyExplanationEngine:
    """
    Translates Layer 7 trust indices, uncertainty components, and risk factors into
    transparent, human-readable prose and explicit limitations.
    """

    def __init__(self):
        pass

    def explain_uncertainty(
        self,
        trust_assessment: TrustAssessment
    ) -> Tuple[str, List[str]]:
        """
        Synthesizes an uncertainty narrative and extracted list of limitations.
        Returns:
            (uncertainty_narrative, limitations_list)
        """
        gti = trust_assessment.global_trust_index
        conf = trust_assessment.global_confidence

        risk_level = getattr(trust_assessment, "risk_level", None)
        if not risk_level:
            if gti >= 0.80:
                risk_level = "LOW"
            elif gti >= 0.60:
                risk_level = "MEDIUM"
            else:
                risk_level = "HIGH"

        u_assess = trust_assessment.uncertainty_assessment
        overall_u = getattr(u_assess, "overall_uncertainty", getattr(u_assess, "total_uncertainty", 0.25))
        active_cats = getattr(u_assess, "active_uncertainties", [])
        active_cat_names = [c.value if hasattr(c, "value") else str(c) for c in active_cats]

        sections: List[str] = []
        limitations: List[str] = list(getattr(trust_assessment, "key_limitations", []))

        # 1. Overall Epistemic Calibrated Trust
        trust_tier_desc = "High" if gti >= 0.80 else ("Moderate" if gti >= 0.60 else "Low")
        conf_tier_desc = "High" if conf >= 0.80 else ("Moderate" if conf >= 0.60 else "Preliminary")

        overview = (
            f"**Epistemic Trust Assessment**: Overall Global Trust Index is calibrated at "
            f"**{gti:.2f} ({trust_tier_desc})** with an empirical confidence probability of "
            f"**{conf:.2f} ({conf_tier_desc})**. Systemic risk profile is categorized as **{risk_level}**."
        )
        sections.append(overview)

        # 2. Deconstruction of the 5 Separately Tracked Uncertainty Dimensions
        dim_explanations: List[str] = []

        # Coverage
        u_cov = getattr(u_assess, "coverage_uncertainty", 0.15 if "INSUFFICIENT_EVIDENCE" in active_cat_names else 0.05)
        if u_cov > 0.10 or "INSUFFICIENT_EVIDENCE" in active_cat_names:
            dim_explanations.append(
                f"- **Information Coverage Deficit ({u_cov:.2f})**: Certain operational sub-aspects or specific parameters "
                f"lack exhaustive representation in the acquired corpus."
            )
            limitations.append("Incomplete corpus coverage across all operational evaluation dimensions.")
        else:
            dim_explanations.append(f"- **Information Coverage ({u_cov:.2f})**: Evidence coverage across targeted sub-queries is robust.")

        # Conflict
        u_conf = getattr(u_assess, "conflict_uncertainty", 0.25 if "CONFLICTING_EVIDENCE" in active_cat_names else 0.05)
        if u_conf > 0.10 or "CONFLICTING_EVIDENCE" in active_cat_names:
            dim_explanations.append(
                f"- **Empirical Contradiction / Conflict ({u_conf:.2f})**: Significant tension exists between "
                f"competing evaluations or differing testing conditions across primary sources."
            )
            limitations.append("Contradictory findings across sources prevent unconditional generalization.")
        else:
            dim_explanations.append(f"- **Cross-Source Consensus ({u_conf:.2f})**: Low conflict observed; reporting across sources is consistent.")

        # Source
        u_src = getattr(u_assess, "source_uncertainty", 0.15 if "WEAK_SOURCE" in active_cat_names else 0.05)
        if u_src > 0.10 or "WEAK_SOURCE" in active_cat_names:
            dim_explanations.append(
                f"- **Source Authority & Provenance ({u_src:.2f})**: Portion of acquired evidence derives from non-peer-reviewed "
                f"or secondary publications, introducing authority variance."
            )
            limitations.append("Reliance on secondary or pre-print literature introduces source authority variance.")
        else:
            dim_explanations.append(f"- **Source Authority ({u_src:.2f})**: Sourced predominantly from verified institutional or peer-reviewed literature.")

        # Reasoning
        u_reas = getattr(u_assess, "reasoning_uncertainty", 0.15 if ("LONG_REASONING_CHAIN" in active_cat_names or "MISSING_PREMISE" in active_cat_names) else 0.05)
        if u_reas > 0.10 or "LONG_REASONING_CHAIN" in active_cat_names or "MISSING_PREMISE" in active_cat_names:
            dim_explanations.append(
                f"- **Reasoning & Deductive Chain ({u_reas:.2f})**: Multi-hop inferential dependency contains a bottleneck "
                f"premise with lower relative grounding."
            )
            limitations.append("Multi-hop deductive derivation depends on intermediate bridge assumptions.")
        else:
            dim_explanations.append(f"- **Reasoning Integrity ({u_reas:.2f})**: The deductive chain maintains strong premise-to-conclusion continuity.")

        # Temporal
        u_temp = getattr(u_assess, "temporal_uncertainty", 0.15 if "OUTDATED_EVIDENCE" in active_cat_names else 0.05)
        if u_temp > 0.10 or "OUTDATED_EVIDENCE" in active_cat_names:
            dim_explanations.append(
                f"- **Temporal Recency Decay ({u_temp:.2f})**: Older literature baselines may not reflect recent "
                f"advancements in rapidly evolving domain architectures."
            )
            limitations.append("Literature baselines reflect temporal decay relative to rapid field advancement.")
        else:
            dim_explanations.append(f"- **Temporal Recency ({u_temp:.2f})**: Literature reflects contemporary findings within domain half-life.")

        sections.append("**Uncertainty Deconstruction**:\n" + "\n".join(dim_explanations))

        # 3. Dominant Factor and Mitigation Pathways
        dom = getattr(u_assess, "dominant_uncertainty", None)
        if dom:
            dom_name = dom.value if hasattr(dom, "value") else str(dom)
        elif active_cat_names:
            dom_name = active_cat_names[0]
        else:
            dom_name = "MINIMAL_RESIDUAL_UNCERTAINTY"

        diag_explanation = getattr(u_assess, "explanation_of_uncertainty", "")
        recs = getattr(u_assess, "mitigation_recommendations", [])
        if not recs and limitations:
            recs = ["Conduct standardized replication experiments across identical benchmark harnesses."]

        rec_text = "\n".join([f"- {rec}" for rec in recs]) if recs else "- Acquire targeted replication studies under identical benchmark conditions."

        pathways = (
            f"**Dominant Uncertainty Driver**: `{dom_name}`.\n\n"
            f"**Diagnostic Summary**: {diag_explanation or 'Evaluated evidence provides sufficient basis with qualified uncertainty.'}\n\n"
            f"**Actionable Uncertainty Mitigation Pathways**:\n{rec_text}"
        )
        sections.append(pathways)

        # Deduplicate limitations
        limitations = list(dict.fromkeys(limitations))
        narrative = "\n\n".join(sections)
        return narrative, limitations
