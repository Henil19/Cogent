# COGENT: EXPERIMENTAL METHODOLOGY & BENCHMARK PLAN (VERSION 1.0)
**Status:** 🔒 Frozen Protocol (`experiment_protocol_v1`)  
**Target:** Scientific Benchmarking, Ablation Studies, Empirical Validation & Research Publication  
**Reproducibility Seed:** `SEED = 42`  

---

## 1. Research Questions & Hypotheses Mapping

The empirical evaluation of Cogent is structured around six core Research Questions ($RQ_1$–$RQ_6$) and six corresponding directional hypotheses ($H_1$–$H_6$):

| Research Question | Associated Hypothesis | Primary Evaluated Layers | Experimental Comparison |
| :--- | :--- | :--- | :--- |
| **RQ1 (Grounding & Attribution)** | **H1:** Cogent achieves statistically significantly higher evidence grounding ($G \ge 0.85$) and citation precision ($P_{\text{cite}} \ge 0.90$) than Naive RAG and Reranked RAG. | L3, L4, L5, L8, L9 | Baselines vs. Cogent Pipeline |
| **RQ2 (Multi-Hop & Conflict Reasoning)** | **H2 & H3:** Explicit DAG reasoning with Zero Winner Forcing resolves multi-hop inferences ($P_1 + P_2 \Rightarrow IC$) and preserves empirical contradictions without premature suppression. | L5, L6, L8 | Direct LLM vs. Cogent DAG Reasoning |
| **RQ3 (Trust & Calibration)** | **H4:** Calibrated multidimensional trust yields lower Expected Calibration Error ($\text{ECE} \le 0.12$) and Brier score than raw LLM softmax probabilities. | L7, L10 | Raw Softmax Confidence vs. Cogent Calibrated GTI |
| **RQ4 (Faithful Explainability)** | **H5:** Explanations derived from topological DAG cut-sets preserve counterfactual sensitivity and eliminate post-hoc rationalization. | L8, L9 | Unstructured Prompt Explanation vs. Cogent DAG Explanations |
| **RQ5 (Latency & Computational Overhead)** | **H6:** Multi-stage cognitive verification incurs bounded latency ($< 3.0\text{s}$ per query on standard hardware) that scales sub-linearly with evidence volume. | L1–L10 | End-to-End Latency vs. Metric Quality Trade-Off |
| **RQ6 (Closed-Loop Improvement)** | **H7:** Post-hoc telemetry and failure diagnosis generate high-quality preference pairs that improve downstream policy selection without live weight corruption. | L10 | Baseline Configuration vs. Post-Telemetry Optimized Configuration |

---

## 2. Benchmark Corpus Taxonomy (100 Queries — `benchmark_v1`)

The benchmark consists of exactly 100 curated, research-grade queries categorized across six distinct cognitive challenges:

| Category | Query IDs | Count | Difficulty Breakdown | Core Objective & Evaluation Target |
| :--- | :--- | :--- | :--- | :--- |
| **1. Factual Grounded** | `Q001`–`Q020` | 20 | Easy: 8, Med: 8, Hard: 4 | Single-source direct factual retrieval; exact numerical or categorical values; fine-grained citation coordinate mapping. |
| **2. Multi-Hop Deductive** | `Q021`–`Q040` | 20 | Med: 10, Hard: 10 | Premise entailment across 2 or more distinct documents or non-adjacent chunks ($P_1 + P_2 \Rightarrow IC$); DAG path validation. |
| **3. Comparative Trade-Off** | `Q041`–`Q060` | 20 | Med: 12, Hard: 8 | Multi-attribute architectural trade-off analysis (accuracy, latency, memory, scaling); criteria matrix synthesis. |
| **4. Conflicting Evidence** | `Q061`–`Q075` | 15 | Med: 5, Hard: 10 | Literature with empirical divergence (differing benchmarks, temporal updates); strict Zero Winner Forcing verification. |
| **5. Insufficient Evidence** | `Q076`–`Q090` | 15 | Med: 8, Hard: 7 | Queries with absent, unanswerable, or out-of-domain premise information; calibrated epistemic refusal and hedging. |
| **6. Ambiguous / Underspecified** | `Q091`–`Q100` | 10 | Easy: 4, Med: 6 | Underspecified or polysemous queries ($S(q) < 0.60$); Layer 1 CLAMBER ambiguity detection and clarification prompting. |

---

## 3. Baseline Systems (`experiments/baselines/`)

To isolate the independent contributions of Cogent's cognitive layers, three reference baseline systems are implemented with an identical execution interface (`BaseBaseline`):

### Baseline 1: LLM-Only Direct (`llm_only`)
- **Pipeline:** Query $\to$ Monolithic LLM Generation $\to$ Direct Answer.
- **Purpose:** Establishes the non-RAG parametric baseline. Measures base model hallucination, unsupported claim rates, and ungrounded confabulation.

### Baseline 2: Standard Naive RAG (`naive_rag`)
- **Pipeline:** Query $\to$ Dense Bi-Encoder Embeddings $\to$ FAISS Vector Index Top-$K$ Retrieval $\to$ Concatenated Context Prompt $\to$ LLM Answer.
- **Purpose:** Standard industry RAG architecture without query planning, hybrid fusion, NLI verification, reasoning DAGs, trust calibration, or citation registries.

### Baseline 3: RAG + Cross-Encoder Reranker (`reranked_rag`)
- **Pipeline:** Query $\to$ FAISS Retrieval $\to$ Cross-Encoder Relevance Reranker $\to$ Top-$K$ Passages $\to$ Concatenated Context Prompt $\to$ LLM Answer.
- **Purpose:** Critical ablation baseline. Isolates whether Cogent's empirical gains stem merely from better passage reranking or from the complete 10-layer cognitive verification architecture.

---

## 4. Metric Hierarchy: Primary vs. Secondary Metrics

To ensure defensible evaluation and prevent post-hoc metric cherry-picking, metrics are strictly stratified into **Primary Evaluation Metrics** (directly answering $RQ_1$–$RQ_6$) and **Secondary Diagnostic Metrics**:

### Primary Evaluation Metrics
1. **Grounding Score ($G \in [0, 1]$)**: Fraction of extracted factual assertions strictly entailed by verified evidence coordinates (GaRAGe).
2. **Citation Precision ($P_{\text{cite}} \in [0, 1]$)**: Ratio of cited documents that genuinely entail the citing statement (CiteBench).
3. **Claim Support Ratio ($\in [0, 1]$)**: Proportion of synthesized claims grounded in valid inferential premise steps.
4. **Expected Calibration Error ($\text{ECE} \in [0, 1]$)**:
   $$\text{ECE} = \sum_{b=1}^{B} \frac{|B_b|}{N} \left| \text{acc}(B_b) - \text{conf}(B_b) \right|$$
5. **Conflict Preservation Rate ($\in [0, 1]$)**: Percentage of contradictory claims preserved as dialectical divergence (Zero Winner Forcing).
6. **Factual Correctness ($\in [0, 1]$)**: Semantic agreement with ground-truth reference assertions.
7. **End-to-End Latency ($\text{ms}$)**: Total wall-clock execution time per inquiry.

### Secondary Diagnostic Metrics
- **Retrieval:** `Hit@K`, `Recall@K`, `MRR@K`, `NDCG@K`.
- **Evidence Quality:** Evidence Precision, Evidence Coverage, Evidence Redundancy, Quality Gating Score.
- **Reasoning:** Premise Grounding Ratio, Reasoning Integrity Score, Weakest-Link Bottleneck Severity.
- **Trust & Calibration:** Brier Score, Overconfidence Penalty, Uncertainty Entropy.
- **Attribution:** Citation Coverage, Claim Attribution Accuracy, Explanation Faithfulness.
- **Resources:** Prompt Tokens, Completion Tokens, Total Tokens, LLM API Calls, Embedding Calls, Estimated Cost ($).

---

## 5. Master Experiment Matrix

| RQ | Experiment ID | Systems Compared | Benchmark Subset | Primary Metrics | Statistical Significance Test |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RQ1** | `EXP-01-GROUNDING` | Naive RAG vs. Cogent | All 100 queries | Grounding Score ($G$), Factual Correctness | Wilcoxon Signed-Rank Test |
| **RQ2** | `EXP-02-EVIDENCE` | RAG+Rerank vs. Cogent | Factual (20) & Multi-Hop (20) | Evidence Precision, Evidence Coverage | Wilcoxon Signed-Rank Test |
| **RQ3** | `EXP-03-REASONING` | LLM-Only vs. Cogent | Multi-Hop (20) & Conflicting (15) | Claim Support Ratio, Conflict Preservation | Wilcoxon Signed-Rank Test |
| **RQ4** | `EXP-04-TRUST` | Softmax LLM vs. Cogent GTI | All 100 queries | Expected Calibration Error (ECE), Brier Score | Paired Student's t-test |
| **RQ5** | `EXP-05-EXPLAIN` | Standard RAG vs. Cogent | All 100 queries | Citation Precision ($P_{\text{cite}}$), Citation Coverage | Wilcoxon Signed-Rank Test |
| **RQ6** | `EXP-06-LATENCY` | All 4 Systems | All 100 queries | Total Latency (ms), Token Usage, Estimated Cost | Paired Student's t-test |

---

## 6. Experimental Validity, Reproducibility & Evaluation Controls

### 6.1 Leakage & Contamination Control
- Benchmark queries, gold answers, and evidence mappings are stored separately under `benchmark/ground_truth/` and are never loaded into runtime retrieval indices or system prompts.
- Both benchmark and corpus are cryptographically hashed and versioned as `benchmark_v1` and `corpus_v1`.
- Any modification of gold references requires a version increment (e.g. `benchmark_v2`).

### 6.2 Controlled System Comparison Protocol
- All baseline systems and Cogent operate under identical constraints:
  - Model family & version: `gemini-2.5-flash` (or deterministic offline mock harness).
  - Generation temperature: `temperature = 0.0`.
  - Maximum output tokens: `max_output_tokens = 1024`.
  - Shared retrieval corpus: `corpus_v1` ($Top\text{-}K = 5$).
  - Shared evaluation environment and timeout policy.

### 6.3 Stochasticity & Replication Policy
- Deterministic components use fixed seed `SEED = 42`.
- Model API executions record raw prompt tokens, completion tokens, temperature, and raw outputs.
- Pilot execution uses 1 run; main benchmark uses 1 full controlled run; critical ablations use 3 repeated runs.

### 6.4 Metric Validation
- Every metric in `experiments/evaluation/` is unit-tested against hand-crafted positive, negative, and edge test cases with known mathematical expected values prior to running experiments.

### 6.5 Failure & Retry Policy
- Runners record execution failures distinctly from model hallucination failures.
- Transient network errors allow up to 3 exponential retries. Unresolvable errors are recorded in the execution log and never silently excluded.

### 6.6 Human Evaluation Protocol
- 20 representative queries evaluated across Cogent and Baselines by 2–3 independent annotators blind to system identity.
- 1–5 Likert scale across: Correctness, Evidence Support, Explanation Faithfulness, Completeness, Conflict Handling, and Overall Usefulness.
- Inter-annotator agreement computed via Fleiss' kappa ($\kappa$).

### 6.7 LLM-as-Judge Safeguards
- Automated LLM evaluation prompts, criteria, and outputs are logged; LLM evaluations are bounded and corroborated by deterministic NLI, lexical overlap, and citation audit checks.

---

## 7. Pre-Registration Declaration

This document constitutes **`experiment_protocol_v1`**. The hypotheses, metrics, benchmark queries, baselines, and statistical criteria defined herein are frozen. Experimental results obtained in Phase C will be interpreted strictly according to this pre-registered rubric.
