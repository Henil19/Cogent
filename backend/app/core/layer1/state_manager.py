"""
Sub-Module 1.3: Conversation State Manager
Maintains multi-turn conversation memory, context carryover, coreference resolution,
and topic drift detection.
Research basis: P4 (Multi-turn CIS - WWW 2025), P9 (CoSearchAgent - arXiv 2024)
"""

import re
import uuid
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from app.models.conversation import ConversationSession, ConversationTurn


class ConversationStateManager:
    """Manages active session turns, contextualizes elliptical queries, and detects topic drift."""

    COREFERENCE_PRONOUNS = [
        r"\b(it|this|that|these|those|its|their|the algorithm|the model|the method|the paper|the system)\b"
    ]

    def get_or_create_conversation(
        self,
        db: Session,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> ConversationSession:
        """Fetch existing conversation or instantiate a new session."""
        if conversation_id:
            conv = db.query(ConversationSession).filter(ConversationSession.id == conversation_id).first()
            if conv:
                return conv

        new_id = conversation_id or str(uuid.uuid4())
        conv = ConversationSession(
            id=new_id,
            user_id=user_id,
            title=title or "Research Session",
            context_summary="",
            clarification_turns_count=0,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    def contextualize_query(
        self,
        db: Session,
        conversation: ConversationSession,
        raw_query: str,
        clarification_response: Optional[str] = None,
    ) -> Tuple[str, int, Dict[str, Any]]:
        """
        Integrate prior turns or clarification responses into the active query.
        Detects topic drift: if the query introduces a completely new domain, avoids stale context carryover.
        Returns:
            (reformed_query, current_turn_number, context_metadata)
        """
        recent_turns: List[ConversationTurn] = (
            db.query(ConversationTurn)
            .filter(ConversationTurn.conversation_id == conversation.id)
            .order_by(ConversationTurn.turn_number.desc())
            .limit(3)
            .all()
        )
        turn_number = (recent_turns[0].turn_number + 1) if recent_turns else 1

        prior_turns_data = []
        for t in recent_turns:
            # Extract only lightweight metadata, NEVER the full recursive layer1_data payload!
            prior_q = None
            target_asp = None
            if isinstance(t.layer1_data, dict):
                c_info = t.layer1_data.get("clarification")
                if isinstance(c_info, dict):
                    prior_q = c_info.get("question")
                    target_asp = c_info.get("target_aspect")

            prior_turns_data.append({
                "turn_number": t.turn_number,
                "user_query": t.user_query,
                "clarification_question": t.clarification_question or prior_q,
                "user_clarification_response": t.user_clarification_response,
                "clarification_rounds": t.clarification_rounds,
                "target_aspect": target_asp,
            })

        context_metadata: Dict[str, Any] = {
            "conversation_id": conversation.id,
            "turn_number": turn_number,
            "clarification_turns_count": conversation.clarification_turns_count,
            "coreference_resolved": False,
            "topic_drift_detected": False,
            "reformulated": False,
            "prior_turns_count": len(recent_turns),
            "prior_turns": prior_turns_data,
        }

        reformed_query = raw_query

        # Case 1: User is submitting a direct clarification response
        if clarification_response:
            reformed_query = f"{raw_query} [Clarification: {clarification_response.strip()}]"
            context_metadata["reformulated"] = True
            return reformed_query, turn_number, context_metadata

        # Case 2: Multi-turn reasoning
        if recent_turns:
            last_turn = recent_turns[0]
            last_user_query = last_turn.user_query

            # Check for topic drift
            is_drift = self._detect_topic_drift(raw_query, last_user_query)
            if is_drift:
                context_metadata["topic_drift_detected"] = True
                return reformed_query, turn_number, context_metadata

            # Coreference resolution heuristics
            has_coreference = any(re.search(pat, raw_query.lower()) for pat in self.COREFERENCE_PRONOUNS)
            is_very_short_followup = len(raw_query.split()) <= 4 and not raw_query.endswith("?")

            if has_coreference or is_very_short_followup:
                reformed_query = f"{raw_query} (context: {last_user_query})"
                context_metadata["coreference_resolved"] = True
                context_metadata["reformulated"] = True

        return reformed_query, turn_number, context_metadata

    def _detect_topic_drift(self, current_query: str, last_query: str) -> bool:
        """
        Heuristic topic drift detector:
        If current query is a long, self-contained question (> 8 words) with no pronouns,
        and shares 0 informative content tokens with the last query, topic drift is flagged.
        """
        words_curr = set(re.findall(r"\b[a-z]{4,}\b", current_query.lower()))
        words_last = set(re.findall(r"\b[a-z]{4,}\b", last_query.lower()))

        has_pronoun = any(re.search(pat, current_query.lower()) for pat in self.COREFERENCE_PRONOUNS)
        if has_pronoun:
            return False

        if len(current_query.split()) >= 8:
            common_tokens = words_curr.intersection(words_last)
            stopwords = {"what", "which", "where", "about", "could", "would", "explain", "compare"}
            meaningful_common = [w for w in common_tokens if w not in stopwords]
            if len(meaningful_common) == 0:
                return True
        return False

    def record_turn(
        self,
        db: Session,
        conversation_id: str,
        turn_number: int,
        user_query: str,
        layer1_data: Dict[str, Any],
        was_clarified: bool = False,
        clarification_question: Optional[str] = None,
        user_clarification_response: Optional[str] = None,
        clarification_rounds: int = 0,
    ) -> ConversationTurn:
        """Record turn metadata into database for ongoing contextual memory."""
        turn = ConversationTurn(
            conversation_id=conversation_id,
            turn_number=turn_number,
            user_query=user_query,
            layer1_data=layer1_data,
            was_clarified=was_clarified,
            clarification_question=clarification_question,
            user_clarification_response=user_clarification_response,
            clarification_rounds=clarification_rounds,
        )
        db.add(turn)
        db.commit()
        db.refresh(turn)
        return turn
