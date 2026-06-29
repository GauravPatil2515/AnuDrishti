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

plt.style.use('seaborn-v0_8-paper')
sns.set_context("paper", font_scale=1.5)
sns.set_style("whitegrid")


def load_data(csv_path):
    csv_path = Path(csv_path)
    if not csv_path.exists():
        print(f"Error: {csv_path} not found. Run run_faithful_eval.py first.")
        return None
    return pd.read_csv(csv_path)


def plot_faithfulness_distribution(df, out_dir):
    plt.figure(figsize=(10, 6))
    # Show the full distribution over claim-bearing molecules (the meaningful
    # population). Rejections (F=0) are included so the figure reflects reality.
    sub = df[df['n_toxicophores'] > 0] if 'n_toxicophores' in df.columns else df
    sns.histplot(data=sub, x='faithfulness_score', bins=20, kde=True, color='#2ecc71')
    plt.title('Distribution of Faithfulness Scores (claim-bearing molecules)', fontweight='bold')
    plt.xlabel('Faithfulness Score $F$ (0-1)')
    plt.ylabel('Count')
    med = sub['faithfulness_score'].median()
    plt.axvline(med, color='red', linestyle='--', label=f'Median: {med:.3f}')
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / 'faithfulness_distribution.png', dpi=300)
    plt.close()
    print("Generated faithfulness_distribution.png")


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
