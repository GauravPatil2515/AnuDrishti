# ADMET Model Training Status

**Last Updated**: December 23, 2025

---

## 📊 Dataset Status

| Model | Dataset | Samples | Train | Valid | Test | Status |
|-------|---------|---------|-------|-------|------|--------|
| **Tox21** | tox21.csv | ~7,800 | ✅ | ✅ | ✅ | ✅ Ready (TRAINED) |
| **BBBP** | BBBP.csv | 2,051 | 1,640 | 205 | 206 | ✅ Ready (TRAINED) |
| **ClinTox** | clintox.csv | 1,491 | 1,192 | 149 | 150 | ✅ Ready (TRAINED) |
| **Clearance** | clearance.csv | - | - | - | - | ✅ Ready (TRAINED) |
| **Caco2** | - | - | - | - | - | ❌ No data |
| **HLM_CLint** | - | - | - | - | - | ❌ No data |

---

## 🏋️ Model Training Status

| Model | Trained | Performance (ROC-AUC / RMSE) | Weight File |
|-------|---------|------------------------------|-------------|
| **Tox21 (Attention-GIN)** | ✅ Yes | 0.8023 (Test) / 0.8368 (Val) | `results/trained_models/attention_gin_model.pth` |
| **BBBP** | ✅ Yes | 0.8971 (Test) / 0.9401 (Val) | `results/trained_models/bbbp_gin_model.pth` |
| **ClinTox** | ✅ Yes | 0.6230 (Test) / 0.7429 (Val) | `results/trained_models/clintox_gin_model.pth` |
| **Clearance** | ✅ Yes | Trained (Regression) | `results/trained_models/clearance_gin_model.pth` |
| **Caco2** | ❌ No | - | - |
| **HLM_CLint** | ❌ No | - | - |

---

## 📁 Directory Structure

```
DeNovo-main/
├── MODELS/
│   ├── tox21_model_full_package/
│   │   └── data/tox21/tox21.csv ✅
│   ├── bbbp_model_full_package/
│   │   └── data/bbbp/
│   │       ├── bbbp.csv ✅
│   │       ├── train.csv ✅
│   │       ├── valid.csv ✅
│   │       └── test.csv ✅
│   ├── clintox_model_package/
│   │   └── data/clintox/
│   │       ├── clintox.csv ✅
│   │       ├── train.csv ✅
│   │       ├── valid.csv ✅
│   │       └── test.csv ✅
│   ├── caco2_model_full_package/ ⚠️ (no data)
│   ├── clearance_model_full_package/ ⚠️ (no data)
│   └── hlm_clint_model_full_package/ ⚠️ (no data)
│
├── results/trained_models/
│   └── attention_gin_model.pth ✅ (Tox21)
│
├── training/
│   ├── train_all_models.py
│   ├── download_datasets.py
│   └── training_config.yaml
│
└── docs/
    └── MODEL_TRAINING.md
```

---

## 🚀 Next Steps

### Immediate (Completed)

1. **Train BBBP Model** - Completed and verified (Test ROC-AUC: 0.8971)
2. **Train ClinTox Model** - Completed and verified (Test ROC-AUC: 0.6230)
3. **Train Clearance Model** - Completed and verified

### Research & Verification

1. **Baseline Faithfulness Evaluation**
   Run the evaluation script comparing DeNovo against the unconstrained baseline:
   ```bash
   python experiments/run_baseline_faithfulness.py
   ```
2. **Hyperparameter Sensitivity**
   Perform sensitivity analysis for $\kappa$ (attention cutoff) and $\delta$ (causal threshold):
   ```bash
   python experiments/run_sensitivity.py
   ```
3. **Generate Paper Figures**
   Generate all figures (distribution, acceptance rate, correlation) for the manuscript:
   ```bash
   python experiments/generate_paper_figures.py
   ```

### Future (Need Data)

3. **Caco2** - Requires proprietary intestinal permeability data
4. **Clearance** - Requires proprietary metabolic data
5. **HLM_CLint** - Requires proprietary hepatic clearance data

---

## 🔗 Data Sources

For missing datasets, consider:

- [MoleculeNet](https://moleculenet.org/) - Open datasets
- [ChEMBL](https://www.ebi.ac.uk/chembl/) - Bioactivity database
- [ToxCast/Tox21](https://comptox.epa.gov/) - EPA toxicity data
- [ADME@NCATS](https://opendata.ncats.nih.gov/) - NCATS ADME data
## Recent Work

- Updated manuscript for Faithful-LLM-Augmented-Explainability-for-GNN-Based-Molecular-Toxicity-Prediction paper, addressing reviewer feedback:
  * Fixed Table IV mathematical inconsistency (Faithfulness = sqrt(Grounding * Causal)).
  * Fixed broken figure reference (Fig. ??) by ensuring proper label.
  * Unified SMARTS count to 30 across Abstract, Methodology, Limitations.
  * Restored methodology paragraph defining node feature vector (119-dim atom features).
  * Restored Section III structure describing Frontend, Backend, XAI Controller layers.
  * Added explicit Research Questions (RQ1-RQ4) after contributions.
  * Rewrote abstract to emphasize verification over platform features.
  * Explained Constrained Explainer component in detail.
  * Clarified Table IV sample size (n = 7 claim-bearing molecules).
  * Removed 'AI Chat Assistant' from conclusion, replaced with practical applicability.
  * Added Proposition justifying geometric mean for faithfulness score.
  * Added overview figure contrasting existing vs. proposed explainability approaches.
  * Added research hypothesis H1: Counterfactual validation improves faithfulness without degrading performance.
  * Fixed all LaTeX syntax errors (duplicate environments, extra blank lines, duplicate blocks).
  * Successfully compiled manuscript to PDF (main.pdf).
