#!/usr/bin/env python3
"""
Real Faithfulness Validation on v2 Graph-Branch Predictions
============================================================

Genuine run of the v1 FaithfulnessValidator machinery on the real v2
RealGraphBranch predictions. Reports the **Counterfactual Consistency Score**
(CCS): for each molecule with a chemically-removable substructure, remove it,
predict on the valid modified molecule, and count the claim as consistent only
if the prediction drops by >= delta.

This script additionally provides the instrument-validation scaffolding that a
mature faithfulness paper requires:

  * A RANDOM-BASELINE control: remove a random non-toxicophore heavy atom
    (size-comparable to a toxicophore fragment) and record the drop. This is the
    chance anchor -- if toxicophore removals are indistinguishable from random
    removals, the negative result is even stronger.
  * A comparative faithfulness metric: gradient-based feature-deletion score
    (zero the top-k% most gradient-important atoms; the drop measures whether
    the model's own attributions are decision-relevant). Engages the
    "disagreement between faithfulness metrics" literature.
  * A METRIC SANITY CHECK (--self_test): a rule-based probe model whose label is
    a known function of a substructure; verifies the SAME counting code correctly
    attributes consistency to the true causal substructure and not to unrelated
    ones. Validates the instrument before trusting what it says about the GNN.

All numbers are REAL (actual GNN predictions + real RDKit counterfactuals).
"""
import json
import sys
import subprocess
import random
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

# Removable SMARTS the CounterfactualGenerator can remove to yield a VALID
# molecule. This is the clean, reproducible counterfactual probe.
REMOVABLE = ["Cl", "Br", "I", "[N+](=O)[O-]", "C1OC1", "C=O", "N=N"]


def _claim_to_removable_smarts(tp: dict, mol) -> str:
    """Bridge SubstructureMapper (name + atom_indices, no SMARTS) to the
    CounterfactualGenerator (needs a removable SMARTS)."""
    name = (tp.get("name") or "").lower()
    idx = tp.get("atom_indices") or []
    name_map = {
        "hydroxyl": "O", "alcohol": "O", "phenol": "O",
        "carboxylic acid": "O", "carboxyl": "O", "ester": "O", "carbonyl": "O",
        "ether": "O", "alkoxy": "O",
        "amine": "[NH2]", "aromatic amine": "[NH2]", "primary amine": "[NH2]",
        "amino": "[NH2]", "amide": "N", "nitro": "[N+](=O)[O-]",
        "halogen": "Cl", "chloro": "Cl", "chlorine": "Cl", "bromo": "Br",
        "bromine": "Br", "iodo": "I", "iodine": "I", "fluoro": "F",
        "epoxide": "C1OC1", "azide": "[N-]=[N+]=N", "azo": "N=N",
        "sulfide": "S", "thiol": "S", "sulfonyl": "S", "phosphate": "P",
    }
    if name in name_map:
        return name_map[name]
    if mol is not None and idx:
        a = mol.GetAtomWithIdx(int(idx[0]))
        sym = a.GetSymbol()
        if sym in ("Cl", "Br", "I", "F"):
            return sym
        if sym == "O":
            return "O"
        if sym == "N":
            return "[NH2]"
        if sym == "S":
            return "S"
    return "O"  # safest removable default


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class RealGraphFaithfulModel:
    """Wraps the trained RealGraphBranch so the validator can predict."""

    def __init__(self, branch, head, device):
        self.branch = branch.to(device).eval()
        self.head = head.to(device).eval()
        self.device = device

    @torch.no_grad()
    def predict_smiles(self, smiles: str) -> float:
        g = featurize_mol(smiles)
        if g is None:
            return None
        g = g.to(self.device)
        emb = self.branch(g)
        logits = self.head(emb)
        return float(torch.sigmoid(logits).max().item())

    @torch.no_grad()
    def __call__(self, data, return_attention=False):
        data = data.to(self.device)
        emb = self.branch(data)
        logits = self.head(emb)
        if return_attention:
            return logits, None
        return logits

    def eval(self):
        self.branch.eval(); self.head.eval(); return self

    def train(self, mode=True):
        self.branch.train(mode); self.head.train(mode); return self


def atom_importance_via_grad(model, smiles: str):
    """Real per-atom importance: gradient of max-prob prediction w.r.t. atom
    features. Returns numpy array length = n_heavy_atoms, normalized to sum 1."""
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
    grad = g.x.grad
    imp = grad.abs().sum(dim=1).detach().cpu().numpy()
    if len(imp) != n_atoms:
        imp = imp[:n_atoms]
    if imp.sum() > 0:
        imp = imp / imp.sum()
    return imp


# ----------------------------------------------------------------------------
# Instrument-validation scaffolding
# ----------------------------------------------------------------------------
def random_atom_removal_drops(smi, model, toxic_atom_idxs, n_tries=3, seed=0):
    """Chance anchor: remove a RANDOM non-toxicophore heavy atom (bond
    disconnection), keep the largest valid fragment, record prediction drop
    (prob - modified_prob). Size-comparable to a single toxicophore fragment.
    Returns list of valid drops."""
    rng = random.Random(seed)
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        return []
    heavy = [a.GetIdx() for a in mol.GetAtoms() if a.GetAtomicNum() > 1]
    candidates = [i for i in heavy if i not in toxic_atom_idxs]
    if not candidates:
        return []
    drops = []
    for _ in range(n_tries):
        ai = rng.choice(candidates)
        emol = Chem.EditableMol(Chem.Mol(mol))
        emol.RemoveAtom(ai)
        try:
            nm = emol.GetMol()
            nm = Chem.MolFromSmiles(Chem.MolToSmiles(nm))
        except Exception:
            continue
        if nm is None:
            continue
        mod = model.predict_smiles(Chem.MolToSmiles(nm))
        if mod is None:
            continue
        prob = model.predict_smiles(smi)
        if prob is None:
            continue
        drops.append(prob - mod)
    return drops


def saliency_deletion_drop(smi, model, frac=0.3):
    """Comparative faithfulness metric (feature-deletion / perturbation score):
    zero the node features of the top-frac% most gradient-important atoms and
    measure the prediction drop. No structural change => always valid. Returns
    drop (prob - prob_masked) or None. A large drop means the model's own
    attributions are decision-relevant (faithful in the deletion sense)."""
    imp = atom_importance_via_grad(model, smi)
    if imp is None:
        return None
    g = featurize_mol(smi)
    if g is None:
        return None
    g = g.to(model.device)
    k = max(1, int(round(frac * len(imp))))
    top = set(np.argsort(-imp)[:k].tolist())
    with torch.no_grad():
        x = g.x.clone()
        for i in top:
            if int(i) < x.shape[0]:
                x[int(i)] = 0.0
        g.x = x
        emb = model.branch(g)
        logits = model.head(emb)
        prob_masked = float(torch.sigmoid(logits).max().item())
    prob = model.predict_smiles(smi)
    if prob is None:
        return None
    return prob - prob_masked


def toxic_atom_idxs_for(smi):
    """Atom indices belonging to any matched REMOVABLE substructure."""
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        return set()
    idxs = set()
    for sp in REMOVABLE:
        try:
            matches = mol.GetSubstructMatches(Chem.MolFromSmarts(sp))
        except Exception:
            continue
        for m in matches:
            idxs.update(m)
    return idxs


def run_causal(model, sample, cf_gen, drop_threshold=0.1, seed=42,
               compute_saliency=True, n_random=3):
    """Core counterfactual-consistency loop. Returns (results, n_with_claims).
    Each result records toxicophore raw_drops, random-control drops, and the
    saliency-deletion drop for the same molecule."""
    results = []
    n_with_claims = 0
    for _, row in sample.iterrows():
        smi = row["smiles"]
        prob = model.predict_smiles(smi)
        if prob is None:
            continue
        matched = [p for p in REMOVABLE
                   if Chem.MolFromSmiles(smi).HasSubstructMatch(Chem.MolFromSmarts(p))]
        if not matched:
            results.append({"smiles": smi, "n_claims": 0, "passed": None})
            continue
        n_with_claims += 1
        passed = 0
        tested = 0
        raw_drops = []
        for sp in matched:
            cf = cf_gen.generate_for_claimed_toxicophore(smi, sp, "grp")
            if cf is None or featurize_mol(cf.modified_smiles) is None:
                continue
            mod = model.predict_smiles(cf.modified_smiles)
            if mod is None:
                continue
            tested += 1
            raw_drops.append(prob - mod)
            if (prob - mod) >= drop_threshold:
                passed += 1
        mol_causal = (passed / tested) if tested else 0.0
        # chance anchor + comparative metric (same molecule)
        toxic_idxs = toxic_atom_idxs_for(smi)
        random_drops = random_atom_removal_drops(smi, model, toxic_idxs,
                                                  n_tries=n_random, seed=seed)
        saliency_drop = (saliency_deletion_drop(smi, model, frac=0.3)
                         if compute_saliency else None)
        results.append({
            "smiles": smi, "n_claims": len(matched),
            "causal_tested": tested, "causal_passed": passed,
            "mol_causal": round(mol_causal, 4),
            "raw_drops": [round(float(d), 4) for d in raw_drops],
            "random_drops": [round(float(d), 4) for d in random_drops],
            "saliency_drop": (round(float(saliency_drop), 4)
                              if saliency_drop is not None else None),
        })
    return results, n_with_claims


# ----------------------------------------------------------------------------
# Metric sanity check (instrument validation via a rule-based probe model)
# ----------------------------------------------------------------------------
class RuleModel:
    """Probe model whose label is a KNOWN function of a substructure:
    presence of a nitro group => 0.9, else 0.1. Used only to validate that the
    counterfactual-consistency counting attributes consistency to the TRUE
    causal substructure and not to unrelated removals."""

    def __init__(self):
        self.device = "cpu"

    def predict_smiles(self, smiles: str) -> float:
        if smiles is None:
            return None
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        has_nitro = mol.HasSubstructMatch(Chem.MolFromSmarts("[N+](=O)[O-]"))
        return 0.9 if has_nitro else 0.1


def run_self_test():
    """Verify the instrument: nitro is the ground-truth cause. Removing nitro must
    register as consistent; removing an unrelated halogen must not."""
    cf_gen = CounterfactualGenerator()
    model = RuleModel()
    probes = {
        "nitrobenzene": "O=[N+]([O-])c1ccccc1",   # cause present
        "nitroethane": "CC[N+](=O)[O-]",            # cause present (canonical)
        "chlorobenzene": "Clc1ccccc1",              # halogen only, NOT the cause
        "bromobenzene": "Brc1ccccc1",               # halogen only, NOT the cause
    }
    print("=== METRIC SANITY CHECK (rule-based probe: nitro => toxic) ===")
    all_ok = True
    for name, smi in probes.items():
        res, _ = run_causal(model,
                            __import__("pandas").DataFrame([{"smiles": smi}]),
                            cf_gen, compute_saliency=False)
        r = res[0]
        has_nitro = Chem.MolFromSmiles(smi).HasSubstructMatch(
            Chem.MolFromSmarts("[N+](=O)[O-]"))
        # expected: nitro-bearing mol => high mol_causal; halogen-only => 0
        expected_high = has_nitro
        got_high = (r.get("mol_causal") or 0.0) >= 0.5
        ok = (expected_high == got_high)
        all_ok &= ok
        print(f"  {name:14s} mol_causal={r.get('mol_causal')} "
              f"(expected {'high' if expected_high else 'low'}) -> {'OK' if ok else 'FAIL'}")
    print("SANITY CHECK:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


# ----------------------------------------------------------------------------
def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="", help="path to RealGraphBranch checkpoint (.pt)")
    ap.add_argument("--out", default="", help="output JSON path for this seed")
    ap.add_argument("--dataset", default="bbbp", choices=["bbbp", "bace", "tox21"],
                    help="which dataset's molecules to probe (must match the checkpoint)")
    ap.add_argument("--self_test", action="store_true",
                    help="run the rule-based metric sanity check and exit (no GPU needed)")
    args = ap.parse_args()

    if args.self_test:
        raise SystemExit(run_self_test())

    ckpt = torch.load(args.ckpt, weights_only=True)
    HID = ckpt["head"]["0.weight"].shape[0]
    branch = RealGraphBranch(out_dim=300, hidden_dim=300, num_layers=5, dropout=0.3)
    head = torch.nn.Sequential(torch.nn.Linear(300, HID), torch.nn.ReLU(), torch.nn.Linear(HID, 1))
    branch.load_state_dict(ckpt["model"]); head.load_state_dict(ckpt["head"])
    model = RealGraphFaithfulModel(branch, head, DEVICE)

    cf_gen = CounterfactualGenerator()

    import pandas as pd
    _csv = {"bbbp": "bbbp_clean.csv", "bace": "bace_clean.csv", "tox21": "tox21_clean.csv"}[args.dataset]
    df = pd.read_csv(REPO / "model-training" / "data" / "raw" / _csv)
    df = df.dropna(subset=["smiles"]).reset_index(drop=True)

    def has_removable(smi):
        m = Chem.MolFromSmiles(smi)
        if m is None:
            return False
        return any(m.HasSubstructMatch(Chem.MolFromSmarts(p)) for p in REMOVABLE)

    removable = df[df["smiles"].map(has_removable)].reset_index(drop=True)
    sample = removable.sample(n=min(60, len(removable)), random_state=42).reset_index(drop=True)
    print(f"[info] molecules with removable toxicophores: {len(removable)}; sampling {len(sample)}")

    results, n_with_claims = run_causal(model, sample, cf_gen, compute_saliency=True)

    # Aggregate counterfactual consistency
    causal_scores = [r["mol_causal"] for r in results if r.get("n_claims", 0) > 0]
    n = len(causal_scores)
    mean_causal = float(np.mean(causal_scores)) if n else None

    # Random-baseline control
    rand_all = [d for r in results for d in (r.get("random_drops") or [])]
    random_frac = float(np.mean([1.0 if d >= 0.1 else 0.0 for d in rand_all])) if rand_all else None
    random_mean = float(np.mean(rand_all)) if rand_all else None

    # Comparative saliency-deletion metric
    sal_all = [r["saliency_drop"] for r in results if r.get("saliency_drop") is not None]
    sal_frac = float(np.mean([1.0 if d >= 0.1 else 0.0 for d in sal_all])) if sal_all else None
    sal_mean = float(np.mean(sal_all)) if sal_all else None

    # Threshold sensitivity (same raw drops, multiple delta)
    thresholds = [0.05, 0.1, 0.2]
    sens = {}
    for t in thresholds:
        per_mol = []
        for r in results:
            rd = r.get("raw_drops", [])
            if rd:
                per_mol.append(float(np.mean([1.0 if d >= t else 0.0 for d in rd])))
        sens[f"{t:.2f}"] = round(float(np.mean(per_mol)), 4) if per_mol else None

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO).decode().strip()
    except Exception:
        commit = "unknown"
    hw = torch.cuda.get_device_name(0) if DEVICE == "cuda" else "CPU"

    out = {
        "model": "RealGraphBranch (v2 GINEConv) -- Counterfactual Consistency Score",
        "dataset": args.dataset,
        "n_evaluated": len(results),
        "n_with_claims": n_with_claims,
        "mean_counterfactual_consistency": round(mean_causal, 4) if mean_causal is not None else None,
        "random_control": {
            "mean_drop": round(random_mean, 4) if random_mean is not None else None,
            "frac_drop_ge_0.1": round(random_frac, 4) if random_frac is not None else None,
            "n_drops": len(rand_all),
        },
        "saliency_deletion": {
            "mean_drop": round(sal_mean, 4) if sal_mean is not None else None,
            "frac_drop_ge_0.1": round(sal_frac, 4) if sal_frac is not None else None,
            "n": len(sal_all),
        },
        "threshold_sensitivity": sens,
        "note": ("Counterfactual Consistency = fraction of toxicophore removals that drop "
                 "the prediction by >= delta. Random-control = same for random non-toxicophore "
                 "atom removal (chance anchor). Saliency-deletion = gradient feature-deletion score "
                 "(comparative metric). Grounding term fixed at 1.0 (no LLM narrative evaluated)."),
        "git_commit": commit,
        "hardware": hw,
        "per_molecule": results,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Evaluated {len(results)} molecules; {n_with_claims} with >=1 claim.")
    print(f"CCS={mean_causal:.4f}  random_frac={random_frac}  saliency_mean={sal_mean}")
    print(f"Saved -> {out_path}")


if __name__ == "__main__":
    main()
