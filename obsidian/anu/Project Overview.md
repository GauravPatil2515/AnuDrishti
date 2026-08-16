# Project Overview

## AnuDrishti / PharmaGuard AI

**Full name**: Faithful LLM-Augmented Explainability for Graph Neural Network-Based Molecular Toxicity Prediction

**Purpose**: Research-grade drug-safety platform for molecular toxicity prediction with faithfulness-gated explainability.

## Target
- SIH 2026 (Student Innovation Hackathon)
- Indian defense applications (iDEX, DRDO/CEMILAC)
- Molecular toxicity prediction with explanation faithfulness gating

## Key Innovations
1. **Attention-GIN (Tox21)**: GNN with GlobalAttention pooling, 12 Tox21 endpoints, ROC-AUC 0.8368
2. **GNNExplainer integration**: True gradient-based atom attribution (not just attention weights)
3. **Live MC Dropout**: Epistemic uncertainty quantification during inference (50 stochastic passes)
4. **Faithfulness Validator**: EFS (Explainability Faithfulness Score) gate — claims must be grounded in model attributions
5. **OOD Detector**: ECFP4 fingerprint-based distribution shift detection (86-molecule reference set)
6. **What-If Optimizer**: Counterfactual molecule generation filtered by QED > 0.4 and SA Score < 6.0

## Architecture
- **Backend**: Flask API (`backend/app.py`) with blueprint routing (`backend/routes/pharmaguard.py`)
- **Models**: `backend/models/` — AttentionGINet, UnifiedADMETPredictor, ConstrainedExplainer
- **Frontend**: React + Vite + Three.js (`frontend/`), served via Flask static files
- **Tests**: 28 tests across `tests/` — integration, batch, faithfulness, OOD, triage