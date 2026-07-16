#!/usr/bin/env python3
"""
Constrained vs. Unconstrained Comparison
========================================
Reads the statistics.json produced by run_faithful_eval.py (constrained DeNovo)
and run_unconstrained_baseline.py (unconstrained LLM) and emits the headline
faithfulness comparison: mean F, grounding, causal, and rejection rate for each,
plus the absolute improvement. Also writes a ready-to-paste LaTeX table fragment.

Usage:
    python compare_baselines.py \
        --constrained results/eval_tox21_fixed/statistics.json \
        --unconstrained results/baseline_unconstrained_tox21/statistics.json \
        --out results/faithfulness_comparison

Author: DeNovo-XAI Research Team
"""

import json
import argparse
from pathlib import Path


def load(path):
    with open(path) as f:
        return json.load(f)


def g(d, *keys):
    """First present, non-None key."""
    for k in keys:
        if d.get(k) is not None:
            return d[k]
    return None


def fmt(x):
    return f"{x:.3f}" if isinstance(x, (int, float)) else "--"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--constrained', required=True)
    ap.add_argument('--unconstrained', required=True)
    ap.add_argument('--out', default='results/faithfulness_comparison')
    args = ap.parse_args()

    c = load(args.constrained)
    u = load(args.unconstrained)

    # Prefer the claim-bearing subset (the scientifically meaningful population).
    c_f = g(c, 'mean_faithfulness_claims', 'mean_faithfulness')
    u_f = g(u, 'mean_faithfulness_claims', 'mean_faithfulness')
    c_g = g(c, 'mean_grounding')   # constrained eval may not log these; fall back to --
    u_g = g(u, 'mean_grounding')
    c_c = g(c, 'mean_causal')
    u_c = g(u, 'mean_causal')
    c_rej = g(c, 'rejection_rate')
    u_rej = g(u, 'rejection_rate')

    delta = (c_f - u_f) if (c_f is not None and u_f is not None) else None

    print("=" * 64)
    print("FAITHFULNESS: CONSTRAINED (DeNovo) vs UNCONSTRAINED LLM")
    print("=" * 64)
    print(f"{'metric':22s} {'constrained':>12s} {'unconstrained':>14s}")
    print(f"{'mean F':22s} {fmt(c_f):>12s} {fmt(u_f):>14s}")
    print(f"{'mean grounding':22s} {fmt(c_g):>12s} {fmt(u_g):>14s}")
    print(f"{'mean causal':22s} {fmt(c_c):>12s} {fmt(u_c):>14s}")
    print(f"{'rejection rate':22s} {fmt(c_rej):>12s} {fmt(u_rej):>14s}")
    if delta is not None:
        print(f"\nAbsolute improvement in F: {delta:+.3f}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    latex = (
        "\\begin{table}[h]\n\\centering\n"
        "\\caption{Faithfulness on Tox21: constrained DeNovo vs.\\ unconstrained LLM "
        "(claim-bearing molecules).}\n\\label{tab:faith_compare}\n"
        "\\begin{tabular}{lcc}\n\\toprule\n"
        "\\textbf{Metric} & \\textbf{DeNovo (constrained)} & \\textbf{Unconstrained LLM} \\\\\n"
        "\\midrule\n"
        f"Mean Faithfulness $F$ & {fmt(c_f)} & {fmt(u_f)} \\\\\n"
        f"Grounding $S_g$ & {fmt(c_g)} & {fmt(u_g)} \\\\\n"
        f"Causal $S_c$ & {fmt(c_c)} & {fmt(u_c)} \\\\\n"
        f"Rejection rate & {fmt(c_rej)} & {fmt(u_rej)} \\\\\n"
        "\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )
    (out / 'faithfulness_comparison.tex').write_text(latex)
    summary = {
        'constrained': {'F': c_f, 'grounding': c_g, 'causal': c_c, 'rejection': c_rej},
        'unconstrained': {'F': u_f, 'grounding': u_g, 'causal': u_c, 'rejection': u_rej},
        'delta_F': delta,
    }
    (out / 'comparison.json').write_text(json.dumps(summary, indent=2))
    print(f"\nWrote {out/'faithfulness_comparison.tex'} and comparison.json")


if __name__ == '__main__':
    main()
