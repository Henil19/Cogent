"""
Sub-Module 7.8: Layer 7 Pipeline Orchestrator
Connects Layer 6 SynthesizedReasoningTrace, Layer 5 VerifiedEvidenceSet, and Layer 2 KnowledgeRetrievalPlan.
Executes Source Credibility Assessment, Evidence Reliability Auditing, Reasoning DAG Trust Modeling,
Uncertainty Decomposition, Claim-Level Confidence Calibration, and Hallucination Risk Detection.
Emits standardized TrustAssessment contract strictly to Layer 8 (Explainability & Attribution).
"""

import time
import logging
from typing import Optional

from app.core.layer7.credibility.source_credibility_evaluator import SourceCredibilityEvaluator
from app.core.layer7.reliability.evidence_reliability_analyzer import EvidenceReliabilityAnalyzer
from app.core.layer7.reasoning_trust.reasoning_trust_evaluator import ReasoningTrustEvaluator
from app.core.layer7.uncertainty.uncertainty_engine import UncertaintyEngine
from app.core.layer7.calibration.confidence_calibrator import ConfidenceCalibrator
from app.core.layer7.hallucination.hallucination_detector import HallucinationDetector
from app.core.layer7.builder.trust_assessment_builder import TrustAssessmentBuilder

from app.schemas.layer2 import KnowledgeRetrievalPlan
from app.schemas.layer5 import VerifiedEvidenceSet
from app.schemas.layer6 import SynthesizedReasoningTrace
from app.schemas.layer7 import TrustAssessment

logger = logging.getLogger(__name__)


class Layer7Pipeline:
    """
    Orchestrates the end-to-end Trust Intelligence pipeline.
    """

    def __init__(
        self,
        credibility_evaluator: Optional[SourceCredibilityEvaluator] = None,
        reliability_analyzer: Optional[EvidenceReliabilityAnalyzer] = None,
        reasoning_evaluator: Optional[ReasoningTrustEvaluator] = None,
        uncertainty_engine: Optional[UncertaintyEngine] = None,
        confidence_calibrator: Optional[ConfidenceCalibrator] = None,
        hallucination_detector: Optional[HallucinationDetector] = None,
        trust_builder: Optional[TrustAssessmentBuilder] = None
    ):
        self.credibility_evaluator = credibility_evaluator or SourceCredibilityEvaluator()
        self.reliability_analyzer = reliability_analyzer or EvidenceReliabilityAnalyzer()
        self.reasoning_evaluator = reasoning_evaluator or ReasoningTrustEvaluator()
        self.uncertainty_engine = uncertainty_engine or UncertaintyEngine()
        self.confidence_calibrator = confidence_calibrator or ConfidenceCalibrator()
        self.hallucination_detector = hallucination_detector or HallucinationDetector()
        self.trust_builder = trust_builder or TrustAssessmentBuilder()

    def execute(
        self,
        trace: SynthesizedReasoningTrace,
        evidence_set: VerifiedEvidenceSet,
        plan: KnowledgeRetrievalPlan
    ) -> TrustAssessment:
        """
        Execute full Layer 7 Trust Intelligence workflow.
        """
        start_time = time.time()
        target_domain = "GENERAL"
        if plan.information_need and plan.information_need.target_domains:
            target_domain = plan.information_need.target_domains[0]

        # 1. Sub-Module 7.1: Source Credibility & Authority Evaluation (RA-RAG 2025, CONFACT 2025)
        source_assessments = self.credibility_evaluator.evaluate_sources(
            evidence_set=evidence_set,
            target_domain=target_domain
        )

        # 2. Sub-Module 7.2: Evidence Reliability & Faithfulness Analysis (FRANQ 2026, AwF 2025)
        evidence_assessments = self.reliability_analyzer.analyze_reliability(
            evidence_set=evidence_set,
            trace=trace
        )

        # 3. Sub-Module 7.3: Reasoning Chain Trust Evaluation (Confidence over Time 2026, RLSeek 2026)
        reasoning_assessment = self.reasoning_evaluator.evaluate_reasoning_trust(
            trace=trace,
            source_assessments=source_assessments
        )

        # 4. Sub-Module 7.4: Uncertainty & Epistemic Risk Engine (FRANQ 2026, S2G-RAG 2026)
        uncertainty_assessment = self.uncertainty_engine.assess_uncertainty(
            trace=trace,
            evidence_set=evidence_set,
            plan=plan,
            source_assessments=source_assessments,
            reasoning_assessment=reasoning_assessment
        )

        # 5. Sub-Module 7.5: Confidence Calibration Engine (CLAIM-CAL 2026, APRICOT 2024)
        claim_assessments = self.confidence_calibrator.calibrate_claims(
            trace=trace,
            source_assessments=source_assessments,
            evidence_assessments=evidence_assessments,
            reasoning_assessment=reasoning_assessment,
            uncertainty_assessment=uncertainty_assessment
        )

        # 6. Sub-Module 7.6: Hallucination & Unsupported-Claim Risk Detection (RAGTruth 2024)
        hallucination_assessment = self.hallucination_detector.audit_hallucination_risk(
            trace=trace,
            evidence_set=evidence_set
        )

        # 7. Sub-Module 7.7: Trust Assessment Master Builder (Towards Trustworthy RAG Survey 2026)
        processing_time_ms = (time.time() - start_time) * 1000.0
        assessment = self.trust_builder.build_assessment(
            plan=plan,
            trace=trace,
            source_assessments=source_assessments,
            evidence_assessments=evidence_assessments,
            reasoning_assessment=reasoning_assessment,
            uncertainty_assessment=uncertainty_assessment,
            claim_assessments=claim_assessments,
            hallucination_assessment=hallucination_assessment,
            processing_time_ms=processing_time_ms
        )

        return assessment
