"""
Sessions API Router
Endpoints for creating, listing, inspecting, and deleting research sessions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.conversation import ConversationSession, ConversationTurn
from app.models.query import QueryLog
from app.models.execution_trace import ExecutionTrace
from app.models.user import User
from app.api.deps import get_optional_current_user

router = APIRouter(prefix="/sessions", tags=["Sessions"])


class SessionCreateRequest(BaseModel):
    title: Optional[str] = "Research Session"


class SessionSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    turn_count: int
    clarification_turns_count: int
    is_active: bool
    context_summary: Optional[str] = ""
    created_at: Optional[datetime] = None
    last_active: Optional[datetime] = None
    updated_at: Optional[str] = None
    query_count: int = 0
    last_query_preview: Optional[str] = None
    confidence_score: Optional[float] = None


class SessionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    turn_count: int
    clarification_turns_count: int
    is_active: bool
    context_summary: Optional[str] = ""
    created_at: Optional[datetime] = None
    last_active: Optional[datetime] = None
    queries: List[Dict[str, Any]] = Field(default_factory=list)


@router.post("", response_model=SessionSummaryResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    request: SessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Creates a new research session."""
    session = ConversationSession(
        title=request.title or "Research Session",
        user_id=current_user.id if current_user else None,
        turn_count=0,
        clarification_turns_count=0,
        is_active=True,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionSummaryResponse(
        id=session.id,
        title=session.title,
        turn_count=session.turn_count,
        clarification_turns_count=session.clarification_turns_count,
        is_active=session.is_active,
        context_summary=session.context_summary or "",
        created_at=session.created_at,
        last_active=session.last_active,
        updated_at=session.last_active.isoformat() if session.last_active else (session.created_at.isoformat() if session.created_at else None),
        query_count=0,
        last_query_preview="",
        confidence_score=None,
    )


@router.get("", response_model=List[SessionSummaryResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    limit: int = 50,
):
    """Lists recent research sessions with query summary information."""
    query = db.query(ConversationSession)
    if current_user:
        query = query.filter((ConversationSession.user_id == current_user.id) | (ConversationSession.user_id.is_(None)))
    sessions = query.order_by(ConversationSession.last_active.desc()).limit(limit).all()
    
    results = []
    for s in sessions:
        logs = db.query(QueryLog).filter(QueryLog.session_id == s.id).order_by(QueryLog.created_at.desc()).all()
        q_count = len(logs)
        latest_log = logs[0] if logs else None
        last_preview = latest_log.original_query if latest_log else (s.title or "")
        conf = latest_log.confidence_score if latest_log else None

        results.append(
            SessionSummaryResponse(
                id=s.id,
                title=s.title or (last_preview[:60] if last_preview else "Research Session"),
                turn_count=s.turn_count,
                clarification_turns_count=s.clarification_turns_count,
                is_active=s.is_active,
                context_summary=s.context_summary or "",
                created_at=s.created_at,
                last_active=s.last_active,
                updated_at=s.last_active.isoformat() if s.last_active else (s.created_at.isoformat() if s.created_at else None),
                query_count=q_count,
                last_query_preview=last_preview,
                confidence_score=conf,
            )
        )
    return results


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_all_sessions(
    db: Session = Depends(get_db),
):
    """Clears all sessions, traces, and queries to provide a clean history state."""
    db.query(ExecutionTrace).delete()
    db.query(QueryLog).delete()
    db.query(ConversationTurn).delete()
    db.query(ConversationSession).delete()
    db.commit()
    return None


@router.get("/{session_id}/latest-response")
def get_session_latest_response(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Returns the most recent query response for a session to restore the investigation view."""
    query_log = (
        db.query(QueryLog)
        .filter(QueryLog.session_id == session_id)
        .order_by(QueryLog.created_at.desc())
        .first()
    )
    if not query_log or not query_log.response_json:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No query responses found for this session."
        )
    return {
        "session_id": session_id,
        "query": query_log.original_query,
        "response": query_log.response_json,
    }


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Fetches details and query history for a research session."""
    session = db.query(ConversationSession).filter(ConversationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    
    # Retrieve query logs for this session
    query_logs = db.query(QueryLog).filter(QueryLog.session_id == session_id).order_by(QueryLog.created_at.asc()).all()
    queries = []
    for q in query_logs:
        queries.append({
            "id": q.id,
            "original_query": q.original_query,
            "response": q.response_json,
            "confidence_score": q.confidence_score,
            "evidence_count": q.evidence_count,
            "conflict_count": q.conflict_count,
            "created_at": q.created_at.isoformat() if q.created_at else None,
            "processing_time_ms": q.processing_time_ms,
        })

    return SessionDetailResponse(
        id=session.id,
        title=session.title or "Research Session",
        turn_count=session.turn_count,
        clarification_turns_count=session.clarification_turns_count,
        is_active=session.is_active,
        context_summary=session.context_summary or "",
        created_at=session.created_at,
        last_active=session.last_active,
        queries=queries,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Deletes a research session and its history."""
    session = db.query(ConversationSession).filter(ConversationSession.id == session_id).first()
    if session:
        db.delete(session)
        db.commit()
    return None

