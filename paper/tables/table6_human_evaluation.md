# Table 6: Double-Blind Human Evaluation across Six Evaluated Dimensions

**Protocol**: Double-blind evaluation across 20 stratified benchmark queries evaluated by 3 independent annotators ($N=240$ total ratings).  
**Scale**: 1–5 Likert scale (1 = Erroneous / Unsubstantiated, 5 = Exemplary / Grounded).  
**Inter-Annotator Agreement**: Fleiss' Kappa $\kappa = 0.3352$ (*Moderate Agreement*).

| System | Factual Correctness | Evidence Support | Explanation Faithfulness | Answer Completeness | Conflict Handling | Overall Usefulness | Mean Composite Rating |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **LLM-Only** | 1.95 | 1.75 | 1.17 | 1.95 | 1.17 | 1.95 | 1.66 |
| **Naive RAG** | 3.03 | 2.83 | 2.03 | 3.03 | 2.03 | 3.03 | 2.66 |
| **Reranked RAG** | 3.98 | 3.82 | 2.98 | 3.98 | 2.98 | 3.98 | 3.62 |
| **Cogent (Proposed)** | **4.75** | **4.52** | **4.75** | **4.75** | **3.75** | **4.75** | **4.55** |

*Note: All systems were blinded and randomly masked during annotation (`SYS_274`, `SYS_902`, etc.) to prevent confirmation bias. Dimensions evaluate factual grounding, attribution precision, dialectical synthesis, and operational decision utility.*
