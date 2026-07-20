# Ablation / Comparison Table — REAL numbers only

Every number below comes from an actual training or baseline run in this repo.
No mock, proxy, or unreproduced figure is included. ChemProp is an official
ChemProp 2.3.0 D-MPNN run (benchmark_results/chemprop_baseline_summary.json,
seed 42, scaffold_balanced split). GINE numbers are our RealGraphBranch
(v2 GINEConv) 5-seed means with bootstrap 95% CI unless marked "(single seed)".

## Table 1. Predictive AUROC vs ChemProp (scaffold split, test set)

| Dataset | ChemProp (1 seed) | GINE 5-seed mean | 95% CI | GINE best seed | beats ChemProp? |
|---------|-------------------|------------------|--------|----------------|-----------------|
| BBBP    | 0.8913            | 0.8494           | [0.831,0.868] | 0.8752 | No (mean below) |
| BACE    | 0.8833            | 0.8493           | [0.818,0.889] | 0.9214 | No (mean below, best above) |
| TOX21 (mean of 12) | 0.7928    | 0.7794           | [0.761,0.799] | 0.8075 | No (mean below) |
| ClinTox FDA/CT | 0.8407 / 0.8600 | — | — | — | not trained |

Honest reading: GINE is **competitive, not superior**. ChemProp is single-seed,
so variance is unknown; a mean-vs-mean gap is not a significance test.

## Table 2. Hyperparameter / regularizer ablations (BBBP, test AUROC)

| Config | value | test AUROC | note |
|--------|-------|------------|------|
| GINE base (5 seeds) | lr 5e-4, hd 300, 5L, MLP head | 0.8494 ± 0.0229 | canonical config |
| GINE lr=3e-4 (seed 42) | lr 3e-4 | 0.8271 | lower LR hurts |
| GINE + causal_reg (5 seeds) | causal_reg 0.5 | 0.7822 ± 0.0600 | AUROC LESS stable than base; F NOT improved |

## Table 3. Faithfulness / explanation (BBBP, real checkpoint)

| Model | causal F (S_causal) | overall F | measured by |
|-------|---------------------|-----------|-------------|
| GINE standard (5 seeds mean) | 0.128 ± 0.027 | 0.36 ± 0.03 | corrected harness, drop≥0.1 |
| GINE + causal_reg (5 seeds mean) | 0.117 ± 0.114 | — | corrected harness, drop≥0.1 |
| GINE + causal_reg (seed 44) | 0.092 | 0.303 | single seed (DO NOT cite as improvement) |
| GINE standard (seed 44) | 0.058 | 0.242 | single seed (earlier) |

Note: causal F is the fraction of toxicophore removals that drop the prediction
by ≥0.1. It is LOW for GNNs (removing a toxicophore usually does not drop, often
raises, the prediction) — a genuine, replicated negative result, NOT the buggy
F=0 and NOT the mock-backed F=1.0. The 5-seed causal_reg sweep shows the
seed-44 "+58%" gap does NOT generalize (0.117 ± 0.114 vs 0.128 ± 0.027 baseline,
indistinguishable; regularizer also destabilizes AUROC). Naive causal
regularization is insufficient — a negative result motivating better causal
objectives as future work.

## Provenance
- GINE 5-seed: benchmark_results/real_graph_branch_{bbbp,bace,tox21}_v5_s4{2..6}.json
- GINE lr3e4 / causal_reg: benchmark_results/real_graph_branch_bbbp_lr3e4.json,
  benchmark_results/real_graph_branch_bbbpcausal_s44.json
- Faithfulness: benchmark_results/faithfulness_seed{42..46}.json,
  benchmark_results/faithfulness_true_causal*_s44.json
- ChemProp: benchmark_results/chemprop_baseline_summary.json
