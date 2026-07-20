# Paper Reframe & Rigor Plan — "Competitive GNN + Verified Explanation"

> **For Hermes:** Plan mode deliverable only. Do NOT execute. Verify each gate
> with real tool output before marking done. Non-force git pushes only.

**Goal:** Reshape the paper (and its supporting experiments) so the core
contribution is *competitive prediction + a causally-verified explanation layer
+ honest small-dataset generalization analysis* — NOT a mean-AUROC SOTA claim
the data does not support — and resolve the one unverified headline number
before any submission.

**Architecture of the work:** (1) a verification gate that proves the
faithfulness headline is real or reframes it honestly; (2) a local
"positive-control" experiment that demonstrates the faithfulness engine actually
works (runs on a causally-constrained GNN, no live LLM needed); (3) paper
restructure (Abstract/Fig1, Methods, 3 Results subsections, Related Work,
Discussion, Limitations, Reproducibility); (4) statistical rigor (5-seed
mean±std + paired test vs ChemProp point estimate with an explicit variance
caveat).

**Tech Stack:** Python 3.11 venv (`.venv`), torch-geometric, rdkit,
`experiments/run_faithful_eval.py`, `v2-foundation-arch/.../train_real_graph.py`,
overleaf LaTeX (main.tex). The trained GINE checkpoints already exist under
`benchmark_results/real_graph_branch_*_v5_s4*.json` + `checkpoints/`.

---

## GATE 0 — Verify the headline faithfulness number is REAL (BLOCKER)

**Objective:** Determine whether the paper's primary claim (F=1.000 constrained
vs F=0.054 unconstrained) is backed by a real run. Current evidence says NO:
`benchmark_results/faithfulness_v2_validation.json` records
`model_type: MockV2Model (CPU mock)` and `hardware: CPU (mock validation)`.

**Files:**
- Inspect: `experiments/run_faithful_eval.py`, `experiments/run_unconstrained_baseline.py`, `experiments/compare_baselines.py`
- Inspect: `benchmark_results/faithfulness_v2_validation.json` (already read — mock)
- Inspect: `overleaf/main.tex:20-40` (the `\Fconstrained{1.000}` macros)

**Step 1: Confirm the live-LLM pipeline is real or still mocked**
Read `run_faithful_eval.py` fully (410 lines). Grep for the actual LLM call:
`grep -nE "api_key|os.environ|groq|openai|requests.post|anthropic|TODO|placeholder|mock" experiments/run_faithful_eval.py`.
Expected: either a real `requests.post`/`openai` call to a live model, OR a
`# TODO`/mock branch. Report which.

**Step 2: Decision branch (record the outcome, do NOT skip)**
- IF a real API key + live LLM path exists AND is runnable:
  run `python experiments/run_faithful_eval.py --model checkpoints/real_graph_bbbp_reg_s44.pt --output results/faithful_constrained/`
  then `python experiments/run_unconstrained_baseline.py ...` and
  `python experiments/compare_baselines.py ...`.
  Capture real F_constrained, F_unconstrained into JSON. Compare to 1.000 / 0.054.
- IF no API key / LLM unavailable in this environment:
  the honest move is to **NOT claim F=1.000 on a live model**. Reframe the
  headline contribution around (a) the verification *methodology* (geometric-
  mean zero-forcing metric + reject-and-retry protocol) and (b) the GNN-level
  causal-verification finding in Task 2 below. State the live-LLM gap as a
  limitation with the protocol specified so a reviewer could reproduce it.

**Step 3: Commit the gate finding**
```bash
git add -A  # only the inspection notes / any re-run JSONs
git commit -m "audit: verify faithfulness headline source (real run vs mock)"
```

**Exit criteria:** We know, with evidence, whether F=1.000/0.054 is real. No
paper edits proceed claiming that number unless Step 2 produced a real run.

---

## Task 1 — Local positive-control: prove the faithfulness engine WORKS

**Objective:** Give the paper a *reproducible, local* striking result: run the
faithfulness validator on a GNN trained WITH causal regularization. If the
engine is sound, a causally-aligned GNN must score F>0 (the "positive control"),
whereas the standard GNN scores F=0 (Task 2). This is the missing evidence that
the engine is not trivially returning 0.

**Files:**
- Modify: `v2-foundation-arch/experiments/training/train_real_graph.py` (already has `--causal_reg`, `--causal_margin`, `_toxicophore_node_mask`)
- Run: `v2-foundation-arch/experiments/ablations/run_real_faithfulness.py` (already points at `real_graph_bbbp_reg_s44.pt`)
- Inspect: `_toxicophore_node_mask(batch, device)` at `train_real_graph.py:159`

**Step 1: Verify the causal mask is non-empty**
Add a 1-line debug print in `_toxicophore_node_mask` (or a scratch script) to
count how many batch molecules have a non-empty toxicophore mask. If it is ~0,
the causal_reg penalty never fires — that is why earlier `--causal_reg` runs gave
F=0. Fix: ensure the SMARTS toxicophore library (`toxicophore_lib` import in
run_real_faithfulness.py) is the same one the trainer uses.

**Step 2: Train a causally-constrained GINE (seed 44, BBBP)**
```bash
"$P/.venv/bin/python" v2-foundation-arch/experiments/training/train_real_graph.py \
  --dataset bbbp --seed 44 --hidden_dim 300 --num_layers 5 --head mlp \
  --lr 5e-4 --dropout 0.4 --weight_decay 1e-4 --patience 25 --cosine \
  --causal_reg 0.5 --causal_margin 0.1 --tag causal_s44
```
Expected: trains without error; saves `checkpoints/real_graph_bbbp_causal_s44.pt`.

**Step 3: Run faithfulness on the constrained checkpoint**
Temporarily point `run_real_faithfulness.py` at `real_graph_bbbp_causal_s44.pt`
(edit the `ckpt_path` line, same pattern as the s44 fix already committed).
Run it. Expected: `mean_F > 0` (positive control passes) — proving the engine
rewards causal alignment.

**Step 4: Commit**
```bash
git add v2-foundation-arch/experiments/training/train_real_graph.py \
        v2-foundation-arch/experiments/ablations/run_real_faithfulness.py \
        benchmark_results/faithfulness_causal_s44.json
git commit -m "exp: causally-constrained GNN scores F>0 (faithfulness engine positive control)"
```

**Exit criteria:** Real JSON showing F>0 on the constrained ckpt AND F=0 on the
standard ckpt (re-run standard to reconfirm). This pair is the paper's local
striking evidence regardless of the live-LLM gate.

---

## Task 2 — Multi-seed GNN faithfulness (replicate the F=0 negative finding)

**Objective:** The strategy notes "if replicated across seeds, it's evidence
standard GNN training doesn't induce causal alignment." Run faithfulness on all
5 BBBP seeds.

**Files:** `run_real_faithfulness.py` (loop over seeds), or a 1-shot loop script.

**Step 1: Loop the validator over the 5 seed checkpoints**
```python
for s in [42,43,44,45,46]:
    ckpt = f"checkpoints/real_graph_bbbp_reg_s{s}.pt"
    # point run_real_faithfulness at ckpt, run, record mean_F
```
Expected: all 5 yield F≈0.0000 (consistent negative result).

**Step 2: Commit the multi-seed faithfulness table**
```bash
git commit -m "exp: GNN faithfulness F=0 replicated across 5 seeds (negative result)"
```

---

## Task 3 — Significance test vs ChemProp (statistical rigor)

**Objective:** Replace best-seed comparisons with mean±std + a paired test, with
an explicit caveat that ChemProp is a single-seed point estimate.

**Files:** `benchmark_results/real_graph_branch_*_v5_s4*.json` (source of truth).
Write a small analysis script under `/tmp/hermes-verify-*.py` (ad-hoc, not committed).

**Step 1: Compute paired bootstrap / Wilcoxon**
For each dataset, bootstrap the 5-seed mean CI (already done in VALIDATION_LOG:
BBBP [0.831,0.868], BACE [0.818,0.889], TOX21 [0.761,0.799]) and state clearly:
"ChemProp reports a single seed (42); no variance is published, so we compare
our 5-seed distribution to their point estimate and report overlap of the 95%
bootstrap CI." This is the honest framing the strategy demands.

**Step 2: Record verbatim into VALIDATION_LOG.md Task 5 section** (already has
the CI; add the explicit ChemProp-no-variance caveat sentence).

**Step 3: Commit**
```bash
git commit -m "docs: add explicit ChemProp single-seed variance caveat to VALIDATION_LOG"
```

---

## Task 4 — Ablation table (graph-only vs multimodal; no-pretrain vs GraphMAE)

**Objective:** Provide the ablation subsection the strategy requires. We have the
pieces: GraphMAE pretrain (`pretrain_graphmae.py`, real, loss 0.26), AttentionGINet
(v1, 0.7026), and the GINE branch. Produce a clean table of AUROC contributions.

**Files:** existing results in `benchmark_results/REAL_GRAPH_INDEX.md` (AttentionGINet
0.7026, reg sweep, GraphMAE tried via `--init` but no improvement).

**Step 1: Assemble the ablation table from REAL existing numbers**
| Configuration | BBBP | BACE | TOX21 | Note |
| graph-only GINE (reg) | 0.849±0.021 | 0.849±0.040 | 0.779±0.022 | final |
| + multimodal (SMILES+desc, cross-attn) | — | — | — | if runnable, else mark "not trained this pass" |
| GraphMAE pretrain (`--init`) | no gain | — | — | from REAL_GRAPH_INDEX |
| AttentionGINet v1 (baseline) | 0.7026 | — | — | dropped |

Do NOT invent multimodal numbers. If the multimodal encoder was never trained
end-to-end, state that as a limitation, not a missing result.

**Step 2: Commit the ablation assembly** (doc-only).

---

## Task 5 — Paper restructure (overleaf/main.tex)

**Objective:** Apply the reframe. Lead with verified-explanation contribution;
move exploration to appendix; add 3 Results subsections; rewrite Related Work,
Discussion, Limitations, Reproducibility.

**Files:** `overleaf/main.tex` (689 lines). Edit sections by line.

### Task 5a — Abstract (lines 63-71) + Fig 1
- Rewrite abstract to: (1) one-sentence achievement = "a multimodal molecular
  architecture competitive with SOTA GNN baselines that provides the first
  causally-verified explanation layer for toxicity GNNs"; (2) why hard = existing
  GNN explainers give no causal guarantee; (3) striking evidence = the
  faithfulness engine's positive-control gap (F>0 on constrained vs F=0 on
  standard GNN, Task 1) — NOT the AUROC leaderboard.
- Remove the "test ROC-AUC of 0.802" headline claim (that was v1/AUROC-led).
- Fig 1 caption: state contribution + hard-part + evidence sentence.

### Task 5b — Methods (lines 223-403): make self-contained, push exploration to appendix
- Keep: Faithfulness Validator (F = √(S_grounding·S_causal), zero-forcing prop),
  Unconstrained Baseline protocol, Counterfactual Generator.
- Move to appendix (new `\appendix` section): Attention-GIN 0.70 narrative
  (lines 240-278), Transfer Learning (279-293), regularization sweep.
- State FINAL architecture directly: GINE (atom17+bond7, 5 layers, MLP head) +
  faithfulness engine. Do not narrate what didn't work in the main flow.

### Task 5c — Results (lines 464-588): 3 explicit subsections
1. **Predictive performance vs ChemProp/Uni-Mol** (lines 467-497): table with
   mean±std across 5 seeds + bootstrap CI + the ChemProp-single-seed caveat (Task 3).
   State what to look at: "our mean lands within the CI of ChemProp's point
   estimate on BACE/TOX21; below on BBBP."
2. **Ablation study** (lines 499-525): the Task 4 table.
3. **Faithfulness verification** (lines 531-561): its OWN subsection with its own
   protocol. Report Task 1 (positive control F>0 vs F=0) and Task 2 (5-seed F=0
   negative result). Frame F=0 as analysis, not failure.

### Task 5d — Related Work (lines 113-169): group by assumption
- GNN explainers (GNNExplainer, PGExplainer, SubgraphX): state the causal
  guarantee they LACK that our counterfactual-validated F provides (novelty wedge).
- 3D methods (Uni-Mol): "assume 3D conformer availability; we assume only 2D
  graph + SMILES for broad applicability."
- LLM-in-chemistry: position our verifiable-explanation layer against
  unfaithful LLM narratives.

### Task 5e — Discussion (lines after 588): turn weaknesses into analysis
- BACE underperformance: small dataset (1513 mols, 148 test) + overfitting
  evidenced by train/val loss gap (VALIDATION_LOG Task 3).
- Val-test gap despite verified scaffold splits: small-test variance is a known
  MoleculeNet limitation, not unique to our method.
- F=0 as a publishable negative result: standard GNN training doesn't induce
  causal toxicophore alignment (replicated across 5 seeds).

### Task 5f — Limitations paragraph + Reproducibility statement
- Add explicit Limitations paragraph (top-tier venues penalize its absence).
- Add Reproducibility statement referencing `benchmark_results/VALIDATION_LOG.md`
  as the audit trail (this is a genuine asset for IEEE-style venues).

**Step (per 5a-5f): edit, then `pdflatex` if available, else `grep` the edited
section to confirm the change; commit each subsection separately:**
```bash
git add overleaf/main.tex
git commit -m "paper: <subsection> reframe per rigor plan"
```

---

## Task 6 — Docs cross-link (README / REAL_GRAPH_INDEX → VALIDATION_LOG)

**Objective:** Ensure all three docs agree and point to the audit trail.

**Files:** `README.md`, `benchmark_results/REAL_GRAPH_INDEX.md` (both already
updated this session), `benchmark.

**Step 1:** Confirm both already cite VALIDATION_LOG (done). Add a one-line note
in REAL_GRAPH_INDEX pointing readers to the paper's Reproducibility statement.

**Step 2: Commit + push (non-force)**
```bash
git add -A
git commit -m "docs: cross-link paper reproducibility to VALIDATION_LOG"
git push origin feat/v2-foundation-arch
```

---

## Risks / Tradeoffs / Open Questions
- **Live-LLM gate (Gate 0) is the biggest risk.** If no API key is available,
  we cannot substantiate F=1.000/0.054. The fallback (methodology + local GNN
  positive-control) is honest and still a strong contribution — but it changes
  the paper's headline from "we achieve F=1.000" to "we provide a verifiable
  explanation methodology demonstrated on GNN predictions." That is the correct,
  defensible framing regardless.
- **Multimodal encoder never trained end-to-end** → do not claim multimodal
  AUROC. Keep it as architecture + limitation.
- **F=0 could be read as "our method failed."** Mitigation: frame as a field-
  level negative result with the positive-control contrast (Task 1).
- **ChemProp has no published variance** → we must state this limitation
  explicitly every time we compare (Task 3). Never headline best-seed.

## Verification Summary (ad-hoc, not suite-green)
- Gate 0: real vs mock confirmation with file evidence.
- Task 1: real JSON `faithfulness_causal_s44.json` with F>0.
- Task 2: 5 seed F-values recorded.
- Task 3: bootstrap CI + caveat in VALIDATION_LOG.
- Task 5: each subsection edited + committed; `pdflatex` build if available.
- No canonical test/lint command exists; verification = real script output.
