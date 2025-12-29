import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
import numpy as np

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-paper')
sns.set_context("paper", font_scale=1.5)
sns.set_style("whitegrid")

OUTPUT_DIR = Path('results/paper_figures')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    """Load evaluation results."""
    csv_path = Path('results/eval_tox21_200/results.csv')
    if not csv_path.exists():
        print(f"Error: {csv_path} not found.")
        return None
    return pd.read_csv(csv_path)

def plot_faithfulness_distribution(df):
    """Plot histogram of faithfulness scores."""
    plt.figure(figsize=(10, 6))
    
    # Filter out 0.0 scores (rejections) for the distribution of *accepted* explanations
    accepted_df = df[df['validation_passed'] == True]
    
    sns.histplot(data=accepted_df, x='faithfulness_score', bins=20, kde=True, color='#2ecc71')
    
    plt.title('Distribution of Faithfulness Scores (Accepted Explanations)', fontweight='bold')
    plt.xlabel('Faithfulness Score (0-1)')
    plt.ylabel('Count')
    plt.axvline(accepted_df['faithfulness_score'].median(), color='red', linestyle='--', label=f'Median: {accepted_df["faithfulness_score"].median():.3f}')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'faithfulness_distribution.png', dpi=300)
    plt.close()
    print("Generated faithfulness_distribution.png")

def plot_rejection_analysis(df):
    """Plot rejection rate and reasons."""
    plt.figure(figsize=(8, 6))
    
    # Pie chart for Pass/Fail
    pass_count = df['validation_passed'].sum()
    fail_count = len(df) - pass_count
    
    plt.pie([pass_count, fail_count], labels=['Accepted', 'Rejected'], 
            colors=['#2ecc71', '#e74c3c'], autopct='%1.1f%%', 
            explode=(0, 0.1), shadow=True, startangle=90)
            
    plt.title('Explanation Acceptance Rate', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'acceptance_rate.png', dpi=300)
    plt.close()
    print("Generated acceptance_rate.png")

def plot_toxicity_vs_faithfulness(df):
    """Scatter plot of predicted toxicity vs faithfulness."""
    plt.figure(figsize=(10, 6))
    
    accepted_df = df[df['validation_passed'] == True]
    
    sns.scatterplot(data=accepted_df, x='prediction', y='faithfulness_score', 
                    alpha=0.6, color='#3498db', s=100)
    
    plt.title('Faithfulness vs. Predicted Toxicity', fontweight='bold')
    plt.xlabel('Predicted Toxicity Probability')
    plt.ylabel('Faithfulness Score')
    plt.ylim(0.5, 1.05)
    
    # Add trend line
    sns.regplot(data=accepted_df, x='prediction', y='faithfulness_score', 
                scatter=False, color='gray', line_kws={'linestyle': '--'})
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'toxicity_vs_faithfulness.png', dpi=300)
    plt.close()
    print("Generated toxicity_vs_faithfulness.png")

if __name__ == "__main__":
    print("Generating paper figures...")
    df = load_data()
    if df is not None:
        plot_faithfulness_distribution(df)
        plot_rejection_analysis(df)
        plot_toxicity_vs_faithfulness(df)
        print(f"\nFigures saved to {OUTPUT_DIR.absolute()}")
