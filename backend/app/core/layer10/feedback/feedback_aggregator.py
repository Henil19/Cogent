"""
Sub-Module 10.2: User Feedback & Interaction Aggregator
Captures explicit user assessments (thumbs, ratings, corrections) and implicit
behavioral signals (clicks, hovers, exports) without confusing engagement with correctness.
"""

from typing import List, Dict, Any, Optional
from app.schemas.layer10 import UserFeedbackPayload, FeedbackType, CogentExecutionTrace
from app.core.layer10.feedback.attribution_mapper import FeedbackAttributionMapper


class UserFeedbackAggregator:
    """
    Collects, attributes, and categorizes user interaction signals.
    Enforces the principle that clicks and dwell times are behavioral metrics,
    not definitive proofs of factual correctness.
    """

    def __init__(self):
        self._feedback_store: List[UserFeedbackPayload] = []
        self._attribution_mapper = FeedbackAttributionMapper()

    def record_feedback(
        self,
        feedback: UserFeedbackPayload,
        trace: Optional[CogentExecutionTrace] = None
    ) -> UserFeedbackPayload:
        """Enriches and persists a user feedback event."""
        enriched = self._attribution_mapper.resolve_feedback_attribution(feedback, trace)
        self._feedback_store.append(enriched)
        return enriched

    def get_feedback_for_execution(self, execution_id: str) -> List[UserFeedbackPayload]:
        """Retrieves all feedback payloads associated with a specific execution."""
        return [fb for fb in self._feedback_store if fb.execution_id == execution_id]

    def compute_interaction_summary(self, execution_id: str) -> Dict[str, Any]:
        """
        Summarizes explicit ratings and behavioral engagement metrics.
        Explicitly separates behavioral interactions from factual correctness.
        """
        feedbacks = self.get_feedback_for_execution(execution_id)
        explicit_positive = 0
        explicit_negative = 0
        claim_flags = 0
        fact_corrections = 0

        citation_clicks = 0
        citation_hovers = 0
        dag_inspections = 0
        view_switches = 0
        exports = 0

        for fb in feedbacks:
            if fb.feedback_type == FeedbackType.THUMBS_UP:
                explicit_positive += 1
            elif fb.feedback_type == FeedbackType.THUMBS_DOWN:
                explicit_negative += 1
            elif fb.feedback_type == FeedbackType.CLAIM_FLAG:
                claim_flags += 1
            elif fb.feedback_type == FeedbackType.FACT_CORRECTION:
                fact_corrections += 1
            elif fb.feedback_type == FeedbackType.CITATION_CLICK:
                citation_clicks += 1
            elif fb.feedback_type == FeedbackType.CITATION_HOVER:
                citation_hovers += 1
            elif fb.feedback_type == FeedbackType.DAG_NODE_INSPECT:
                dag_inspections += 1
            elif fb.feedback_type == FeedbackType.AUDIENCE_TAB_SWITCH:
                view_switches += 1
            elif fb.feedback_type == FeedbackType.EXPORT_CLICK:
                exports += 1

        is_explicitly_disputed = (explicit_negative > 0 or claim_flags > 0 or fact_corrections > 0)
        is_explicitly_endorsed = (explicit_positive > 0 and not is_explicitly_disputed)

        return {
            "execution_id": execution_id,
            "explicit_feedback": {
                "positive_ratings": explicit_positive,
                "negative_ratings": explicit_negative,
                "claim_flags": claim_flags,
                "fact_corrections": fact_corrections,
                "is_explicitly_disputed": is_explicitly_disputed,
                "is_explicitly_endorsed": is_explicitly_endorsed,
            },
            "implicit_behavioral_signals": {
                "citation_clicks": citation_clicks,
                "citation_hovers": citation_hovers,
                "dag_inspections": dag_inspections,
                "audience_switches": view_switches,
                "exports": exports,
                "behavioral_engagement_score": min(
                    1.0,
                    (citation_clicks * 0.3 + dag_inspections * 0.3 + citation_hovers * 0.1 + exports * 0.3)
                )
            }
        }
