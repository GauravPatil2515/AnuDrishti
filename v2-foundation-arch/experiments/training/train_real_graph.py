#!/usr/bin/env python3
"""
Real Graph-Only Training (v2-foundation-arch)
=============================================

Trains the REAL edge-aware graph branch (real_graph_branch.RealGraphBranch)
on actual MoleculeNet data with proper scaffold splits, and reports honest
test AUROC per task.

This replaces the placeholder graph branch (mean-pooled one-hot atomic number,
no bonds) with a genuine GINEConv GNN, and uses a SCAFFOLD split (not the
seeded random split used by results/prediction_metrics.json) so the numbers
are comparable to the ChemProp baselines in benchmark_results/chemprop_*.json.

Usage:
  python v2-foundation-arch/experiments/training/train_real_graph.py \
      --dataset tox21 --epochs 30 --batch_size 32 --device cuda

Results are written to benchmark_results/real_graph_branch_<dataset>.json
stamped with git commit, seed, and hardware.
"""

import argparse
import json
import sys
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torch_geometric.data import Batch
from sklearn.metrics import roc_auc_score

# ---- paths ----
# script is in v2-foundation-arch/experiments/training/ -> go up 4 levels to repo root
BASE = Path(__file__).resolve().parent.parent.parent.parent  # repo root
sys.path.insert(0, str(BASE / "v2-foundation-arch" / "architecture_design"))

from real_graph_branch import RealGraphBranch, RealGraphDataset, collate_graph  # noqa: E402

import pandas as pd  # noqa: E402

try:
    from rdkit.Chem.Scaffolds import MurckoScaffold  # noqa: E402
    from rdkit import Chem  # noqa: E402
    HAS_RDKIT = True
except Exception:
    HAS_RDKIT = False


def scaffold_split(smiles_list, seed=42, frac_train=0.8, frac_val=0.1):
    """Murcko scaffold split -> (train_idx, val_idx, test_idx)."""
    scaffolds = {}
    for i, smi in enumerate(smiles_list):
        mol = Chem.MolFromSmiles(smi) if HAS_RDKIT else None
        if mol is None:
            scaf = "none"
        else:
            try:
                scaf = MurckoScaffold.MurckoScaffoldSmiles(mol=mol)
            except Exception:
                scaf = "none"
        scaffolds.setdefault(scaf, []).append(i)
    # Sort by size so largest scaffold groups go to train first
    groups = sorted(scaffolds.values(), key=lambda x: -len(x))
    rng = __import__("random").Random(seed)
    rng.shuffle(groups)
    train, val, test = [], [], []
    n = len(smiles_list)
    for g in groups:
        if len(train) < frac_train * n:
            train += g
        elif len(val) < frac_val * n:
            val += g
        else:
            test += g
    return train, val, test


def load_dataset(name, seed=42):
    csv = BASE / "model-training" / "data" / "raw" / f"{name}_clean.csv"
    df = pd.read_csv(csv)
    if name == "bbbp":
        smiles_col, label_cols = "smiles", ["p_np"]
    elif name == "clintox":
        smiles_col, label_cols = "smiles", ["FDA_APPROVED", "CT_TOX"]
    elif name == "tox21":
        smiles_col = "smiles"
        label_cols = [c for c in df.columns if c not in ("smiles", "mol_id")]
        if "smiles" not in df.columns:
            # tox21_clean may not have a smiles col; fall back to index
            smiles_col = None
    elif name == "bace":
        smiles_col, label_cols = "smiles", ["Class"]
    else:
        raise ValueError(name)

    if smiles_col is None:
        # tox21 without explicit smiles -> cannot featurize; skip
        print(f"[WARN] {name} has no smiles column; skipping")
        return None

    records = []
    for _, row in df.iterrows():
        smi = row[smiles_col]
        if not isinstance(smi, str) or len(smi.strip()) == 0:
            continue
        labels = []
        ok = True
        for c in label_cols:
            v = row[c]
            if pd.isna(v) or v == -1:
                labels.append(float("nan"))
            else:
                labels.append(float(v))
        records.append({"smiles": smi, "label": torch.tensor(labels, dtype=torch.float)})

    smiles_list = [r["smiles"] for r in records]
    tr, va, te = scaffold_split(smiles_list, seed=seed)
    mk = lambda idxs: RealGraphDataset([records[i] for i in idxs])
    return {
        "train": mk(tr), "val": mk(va), "test": mk(te),
        "n_tasks": len(label_cols),
        "n_train": len(tr), "n_val": len(va), "n_test": len(te),
    }


def get_pos_weight(labels):
    labels = torch.stack(labels)
    pw = []
    for i in range(labels.shape[1]):
        col = labels[:, i]
        valid = col[~torch.isnan(col) & (col != -1)]
        if len(valid) == 0:
            pw.append(1.0); continue
        n_pos = valid.sum(); n_neg = len(valid) - n_pos
        pw.append(max(n_neg, 1) / max(n_pos, 1))
    return torch.tensor(pw)


# Toxicophore SMARTS used to build the causal regularizer (from backend
# substructure_mapper TOXICOPHORES). Masking these atoms during training forces
# the model to learn substructure->toxicity causality (the faithfulness test).
_CAUSAL_SMARTS = [
    '[N+](=O)[O-]',      # nitro
    'C1OC1',             # epoxide
    '[CH]=O',            # aldehyde
    'C=CC=O',            # michael acceptor
    'c[Cl,Br,I]',        # halogenated aromatic
    'NN',                # hydrazine
    'N=N',               # azo
    '[N-]=[N+]=N',       # azide
    'c-[NH2]',           # aminoaromatic
]


def _toxicophore_node_mask(batch, device):
    """Return a [N_total] float mask: 1.0 on atoms belonging to a toxicophore,
    0.0 elsewhere. Uses RDKit substruct matches on the original SMILES."""
    from rdkit import Chem
    import numpy as np
    smiles_list = getattr(batch, "smiles", None)
    if smiles_list is None:
        return None
    # build per-graph node offset using batch.batch
    bidx = batch.batch.cpu().numpy()
    n_total = batch.x.size(0)
    mask = np.zeros(n_total, dtype=np.float32)
    # node index ranges per graph
    n_per = np.bincount(bidx) if len(bidx) else np.array([n_total])
    offsets = np.concatenate([[0], np.cumsum(n_per)])
    for gi, smi in enumerate(smiles_list):
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            continue
        local = set()
        for pat in _CAUSAL_SMARTS:
            q = Chem.MolFromSmarts(pat)
            if q is None:
                continue
            for match in mol.GetSubstructMatches(q):
                local.update(match)
        for a in local:
            if a < n_per[gi]:
                mask[offsets[gi] + a] = 1.0
    return torch.from_numpy(mask).to(device)


def train_one(model, head, loader, opt, pos_weight, device, causal_reg=0.0, causal_margin=0.1):
    model.train(); head.train()
    total = 0
    n_batches = 0
    for batch, labels in loader:
        batch = batch.to(device)
        labels = labels.to(device)
        opt.zero_grad()
        out = head(model(batch))
        is_valid = (~torch.isnan(labels)) & (labels != -1)
        clean = torch.nan_to_num(labels, nan=0.0)
        pw = pos_weight.view(1, -1).expand_as(labels)
        loss_raw = F.binary_cross_entropy_with_logits(out, clean, reduction="none")
        loss_raw = loss_raw * (clean * (pw - 1.0) + 1.0)
        loss = (loss_raw * is_valid).sum() / is_valid.sum()

        # --- causal regularizer: removing toxicophore atoms must drop prediction
        if causal_reg > 0:
            tmask = _toxicophore_node_mask(batch, device)
            if tmask is not None and tmask.sum() > 0:
                xm = batch.x.clone()
                xm[tmask.bool()] = 0.0
                bm = batch.clone(); bm.x = xm
                out_m = torch.sigmoid(head(model(bm)))  # [B, T]
                out_o = torch.sigmoid(out.detach())      # use detached orig for stability
                # only penalize for toxic tasks (label==1) where drop is expected
                tox = (clean == 1.0) & is_valid
                drop = out_o - out_m  # positive => prediction dropped
                # want drop >= margin on toxic samples
                penalty = torch.clamp(causal_margin - drop, min=0.0)
                creg = (penalty * tox.float()).sum() / tox.float().sum().clamp(min=1.0)
                loss = loss + causal_reg * creg
        loss.backward(); opt.step()
        total += loss.item()
        n_batches += 1
    return total / max(n_batches, 1)


@torch.no_grad()
def evaluate(model, head, loader, device):
    model.eval(); head.eval()
    preds, labels = [], []
    for batch, lab in loader:
        batch = batch.to(device)
        preds.append(torch.sigmoid(head(model(batch))).cpu())
        labels.append(lab.cpu())
    preds = torch.cat(preds); labels = torch.cat(labels)
    aurocs = []
    for i in range(labels.shape[1]):
        l = labels[:, i]; p = preds[:, i]
        m = (~torch.isnan(l)) & (l != -1) & (~torch.isnan(p))
        lv, pv = l[m].numpy(), p[m].numpy()
        if len(lv) > 1 and len(set(lv.tolist())) > 1:
            aurocs.append(roc_auc_score(lv, pv))
    return sum(aurocs) / len(aurocs) if aurocs else 0.5, aurocs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=["tox21", "bbbp", "clintox", "bace"])
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch_size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--init", default=None,
                    help="Path to a pretrained GraphMAE encoder (.pt) to initialise weights")
    ap.add_argument("--causal_reg", type=float, default=0.0,
                    help="Weight of the toxicophore-masking causal regularizer (0 = off)")
    ap.add_argument("--causal_margin", type=float, default=0.1,
                    help="Required prediction drop when toxicophore atoms are masked")
    ap.add_argument("--hidden_dim", type=int, default=256,
                    help="GNN hidden width (wider -> more capacity)")
    ap.add_argument("--num_layers", type=int, default=4,
                    help="Number of GINEConv layers")
    ap.add_argument("--head_mlp", action="store_true",
                    help="Use a 2-layer MLP head instead of a single Linear")
    ap.add_argument("--schedule", default="none", choices=["none", "cosine"],
                    help="LR schedule")
    ap.add_argument("--patience", type=int, default=0,
                    help="Early stopping patience (epochs w/o val improvement; 0 = off)")
    ap.add_argument("--tag", default="",
                    help="Suffix added to checkpoint/json filenames (e.g. seed id)")
    ap.add_argument("--dropout", type=float, default=0.15,
                    help="GNN dropout (higher = more regularization)")
    ap.add_argument("--weight_decay", type=float, default=1e-5,
                    help="AdamW weight decay")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    data = load_dataset(args.dataset, seed=args.seed)
    if data is None:
        return
    print(f"[{args.dataset}] train={data['n_train']} val={data['n_val']} test={data['n_test']} tasks={data['n_tasks']}")

    tr_loader = DataLoader(data["train"], batch_size=args.batch_size, shuffle=True, collate_fn=collate_graph)
    va_loader = DataLoader(data["val"], batch_size=args.batch_size, collate_fn=collate_graph)
    te_loader = DataLoader(data["test"], batch_size=args.batch_size, collate_fn=collate_graph)

    train_labels = [data["train"].labels[i] for i in range(len(data["train"]))]
    pos_weight = get_pos_weight(train_labels).to(args.device)

    model = RealGraphBranch(out_dim=args.hidden_dim, hidden_dim=args.hidden_dim,
                            num_layers=args.num_layers, dropout=args.dropout).to(args.device)
    if args.init:
        sd = torch.load(args.init, map_location=args.device, weights_only=True)
        model.load_state_dict(sd["model"])
        print(f"[init] loaded pretrained encoder from {args.init}")
    if args.head_mlp:
        head = nn.Sequential(
            nn.Linear(args.hidden_dim, args.hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(args.hidden_dim // 2, data["n_tasks"]),
        ).to(args.device)
    else:
        head = nn.Linear(args.hidden_dim, data["n_tasks"]).to(args.device)
    opt = torch.optim.AdamW(list(model.parameters()) + list(head.parameters()), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = None
    if args.schedule == "cosine":
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)

    best_val = 0
    best_epoch = 0
    patience = getattr(args, "patience", 0)
    wait = 0
    for ep in range(args.epochs):
        loss = train_one(model, head, tr_loader, opt, pos_weight, args.device,
                         causal_reg=args.causal_reg, causal_margin=args.causal_margin)
        val_auroc, _ = evaluate(model, head, va_loader, args.device)
        if val_auroc > best_val:
            best_val = val_auroc
            best_epoch = ep + 1
            torch.save({"model": model.state_dict(), "head": head.state_dict()}, f"checkpoints/real_graph_{args.dataset}{args.tag}.pt")
            wait = 0
        else:
            wait += 1
            if patience and wait >= patience:
                print(f"Early stopping at epoch {ep+1} (no val improve for {patience})")
                break
        print(f"Epoch {ep+1}/{args.epochs} loss={loss:.4f} val_auroc={val_auroc:.4f}")
        if scheduler is not None:
            scheduler.step()

    ckpt = torch.load(f"checkpoints/real_graph_{args.dataset}{args.tag}.pt", weights_only=True)
    model.load_state_dict(ckpt["model"]); head.load_state_dict(ckpt["head"])
    test_auroc, task_aurocs = evaluate(model, head, te_loader, args.device)
    print(f"\n>>> {args.dataset} REAL graph branch test AUROC = {test_auroc:.4f}")

    try:
        commit = __import__("subprocess").check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        commit = "unknown"
    hw = torch.cuda.get_device_name(0) if args.device == "cuda" else "CPU"

    out = {
        "model": "RealGraphBranch (GINEConv, atom+bond features)",
        "dataset": args.dataset,
        "split": "murcko_scaffold",
        "seed": args.seed,
        "epochs": args.epochs,
        "test_auroc_mean": round(test_auroc, 4),
        "per_task_auroc": [round(x, 4) for x in task_aurocs],
        "n_train": data["n_train"], "n_val": data["n_val"], "n_test": data["n_test"],
        "git_commit": commit,
        "hardware": hw,
        "note": "Real GINEConv GNN with atom+bond featurization; replaces one-hot linear stub.",
        "hidden_dim": args.hidden_dim,
        "num_layers": args.num_layers,
        "head_mlp": args.head_mlp,
        "schedule": args.schedule,
        "dropout": args.dropout,
        "weight_decay": args.weight_decay,
        "best_val_auroc": round(float(best_val), 4),
        "best_epoch": best_epoch,
        "causal_reg": args.causal_reg,
        "causal_margin": args.causal_margin,
    }
    out_path = BASE / "benchmark_results" / f"real_graph_branch_{args.dataset}{args.tag}.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Saved -> {out_path}")


if __name__ == "__main__":
    main()
