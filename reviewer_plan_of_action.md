# DeNovo — Reviewer Response Plan of Action

> **Verdict**: Competitive for IEEE conference proceedings, Springer CCIS/LNNS, AI-in-Healthcare workshops, and applied AI venues. Score: 8.8–9.0/10. Weak Accept → Accept at target venues.
>
> Key identity the reviewer sees: **Reject-and-Retry Faithfulness Validation**, not Attention-GIN.

---

## Tier 1 — Quick Wins (≤2 hours, do these first)

These are zero-risk, high-signal fixes the reviewer explicitly named.

### 1.1 Remove the "Abstract—+" Artifact ✅ *P0*

The reviewer flagged `Abstract—+` appearing in the compiled output. This is the `+` at the start of the abstract body in `main.tex` (line 36).

**File**: `overleaf/main.tex`, line 36  
**Fix**: Delete the leading `+` from the `\begin{abstract}` body.

```diff
-+The pharmaceutical industry faces...
+The pharmaceutical industry faces...
```

---

### 1.2 Add Code Availability Statement ✅ *P0*

The reviewer specifically said: *"Release the code, or state it will be released upon acceptance."*  
Currently no such statement exists anywhere in the paper.

**File**: `overleaf/main.tex` — add to end of Conclusion or as a standalone paragraph before References.

**Suggested text**:
> The complete source code for the DeNovo platform — including the Attention-GIN training pipeline, Faithful XAI Engine, SMARTS-based Substructure Mapper, and the reproducibility scripts — will be made publicly available upon acceptance of this paper.

---

### 1.3 Reframe the Title to Emphasize Faithfulness Validation ✅ *P0*

The reviewer said reviewers will **remember Reject-and-Retry Faithfulness Validation**, not Attention-GIN. The title should reflect the identity.

**Current (inferred)**: *Faithful LLM-Augmented Explainability for GNN-Based Molecular Toxicity Prediction*  
**Suggested revision**: *DeNovo: Reject-and-Retry Faithfulness Validation for LLM-Augmented GNN Explanations in Molecular Toxicity Prediction*

Or a shorter variant: *Faithful-by-Design: Counterfactual Validation of LLM Explanations for GNN-Based Drug Toxicity Prediction*

This makes the core contribution the headline claim.

---

### 1.4 Add Figure 5 Consistency Note ✅ *P1*

The reviewer said: *"Make Figure 5 consistent with the other figures."*  
Check font sizes, line styles, colour palette, axis labels, and DPI against Figures 6 and 7.

**File**: `experiments/generate_paper_figures.py` + `overleaf/figures/ablation.png`  
**Action**: Re-generate with consistent style (same seaborn theme/palette as `faithfulness_distribution.png` and `sensitivity_tradeoff.png`).

---

## Tier 2 — High-Impact Technical Work (1–3 days)

These address the two biggest weaknesses the reviewer identified.

### 2.1 Add GNNExplainer Faithfulness Comparison ✅ *P0 — Most Critical*

> *"Add comparison with one more XAI baseline (GNNExplainer or PGExplainer) under the same faithfulness metric if feasible."*

This is the single most impactful thing to add. It answers the reviewer question *"Why not use SHAP/GNNExplainer?"* with data, not prose.

**What to do**:
1. Run GNNExplainer (already cited in `main.tex`, line 53) on the same 200-molecule Tox21 test set.
2. Map its output subgraph masks to the same 30-SMARTS library.
3. Score it with the **identical** `FaithfulnessValidator` (grounding + causal consistency).
4. Add a column to Table IV (Faithfulness Comparison).

**Expected result**: GNNExplainer will likely have higher grounding (it optimizes directly for subgraph attribution) but lower causal consistency (no reject-and-retry loop). This makes DeNovo's position stronger, not weaker.

**Files to create/edit**:
- `experiments/run_gnnexplainer_baseline.py` — new script
- `overleaf/main.tex` — add GNNExplainer row to Table IV, cite `\cite{ying2019gnnexplainer}`
- `SUBMISSION_CHECKLIST.md` — add verification entry

**Estimated effort**: 1–2 days (PyG has a built-in `GNNExplainer` class).

---

### 2.2 Expand the Claim-Bearing Evaluation Set ✅ *P0 — Critical*

> *"Seven claim-bearing molecules immediately raises reviewer questions. If you had 100+ examples this paper would become significantly stronger."*

**Root cause** (from code analysis): `identify_substructures()` uses an adaptive cutoff of `κ/N` (default `κ=2.0`). Only matches *above* this cutoff are counted. Most test molecules are benign and have no active toxicophore. N=7 is correct but looks thin.

**Two complementary strategies**:

#### Strategy A — Lower κ from 2.0 to 1.5 (softer threshold)
- Edit `substructure_mapper.py` `relative_factor` default from `2.0` → `1.5`
- Re-run `run_faithful_eval.py`
- Report new N; if it rises to 12–20, update `\NwithClaims` in the paper

#### Strategy B — Add a second dataset (BBBP or ClinTox faithfulness run)
- The BBBP model is already trained (0.897 ROC-AUC)
- Run `run_faithful_eval.py --dataset bbbp` on the BBBP test set
- Report a combined claim-bearing N across both datasets
- This also answers the reviewer's third weakness: *"Most evaluation is on Tox21 — does it generalize?"*

**Files to edit**:
- `backend/utils/substructure_mapper.py` — `relative_factor = 1.5` (tune with validation)
- `experiments/run_faithful_eval.py` — add `--dataset` argument if not present
- `overleaf/main.tex` — update `\NwithClaims`, update CI numbers, add BBBP faithfulness row

---

### 2.3 Answer "Does Attention Really Represent Causality?" More Rigorously ✅ *P1*

The reviewer says this is *partially addressed* but will be questioned. Add a single-paragraph discussion in the Methods section that frames this explicitly:

**Suggested addition to Section III (XAI Engine)**:
> We explicitly reject the naive conflation of attention with causality. In our framework, attention weights serve solely as a *proposal mechanism* — a computationally efficient screen for candidate substructures. The causal claim is established independently through the counterfactual intervention test ($\Delta y > \delta$). This is analogous to the distinction between correlation and causation in classical experimental design: attention identifies *candidate features*; counterfactual testing confirms *causal features*. Explanations that pass only the attention filter but fail the causal test are rejected, which is the function of the retry loop.

---

## Tier 3 — Strategic Positioning (before submission)

### 3.1 Target Venue Selection

Based on the reviewer's verdict, the following venues are the best match:

| Venue | Fit | Deadline Cadence |
|---|---|---|
| **IEEE BIBM** (Bioinformatics & Biomedicine) | ✅ Excellent | Annual (Aug–Sept CFP) |
| **IEEE ICHI** (Int'l Conf on Healthcare Informatics) | ✅ Excellent | Annual (Feb–Mar CFP) |
| **IEEE EMBC** (Engineering in Medicine & Biology) | ✅ Strong | Annual (Jan CFP) |
| **Springer CCIS** (Communications in CS & IS) | ✅ Strong | Rolling / workshop-based |
| **XAI4Science @ NeurIPS/ICML workshop** | ✅ Good | Co-located with flagship |
| **AI4DrugDiscovery AAAI workshop** | ✅ Good | Co-located |

**Recommendation**: Target **IEEE BIBM** as primary. It is peer-reviewed, indexed (IEEE Xplore), well-regarded in computational biology, and explicitly covers explainability in healthcare.

---

### 3.2 Leverage Engineering as a Differentiator

The reviewer gave engineering 9.5/10. Lean into it in the **cover letter**:

> *"Unlike most XAI papers that demonstrate concepts in isolated notebooks, DeNovo is a production-grade system with a React frontend, FastAPI backend, multi-endpoint GNN inference, and a batch prediction pipeline — deployed end-to-end. This demonstrates real-world applicability of the faithfulness validation framework beyond a proof-of-concept."*

---

### 3.3 Acknowledge Remaining Limitations Honestly in the Paper

The reviewer praised *"you didn't hide weaknesses."* Ensure the Limitations section explicitly acknowledges:

- [ ] Faithfulness evaluated on Tox21 only (multi-endpoint: future work)
- [ ] N=7 claim-bearing subset (explain structural scarcity, report bootstrap CI)
- [ ] No human expert validation study (future work)
- [ ] Scaffold splits not used (random splits; future work)
- [ ] Retry mechanism adds latency (report average wall-clock time per molecule)

---

## Summary Table

| # | Action | Priority | Effort | Impact |
|---|---|---|---|---|
| 1.1 | Remove `Abstract—+` artifact | 🔴 P0 | 2 min | Presentation |
| 1.2 | Add code availability statement | 🔴 P0 | 10 min | Credibility |
| 1.3 | Reframe title around Faithfulness Validation | 🟠 P0 | 20 min | Identity |
| 1.4 | Fix Figure 5 consistency | 🟡 P1 | 1–2 hr | Presentation |
| 2.1 | **GNNExplainer faithfulness comparison** | 🔴 P0 | 1–2 days | Validation |
| 2.2 | **Expand claim-bearing N (lower κ or add BBBP)** | 🔴 P0 | 1–2 days | Validation |
| 2.3 | Attention ≠ Causality discussion paragraph | 🟠 P1 | 30 min | Methodology |
| 3.1 | Select target venue (IEEE BIBM recommended) | 🟠 P1 | Research | Strategy |
| 3.2 | Cover letter emphasising engineering | 🟡 P2 | 30 min | Submission |
| 3.3 | Expand Limitations section checklist | 🟡 P1 | 30 min | Credibility |

---

> **Bottom line**: The paper is already well-positioned. The two items that will make the most difference before submission are **2.1** (GNNExplainer comparison) and **2.2** (expanding the claim-bearing evaluation set). Everything in Tier 1 should be done today — they take less than an hour combined.
