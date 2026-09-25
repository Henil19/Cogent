"""
Sub-Module 10.3: Reasoning Soundness & Dialectical Balance Evaluator
Audits the structural validity of the Layer 6 reasoning DAG and evaluates
the dialectical presentation fairness between opposing viewpoints.
"""

from typing import List, Dict, Any, Tuple


class ReasoningEvaluator:
    """
    Evaluates:
    1. Reasoning Soundness: Absence of orphaned deductive steps, cycles, or ungrounded intermediate claims.
    2. Dialectical Balance: Equal representation of thesis and antithesis evidence without forced consensus.
    """

    def __init__(self):
        pass

    def evaluate_reasoning_soundness(
        self,
        reasoning_trace_meta: Dict[str, Any]
    ) -> float:
        """Evaluates DAG soundness score [0.0, 1.0]."""
        if not reasoning_trace_meta:
            return 1.0

        steps = reasoning_trace_meta.get("reasoning_steps", [])
        if not steps:
            return 1.0

        step_ids = {s.get("step_id") for s in steps if isinstance(s, dict)}
        valid_transitions = 0
        total_transitions = 0

        for s in steps:
            if not isinstance(s, dict):
                continue
            deps = s.get("dependent_step_ids", [])
            for dep in deps:
                total_transitions += 1
                if dep in step_ids:
                    valid_transitions += 1

        if total_transitions == 0:
            return 1.0

        return round(valid_transitions / total_transitions, 3)

    def evaluate_dialectical_balance(
        self,
        conflicts: List[Dict[str, Any]],
        rendered_sections: List[Dict[str, Any]]
    ) -> float:
        """
        Evaluates dialectical parity [0.0, 1.0].
        If conflicts exist, checks whether conflicting viewpoints received side-by-side coverage.
        """
        if not conflicts:
            return 1.0  # No dialectical conflict existed, parity is vacuously satisfied

        conflict_sec_exists = any(
            s.get("section_type") == "CONFLICTING_EVIDENCE" for s in rendered_sections
        )

        balanced_conflicts = 0
        for conf in conflicts:
            if not isinstance(conf, dict):
                continue
            thesis = conf.get("thesis_statement") or conf.get("point_of_disagreement")
            antithesis = conf.get("antithesis_statement")
            if thesis and antithesis:
                balanced_conflicts += 1

        parity_ratio = balanced_conflicts / len(conflicts) if conflicts else 1.0

        if conflict_sec_exists:
            return round(min(1.0, parity_ratio * 1.0), 3)
        else:
            return round(parity_ratio * 0.7, 3)
