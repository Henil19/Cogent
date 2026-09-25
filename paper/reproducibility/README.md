# Cogent Reproducibility Package

This package contains all artifacts, configurations, scripts, and instructions necessary to replicate the empirical findings and ablation studies presented in the Cogent research paper.

---

## 1. Directory Structure

```
paper/
├── manuscript/
│   ├── main.md                 # Full academic research paper draft
│   └── references.bib          # BibTeX citation records
├── figures/                    # High-resolution publication figures (300 DPI)
│   ├── fig1_overall_performance.png
│   ├── fig2_category_radar.png
│   ├── fig3_calibration_reliability.png
│   ├── fig4_latency_quality_tradeoff.png
│   ├── fig5_layer_failure_attribution.png
│   └── fig6_ablation_effects.png
├── tables/                     # Formatted Markdown, CSV, and LaTeX tables
│   ├── table1_overall_comparison.md / .csv
│   ├── table2_hypothesis_testing.md / .csv
│   ├── table3_ablation_matrix.md / .csv / .tex
│   └── table4_cost_latency_tradeoff.md
├── ablations/                  # Ablation execution results & statistics
│   └── ablation_summary.json
├── configs/                    # Frozen environmental & protocol configurations
│   └── experiment_config.json
├── benchmark/                  # Benchmark manifest & queries
│   └── benchmark_manifest.json
└── reproducibility/
    ├── README.md               # This replication guide
    └── reproduce_all.py        # One-click end-to-end replication runner
```

---

## 2. Environment Setup & Prerequisites

All experiments operate under **Python 3.14** (or Python $\ge 3.10$) with the following pinned core libraries:
- `numpy >= 1.26`
- `scipy >= 1.13`
- `matplotlib >= 3.8`
- `pandas >= 2.2`
- `tabulate >= 0.9`
- `pydantic >= 2.10`
- `pytest >= 8.0`

### Setup Virtual Environment:
```powershell
python -m venv backend/.venv
.\backend\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
pip install matplotlib pandas tabulate
```

---

## 3. Replication Protocol

### Step 1: Validate Frozen Phase C Results
Verify that the 400 main benchmark executions and summary metrics match the published tables:
```powershell
python experiments/evaluation/validate_phase_c.py
```
*Expected: All 6 audit checks PASS with zero missing traces or numerical discrepancies.*

### Step 2: Replicate Layer-Dropout & Retrieval Ablations
Run the 6 ablation configurations across the 100 benchmark queries ($N=600$ runs):
```powershell
python experiments/runners/run_ablations.py
```
*Expected: Re-generates `paper/tables/table3_ablation_matrix.md` and `paper/figures/fig6_ablation_effects.png`.*

### Step 3: Run Research Syntheses & Findings Generator
```powershell
python experiments/evaluation/research_interpretation.py
```
*Expected: Updates all 6 findings documents in `experiments/results/findings/`.*

### Or Run Everything with the Master Replication Script:
```powershell
python paper/reproducibility/reproduce_all.py
```

---

## 4. Controlled Deterministic Parameters
- Random Seed: `42`
- Temperature: `0.0`
- Max Output Tokens: `1024`
- Retrieval Depth: Top-$K = 5$
- Benchmark Version: `benchmark_v1` (100 queries)
- Corpus Version: `corpus_v1` (130 document chunks)
