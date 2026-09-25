"""
Query Log Model
Stores all user queries and their full Cogent responses for history and analytics.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, JSON, Integer, func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id = Column(String, ForeignKey("conversation_sessions.id", ondelete="SET NULL"), nullable=True, index=True)

    # Query Data
    original_query = Column(Text, nullable=False)
    processed_query = Column(Text, nullable=True)
    resolved_query = Column(Text, nullable=True)  # after clarification

    # Layer 1 Results
    intent = Column(String(50), nullable=True)
    query_type = Column(String(50), nullable=True)
    sufficiency_score = Column(Float, nullable=True)
    was_clarified = Column(String(10), default="false")  # "true" or "false"
    clarification_rounds = Column(Integer, default=0)
    ambiguity_report_json = Column(JSON, default=dict)
    structured_input_json = Column(JSON, default=dict)

    # Full Pipeline Results
    response_json = Column(JSON, default=dict)  # Complete CogentResponse
    confidence_score = Column(Float, nullable=True)
    evidence_count = Column(Integer, default=0)
    conflict_count = Column(Integer, default=0)

    # Feedback
    user_rating = Column(Integer, nullable=True)  # 1-5 stars
    user_feedback = Column(Text, nullable=True)

    # Timing
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="query_logs")

    def __repr__(self):
        return f"<QueryLog(id={self.id}, query={self.original_query[:50]}...)>"
