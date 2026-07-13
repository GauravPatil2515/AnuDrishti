#!/usr/bin/env python3
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def main():
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
    
    # Data from Table III
    configurations = [
        "Full DeNovo",
        "No Attention\n(Mean Pooling)",
        "No Transfer\nLearning",
        "No Causal\nValidation"
    ]
    
    roc_auc = [0.802, 0.815, 0.798, 0.837]
    faithfulness = [0.865, 0.0, 0.810, 0.635]  # Mean pooling is N/A (0.0 for plot)
    
    import pandas as pd
    df = pd.DataFrame({
        'Configuration': configurations * 2,
        'Metric Value': roc_auc + faithfulness,
        'Metric': ['ROC-AUC'] * 4 + ['Faithfulness'] * 4
    })
    
    plt.figure(figsize=(9, 6))
    
    # Palette matching DeNovo's theme: Blue for ROC-AUC, Green for Faithfulness
    colors = ['#3498db', '#2ecc71']
    
    ax = sns.barplot(
        data=df,
        x='Configuration',
        y='Metric Value',
        hue='Metric',
        palette=colors,
        edgecolor='black',
        linewidth=1.0
    )
    
    # Customise axes
    plt.xlabel('System Configuration', fontweight='bold', labelpad=10)
    plt.ylabel('Score (0.0 - 1.0)', fontweight='bold', labelpad=10)
    plt.title('Architecture Component Ablation Study (Tox21)', fontweight='bold', pad=15)
    plt.ylim(0, 1.05)
    
    # Annotate the values on top of bars
    for p in ax.patches:
        height = p.get_height()
        if height > 0.0:
            ax.annotate(f'{height:.3f}',
                        (p.get_x() + p.get_width() / 2., height),
                        ha='center', va='center',
                        xytext=(0, 8),
                        textcoords='offset points',
                        fontsize=10,
                        fontweight='bold')
        elif p.get_x() > 0.5 and p.get_x() < 1.5:  # This is the Faithfulness bar for Mean Pooling
            # Draw "N/A" text for mean pooling faithfulness
            ax.annotate('N/A',
                        (p.get_x() + p.get_width() / 2., 0.02),
                        ha='center', va='center',
                        xytext=(0, 8),
                        textcoords='offset points',
                        fontsize=10,
                        fontweight='bold',
                        color='gray')
            
    plt.legend(loc='lower left', frameon=True, facecolor='white', edgecolor='gray')
    plt.tight_layout()
    
    # Save to both locations
    results_dir = Path('results/paper_figures')
    results_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(results_dir / 'ablation.pdf', dpi=300, format='pdf')
    
    overleaf_dir = Path('overleaf/figures')
    overleaf_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(overleaf_dir / 'ablation.pdf', dpi=300, format='pdf')
    plt.close()
    
    print("Successfully generated ablation.pdf in both results/paper_figures/ and overleaf/figures/.")

if __name__ == '__main__':
    main()
