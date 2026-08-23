# AnuDrishti (PharmaGuard AI) — System Architecture Specification

> **Enterprise AI Decision-Support Platform for Predictive Molecular Toxicology, Safety Screening, and Formulation Integrity**  
> *Compliant with 21 CFR Part 11 Data Integrity, OECD QSAR Principles, and FDA Modernization Act 2.0 NAM Guidelines*

---

## 1. System Overview & Core Philosophy

**AnuDrishti** is an open-source, regulatory-grade drug safety decision-support architecture. Modern pharmaceutical discovery requires moving beyond black-box toxicity prediction toward **mechanistic, causal, and uncertainty-calibrated safety intelligence**. 

AnuDrishti integrates:
1. **Multi-Scale Molecular Graph Neural Networks (Attention-GIN)** for empirical bioactivity and toxicological endpoint prediction.
2. **Mechanistic Structural Alert Rulesets & Desirability Functions** (Wager 2010 CNS MPO, Noisy-OR P-gp Efflux, SMARTS Toxicophore filters).
3. **Mondrian Conformal Prediction** guaranteeing finite-sample coverage across distinct molecular scaffolds.
4. **Sheridan Applicability Domain (AD) Verification** to detect out-of-domain compounds.
5. **Neuro-Symbolic Bioisosteric Co-Pilot** executing autonomous optimization loops with causal Faithfulness Verification (EFS).
6. **21 CFR Part 11 Immutable Audit Logging** with cryptographic SHA-256 hash chaining and HMAC signatures.

---

## 2. Six-Layer Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: Molecular Featurization & Structure Standardization               │
│ RDKit Morgan ECFP4 (2048-bit), PyTorch-Geometric Graph Node/Edge Encodings │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ LAYER 2: Multi-Task Graph Neural Network & ML Screening                     │
│ 5-Layer Attention-GIN (Tox21, Clintox, BBBP, Clearance) + Random Forest hERG│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ LAYER 3: Mechanistic Screening & Physicochemical Desirability               │
│ Wager 2010 CNS MPO (0-6), Noisy-OR P-gp Efflux, 3-Channel Cardiotoxicity   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ LAYER 4: Statistical Uncertainty Calibration & Applicability Domain         │
│ Split-Conformal Mondrian Predictor (95% Coverage) + Sheridan 2004 AD Gate    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ LAYER 5: Explainability & Neuro-Symbolic Bioisosteric Co-Pilot              │
│ Attention Attribution, Toxicophore Replacement, EFS Faithfulness Gate (>=0.7)│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ LAYER 6: Regulatory Integrity & Compliance Layer (21 CFR Part 11)           │
│ SQLite Append-Only Immutable Triggers, SHA-256 Hash Chaining, HMAC Signatures│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Pillar-by-Pillar Technical Specifications

### Pillar 1: Multi-Channel Cardiotox Alert Screening
- **hERG (I_Kr) Liability**: Trained Random Forest model on 655 ChEMBL/TDC compounds with 2048-bit ECFP4 fingerprints. Validated with 5-fold cross-validation ROC-AUC of **0.8627**.
- **Multi-Channel SMARTS Alerts**: Identifies structural motifs associated with Nav1.5 ($I_{Na}$) and Cav1.2 ($I_{CaL}$) liabilities.
- **Scientific Disclosures**: Clearly flagged as a hypothesis-generating structural screen (not the FDA CiPA ODE action-potential simulation paradigm).

### Pillar 2: Cross-Species Toxicokinetics & NAMs
- **Allometric Scaling**: Kleiber's Law ($Y = a \cdot W^b$, $b=0.75$ for clearance, $b=1.0$ for volume of distribution) extrapolating across Human, Dog, Cynomolgus Monkey, Rat, and Mouse.
- **HED & Safety Margins**: FDA Guidance formula:
  $$\text{HED} = \text{NOAEL}_{\text{animal}} \times \left(\frac{\text{BW}_{\text{animal}}}{\text{BW}_{\text{human}}}\right)^{0.33}$$
- **Acute Toxicity (LD50)**: ProTox-3.0 API client with graceful rule-based fallback.

### Pillar 3: Central Nervous System (CNS) Safety & Oncology Selectivity
- **Wager 2010 CNS MPO**: Published multiparameter optimization score (0–6) using 6 piecewise linear desirability functions ($C\log P$, $C\log D_{7.4}$, MW, TPSA, HBD, $\text{p}K_{a,\text{basic}}$). Marketed CNS drugs benchmark: $\ge 4.0$.
- **P-gp Efflux (Noisy-OR)**: Replaces naive max-pooling with independent causal factor pooling:
  $$P(\text{Substrate}) = 1.0 - \prod_{i} (1.0 - P_i)$$
- **Kinome Selectivity**: Selectivity Index ($SI = \frac{IC_{50,\text{off-target}}}{IC_{50,\text{target}}}$) and kinome cross-reactivity screening.

### Pillar 4: Neuro-Symbolic Co-Pilot & Conformal Uncertainty
- **Autonomous Optimization**: 3-iteration closed-loop bioisosteric substitution replacing reactive toxicophores (nitro $\to$ amide, amine $\to$ morpholine, aniline $\to$ pyridine) with re-scoring against QED and toxicity constraints.
- **Explanation Faithfulness Score (EFS)**:
  $$\text{EFS} = 0.30 \cdot \text{Attribution} + 0.30 \cdot \text{Counterfactual} + 0.20 \cdot \text{Substructure} + 0.20 \cdot \text{Rules}$$
  Threshold: $\ge 0.70$ required; fails escalate to `HUMAN_REVIEW`.
- **Mondrian Conformal Prediction**: Finite-sample validity conditioned on Murcko scaffolds to prevent under-coverage on out-of-distribution molecules.
- **Sheridan 2004 Applicability Domain**: ECFP4 Tanimoto similarity threshold ($T \ge 0.30$) against the training corpus.

---

## 4. 21 CFR Part 11 Immutable Audit Architecture

```
[Record N-1]  ──>  record_hash_N-1
                        │
                        ▼
[Record N]    ──>  SHA256( record_hash_N-1 | timestamp | user_id | action | smiles | payload )
                        │
                        ▼
                   HMAC-SHA256( secret_key, record_hash_N )  ──>  Immutable Storage (WAL)
```

1. **Database-Level Protection**: SQLite triggers abort any attempt to execute `UPDATE` or `DELETE` on the `audit_records` table.
2. **Cryptographic Chaining**: Every record incorporates the SHA-256 hash of its predecessor, creating a forward-secure tamper-evident ledger.
3. **Automated Verification**: Endpoint `/api/v1/audit/verify` audits the full blockchain ledger from genesis to head in $O(N)$ time.

---

## 5. Technology Stack

- **Backend**: Python 3.10+, PyTorch 2.0+, PyTorch Geometric, RDKit, scikit-learn, Flask.
- **Frontend**: React 18, TailwindCSS/Vanilla CSS, Lucide Icons, Vite.
- **Data & Compliance**: SQLite (WAL mode, Part 11 triggers), HMAC-SHA256, fpdf2.
- **Integrations**: ProTox-3.0 API, PubChem REST, Therapeutics Data Commons (TDC), ChEMBL.
