#!/usr/bin/env python3
"""
GraphMAE self-supervised pretraining (v2-foundation-arch)
=========================================================

Trains a GraphMAE on the REAL MoleculeNet molecules we already have locally
(bbbp + clintox + tox21 + bace). No external download (disk/RAM constrained).

Objective: mask ~15% of atom features, reconstruct them with a lightweight
decoder. The encoder (RealGraphBranch) learns chemically meaningful node
embeddings that we then use to INITIALISE the supervised graph branch, so that
removing a toxicophore produces a meaningful prediction shift (causal faithfulness).

Usage:
  python pretrain_graphmae.py --epochs 20 --device cuda --out checkpoints/graphmae_encoder.pt
"""
import argparse
import sys
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Batch
from torch_geometric.loader import DataLoader

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO / "v2-foundation-arch" / "architecture_design"))
sys.path.insert(0, str(REPO / "v2-foundation-arch"))
sys.path.insert(0, str(REPO / "model-training"))  # for data loading helpers

from real_graph_branch import RealGraphBranch, featurize_mol  # noqa: E402


class GraphMAE(nn.Module):
    """Encoder (RealGraphBranch) + masked-atom reconstruction decoder.

    The encoder produces per-node embeddings; a decoder reconstructs the
    MASKED input atom features. We train with MSE on masked nodes only.
    """

    def __init__(self, in_atom_dim=17, hidden=256, mask_rate=0.15):
        super().__init__()
        self.encoder = RealGraphBranch(
            in_atom_dim=in_atom_dim, in_edge_dim=7, hidden_dim=hidden,
            out_dim=hidden, num_layers=4, dropout=0.15,
        )
        # decoder: node embedding -> reconstructed atom feature
        self.decoder = nn.Sequential(
            nn.Linear(hidden, hidden), nn.ReLU(), nn.Linear(hidden, in_atom_dim),
        )
        self.mask_rate = mask_rate

    def forward(self, batch):
        x_orig = batch.x.clone()  # original features = reconstruction target (keep!)
        x_masked = batch.x.clone()
        # mask a random subset of nodes (global indices across the batch)
        num_nodes = x_orig.size(0)
        perm = torch.randperm(num_nodes, device=x_orig.device)
        n_mask = max(1, int(self.mask_rate * num_nodes))
        masked_idx = perm[:n_mask]
        # zero the masked atom features (simple, effective mask token)
        x_masked[masked_idx] = 0.0
        batch = batch.clone()
        batch.x = x_masked

        h = self.encoder(batch, return_nodes=True)  # [N, hidden] node embeddings (masked x)
        recon = self.decoder(h)  # [N, in_atom_dim]
        # reconstruct ORIGINAL (pre-mask) features at masked nodes
        loss = F.mse_loss(recon[masked_idx], x_orig[masked_idx])
        return loss, recon, masked_idx


def build_pretrain_graphs(max_mols=12000):
    csvs = [
        REPO / "model-training" / "data" / "raw" / "bbbp_clean.csv",
        REPO / "model-training" / "data" / "raw" / "clintox_clean.csv",
        REPO / "model-training" / "data" / "raw" / "tox21_clean.csv",
        REPO / "model-training" / "data" / "raw" / "bace_clean.csv",
    ]
    graphs = []
    import pandas as pd
    for c in csvs:
        if not c.exists():
            continue
        df = pd.read_csv(c).dropna(subset=["smiles"])
        for smi in df["smiles"].tolist():
            if len(graphs) >= max_mols:
                break
            g = featurize_mol(smi)
            if g is not None:
                graphs.append(g)
    return graphs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out", default="checkpoints/graphmae_encoder.pt")
    ap.add_argument("--max_mols", type=int, default=12000)
    args = ap.parse_args()

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    graphs = build_pretrain_graphs(args.max_mols)
    print(f"[pretrain] built {len(graphs)} real molecule graphs for MAE")
    loader = DataLoader(graphs, batch_size=args.batch_size, shuffle=True)

    model = GraphMAE().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-5)

    for ep in range(1, args.epochs + 1):
        model.train()
        tot = 0.0
        nb = 0
        for batch in loader:
            batch = batch.to(device)
            loss, _, _ = model(batch)
            opt.zero_grad()
            loss.backward()
            opt.step()
            tot += loss.item()
            nb += 1
        print(f"Epoch {ep}/{args.epochs} mae_loss={tot/nb:.4f}")

    # save ONLY the encoder (RealGraphBranch) state for downstream fine-tuning
    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.encoder.state_dict(),
                "in_atom_dim": 17, "config": "graphmae_pretrained"}, out)
    print(f"Saved pretrained encoder -> {out}")


if __name__ == "__main__":
    main()
