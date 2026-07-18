# DeNovo Project: Comprehensive Architecture and Methods

This document provides a complete overview of the DeNovo AI-powered drug discovery platform, covering both v1 (Attention-GIN) and v2 (4-branch multimodal) architectures, training methods, and evaluation approaches.

## Table of Contents
1. [v1 Architecture: Attention-GIN](#v1-architecture)
2. [v2 Architecture: 4-Branch Multimodal Encoder](#v2-architecture)
3. [Faithful XAI Engine](#faithful-xai)
4. [Training Methods](#training-methods)
5. [Model Performance Comparison](#model-comparison)

---

## v1 Architecture: Attention-GIN

### Overview
The v1 architecture is a Graph Isomorphism Network enhanced with Global Attention Pooling for explainable molecular toxicity prediction.

### Architecture Flow
```
SMILES Input → RDKit Parsing → Molecular Graph (V, E)
              ↓
       Embedding Layer (119-dim → 300-dim)
              ↓
       5x GINEConv Layers + BatchNorm
              ↓
       ┌─────────────────────────────────────────┐
       │  Global Attention Pooling (Novel)         │
       │  • Gate network learns atom importance     │
       │  • Returns attention weights per atom      │
       └─────────────────────────────────────────┘
              ↓
       Feature Projection (300-dim → 512-dim)
              ↓
       2-Layer MLP Preditor (Softplus)
              ↓
   Output: Prediction + Attention Weights (Explainability)
```

### Key Components

| Component | Description | Dimensions |
|-----------|-------------|------------|
| Node Embedding | Atomic number + chirality | 119 → 300 |
| GINEConv Layers | Message passing with edge features | 300-dim |
| Attention Pool | GlobalAttention with gate network | 1 output per atom |
| Prediction Head | MLP with Softplus | 512 → num_tasks |

### Attention-GINet Parameters
- `num_layer`: 5 (GINEConv layers)
- `emb_dim`: 300 (embedding dimension)
- `feat_dim`: 512 (feature dimension)
- `drop_ratio`: 0.3 (dropout)
- `num_tasks`: 12 (Tox21 endpoints)

---

## v2 Architecture: 4-Branch Multimodal Encoder

### Overview
The v2 architecture extends v1 with a 4-branch multimodal design that combines graph, SMILES, 3D conformer, and descriptor representations.

### Branch Specifications

| Branch | Input | Architecture | Output Dim |
|--------|-------|--------------|------------|
| Graph | Atom features (119-dim) | Graph Transformer (6 layers) | 256 |
| SMILES | Token IDs | ChemBERTa-2 (12 layers) | 768 |
| Conformer | 3D coords (N,3) | SchNet distance-based | 128 |
| Descriptor | 200 features | RDKit descriptors | 64 |

### Fusion Architecture
```
Branch Outputs (256, 768, 128, 64)
         ↓
   Cross-Attention Fusion
   Query: SMILES [CLS]
   Keys/Values: All branches
         ↓
   Mixture of Experts (4 experts, sparse gating)
         ↓
   Multi-task Heads (12 tasks)
```

### Training Configuration
- Optimizer: AdamW with differential LR (encoder: 1e-4, attention: 5e-4)
- Loss: Asymmetric Loss (gamma_neg=4) for class imbalance
- Scheduler: CosineAnnealingLR
- Pretraining: GraphMAE on ZINC-15

---

## Faithful XAI Engine

### Three-Stage Validation

1. **Causal Consistency Test**
   - Remove claimed toxicophores and verify prediction drops
   - Threshold: ≥0.1 prediction drop required

2. **Counterfactual Sensitivity Test**
   - Generate modified molecules, check explanation stability
   - Correlation between prediction changes and explanation changes

3. **Grounding Test**
   - Verify claimed toxicophores align with high-attention atoms
   - Adaptive threshold: κ/N where κ=2.0

### Faithfulness Score
F = √(S_causal × S_grounding)

Where S_causal and S_grounding are scores in [0,1].

### Performance
| Metric | Value |
|--------|-------|
| Constrained F | 1.000 |
| Unconstrained F | 0.054 |
| Reproduction rate | 13.5% (reduced from 36.5%) |

---

## Training Methods

### Data Processing
1. SMILES canonicalization via RDKit
2. Scaffold splitting for train/val/test separation
3. Missing label handling (-1 masking)
4. Per-task pos_weight for class imbalance

### Loss Functions
- **Asymmetric Loss**: For imbalanced molecular data
- **Uncertainty Weighted Loss**: Multi-task uncertainty weighting
- **Focal Loss**: Alternative for class imbalance

### Hyperparameter Search
- 300 Optuna trials
- AUROC maximization objective
- Targets: TOX21=0.918, BBBP=0.924, ClinTox=0.931