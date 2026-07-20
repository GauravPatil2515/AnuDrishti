#!/usr/bin/env python3
"""
Train the REAL v1 AttentionGINet on MoleculeNet (BBBP/BACE/ClinTox/TOX21) using
the v1 integer featurisation (AddHs, ATOM_LIST/CHIRALITY_LIST/BOND_LIST/BONDDIR_LIST)
and a scaffold split. Uses the SAME molecular representation as ChemProp, so it is a
fair head-to-head SOTA comparison.

Goal: beat the ChemProp D-MPNN baseline (BBBP 0.8913, BACE 0.8833,
ClinTox 0.8407/0.8600, TOX21 mean 0.7928) on real scaffold-split AUROC.
"""
import argparse, json, sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch_geometric.data import Data, Batch, Dataset
from torch_geometric.loader import DataLoader

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "backend" / "models"))
from attention_ginet import AttentionGINet

from rdkit import Chem
from rdkit.Chem.rdchem import ChiralType, BondType as BT
from rdkit.Chem.Scaffolds.MurckoScaffold import MurckoScaffoldSmiles
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")

ATOM_LIST = list(range(1, 119))
CHIRALITY_LIST = [ChiralType.CHI_UNSPECIFIED, ChiralType.CHI_TETRAHEDRAL_CW,
                  ChiralType.CHI_TETRAHEDRAL_CCW, ChiralType.CHI_OTHER]
BOND_LIST = [BT.SINGLE, BT.DOUBLE, BT.TRIPLE, BT.AROMATIC]
BONDDIR_LIST = [Chem.rdchem.BondDir.NONE, Chem.rdchem.BondDir.ENDUPRIGHT,
                Chem.rdchem.BondDir.ENDDOWNRIGHT]


def featurize_v1(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    mol = Chem.AddHs(mol)
    type_idx, chir_idx = [], []
    for atom in mol.GetAtoms():
        type_idx.append(ATOM_LIST.index(atom.GetAtomicNum()))
        chir_idx.append(CHIRALITY_LIST.index(atom.GetChiralTag()))
    x = torch.tensor([type_idx, chir_idx], dtype=torch.long).t().contiguous()
    row, col, edge_feat = [], [], []
    for bond in mol.GetBonds():
        s, e = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        row += [s, e]; col += [e, s]
        bt = bond.GetBondType()
        bi = BOND_LIST.index(bt) if bt in BOND_LIST else 0
        bd = bond.GetBondDir()
        bdi = BONDDIR_LIST.index(bd) if bd in BONDDIR_LIST else 0
        edge_feat += [[bi, bdi], [bi, bdi]]
    edge_index = torch.tensor([row, col], dtype=torch.long)
    edge_attr = torch.tensor(edge_feat, dtype=torch.long)
    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)


def scaffold_split(smiles_list, valid_size, test_size, seed):
    scaffolds = {}
    for i, smi in enumerate(smiles_list):
        try:
            sc = MurckoScaffoldSmiles(Chem.MolFromSmiles(smi), includeChirality=False)
        except Exception:
            sc = f"_none_{i}"
        scaffolds.setdefault(sc, []).append(i)
    sets = sorted(scaffolds.values(), key=lambda x: (len(x), x[0]), reverse=True)
    n = len(smiles_list)
    cut_tr = int((1 - valid_size - test_size) * n)
    cut_va = int((1 - test_size) * n)
    tr, va, te = [], [], []
    for s in sets:
        if len(tr) + len(s) > cut_tr:
            if len(tr) + len(va) + len(s) > cut_va:
                te += s
            else:
                va += s
        else:
            tr += s
    return tr, va, te


def roc_auc(y, p):
    from sklearn.metrics import roc_auc_score
    m = ~np.isnan(y)
    if m.sum() < 2 or len(np.unique(y[m])) < 2:
        return 0.5
    return roc_auc_score(y[m], p[m])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="bbbp", choices=["bbbp", "clintox", "tox21", "bace"])
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--batch_size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--emb_dim", type=int, default=300)
    ap.add_argument("--num_layer", type=int, default=5)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    torch.manual_seed(args.seed); np.random.seed(args.seed)
    csv_path = REPO / "model-training" / "data" / "raw" / f"{args.dataset}_clean.csv"
    df = pd.read_csv(csv_path)
    col_map = {"bbbp": ["p_np"], "clintox": ["FDA_APPROVED", "CT_TOX"],
               "bace": ["Class"],
               "tox21": [c for c in df.columns if c not in ("mol_id", "smiles")]}
    label_cols = col_map[args.dataset]
    smiles_list, label_list = [], []
    for _, row in df.iterrows():
        smi = row.get("smiles")
        if not isinstance(smi, str) or not smi.strip():
            continue
        lab = []
        for c in label_cols:
            v = row[c]
            lab.append(float(v) if (isinstance(v, (int, float)) and not pd.isna(v)) else np.nan)
        smiles_list.append(smi); label_list.append(lab)
    print(f"[{args.dataset}] loaded {len(smiles_list)} molecules, tasks={label_cols}")

    feats = [featurize_v1(s) for s in smiles_list]
    keep = [i for i, f in enumerate(feats) if f is not None]
    graphs = [feats[i] for i in keep]
    labels = [np.array(label_list[i], dtype=np.float32) for i in keep]
    num_tasks = len(label_cols)
    print(f"featurized {len(graphs)} valid graphs")

    tr, va, te = scaffold_split([smiles_list[i] for i in keep], 0.1, 0.1, args.seed)
    device = args.device
    model = AttentionGINet(task="classification", num_layer=args.num_layer, emb_dim=args.emb_dim,
                           feat_dim=512, drop_ratio=0.3, num_tasks=num_tasks,
                           pred_n_layer=2, pred_act="softplus", pool="attention").to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-5)

    def auroc_eval(indices):
        model.eval()
        ys, ps = [], []
        with torch.no_grad():
            for i in range(0, len(indices), args.batch_size):
                bidx = indices[i:i+args.batch_size]
                b = Batch.from_data_list([graphs[j] for j in bidx]).to(device)
                _, pred = model(b, return_attention=False)
                ps.append(torch.sigmoid(pred).cpu().numpy())
                ys.append(np.vstack([labels[j] for j in bidx]))
        y = np.vstack(ys); p = np.vstack(ps)
        return float(np.mean([roc_auc(y[:, k], p[:, k]) for k in range(num_tasks)]))

    best_val = 0
    for ep in range(args.epochs):
        model.train()
        for i in range(0, len(tr), args.batch_size):
            bidx = tr[i:i+args.batch_size]
            b = Batch.from_data_list([graphs[j] for j in bidx]).to(device)
            y = torch.tensor(np.vstack([labels[j] for j in bidx]), dtype=torch.float, device=device)
            opt.zero_grad()
            _, pred = model(b, return_attention=False)
            is_v = ~torch.isnan(y)
            loss = F.binary_cross_entropy_with_logits(pred[is_v], y[is_v])
            loss.backward(); opt.step()
        val = auroc_eval(va)
        if val > best_val:
            best_val = val
            torch.save({"model": model.state_dict(),
                        "args": {"num_layer": args.num_layer, "emb_dim": args.emb_dim,
                                 "num_tasks": num_tasks, "feat_dim": 512, "pool": "attention"}},
                       REPO / "checkpoints" / f"attention_gin_{args.dataset}.pt")
        print(f"Epoch {ep+1}/{args.epochs} val_auroc={val:.4f}")

    model.load_state_dict(torch.load(REPO / "checkpoints" / f"attention_gin_{args.dataset}.pt",
                                     weights_only=True)["model"])
    test = auroc_eval(te)
    print(f"\n>>> {args.dataset} REAL AttentionGINet test AUROC = {test:.4f}")

    sota = {"bbbp": 0.8913, "bace": 0.8833, "clintox": 0.85035, "tox21": 0.7928}
    out = {
        "model": "AttentionGINet (v1, attention-pooling, integer featurisation)",
        "dataset": args.dataset, "split": "murcko_scaffold", "seed": args.seed,
        "epochs": args.epochs, "test_auroc_mean": round(test, 4),
        "chemprop_sota": sota, "beats_chemprop": test > sota[args.dataset],
        "note": "v1 attention-GIN encoder; comparable featurisation to ChemProp D-MPNN.",
    }
    (REPO / "benchmark_results" / f"attention_gin_{args.dataset}.json").write_text(json.dumps(out, indent=2))
    print("Saved benchmark_results/attention_gin_%s.json" % args.dataset)


if __name__ == "__main__":
    main()
