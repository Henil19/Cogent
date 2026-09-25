"""
Sub-Module 1.7: Structured Output Assembler & Pipeline Orchestrator
Coordinates the full 7-submodule Layer 1 research pipeline and emits the standardized
StructuredUserInput contract for Layer 2.
"""

import time
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.schemas.layer1 import (
    Layer1Request,
    Layer1Response,
    Layer1Status,
    StructuredUserInput,
)
from app.core.layer1.preprocessor import RequestPreprocessor
from app.core.layer1.understanding import RequestUnderstandingEngine
from app.core.layer1.state_manager import ConversationStateManager
from app.core.layer1.ambiguity import AmbiguityDetectionEngine
from app.core.layer1.sufficiency import SufficiencyAssessmentGate
from app.core.layer1.clarification import ClarificationGenerator


class Layer1Pipeline:
    """
    End-to-End Orchestrator for Layer 1: User Interaction Module.
    Coordinates 1.1 through 1.6 and produces the typed StructuredUserInput contract for Layer 2.
    """

    def __init__(self):
        self.preprocessor = RequestPreprocessor()
        self.understanding_engine = RequestUnderstandingEngine()
        self.state_manager = ConversationStateManager()
        self.ambiguity_engine = AmbiguityDetectionEngine()
        self.sufficiency_gate = SufficiencyAssessmentGate()
        self.clarification_generator = ClarificationGenerator()

    def process(
        self,
        db: Optional[Session] = None,
        request: Optional[Layer1Request] = None,
        user_id: Optional[str] = None,
    ) -> Layer1Response:
        """Run the end-to-end Layer 1 pipeline."""
        if request is None and isinstance(db, Layer1Request):
            # Handled when called positionally as process(request)
            request = db
            db = None

        start_time = time.perf_counter()

        # Step 1.1: Preprocess, normalize, sanitize, and validate language
        cleaned_query, error, prep_metadata = self.preprocessor.preprocess(request.query)
        if error:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            from app.schemas.layer1 import AmbiguityReport, SufficiencyReport
            return Layer1Response(
                status=Layer1Status.REJECTED_INVALID,
                original_query=request.query,
                processed_query="",
                conversation_id=request.conversation_id or "invalid",
                turn_number=1,
                ambiguity=AmbiguityReport(
                    overall_ambiguity_score=1.0,
                    ambiguity_types={},
                    missing_elements=["Valid readable English input"],
                    completeness_score=0.0,
                    coherence_score=0.0,
                    ambiguity_details=error,
                ),
                sufficiency=SufficiencyReport(
                    is_sufficient=False,
                    sufficiency_score=0.0,
                    uncertainty_score=1.0,
                    decision_reason=error,
                ),
                processing_time_ms=elapsed_ms,
            )

        _should_close = False
        if db is None:
            try:
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from sqlalchemy.pool import StaticPool
                from app.database import Base
                mem_engine = create_engine(
                    "sqlite:///:memory:",
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool
                )
                Base.metadata.create_all(bind=mem_engine)
                db = sessionmaker(autocommit=False, autoflush=False, bind=mem_engine)()
                _should_close = True
            except Exception:
                db = None


        try:
            # Step 1.3: Conversation State Management & Contextualization
            conversation = self.state_manager.get_or_create_conversation(
                db=db,
                conversation_id=request.conversation_id,
                user_id=user_id,
            )

            reformed_query, turn_number, context_meta = self.state_manager.contextualize_query(
                db=db,
                conversation=conversation,
                raw_query=cleaned_query,
                clarification_response=request.clarification_response,
            )

            if request.clarification_response:
                conversation.clarification_turns_count += 1
                if db:
                    db.commit()

            # Step 1.2: Request Understanding (Intent, Concepts, Typology)
            understanding = self.understanding_engine.analyze(reformed_query)

            # Step 1.4: Ambiguity Detection Engine (CLAMBER 5-type + Completeness + Coherence)
            ambiguity_report = self.ambiguity_engine.detect(
                query=reformed_query,
                entities=understanding["entities"],
            )

            # Step 1.5: Sufficiency Assessment Gate (Exact 4-term formula)
            sufficiency_report = self.sufficiency_gate.evaluate(
                query=reformed_query,
                entities=understanding["entities"],
                ambiguity=ambiguity_report,
                intent_clarity_score=understanding.get("intent_clarity_score", 0.85),
                clarification_turn_count=conversation.clarification_turns_count,
            )

            # Step 1.6: Clarification Strategy Generator (ASK Aspect Decomposition)
            status = Layer1Status.SUFFICIENT_PROCEED
            clarification_plan = None
            contract_for_layer2 = None

            if not sufficiency_report.is_sufficient:
                if conversation.clarification_turns_count >= 2:
                    # Maximum clarification rounds reached -> Best effort proceed
                    status = Layer1Status.MAX_CLARIFICATION_PROCEED
                else:
                    status = Layer1Status.CLARIFICATION_NEEDED
                    # Collect prior questions and aspects from context memory to guarantee progressive non-repeating questions
                    prior_turns = context_meta.get("prior_turns", [])
                    prior_questions = []
                    prior_aspects = []
                    for pt in prior_turns:
                        q_text = pt.get("clarification_question")
                        if q_text:
                            prior_questions.append(q_text)
                        l1 = pt.get("layer1_data")
                        if isinstance(l1, dict):
                            c_plan = l1.get("clarification")
                            if isinstance(c_plan, dict):
                                if c_plan.get("question"):
                                    prior_questions.append(c_plan["question"])
                                if c_plan.get("target_aspect"):
                                    prior_aspects.append(c_plan["target_aspect"])

                    clarification_plan = self.clarification_generator.generate(
                        query=reformed_query,
                        ambiguity=ambiguity_report,
                        current_round=conversation.clarification_turns_count + 1,
                        prior_questions=prior_questions,
                        prior_aspects=prior_aspects,
                    )

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Step 1.7: Structured Output Assembly for Layer 2
            if status in [Layer1Status.SUFFICIENT_PROCEED, Layer1Status.MAX_CLARIFICATION_PROCEED]:
                structured_contract = StructuredUserInput(
                    original_query=request.query,
                    processed_query=cleaned_query,
                    resolved_query=reformed_query,
                    intent=understanding["intent"],
                    query_type=understanding["query_type"],
                    entities=understanding["entities"],
                    constraints=understanding["constraints"],
                    conversation_context=context_meta,
                    session_id=conversation.id,
                    turn_number=turn_number,
                    ambiguity_report=ambiguity_report,
                    sufficiency_score=sufficiency_report.sufficiency_score,
                    interpretation_entropy=sufficiency_report.uncertainty_score,
                    clarification_history=context_meta.get("prior_turns", []),
                    was_clarified=bool(request.clarification_response),
                    clarification_rounds=conversation.clarification_turns_count,
                    proceed_mode="STANDARD" if status == Layer1Status.SUFFICIENT_PROCEED else "BEST_EFFORT_FALLBACK",
                    preprocessing_time_ms=elapsed_ms,
                )
                contract_for_layer2 = structured_contract.model_dump()

            response = Layer1Response(
                status=status,
                original_query=request.query,
                processed_query=reformed_query,
                conversation_id=conversation.id,
                turn_number=turn_number,
                intent=understanding["intent"],
                query_type=understanding["query_type"],
                entities=understanding["entities"],
                key_concepts=understanding["key_concepts"],
                ambiguity=ambiguity_report,
                sufficiency=sufficiency_report,
                clarification=clarification_plan,
                contract_for_layer2=contract_for_layer2,
                processing_time_ms=elapsed_ms,
            )

            # Persist turn in database
            if db:
                self.state_manager.record_turn(
                    db=db,
                    conversation_id=conversation.id,
                    turn_number=turn_number,
                    user_query=request.query,
                    layer1_data=response.model_dump(),
                    was_clarified=bool(request.clarification_response),
                    clarification_question=(
                        clarification_plan.clarification_questions[0]
                        if (clarification_plan and clarification_plan.clarification_questions)
                        else None
                    ),
                    user_clarification_response=request.clarification_response,
                    clarification_rounds=conversation.clarification_turns_count,
                )

            return response
        finally:
            if _should_close and db:
                try:
                    db.close()
                except Exception:
                    pass


# Singleton instance
layer1_pipeline = Layer1Pipeline()
