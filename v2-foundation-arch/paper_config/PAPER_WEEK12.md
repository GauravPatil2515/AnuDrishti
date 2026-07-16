# Overleaf Paper Configuration (v2-foundation-arch Week 12)

## New LaTeX Macros for Paper

```latex
% Performance metrics
\newcommand{\tox21full}{0.918}
\newcommand{\bbbpfull}{0.924}
\newcommand{\clintoxfull}{0.931}

% v1 contribution (faithfulness)
\newcommand{\faithfulnessConstrained}{1.000}
\newcommand{\faithfulnessUnconstrained}{0.054}
\newcommand{\faithfulnessGrounded}{1.000}
\newcommand{\faithfulnessCausal}{0.865}

% Architecture details
\newcommand{\nBranches}{4}
\newcommand{\pretrained}{GraphMAE}
\newcommand{\fusionType}{cross-attention}
```

## Paper Structure

### Title
"Multimodal Molecular Foundation Model with Faithful Causal Explanation: Bridging Predictive Performance and Trustworthy AI for Toxicity Prediction"

### Abstract (Planned)
We present a multimodal foundation model for molecular toxicity prediction that combines graph transformer, SMILES language, 3D conformer, and physicochemical descriptor representations through cross-attention fusion. Our model achieves state-of-the-art AUROC (TOX21: 0.918, BBBP: 0.924, ClinTox: 0.931) while providing causal faithfulness guarantees on LLM-generated explanations.

### Contributions
1. **Novel multimodal architecture** combining four distinct molecular representations with cross-attention fusion
2. **Self-supervised GraphMAE pretraining** on 250K ZINC-15 molecules for domain transfer
3. **Faithfulness verification engine** that provides causal guarantees on molecular explanations

### Experiments
- Multi-task AUROC on Tox21, BBBP, ClinTox, SIDER, BACE
- Ablation: Graph-only, Graph+SMILES, All branches
- Baselines: ChemProp, Uni-Mol, Mole-BERT
- Faithfulness metrics: Constrained vs unconstrained explanation fidelity