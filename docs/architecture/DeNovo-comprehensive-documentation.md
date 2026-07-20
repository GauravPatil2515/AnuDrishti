# DeNovo Project: Comprehensive Architecture and Methods Documentation

> **V1 HISTORY — SUPERSEDED.** Numbers here (e.g. Tox21 0.802/0.837) are v1
> Attention-GIN results, not the verified v2 GINE findings. Authoritative,
> verified results: `benchmark_results/VALIDATION_LOG.md`, `ABLATION_TABLE.md`,
> `paper-2/main.tex` (GINE 5-seed AUROC; true causal faithfulness ≈0.13; causal
> regularizer does not reliably help). Do not cite figures from this file.

## Project Overview
DeNovo is an AI-powered drug discovery platform that combines Graph Neural Networks (GNNs) for molecular property prediction with Large Language Models (LLMs) for faithful, explainable insights. The platform focuses on molecular toxicity prediction with explainable AI capabilities.

## Core Architecture Components

### 1. Attention-GIN (Graph Isomorphism Network) Model
The primary architecture for molecular property prediction featuring:

**Architecture Flow:**
```
SMILES Input → RDKit Parsing → Molecular Graph (V, E) 
              → 5x GINEConv Layers (300-dim embeddings) 
              → Global Attention Pooling (per-atom importance α) 
              → 2-Layer MLP Predictor (Softplus)
              → Output: Prediction + Attention Weights for Explainability
```

**Key Features:**
- 5-layer GINEConv with 300-dimensional embeddings
- Global attention pooling for interpretable atom importance
- 2-layer MLP predictor with Softplus activation
- Outputs both predictions and attention weights

### 2. Faithful XAI (Explainable AI) Engine
Connects model attention to LLM-generated explanations with validation:

**Workflow:**
```
Attention Weights (α) → Substructure Mapper → Constrained LLM Prompt
                                                        ↓
                                         Faithfulness Validator ← LLM Explanation
                                                        ↓
                                                ACCEPT or REJECT
```

**Performance:** 13.5% rejection rate (reduces hallucination rate from 36.5% in unconstrained baseline to 13.5%)

### 3. System Architecture
```
Frontend (React.js) ↔ Backend API (Flask/Python) ↔ Model Services (PyTorch Models)
                              ↓
                     Utility Services (RDKit, Groq, etc.)
```

## Model Zoo

### Currently Implemented Models:
1. **Tox21**: Attention-GIN (0.802 Test / 0.837 Val ROC-AUC) - Trained
2. **BBBP**: Attention-GIN (0.897 Test / 0.940 Val ROC-AUC) - Trained  
3. **ClinTox**: Attention-GIN (0.623 Test / 0.743 Val ROC-AUC) - Trained
4. **Clearance**: Attention-GIN (Trained, Regression)
5. **Caco2**: Pending data
6. **HLM_CLint**: Pending data

### Enhanced Features (v2.0):
- **RDKit Integration**: Expanded from 50 to 200+ molecular descriptors (+5-10% accuracy improvement)
- **SMILES Validation & Canonicalization**: 95% reduction in invalid predictions
- **Expanded Toxicity Endpoints**: Increased from 5 to 12 endpoints (2.4x more comprehensive)
  - Nuclear Receptors (7 endpoints): NR-AR, NR-AR-LBD, NR-AhR, NR-ER, NR-ER-LBD, NR-PPAR-gamma, NR-Aromatase
  - Stress Response (5 endpoints): SR-MMP, SR-ARE, SR-ATAD5, SR-HSE, SR-p53
- **API Rate Limiting**: Token bucket algorithm with multi-tier limits

## Key Technologies

### Deep Learning
- **Framework**: PyTorch, PyTorch Geometric (GNN layers)
- **Architecture**: Attention-GINet with Global Attention Pooling

### API Framework
- **Backend**: Flask with RESTful endpoints
- **Endpoints**: 
  - `GET /api/health` - Health check
  - `POST /api/predict` - Single molecule prediction
  - `POST /api/batch-predict` - Batch processing
  - `POST /api/chat` - AI chat with Groq integration

### Explainability Components
- **RDKit**: Substructure mapping and molecular descriptors
- **Groq API**: LLM for explanation generation
- **Faithfulness Validator**: Counterfactual testing for explanation validation

### Data Processing
- **Libraries**: Pandas, NumPy, scikit-learn
- **Features**: 200+ RDKit descriptors, Morgan fingerprints, ChemBERT embeddings

### Visualization
- **Libraries**: Matplotlib, Seaborn (for attention weight visualization)

### Deployment
- **Options**: Docker, Gunicorn, cloud platforms (Render, AWS)
- **Configuration**: Environment variables (.env file), training config (YAML)

## Data Flow

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

## Model Training Pipeline

### Data Sources
- **Primary**: Tox21 dataset (~12,000 compounds, 12 toxicity assays)
- **Secondary**: ToxCast, ChEMBL, PubChem BioAssay
- **Recommended Mix**: 50% Tox21, 30% ToxCast, 20% filtered ChEMBL (~71,000 compounds)

### Feature Engineering
1. **RDKit Descriptors** (200+ features): Molecular weight, LogP, TPSA, H-bond donors/acceptors, rotatable bonds, ring counts, Lipinski descriptors, etc.
2. **Morgan Fingerprints** (2048-bit): Circular fingerprints for molecular similarity
3. **ChemBERT Embeddings** (768-dim): Transformer-based molecular representations
4. **GNN Features**: Learned representations from Attention-GINet

### Model Selection & Optimization
- **Baseline**: Random Forest
- **Production**: XGBoost (handles class imbalance, high accuracy)
- **Research**: Graph Neural Network (state-of-art for molecular data)
- **Optimization**: Optuna/Ray Tune for hyperparameter search with 5-fold CV

### Training Implementation
```python
# Example XGBoost training with class imbalance handling
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
params = {
    'objective': 'binary:logistic',
    'eval_metric': 'auc',
    'max_depth': 6,
    'learning_rate': 0.1,
    'n_estimators': 500,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'scale_pos_weight': scale_pos_weight,
    'random_state': 42,
    'tree_method': 'hist',
    'device': 'cuda'  # GPU acceleration
}
```

## Performance Characteristics

- **Latency**: ~50-200ms per prediction (after model loading)
- **Memory**: ~10MB per model, ~50MB total for loaded models
- **Scalability**: Horizontal scaling via multiple API instances
- **Batch Processing**: Optimized for throughput with minimal overhead

## Security & Privacy
- API key authentication for LLM services
- Input sanitization (SMILES validation)
- No storage of proprietary compounds without consent
- GDPR-compliant data handling practices

## Recent Improvements (v2.0)
1. Enhanced RDKit integration (200+ descriptors)
2. SMILES validation and canonicalization pipeline
3. Expanded to 12 toxicity endpoints
4. API rate limiting with token bucket algorithm
5. Improved prediction accuracy (+5-10% improvement)
6. Better error handling and user experience

## File Structure
```
DeNovo-main/
├── backend/                    # Flask API server
│   ├── app.py                  # Main application entry point
│   ├── models/                 # ML model implementations
│   │   ├── attention_ginet.py  # Attention-GIN architecture
│   │   ├── unified_predictor.py# Combined ADMET predictor
│   │   ├── gin_predictor.py    # GNN-based predictions
│   │   ├── simple_predictor.py # XGBoost predictions
│   │   ├── faithfulness_validator.py # XAI validation
│   │   └── constrained_explainer.py  # LLM explanation
│   └── utils/                  # Utility functions
├── frontend/                   # React.js web interface
├── data_packages/              # Training data packages
├── results/                    # Trained models & results
├── training/                   # Training scripts
├── experiments/                # Research experiments
├── overleaf/                   # Research paper (LaTeX)
├── docs/                       # Documentation
└── scripts/                    # Utility scripts
```

## Key Files Explained

### backend/models/attention_ginet.py
- Implements the Attention-GINet architecture with global attention pooling
- Provides attention weights for explainability
- Includes methods for pretrained weight loading and attention extraction

### backend/models/faithfulness_validator.py
- Validates LLM-generated explanations through counterfactual testing
- Implements the acceptance/rejection mechanism for explanations

### backend/models/constrained_explainer.py
- Generates constrained LLM prompts using attention-weighted substructures
- Integrates with Groq API for explanation generation

### backend/models/unified_predictor.py
- Combines multiple models (Attention-GIN, XGBoost) for multi-task prediction
- Handles model loading and prediction aggregation

### backend/app.py
- Main Flask application with REST API endpoints
- Handles request routing, model inference, and response formatting

## Usage Examples

### Single Molecule Prediction
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"}'
```

### Batch Prediction
```bash
curl -X POST http://localhost:5000/api/batch-predict \
  -H "Content-Type: application/json" \
  -d '{"smiles_list": ["CCO", "CC(=O)OC1=CC=CC=C1C(=O)O"]}'
```

### AI Chat Explanation
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Why is nitrobenzene considered toxic?", "smiles": "c1ccc([N+](=O)[O-])cc1"}'
```

## Training Commands

### Train All Models
```bash
python training/train_all_models.py
```

### Run Faithfulness Evaluation
```bash
python experiments/run_faithful_eval.py \
    --model results/trained_models/attention_gin_model.pth \
    --output results/my_eval
```

### Single Molecule Demo with Explanation
```bash
python experiments/faithful_xai_demo.py \
    --smiles "c1ccc([N+](=O)[O-])cc1" \
    --use-groq
```

## Deployment Options

### Docker Deployment
```bash
docker build -t denovo .
docker run -p 5000:5000 -e GROQ_API_KEY=your_key denovo
```

### Local Production Deployment
```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Cloud Deployment (Render)
1. Fork repository
2. Connect to Render
3. Create new Web Service pointing to repo
4. Render auto-detects render.yaml and deploys

## Research Contributions

The DeNovo platform introduces several novel contributions:
1. **Attention-GIN Architecture**: Novel GNN with global attention pooling for interpretable molecular predictions
2. **Faithful XAI Engine**: Framework connecting model-agnostic method for validating LLM explanations through counterfactual testing
3. **Constrained Explainer**: Method for grounding LLM explanations in model attention weights and molecular substructures
4. **Multi-task ADMET Prediction**: Unified framework for predicting 12 toxicity endpoints with shared molecular representations
5. **Quantifiable Faithfulness Metrics**: Mathematical formulation for explanation faithfulness score

## References and Acknowledgments

- **PyTorch Geometric**: GNN framework
- **RDKit**: Cheminformatics toolkit
- **Groq**: LLM inference API
- **SIES Graduate School of Technology**: Computational resources
- **ATLAS SkillTech University**: Research collaboration

---
*Document generated: 2026-07-09*
*Based on DeNovo: AI-Powered Drug Discovery Platform*