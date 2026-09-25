"""
Telemetry & Feedback API Router
Endpoints for logging human evaluation feedback, inspecting Layer 10 cognitive traces, and auditing system analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.feedback import UserFeedback
from app.models.execution_trace import ExecutionTrace
from app.models.query import QueryLog
from app.api.deps import get_optional_current_user
from app.models.user import User

router = APIRouter(prefix="/telemetry", tags=["Telemetry & Feedback"])


class FeedbackSubmissionRequest(BaseModel):
    query_id: str
    rating: Optional[int] = Field(None, ge=1, le=5, description="1-5 star user satisfaction rating")
    is_factual: Optional[bool] = Field(None, description="User verified factual correctness flag")
    citation_accurate: Optional[bool] = Field(None, description="User verified citation validity flag")
    feedback_text: Optional[str] = Field(None, max_length=2000, description="Optional qualitative feedback")
    claim_corrections: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class ExecutionTraceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    query_id: Optional[str] = None
    session_id: Optional[str] = None
    execution_status: str
    failure_code: Optional[str] = None
    raw_query: str
    total_latency_ms: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    request: FeedbackSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Submits user feedback and empirical annotations for a specific Cogent query."""
    feedback = UserFeedback(
        query_id=request.query_id,
        user_id=current_user.id if current_user else None,
        rating=request.rating,
        is_factual=request.is_factual,
        citation_accurate=request.citation_accurate,
        feedback_text=request.feedback_text,
        claim_corrections_json=request.claim_corrections,
    )
    db.add(feedback)

    # Also update QueryLog rating if present
    query_log = db.query(QueryLog).filter(QueryLog.id == request.query_id).first()
    if query_log:
        if request.rating is not None:
            query_log.user_rating = request.rating
        if request.feedback_text:
            query_log.user_feedback = request.feedback_text

    db.commit()
    return {
        "api_version": "v1",
        "schema_version": "1.0.0",
        "status": "RECORDED",
        "message": "Feedback recorded successfully.",
    }


@router.get("/traces", response_model=List[ExecutionTraceSummary])
def list_execution_traces(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Lists recent execution traces for the Layer 10 analytics inspector."""
    traces = db.query(ExecutionTrace).order_by(ExecutionTrace.started_at.desc()).limit(limit).all()
    return traces


@router.get("/traces/{trace_id}", response_model=Dict[str, Any])
def get_execution_trace_detail(
    trace_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves full cognitive telemetry, layer outputs, and failure artifacts for a trace."""
    trace = db.query(ExecutionTrace).filter(ExecutionTrace.id == trace_id).first()
    if not trace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution trace not found.")
    
    return {
        "api_version": "v1",
        "schema_version": "1.0.0",
        "id": trace.id,
        "query_id": trace.query_id,
        "session_id": trace.session_id,
        "execution_status": trace.execution_status,
        "failure_code": trace.failure_code,
        "failure_message": trace.failure_message,
        "failed_layer": trace.failed_layer,
        "raw_query": trace.raw_query,
        "started_at": trace.started_at.isoformat() if trace.started_at else None,
        "completed_at": trace.completed_at.isoformat() if trace.completed_at else None,
        "total_latency_ms": trace.total_latency_ms,
        "prompt_tokens": trace.prompt_tokens,
        "completion_tokens": trace.completion_tokens,
        "total_tokens": trace.total_tokens,
        "total_cost_usd": trace.total_cost_usd,
        "layer_summaries": trace.layer_summaries_json,
        "full_trace": trace.full_trace_json,
    }
