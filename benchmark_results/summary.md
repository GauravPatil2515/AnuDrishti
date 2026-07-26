# Final Benchmark Comparison
TOX21: 0.8023 (v1), Target: 0.918 (Uni-Mol), Gap: -0.116
BBBP: 0.8971 (v1), Target: 0.924 (Uni-Mol), Gap: -0.027
ClinTox: 0.7589 (v1), Target: 0.931 (Uni-Mol), Gap: -0.172

Loss Functions (imbalanced ~30% positive):
- FocalLoss: Final=0.0039 (best on test)
- AsymmetricLoss: Final=0.0188
- BCE: Final=0.1098

Hyperparameter Search (50 trials):
- Best AUROC: 0.7541
- Best params: lr=1.7e-4, wd=1.2e-5, dropout=0.35, hidden=128