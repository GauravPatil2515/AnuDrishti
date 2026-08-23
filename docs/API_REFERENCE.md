# AnuDrishti (PharmaGuard AI) — REST API Reference Manual

> **Base URL:** `http://localhost:5000/api`  
> **Protocol:** HTTP/1.1 or HTTP/2  
> **Content-Type:** `application/json`

---

## Table of Contents
1. [System & Health Endpoints](#1-system--health-endpoints)
2. [Molecular Prediction & ADMET Endpoints](#2-molecular-prediction--admet-endpoints)
3. [Cardiotoxicity & Cross-Species Translation](#3-cardiotoxicity--cross-species-translation)
4. [CNS Safety & Kinome Selectivity](#4-cns-safety--kinome-selectivity)
5. [Neuro-Symbolic Co-Pilot & Optimization](#5-neuro-symbolic-co-pilot--optimization)
6. [Statistical Calibration & Conformal Prediction](#6-statistical-calibration--conformal-prediction)
7. [21 CFR Part 11 Audit Trail & Compliance](#7-21-cfr-part-11-audit-trail--compliance)

---

## 1. System & Health Endpoints

### `GET /health`
Returns system status, active models, device configuration, and cache hit ratios.

#### Response `200 OK`
```json
{
  "status": "healthy",
  "version": "v3.0.0",
  "device": "cpu",
  "models_loaded": ["attention_gin", "herg_rf", "conformal_predictor", "audit_trail"],
  "timestamp": "2026-08-24T00:00:00Z"
}
```

---

## 2. Molecular Prediction & ADMET Endpoints

### `POST /predict`
Executes multi-task graph neural network inference on input molecular structure.

#### Request Body
```json
{
  "smiles": "CC(=O)Oc1ccccc1C(=O)O"
}
```

#### Response `200 OK`
```json
{
  "smiles": "CC(=O)Oc1ccccc1C(=O)O",
  "predictions": {
    "tox21": {
      "NR-AR": 0.042,
      "NR-AhR": 0.081,
      "SR-MMP": 0.055
    },
    "bbbp": 0.21,
    "clintox": 0.01
  },
  "applicability_domain": {
    "in_domain": true,
    "max_tanimoto": 0.784,
    "threshold": 0.30
  }
}
```

---

## 3. Cardiotoxicity & Cross-Species Translation

### `POST /cipa`
Evaluates 3-channel cardiac ion channel liability ($I_{Kr}$, $I_{Na}$, $I_{CaL}$) using the trained Random Forest hERG model and structural alert engines.

#### Request Body
```json
{
  "smiles": "Cc1cc2c(cc1C(=O)N2)C3=CC=C(C=C3)N4CCN(CC)CC4"
}
```

#### Response `200 OK`
```json
{
  "smiles": "Cc1cc2c(cc1C(=O)N2)C3=CC=C(C=C3)N4CCN(CC)CC4",
  "overall_risk": "HIGH",
  "channels": {
    "herg_ikr": {
      "probability": 0.92,
      "risk": "HIGH",
      "model": "RandomForest (class_weight=balanced, n=300)",
      "conformal_ci": [0.81, 0.98]
    },
    "nav15_ina": {
      "probability": 0.15,
      "risk": "LOW"
    },
    "cav12_ical": {
      "probability": 0.10,
      "risk": "LOW"
    }
  },
  "disclaimer": "Structure-based alert screen; PATCH-CLAMP ASSAY REQUIRED per ICH S7B."
}
```

### `POST /translate`
Translates PK parameters and acute oral toxicity across 5 mammalian species (Human, Dog, Monkey, Rat, Mouse).

#### Request Body
```json
{
  "smiles": "CC(=O)Nc1ccc(O)cc1",
  "human_dose_mg": 500.0,
  "human_clearance": 5.0
}
```

---

## 4. CNS Safety & Kinome Selectivity

### `POST /cns-safety`
Computes the Wager 2010 CNS MPO score and Noisy-OR P-gp efflux substrate probability.

#### Request Body
```json
{
  "smiles": "CN1CCC(CC1)C2=CC=C(C=C2)C(=O)C3=CC=CC=C3"
}
```

#### Response `200 OK`
```json
{
  "smiles": "CN1CCC(CC1)C2=CC=C(C=C2)C(=O)C3=CC=CC=C3",
  "cns_mpo_score": 4.82,
  "cns_penetrant_likely": true,
  "pgp_substrate_probability": 0.35,
  "pgp_pooling_method": "noisy-or"
}
```

---

## 5. Neuro-Symbolic Co-Pilot & Optimization

### `POST /copilot/optimize`
Performs autonomous 3-iteration bioisosteric optimization to eliminate toxicophores while preserving QED and EFS faithfulness constraints.

#### Request Body
```json
{
  "smiles": "c1ccc([N+](=O)[O-])cc1",
  "max_iterations": 3,
  "min_efs": 0.70
}
```

#### Response `200 OK`
```json
{
  "original_smiles": "c1ccc([N+](=O)[O-])cc1",
  "final_smiles": "NC(=O)c1ccccc1",
  "iterations": [
    {
      "iteration": 1,
      "candidate_smiles": "NC(=O)c1ccccc1",
      "toxicophore_replaced": "Nitro aromatic",
      "toxicity_score": 0.08,
      "qed": 0.65,
      "efs": 0.88,
      "decision": "ACCEPT"
    }
  ],
  "status": "OPTIMIZATION_SUCCESSFUL"
}
```

---

## 6. Statistical Calibration & Conformal Prediction

### `POST /conformal/mondrian`
Returns scaffold-stratified Mondrian conformal prediction intervals with guaranteed finite-sample coverage at confidence level $1-\alpha = 0.95$.

---

## 7. 21 CFR Part 11 Audit Trail & Compliance

### `GET /v1/audit/trail`
Retrieves immutable audit trail records with pagination and filtering.

#### Query Parameters
- `limit` (optional, default 50, max 500)
- `offset` (optional, default 0)
- `user_id` (optional)
- `action` (optional)
- `smiles` (optional)

### `GET /v1/audit/verify`
Executes complete cryptographic hash-chain and HMAC verification across all audit records.

#### Response `200 OK`
```json
{
  "success": true,
  "valid": true,
  "total_records": 128,
  "verified_records": 128,
  "latest_record_hash": "a4f89d31b8...",
  "status": "ALL_RECORDS_VERIFIED_AND_INTACT",
  "compliance": "21 CFR Part 11 & ALCOA+ Tamper-Evident Certified"
}
```

### `POST /v1/audit/log`
Appends a contemporaneous event to the immutable audit trail.
