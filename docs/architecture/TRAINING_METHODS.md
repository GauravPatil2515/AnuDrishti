# DeNovo Training Methods and Configuration

## Overview

This document details the training methodologies, configurations, and hyperparameter search strategies used in both v1 (Attention-GIN) and v2 (4-branch multimodal) architectures.

---

## v1 Training Pipeline (Attention-GIN)

### Model Configuration

```yaml
model:
  num_layer: 5           # GINEConv layers
  emb_dim: 300           # Embedding dimension
  feat_dim: 512          # Feature dimension after pooling
  drop_ratio: 0.2        # Reduced dropout for better learning
  pred_n_layer: 2        # Prediction head layers
  pred_act: "softplus"   # Activation function
  pool: "attention"      # GlobalAttention pooling
```

### Training Parameters

```yaml
training:
  batch_size: 32
  epochs: 150
  learning_rate: 1e-4    # Base encoder LR
  attention_lr: 5e-4     # Higher LR for attention layer
  weight_decay: 1e-6
  patience: 50           # High patience for convergence
  min_delta: 1e-4
  grad_clip: 1.0
  use_focal_loss: true   # For class imbalance (ClinTox)
  focal_loss_gamma: 2.0
```

### Optimizer Configuration

The training uses **differential learning rates**:
- Encoder parameters: `1e-4` (standard)
- Attention gate parameters: `5e-4` (higher for faster convergence)
- Prediction head: `1e-4`

Implemented via AdamW optimizer with parameter groups.

### Loss Functions

#### Asymmetric Loss (Primary)
Used for imbalanced molecular datasets:

```
ASL = - (loss_pos + loss_neg) / mean

loss_pos = y * (1-p)^γ_pos * log(p)
loss_neg = (1-y) * p^γ_neg * log(1-p)

γ_pos = 0.0 (no focusing on positives)
γ_neg = 4.0 (strong focusing on negatives)
clip = 0.05 (probability clipping)
```

#### Uncertainty Weighted Loss (Alternative)
Multi-task uncertainty weighting:

```
L = Σᵢ (σᵢ⁻² * BCE(yᵢ, ŷᵢ) + log(σᵢ))

where σᵢ are learnable task-specific uncertainties
```

---

## v2 Training Pipeline (4-Branch Multimodal)

### Branch Configurations

| Branch | Encoder | Output Dim | Notes |
|--------|---------|------------|-------|
| Graph | GraphTransformerEncoder (6 layers) | 256 | Replaces GIN with attention |
| SMILES | ChemBERTa-2 Transformer (12 layers) | 768 | Frozen backbone |
| Conformer | SchNet (3 CF conv layers) | 128 | Distance-based features |
| Descriptor | RDKit 200 features → MLP | 64 | Physicochemical props |

### Fusion and Output

```python
# Cross-attention fusion
fusion = nn.MultiheadAttention(
    embed_dim=768,
    num_heads=8,
    dropout=0.1,
    batch_first=True
)

# Mixture of Experts
n_experts = 4
expert_gate = nn.Linear(768, 4)  # Sparse gating
expert_layers = nn.ModuleList([nn.Linear(768, 768) for _ in range(4)])

# Multi-task heads
n_tasks = 41  # Combined Tox21, BBBP, ClinTox, SIDER, BACE
task_heads = nn.ModuleList([nn.Linear(768, 1) for _ in range(n_tasks)])
```

### Pretraining Strategy

#### GraphMAE Pretraining
Self-supervised learning on ZINC-15:

```
Input: Molecular graphs
Masking: 25% random atom masking
Loss: MSE on masked atom features
Pretraining: 250,000 molecules
```

Architecture:
- Encoder: Transformer layers on masked graphs
- Decoder: Reconstructs original atom features
- Output: Reconstructed features for masked atoms only

---

## Hyperparameter Search

### Optuna Configuration

```python
def objective(trial):
    # Sample hyperparameters
    lr = trial.suggest_float('lr', 1e-5, 1e-3, log=True)
    weight_decay = trial.suggest_float('weight_decay', 1e-6, 1e-4, log=True)
    dropout = trial.suggest_float('dropout', 0.0, 0.5)
    num_heads = trial.suggest_categorical('num_heads', [4, 8, 12, 16])
    num_layers = trial.suggest_categorical('num_layers', [3, 6, 9])
    warmup_ratio = trial.suggest_float('warmup_ratio', 0.05, 0.2)
    
    return val_auc  # Maximize AUROC
```

### Search Space

| Parameter | Range | Best Value (Typical) |
|-----------|-------|-------------------|
| Learning Rate | 1e-5 to 1e-3 | 1e-4 |
| Weight Decay | 1e-6 to 1e-4 | 1e-6 |
| Dropout | 0.0 to 0.5 | 0.1-0.2 |
| Num Heads | {4, 8, 12, 16} | 8 |
| Num Layers | {3, 6, 9} | 6 |
| Warmup Ratio | 0.05 to 0.2 | ~0.1 |

### Trial Configuration
- **Number of trials**: 300 minimum
- **Sampler**: TPE (Tree-structured Parzen Estimator)
- **Pruner**: Median pruner
- **Objective**: Maximize validation AUROC

---

## Data Processing

### Scaffold Splitting

Used for better generalization (non-random):

```
Splitting: Scaffold-based
Ratio: 80% train / 10% val / 10% test
Purpose: Prevents data leakage across similar scaffolds
```

### Missing Label Handling

- Labels marked as `-1` are ignored in loss computation
- Per-task pos_weight calculated dynamically during training
- Handles incomplete assay data in MoleculeNet

### Feature Engineering

| Feature Type | Dimension | Source |
|--------------|-----------|--------|
| Atom Types | 119 | Periodic table + mask |
| Chirality | 3 | RDKit stereo |
| Bond Types | 5 | Single, double, triple, aromatic |
| Bond Direction | 3 | RDKit direction |
| RDKit Descriptors | 200 | Physicochemical |
| Morgan FP | 2048 | Circular fingerprints |

---

## Evaluation Metrics

### Classification Metrics
- **ROC-AUC**: Area under ROC curve (primary)
- **Precision-Recall AUC**: For imbalanced data
- **Accuracy**: Overall correctness

### Regression Metrics
- **RMSE**: Root mean squared error
- **MAE**: Mean absolute error
- **R²**: Coefficient of determination

### Faithfulness Metrics
- **F = √(S_causal × S_grounding)**: Composite score
- **Rejection rate**: % of explanations failing validation
- **Correlation**: Between attention and claimed toxicophores

---

## Training Commands

### v1 Training
```bash
# Train Attention-GIN on Tox21
python backend/models/train_attention_gin.py --task tox21 --epochs 150

# Evaluate trained model
python experiments/run_faithful_eval.py --model results/trained_models/attention_gin_model.pth
```

### v2 Training
```bash
# Run smoke tests on all branches
for f in v2-foundation-arch/architecture_design/*.py; do python $f; done

# Run Optuna search
python v2-foundation-arch/experiments/optuna_search/optuna_search.py --trials 10

# Run ablation study
python v2-foundation-arch/experiments/ablations/run_real_ablation.py
```

### Verification
```bash
# Validate all models
python scripts/validate_all_models.py

# Test faithfulness
python tests/test_faithfulness.py
```