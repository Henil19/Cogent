"""
User Feedback Model
Stores ratings, claim evaluations, and qualitative annotations for Cogent inquiries.
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id = Column(String, ForeignKey("query_logs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    rating = Column(Integer, nullable=True)  # 1 to 5
    is_factual = Column(Boolean, nullable=True)  # True/False flag
    citation_accurate = Column(Boolean, nullable=True)
    feedback_text = Column(Text, nullable=True)
    claim_corrections_json = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<UserFeedback(id={self.id}, query={self.query_id}, rating={self.rating})>"
