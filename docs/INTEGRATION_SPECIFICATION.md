# COGENT: SYSTEM INTEGRATION SPECIFICATION
**Version:** 1.0 (Locked)  
**Target:** Master Cognitive Pipeline Integration (`CogentPipeline`)  

---

## 1. Master Pipeline Lifecycle & Flow

The master orchestrator (`CogentPipeline`) coordinates the end-to-end cognitive flow within a single, correlated execution lifecycle:

```
[User Request]
       │
       ▼
[ExecutionContext Initialization]  <── Generates global execution_id
       │
       ▼
┌──────────────┐
│   Layer 1    │ ── (S(q) < 0.60) ──> [Early Return: CLARIFICATION_REQUIRED]
└──────┬───────┘
       │ S(q) ≥ 0.60
       ▼
┌──────────────┐
│   Layer 2    │ ──> KnowledgeRetrievalPlan (DAG sub-queries & routing)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Layer 3    │ ──> AcquiredCorpusBatch (Local + Tavily Live Web)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Layer 4    │ ──> RetrievedCandidateSet (FAISS Dense + BM25 Sparse + RRF)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Layer 5    │ ──> VerifiedEvidenceSet (Cross-Encoder, Deduplication, ConfRAG)
└──────┬───────┘
       │
       ├─────────────────────────────────────────────┐
       │ (Candidate/Evidence Deficit)                │
       ▼                                             ▼
┌──────────────┐                             ┌──────────────┐
│   Layer 6    │                             │  Epistemic   │
│ Reasoning    │                             │   Hedging    │
└──────┬───────┘                             └──────┬───────┘
       │                                            │
       ▼                                            │
┌──────────────┐                                    │
│   Layer 7    │ <──────────────────────────────────┘
│ Trust & Cal  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Layer 8    │ ──> ExplanationPackage (Topological DAG Narrative & Tokens)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Layer 9    │ ──> UnifiedResponsePayload (Markdown, Badges [1], DAG UI JSON)
└──────┬───────┘
       │
       ├───────────────────────────────────────┐
       ▼                                       ▼
[User Receives Response]           ┌──────────────────────┐
                                   │  Layer 10 (Post-Hoc) │ (Asynchronous / Non-Blocking)
                                   │  Telemetry & RCA     │
                                   └──────────────────────┘
```

---

## 2. Correlation & Execution Context (`ExecutionContext`)

Every transaction is assigned a globally unique UUID: `execution_id = "exec_" + uuid.uuid4().hex[:12]`.

### Context Fields:
- `execution_id: str`: Global correlation identifier across all 10 layers.
- `session_id: Optional[str]`: User session identifier for multi-turn conversational history.
- `start_time: float`: High-resolution monotonic timestamp.
- `layer_status: Dict[int, str]`: Status tracker per layer (`PENDING`, `RUNNING`, `SUCCESS`, `FAILED`, `SKIPPED`).
- `layer_timings_ms: Dict[int, float]`: Exact execution duration per layer.
- `warnings: List[str]`: Non-fatal warning messages accumulated along the pipeline.
- `errors: List[str]`: Fatal error details if a layer fails.
- `layer_artifacts: Dict[int, Any]`: Structured Pydantic contracts produced by each layer, frozen for Layer 10 telemetry attachment.

---

## 3. Explicit Error Boundaries & Failure Policies

### 3.1 Layer 1 Ambiguity Boundary (Early Return)
- **Condition:** When query sufficiency $S(q) < 0.60$ or intent is classified as `AMBIGUOUS`.
- **Action:** Master orchestrator marks status as `CLARIFICATION_REQUIRED`, generates structured clarification questions, and returns immediately.
- **Invariant:** Downstream retrieval (Layers 2–9) is never invoked on under-specified or incoherent queries.

### 3.2 Layers 4 & 5 Evidence Deficit Boundary (Calibrated Abstention)
- **Condition:** When `retrieved_candidates == 0` or Layer 5 cross-encoders filter out all candidate passages as unentailed/irrelevant.
- **Action:** The pipeline does **not** crash or raise an unhandled exception. Instead:
  - Layer 6 instantiates an explicit epistemic boundary node indicating missing evidence.
  - Layer 7 reduces global confidence to low/negligible ($< 0.40$) and flags coverage uncertainty.
  - Layer 8 formulates a calibrated refusal/hedge explanation.
  - Layer 9 generates a qualified response bounded by the unanswerability findings.

### 3.3 Layer 10 Telemetry Failure Isolation (Zero User Impact)
- **Condition:** If an exception occurs in Layer 10 (e.g. telemetry database write error, post-hoc evaluation timeout, or drift computation error).
- **Action:** The exception is caught, logged to stderr, and attached to the internal execution log.
- **Invariant:** The user-facing Layer 9 response is **never** blocked, corrupted, or degraded by a telemetry or analytics failure.

---

## 4. Master Orchestration Contracts

### `CogentQueryRequest`
```python
class CogentQueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    target_audience: ExplanationAudience = ExplanationAudience.TECHNICAL_RESEARCHER
    retrieval_target: SourceTarget = SourceTarget.HYBRID
    max_evidence_count: int = 10
    user_id: Optional[str] = None
```

### `CogentQueryResponse`
```python
class CogentQueryResponse(BaseModel):
    execution_id: str
    status: PipelineStatus  # SUCCESS, CLARIFICATION_REQUIRED, INSUFFICIENT_EVIDENCE_QUALIFIED, ERROR
    unified_response: Optional[UnifiedResponsePayload] = None
    clarification_prompt: Optional[Dict[str, Any]] = None
    metrics: ExecutionMetrics
    warnings: List[str] = []
    created_at: str
```
