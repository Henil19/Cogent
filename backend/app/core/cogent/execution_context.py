"""
Cogent Master Execution Context
Maintains global correlation ID, per-layer execution lifecycle, latency timers,
warning accumulators, and frozen layer contracts for Layer 10 telemetry.
"""

from typing import Dict, Any, List, Optional
import time
import uuid
from datetime import datetime, timezone


class ExecutionContext:
    """
    Correlation spine tracking an end-to-end Cogent execution across all 10 layers.
    """

    def __init__(
        self,
        raw_query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        execution_id: Optional[str] = None
    ):
        self.execution_id: str = execution_id or f"exec_{uuid.uuid4().hex[:12]}"
        self.session_id: Optional[str] = session_id
        self.user_id: Optional[str] = user_id
        self.raw_query: str = raw_query

        self._start_perf: float = time.perf_counter()
        self.started_at: str = datetime.now(timezone.utc).isoformat()
        self.completed_at: Optional[str] = None

        self.layer_status: Dict[int, str] = {i: "PENDING" for i in range(1, 11)}
        self.layer_timings_ms: Dict[int, float] = {}
        self.layer_artifacts: Dict[int, Any] = {}
        self._layer_start_perf: Dict[int, float] = {}

        self.warnings: List[str] = []
        self.errors: List[str] = []

    def start_layer(self, layer_id: int) -> None:
        """Marks a layer as RUNNING and begins its high-resolution latency timer."""
        self.layer_status[layer_id] = "RUNNING"
        self._layer_start_perf[layer_id] = time.perf_counter()

    def end_layer(self, layer_id: int, artifact: Any = None) -> float:
        """Marks a layer as SUCCESS, records its duration in ms, and attaches its contract."""
        start = self._layer_start_perf.get(layer_id, time.perf_counter())
        duration_ms = round((time.perf_counter() - start) * 1000.0, 3)
        self.layer_timings_ms[layer_id] = duration_ms
        self.layer_status[layer_id] = "SUCCESS"
        if artifact is not None:
            self.layer_artifacts[layer_id] = artifact
        return duration_ms

    def fail_layer(self, layer_id: int, error_message: str) -> None:
        """Marks a layer as FAILED and records the error detail."""
        start = self._layer_start_perf.get(layer_id, time.perf_counter())
        duration_ms = round((time.perf_counter() - start) * 1000.0, 3)
        self.layer_timings_ms[layer_id] = duration_ms
        self.layer_status[layer_id] = "FAILED"
        self.errors.append(f"Layer {layer_id} Failure: {error_message}")

    def skip_layer(self, layer_id: int, reason: str = "") -> None:
        """Marks a layer as SKIPPED (e.g. on early-return ambiguity gate)."""
        self.layer_status[layer_id] = "SKIPPED"
        self.layer_timings_ms[layer_id] = 0.0
        if reason:
            self.warnings.append(f"Layer {layer_id} Skipped: {reason}")

    def add_warning(self, message: str) -> None:
        """Appends a non-fatal warning notice."""
        self.warnings.append(message)

    def finalize(self) -> float:
        """Concludes the execution context and returns total duration in ms."""
        self.completed_at = datetime.now(timezone.utc).isoformat()
        return round((time.perf_counter() - self._start_perf) * 1000.0, 3)

    @property
    def total_duration_ms(self) -> float:
        """Returns total elapsed milliseconds since context initialization."""
        return round((time.perf_counter() - self._start_perf) * 1000.0, 3)
