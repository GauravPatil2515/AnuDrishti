#!/usr/bin/env python3
"""
Optuna hyperparameter sweep for ADMET models (P3).

Motivation: the saved ClinTox model scores ~0.62 test ROC-AUC because it was
trained with a plain, unweighted BCE loss despite severe class imbalance
(CT_TOX ~7% positive). This sweep adds Focal Loss with per-task positive
weighting and Bayesian-optimizes the key hyperparameters, then retrains the best
configuration and reports test ROC-AUC on the fixed test.csv split.

Reuses each dataset's own training module (loader, model class, evaluate) so the
featurization and metric are identical to the original pipeline.

Usage:
    python experiments/hyperparam_sweep.py --dataset clintox --trials 30
    python experiments/hyperparam_sweep.py --dataset bbbp --trials 30
"""

import sys
import json
import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import optuna

PROJECT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT / "training"))

DATASETS = {
    "clintox": {
        "module": "train_clintox", "loader": "load_clintox_data", "num_tasks": 2,
        "data_dir": PROJECT / "data_packages" / "clintox_model_package" / "data" / "clintox",
    },
    "bbbp": {
        "module": "train_bbbp", "loader": "load_bbbp_data", "num_tasks": 1,
        "data_dir": PROJECT / "data_packages" / "bbbp_model_full_package" / "data" / "bbbp",
    },
}


class FocalLoss(nn.Module):
    """Multi-label focal loss with optional per-task positive weighting."""
    def __init__(self, gamma=2.0, pos_weight=None):
        super().__init__()
        self.gamma = gamma
        self.pos_weight = pos_weight

    def forward(self, logits, targets):
        bce = F.binary_cross_entropy_with_logits(
            logits, targets, reduction="none", pos_weight=self.pos_weight)
        p = torch.sigmoid(logits)
        p_t = p * targets + (1 - p) * (1 - targets)
        return (((1 - p_t) ** self.gamma) * bce).mean()


def compute_pos_weight(train_data, num_tasks, device):
    """Per-task neg/pos ratio from the training labels."""
    ys = torch.stack([d.y.view(-1) for d in train_data]).float()  # [N, num_tasks]
    pos = ys.sum(0).clamp(min=1.0)
    neg = (ys.shape[0] - pos).clamp(min=1.0)
    return (neg / pos).to(device)


def run_dataset(name, n_trials, final_epochs):
    from torch_geometric.loader import DataLoader
    cfg = DATASETS[name]
    mod = __import__(cfg["module"])
    load_fn = getattr(mod, cfg["loader"])
    AttentionGINet = getattr(mod, "AttentionGINet")
    train_epoch = getattr(mod, "train_epoch")
    evaluate = getattr(mod, "evaluate")
    num_tasks = cfg["num_tasks"]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[{name}] device={device}")
    train_data, valid_data, test_data = load_fn(cfg["data_dir"])
    base_pos_weight = compute_pos_weight(train_data, num_tasks, device)
    print(f"[{name}] base per-task pos_weight (neg/pos): {base_pos_weight.tolist()}")

    def make_loaders(batch_size):
        return (DataLoader(train_data, batch_size=batch_size, shuffle=True),
                DataLoader(valid_data, batch_size=batch_size),
                DataLoader(test_data, batch_size=batch_size))

    def fit(params, epochs, save_to=None):
        torch.manual_seed(42); np.random.seed(42)
        tr, va, te = make_loaders(params["batch_size"])
        model = AttentionGINet(num_tasks=num_tasks, emb_dim=300,
                               drop_ratio=params["dropout"]).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=params["lr"],
                               weight_decay=params["weight_decay"])
        pw = base_pos_weight * params["pos_weight_scale"]
        crit = FocalLoss(gamma=params["gamma"], pos_weight=pw)
        best_val, best_state, patience = 0.0, None, 0
        for _ in range(epochs):
            train_epoch(model, tr, opt, crit, device, num_tasks) if _accepts_tasks(train_epoch) \
                else train_epoch(model, tr, opt, crit, device)
            val = _avg(evaluate(model, va, device))
            if val > best_val:
                best_val, best_state, patience = val, {k: v.cpu().clone() for k, v in model.state_dict().items()}, 0
            else:
                patience += 1
                if patience >= 15:
                    break
        if best_state:
            model.load_state_dict(best_state)
        test_roc = _avg(evaluate(model, te, device))
        if save_to and best_state:
            torch.save(model.state_dict(), save_to)
        return best_val, test_roc, model

    def objective(trial):
        params = {
            "lr": trial.suggest_float("lr", 1e-5, 1e-3, log=True),
            "weight_decay": trial.suggest_float("weight_decay", 1e-6, 1e-3, log=True),
            "dropout": trial.suggest_float("dropout", 0.1, 0.5),
            "gamma": trial.suggest_float("gamma", 0.0, 3.0),
            "pos_weight_scale": trial.suggest_float("pos_weight_scale", 0.5, 3.0),
            "batch_size": trial.suggest_categorical("batch_size", [16, 32, 64]),
        }
        best_val, _, _ = fit(params, epochs=60)
        return best_val

    study = optuna.create_study(direction="maximize",
                                sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    best = study.best_params
    print(f"[{name}] best val={study.best_value:.4f} params={best}")
    out_dir = PROJECT / "results" / "trained_models"
    out_dir.mkdir(parents=True, exist_ok=True)
    save_to = out_dir / f"{name}_gin_model_tuned.pth"
    best_val, test_roc, _ = fit(best, epochs=final_epochs, save_to=save_to)
    print(f"[{name}] FINAL retrain: val={best_val:.4f}  TEST ROC-AUC={test_roc:.4f}")

    result = {
        "dataset": name, "best_val_roc": round(best_val, 4),
        "test_roc_auc": round(test_roc, 4), "n_trials": n_trials,
        "best_params": best, "weights": str(save_to),
    }
    (PROJECT / "results" / f"hpo_{name}.json").write_text(json.dumps(result, indent=2))
    return result


def _avg(out):
    return float(out[0]) if isinstance(out, tuple) else float(out)


def _accepts_tasks(fn):
    import inspect
    return "num_tasks" in inspect.signature(fn).parameters


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=list(DATASETS), required=True)
    ap.add_argument("--trials", type=int, default=30)
    ap.add_argument("--final-epochs", type=int, default=120)
    args = ap.parse_args()
    res = run_dataset(args.dataset, args.trials, args.final_epochs)
    print("\n" + json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
