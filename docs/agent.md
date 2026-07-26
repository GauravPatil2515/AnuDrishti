# Agent Reference Context: DeNovo Platform

## 📌 Project Overview
**DeNovo** is a comprehensive Full-Stack Web Application + ML AI platform for early-stage drug discovery. It combines **Graph Neural Networks (GNNs)** (specifically Attention-GIN) for molecular property/toxicity prediction with **Large Language Models (LLMs)** to provide faithful, explainable insights.

**Key Mission:** Provide multi-task ADMET (Absorption, Distribution, Metabolism, Excretion, Toxicity) prediction with LLM-augmented explainable AI (XAI) that rejects unfaithful hallucinations.

## 📁 Repository Structure at a Glance
- `backend/`: Python Flask/FastAPI backend containing the core API, ML inference models (`attention_ginet.py`, `unified_predictor.py`), explainability logic (`faithfulness_validator.py`, `constrained_explainer.py`), and utility scripts.
- `frontend/`: React + Tailwind CSS web application interface.
- `model-training/`: Scripts, notebooks, and tracking markdown files for training the GNN/XGBoost models.
- `data_packages/`: Pre-packaged trained model weights and data for 6 distinct endpoints: Tox21, BBBP, ClinTox, Caco-2, Clearance, HLM-CLint.
- `database/`: Database schema files (`schema.sql`).
- `docs/`: Extensive documentation including roadmaps, redesign references, APIs, and model training progress.
- `experiments/`: Benchmark scripts for the faithful XAI evaluation and figure generation for research papers.
- `overleaf/`: LaTeX files (`main.tex`, `extra_results.tex`, `references.bib`) for the associated research paper.
- `results/`: Output reports, evaluation summaries, and generated figures from benchmarks.
- `scripts/`: Development and deployment automation scripts (batch/powershell and Python).
- `tests/`: Integration and unit tests for backend, frontend, and models.

## 🚀 Current Technical Stack
- **Backend:** Python 3.10+, Flask, PyTorch, PyTorch Geometric, RDKit
- **Frontend:** React, Node.js, Tailwind CSS
- **Machine Learning:** Attention-GIN (Graph Isomorphism Network), XGBoost
- **LLM/XAI:** Constrained explainer with hallucination filtering (36.5% rejection rate), counterfactual generation

## 📈 Status / Progress "Till Now"
- **Model Training:** Successfully trained models across 6 endpoints (Tox21 ROC-AUC 0.837, BBBP 0.825, ClinTox 0.816, Clearance RMSE 0.52).
- **Explainability Validation:** The faithful XAI pipeline is functional, implementing a verification step against counterfactual structures.
- **Frontend / Backend Integration:** A fully updated frontend redesign is marked complete (`FRONTEND_REDESIGN_COMPLETE.md`), and the backend features an enhanced app version with batch processing (`app_enhanced.py`).
- **Research/Paper Context:** The workspace contains active experimentation scripts and LaTeX sources (`overleaf/`) indicating that this is an actively researched methodology.
- **Deployment:** Deployment readiness is outlined via Dockerfiles, `render.yaml`, and `Procfile`.

## 🤖 Agent Instructions Context
- When assisting, prioritize maintaining the faithful explainability pipeline and GNN integration.
- Check both `backend/` for inference/API functionality and `model-training/` for weight/training adjustments.
- Use `scripts/` to launch tests, platforms, and database validations.
- For documentation updates or reviewing pipeline flow, consult the `docs/` and root `*.md` files.