# ADMET Model Training Plan

## Complete Guide for Training and Integrating GIN Models

**Date:** December 23, 2025  
**Author:** Gaurav Patil  
**Status:** Planning Phase

---

## 1. Executive Summary

### Objective

Train and integrate 6 Graph Isomorphism Network (GIN) models for comprehensive ADMET property prediction:

| Model | Property | Type | Target Metrics |
|-------|----------|------|----------------|
| **Tox21** | Toxicity (12 endpoints) | Classification | ROC-AUC ≥ 0.82 ✅ (Done: 0.8368) |
| **ClinTox** | Clinical Toxicity (2 endpoints) | Classification | ROC-AUC ≥ 0.90 |
| **BBBP** | Blood-Brain Barrier Penetration | Classification | ROC-AUC ≥ 0.85 |
| **Caco2** | Intestinal Absorption | Regression | RMSE ≤ 0.5 |
| **Clearance** | Metabolic Clearance | Regression | RMSE ≤ 0.6 |
| **HLM_CLint** | Hepatic Microsomal Clearance | Regression | RMSE ≤ 0.55 |

### Current Status

- ✅ Tox21: Trained (ROC-AUC 0.8368)
- ❌ ClinTox: Architecture only
- ❌ BBBP: Architecture only
- ❌ Caco2: Architecture only
- ❌ Clearance: Architecture only
- ❌ HLM_CLint: Architecture only

---

## 2. Directory Structure

```
DeNovo-main/
├── MODELS/                           # GIN model packages
│   ├── tox21_model_full_package/     # Tox21 (toxicity)
│   ├── bbbp_model_full_package/      # BBBP (distribution)
│   ├── caco2_model_full_package/     # Caco2 (absorption)
│   ├── clearance_model_full_package/ # Clearance (metabolism)
│   ├── hlm_clint_model_full_package/ # HLM CLint (metabolism)
│   └── clintox_model_package/        # ClinTox (to be created)
│
├── results/
│   └── trained_models/               # All trained weights
│       ├── attention_gin_model.pth   # Tox21 ✅
│       ├── bbbp_gin_model.pth        # BBBP (to train)
│       ├── caco2_gin_model.pth       # Caco2 (to train)
│       ├── clearance_gin_model.pth   # Clearance (to train)
│       ├── hlm_clint_gin_model.pth   # HLM CLint (to train)
│       └── clintox_gin_model.pth     # ClinTox (to train)
│
├── training/                         # Training scripts and logs
│   ├── train_all_models.py           # Master training script
│   ├── training_config.yaml          # Training configuration
│   └── logs/                         # Training logs
│
└── docs/
    └── MODEL_TRAINING.md             # This document
```

---

## 3. Training Schedule

### Phase 1: Data Preparation (Day 1)

- [ ] Verify all datasets are present in each model package
- [ ] Check data format compatibility
- [ ] Create unified data loading utilities

### Phase 2: Model Training (Days 2-5)

| Day | Model | Est. Time | GPU Required |
|-----|-------|-----------|--------------|
| Day 2 | BBBP | 2-3 hours | RTX 3050/3060 |
| Day 2 | ClinTox | 2-3 hours | RTX 3050/3060 |
| Day 3 | Caco2 | 3-4 hours | RTX 3050/3060 |
| Day 4 | Clearance | 3-4 hours | RTX 3050/3060 |
| Day 5 | HLM_CLint | 3-4 hours | RTX 3050/3060 |

### Phase 3: Validation & Integration (Day 6-7)

- [ ] Run comprehensive validation on all models
- [ ] Integrate into UnifiedADMETPredictor
- [ ] Update API endpoints
- [ ] Test end-to-end pipeline

---

## 4. Training Commands

### 4.1 BBBP Model (Blood-Brain Barrier Penetration)

```powershell
cd MODELS\bbbp_model_full_package
python finetune.py --task bbbp --epochs 100 --batch_size 32 --lr 0.0001

# After training, copy weights:
copy models\checkpoint_best.pth ..\..\results\trained_models\bbbp_gin_model.pth
```

### 4.2 ClinTox Model (Clinical Toxicity)

```powershell
# First create ClinTox package (copy from Tox21 and modify)
cd MODELS\tox21_model_full_package
python finetune.py --task clintox --epochs 100 --batch_size 32 --lr 0.0001
```

### 4.3 Caco2 Model (Intestinal Permeability)

```powershell
cd MODELS\caco2_model_full_package
python finetune.py --task caco2 --epochs 100 --batch_size 32 --lr 0.0001

# Copy weights:
copy models\checkpoint_best.pth ..\..\results\trained_models\caco2_gin_model.pth
```

### 4.4 Clearance Model

```powershell
cd MODELS\clearance_model_full_package
python finetune.py --task clearance --epochs 100 --batch_size 32 --lr 0.0001

# Copy weights:
copy models\checkpoint_best.pth ..\..\results\trained_models\clearance_gin_model.pth
```

### 4.5 HLM CLint Model

```powershell
cd MODELS\hlm_clint_model_full_package
python finetune.py --task hlm_clint --epochs 100 --batch_size 32 --lr 0.0001

# Copy weights:
copy models\checkpoint_best.pth ..\..\results\trained_models\hlm_clint_gin_model.pth
```

---

## 5. Training Configuration

### Recommended Hyperparameters

```yaml
# training_config.yaml
common:
  device: cuda
  seed: 42
  early_stopping_patience: 50

classification_models:  # Tox21, ClinTox, BBBP
  epochs: 100
  batch_size: 32
  learning_rate: 0.0001
  attention_lr: 0.0005
  pos_weight: 3.0  # For imbalanced data
  dropout: 0.3

regression_models:  # Caco2, Clearance, HLM_CLint
  epochs: 150
  batch_size: 32
  learning_rate: 0.0001
  dropout: 0.3
  loss: MSE
```

---

## 6. Integration Plan

### 6.1 Update UnifiedADMETPredictor

After training, update `backend/models/unified_predictor.py`:

```python
# Add new model loading methods
def _load_bbbp_model(self):
    model_path = Path(__file__).parent.parent.parent / "results" / "trained_models" / "bbbp_gin_model.pth"
    # Load model...

def _load_caco2_model(self):
    model_path = Path(__file__).parent.parent.parent / "results" / "trained_models" / "caco2_gin_model.pth"
    # Load model...
```

### 6.2 Update API Endpoints

In `backend/app.py`, the `/api/predict` endpoint will automatically use all models through `UnifiedADMETPredictor`.

### 6.3 Update Frontend

Update `frontend/src/pages/EnhancedPredictions.jsx` to display new ADMET properties:

- BBB Penetration (Yes/No with confidence)
- Caco2 Permeability (High/Medium/Low)
- Clearance Rate (Fast/Medium/Slow)
- HLM CLint (value in mL/min/kg)

---

## 7. Validation Checklist

### Per-Model Validation

- [ ] Training loss converged
- [ ] Validation metrics meet targets
- [ ] No overfitting (train/val gap < 10%)
- [ ] Inference works on test molecules
- [ ] Model size is reasonable (< 50 MB)

### Integration Validation

- [ ] API returns predictions for all models
- [ ] Frontend displays all ADMET properties
- [ ] Response time < 2 seconds
- [ ] No memory leaks

---

## 8. Documentation Checklist

- [ ] Update `README.md` with new model info
- [ ] Create training logs for each model
- [ ] Document final hyperparameters used
- [ ] Create model cards for each trained model
- [ ] Update `MODEL_VALIDATION_SUMMARY.md`

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| GPU memory issues | Reduce batch size to 16 |
| Training doesn't converge | Try learning rate warmup |
| Overfitting | Increase dropout, add augmentation |
| Missing data | Check dataset completeness first |
| Long training time | Use mixed precision (FP16) |

---

## 10. Quick Start Commands

### Start Training All Models (Automated)

```powershell
cd DeNovo-main
python training/train_all_models.py --config training/training_config.yaml
```

### Monitor Training

```powershell
# Watch training logs
Get-Content -Path training\logs\latest.log -Wait
```

### Validate After Training

```powershell
python validate_models.py
```

---

## 11. Next Steps

1. **Immediate**: Create `training/` folder and master training script
2. **Day 1**: Verify data availability for all models
3. **Day 2-5**: Train each model sequentially
4. **Day 6**: Integration and validation
5. **Day 7**: Documentation and testing

---

## Appendix A: Model Architecture Summary

All models use the **AttentionGINet** architecture:

- **Encoder**: 5-layer GINE convolutions
- **Hidden Dim**: 300
- **Feature Dim**: 512
- **Pooling**: GlobalAttention mechanism
- **Predictor**: 2-layer MLP with softplus activation

This architecture enables explainability through attention weights.
