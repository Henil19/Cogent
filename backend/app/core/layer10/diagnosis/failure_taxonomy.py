"""
Sub-Module 10.5: Failure Taxonomy Definitions (GroUSE, Li et al.)
Defines the 9-tier failure taxonomy and decision boundaries for cognitive root-cause diagnosis.
"""

from app.schemas.layer10 import FailureCategory, FailureSeverity


TAXONOMY_DESCRIPTIONS = {
    FailureCategory.L1_AMBIGUITY_MISCLASSIFICATION: (
        "Layer 1 failed to detect conversational ambiguity, passing an underspecified "
        "or multi-intent query directly to planning without necessary clarification."
    ),
    FailureCategory.L2_DECOMPOSITION_FAILURE: (
        "Layer 2 generated insufficient sub-queries, missing critical comparative entities "
        "or establishing an overly shallow dependency graph."
    ),
    FailureCategory.L3_ACQUISITION_EXTRACTION_FAILURE: (
        "Layer 3 failed to acquire target source documents, encountered text extraction "
        "failures, or lost TROVE provenance coordinates."
    ),
    FailureCategory.L4_RETRIEVAL_MISS: (
        "Layer 4 hybrid retrieval failed to recall relevant candidate passages (Recall@K failure), "
        "or fusion ranking demoted critical evidence below cutoff."
    ),
    FailureCategory.L5_VERIFICATION_SELECTION_GAP: (
        "Layer 5 cross-encoder discarded valid evidence, failed to reconcile contradictory "
        "empirical findings, or extracted flawed atomic claims."
    ),
    FailureCategory.L6_REASONING_DEDUCTION_GAP: (
        "Layer 6 generated an unsupported intermediate claim, created cyclic dependencies, "
        "or drew deductive conclusions contradicted by premises."
    ),
    FailureCategory.L7_TRUST_MISCALIBRATION: (
        "Layer 7 assigned high confidence to an ungrounded claim (overconfidence gap), "
        "or failed to detect elevated hallucination risk."
    ),
    FailureCategory.L8_EXPLANATION_FIDELITY_FAILURE: (
        "Layer 8 failed explanation audit gates, inverted reasoning step order, "
        "or distorted uncertainty boundaries during narrative synthesis."
    ),
    FailureCategory.L9_PRESENTATION_INVARIANCE_FAILURE: (
        "Layer 9 generated orphan citation tags, introduced ungrounded text during response "
        "assembly, or violated epistemic invariance during audience view switching."
    ),
    FailureCategory.NO_FAILURE_DETECTED: (
        "Execution completed successfully; all factual grounding, reasoning, and presentation "
        "fidelity invariants were satisfied."
    )
}
