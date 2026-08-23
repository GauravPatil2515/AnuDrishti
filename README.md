# AnuDrishti (PharmaGuard AI) 🧬🔬

### **A Regulatory-Grade Neuro-Symbolic Platform for Molecular Toxicology, Cardiotoxicity Screening, and Drug Safety Triage**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch 2.0+](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![RDKit](https://img.shields.io/badge/RDKit-2023.09%2B-green.svg)](https://www.rdkit.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![21 CFR Part 11](https://img.shields.io/badge/Compliance-21%20CFR%20Part%2011%20Audit%20Trail-blueviolet.svg)](docs/ARCHITECTURE.md)
[![Tests: Passing](https://img.shields.io/badge/Tests-214%20Passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/Conformal%20Coverage-95.25%25-success.svg)](results/calibration/coverage_stats.json)

---

## 📌 Keywords & Taxonomy
`AI Drug Discovery` • `Molecular Toxicity Prediction` • `Computational Toxicology` • `Graph Neural Networks (GNN)` • `Attention-GIN` • `Neuro-Symbolic AI` • `21 CFR Part 11 Compliant AI` • `Mondrian Conformal Prediction` • `hERG Cardiotoxicity` • `Wager CNS MPO` • `Bioisosteric Optimization` • `Explanation Faithfulness (EFS)` • `Tox21 & ChEMBL Benchmarks` • `FDA Modernization Act 2.0 / NAMs` • `Cross-Species Allometric Scaling` • `Chemoinformatics` • `RDKit`

---

## 🌟 Overview

**AnuDrishti** (PharmaGuard AI) is a trustworthy, open-source, regulatory-grade decision-support platform designed to bridge the gap between academic deep learning and stringent pharmaceutical safety standards.

Traditional molecular machine learning models often act as opaque black boxes, suffer from silent out-of-distribution (OOD) failure modes, and lack statistical uncertainty bounds or regulatory audit trails. AnuDrishti solves this by integrating **multi-task Graph Neural Networks (Attention-GIN)**, **scientifically validated mechanistic screens** (Wager CNS MPO, Noisy-OR P-gp, Random Forest hERG), **Mondrian conformal prediction**, **causal faithfulness validation (EFS)**, and an **immutable 21 CFR Part 11 append-only audit trail**.

---

## 🏛️ The 4 Pillars of Enterprise PharmaGuard

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ PILLAR 1: Multi-Channel Cardiotox Screening & Safety Assays                                 │
│ • Random Forest hERG (IKr) Classifier (CV ROC-AUC: 0.8627 on 655 ChEMBL molecules)          │
│ • Nav1.5 (INa) & Cav1.2 (ICaL) SMARTS structural alert channels                             │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ PILLAR 2: Cross-Species Toxicokinetics & FDA Modernization Act NAMs                         │
│ • Kleiber's Law Allometric Scaling across 5 species (Human, Dog, Monkey, Rat, Mouse)        │
│ • FDA Human Equivalent Dose (HED) & Margin of Safety (MOS) calculation                      │
│ • ProTox-3.0 ML API Integration for acute oral LD50 and GHS toxicity categorization         │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ PILLAR 3: CNS Safety Multiparameter Optimization & Kinome Selectivity                       │
│ • Wager 2010 CNS MPO Score (0–6 score from 6 piecewise linear desirability functions)       │
│ • Noisy-OR independent causal factor pooling for P-glycoprotein (P-gp) efflux liability     │
│ • Kinome Selectivity Index (SI) and off-target cross-reactivity profiling                   │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ PILLAR 4: Neuro-Symbolic Bioisosteric Co-Pilot & Conformal Uncertainty                      │
│ • 3-Iteration closed-loop bioisosteric optimization (Nitro, Amine, Aniline replacements)    │
│ • Explanation Faithfulness Score (EFS >= 0.70 threshold) with Human-in-the-Loop escalation   │
│ • Mondrian Conformal Prediction (95% finite-sample coverage across molecular scaffolds)     │
│ • Sheridan 2004 Applicability Domain (AD) Tanimoto gate (T >= 0.30)                         │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔬 Scientific Validation & Benchmarks

All models and heuristics in AnuDrishti are grounded in peer-reviewed literature and evaluated on held-out benchmarks:

| Target / Endpoint | Model Architecture | Dataset / Source | Metric | Status | Reference Citation |
|---|---|---|---|---|---|
| **hERG Cardiotoxicity** | Random Forest (ECFP4, 2048-bit) | TDC / ChEMBL-240 ($N=655$) | **CV ROC-AUC: 0.8627** | ✅ Production | Arab & Barakat, *Sci. Data* 2021 |
| **GNN Generalization** | Attention-GIN (5 Layers) | Scaffold Split (80/10/10) | **Test ROC-AUC: 0.7326** | ✅ Production | Hu et al., *ICLR* 2020 |
| **CNS Permeability** | CNS MPO (6 Desirability Functions) | Marketed CNS Drugs | **Score: 0.0 – 6.0** | ✅ Validated | Wager et al., *ACS Chem. Neurosci.* 2010 |
| **P-gp Efflux** | Noisy-OR Probabilistic Causal Model | In Vitro Efflux Corpus | **Calibrated Probability** | ✅ Validated | Jaeger et al., *JCIM* 2017 |
| **Uncertainty Calibration** | Split-Conformal Mondrian | Held-Out Calibration ($N=400$) | **Coverage: 95.25%** | ✅ Guaranteed | Vovk et al., *Springer* 2005 |
| **Acute Toxicity (LD50)** | Similarity ML / ProTox-3.0 | 18+ Toxicity Endpoints | **GHS Categories I–VI** | ✅ Integrated | Banerjee et al., *NAR* 2024 |
| **Applicability Domain** | Sheridan Tanimoto Gate ($T \ge 0.30$) | Training Morgan Fingerprints | **Binary In/Out Domain** | ✅ Active | Sheridan et al., *JCICS* 2004 |

> 📖 **Detailed Report:** See [SCIENTIFIC_VALIDATION.md](docs/SCIENTIFIC_VALIDATION.md) for complete curves, datasets, and equations.

---

## 🛡️ 21 CFR Part 11 Tamper-Evident Audit Trail

AnuDrishti features an **append-only immutable audit trail** satisfying FDA 21 CFR Part 11 and ALCOA+ data integrity guidelines:
- **Database Immutability Triggers**: SQLite-level SQL triggers immediately abort any `UPDATE` or `DELETE` commands.
- **Cryptographic Hash Chaining**: Every log row incorporates `SHA256(prev_record_hash | timestamp | user_id | action | smiles | payload)`.
- **HMAC Signatures**: Each record is digitally signed with HMAC-SHA256.
- **Integrity Verification**: Continuous chain auditing via `GET /api/v1/audit/verify`.

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python:** `3.10+`
- **Node.js:** `18+`
- **Operating System:** Linux, macOS, or Windows WSL2

### 1. Clone Repository
```bash
git clone https://github.com/GauravPatil2515/AnuDrishti.git
cd AnuDrishti
```

### 2. Backend Installation & Startup
```bash
# Create and activate virtual environment
python3 -m venv backend/venv
source backend/venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the Flask API server
PYTHONPATH=".:backend" python backend/app.py
```
*Backend runs on `http://localhost:5000`.*

### 3. Frontend Workbench Startup
```bash
cd frontend
npm install
npm start
```
*Interactive Workbench runs on `http://localhost:3000`.*

---

## 🧪 Running the Complete Automated Test Suite

AnuDrishti includes an extensive regression test suite (214+ unit, integration, and property tests):

```bash
PYTHONPATH=".:backend" backend/venv/bin/python -m pytest tests/ -p no:asyncio -v
```

---

## 📚 API Endpoints Summary

| Endpoint | Method | Description |
|---|---|---|
| `/api/predict` | `POST` | Multi-task GNN inference across Tox21, BBBP, and ClinTox |
| `/api/cipa` | `POST` | 3-Channel cardiotoxicity screen ($I_{Kr}$, $I_{Na}$, $I_{CaL}$) |
| `/api/translate` | `POST` | Cross-species allometric scaling (Human, Dog, Monkey, Rat, Mouse) |
| `/api/cns-safety` | `POST` | Wager 2010 CNS MPO score & Noisy-OR P-gp efflux liability |
| `/api/copilot/optimize` | `POST` | 3-Iteration closed-loop bioisosteric co-pilot with EFS verification |
| `/api/conformal/mondrian` | `POST` | Scaffold-stratified Mondrian conformal prediction intervals |
| `/api/applicability-domain` | `POST` | Sheridan 2004 Tanimoto similarity domain validation |
| `/api/dossier/export` | `POST` | Tamper-evident PDF safety dossier generation |
| `/api/v1/audit/trail` | `GET` | 21 CFR Part 11 paginated immutable audit log query |
| `/api/v1/audit/verify` | `GET` | Cryptographic hash chain & HMAC integrity audit |

> 📖 **Full API Docs:** See [API_REFERENCE.md](docs/API_REFERENCE.md) for complete request/response schemas.

---

## 📑 Documentation Index

- [System Architecture Specification](docs/ARCHITECTURE.md)
- [REST API Reference Manual](docs/API_REFERENCE.md)
- [Scientific Validation & Benchmark Report](docs/SCIENTIFIC_VALIDATION.md)
- [Contribution Guidelines](docs/CONTRIBUTING.md)
- [Citation Metadata](CITATION.cff)

---

## ⚖️ Ethical Disclosures & Regulatory Notice

1. **Research Use Only**: In silico predictions generated by AnuDrishti are computational screening tools intended to prioritize wet-lab testing and reduce animal usage under the **FDA Modernization Act 2.0**.
2. **Not a Substitute for Patch-Clamp Assays**: Structure-based cardiotoxicity screening flags potential liabilities; formal cardiac safety profiles require in vitro electrophysiology per **ICH S7B**.
3. **Electronic Records**: The HMAC-SHA256 audit ledger provides data integrity and non-repudiation controls; full institutional 21 CFR Part 11 compliance requires organization-level SOPs and access controls.

---

## ✍️ Citation

If you use AnuDrishti in academic research or industrial screening campaigns, please cite:

```bibtex
@software{patil2026anudrishti,
  author = {Patil, Gaurav},
  title = {AnuDrishti (PharmaGuard AI): A Regulatory-Grade Neuro-Symbolic Platform for Molecular Toxicology & Drug Safety Triage},
  year = {2026},
  url = {https://github.com/GauravPatil2515/AnuDrishti},
  version = {3.0.0}
}
```

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.