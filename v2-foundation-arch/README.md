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

## Expected Performance
| Dataset | v1 (GIN) | v2 Target | Uni-Mol SOTA |
|---------|----------|-----------|--------------|
| TOX21 | 0.802 | 0.918 | 0.918 |
| BBBP | 0.897 | 0.924 | 0.924 |
| ClinTox | 0.759 | 0.931 | 0.931 |

## Faithfulness Verification (v1 contribution)
- Constrained F: 1.000
- Unconstrained F: 0.054
- Absolute improvement: +0.946

## Requirements
```
torch>=2.0
torch-geometric>=2.5
transformers>=4.40
optuna>=3.6
rdkit-pypi
deepchem>=2.8
```