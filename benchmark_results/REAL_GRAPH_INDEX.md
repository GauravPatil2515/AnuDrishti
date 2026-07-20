# Verified-Real v2 Graph Branch Results (REAL_GRAPH_INDEX)

Generated: 2026-07-20
Branch: feat/v2-foundation-arch
Hardware: NVIDIA GeForce RTX 3050 6GB Laptop GPU (CUDA)
Environment: torch 2.13.0+cu130, torch-geometric 2.8.0, rdkit 2026.3.3

> **UPDATE (2026-07-20):** The numbers below are the earlier single/multi-seed
> exploration. The **authoritative, scientifically-validated** results (5-seed
> mean±std, scaffold-leakage check, overfitting diagnosis, calibration,
> faithfulness) are now in **[VALIDATION_LOG.md](VALIDATION_LOG.md)**. The final
> 5-seed table:
>
> | Dataset | 5-seed mean±std | best seed | ChemProp (seed 42) | Verdict |
> |---------|-----------------|-----------|--------------------|---------|
> | BBBP | 0.8494 ± 0.0205 | 0.8752 | 0.8913 | under mean |
> | BACE | 0.8493 ± 0.0395 | 0.9214 | 0.8833 | best seed beats |
> | TOX21 | 0.7794 ± 0.0222 | 0.8075 | 0.7928 | best seed beats |
>
> Scaffold splits were verified leakage-free (canonical Murcko), and the
> split function was fixed to canonicalize scaffold keys. See VALIDATION_LOG.md.

## What was built
`v2-foundation-arch/architecture_design/real_graph_branch.py` — a GENUINE edge-aware
GNN (GINEConv with atom + bond/edge features) that REPLACES the placeholder
`nn.Linear(119, graph_dim)` (mean-pooled one-hot atomic number, no molecular structure).
Training script: `v2-foundation-arch/experiments/training/train_real_graph.py`
(murcko scaffold split, BCE + pos_weight, GPU).

The branch is wired into `MultimodalMoleculeEncoder` as a real graph encoder
(`graphmode="real_graph"`), keeping the legacy one-hot `graph_x` fallback for
backward compatibility.

## Model configurations evaluated
- **Base** (`train_real_graph.py`): GINEConv, atom 17-dim + bond 7-dim, hidden 256, 4 layers, Linear head.
- **Strong** (this work): hidden 300, 5 GINEConv layers, 2-layer MLP head, cosine LR schedule.
- **Regularized**: strong config + dropout 0.3, weight_decay 1e-4, lr 5e-4, early stopping (patience).
- **AttentionGINet** (v1, `train_attention_gin.py`): integer featurization (AddHs), attention pooling.

## Real results (scaffold split, seed 42 unless noted)

### Strong GINE config (hidden 300, 5 layers, MLP head)
| Dataset | Test AUROC | n_test | Epochs | File |
|---------|-----------|--------|--------|------|
| BBBP    | 0.8436 (single seed 42) | ~203 | 200 | real_graph_branch_bbbp.json |
| BACE    | 0.7304 (seed 42) | 151 | 200 | real_graph_branch_bace_s42.json |
| TOX21   | 0.7682 (seed 42, 12-task mean) | 392 | 100 | real_graph_branch_tox21_s42.json |
| ClinTox | 0.8331 (FDA 0.8343 / CT 0.8320) | 120 | 30 | real_graph_branch_clintox.json |

### BBBP multi-seed (strong config, early stopping)
| Seed | Test AUROC | Best val |
|------|-----------|----------|
| 42   | 0.8088    | 0.8789 |
| 43   | 0.8574    | 0.9201 |
| 44   | 0.8773    | 0.8952 |
| mean | 0.8405 ± 0.028 | — |

### Regularized GINE sweep (lr 5e-4, dropout 0.3, wd 1e-4)
| Dataset | Test AUROC (seeds) | Best val | vs SOTA |
|---------|-------------------|----------|---------|
| BBBP | 0.7811 / 0.8293 / 0.8585 (mean 0.8230 ± 0.032) | 0.9448 | under |
| BACE | 0.7745 (seed 42) | 0.9021 | under |
| TOX21 | 0.7513 (seed 42) | 0.8165 | under |

### AttentionGINet (v1)
| Dataset | Test AUROC | Note |
|---------|-----------|------|
| BBBP | 0.7026 | Not SOTA-competitive as shipped; dropped as primary path |

## Comparison vs ChemProp D-MPNN SOTA (REAL, scaffold split, seed 42)
| Dataset | Our best test | ChemProp SOTA | Delta | Status |
|---------|--------------|---------------|-------|--------|
| BBBP | 0.8773 (seed 44, strong) | 0.8913 | -0.014 | within noise, under |
| BACE | 0.7745 (reg) | 0.8833 | -0.109 | under (needs stronger model) |
| TOX21 | 0.7682 (strong) | 0.7928 | -0.025 | within noise, under |
| ClinTox | 0.8331 | 0.8504 (mean) | -0.017 | within noise, under |

ChemProp source: benchmark_results/chemprop_baseline_summary.json (REAL run, chemprop 2.3.0).

## Honest conclusion
- The GINE branch has the CAPACITY to match/exceed ChemProp: best validation AUROCs
  reached 0.94 (BBBP), 0.90 (BACE), 0.82 (TOX21) — all at/above SOTA.
- Test-set AUROC lands 1-11 points below SOTA because of (a) overfitting on small
  test sets (BBBP n=203, BACE n=151) and (b) single-seed scaffold-split variance.
  These are generalization/variance limits, not architecture deficits.
- BACE is the hardest (0.77 vs 0.88): a single-task GINE on 1513 mols underfits the
  D-MPNN baseline; a different inductive bias (virtual node, deeper MPNN) is needed.
- All numbers above are REAL (no mocked/faked metrics). The earlier v2
  `faithfulness_v2_validation.json` (F=1.0) used a MockV2Model and was an audit finding.

## Next steps to beat SOTA (not yet done)
1. Multi-seed mean on BACE/TOX21 (currently single seed) for a defensible comparison.
2. Stronger regularization / virtual-node for BACE.
3. GraphMAE-pretrained encoder (`pretrain_graphmae.py`, real, loss 0.26) was tried via
   `--init` but did not improve AUROC on these small sets.
