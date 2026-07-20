#!/usr/bin/env python3
"""
PHASE 1: Real MoleculeNet data acquisition.

Downloads TOX21, BBBP, ClinTox, SIDER, BACE CSVs from DeepChem's public S3 bucket
into model-training/data/raw/. No placeholders, no synthetic data. Verifies each
download yields a parseable CSV with a 'smiles' column and non-trivial row count.

DeepChem hosts these as .csv.gz; we stream-decompress and write plain CSV.
"""
import os
import gzip
import urllib.request
import csv
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_RAW, ensure_dirs

# (name, remote .csv.gz, expected minimum rows, label columns hint)
DATASETS = {
    "tox21": {
        "url": "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz",
        "min_rows": 1000,
    },
    "bbbp": {
        "url": "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/BBBP.csv",
        "min_rows": 1000,
        "gz": False,
    },
    "clintox": {
        "url": "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/clintox.csv.gz",
        "min_rows": 100,
    },
    "sider": {
        "url": "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/sider.csv.gz",
        "min_rows": 1000,
    },
    "bace": {
        # DeepChem's canonical BACE classification file ships as a descriptor CSV
        # with a 'mol' (SMILES) column and a 'Class' (0/1) label column. We
        # download it and project to (smiles, Class) to match the other datasets.
        "url": "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/bace.csv",
        "min_rows": 1000,
        "gz": False,
        "project": ("mol", "Class"),
    },
}


def _project_csv(path, smiles_col, label_col):
    """Extract (smiles, label) into a clean 2-column CSV, overwriting path."""
    tmp = path + ".tmp"
    with open(path, newline="") as fin, open(tmp, "w", newline="") as fout:
        reader = csv.reader(fin)
        header = next(reader)
        si, li = header.index(smiles_col), header.index(label_col)
        writer = csv.writer(fout)
        writer.writerow(["smiles", label_col])
        n = 0
        for row in reader:
            if not row or not row[si].strip():
                continue
            writer.writerow([row[si].strip(), row[li].strip()])
            n += 1
    os.replace(tmp, path)
    print(f"[project] {path}: kept {n} rows with columns (smiles, {label_col})")


def download(name, url, min_rows, gz=True, project=None):
    out_path = os.path.join(DATA_RAW, f"{name}.csv")
    if os.path.exists(out_path):
        print(f"[skip] {name}: already present at {out_path}")
        return verify(out_path, min_rows)
    print(f"[download] {name} <- {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read()
    # DeepChem files are gzipped CSVs; some are plain CSV.
    is_gz = gz
    if is_gz:
        try:
            text = gzip.decompress(raw).decode("utf-8", errors="replace")
        except OSError:
            text = raw.decode("utf-8", errors="replace")
    else:
        text = raw.decode("utf-8", errors="replace")
    with open(out_path, "w") as f:
        f.write(text)
    # Optional projection: extract (smiles, label) into a clean 2-column CSV.
    if project:
        _project_csv(out_path, project[0], project[1])
    print(f"[saved] {out_path} ({len(text)} bytes)")
    return verify(out_path, min_rows)


def verify(path, min_rows):
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        n = sum(1 for _ in reader)
    has_smiles = "smiles" in [h.lower() for h in header]
    ok = (n >= min_rows) and has_smiles
    print(f"[verify] {os.path.basename(path)}: rows={n} smiles_col={has_smiles} -> {'OK' if ok else 'FAIL'}")
    return {"path": path, "rows": n, "has_smiles": has_smiles, "ok": ok,
            "n_label_cols": max(0, len(header) - 1)}


def main():
    ensure_dirs()
    summary = {}
    all_ok = True
    for name, meta in DATASETS.items():
        try:
            r = download(name, meta["url"], meta["min_rows"], meta.get("gz", True), meta.get("project"))
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            r = {"path": "", "rows": 0, "has_smiles": False, "ok": False, "error": str(e)}
            all_ok = False
        summary[name] = r
        if not r["ok"]:
            all_ok = False
    print("\n=== DATA ACQUISITION SUMMARY ===")
    for k, v in summary.items():
        print(f"  {k:10s}: rows={v.get('rows')} smiles={v.get('has_smiles')} ok={v.get('ok')}")
    if not all_ok:
        print("RESULT: FAIL — one or more datasets missing/invalid")
        sys.exit(1)
    print("RESULT: OK — all 5 datasets downloaded and verified")


if __name__ == "__main__":
    main()
