# Table 1: Overall System Performance Comparison

| System        |   Grounding Score |   Factual F1 |   Citation Precision |   Claim Support Ratio |   Conflict Preservation |    ECE |   Mean Latency (ms) | Total Cost ($)   |
|:--------------|------------------:|-------------:|---------------------:|----------------------:|------------------------:|-------:|--------------------:|:-----------------|
| LLM-Only      |            0.075  |       0.3038 |                0.8   |                0      |                    0.85 | 0.2962 |                0    | $0.000782        |
| Naive RAG     |            0.7066 |       0.1122 |                0.946 |                1      |                    0.85 | 0.6078 |                0.3  | $0.002086        |
| Reranked RAG  |            0.715  |       0.2187 |                0.964 |                1      |                    0.85 | 0.6013 |                0.44 | $0.002088        |
| Cogent (Ours) |            0.163  |       0.3578 |                0.982 |                0.1489 |                    0.85 | 0.2988 |               37.96 | $0.232209        |
