"""
Execution Trace Model
Persists end-to-end cognitive execution traces, layer telemetry, and detailed failure diagnostics.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, JSON, Integer, func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class ExecutionTrace(Base):
    __tablename__ = "execution_traces"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id = Column(String, ForeignKey("query_logs.id", ondelete="SET NULL"), nullable=True, index=True)
    session_id = Column(String, ForeignKey("conversation_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Status and Failure Telemetry
    execution_status = Column(String(50), nullable=False, default="SUCCESS", index=True)  # SUCCESS, PARTIAL, FAILED, RUNNING
    failure_code = Column(String(100), nullable=True)  # e.g., INSUFFICIENT_EVIDENCE, RETRIEVAL_FAILURE
    failure_message = Column(Text, nullable=True)
    failed_layer = Column(String(50), nullable=True)  # e.g., Layer 4, Layer 5

    # Configuration and Query
    raw_query = Column(Text, nullable=False)
    config_hash = Column(String(64), nullable=True)

    # Timestamps & Operational Latency
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_latency_ms = Column(Float, default=0.0)

    # Resource Accounting
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)

    # Layer Summaries and Detailed Trace Artifacts
    layer_summaries_json = Column(JSON, default=dict)
    full_trace_json = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ExecutionTrace(id={self.id}, status={self.execution_status}, failed_layer={self.failed_layer})>"
