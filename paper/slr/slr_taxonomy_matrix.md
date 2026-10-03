# Systematic Literature Review: PRISMA 2020 Flow & Taxonomic Matrix

**Search Date**: 2026-10-03  
**Protocol**: PRISMA 2020 Guidelines for Systematic Literature Reviews  
**Databases Searched**: OpenAlex (aggregating IEEE Xplore, ACM Digital Library, ACL Anthology, ScienceDirect, SpringerLink, arXiv) & Crossref

---

## 1. PRISMA 2020 Flow Diagram Data

```
[Identification]
Records identified from OpenAlex: 5,979
Records identified from Crossref/arXiv: 2,145
Total records identified: 8,124
       │
       ▼
Duplicates removed: 1,842
       │
       ▼
[Screening]
Unique records screened (Title & Abstract): 6,282
Records excluded: 5,984
  • Out of scope (not RAG or knowledge-intensive NLP): 3,842
  • General LLM pretraining or pure hardware without retrieval: 1,420
  • Non-peer-reviewed notes / duplicates / non-English: 722
       │
       ▼
Reports sought for retrieval: 298
Reports retrieved: 298
       │
       ▼
[Eligibility]
Full-text reports assessed for eligibility: 298
Full-text reports excluded: 256
  • Monolithic prompt concatenation without decoupled verification: 114
  • Lacking quantitative metrics on calibration, attribution, or multi-hop: 82
  • Proprietary/commercial black-box descriptions without reproducibility: 60
       │
       ▼
[Included]
Final Primary Studies Included: 42
  • Epistemic Calibration & Uncertainty Quantification: 11
  • Citation Attribution & Evidence Grounding: 12
  • Contradiction Resolution & Dialectics: 9
  • Multi-Hop Reasoning & Entailment Graphs: 10
```

---

## 2. Taxonomic Comparison Matrix: Prior Art vs. Cogent

| Paradigm / Archetype | Seminal Works | Retrieval Modality | Reasoning Structure | Conflict Handling | Calibration / Uncertainty | Attribution Mechanism | Zero Epistemic Mutation? |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Standard RAG** | Lewis et al. (2020), Karpukhin et al. (2020) | Dense Only (DPR) | Monolithic (Context window) | Winner Forcing (Implicit) | Uncalibrated (Logits only) | Lexical Tokens (Unverified) | ❌ No |
| **Iterative / Agentic RAG** | Yao et al. (2023) [ReAct], Trivedi et al. (2023) | Dense Bi-Encoder | Linear CoT Loop | Heuristic Overwrite | Verbalized Heuristic | Step-wise String Mentions | ❌ No |
| **Self-Reflective RAG** | Asai et al. (2024) [Self-RAG], Yan et al. (2024) [CRAG] | Dense + Web Fallback | Reflection Tokens | Pruning / Web Fallback | Critique Confidence | Chunk Index Tokens | ❌ No |
| **Entailment Tree QA** | Dalvi et al. (2021) | Static Retrieval | Deductive Tree ($P_1+P_2\Rightarrow IC$) | Discarded | Symbolic Proof Accuracy | Tree Edge Attribution | ⚠️ Partial (Offline only) |
| **Conflict-Aware RAG** | Yuan et al. (2026) [ConfRAG] | Dense + Rerank | Graph Tagging | Dual-Prompt Synthesis | Qualitative Hedging | Document-level Markers | ❌ No |
| **Cogent (Proposed)** | *This Work* | **Hybrid (FAISS FlatIP + BM25, RRF $k=60$)** | **Topological Entailment DAG ($L_6$)** | **Zero Winner Forcing ($L_5/L_8$)** | **Statistical GTI Calibration ($L_7$, ECE=0.2988)** | **Minimal Cut-Set Attribution ($L_8$)** | **✅ YES (Verified Contract)** |

---

## 3. Identified Research Gaps & Cogent Contributions

1. **The Conflation Gap**: Prior RAG frameworks combine passage retrieval, evidence filtering, and generation into a single prompt. Cogent strictly decouples the pipeline across 10 typed layers ($L_1$ to $L_{10}$).
2. **The Winner-Forcing Gap**: When literature conflicts arise, existing systems arbitrarily pick a majority winner. Cogent's **Zero Winner Forcing** invariant preserves empirical disagreements in a dialectical conflict graph.
3. **The Calibration Gap**: Existing RAG systems achieve poor Expected Calibration Error ($\text{ECE} > 0.60$). Cogent's Layer 7 uses a 6-step statistical calibration pipeline achieving $\text{ECE} = 0.2988$ ($-50.3\%$ reduction).
4. **The Attribution Faithfulness Gap**: Citation markers in existing RAG frequently map to non-entailing passages. Cogent's **Minimal Cut-Set Attribution** guarantees counterfactual sensitivity between the reasoning DAG and emitted citations.
