"""
Layer 1 API Router
Endpoints to process queries through the User Interaction Module and manage conversational sessions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.conversation import Conversation, ConversationTurn
from app.schemas.layer1 import Layer1Request, Layer1Response
from app.core.layer1.pipeline import Layer1Pipeline

router = APIRouter(prefix="/layer1", tags=["Layer 1: User Interaction Module"])
pipeline = Layer1Pipeline()


@router.post("/process", response_model=Layer1Response)
def process_user_query(
    request: Layer1Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Process raw user query through the 7-submodule Layer 1 research pipeline:
    1.1 Preprocess & sanitize
    1.2 Understand intent & extract concepts
    1.3 Contextualize with multi-turn conversation memory
    1.4 CLAMBER 5-type ambiguity detection
    1.5 Calibrated sufficiency gate (IntentSim & CLAIM entropy)
    1.6 ASK aspect-based targeted clarification (max 2 rounds)
    1.7 Structured contract assembly for Layer 2
    """
    user_id = current_user.id if current_user else None
    response = pipeline.process(db=db, request=request, user_id=user_id)
    return response


@router.get("/conversations/{conversation_id}")
def get_conversation_history(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Retrieve multi-turn conversation state and turn history."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    turns = (
        db.query(ConversationTurn)
        .filter(ConversationTurn.conversation_id == conversation_id)
        .order_by(ConversationTurn.turn_number.asc())
        .all()
    )

    return {
        "conversation_id": conv.id,
        "title": conv.title,
        "clarification_turns_count": conv.clarification_turns_count,
        "turns": [
            {
                "turn_number": t.turn_number,
                "user_query": t.user_query,
                "layer1_status": t.layer1_data.get("status") if t.layer1_data else None,
                "created_at": t.created_at,
            }
            for t in turns
        ],
    }


@router.get("/health")
def layer1_health_check():
    """Health status of Layer 1 pipeline."""
    return {"status": "online", "module": "Layer 1: User Interaction Module", "version": "1.0.0"}
