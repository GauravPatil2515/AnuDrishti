# DeNovo Model Comparison Table

## Performance Comparison

| Model | Dataset | Task | AUROC/Test | AUROC/Val | RMSE/MAE | Notes |
|-------|---------|------|------------|-----------|----------|-------|
| **Attention-GIN (v1)** | TOX21 | Toxicity (12 endpoints) | 0.802 | 0.837 | - | With attention pooling |
| Attention-GIN (v1) | BBBP | Blood-Brain Barrier | 0.897 | 0.940 | - | Single task |
| Attention-GIN (v1) | ClinTox | Clinical Toxicity | 0.623 | 0.759 | - | 2 tasks, imbalanced |
| XGBoost | Various | ADMET endpoints | 0.78 | - | - | Baseline ensemble |
| **4-Branch Multimodal (v2)** | TOX21 | Toxicity (12 endpoints) | **0.918** | **0.92+** | - | **Target SOTA** |
| 4-Branch Multimodal (v2) | BBBP | Blood-Brain Barrier | **0.924** | **0.93+** | - | **Target SOTA** |
| 4-Branch Multimodal (v2) | ClinTox | Clinical Toxicity | **0.931** | **0.94+** | - | **Target SOTA** |
| Uni-Mol (SOTA) | TOX21 | Toxicity | 0.918 | 0.92+ | - | Reference SOTA |
| Uni-Mol (SOTA) | BBBP | Blood-Brain Barrier | 0.924 | 0.93+ | - | Reference SOTA |
| Uni-Mol (SOTA) | ClinTox | Clinical Toxicity | 0.931 | 0.94+ | - | Reference SOTA |

---

## Architecture Comparison

| Aspect | v1 (Attention-GIN) | v2 (4-Branch Multimodal) | Improvement |
|--------|---------------------|--------------------------|-------------|
| **Input Representation** | Graph only | Graph + SMILES + 3D + Descriptors | 4x modalities |
| **GNN Type** | GINEConv (5 layers) | Graph Transformer (6 layers) | Attention-based |
| **Feature Dim** | 300 → 512 | 256 → 768 (fused) | Multi-representation |
| **Pretraining** | None (from scratch) | GraphMAE on ZINC-15 | Self-supervised |
| **Fusion Method** | None | Cross-attention + MoE | Learned fusion |
| **Attention** | GlobalAttention pool | Multi-head cross-attention | Multi-way |
| **Loss Function** | BCE / Focal | Asymmetric Loss | Better imbalance |
| **Tasks** | 12 (TOX21) | 41 (multi-dataset) | 3.4x more tasks |

---

## Model Parameters

| Parameter | v1 Attention-GIN | v2 Graph Branch | v2 SMILES Branch | v2 Conformer | v2 Descriptor |
|-----------|------------------|-----------------|------------------|--------------|---------------|
| Parameters | ~1.2M | ~0.7M | ~77M (frozen) | ~0.2M | ~50K |
| Layers | 5 GINEConv + 2 MLP | 6 Transformer | 12 Transformer | 3 CFConv | 2 MLP |
| Hidden Dim | 300 | 256 | 768 | 128 | 128 |
| Dropout | 0.3 | 0.1 | Fixed | 0.1 | 0.1 |

---

## Training Configuration Comparison

| Configuration | v1 | v2 |
|---------------|-----|-----|
| **Optimizer** | AdamW | AdamW |
| **Learning Rate** | 1e-4 / 5e-4 (attention) | Optimizable via Optuna |
| **Epochs** | 150 | Configurable (Optuna) |
| **Batch Size** | 32 | 32 |
| **Scheduler** | CosineAnnealingLR | CosineAnnealingLR |
| **Early Stopping** | Patience 50 | Patience 15 |
| **Split Method** | Scaffold split | Scaffold split |
| **Hyperparam Search** | Manual | Optuna (300 trials) |

---

## Faithfulness Metrics

| Metric | v1 (Constrained) | v1 (Unconstrained) | Improvement |
|--------|------------------|---------------------|-------------|
| Faithfulness Score (F) | 1.000 | 0.054 | +17.9x |
| Rejection Rate | 13.5% | 36.5% | -23pp |
| Causal Consistency Score | 0.865 | - | Verified |
| Grounding Score | 1.000 | - | Perfect |

**Note**: The constrained XAI engine achieves 100% faithfulness by rejecting unfaithful explanations, demonstrating the effectiveness of counterfactual validation.

---

## Computational Requirements

| Requirement | v1 | v2 |
|-------------|-----|-----|
| **GPU Memory** | 4GB minimum | 8GB minimum |
| **Training Time** | ~2 hours (TOX21) | Variable (Optuna) |
| **Inference Latency** | ~50ms | ~100-200ms |
| **Model Size** | ~50MB | ~150MB |

---

## Key Files Reference

| Component | v1 Path | v2 Path |
|-----------|---------|---------|
| Main Model | `backend/models/attention_ginet.py` | `v2-foundation-arch/architecture_design/multimodal_encoder.py` |
| Training | `backend/models/train_attention_gin.py` | `v2-foundation-arch/experiments/training/train_v2.py` |
| Faithfulness | `backend/models/faithfulness_validator.py` | Integrated in v2 |
| Explainer | `backend/models/constrained_explainer.py` | Integrated in v2 |
| Pretraining | None | `v2-foundation-arch/experiments/pretraining/graphmae_pretrain.py` |
| Loss | Asymmetric in training file | `v2-foundation-arch/experiments/losses/asymmetric_loss.py` |
| Optuna Search | None | `v2-foundation-arch/experiments/optuna_search/optuna_search.py` |
| Ablation | None | `v2-foundation-arch/experiments/ablations/ablation_study.py` |