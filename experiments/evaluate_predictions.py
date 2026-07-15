#!/usr/bin/env python3
"""
Lock the predictive-performance numbers (P1).

Recomputes TEST-set ROC-AUC for the saved ADMET models by reusing each dataset's
own training module (same model class, same featurization) and evaluating on the
dataset's fixed test.csv split -- so the numbers are trustworthy (no split
guessing, no data leakage). Writes results/prediction_metrics.json.

This exists because reported SOTA claims (e.g. "ClinTox 0.8349") did not match the
actual saved-model test performance; run this to get the ground truth before
putting any number in the paper.

Usage:
    python experiments/evaluate_predictions.py
"""

import sys
import json
from pathlib import Path

import torch

PROJECT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT / "training"))

# Data lives under data_packages/ (the MODELS/ path in the training scripts is stale).
DATASETS = {
    "bbbp": {
        "module": "train_bbbp",
        "loader": "load_bbbp_data",
        "num_tasks": 1,
        "data_dir": PROJECT / "data_packages" / "bbbp_model_full_package" / "data" / "bbbp",
        "weights": PROJECT / "results" / "trained_models" / "bbbp_gin_model.pth",
        "sota_ref": "ChemProp ~0.90 (MoleculeNet, scaffold)",
    },
    "clintox": {
        "module": "train_clintox",
        "loader": "load_clintox_data",
        "num_tasks": 2,
        "data_dir": PROJECT / "data_packages" / "clintox_model_package" / "data" / "clintox",
        "weights": PROJECT / "results" / "trained_models" / "clintox_gin_model.pth",
        "sota_ref": "ChemProp ~0.88-0.90 (MoleculeNet)",
    },
}


def eval_one(name, cfg, device):
    from torch_geometric.loader import DataLoader
    mod = __import__(cfg["module"])
    load_fn = getattr(mod, cfg["loader"])
    AttentionGINet = getattr(mod, "AttentionGINet")
    evaluate = getattr(mod, "evaluate")

    if not cfg["data_dir"].exists():
        return {"error": f"data_dir missing: {cfg['data_dir']}"}
    if not cfg["weights"].exists():
        return {"error": f"weights missing: {cfg['weights']}"}

    _, _, test_data = load_fn(cfg["data_dir"])
    test_loader = DataLoader(test_data, batch_size=32)

    model = AttentionGINet(num_tasks=cfg["num_tasks"]).to(device)
    state = torch.load(cfg["weights"], map_location=device)
    model.load_state_dict(state.get("model_state_dict", state) if isinstance(state, dict) else state)
    model.eval()

    out = evaluate(model, test_loader, device)
    # evaluate() may return (avg_roc, per_task) or a scalar.
    if isinstance(out, tuple):
        avg_roc, per_task = out[0], out[1]
        per_task = [float(x) for x in per_task] if hasattr(per_task, "__iter__") else None
    else:
        avg_roc, per_task = out, None
    return {
        "test_roc_auc": round(float(avg_roc), 4),
        "per_task": per_task,
        "n_test": len(test_data),
        "sota_ref": cfg["sota_ref"],
    }


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}\n")
    results = {}
    for name, cfg in DATASETS.items():
        print(f"=== {name} ===")
        try:
            results[name] = eval_one(name, cfg, device)
        except Exception as e:
            results[name] = {"error": f"{type(e).__name__}: {e}"}
        print(json.dumps(results[name], indent=2), "\n")

    # Tox21 test AUC is already logged from training (no fixed test.csv; uses the
    # seeded wrapper split). Surface it here for a single consolidated table.
    tox21_res = PROJECT / "results" / "trained_models" / "test_results.json"
    if tox21_res.exists():
        try:
            tj = json.loads(tox21_res.read_text())
            results["tox21"] = {
                "test_roc_auc": round(float(tj["test_metrics"]["mean_roc_auc"]), 4),
                "source": "logged at training (seeded random split)",
                "sota_ref": "ChemProp ~0.845 (MoleculeNet)",
            }
        except Exception as e:
            results["tox21"] = {"error": str(e)}

    out_path = PROJECT / "results" / "prediction_metrics.json"
    out_path.write_text(json.dumps(results, indent=2))
    print("=" * 60)
    print("SUMMARY (test ROC-AUC):")
    for k, v in results.items():
        val = v.get("test_roc_auc", v.get("error"))
        print(f"  {k:10s}: {val}   [{v.get('sota_ref', '')}]")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
