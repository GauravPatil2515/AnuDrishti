#!/usr/bin/env python3
"""
Real Faithfulness Validation on v2 Graph-Branch Predictions
============================================================

Replaces the faked "MockV2Model" faithfulness_v2_validation.json with a GENUINE
run of the v1 FaithfulnessValidator on the real v2 RealGraphBranch predictions.

Pipeline:
  1. Load trained RealGraphBranch + head (checkpoints/real_graph_bbbp.pt).
  2. Build RealGraphFaithfulModel: exposes the interface FaithfulnessValidator
     expects (_predict_smiles via the real GNN on real atom+bond graphs).
  3. For each molecule, derive model-derived per-atom importance via input
     gradients (real, not fake attention) and use the v1 SubstructureMapper to
     produce chemically-grounded explanations (SMARTS + atom_indices).
  4. Run FaithfulnessValidator (causal consistency via real CounterfactualGenerator,
     grounding vs model importance). Report F = sqrt(S_causal * S_grounding).

All numbers are REAL (actual GNN predictions + real RDKit counterfactuals).
Saves benchmark_results/faithfulness_v2_real.json stamped with commit/seed/hardware.
"""
import json
import sys
import subprocess
from pathlib import Path

import torch
import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent.parent  # repo root
sys.path.insert(0, str(REPO / "v2-foundation-arch" / "architecture_design"))
sys.path.insert(0, str(REPO / "v2-foundation-arch"))
sys.path.insert(0, str(REPO / "backend" / "models"))    # v1 faithfulness engine
sys.path.insert(0, str(REPO / "backend" / "utils"))      # substructure/counterfactual utils

from real_graph_branch import RealGraphBranch, featurize_mol  # noqa: E402
from torch_geometric.data import Batch  # noqa: E402

from faithfulness_validator import FaithfulnessValidator  # noqa: E402
from substructure_mapper import SubstructureMapper  # noqa: E402
from counterfactual_generator import CounterfactualGenerator  # noqa: E402
from rdkit import Chem  # noqa: E402

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class RealGraphFaithfulModel:
    """Wraps the trained RealGraphBranch so FaithfulnessValidator can predict."""

    def __init__(self, branch, head, device):
        self.branch = branch.to(device).eval()
        self.head = head.to(device).eval()
        self.device = device

    @torch.no_grad()
    def predict_smiles(self, smiles: str) -> float:
        """Return max toxicity probability (0-1) for a SMILES, matching the
        validator's expectation (it internally calls model(data, ...))."""
        g = featurize_mol(smiles)
        if g is None:
            return None
        g = g.to(self.device)
        emb = self.branch(g)
        logits = self.head(emb)
        return float(torch.sigmoid(logits).max().item())

    # FaithfulnessValidator internally calls self.model(data, return_attention=False)
    # where `data` is its own v1-format PyG Data. We override _smiles_to_data in the
    # validator subclass, so here we just need a callable that takes a real-graph
    # Data and returns logits. Provide a compatible forward.
    @torch.no_grad()
    def __call__(self, data, return_attention=False):
        data = data.to(self.device)
        emb = self.branch(data)
        logits = self.head(emb)
        if return_attention:
            return logits, None
        return logits

    # FaithfulnessValidator calls model.eval() / model.train() around prediction.
    def eval(self):
        self.branch.eval(); self.head.eval(); return self

    def train(self, mode=True):
        self.branch.train(mode); self.head.train(mode); return self


def atom_importance_via_grad(model: RealGraphFaithfulModel, smiles: str):
    """Real per-atom importance: gradient of max-prob prediction w.r.t. atom
    features, aggregated per atom. Returns numpy array length = n_atoms (RDKit,
    no Hs to match substructure atom indices)."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    n_atoms = mol.GetNumAtoms()
    g = featurize_mol(smiles)
    if g is None:
        return None
    g = g.to(model.device)
    g.x.requires_grad_(True)
    emb = model.branch(g)
    logits = model.head(emb)
    score = logits.max(dim=1).values.sum()
    model.branch.zero_grad()
    score.backward()
    grad = g.x.grad  # [n_atoms_with_H, feat]
    # aggregate gradient magnitude per atom (original atom index = position)
    imp = grad.abs().sum(dim=1).detach().cpu().numpy()
    # featurize_mol added Hs; map back: molecule built with AddHs, so atom order
    # in g matches mol-with-Hs. SubstructureMapper uses mol WITH Hs too, so indices
    # align directly.
    if len(imp) != n_atoms:
        # featurize added explicit Hs; take first n_atoms (heavy atoms first in RDKit AddHs)
        imp = imp[:n_atoms]
    # normalize to a pseudo-attention distribution (sum 1) for the grounding test
    if imp.sum() > 0:
        imp = imp / imp.sum()
    return imp


class RealFaithfulnessValidator(FaithfulnessValidator):
    """FaithfulnessValidator that builds REAL atom+bond graphs for the v2 branch."""

    def _smiles_to_data(self, smiles: str):
        return featurize_mol(smiles)  # real Data with float x [n,17], edge_attr [e,7]

    def _predict_smiles(self, smiles: str):
        """Robust wrapper: returns None on invalid/missing graphs so the engine
        excludes that molecule rather than crashing."""
        try:
            g = featurize_mol(smiles)
            if g is None:
                return None
            self.model.eval()
            data = g.to(self.device)
            with torch.no_grad():
                predictions = self.model(data, return_attention=False)
                probs = torch.sigmoid(predictions)
            return float(torch.max(probs).item())
        except Exception:
            return None


def main():
    # --- load trained branch + head ---
    ckpt = torch.load(f"{REPO}/checkpoints/real_graph_bbbp.pt", weights_only=True)
    branch = RealGraphBranch(out_dim=256)
    head = torch.nn.Linear(256, 1)
    branch.load_state_dict(ckpt["model"]); head.load_state_dict(ckpt["head"])
    model = RealGraphFaithfulModel(branch, head, DEVICE)

    mapper = SubstructureMapper(include_functional_groups=True)
    cf_gen = CounterfactualGenerator()
    validator = RealFaithfulnessValidator(
        model=model, counterfactual_generator=cf_gen,
        faithfulness_threshold=0.6, causal_drop_threshold=0.1, attention_threshold=0.1,
    )

    # --- sample BBBP molecules that actually contain REMOVABLE toxicophores
    #     (nitro / halogen) so the causal test has genuinely testable claims ---
    import pandas as pd
    from rdkit import Chem
    df = pd.read_csv(REPO / "model-training" / "data" / "raw" / "bbbp_clean.csv")
    df = df.dropna(subset=["smiles"]).reset_index(drop=True)

    def has_removable(smi):
        m = Chem.MolFromSmiles(smi)
        if m is None:
            return False
        for pat in ("[N+](=O)[O-]", "[Cl,Br,I]"):
            if m.HasSubstructMatch(Chem.MolFromSmarts(pat)):
                return True
        return False

    removable = df[df["smiles"].map(has_removable)].reset_index(drop=True)
    sample = removable.sample(n=min(60, len(removable)), random_state=42).reset_index(drop=True)
    print(f"[info] molecules with removable toxicophores: {len(removable)}; sampling {len(sample)}")

    results = []
    n_with_claims = 0
    causal_scores, grounding_scores = [], []
    for _, row in sample.iterrows():
        smi = row["smiles"]
        prob = model.predict_smiles(smi)
        if prob is None:
            continue
        imp = atom_importance_via_grad(model, smi)
        if imp is None:
            continue
        explanation_dict = mapper.generate_explanation(smi, imp, prob)
        # SubstructureMapper stores the pattern under 'smarts'; FaithfulnessValidator
        # reads 'smarts_pattern'. Rename so the causal test can match counterfactuals.
        for tp in explanation_dict.get("identified_toxicophores", []):
            if "smarts" in tp and "smarts_pattern" not in tp:
                tp["smarts_pattern"] = tp["smarts"]
        tox = explanation_dict.get("identified_toxicophores", [])
        if not tox:
            # still record: nothing claimed -> n_claims=0 (excluded from F per engine)
            results.append({"smiles": smi, "n_claims": 0, "passed": None})
            continue
        n_with_claims += 1
        attn = imp  # grounding uses model-derived importance
        score = validator.validate(explanation_dict, smi, prob, attn, run_counterfactual_test=True)
        d = score.to_dict()
        d["smiles"] = smi
        d["n_claims"] = score.n_claims
        results.append(d)
        causal_scores.append(score.causal_consistency.score)
        grounding_scores.append(score.grounding.score)

    # Aggregate over molecules that had >=1 falsifiable claim
    n = len(causal_scores)
    mean_causal = float(np.mean(causal_scores)) if n else None
    mean_grounding = float(np.mean(grounding_scores)) if n else None
    mean_F = float(np.sqrt(mean_causal * mean_grounding)) if (n and mean_causal is not None) else None

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO).decode().strip()
    except Exception:
        commit = "unknown"
    hw = torch.cuda.get_device_name(0) if DEVICE == "cuda" else "CPU"

    out = {
        "model": "RealGraphBranch (v2 GINEConv) + v1 FaithfulnessValidator (REAL, not MockV2Model)",
        "dataset": "bbbp",
        "n_evaluated": len(results),
        "n_with_claims": n_with_claims,
        "mean_causal_consistency": round(mean_causal, 4) if mean_causal is not None else None,
        "mean_grounding": round(mean_grounding, 4) if mean_grounding is not None else None,
        "mean_F": round(mean_F, 4) if mean_F is not None else None,
        "note": ("F=sqrt(S_causal*S_grounding) over molecules with >=1 falsifiable claim. "
                 "Replaces the faked faithfulness_v2_validation.json (MockV2Model)."),
        "git_commit": commit,
        "hardware": hw,
        "per_molecule": results,
    }
    out_path = REPO / "benchmark_results" / "faithfulness_v2_real.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Evaluated {len(results)} molecules; {n_with_claims} with >=1 claim.")
    print(f"MEAN  causal={mean_causal:.4f}  grounding={mean_grounding:.4f}  F={mean_F:.4f}")
    print(f"Saved -> {out_path}")


if __name__ == "__main__":
    main()
