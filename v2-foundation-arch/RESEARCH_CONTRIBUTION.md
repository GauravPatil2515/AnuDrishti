# v2 Paper Framing

## Proposed Title
"Multimodal Molecular Foundation Model with Faithful Causal Explanation: Bridging Predictive Performance and Trustworthy AI for Toxicity Prediction"

## Key Contributions
1. **First multimodal fusion** (graph + SMILES + 3D + descriptors) for toxicity prediction with cross-attention
2. **Self-supervised pretraining** (GraphMAE + SMILES contrastive + conformer contrastive) on ZINC-15
3. **Faithfulness verification engine** - formal causal guarantees on LLM explanations (v1 contribution, unique to this work)

## Performance Targets
| Model | TOX21 | BBBP | ClinTox |
|-------|-------|------|---------|
| ChemProp (baseline) | 0.845 | 0.903 | 0.912 |
| Uni-Mol (SOTA) | 0.918 | 0.924 | 0.931 |
| **Our Target** | 0.91+ | 0.92+ | 0.92+ |

## Experimental Validation Plan
- Multi-task AUROC across Tox21, BBBP, ClinTox, SIDER, BACE
- 300 Optuna trials for hyperparameter optimization
- Systematic ablation study (7 configurations)
- Faithfulness verification metrics (constrained vs unconstrained)

## Next Steps (Week 6-7)
- [ ] Complete actual branch implementations (load pretrained weights)
- [ ] Start GraphMAE pretraining on ZINC-15 subset
- [ ] Integrate into training pipeline