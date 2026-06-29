# DeNovo: AI-Powered Drug Discovery Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)

**DeNovo** is a comprehensive AI platform for early-stage drug discovery that combines **Graph Neural Networks (GNNs)** for molecular property prediction with **Large Language Models (LLMs)** for faithful, explainable insights.

![DeNovo Platform](overleaf/figures/platform.png)

## 🎯 Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Task ADMET Prediction** | 6 endpoints: Tox21, BBBP, ClinTox, Caco-2, Clearance, HLM-CLint |
| **Faithful Explainability** | LLM explanations validated through counterfactual testing |
| **Attention-GIN Architecture** | Custom GNN with per-atom importance scores |
| **13.5% Rejection Rate** | Automatic filtering of unfaithful LLM explanations (restricts explanation hallucinations down from 36.5% in the unconstrained baseline to 13.5%) |
| **Production-Ready API** | Flask backend with batch processing support |

## 📊 Model Performance

| Model | Task | Metric | Performance |
|-------|------|--------|-------------|
| **Tox21** (Attention-GIN) | Toxicity (12 endpoints) | ROC-AUC | **0.802** (Test) / **0.837** (Val) |
| **BBBP** | Blood-Brain Barrier | ROC-AUC | **0.897** (Test) / **0.940** (Val) |
| **ClinTox** | Clinical Toxicity | ROC-AUC | **0.623** (Test) / **0.743** (Val) |
| **Clearance** | Metabolic Clearance | RMSE | **0.52** (Trained) |
| **XGBoost Ensemble** | NR Endpoints | ROC-AUC | **0.78** |

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/GauravPatil2515/DeNovo.git
cd DeNovo-main

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Backend Server
```bash
cd backend
python app.py
```
The API will be available at `http://localhost:5000`

### 3. Test a Prediction
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"}'
```

## 📁 Repository Structure
```
DeNovo-main/
├── backend/                    # Flask API server
│   ├── app.py                  # Main application entry point
│   ├── models/                 # ML model implementations
│   │   ├── attention_ginet.py  # Attention-GIN architecture
│   │   ├── unified_predictor.py# Combined ADMET predictor
│   │   ├── gin_predictor.py    # GNN-based predictions
│   │   ├── simple_predictor.py # XGBoost predictions
│   │   ├── faithfulness_validator.py  # XAI validation
│   │   └── constrained_explainer.py   # LLM explanation
│   └── utils/                  # Utility functions
│       ├── substructure_mapper.py     # SMARTS toxicophore mapping
│       ├── counterfactual_generator.py# Molecular perturbations
│       └── admet_rules.py      # Rule-based overrides
├── frontend/                   # React.js web interface
│   └── src/
│       ├── pages/              # Page components
│       └── components/         # UI components
├── data_packages/              # Training data packages
│   ├── tox21_model_full_package/
│   ├── bbbp_model_full_package/
│   ├── caco2_model_full_package/
│   ├── clearance_model_full_package/
│   ├── hlm_clint_model_full_package/
│   └── clintox_model_package/
├── results/                    # Trained models & results
│   ├── trained_models/         # Model weights (.pth files)
│   │   ├── attention_gin_model.pth    # Tox21
│   │   ├── bbbp_gin_model.pth         # BBBP
│   │   ├── clintox_gin_model.pth      # ClinTox
│   │   └── clearance_gin_model.pth    # Clearance
│   └── eval_tox21_200/         # Evaluation results
├── training/                   # Training scripts
│   ├── training_config.yaml    # Hyperparameter config
│   └── train_all_models.py     # Master training script
├── experiments/                # Research experiments
│   ├── run_faithful_eval.py    # Faithfulness evaluation
│   └── generate_paper_figures.py
├── overleaf/                   # Research paper (LaTeX)
│   ├── main.tex
│   └── figures/
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
├── requirements.txt            # Python dependencies
└── render.yaml                 # Cloud deployment config
```

## 🧠 Model Architecture

### Attention-GIN (Primary Model)
```
┌─────────────────────────────────────────────────────────────┐
│                    SMILES Input                              │
├─────────────────────────────────────────────────────────────┤
│                    RDKit Parsing                             │
│                         ↓                                    │
│              Molecular Graph (V, E)                          │
├─────────────────────────────────────────────────────────────┤
│         5x GINEConv Layers (300-dim embeddings)              │
│                         ↓                                    │
│              Global Attention Pooling                        │
│              (per-atom importance α)                         │
│                         ↓                                    │
│         2-Layer MLP Predictor (Softplus)                     │
├─────────────────────────────────────────────────────────────┤
│  Output: Prediction + Attention Weights for Explainability  │
└─────────────────────────────────────────────────────────────┘
```

### Faithful XAI Engine
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
Rejection Rate: 13.5% (reduces hallucination rate from 36.5% in unconstrained baseline to 13.5%)

## 🔌 API Reference

### Health Check
```bash
GET /api/health
```

### Single Molecule Prediction
```bash
POST /api/predict
Content-Type: application/json

{
    "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"
}
```
**Response:**
```json
{
    "success": true,
    "predictions": {
        "NR-AR": {
            "probability": 0.15,
            "prediction": "Non-toxic",
            "confidence": "High",
            "source": "Attention-GIN (Tox21)"
        },
        "BBBP": {
            "probability": 0.82,
            "prediction": "Permeable",
            "confidence": "High",
            "source": "Attention-GIN (BBBP)"
        },
        "FDA_APPROVED": {
            "probability": 0.08,
            "prediction": "Approved",
            "confidence": "Very High",
            "source": "Attention-GIN (ClinTox)"
        },
        "CT_TOX": {
            "probability": 0.05,
            "prediction": "Safe in Trials",
            "confidence": "Very High",
            "source": "Attention-GIN (ClinTox)"
        },
        "Clearance": {
            "value": 12.4,
            "unit": "mL/min/kg",
            "interpretation": "Moderate",
            "source": "Attention-GIN (Clearance)"
        }
    },
    "explanation": "The molecule has a high probability of BBB permeability and is predicted to be safe in clinical trials. It does not show typical reactive group alerts for receptor-binding toxicity...",
    "faithfulness_score": 0.865
}
```

### Batch Prediction
```bash
POST /api/batch-predict
Content-Type: application/json

{
    "smiles_list": ["CCO", "CC(=O)OC1=CC=CC=C1C(=O)O"]
}
```

### AI Chat (with Groq)
```bash
POST /api/chat
Content-Type: application/json

{
    "message": "Why is nitrobenzene considered toxic?",
    "smiles": "c1ccc([N+](=O)[O-])cc1"
}
```

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the `backend/` directory:
```env
# LLM API Key (required for explanations)
GROQ_API_KEY=your_groq_api_key_here

# Optional configurations
FLASK_ENV=development
FLASK_DEBUG=1
MODEL_CACHE_SIZE=1000
RATE_LIMIT=100
```

### Training Configuration
Edit `training/training_config.yaml`:
```yaml
architecture:
  model_type: AttentionGINet
  num_layer: 5
  emb_dim: 300
  feat_dim: 512
  drop_ratio: 0.3

classification:
  epochs: 100
  batch_size: 32
  learning_rate: 0.0001
  pos_weight: 3.0
```

## 🚢 Deployment

### Deploy to Render
1. Fork this repository
2. Connect to [Render](https://render.com)
3. Create a new Web Service pointing to this repo
4. Render will auto-detect `render.yaml` and deploy

### Deploy with Docker
```bash
docker build -t denovo .
docker run -p 5000:5000 -e GROQ_API_KEY=your_key denovo
```

### Deploy Locally (Production)
```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🧪 Running Tests

### Validate All Models
```bash
python scripts/validate_all_models.py
```

### Run Faithfulness Evaluation
```bash
python experiments/run_faithful_eval.py \
    --model results/trained_models/attention_gin_model.pth \
    --output results/my_eval
```

### Single Molecule Demo
```bash
python experiments/faithful_xai_demo.py \
    --smiles "c1ccc([N+](=O)[O-])cc1" \
    --use-groq
```

## 📚 Research Paper
The research paper describing DeNovo is available in the `overleaf/` directory:
- **Title**: *DeNovo: A Faithful, Multi-Task AI Platform for Safer Drug Discovery with LLM-Augmented Explainability*
- **Authors**: Gaurav Patil, Parth Parmar
- **Key Contribution**: Causal faithfulness validation for LLM explanations in molecular toxicity prediction

To compile the paper:
```bash
cd overleaf
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-model`
3. Commit changes: `git commit -am 'Add new ADMET endpoint'`
4. Push to branch: `git push origin feature/new-model`
5. Submit a Pull Request

### Adding a New Model
1. Add training data to `data_packages/new_model_package/`
2. Update `training/training_config.yaml`
3. Train: `python training/train_all_models.py --model new_model`
4. Update `backend/models/unified_predictor.py` to load the new model

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments
- **SIES Graduate School of Technology** - Computational resources
- **ATLAS SkillTech University** - Research collaboration
- **PyTorch Geometric** - GNN framework
- **RDKit** - Cheminformatics toolkit
- **Groq** - LLM inference API

## 📧 Contact
- **Gaurav Patil** - [gauravppaiml123@gst.sies.edu.in](mailto:gauravppaiml123@gst.sies.edu.in)
- **GitHub**: [GauravPatil2515](https://github.com/GauravPatil2515)

<p align="center">
  Made with ❤️ for safer drug discovery
</p>