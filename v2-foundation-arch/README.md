# v2-foundation-arch

Multimodal Molecular Foundation Model with Faithful Causal Explanation.

## Overview
4-branch architecture: Graph Transformer + SMILES + 3D Conformer + Descriptors

## Structure
```
v2-foundation-arch/
├── architecture_design/      # Model components
│   ├── multimodal_encoder.py # 4-branch fusion
│   ├── graph_transformer_branch.py
│   ├── smiles_branch.py
│   ├── conformer_branch.py
│   └── descriptor_branch.py
├── experiments/             # Training and evaluation
│   ├── optuna_search/      # Hyperparameter optimization
│   ├── pretraining/        # GraphMAE self-supervised
│   ├── losses/             # Asymmetric/UW losses
│   ├── ablations/          # Systematic ablation study
│   ├── ensemble/           # MoE ensemble + verification
│   └── training/           # Training pipeline
├── baselines/              # SOTA baseline reproduction
├── benchmark_results/      # Metrics and comparison
├── paper_config/           # LaTeX macros and paper config
└── docs/                   # Documentation
    ├── README_ARCHITECTURE.md
    ├── README_TRAINING.md
    └── README_EXPERIMENTS.md
```

## Quick Start
```bash
# Run smoke tests
for f in v2-foundation-arch/architecture_design/*.py; do
    python $f
done

# Run ablation study
python v2-foundation-arch/experiments/ablations/run_real_ablation.py
```

## Expected Performance (REAL, scaffold split, 5 seeds)
| Dataset | GINE 5-seed mean±std | 95% CI | ChemProp D-MPNN (seed 42) |
|---------|----------------------|--------|---------------------------|
| BBBP    | 0.8494 ± 0.0229 | [0.831,0.868] | 0.8913 |
| BACE    | 0.8493 ± 0.0442 | [0.818,0.889] | 0.8833 |
| TOX21   | 0.7794 ± 0.0248 | [0.761,0.799] | 0.7928 |

Competitive with, but not robustly superior to, ChemProp (single seed).

## Faithfulness Verification (GNN-level, verified)
- True causal-faithfulness score (5 seeds): 0.128 ± 0.027 (range 0.083–0.150)
- Standard GNN training does NOT induce toxicophore→toxicity causality
  (removing a toxicophore usually does not drop the prediction).
- Causal regularizer improves alignment (0.058 → 0.092) but is insufficient.
- NOTE: the earlier "Constrained F: 1.000 / Unconstrained F: 0.054" figures came
  from a mock model (`faithfulness_v2_validation.json`) and are superseded.
- Reframed manuscript: `paper-2/main.tex`; audit trail: `benchmark_results/VALIDATION_LOG.md`,
  `benchmark_results/ABLATION_TABLE.md`.

## Requirements
```
torch>=2.0
torch-geometric>=2.5
transformers>=4.40
optuna>=3.6
rdkit-pypi
deepchem>=2.8
```