# AnuDrishti / PharmaGuard AI — Knowledge Vault

> Faithful LLM-Augmented Explainability for GNN-Based Molecular Toxicity Prediction

## Quick Links
- [[Project Overview]]
- [[Architecture]]
- [[Models]]
- [[API Endpoints]]
- [[Testing]]
- [[SIH 2026 Audit]]
- [[Obsidian Setup]]

## Status: ACTIVE — 2026-08-16

### What was fixed today
- Restored `backend/models/unified_predictor.py` from `.before_tdc` backup (fixed SyntaxError from broken try/except and duplicated TDC blocks)
- Fixed `get_atom_attributions()` in `backend/models/attention_ginet.py`:
  - Wrapper now handles 2-tuple vs 3-tuple model output correctly
  - Changed GNNExplainer `node_mask_type` from `'attributes'` to `None` (embedding indices can't receive gradient masks)
  - Edge mask importance now aggregated to node scores
  - Proper fallback to attention weights on failure
- All 28 tests pass
- Pushed to GitHub: https://github.com/GauravPatil2515/AnuDrishti.git (main)