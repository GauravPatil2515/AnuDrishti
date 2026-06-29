# DeNovo Architecture Summary

## Overview
DeNovo combines Graph Neural Networks (GNNs) for molecular property prediction with Large Language Models (LLMs) for faithful, explainable insights in drug discovery.

## Core Architecture Components

### 1. Attention-GIN (Graph Isomorphism Network) Model
The primary architecture for molecular property prediction.

```
┌─────────────────────────────────────────────────────────────┐
│                    SMILES Input                              │
├─────────────────────────────────────────────────────────────┤
│                    RDKit Parsing                             │
│                         ↓                                    │
│              Molecular Graph (Vertices, Edges)               │
├─────────────────────────────────────────────────────────────┤
│         5x GINEConv Layers (300-dim embeddings)              │
│                         ↓                                    │
│              Global Attention Pooling                        │
│              (per-atom importance weights α)                 │
│                         ↓                                    │
│         2-Layer MLP Predictor (Softplus activation)          │
├─────────────────────────────────────────────────────────────┤
│  Output: Prediction + Attention Weights for Explainability  │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- 5-layer GINEConv with 300-dimensional embeddings
- Global attention pooling for interpretable atom importance
- 2-layer MLP predictor with Softplus activation
- Outputs both predictions and attention weights

### 2. Faithful XAI (Explainable AI) Engine
Connects model attention to LLM-generated explanations with validation.

```
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Attention    │ → │  Substructure │ → │  Constrained  │
│  Weights (α)  │   │    Mapper     │   │  LLM Prompt   │
└───────────────┘   └───────────────┘   └───────────────┘
                                               ↓
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   ACCEPT or   │ ← │  Faithfulness │ ← │     LLM       │
│    REJECT     │   │   Validator   │   │  Explanation  │
└───────────────┘   └───────────────┘   └───────────────┘
```

**Workflow:**
1. Extract attention weights from GNN
2. Map weights to molecular substructures via SMARTS patterns
3. Generate constrained LLM prompt using highlighted substructures
4. Validate explanation faithfulness through counterfactual testing
5. Accept or reject explanation based on fidelity threshold

**Performance:** 13.5% rejection rate (reduces hallucination rate from 36.5% in unconstrained baseline to 13.5% under DeNovo)

### 3. System Architecture
```
┌─────────────────┐    ┌──────────────────────┐    ┌────────────────────┐
│   Frontend      │    │   Backend API        │    │   Model Services   │
│   (React.js)    │◄──►│   (Flask/Python)     │◄──►│   (PyTorch Models) │
└─────────────────┘    └──────────────────────┘    └────────────────────┘
          │                         │                         │
          │                         ▼                         │
          │              ┌─────────────────────┐              │
          │              │   Utility Services  │              │
          │              │   (RDKit, Groq, etc)│              │
          │              └─────────────────────┘              │
          ▼                         │                         ▼
┌─────────────────┐    ┌──────────────────────┐    ┌────────────────────┐
│   User Interface│    │   REST Endpoints     │    │   Model Zoo        │
│   & Visualization│    │   • /predict        │    │   • Tox21 Model    │
│                 │    │   • /batch-predict   │    │   • BBB Model      │
│                 │    │   • /chat            │    │   • etc.           │
└─────────────────┘    └──────────────────────┘    └────────────────────┘
```

### 4. Key Technologies
- **Deep Learning**: PyTorch, PyTorch Geometric (GNN layers)
- **API Framework**: Flask with RESTful endpoints
- **Explainability**: RDKit for substructure matching, Groq API for LLMs
- **Data Processing**: Pandas, NumPy, scikit-learn
- **Visualization**: Matplotlib, Seaborn (for attention weights)
- **Deployment**: Docker, Gunicorn, cloud platforms (Render, AWS, etc.)

### 5. Data Flow
1. **Input**: SMILES string via API or UI
2. **Preprocessing**: RDKit converts to molecular graph
3. **Feature Extraction**: GNN learns node/edge embeddings
4. **Attention Mechanism**: Computes atom importance weights
5. **Prediction**: MLP outputs ADMET properties
6. **Explanation Generation**:
   - Attention weights mapped to substructures
   - LLM generates natural language explanation
   - Faithfulness validator checks explanation consistency
7. **Output**: Predictions + explanation + confidence score

### 6. Model Zoo
Currently implemented models:
- **Tox21**: Attention-GIN (0.802 Test / 0.837 Val ROC-AUC) - Trained
- **BBBP**: Attention-GIN (0.897 Test / 0.940 Val ROC-AUC) - Trained
- **ClinTox**: Attention-GIN (0.623 Test / 0.743 Val ROC-AUC) - Trained
- **Clearance**: Attention-GIN (Trained, Regression)
- **Caco2**: Pending data
- **HLM_CLint**: Pending data

### 7. Extensibility Points
- **New Models**: Add to `backend/models/` and update `unified_predictor.py`
- **New Endpoints**: Add Flask routes in `app.py`
- **Explainability Methods**: Extend `faithfulness_validator.py`
- **Data Sources**: Add to `data_packages/` directory
- **Visualization**: Enhance frontend components in `frontend/src/`

### 8. Performance Characteristics
- **Latency**: ~50-200ms per prediction (after model loading)
- **Memory**: ~10MB per model, ~50MB total for loaded models
- **Scalability**: Horizontal scaling via multiple API instances
- **Batch Processing**: Optimized for throughput with minimal overhead

### 9. Security & Privacy
- API key authentication for LLM services
- Input sanitization (SMILES validation)
- No storage of proprietary compounds without consent
- GDPR-compliant data handling practices

### 10. Future Enhancements
- Graph attention visualization in frontend
- Uncertainty estimation with Bayesian GNNs
- Federated learning for multi-institutional data
- Integration with additional LLM providers
- Real-time explanation streaming

---

*This architecture enables trustworthy AI-assisted drug discovery by combining accurate predictions with verifiable explanations.*