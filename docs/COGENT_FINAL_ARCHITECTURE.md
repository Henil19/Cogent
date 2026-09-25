# COGENT: FINAL ARCHITECTURE SPECIFICATION
**Version:** 1.0 (Locked)  
**Research Title:** *Cogent: An Explainable and Trustworthy AI Framework for Evidence-Based Decision Support*  
**Scope:** Research-Ready Integrated Cognitive Pipeline  

---

## 1. Executive Summary & System Objective
Large Language Models (LLMs) frequently suffer from hallucination, ungrounded speculation, opaque reasoning leaps, and poorly calibrated overconfidence. Standard Retrieval-Augmented Generation (RAG) improves factual retrieval but fails to ensure transparent multihop deduction, faithful citation provenance, dialectical conflict preservation, or calibrated epistemic uncertainty.

**Cogent** resolves these fundamental limitations by replacing monolithic prompt-and-generate architectures with a **10-layer cognitive pipeline**:
$$\text{L1 (Understand)} \longrightarrow \text{L2 (Plan)} \longrightarrow \text{L3 (Acquire)} \longrightarrow \text{L4 (Retrieve)} \longrightarrow \text{L5 (Verify)} \longrightarrow \text{L6 (Reason)} \longrightarrow \text{L7 (Trust)} \longrightarrow \text{L8 (Explain)} \longrightarrow \text{L9 (Present)} \longrightarrow \mathbf{\text{L10 (Learn)}}$$

### Research Goals & Research Questions (RQs)
- **RQ1 (Grounding & Attribution):** Does Cogent significantly improve factual grounding and fine-grained citation precision compared to naive RAG baselines?
- **RQ2 (Multi-Hop & Conflict Reasoning):** Does explicit DAG-based reasoning with *Zero Winner Forcing* preserve opposing evidence viewpoints and resolve complex multi-hop dependencies better than standard prompt synthesis?
- **RQ3 (Trust & Calibration):** Does multidimensional trust decomposition (Source Credibility, Evidence Reliability, Reasoning Integrity, Epistemic Uncertainty) yield lower Expected Calibration Error (ECE) and Brier scores than raw model probabilities?
- **RQ4 (Faithful Explainability):** Does deriving natural language narratives directly from reasoning graph cut-sets preserve counterfactual sensitivity and eliminate post-hoc rationalization?
- **RQ5 (Computational Latency Overhead):** What is the empirical latency and token overhead of multi-stage cognitive verification relative to standard RAG?
- **RQ6 (Closed-Loop Improvement):** Can non-blocking cognitive telemetry and user feedback attribution successfully diagnose systemic bottlenecks and curate offline DPO alignment datasets?

---

## 2. Overall 10-Layer Architecture

```
                                 USER QUERY
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: USER INTERACTION & AMBIGUITY GATE                                 │
│ Intent Typology • CLAMBER Ambiguity • Calibrated Sufficiency S(q) • Clarify │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ StructuredUserInput (S(q) ≥ 0.60)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: QUERY UNDERSTANDING & PLANNING LAYER                               │
│ Information Need Deficit • Q-DREAM DAG Decomposition • Adaptive Routing    │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ KnowledgeRetrievalPlan
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: KNOWLEDGE ACQUISITION & PRE-RETRIEVAL GROUNDING                    │
│ Multi-Format Extraction • Late Chunking • SHA-256 Hashes • TROVE Coordinates│
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ AcquiredCorpusBatch
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 4: HYBRID KNOWLEDGE RETRIEVAL LAYER                                  │
│ FAISS Vector IP • Okapi BM25 Inverted Index • Reciprocal Rank Fusion (RRF) │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ RetrievedCandidateSet (Zero Pruning)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 5: EVIDENCE INTELLIGENCE & CONFLICT RESOLUTION                        │
│ Relevance & Quality Gating • Cross-Encoder • Deduplication • ConfRAG Graph │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ VerifiedEvidenceSet (Zero Winner Forcing)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 6: TRANSPARENT REASONING & SYNTHESIS LAYER                           │
│ Entailment Trees • Multihop DAG • Comparative Matrix • Epistemic Boundaries│
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ SynthesizedReasoningTrace
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 7: TRUST INTELLIGENCE & CALIBRATION LAYER                            │
│ Source Credibility • Evidence Reliability • 5 Uncertainty Dims • ECE Trust │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ TrustAssessment (GTI ≠ Confidence)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 8: DYNAMIC EXPLAINABILITY & ATTRIBUTION LAYER                        │
│ Topological Narratives • [C{i}-E{j}] Tokens • Counterfactual Sensitivity   │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ ExplanationPackage (Audience Invariant)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 9: RESPONSE GENERATION & PRESENTATION LAYER                          │
│ Grounded Generator • [1] Badges • Conflict Widgets • SVG DAG Explorer UI   │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ UnifiedResponsePayload
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 10: ANALYTICS, TELEMETRY & CONTINUOUS LEARNING LAYER (POST-HOC)       │
│ BERGEN Trace • GaRAGe Grounding • SGIC Drift • GroUSE RCA • Offline DPO    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Layer-by-Layer Specifications & Contracts

### Layer 1: User Interaction & Ambiguity Resolution
- **Purpose:** Sanitizes raw queries, extracts intent typology, detects conversational state drift, and calculates mathematical query sufficiency before initiating expensive retrieval.
- **Contract Output:** `StructuredUserInput`
- **Core Formula:**
  $$S(q) = 0.35(1 - \max \mathcal{A}) + 0.30 C_{\text{comp}} + 0.15 C_{\text{coh}} + 0.20 I_{\text{clarity}}$$
- **Operational Boundary:** If $S(q) < 0.60$, execution terminates early with `CLARIFICATION_REQUIRED` returning targeted clarification options without executing downstream retrieval.

### Layer 2: Query Understanding & Strategic Planning
- **Purpose:** Decomposes complex queries into atomic sub-questions scheduled in a directed acyclic graph (DAG), extracts sparse/dense representations, and assigns source routing targets (`LOCAL_DOCS`, `LIVE_WEB`, `HYBRID`).
- **Contract Output:** `KnowledgeRetrievalPlan`
- **Research Anchors:** Q-DREAM (ACL 2025), Adaptive-RAG (NAACL 2024), RealRoute (2026).

### Layer 3: Knowledge Acquisition & Pre-Retrieval Grounding
- **Purpose:** Ingests local files (PDF, Markdown, TXT) and live web articles (Tavily), normalizes content, performs structure-preserving Late Chunking, and attaches immutable TROVE coordinate breadcrumbs.
- **Contract Output:** `AcquiredCorpusBatch`
- **Research Anchors:** SCAN (ACL 2025), Late Chunking (2024), TROVE (ACL 2025).

### Layer 4: Hybrid Knowledge Retrieval
- **Purpose:** Performs bi-encoder dense embedding search (FAISS `IndexFlatIP`) and sparse keyword search (Okapi BM25), fusing ranked candidate lists via rank-based Reciprocal Rank Fusion ($k=60$).
- **Contract Output:** `RetrievedCandidateSet`
- **Core Formula:**
  $$\text{RRF}(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{1}{60 + r_m(d)}$$
- **Invariant:** Strict **Zero Evidence Pruning** at Layer 4; all candidate rankings and coordinates are preserved for Layer 5.

### Layer 5: Evidence Intelligence & Conflict Resolution
- **Purpose:** Executes evidence relevance/quality analysis, deduplication, conflict detection, coverage analysis, and evidence selection, with cross-encoder reranking where configured.
- **Contract Output:** `VerifiedEvidenceSet`
- **Research Anchors:** ConfRAG (ACL 2026), S2G-RAG (ACL 2026), Alt et al. (EACL 2026).
- **Invariant:** **Zero Winner Forcing**—conflicting propositions are preserved as bidirectional contradiction edges rather than prematurely discarded.

### Layer 6: Transparent Reasoning & Synthesis
- **Purpose:** Constructs the structured reasoning graph, performs evidence-grounded multi-hop and comparative reasoning, reconciles conflicts without forced winner selection, and identifies epistemic gaps.
- **Contract Output:** `SynthesizedReasoningTrace`
- **Research Anchors:** Entailment Trees (EMNLP 2021), Self-Deduction (2025), Comparative Matrices (2026).

### Layer 7: Trust Intelligence & Confidence Calibration
- **Purpose:** Evaluates source credibility, evidence reliability, reasoning trust, uncertainty, hallucination risk, and calibrated confidence where calibration has been empirically established.
- **Contract Output:** `TrustAssessment`
- **Key Invariant:** **Global Trust Index $\neq$ Confidence Probability**. GTI integrates epistemic risk and source authority; confidence reflects model calibration.
- **Research Anchors:** CLAIM-CAL (2026), RAGTruth (ACL 2024), APRICOT (ACL 2024).

### Layer 8: Dynamic Explainability & Attribution
- **Purpose:** Traverses the reasoning DAG topologically to construct multi-fidelity explanations, replaces internal evidence references with bracketed tokens `[C{i}-E{j}]`, and derives counterfactual sensitivity cut-sets.
- **Contract Output:** `ExplanationPackage`
- **Key Invariant:** **Epistemic Invariance Across Audiences**—executive, technical, layperson, and expert views share the exact same factual claims and confidence bounds.

### Layer 9: Response Generation & Presentation
- **Purpose:** Synthesizes presentation-ready Markdown, resolves citation tokens into sequential interactive badges `[1]`, renders side-by-side dialectical conflict cards, and formats the interactive SVG/React Flow Reasoning DAG Explorer.
- **Contract Output:** `UnifiedResponsePayload`
- **Key Invariant:** **Zero Epistemic Mutation**—Layer 9 formats and explains, but never invents facts or alters upstream confidence.

### Layer 10: Analytics, Telemetry & Continuous Learning
- **Purpose:** Records post-execution telemetry, feedback, evaluation, calibration diagnostics, failure analysis, and learning signals non-blockingly; generated learning signals are used only through controlled offline validation and do not mutate the current execution.
- **Contract Output:** `CogentExecutionTrace`, `EvaluationMetricsReport`, `CalibrationDriftReport`, `RootCauseDiagnosis`, `DatasetCuratorExport`
- **Research Anchors:** BERGEN (EMNLP 2024), RAGEval (ACL 2025), GaRAGe (EMNLP 2024), GroUSE (ACL 2025), SGIC (2024), IUPO/DJPO (2024).

---

## 4. Master Data Contracts Matrix

| Sending Layer | Receiving Layer | Contract Data Model | Key Payload Contents |
| :--- | :--- | :--- | :--- |
| **L1** | **L2** | `StructuredUserInput` | Cleaned query, intent typology, conversational context, sufficiency $S(q)$ |
| **L2** | **L3 / L4** | `KnowledgeRetrievalPlan` | Sub-queries, DAG dependencies, dense/sparse expansions, routing targets |
| **L3** | **L4** | `AcquiredCorpusBatch` | Document chunks, text content, SHA-256 hashes, TROVE coordinates |
| **L4** | **L5** | `RetrievedCandidateSet` | Top-$K$ candidates, dense scores, BM25 scores, RRF fusion ranks |
| **L5** | **L6 / L7** | `VerifiedEvidenceSet` | Selected evidence, cross-encoder scores, conflict edges, coverage map |
| **L6** | **L7 / L8** | `SynthesizedReasoningTrace` | Synthesized claims, premise links, comparative matrix, epistemic hedges |
| **L7** | **L8 / L9** | `TrustAssessment` | Global Trust Index, calibrated confidence, 5 uncertainty components, risk tier |
| **L8** | **L9** | `ExplanationPackage` | Multi-fidelity narratives, `[C{i}-E{j}]` tokens, counterfactual cut-sets |
| **L9** | **User / L10**| `UnifiedResponsePayload` | Formatted sections, `[1]` badges, conflict cards, DAG explorer JSON |
| **L1–L9** | **L10** | `CogentExecutionTrace` | Frozen correlated copy of all layer contracts for post-hoc evaluation |

---

## 5. Architectural Invariants
1. **Zero Epistemic Mutation:** Neither Layer 9 nor Layer 10 may alter the factual propositions, confidence scores, conflict clusters, or evidence links generated by upstream layers.
2. **Zero Winner Forcing:** Disagreements across authoritative sources must be preserved as dialectical divergence; the system never arbitrarily suppresses valid counter-evidence.
3. **Calibrated Uncertainty Bounds:** Insufficient evidence or unanswerable queries must trigger qualified hedges and abstention rather than ungrounded speculative completion.
4. **Controlled Offline Learning Boundary:** Telemetry, failure diagnoses, and preference pairs generated by Layer 10 are strictly quarantined for offline validation and supervised fine-tuning; no online base-model weights mutation occurs during inference.
