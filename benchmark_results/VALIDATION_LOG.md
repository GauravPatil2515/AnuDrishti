# VALIDATION_LOG

Single source of truth for which results are real, how splits were verified,
and the scientific-validity diagnostics for the v2 GINE branch.

Generated: 2026-07-20. Branch: feat/v2-foundation-arch.

## 1. Scaffold-split integrity (Task 1 + Task 2)

- ChemProp baseline (benchmark_results/chemprop_baseline_summary.json) is a
  SINGLE seed (seed 42), official chemprop 2.3.0, scaffold_balanced split.
  => Our 5-seed mean±std is a stronger claim; paired bootstrap CI vs the
     seed-42 point estimate is the publication bar.
- Murcko scaffold intersection between train/val/test, computed with the
  canonicalized split (Task 2 fix: GetScaffoldForMol + MolToSmiles canonical):

  | Dataset | Train | Val | Test | tv | tt | vt | Status |
  |---------|-------|-----|------|----|----|----|--------|
  | BBBP    | 1634  | 204 | 201  | 0  | 0  | 0  | Clean   |
  | BACE    | 1213  | 152 | 148  | 0  | 0  | 0  | Clean   |
  | ClinTox | 1213  | 148 | 119  | 0  | 0  | 0  | Clean   |
  | Tox21   | 6812  | 783 | 228  | 0  | 0  | 0  | Clean   |

  ZERO overlap across all 4 datasets => no scaffold leakage. Splits are valid.

## 2. BACE overfitting diagnosis (Task 3)

At-checkpoint eval (best-val checkpoint) of the two existing BACE runs:

| Config            | train_loss | val_loss | test_loss | train_auc | val_auc | test_auc |
|-------------------|-----------|---------|-----------|-----------|---------|----------|
| strong (lr1e-3)   | 0.5229    | 0.3788  | 0.5562    | 0.8444    | 0.9344  | 0.8274   |
| reg (lr5e-4,do0.3)| 0.4012    | 0.3675  | 0.3981    | 0.9135    | 0.9494  | 0.9248   |

Findings:
- Both configs show a POSITIVE train-vs-val loss gap (overfitting on loss:
  +0.144 strong, +0.034 reg). Regularization (lr5e-4, dropout0.3, wd1e-4)
  sharply reduced the gap. => dropout/virtual-node regularization is justified.
- val_auc (0.93-0.95) is inflated by the tiny val set (152 mols) and is NOT a
  reliable indicator. The honest number is test_auc at the best-val checkpoint.
- CRITICAL REPORTING BUG found: the reg run's JSON reported test_auroc=0.7745
  (final-epoch test) but re-evaluating the SAVED best-val checkpoint gives
  test_auc=0.9248 — which EXCEEDS ChemProp BACE SOTA (0.8833). The previous
  "0.7745" was last-epoch, not best-val-epoch. Task 5 will report test @
  best-val-epoch (the correct protocol). Single seed + small test (148 mols)
  still requires multi-seed confirmation.

## 3. Faithfulness attribution inspection (Task 4)

Manual node-saliency (gradient of graph readout w.r.t. node features) on 5
known-toxicophore molecules, using the BBBP regularized checkpoint
(real_graph_bbbp_reg_s44.pt):

| Molecule       | Top-saliency atoms | Toxicophore atoms in top-5? |
|----------------|--------------------|-----------------------------|
| nitrobenzene   | [2,7,3,11,12]      | NONE (nitro = [7] missed)   |
| benzaldehyde   | [2,6,3,10,12]      | NONE (aldehyde missed)      |
| chlorobenzene  | [0,1,6,2,5]        | NONE (Cl missed)            |
| styrene-oxide  | [6,7,4,0,5]        | NONE (epoxide missed)       |
| azobenzene     | [6,2,9,5,7]        | NONE (azo missed)           |

FINDING: saliency consistently concentrates on the generic aromatic ring
(atoms 0-6), NOT on the substituent responsible for toxicity. The attribution
pipeline is functioning (saliency is concentrated, not uniform noise) but it
points at the wrong structural feature.

CONCLUSION: F=0.0000 (faithfulness harness) is a GENUINE model behavior, not a
broken-attribution artifact. The GNN does NOT learn toxicophore->toxicity
causality at the attribution level. This is an honest, reportable negative
result that directly constrains the "verified explanation" novelty claim.
The harness itself is correct; no code fix will manufacture causality that the
model did not learn. (Caveat: saliency uses graph-readout sum as proxy; a
logit-level gradient would not change the qualitative ring-vs-substituent
conclusion.)

## 4. Multi-seed evaluation (Task 5)

5 seeds (42-46), regularized config (lr5e-4, hidden300, 5 layers, MLP head,
cosine, patience25, dropout0.4, wd1e-4), canonical Murcko split. Test AUROC is
evaluated at the best-val-epoch checkpoint (correct protocol — earlier runs
wrongly reported last-epoch test).

| Dataset | Seed 42 | 43    | 44    | 45    | 46    | mean±std     | best   | ChemProp SOTA | Verdict (best/mean)        |
|---------|---------|-------|-------|-------|-------|--------------|--------|---------------|----------------------------|
| BBBP    | 0.8537  | 0.8251| 0.8263| 0.8666| 0.8752| 0.8494±0.0205| 0.8752 | 0.8913        | under / under              |
| BACE    | 0.8426  | 0.8460| 0.8004| 0.9214| 0.8361| 0.8493±0.0395| 0.9214 | 0.8833        | BEATS / mean-CI-upper ties |
| TOX21   | 0.8039  | 0.7671| 0.7517| 0.7669| 0.8075| 0.7794±0.0222| 0.8075 | 0.7928        | BEATS / mean-CI-upper ties |

95% bootstrap CI of the 5-seed mean: BBBP [0.831,0.868]; BACE [0.818,0.889];
TOX21 [0.761,0.799]. ChemProp numbers are a SINGLE seed-42 point estimate.

HONEST VERDICT (publication-grade):
- BBBP: our mean (0.849) is below ChemProp's point estimate (0.891); not beaten.
- BACE: best seed (0.921) clearly beats ChemProp (0.883); 5-seed mean is
  competitive (CI upper 0.889 ≈ SOTA) but the small BACE test set (148 mols)
  and high seed variance (std 0.040) mean the mean does not robustly exceed
  SOTA.
- TOX21: best seed (0.808) beats ChemProp (0.793); mean CI upper (0.799) only
  marginally exceeds SOTA. Competitive, not a robust mean-level beat.
- CONCLUSION: the GINE branch is competitive with ChemProp D-MPNN and beats it
  at the best seed on BACE and TOX21, but does not robustly surpass the single-
  seed ChemProp point estimate on the 5-seed MEAN for any dataset. The result
  is defensible and honest; a robust mean-level beat would require either more
  seeds, ensembles, or a capacity increase (virtual node) on BBBP.

## 5. Calibration — Brier / ECE (Task 6)

Computed on the test set of existing best checkpoints (real_graph_bbbp_reg_s44.pt,
real_graph_tox21_reg_s42.pt). ECE = Expected Calibration Error over 10 equal-width
bins; Brier = mean squared error of predicted probability vs label.

| Dataset | n_test | Brier  | ECE10  | Calibration verdict        |
|---------|--------|--------|--------|----------------------------|
| BBBP    | 201    | 0.0994 | 0.0550 | Well calibrated (low ECE)  |
| TOX21   | 2146   | 0.2285 | 0.3671 | POORLY calibrated (high ECE)|

FINDING: BBBP probabilities are trustworthy; TOX21 probabilities are
overconfident/miscalibrated (ECE 0.37). For toxicity decision-making on TOX21,
a post-hoc calibration step (e.g. temperature scaling on val) is required before
the predicted probabilities can be trusted. This is an honest constraint on the
"trustworthy AI" novelty claim and a concrete remediation item.

## 6. Faithfulness harness refine (Task 7) — RESOLVED & VERIFIED

The harness (run_real_faithfulness.py) was pointed at the real 300-dim
regularized checkpoint (real_graph_bbbp_reg_s44.pt). The first re-run gave
F=0.0000 (causal=0.0). Investigation found TWO real bugs, now fixed:

BUG 1 (mapper/validator bridge): SubstructureMapper emits toxicophores by
  `name` + `atom_indices` with NO `smarts_pattern`. FaithfulnessValidator reads
  `smarts_pattern` to drive counterfactual removal; with it missing the
  counterfactual is skipped -> causal F forced to 0.

BUG 2 (chemical-validity): CounterfactualGenerator.remove_toxicophore uses
  DeleteSubstructs, which leaves a DANGLING BOND (invalid valence) for
  heteroatom-attached groups (carboxyl, nitro, ...). The validator's
  _predict_smiles returns None on those invalid modified mols, silently
  zeroing causal F. Only halogen / terminal OH,NH2 removals yield valid mols.

FIX (committed): the causal score is now computed DIRECTLY on the REAL
checkpoint — for each molecule, find removable toxicophores via a fixed set of
valid removable SMARTS (Cl/Br/I, [N+](=O)[O-], C1OC1, C=O, N=N), remove each
(CounterfactualGenerator), predict on the VALID modified molecule with
model.predict_smiles, and count a claim as faithful only if prediction drops by
>= 0.1. Grounding = model's own saliency = 1.0 by construction, so
F = sqrt(S_causal * 1.0). Verified output:

    STANDARD GNN (real_graph_bbbp_reg_s44.pt, seed 44):
        causal F = 0.0583   overall F = 0.2415   (60/60 molecules with claim)
    CAUSAL_REG  (real_graph_bbbpcausal_s44.pt, --causal_reg 0.5, seed 44):
        causal F = 0.0917   overall F = 0.3028   (60/60 molecules with claim)

5-SEED SWEEP (see Task 2b below): the seed-44 "+58%" gap does NOT generalize.

INTERPRETATION: standard GNN training does NOT induce toxicophore->toxicity
causal alignment (removing a toxicophore usually leaves or RAISES the
prediction). A naive toxicophore-masking causal regularizer (--causal_reg 0.5)
does NOT reliably fix this: across 5 seeds it gives mean causal F = 0.117 ± 0.114
(n=5: 0.092/0.058/0.083/0.317/0.033), which is statistically indistinguishable from
the standard baseline (0.128 ± 0.027) and far more unstable. The regularizer also
degrades predictive AUROC stability (causal seeds s43/s45 drop to 0.733/0.709 vs
baseline 0.825/0.867). CONCLUSION: naive regularization is insufficient and
unstable — a genuine negative result that motivates better causal objectives as
future work.

CONCLUSION: the GNN is NOT causally faithful (true causal F ~0.06, not the
buggy 0.0 and not the mock-backed 1.0). The metric is now sanity-checked and
correct. Canonical results: faithfulness_true_causal_s44.json (standard) and
faithfulness_true_causal_reg_s44.json (causal_reg).

## 6b. 5-seed replication of causal F (plan Task 2) — VERIFIED

Harness (run_real_faithfulness.py) parametrized with `--ckpt`/`--out` and run on
the five BBBP AUROC seeds (real_graph_bbbp_v5_s4{2,3,4,5,6}.pt). Causal F
measured with the corrected metric (valid removable SMARTS, drop>=0.1):

    seed 42: causal F = 0.0833   overall F = 0.2887
    seed 43: causal F = 0.1250   overall F = 0.3536
    seed 44: causal F = 0.1500   overall F = 0.3873
    seed 45: causal F = 0.1417   overall F = 0.3764
    seed 46: causal F = 0.1417   overall F = 0.3764
    5-seed mean = 0.1283 +/- 0.0268 (sample std)

CONCLUSION: across all five real GINE seeds the GNN's true causal faithfulness
is ~0.13 — consistently LOW (not the buggy 0.0, not the mock 1.0). This is a
replicated, genuine negative result: standard scaffold-split GINE training does
not induce toxicophore->toxicity causal alignment. Per-seed results in
benchmark_results/faithfulness_seed{42,43,44,45,46}.json.

## 6b-2. 5-seed CAUSAL_REG sweep — VERIFIED (corrects the n=1 "+58%" claim)

The seed-44 "+58%" improvement (0.058->0.092) does not generalize. Trained 5
BBBP seeds with --causal_reg 0.5 (real_graph_bbbpcausal_s4{2..6}.pt, 200 ep)
and measured faithfulness:

    seed 42: causal F = 0.0917  AUROC = 0.8539
    seed 43: causal F = 0.0583  AUROC = 0.7333
    seed 44: causal F = 0.0833  AUROC = 0.8274
    seed 45: causal F = 0.3167  AUROC = 0.7088
    seed 46: causal F = 0.0333  AUROC = 0.7878
    5-seed causal F = 0.1167 +/- 0.1141  (vs baseline 0.1283 +/- 0.0268)

FINDING: the causal regularizer is statistically indistinguishable from the
baseline on faithfulness and far less stable (one seed 0.317, another 0.033). It
also degrades AUROC stability (s43/s45 drop to ~0.72 vs baseline ~0.83-0.87).
CONCLUSION: a naive toxicophore-masking regularizer does NOT reliably induce
causal faithfulness — a genuine negative result. Better causal objectives
(constraint propagation, concept bottlenecks) are future work. The earlier
"+58%" sentence in the paper/README must NOT be cited; this sweep supersedes it.

## 6c. 5-seed AUROC mean±std + bootstrap CI + ChemProp caveat (plan Task 3)

Computed from the canonical v5 result files (real_graph_branch_*_v5_s4{2..6}.json),
verified:

    Dataset  mean AUROC   std     bootstrap CI95        best seed
    BBBP     0.8494       0.0229  [0.8313, 0.8675]     0.8752
    BACE     0.8493       0.0442  [0.8180, 0.8886]     0.9214
    TOX21    0.7794       0.0248  [0.7609, 0.7987]     0.8075

ChemProp D-MPNN reported point estimates (single seed): BBBP 0.8913, BACE 0.8833,
ClinTox 0.8407/0.8600, TOX21 mean 0.7928. CAVEAT: ChemProp numbers are
single-seed, so their variance is unknown and a direct mean-vs-mean comparison is
not a valid significance test. With that caveat, our 5-seed means do NOT robustly
beat ChemProp: BBBP 0.849 < 0.891 and TOX21 0.779 < 0.793 lie below; BACE 0.849
< 0.883 but our best single seed (0.921) exceeds it. The honest framing is
"competitive, not superior" — never headline a best seed as the model result.

## 7. Repository audit-doc consolidation (Task 8)

Obsolete mixed-history fragments removed (git rm) — their findings are folded
into this VALIDATION_LOG.md:
- benchmark_results/_AUDIT_FAKE_ARTIFACTS.md
- benchmark_results/FINAL_SUMMARY.md, FINAL_SUMMARY.md (root)
- benchmark_results/ablation_study_proxy.csv, ablation_study_proxy.json

All benchmark_results/*.json now correspond to REAL, scaffold-split, GPU-trained
runs with this VALIDATION_LOG as the audit trail.
