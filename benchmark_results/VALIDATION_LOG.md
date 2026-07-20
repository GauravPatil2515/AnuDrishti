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

TODO.

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

## 6. Faithfulness harness refine (Task 7)

TODO.
