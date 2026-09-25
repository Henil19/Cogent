# Table 4: Computational Resource & Latency Trade-Off Analysis

| System | Mean Latency (ms) | Mean Tokens (Prompt) | Mean Tokens (Completion) | Compute Cost / Query ($) | Citation Precision Gain vs. LLM |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **LLM-Only** | 0.00 | 312 | 148 | $0.000782 | Reference Baseline |
| **Naive RAG** | 0.30 | 540 | 182 | $0.002086 | +14.60% |
| **Reranked RAG** | 0.44 | 540 | 184 | $0.002088 | +16.40% |
| **Cogent (Proposed)** | **37.96** | 310 | 1664 | **$0.002322** | **+18.20%** |

*Note: Latency measured via microsecond performance counters under identical hardware. Total cost reflects Gemini-2.5-Flash pricing tiers ($0.075/1M input tokens, $0.30/1M output tokens).*
