"""
Shared constants and helpers for the v2-foundation-arch real benchmark pipeline.

All runs must stamp their outputs with git_commit, timestamp, seed, and hardware
so that NO metric is ever reported without provenance.
"""
import os
import subprocess
import json
from datetime import datetime, timezone

REPO_ROOT = "/home/gaurav/Desktop/gaurav code /Paper/denovo/Faithful-LLM-Augmented-Explainability-for-Graph-Neural-Network-Based-Molecular-Toxicity-Prediction"
SCRIPTS_DIR = os.path.join(REPO_ROOT, "v2-foundation-arch", "scripts")
DATA_RAW = os.path.join(REPO_ROOT, "model-training", "data", "raw")
DATA_PROCESSED = os.path.join(REPO_ROOT, "model-training", "data", "processed")
BENCHMARK_DIR = os.path.join(REPO_ROOT, "benchmark_results")
CHECKPOINT_DIR = os.path.join(REPO_ROOT, "model-training", "checkpoints")
VENV_PYTHON = os.path.join(REPO_ROOT, ".venv", "bin", "python")

SEED = 42
HARDWARE = "RTX 3050 6GB (NVIDIA GeForce RTX 3050 Laptop GPU, 6144 MiB)"


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", REPO_ROOT, "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stamp(extra: dict = None) -> dict:
    """Standard metadata block attached to every result file."""
    base = {
        "git_commit": git_commit(),
        "timestamp": now_iso(),
        "seed": SEED,
        "hardware": HARDWARE,
        "venv_python": VENV_PYTHON,
    }
    if extra:
        base.update(extra)
    return base


def save_json(path: str, obj: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
    print(f"[saved] {path}")


def ensure_dirs():
    for d in (DATA_RAW, DATA_PROCESSED, BENCHMARK_DIR, CHECKPOINT_DIR):
        os.makedirs(d, exist_ok=True)
