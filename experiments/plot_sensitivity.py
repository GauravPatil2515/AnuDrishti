#!/usr/bin/env python3
import json
from pathlib import Path
import matplotlib.pyplot as plt

def main():
    # Configure clean, publication-quality matplotlib style
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['xtick.labelsize'] = 11
    plt.rcParams['ytick.labelsize'] = 11
    
    json_path = Path('results/sensitivity_results.json')
    if not json_path.exists():
        print(f"Error: {json_path} not found.")
        return
        
    with open(json_path) as f:
        data = json.load(f)
        
    for d in data:
        d['rejection_rate_pct'] = d['rejection_rate'] * 100.0
        
    plt.figure(figsize=(9, 6.5))
    plt.grid(True, linestyle='--', alpha=0.6)
    
    for d in data:
        is_default = (d['kappa'] == 2.0 and d['delta'] == 0.1)
        color = '#e74c3c' if is_default else '#34495e'
        marker = '*' if is_default else 'o'
        size = 250 if is_default else 120
        
        plt.scatter(d['rejection_rate_pct'], d['mean_faithfulness'], 
                    color=color, marker=marker, s=size, zorder=5)
        
        # Label the point using raw strings to avoid syntax warnings
        label_text = r"$\kappa=" + str(d['kappa']) + r"$, $\delta=" + str(d['delta']) + r"$"
        if is_default:
            label_text += "\n(Default Operating Point)"
            
        xytext = (10, -5) if not is_default else (-40, -45)
        if d['kappa'] == 1.5:
            xytext = (-90, 5)
        elif d['kappa'] == 3.0:
            xytext = (10, 5)
        elif d['delta'] == 0.05:
            xytext = (-70, 15)
            
        plt.annotate(label_text, 
                     xy=(d['rejection_rate_pct'], d['mean_faithfulness']),
                     xytext=xytext,
                     textcoords='offset points',
                     fontsize=11,
                     fontweight='bold' if is_default else 'normal',
                     arrowprops=dict(arrowstyle="->", color='gray', lw=0.8) if is_default else None)

    plt.xlabel('Explanation Rejection Rate (%)', fontweight='bold')
    plt.ylabel('Average Faithfulness Score $F$', fontweight='bold')
    plt.title('Sensitivity Analysis & Parameter Trade-offs', fontweight='bold', pad=15)
    plt.xlim(2, 22)
    plt.ylim(0.78, 0.98)
    
    plt.tight_layout()
    
    results_dir = Path('results/paper_figures')
    results_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(results_dir / 'sensitivity_tradeoff.png', dpi=300)
    
    overleaf_dir = Path('overleaf/figures')
    overleaf_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(overleaf_dir / 'sensitivity_tradeoff.png', dpi=300)
    plt.close()
    
    print("Successfully generated sensitivity_tradeoff.png in both results/paper_figures/ and overleaf/figures/.")

if __name__ == '__main__':
    main()
