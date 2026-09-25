"""
Conversation Session Models
Tracks multi-turn conversation state for Layer 1 context management.
Research basis: P4 (Query Understanding in CIS), P9 (CoSearchAgent)
"""

# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, func
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class ConversationSession(Base):
    """
    Represents a multi-turn conversation session between user and Cogent.
    Tracks active entities, constraints, and topic trajectory across turns.
    """
    __tablename__ = "conversation_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), default="Research Session")
    turn_count = Column(Integer, default=0)
    clarification_turns_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Conversation State (serialized)
    context_summary = Column(Text, default="")
    active_entities_json = Column(JSON, default=list)  # currently discussed entities
    active_constraints_json = Column(JSON, default=list)  # carried-over constraints
    topic_trajectory_json = Column(JSON, default=list)  # how topic evolved

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="conversation_sessions")
    turns = relationship(
        "ConversationTurn",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ConversationTurn.turn_number"
    )

    def __repr__(self):
        return f"<ConversationSession(id={self.id}, turns={self.turn_count})>"


# Alias for backward and forward compatibility
Conversation = ConversationSession


class ConversationTurn(Base):
    """
    Individual turn within a conversation session.
    Stores raw input, processed output, ambiguity analysis, and clarification data.
    """
    __tablename__ = "conversation_turns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversation_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_number = Column(Integer, nullable=False)

    # Input & Queries
    user_query = Column(Text, nullable=False)
    processed_input = Column(Text, nullable=True)

    # Layer 1 Analysis
    intent = Column(String(50), nullable=True)
    query_type = Column(String(50), nullable=True)
    entities_json = Column(JSON, default=list)
    constraints_json = Column(JSON, default=list)
    ambiguity_report_json = Column(JSON, default=dict)
    sufficiency_score = Column(Float, nullable=True)

    # Clarification
    was_clarified = Column(Boolean, default=False)
    clarification_question = Column(Text, nullable=True)
    user_clarification_response = Column(Text, nullable=True)
    clarification_rounds = Column(Integer, default=0)

    # Layer 1 full snapshot
    layer1_data = Column(JSON, default=dict)

    # Output
    structured_output_json = Column(JSON, default=dict)
    processing_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ConversationSession", back_populates="turns")

    @property
    def raw_input(self) -> str:
        return self.user_query

    @property
    def session_id(self) -> str:
        return self.conversation_id

    def __repr__(self):
        return f"<ConversationTurn(conversation_id={self.conversation_id}, turn={self.turn_number})>"


class AnalyticsEvent(Base):
    """
    General-purpose analytics event tracking (Layer 10).
    """
    __tablename__ = "analytics_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_data_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<AnalyticsEvent(type={self.event_type})>"
