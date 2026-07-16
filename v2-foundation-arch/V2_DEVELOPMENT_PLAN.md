# v2 Foundation Architecture - Development Plan

## Phase Overview (12 Weeks)

### Week 1: Audit & Literature Review
- [x] v1-archive created with complete paper artifacts
- [x] Literature spreadsheet created (ChemProp, Uni-Mol, Mole-BERT, GraphMAE baselines)
- [ ] Run ChemProp baseline reproduction (Weeks 2-3)

### Week 2-3: Baseline Implementation
- ChemProp D-MPNN baseline
- Uni-Mol 3D representation baseline
- Mole-BERT self-supervised baseline

### Week 4-5: Architecture Design
4-branch multimodal encoder:
1. Graph Transformer (GPS/SAN) - replace GIN message passing
2. SMILES Language Branch (ChemBERTa-2) - tokenization + transformer
3. 3D Conformer Branch (SchNet/DimeNet++) - distance/angle features
4. RDKit Descriptor Branch (200 features) - physicochemical properties

Cross-attention fusion → Mixture-of-Experts → Multi-task heads

### Week 6-7: Pretraining
- GraphMAE masking on ZINC-15
- SMILES augmentation contrastive
- Conformer contrastive

### Week 8: Hyperparameter Search
- 300 Optuna trials minimum
- AUROC maximization objective
- Target: match/exceed Uni-Mol performance

### Week 9-10: Verification Integration
- Plug v1 faithfulness engine as post-prediction layer
- Causal counterfactual verification
- LLM explanation conditioning

### Week 11: Systematic Ablations
- Branch ablation (4 configurations)
- Pretraining ablation (3 variants)
- Loss function ablation
- Multi-task ablation

### Week 12: Paper Writing & Submission
- Reframe: "Multimodal Molecular Foundation Model with Faithful Causal Explanation"
- Contribution emphasis on verification engine
- SOTA performance + causal guarantees

## Key Insight from Analysis
Your **faithfulness verification engine** (v1) is the unique contribution.
The GIN backbone is replaceable, but the ACCEPT/REJECT mechanism with
counterfactual validation is novel in 2025-26 molecular property prediction.

## Immediate Next Steps
1. Run `v2-foundation-arch/baselines/train_chemprop_baseline.py` to establish floor
2. Clone Uni-Mol repo for baseline reproduction
3. Design 4-branch encoder architecture in `architecture_design/`