# Architecture

## System Diagram

```
[SMILES Input] → Flask API → UnifiedADMETPredictor
                                          ├── Attention-GIN (Tox21, 12 endpoints)
                                          ├── BBBP GIN
                                          ├── ClinTox GIN
                                          ├── Clearance GIN
                                          └── TDC placeholders (hERG, DILI, AMES)
                                          ↓
[Attention/GNNExplainer] → Per-atom attribution → Faithfulness Validator (EFS gate)
                                          ↓
[OOD Detector] → ECFP4 fingerprint comparison → Triage Engine
                                          ↓
[LLM Explanation (Groq)] → Faithfulness-verified explanation
                                          ↓
[Counterfactual Generator] → QED/SA filtered alternatives
                                          ↓
React Frontend ← JSON API responses
```

## Backend
- **Framework**: Flask with Flask-CORS
- **Entry point**: `backend/app.py`
- **Blueprints**: `backend/routes/pharmaguard.py` (PharmaGuard AI endpoints)
- **Port**: 5000

## Models
### Attention-GIN (`backend/models/attention_ginet.py`)
- 5-layer GINEConv with BatchNorm
- GlobalAttention pooling (gate_nn: Linear→ReLU→BN→Linear)
- Returns: (features, predictions, attention_info)
- Key methods:
  - `get_attention_weights()`: softmax-normalized per-atom weights
  - `get_atom_attributions()`: GNNExplainer-based attribution with edge-mask→node aggregation fallback
  - `predict_mc_dropout()`: 50 stochastic forward passes for epistemic uncertainty

### UnifiedADMETPredictor (`backend/models/unified_predictor.py`)
- Loads 4 model types: attention_gin, bbbp, clintox, clearance
- `_smiles_to_graph_simple()`: PyG Data conversion (atom type + chirality indices)
- `_smiles_to_graph()`: PyG Data conversion (9-dim atom features for training)
- `predict()`: Multi-model ensemble prediction with uncertainty

## Key Services
- **OODDetector**: `backend/utils/ood_detector.py` — ECFP4 fingerprint comparison
- **TriageEngine**: `backend/utils/triage_engine.py` — RED/YELLOW/GREEN triage with disclaimer
- **FaithfulnessValidator**: `backend/models/faithfulness_validator.py` — EFS score gate
- **PredictionCache**: `backend/utils/cache.py` — LRU cache with TTL
- **CounterfactualGenerator**: `backend/utils/counterfactual_generator.py` — QED/SA filtered

## Frontend
- **Framework**: React + Vite
- **3D**: Three.js for molecular rendering
- **State**: React state management
- **API**: `/api/` endpoints via REST