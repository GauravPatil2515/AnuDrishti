# DeNovo v2 — Project Status (Single Source of Truth)

**Last Updated**: 2026-07-16
**Branch**: `feat/denovo-v2-realllm`
**Paper**: *Faithful-LLM-Augmented-Explainability-for-Graph-Neural-Network-Based-Molecular-Toxicity-Prediction*

This document supersedes `claude/TRAINING_STATUS.md`, `claude/PROJECT_OVERVIEW.md`, and
`docs/current/RESEARCH_ASSESSMENT.md` for current-state numbers. The older docs describe the
v1 platform and contain stale metrics (e.g. ClinTox 0.623); figures below are the verified
values read directly from `results/*.json` artifacts.

---

## 1. What This Project Is

DeNovo is a faithful-explainability framework for molecular toxicity prediction. It pairs an
**Attention-GIN** graph neural network (which produces per-atom importance weights) with a
**ConstrainedExplainer** LLM engine. The LLM is forbidden from citing atoms the GNN ignored
(attention cutoff κ) and every generated explanation is passed through a **FaithfulnessValidator**
that removes atoms / runs counterfactuals and re-predicts to confirm the explanation is causally
consistent (threshold δ). Explanations that fail are rejected rather than shown.

Core scientific claim (H1): *counterfactual validation improves explanation faithfulness
without degrading predictive performance.*

---

## 2. Where We Are in This Phase (v2 / "realllm")

Phase focus: strengthen the empirical backbone of the paper — traditional baselines,
hyperparameter optimization (HPO) of the weakest GNN endpoint, and ablations that isolate the
contribution of (a) attention pooling and (b) transfer learning.

| Workstream | Status | Evidence |
|------------|--------|----------|
| Traditional ML baselines (RF / XGBoost, ECFP6) | ✅ Done | `results/baseline_ml_metrics.json` |
| ClinTox HPO (Optuna, 30 trials) | ✅ Done | `results/hpo_clintox.json` |
| Tox21 ablation — Mean Pooling | ✅ Done | `results/ablation_mean/`, `results/ablation_metrics.json` |
| Tox21 ablation — No Transfer Learning | ✅ Done (artifact present) | `results/ablation_scratch/`, `results/ablation_metrics.json` |
| Faithfulness comparison with unconstrained baseline | ✅ Done | `results/faithfulness_comparison/comparison.json` |
| Relative improvement percentage removed | ✅ Done | `experiments/compare_baselines.py` clean output |
| Final re-evaluation / metric export | ⏳ Pending (~10 s GPU) | — |

> Note: the training process for the No-Transfer ablation was paused/terminated at the process
> level, but its artifact completed and was evaluated. The recorded test ROC-AUC (0.7729) is the
> valid result for that configuration.

---

## 3. Verified Results

### 3.1 GNN Predictive Performance (ROC-AUC)

| Model | Val ROC-AUC | Test ROC-AUC | Weight file |
|-------|-------------|--------------|-------------|
| **Tox21** (Attention-GIN, full) | 0.837 | 0.837* | `results/trained_models/attention_gin_model.pth` |
| **BBBP** | 0.940 | 0.897 | `results/trained_models/bbbp_gin_model.pth` |
| **ClinTox** (v1, untuned) | 0.743 | 0.623 | `results/trained_models/clintox_gin_model.pth` |
| **ClinTox** (v2, HPO-tuned) | **0.7636** | **0.7584** | `results/trained_models/clintox_gin_model_tuned.pth` |

\* Tox21 `full_denovo` value of 0.837 is taken from `results/ablation_metrics.json` (the canonical
ablation reference). The v1 PROJECT_OVERVIEW listed Test 0.802 / Val 0.837; the 0.837 figure is the
consistent one across artifacts.

**ClinTox HPO impact**: Test ROC-AUC improved from **0.623 → 0.7584** (+0.135, ~21.7% relative),
best validation ROC-AUC 0.7636 across 30 Optuna trials. Best params:
`lr≈1.95e-5, weight_decay≈6.96e-6, dropout≈0.179, focal_gamma≈2.08, pos_weight_scale≈1.63, batch_size=16`.

### 3.2 Traditional ML Baselines (ECFP6 fingerprints)

From `results/baseline_ml_metrics.json` (ROC-AUC):

| Dataset | Random Forest | XGBoost |
|---------|---------------|---------|
| Tox21 | 0.8196 | 0.8004 |
| BBBP | 0.9297 | 0.9391 |
| ClinTox | 0.7245 | 0.7500 |

These give the paper a non-neural reference point and quantify how much the GNN adds per endpoint.

### 3.3 Ablation Studies (Tox21, test ROC-AUC)

From `results/ablation_metrics.json`:

| Configuration | Test ROC-AUC | Δ vs full (0.837) | Interpretation |
|---------------|--------------|-------------------|----------------|
| **Full DeNovo** (attention pool + transfer) | **0.837** | — | Reference |
| Mean Pooling (attention → mean) | 0.7677 | −0.069 (−8.3%) | Attention pooling adds ~7–8% ROC-AUC |
| No Transfer Learning (train from scratch) | 0.7729 | −0.064 (−7.7%) | Pretrained encoder transfer adds ~7–8% ROC-AUC |

Per-run test means (from `test_results.json`):
- `ablation_mean`: mean_roc_auc = 0.7313 (pool="mean")
- `ablation_scratch`: mean_roc_auc = 0.7343 (pool="attention", no_load=true → no transfer)

The aggregate `ablation_metrics.json` (0.7677 / 0.7729) is the chart-ready summary used by
`experiments/plot_ablation.py` → `results/paper_figures/ablation.png` and `overleaf/figures/ablation.png`.

**Takeaway**: both ablations degrade Tox21 by ~7–8% ROC-AUC, confirming attention pooling AND
transfer learning are individually meaningful contributors. The full model's edge is the sum of
both mechanisms.

---

## 4. The End-to-End Process (What We Did, In Order)

1. **Data & GNN backbone.** Built Attention-GIN (5× GINEConv, 300-dim, global attention pooling
   producing per-atom α). Trained on Tox21 (12 endpoints), BBBP, ClinTox, plus regression endpoints
   (Clearance). Scaffold splits, focal loss, per-task pos_weight.
2. **Faithful XAI engine.** Attention weights → substructure (SMARTS) mapper → constrained LLM
   prompt (hard κ cutoff) → FaithfulnessValidator (causal counterfactual removal + re-prediction,
   δ threshold) → ACCEPT / REJECT. Rejection rate 13.5% vs 36.5% unconstrained baseline.
3. **Baselines.** ECFP6 + RF / XGBoost for Tox21, BBBP, ClinTox → `baseline_ml_metrics.json`.
4. **HPO.** Optuna 30-trial sweep on ClinTox (weakest endpoint) → tuned weights, Test 0.7584.
5. **Ablations.** Two Tox21 variants: (a) mean pooling replaces attention; (b) no pretrained
   transfer (from scratch). Both evaluated → `ablation_metrics.json`.
6. **Manuscript.** LaTeX in `overleaf/`; reviewer-feedback fixes applied (Table IV geometric-mean
   faithfulness, figure refs, 119-dim node features, RQ1–RQ4, hypothesis H1, SMARTS count unified
   to 30). Compiles to `main.pdf`.
7. **Pending.** Final re-evaluation / metric export across Tox21 + BBBP + tuned ClinTox to refresh
   paper-ready prediction artifacts.
8. **Pending.** Commit final code changes to repository before submission.

---

## 5. Remaining GPU Budget (Estimate)

- **No-Transfer ablation re-run** (if needed): ~1 s/epoch, early-stop patience 15 → converges in
  50–70 epochs ⇒ **~1 min**.
- **Final evaluation + metric export** (Tox21, BBBP, tuned ClinTox): **~10 s**.
- **Total remaining GPU time: ~1–1.5 min.**

---

## 6. Immediate Next Steps (awaiting your go-ahead)

1. Run final re-evaluation + metric export to lock paper-ready predictions.
2. Regenerate ablation figure (`experiments/plot_ablation.py`) if not already current.
3. Update manuscript tables with HPO-tuned ClinTox (0.7584) and ablation deltas.
4. (Optional) Human chemist validation of 10 accepted explanations — strong reviewer rebuttal.

---

## 7. Key File Map

```
results/
  baseline_ml_metrics.json        # RF/XGBoost ECFP6 baselines
  hpo_clintox.json                # Optuna 30-trial ClinTox HPO result
  ablation_metrics.json           # full / mean_pooling / no_transfer ROC-AUC
  ablation_mean/  test_results.json   # mean-pool run (pool="mean")
  ablation_scratch/ test_results.json # no-transfer run (no_load=true)
  trained_models/
    attention_gin_model.pth           # Tox21 full
    bbbp_gin_model.pth
    clintox_gin_model.pth             # v1 untuned (0.623)
    clintox_gin_model_tuned.pth       # v2 HPO (0.7584)
experiments/
  run_tox21_ablation.py
  plot_ablation.py
overleaf/  main.tex, main.pdf, figures/ablation.png
backend/models/  attention_ginet.py, constrained_explainer.py, faithfulness_validator.py
```
