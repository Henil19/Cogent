"""
Cogent Layer 10: Analytics, Telemetry & Continuous Learning Layer
Package initialization and clean exports.
"""

from app.core.layer10.pipeline import Layer10Pipeline, layer10_pipeline
from app.core.layer10.telemetry.collector import CognitiveTelemetryCollector
from app.core.layer10.feedback.feedback_aggregator import UserFeedbackAggregator
from app.core.layer10.evaluation.evaluation_engine import PostHocEvaluationEngine
from app.core.layer10.calibration.drift_monitor import CalibrationDriftMonitor
from app.core.layer10.diagnosis.failure_analyzer import FailureAnalyzer
from app.core.layer10.optimization.policy_optimizer import AdaptivePolicyOptimizationEngine
from app.core.layer10.datasets.dataset_curator import DatasetCuratorEngine
from app.core.layer10.experimentation.analytics_engine import SystemAnalyticsEngine
from app.core.layer10.experimentation.experiment_manager import ExperimentManager

__all__ = [
    "Layer10Pipeline",
    "layer10_pipeline",
    "CognitiveTelemetryCollector",
    "UserFeedbackAggregator",
    "PostHocEvaluationEngine",
    "CalibrationDriftMonitor",
    "FailureAnalyzer",
    "AdaptivePolicyOptimizationEngine",
    "DatasetCuratorEngine",
    "SystemAnalyticsEngine",
    "ExperimentManager",
]
