# Models

## Attention-GIN (Tox21)
**File**: `backend/models/attention_ginet.py`
**ROC-AUC**: 0.8368 (12 Tox21 endpoints)

### Architecture
- Input: atom type (1-118) + chirality (0-3) indices
- 5x GINEConv layers with BatchNorm
- GlobalAttention pooling (learnable gate network)
- Feature projection (300→512) + prediction head (512→256→256→12)
- Softplus activations, dropout ratio 0.3

### Key Methods
- `forward(data, return_attention=True)`: Returns (features, predictions, attention_info)
- `get_attention_weights()`: Per-atom softmax-normalized attention scores from gate_nn
- `get_atom_attributions(data, target_class=0)`: GNNExplainer-based gradient attribution
  - Uses edge_mask (node_mask disabled because embeddings can't receive gradient masks)
  - Aggregates edge importance → node importance
  - Falls back to attention weights on any failure
- `predict_mc_dropout(data, n_samples=30)`: MC Dropout for epistemic uncertainty
  - Sets model.train() + disables BatchNorm updates
  - Returns (mean, std, ci_low, ci_upper)

## UnifiedADMETPredictor
**File**: `backend/models/unified_predictor.py`

### Model Inventory
1. **attention_gin** — Tox21 12 endpoints (NR-AR, NR-AR-LBD, NR-AhR, NR-Aromatase, NR-ER, NR-ER-LBD, NR-PPAR-gamma, SR-ARE, SR-ATAD5, SR-HSE, SR-MMP, SR-p53)
2. **bbbp** — Blood-Brain Barrier Penetration (1 task)
3. **clintox** — Clinical Toxicity (2 tasks: FDA_APPROVED, CT_TOX)
4. **clearance** — Intrinsic Clearance (1 task, regression)
5. **xgboost** — 5 NR endpoints (fallback, not currently loaded)
6. **tdc** — hERG, DILI, AMES (placeholder, TDC package available but no trained models)

### Featurization
- `_smiles_to_graph_simple()`: atom_type_index + chirality_index (for Attention-GIN models)
- `_smiles_to_graph()`: 9-dim atom features (for training scripts)
- Uses RDKit for SMILES parsing

### Prediction Flow
1. Convert SMILES → graph (PyG Data)
2. Run Attention-GIN with MC Dropout (50 samples)
3. Compute per-endpoint probability, confidence, CI
4. Aggregate to overall toxicity mean + std + CI