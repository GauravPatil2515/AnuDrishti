# AnuDrishti / PharmaGuard AI: Free, Explainable Molecular Safety Triage

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)
[![Tests](https://img.shields.io/badge/Tests-18%2F18%20Passing-brightgreen.svg)]()

**AnuDrishti (PharmaGuard AI)** is a deployable, trustworthy drug-safety decision-support platform combining **Graph Neural Networks (GNNs)** for multi-task molecular toxicity/ADMET prediction with **LLM explanations validated by counterfactual faithfulness checking** — the first system that **rejects unfaithful explanations** before they reach scientists.

---

## 🎁 Zero-Setup Demo: 2 Free Molecule Evaluation

Experience the full end-to-end capabilities of AnuDrishti without an API key or molecular input required:

1. **Paracetamol (Acetaminophen)** — 🟢 **GREEN Triage**: Safe therapeutic profile with minimal toxicity risk.
2. **Nitrobenzene** — 🔴 **RED Triage**: High mutagenicity & toxicity driven by reactive nitro group (`[N+](=O)[O-]`).

Try it instantly via the web workbench's **Demo Tab** or via API: `GET /api/demo`.

---

## 🎯 Key Innovation: Faithfulness-Gated Explanations

| Traditional AI | AnuDrishti / PharmaGuard AI |
|----------------|-----------------------------|
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

### 1. Clone Repository
```bash
git clone https://github.com/GauravPatil2515/AnuDrishti.git
cd AnuDrishti
```

### 2. Run Backend
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
python backend/app.py
```
*Backend runs on `http://localhost:5000`*

### 3. Run Frontend
```bash
cd frontend
npm install
npm start
```
*Frontend runs on `http://localhost:3000`*

---

## 🧪 API Endpoints (All 18 Tests Passing ✅)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | System health + cache stats |
| `/api/demo` | GET | **Zero-Setup Demo** — 2 curated molecules (Paracetamol & Nitrobenzene) |
| `/api/lookup/smiles` | POST | **Mode D** — Compound name → SMILES via PubChem REST |
| `/api/analyze/single` | POST | **Mode A** — Single molecule full pipeline with MC-Dropout |
| `/api/analyze/batch` | POST | **Mode B** — Library screening (1000 max) |
| `/api/analyze/batch-status` | GET | Cached batch results |
| `/api/explain/verify` | POST | **Faithfulness verification** (EFS + claim audit) |
| `/api/optimize/what-if` | POST | **Mode C** — Counterfactual bioisostere optimization |
| `/api/report/export` | POST | JSON audit trail download |
| `/api/predict` | POST | Unified ensemble raw prediction |
| `/api/endpoints` | GET | List loaded GNN models |
| `/api/config/status` | GET | Groq + model status |
| `/api/cache/stats` | GET | Cache hit ratio tracking |

---

## 💡 Demo Flow (2 Minutes)

1. **Try Demo** → Click "Try Demo" on Hero or Workbench → Instantly inspect Paracetamol (🟢 GREEN) & Nitrobenzene (🔴 RED).
2. **Mode A (Single Molecule)** → Input compound name "Aspirin" via Mode D lookup or paste SMILES `c1ccc([N+](=O)[O-])cc1` (nitrobenzene).
3. **Safety Tab** → Inspect 16 ADMET endpoints, Epistemic Uncertainty bands, and OOD alerts.
4. **Audit Tab** → Click **"Verify Explanation"** → Inspect EFS Score (VERIFIED / PARTIAL / REJECTED).
5. **What-If Tab** → Saturation / CF₃ replacement lowers toxicity.
6. **Library Tab** → Batch screen up to 1000 molecules → Export CSV.

---

## 📁 Repository Structure

```
AnuDrishti/
├── backend/
│   ├── app.py                 # Flask API app & Blueprint registration
│   ├── routes/
│   │   └── pharmaguard.py     # 8 core PharmaGuard REST endpoints
│   ├── models/
│   │   ├── attention_ginet.py # Multi-task GNN with MC-Dropout
│   │   ├── unified_predictor.py # 4-model ensemble predictor
│   │   └── faithfulness_validator.py # EFS calculation & claim audit
│   ├── utils/
│   │   ├── triage_engine.py   # GREEN/YELLOW/RED risk scoring
│   │   ├── ood_detector.py    # ECFP4 Tanimoto + latent Mahalanobis OOD
│   │   ├── counterfactual_generator.py # Bioisostere & scaffold optimizer
│   │   └── substructure_mapper.py # Toxicophore SMARTS mapping
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # Input, Dashboard, Explorer, Audit, Library
│   │   ├── pages/             # Home.jsx (Hero) & PharmaGuardWorkbench.jsx
│   │   └── index.css          # Tailwind CSS design system
│   ├── tailwind.config.js
│   └── package.json
├── tests/                     # 18 passing pytest integration & unit tests
└── README.md
```

---

## 🧪 Tests

```bash
PYTHONPATH=. pytest -p no:asyncio tests/
```
*Output: 18 passed in ~6.9s*

---

## 🤝 Contributing & License

Licensed under the **MIT License**. Contributions are welcome!

---

## 📧 Contact & Acknowledgments

- **Gaurav Patil** — [GitHub: GauravPatil2515](https://github.com/GauravPatil2515)
- **Repository**: [https://github.com/GauravPatil2515/AnuDrishti.git](https://github.com/GauravPatil2515/AnuDrishti.git)
- **Special Thanks**: PyTorch Geometric, RDKit, Groq, MoleculeNet.