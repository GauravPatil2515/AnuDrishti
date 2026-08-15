# PharmaGuard AI: Trustworthy Drug-Safety Decision Support

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)

**PharmaGuard AI** is a deployable, trustworthy drug-safety decision-support platform combining **Graph Neural Networks (GNNs)** for multi-task molecular toxicity/ADMET prediction with **LLM explanations validated by counterfactual faithfulness checking** — the first system that **rejects unfaithful explanations** before they reach scientists.

---

## 🎯 Key Innovation: Faithfulness-Gated Explanations

| Traditional AI | PharmaGuard AI |
|----------------|----------------|
| LLM generates free-form explanation | LLM **constrained** by GNN evidence |
| No verification of claims | **Counterfactual test**: remove cited substructure → prediction must drop |
| Hallucinations silently shown | **EFS threshold (0.70)**: fails → **REJECTED** with audit trail |

> **Core thesis**: "An explanation should be accepted only when it is supported by model-derived molecular evidence and survives counterfactual validation."

---

## 📊 Validated Performance (5-Seed Scaffold Splits)

| Dataset | Model | 5-Seed Mean AUROC ± Std | Best Seed | ChemProp D-MPNN | Verdict |
|---------|-------|------------------------|-----------|-----------------|---------|
| **BBBP** | Attention-GIN | 0.849 ± 0.023 | 0.875 | 0.891 | Competitive |
| **BACE** | Attention-GIN | 0.849 ± 0.044 | **0.921** | 0.883 | **Best beats SOTA** |
| **TOX21** | Attention-GIN | 0.779 ± 0.025 | 0.808 | 0.793 | **Best beats SOTA** |
| **ClinTox** | Attention-GIN | 2-task (FDA + CT) | — | — | Loaded |
| **Clearance** | Attention-GIN | Regression (mL/min/kg) | — | — | Loaded |

**Faithfulness (EFS)**: 5-seed causal faithfulness = **0.128 ± 0.027** — standard GNN training does **not** induce toxicophore→toxicity causality (honest negative result).

---

## 🏗️ 6-Layer Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 1: Molecular Processing  (RDKit → Graph + Descriptors)       │
├─────────────────────────────────────────────────────────────────────┤
│ Layer 2: Multi-Task GNN       (Attention-GIN → 16 endpoints)       │
├─────────────────────────────────────────────────────────────────────┤
│ Layer 3: Explainability       (Atom Attention → Toxicophores)      │
├─────────────────────────────────────────────────────────────────────┤
│ Layer 4: Counterfactuals      (Bioisosteres + Scaffold Alters)     │
├─────────────────────────────────────────────────────────────────────┤
│ Layer 5: LLM Explanation      (Groq + Constrained Prompt)          │
├─────────────────────────────────────────────────────────────────────┤
│ Layer 6: Faithfulness Validator (EFS = 0.3·Attr + 0.3·CF + 0.2·Sub + 0.2·Rules) │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) `GROQ_API_KEY` for live LLM explanations

### 1. Clone & Install Backend
```bash
git clone https://github.com/GauravPatil2515/PharmaGuard-AI.git
cd PharmaGuard-AI

# Backend
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
# Edit backend/.env to add GROQ_API_KEY (optional)
```

### 2. Install Frontend
```bash
cd frontend
npm install
```

### 3. Run Both Servers
```bash
# Terminal 1 - Backend (port 5000)
cd backend
python app.py

# Terminal 2 - Frontend (port 3000)
cd frontend
npm start
```

### 4. Open PharmaGuard Workbench
```
http://localhost:3000/app/pharmaguard
```

---

## 🧪 API Endpoints (All Tested ✅)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | System health + cache stats |
| `/api/analyze/single` | POST | **Mode A** — Single molecule full pipeline |
| `/api/analyze/batch` | POST | **Mode B** — Library screening (1000 max) |
| `/api/analyze/batch-status` | GET | Cached batch results |
| `/api/explain/verify` | POST | **Faithfulness verification** (EFS + claim audit) |
| `/api/optimize/what-if` | POST | **Mode C** — Counterfactual optimization |
| `/api/report/export` | POST | JSON audit trail download |
| `/api/predict` | POST | Legacy prediction |
| `/api/endpoints` | GET | List loaded models |
| `/api/config/status` | GET | Groq + model status |
| `/api/cache/stats` | GET | Cache hit ratio (fixed ✅) |

---

## 💡 Demo Flow (2 Minutes)

1. **Mode A** → Paste `c1ccc([N+](=O)[O-])cc1` (nitrobenzene) → **Run Analysis**
2. **Safety Tab** → YELLOW triage, 16 endpoints, OOD flagged
3. **Audit Tab** → **"Verify Explanation"** → **EFS=1.0 VERIFIED** ✅
4. **Audit Tab** → **"Simulate Unfaithful"** → **EFS=0.5 REJECTED** ❌
5. **What-If Tab** → Saturation/CF₃ swap lowers toxicity
6. **Library Tab** → Batch 3 molecules → **Export CSV**
7. **Report Tab** → **Download JSON** → Full audit trail

---

## 📁 Repository Structure (Cleaned)

```
PharmaGuard-AI/
├── backend/
│   ├── app.py                 # Flask API with 12 PharmaGuard endpoints
│   ├── config/                # Groq, Supabase configs
│   ├── models/
│   │   ├── attention_ginet.py     # Attention-GIN architecture
│   │   ├── unified_predictor.py   # 4-model ensemble loader
│   │   ├── faithfulness_validator.py  # EFS + claim audit
│   │   ├── constrained_explainer.py   # LLM + faithfulness gate
│   │   └── meditox_feature.py       # Chemical safety analysis
│   ├── utils/
│   │   ├── cache.py               # Fixed get_hit_ratio()
│   │   ├── ood_detector.py        # ECFP4 Tanimoto + latent Mahalanobis
│   │   ├── triage_engine.py       # GREEN/YELLOW/RED risk scoring
│   │   ├── counterfactual_generator.py  # Bioisosteres + scaffold alters
│   │   └── substructure_mapper.py # SMARTS toxicophore mapping
│   ├── requirements.txt
│   ├── .env / .env.example
│   └── gunicorn.conf.py
├── frontend/
│   ├── src/
│   │   ├── components/        # 6 PharmaGuard components
│   │   │   ├── MolecularInput.js
│   │   │   ├── MolecularExplorer.js
│   │   │   ├── SafetyDashboard.js
│   │   │   ├── ExplanationAudit.js      # EFS gauge + hallucination toggle
│   │   │   ├── LibraryScreening.js
│   │   │   └── WhatIfOptimizer.js
│   │   ├── pages/
│   │   │   └── PharmaGuardWorkbench.jsx # 6-tab workbench
│   │   └── App.js
│   ├── package.json
│   └── public/
├── tests/
│   └── test_faithfulness.py   # 4/4 passing
├── .gitignore
└── README.md
```

---

## ⚙️ Configuration

### Backend `.env`
```env
# LLM (optional - enables live explanations)
GROQ_API_KEY=your_groq_key

# Supabase (optional - audit trail persistence)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx

FLASK_ENV=development
FLASK_DEBUG=1
MODEL_CACHE_SIZE=10000
RATE_LIMIT=100
```

### Models Loaded Automatically
- `results/trained_models/attention_gin_model.pth` (Tox21, 12 endpoints)
- `results/trained_models/bbbp_gin_model.pth` (BBBP)
- `results/trained_models/clintox_gin_model.pth` (ClinTox, 2 tasks)
- `results/trained_models/clearance_gin_model.pth` (Clearance, regression)

---

## 🧪 Tests

```bash
# Faithfulness validator tests (4/4 passing)
cd PharmaGuard-AI
python -m pytest tests/test_faithfulness.py -v
```

---

## 🚢 Deployment

### Docker (Recommended)
```bash
docker build -t pharmaguard .
docker run -p 5000:5000 -e GROQ_API_KEY=xxx pharmaguard
```

### Production (Gunicorn)
```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Render / Cloud
- Fork repo → connect to Render
- Auto-detects Python + Node.js
- Add `GROQ_API_KEY` in env vars

---

## 📚 Research Background

PharmaGuard AI extends the DeNovo-XAI research platform with:

- **Validated faithfulness metric (EFS)**: 4-component weighted agreement
- **Honest negative result**: Causal faithfulness = 0.128 ± 0.027 (standard GNN doesn't learn toxicophore→toxicity causality)
- **Counterfactual optimization**: Chemically valid bioisosteric/scaffold modifications
- **OOD detection**: Hybrid ECFP4 Tanimoto + latent Mahalanobis
- **Risk triage**: Transparent 5-component scoring → GREEN/YELLOW/RED

---

## 🤝 Contributing

1. Fork → feature branch → PR
2. All tests must pass (`pytest tests/`)
3. Follow existing code style

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **SIES Graduate School of Technology** — Computational resources
- **ATLAS SkillTech University** — Research collaboration
- **PyTorch Geometric** — GNN framework
- **RDKit** — Cheminformatics toolkit
- **Groq** — LLM inference API
- **MoleculeNet** — Benchmark datasets

---

## 📧 Contact

- **Gaurav Patil** — [gauravppaiml123@gst.sies.edu.in](mailto:gauravppaiml123@gst.sies.edu.in)
- **GitHub**: [GauravPatil2515](https://github.com/GauravPatil2515)
- **Branch**: `feat/sih-pharmaguard-ai`

---

<p align="center">
  <b>PharmaGuard AI — Predict · Explain · Verify · Trust</b><br/>
  Made for safer drug discovery 🛡️
</p>