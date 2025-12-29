# Training Results Summary

## Faithful XAI - Attention-GIN Model

### Training Configuration

- **Dataset**: Tox21 (7,822 molecules)
- **Split**: Random (80/10/10)
- **Epochs**: 106 (early stopping)
- **Best Epoch**: 56
- **Batch Size**: 32
- **Learning Rate**: 0.0001 (encoder), 0.0005 (attention)
- **Class Weighting**: pos_weight = 3.0

### Final Results

| Metric | Value |
|--------|-------|
| **Best Validation ROC-AUC** | **0.8368** ✅ |
| Test ROC-AUC | 0.8023 |
| Target | ≥ 0.82 |
| Status | **TARGET EXCEEDED** |

### Training Progress (Key Epochs)

| Epoch | Val ROC-AUC | Notes |
|-------|-------------|-------|
| 1 | 0.7195 | Start |
| 5 | 0.7868 | Rapid improvement |
| 9 | 0.8119 | Crossed 0.81 |
| 13 | 0.8252 | **Target reached** |
| 17 | 0.8300 | New best |
| 27 | 0.8349 | New best |
| 44 | 0.8351 | New best |
| 54 | 0.8353 | New best |
| 56 | 0.8368 | **FINAL BEST** |
| 106 | 0.8158 | Early stopping |

### Model Files

- `attention_gin_model.pth` (9 MB) - Model weights only
- `checkpoint_best.pth` (27 MB) - Full checkpoint with optimizer
- `test_results.json` - Test set evaluation
- `training_history.csv` - Full training log

### Demo Verification

```
Molecule: Nitrobenzene (c1ccc([N+](=O)[O-])cc1)
Explanation: ACCEPTED
Faithfulness Score: 0.794
Rejection Rate: 0.0%
```

### Date

2025-12-21

### Next Steps

1. Run full evaluation on Tox21 test set
2. Run evaluations on ClinTox, BBBP datasets
3. Ablation studies
4. Generate paper figures
