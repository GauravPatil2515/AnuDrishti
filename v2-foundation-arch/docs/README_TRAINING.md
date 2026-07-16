# Training Documentation

## Training Pipeline

### Pretraining (Week 4-5)
- **GraphMAE**: Mask 15-25% atom features, reconstruct
- **Dataset**: ZINC-15 250K molecules
- **Duration**: ~2.5 days on A100 (50GB VRAM)

### Fine-tuning (Week 6-7)
- **Datasets**: MoleculeNet splits (Tox21, BBBP, ClinTox, SIDER, BACE)
- **Loss**: Asymmetric Loss (gamma_neg=4, clip=0.05)
- **Optimizer**: AdamW with cosine annealing

### Hyperparameter Search (Week 8)
- **Trials**: 300
- **Parameters**: lr, weight_decay, dropout, num_heads, num_layers, warmup_ratio
- **Target**: Max AUROC on validation set

### Ensemble (Week 9-10)
- Weight top 7 checkpoints by validation AUROC
- Average with softmax-weighted MoE
- Apply faithfulness verification layer

## Execution Order
1. `experiments/pretraining/graphmae_pretrain.py` - Pretrain on ZINC-15
2. `experiments/optuna_search/optuna_integration.py` - Find best hyperparameters
3. `experiments/training/train_v2.py` - Train final model
4. `experiments/ablations/run_real_ablation.py` - Run ablation study