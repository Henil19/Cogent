"""
Cogent Layer 10 API Router: Analytics, Telemetry & Continuous Learning Layer
Exposes endpoints for execution trace ingestion, feedback attribution, post-hoc evaluation,
calibration drift reporting, failure diagnosis, learning signals, and A/B experiments.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.schemas.layer10 import (
    CogentExecutionTrace,
    UserFeedbackPayload,
    EvaluationMetricsReport,
    CalibrationDriftReport,
    RootCauseDiagnosis,
    LearningSignal,
    DatasetCuratorExport,
    ExperimentRun,
    Layer10AnalyticsOverview,
    Layer10DirectRequest,
    Layer10Response,
)
from app.core.layer10.pipeline import layer10_pipeline

router = APIRouter(prefix="/layer10", tags=["Layer 10 - Analytics, Telemetry & Continuous Learning"])


class ABExperimentRequest(BaseModel):
    experiment_name: str
    baseline_config_hash: str
    candidate_config_hash: str
    baseline_evaluations: List[EvaluationMetricsReport]
    candidate_evaluations: List[EvaluationMetricsReport]
    baseline_latencies: List[float]
    candidate_latencies: List[float]


@router.post("/trace", response_model=Layer10Response, summary="Ingest and Analyze Execution Trace")
async def process_trace_endpoint(request: Layer10DirectRequest):
    """
    Ingests a complete execution trace, runs multi-gate evaluation, monitors calibration drift,
    diagnoses root causes, and emits learning signals while strictly preserving Zero Epistemic Mutation.
    """
    return layer10_pipeline.process_execution(
        trace=request.execution_trace,
        include_failure_diagnosis=request.include_failure_diagnosis,
        include_evaluation=request.include_evaluation,
        include_learning_signals=request.include_learning_signals,
    )


@router.post("/feedback", response_model=UserFeedbackPayload, summary="Record and Attribute User Feedback")
async def record_feedback_endpoint(feedback: UserFeedbackPayload):
    """
    Records explicit ratings or implicit behavioral interactions and maps attribution
    backwards through presentation badges to claims, evidence, and source documents.
    """
    return layer10_pipeline.record_user_feedback(feedback)


@router.post("/evaluate", response_model=EvaluationMetricsReport, summary="Post-Hoc Evaluation on Demand")
async def evaluate_trace_endpoint(trace: CogentExecutionTrace):
    """
    Executes the multi-gate post-hoc evaluation suite (RAGEval, GaRAGe, GroUSE)
    on an execution trace without side-effects.
    """
    return layer10_pipeline.evaluator.evaluate_trace(trace)


@router.get("/analytics", response_model=Layer10AnalyticsOverview, summary="System-Wide Operational Analytics")
async def get_analytics_endpoint():
    """Returns global operational KPIs, mean grounding, latency, and failure distributions."""
    return layer10_pipeline.get_analytics_overview()


@router.get("/calibration", response_model=CalibrationDriftReport, summary="Trust Calibration & ECE Report")
async def get_calibration_endpoint():
    """Returns empirical calibration health, ECE, Brier score, and drift status."""
    return layer10_pipeline.get_calibration_report()


@router.get("/learning-signals", response_model=List[LearningSignal], summary="Active Learning Signals")
async def list_learning_signals_endpoint():
    """Returns all active, validated learning signals targeting upstream pipeline configurations."""
    return layer10_pipeline.policy_optimizer.list_active_signals()


@router.get("/datasets", response_model=DatasetCuratorExport, summary="Curated Training & Evaluation Datasets")
async def export_datasets_endpoint():
    """Exports curated Gold benchmarks, DPO preference pairs, and automated regression test cases."""
    return layer10_pipeline.export_curated_datasets()


@router.post("/experiments", response_model=ExperimentRun, summary="Execute A/B Configuration Experiment")
async def run_experiment_endpoint(request: ABExperimentRequest):
    """Executes a reproducible A/B comparison across configuration hashes per BERGEN guidelines."""
    return layer10_pipeline.run_ab_experiment(
        experiment_name=request.experiment_name,
        baseline_config_hash=request.baseline_config_hash,
        candidate_config_hash=request.candidate_config_hash,
        baseline_evaluations=request.baseline_evaluations,
        candidate_evaluations=request.candidate_evaluations,
        baseline_latencies=request.baseline_latencies,
        candidate_latencies=request.candidate_latencies,
    )


@router.get("/health", summary="Layer 10 Health & Observability Status")
async def layer10_health():
    """Health check reporting telemetry collector and drift monitor operational readiness."""
    overview = layer10_pipeline.get_analytics_overview()
    return {
        "layer": 10,
        "name": "Analytics, Telemetry & Continuous Learning Layer",
        "status": "HEALTHY",
        "total_traces_tracked": overview.total_executions,
        "calibration_status": overview.calibration_status,
        "active_learning_signals": overview.active_learning_signals_count,
        "invariants": {
            "zero_epistemic_mutation": True,
            "controlled_offline_learning": True,
            "verbosity_regularization": True,
        }
    }
