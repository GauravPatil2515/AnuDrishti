#!/usr/bin/env python3
"""Task 5 launcher: 5-seed evaluation (seeds 42-46) for bbbp/bace/tox21,
regularized config. Runs in waves of 3 concurrent jobs to stay within 6GB VRAM
and ~2GB free RAM. Writes per-seed JSONs (already handled by train_real_graph)."""
import subprocess, sys, time, os
from pathlib import Path

REPO = Path("/home/gaurav/Desktop/gaurav code /Paper/denovo/Faithful-LLM-Augmented-Explainability-for-Graph-Neural-Network-Based-Molecular-Toxicity-Prediction")
VENV = REPO / ".venv" / "bin" / "python"
PY = str(REPO / "v2-foundation-arch" / "experiments" / "training" / "train_real_graph.py")

CFG = ["--epochs", "200", "--batch_size", "32", "--lr", "5e-4", "--hidden_dim", "300",
       "--num_layers", "5", "--head_mlp", "--schedule", "cosine", "--patience", "25",
       "--dropout", "0.4", "--weight_decay", "1e-4", "--device", "cuda"]

def launch(ds, seed):
    out = REPO / f"/tmp/v5_{ds}_{seed}.log"
    cmd = [str(VENV), PY, "--dataset", ds, "--seed", str(seed), "--tag", f"_v5_s{seed}"] + CFG
    p = subprocess.Popen(cmd, cwd=str(REPO), stdout=open(str(out), "w"), stderr=subprocess.STDOUT)
    return p

datasets = ["bbbp", "bace", "tox21"]
seeds = [42, 43, 44, 45, 46]

# wave = up to 3 concurrent (one per dataset) to bound memory
for s in seeds:
    procs = []
    for ds in datasets:
        procs.append(launch(ds, s))
        print(f"[launch] seed {s} {ds}")
    # wait for this wave (all 3 datasets for this seed) to finish
    for p in procs:
        p.wait()
    print(f"[done] seed {s} wave complete")

print("ALL TASK5 RUNS COMPLETE")
