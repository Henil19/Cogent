"""
Sub-Module 10.1: Cognitive Telemetry Collector (BERGEN, EMNLP 2024)
Collects structured telemetry, latency profiles, token metrics, and layer artifacts
across Layers 1 through 9 into a reproducible, unified CogentExecutionTrace.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.schemas.layer10 import (
    TelemetryPacket,
    LayerExecutionSummary,
    CogentExecutionTrace,
)
from app.core.layer10.telemetry.correlation_manager import CorrelationManager


class CognitiveTelemetryCollector:
    """
    Central telemetry ingestion hub for the Cogent architecture.
    Aggregates runtime events, measures latency breakdowns, and persists execution traces.
    """

    def __init__(self):
        # In-memory execution trace store
        self._traces: Dict[str, CogentExecutionTrace] = {}

    def start_trace(
        self,
        raw_query: str,
        session_id: Optional[str] = None,
        query_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        model_versions: Optional[Dict[str, str]] = None,
        prompt_versions: Optional[Dict[str, str]] = None,
        pipeline_parameters: Optional[Dict[str, Any]] = None,
    ) -> CogentExecutionTrace:
        """Initializes a master CogentExecutionTrace before pipeline execution."""
        exec_id = execution_id or CorrelationManager.generate_execution_id()
        models = model_versions or {"llm": "gemini-2.5-flash", "embedder": "mock-dense-384"}
        prompts = prompt_versions or {}
        params = pipeline_parameters or {"retriever_alpha": 0.5, "rerank_threshold": 0.35}

        config_hash = CorrelationManager.compute_config_hash(models, prompts, params)

        trace = CogentExecutionTrace(
            execution_id=exec_id,
            session_id=session_id or f"sess_{exec_id}",
            query_id=query_id or f"qry_{exec_id}",
            raw_query=raw_query,
            started_at=datetime.now(timezone.utc).isoformat(),
            config_hash=config_hash,
            model_versions=models,
            prompt_versions=prompts,
            pipeline_parameters=params,
        )
        self._traces[exec_id] = trace
        return trace

    def record_packet(self, packet: TelemetryPacket) -> None:
        """Appends a micro-telemetry packet to the corresponding execution trace."""
        trace = self._traces.get(packet.execution_id)
        if not trace:
            return

        trace.telemetry_packets.append(packet)

        # Update layer summary
        summary = trace.layer_summaries.get(packet.layer_id)
        if not summary:
            summary = LayerExecutionSummary(
                layer_id=packet.layer_id,
                layer_name=f"Layer {packet.layer_id}",
                duration_ms=0.0,
            )
            trace.layer_summaries[packet.layer_id] = summary

        summary.duration_ms += packet.duration_ms
        summary.sub_component_latencies[packet.component_name] = (
            summary.sub_component_latencies.get(packet.component_name, 0.0) + packet.duration_ms
        )

    def attach_layer_artifact(
        self,
        execution_id: str,
        layer_id: int,
        artifact: Any,
        duration_ms: float = 0.0
    ) -> None:
        """Attaches a formal layer output contract to the execution trace."""
        trace = self._traces.get(execution_id)
        if not trace:
            return

        # Convert Pydantic models to dict if necessary
        data = artifact.model_dump() if hasattr(artifact, "model_dump") else artifact

        if layer_id == 1:
            trace.layer1_input = data
        elif layer_id == 2:
            trace.layer2_plan = data
        elif layer_id == 3:
            trace.layer3_corpus_meta = data
        elif layer_id == 4:
            trace.layer4_retrieval_meta = data
        elif layer_id == 5:
            trace.layer5_evidence_meta = data
        elif layer_id == 6:
            trace.layer6_reasoning_meta = data
        elif layer_id == 7:
            trace.layer7_trust_meta = data
        elif layer_id == 8:
            trace.layer8_explanation_meta = data
        elif layer_id == 9:
            trace.layer9_response_payload = data

        summary = trace.layer_summaries.get(layer_id)
        if not summary:
            summary = LayerExecutionSummary(
                layer_id=layer_id,
                layer_name=f"Layer {layer_id}",
                duration_ms=duration_ms,
            )
            trace.layer_summaries[layer_id] = summary
        else:
            summary.duration_ms += duration_ms

    def finalize_trace(self, execution_id: str) -> Optional[CogentExecutionTrace]:
        """Finalizes timestamps and total latency for the execution trace."""
        trace = self._traces.get(execution_id)
        if not trace:
            return None

        trace.completed_at = datetime.now(timezone.utc).isoformat()
        trace.total_latency_ms = sum(s.duration_ms for s in trace.layer_summaries.values())
        return trace

    def get_trace(self, execution_id: str) -> Optional[CogentExecutionTrace]:
        """Retrieves an execution trace by its ID."""
        return self._traces.get(execution_id)

    def list_recent_traces(self, limit: int = 50) -> List[CogentExecutionTrace]:
        """Returns recent traces in descending order."""
        return list(self._traces.values())[-limit:]
