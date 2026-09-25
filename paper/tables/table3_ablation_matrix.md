# Table 3: Cogent Layer-Dropout & Retrieval Ablation Analysis

| Configuration                             |   Grounding Score |   Factual F1 | Citation Precision   |    ECE |   Latency (ms) |
|:------------------------------------------|------------------:|-------------:|:---------------------|-------:|---------------:|
| Full Cogent (Reference)                   |            0.163  |       0.3578 | 0.982                | 0.2988 |          37.96 |
| Without Evidence Intelligence (-L5)       |            0.0732 |       0.1224 | 0.982                | 0.5306 |          14.1  |
| Without Transparent DAG Reasoning (-L6)   |            0.0587 |       0.0757 | 0.982                | 0.5746 |          15.9  |
| Without Epistemic Trust Calibration (-L7) |            0.1631 |       0.3637 | 0.982                | 0.1363 |          34.83 |
| Without Attribution & Explanation (-L8)   |            0.0587 |       0.0734 | N/A                  | 0.5832 |          19.17 |
| Dense Retrieval Only (FAISS)              |            0.1373 |       0.2681 | 0.982                | 0.3841 |          33.67 |
| Sparse Retrieval Only (BM25)              |            0.184  |       0.3508 | 0.977                | 0.3266 |          37.08 |

*Note: In the -L8 ablation, attribution processing is removed while preserving underlying responses; citation metrics are marked N/A rather than penalized artificially.*
