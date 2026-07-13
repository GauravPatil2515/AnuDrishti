#!/usr/bin/env python3
"""
Generate publication figures from a faithfulness evaluation run.

Reads the results.csv written by run_faithful_eval.py and produces:
  - faithfulness_distribution.png  (distribution of scores; real, not the old constant)
  - acceptance_rate.png            (accepted vs rejected)
  - toxicity_vs_faithfulness.png   (faithfulness vs predicted toxicity)

Usage:
    python generate_paper_figures.py \
        --results results/eval_tox21_fixed/results.csv \
        --output results/paper_figures
"""

import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman"],
    "axes.linewidth": 1.5,
    "axes.labelsize": 14,
    "font.size": 12,
    "xtick.major.width": 1.5,
    "ytick.major.width": 1.5,
    "legend.fontsize": 12,
    "legend.frameon": True,
})
sns.set_style("white")


def load_data(csv_path):
    csv_path = Path(csv_path)
    if not csv_path.exists():
        print(f"Error: {csv_path} not found. Run run_faithful_eval.py first.")
        return None
    return pd.read_csv(csv_path)


def plot_faithfulness_distribution(df, out_dir):
    plt.figure(figsize=(10, 6))
    sub = df[df['n_toxicophores'] > 0] if 'n_toxicophores' in df.columns else df
    sns.violinplot(data=sub, x='faithfulness_score', color='#ecf0f1', inner=None, linewidth=1.5)
    sns.swarmplot(data=sub, x='faithfulness_score', color='#2ecc71', size=10, alpha=0.9, edgecolor='black', linewidth=1)
    plt.title('Distribution of Faithfulness Scores (claim-bearing molecules)', fontweight='bold')
    plt.xlabel('Faithfulness Score $F$ (0-1)')
    plt.tight_layout()
    plt.savefig(out_dir / 'faithfulness_distribution.pdf', dpi=300, format='pdf')
    
    # Also save to overleaf
    overleaf_dir = Path('overleaf/figures')
    if overleaf_dir.exists():
        plt.savefig(overleaf_dir / 'faithfulness_distribution.pdf', dpi=300, format='pdf')
    
    plt.close()
    print("Generated faithfulness_distribution.pdf")


def plot_rejection_analysis(df, out_dir):
    plt.figure(figsize=(8, 6))
    pass_count = int(df['validation_passed'].sum())
    fail_count = len(df) - pass_count
    plt.pie([pass_count, fail_count], labels=['Accepted', 'Rejected'],
            colors=['#2ecc71', '#e74c3c'], autopct='%1.1f%%',
            explode=(0, 0.1), shadow=True, startangle=90)
    plt.title('Explanation Acceptance Rate', fontweight='bold')
    plt.tight_layout()
    plt.savefig(out_dir / 'acceptance_rate.png', dpi=300)
    plt.close()
    print("Generated acceptance_rate.png")


def plot_toxicity_vs_faithfulness(df, out_dir):
    plt.figure(figsize=(10, 6))
    sub = df[df['n_toxicophores'] > 0] if 'n_toxicophores' in df.columns else df
    sns.scatterplot(data=sub, x='prediction', y='faithfulness_score',
                    alpha=0.6, color='#3498db', s=100)
    plt.title('Faithfulness vs. Predicted Toxicity', fontweight='bold')
    plt.xlabel('Predicted Toxicity Probability')
    plt.ylabel('Faithfulness Score $F$')
    if len(sub) > 2:
        sns.regplot(data=sub, x='prediction', y='faithfulness_score',
                    scatter=False, color='gray', line_kws={'linestyle': '--'})
    plt.tight_layout()
    plt.savefig(out_dir / 'toxicity_vs_faithfulness.png', dpi=300)
    plt.close()
    print("Generated toxicity_vs_faithfulness.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', default='results/eval_tox21_fixed/results.csv',
                    help='Path to results.csv from run_faithful_eval.py')
    ap.add_argument('--output', default='results/paper_figures',
                    help='Output directory for figures')
    args = ap.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Generating paper figures...")
    df = load_data(args.results)
    if df is not None:
        plot_faithfulness_distribution(df, out_dir)
        plot_rejection_analysis(df, out_dir)
        plot_toxicity_vs_faithfulness(df, out_dir)
        print(f"\nFigures saved to {out_dir.absolute()}")


if __name__ == "__main__":
    main()
