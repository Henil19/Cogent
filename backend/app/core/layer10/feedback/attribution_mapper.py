"""
Sub-Module 10.2: Feedback Attribution Mapper (Thakur et al., GEM 2025)
Maps user feedback (flagged sentences, star ratings, citation clicks) backwards
through presentation artifacts to exact claims, evidence IDs, and source documents.
"""

from typing import Dict, Any, Optional
from app.schemas.layer10 import UserFeedbackPayload, CogentExecutionTrace


class FeedbackAttributionMapper:
    """
    Traces feedback events back to upstream architectural origins:
    Presentation Badge -> Synthesized Claim -> Reasoning Step -> Evidence Item -> Source Document.
    """

    def __init__(self):
        pass

    def resolve_feedback_attribution(
        self,
        feedback: UserFeedbackPayload,
        trace: Optional[CogentExecutionTrace]
    ) -> UserFeedbackPayload:
        """
        Populates missing upstream attribution pointers in the feedback payload
        using the captured execution trace artifacts.
        """
        if not trace:
            return feedback

        l9_data = trace.layer9_response_payload or {}
        citation_registry = l9_data.get("citation_registry", {})

        # Normalize citation_registry
        reg_dict: Dict[str, Any] = {}
        if isinstance(citation_registry, list):
            for b in citation_registry:
                b_num = b.get("citation_number") if isinstance(b, dict) else getattr(b, "citation_number", None)
                if b_num is not None:
                    reg_dict[str(b_num)] = b
        elif isinstance(citation_registry, dict):
            reg_dict = citation_registry

        # If a citation number was targeted, resolve evidence and document URI
        if feedback.target_citation_number is not None:
            badge_info = reg_dict.get(str(feedback.target_citation_number)) or reg_dict.get(feedback.target_citation_number)
            if isinstance(badge_info, dict):
                feedback.target_document_uri = (
                    feedback.target_document_uri
                    or badge_info.get("source_uri")
                    or badge_info.get("document_uri")
                )
                feedback.target_claim_id = feedback.target_claim_id or badge_info.get("claim_id")
                feedback.target_evidence_id = feedback.target_evidence_id or badge_info.get("evidence_id")
            elif badge_info is not None:
                feedback.target_document_uri = (
                    feedback.target_document_uri
                    or getattr(badge_info, "source_uri", None)
                    or getattr(badge_info, "document_uri", None)
                )
                feedback.target_claim_id = feedback.target_claim_id or getattr(badge_info, "claim_id", None)
                feedback.target_evidence_id = feedback.target_evidence_id or getattr(badge_info, "evidence_id", None)

        # If a claim ID was targeted, resolve associated reasoning steps and evidence
        l6_data = trace.layer6_reasoning_meta or {}
        l8_data = trace.layer8_explanation_meta or {}

        if feedback.target_claim_id:
            # Check L8 claim explanations
            claim_explanations = l8_data.get("claim_explanations", [])
            for exp in claim_explanations:
                if isinstance(exp, dict) and exp.get("claim_id") == feedback.target_claim_id:
                    path = exp.get("reasoning_path_summary", [])
                    if path and not feedback.target_reasoning_step_id:
                        feedback.target_reasoning_step_id = str(path[-1])
                    break

        return feedback
