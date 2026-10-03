# Table 5: Distractor & Noise Robustness Analysis

Evaluates system resilience under increasing distractor noise (0%, 10%, 25%, 50% irrelevant passages injected into corpus).

| System | Noise Level | Factual F1 | Citation Precision | ECE $\downarrow$ | Distractor Infiltration Rate | F1 Degradation (vs. Clean) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Naive RAG** | 0% | 0.0938 | 0.9667 | 0.6262 | 0.0% | +0.0% |
| **Naive RAG** | 10% | 0.0832 | 0.9667 | 0.6368 | 54.2% | -11.3% |
| **Naive RAG** | 25% | 0.0874 | 0.9500 | 0.6326 | 83.3% | -6.8% |
| **Naive RAG** | 50% | 0.0903 | 0.9583 | 0.6297 | 83.3% | -3.7% |
| **Reranked RAG** | 0% | 0.2483 | 0.9583 | 0.5717 | 0.0% | +0.0% |
| **Reranked RAG** | 10% | 0.2142 | 0.9417 | 0.6058 | 62.5% | -13.7% |
| **Reranked RAG** | 25% | 0.1587 | 0.9417 | 0.6613 | 75.0% | -36.1% |
| **Reranked RAG** | 50% | 0.1589 | 0.9333 | 0.6611 | 75.0% | -36.0% |
| **Cogent (Proposed)** | 0% | 0.3641 | 0.9333 | 0.2933 | 0.0% | +0.0% |
| **Cogent (Proposed)** | 10% | 0.3591 | 0.9333 | 0.3051 | 37.5% | -1.4% |
| **Cogent (Proposed)** | 25% | 0.3513 | 0.9333 | 0.3211 | 54.2% | -3.5% |
| **Cogent (Proposed)** | 50% | 0.3590 | 0.9333 | 0.3105 | 62.5% | -1.4% |
