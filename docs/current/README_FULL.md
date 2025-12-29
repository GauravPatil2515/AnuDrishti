# Faithful XAI: Causally-Constrained Explanations for Molecular Toxicity

**A research module of the DeNovo AI Platform.**

This repository implements a **Faithful Explainable AI (XAI)** system for predicting and explaining molecular toxicity. Unlike standard LLM approaches that may hallucinate, this system enforces **causal faithfulness** by constraining the LLM to only interpret features (toxicophores) that the underlying Graph Neural Network (GNN) actually used for its prediction.

## 🏆 Key Results (Tox21 Dataset)

| Metric | Performance |
|--------|-------------|
| **Prediction Accuracy (ROC-AUC)** | **0.8368** (Target: >0.82) |
| **Explanation Faithfulness (Median)** | **0.794** |
| **Rejection Rate** | **36.5%** |

*The high rejection rate demonstrates the system's rigor: it rejects 36.5% of generated explanations because they fail to meet strict causal consistency and grounding checks.*

## 📂 Repository Structure

```
DeNovo-main/
├── backend/
│   ├── models/
│   │   ├── attention_ginet.py       # The GNN model with Global Attention
│   │   ├── constrained_explainer.py # The Explain-Verify-Reject engine
│   │   ├── faithfulness_validator.py# The 3-test validation suite
│   │   └── substructure_mapper.py   # Maps attention weights to chemical groups
│   └── utils/                       # Utility scripts
│
├── results/
│   ├── trained_models/              # Final trained GNN weights
│   ├── eval_tox21_200/              # Full evaluation data (CSV + JSON)
│   ├── paper_figures/               # Generated plots for publication
│   └── EVALUATION_SUMMARY.md        # Detailed report
│
├── experiments/
│   ├── run_faithful_eval.py         # Main evaluation script
│   ├── faithful_xai_demo.py         # Single-molecule demo script
│   └── generate_paper_figures.py    # Figure generation
│
├── scripts/                         # Operational scripts (setup, training)
├── docs/                            # Documentation & Archive
└── tests/                           # Unit tests
```

## 🚀 Usage

### 1. Setup Environment

```powershell
.\scripts\setup_windows.ps1
```

### 2. Run Single-Molecule Demo

See the constrained explanation in action for a specific molecule.

```bash
python experiments/faithful_xai_demo.py --use-groq --smiles "c1ccc([N+](=O)[O-])cc1"
```

### 3. Reproduce Evaluation

Run the full benchmark on the Tox21 test set (200 molecules).

```bash
python experiments/run_faithful_eval.py --model results/trained_models/attention_gin_model.pth --output results/my_eval
```

## 🧠 Methodology

1. **Attention-GIN**: A GNN is trained to predict toxicity while learning attention weights on atoms.
2. **Evidence Extraction**: High-attention atoms are mapped to known toxicophores (e.g., Nitro groups).
3. **Constrained Generation**: An LLM (LLaMA 3.3) generates an explanation, strictly constrained to the extracted evidence.
4. **Faithfulness Validation**: The explanation is tested:
    * **Grounding**: Are cited features actually important?
    * **Causal Consistency**: Does removing the feature drop the predicted toxicity?
    * **Counterfactuals**: Does the explanation change if the molecule changes?
5. **Output**: Only explanations passing these tests are accepted.

## 📄 License

MIT License
