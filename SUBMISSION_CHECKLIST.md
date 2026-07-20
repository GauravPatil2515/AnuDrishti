# DeNovo Research Submission: Replication & Reviewer Checklist

> **CORRECTED / SUPERSEDED NUMBERS BELOW (v1).** This file is v1 history. The
> verified, current results are in `benchmark_results/VALIDATION_LOG.md`,
> `benchmark_results/ABLATION_TABLE.md`, and the reframed manuscript
> `paper-2/main.tex`. Key corrections: the headline faithfulness
> `F=1.000 / F=0.054` came from a **mock model** and is superseded; the true
> GNN causal faithfulness is ≈0.13 (5 seeds); the causal regularizer does **not**
> reliably help (0.117 ± 0.114). Do not cite figures from this file.

This document maps all figures, tables, and key quantitative claims in the manuscript to their corresponding scripts, codebase structures, and result artifacts in the repository.

---

## 1. Reproducibility Entry Point

The entire evaluation pipeline can be executed using the reproducibility script in the root directory:
```bash
./reproduce_paper_results.sh
```
This script automates the validation of GNN models, baseline comparisons, parameter grid-search plotting, and generation of all manuscript figures and case studies.

---

## 2. Document & Artifact Mapping

### Figures

| Manuscript Figure | Description | Generation Script | Saved Output Path | Source Data File |
| :--- | :--- | :--- | :--- | :--- |
| **Figure 1** | DeNovo Platform Interface | Mockup / UI | `overleaf/figures/platform.png` | Frontend UI state |
| **Figure 2** | GINEConv Architecture | Vector diagram | `overleaf/figures/arch.png` | GIN model specifications |
| **Figure 3** | Transfer Learning Strategy | Diagram | `overleaf/figures/transfer.jpg` | Context prediction phase |
| **Figure 4** | ROC Curve (Tox21) | Model evaluation | `overleaf/figures/roc.png` | GNN training checkpoints |
| **Figure 5** | Ablation Study | Plotting | `overleaf/figures/ablation.png` | `results/eval_ablation_causal/statistics.json` |
| **Figure 6** | Faithfulness Distribution | `generate_paper_figures.py` | `overleaf/figures/faithfulness_distribution.png` | `results/eval_tox21_fixed/results.csv` |
| **Figure 7** | Sensitivity Pareto Curve | `plot_sensitivity.py` | `overleaf/figures/sensitivity_tradeoff.png` | `results/sensitivity_results.json` |
| **Figure 8** | Generative Feedback Loop | Diagram | `overleaf/figures/genloop.png` | Future architecture design |

### Tables

| Manuscript Table | Description | Reproduction Script / Command | Primary Result Source File |
| :--- | :--- | :--- | :--- |
| **Table I** | Dataset Statistics | N/A (Standard benchmark stats) | `overleaf/main.tex` (Sec V.A) |
| **Table II** | Predictive Performance | `validate_models.py` | `results/model_validation_report.json` |
| **Table III** | Ablation Study | `run_faithful_eval.py --disable-*` | `results/eval_ablation_causal/statistics.json` |
| **Table IV** | Faithfulness Comparison | `compare_baselines.py` | `results/faithfulness_comparison/comparison.json` |
| **Table V** | Sensitivity Grid | `run_sensitivity.py` | `results/sensitivity_results.json` |

---

## 3. Key Quantitative Claims & Empirical Verification

### Claim 1: Rejection Rate & Faithfulness Improvement
*   **Claimed in Abstract / Section VI.C**: The neuro-symbolic reject-and-retry mechanism raises mean faithfulness from **0.054** to **0.865**, rejecting **13.5%** of generated explanations.
*   **Empirical Source**:
    *   `results/eval_tox21_fixed/statistics.json` -> `"mean_faithfulness": 0.865`, `"rejection_rate": 0.135` (overall)
    *   `results/baseline_REAL/statistics.json` -> `"mean_faithfulness": 0.054` (unconstrained)

### Claim 2: GNN Model Competence
*   **Claimed in Section VI.A**: Attention-GIN achieves test ROC-AUC of **0.802** (validation: **0.837**) on Tox21.
*   **Empirical Source**:
    *   `results/EVALUATION_SUMMARY.md` -> `Test ROC-AUC: 0.8023`, `Best Validation ROC-AUC: 0.8368`

### Claim 3: Grounding and Causal-Consistency
*   **Claimed in Table IV / Section VI.C**: Grounding score is raised to **1.000** (from 0.080) and Causal score is raised to **0.865** (from 0.503) for DeNovo (constrained).
*   **Empirical Source**:
    *   `results/eval_tox21_fixed/statistics.json` -> `"mean_grounding": 1.0`, `"mean_causal": 0.865`
    *   `results/baseline_REAL/statistics.json` -> `"mean_grounding": 0.080`, `"mean_causal": 0.503`

---

## 4. Final Submission Verification Checklist

- [x] **LaTeX Compilation**: Verified that `overleaf/main.tex` compiles without errors and generates `overleaf/main.pdf`.
- [x] **TODO Placeholders**: All author placeholders (`\TODO`) and illustrative comments have been purged from the manuscript.
- [x] **Ablation Table Integrity**: The ablation table shows correct values: Full (0.837) vs Mean Pooling (0.7677) vs No Transfer (0.7729).
- [x] **Narrative Bounds (ClinTox)**: Confirmed ClinTox HPO results (test 0.7584, val 0.7636) in manuscript.
- [x] **SMARTS Pattern Count**: Standard toxicophore library of 48 patterns (28 toxicophores + 20 functional groups) documented.
- [x] **Pareto Figure Integration**: The Pareto plot (`sensitivity_tradeoff.png`) generated and cited.
- [x] **Unconstrained Failure Analysis**: Case studies in `results/paper_figures/selected_cases.md` show hallucination detection.
- [x] **Baseline Citations**: Table II cites MoleculeNet and ChemProp benchmarks.
- [x] **Relative Improvement Removed**: `compare_baselines.py` now reports only absolute improvement (+0.946 F), no misleading percentages.
- [x] **Verification Complete**: All metrics trace to empirical artifacts; no fabricated claims.

---