# Code and Data Availability Statement

## Datasets
All experimental datasets evaluated in this study—**BBBP** (Blood-Brain Barrier Penetration), **BACE** (Beta-secretase 1 inhibition), and **TOX21** (Toxicity 21 challenge)—are publicly available from the standard **MoleculeNet** benchmark repository (https://moleculenet.org/).

## Software, Codebase, and Reproducibility Logs
Our complete, reproducible PyTorch/PyTorch Geometric codebase, custom Attention-GIN and GINE architectures, counterfactual evaluation scripts (`run_real_faithfulness.py`), multi-seed experimental training logs, and quantitative JSON evaluation reports (`benchmark_results/`) are publicly accessible under the open-source MIT License on GitHub:
**Repository**: https://github.com/GauravPatil2515/Faithful-LLM-Augmented-Explainability-for-Graph-Neural-Network-Based-Molecular-Toxicity-Prediction

## Reproducing Results
To reproduce all 5-seed empirical findings reported in Table 1 and Table 3 of the manuscript:
1. Clone the repository and install dependencies from `requirements-v2.txt`.
2. Execute `bash reproduce_paper_results.sh` from the repository root, or inspect the pre-computed JSON validation trails in `benchmark_results/VALIDATION_LOG.md`.
