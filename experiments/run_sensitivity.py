#!/usr/bin/env python3
"""
Hyperparameter Sensitivity Analysis
===================================
Runs the faithful evaluation pipeline over a grid of:
- kappa (adaptive cutoff factor): 1.5, 2.0, 3.0
- delta (causal drop threshold): 0.05, 0.10, 0.15

Usage:
    python experiments/run_sensitivity.py

Author: DeNovo-XAI Research Team
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Add paths
SCRIPT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = SCRIPT_DIR.parent / 'backend'
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(BACKEND_DIR / 'models'))
sys.path.insert(0, str(BACKEND_DIR / 'utils'))

from run_faithful_eval import run_faithful_evaluation
from faithfulness_validator import FaithfulnessValidator
from substructure_mapper import SubstructureMapper

def main():
    grid = [
        {'kappa': 1.5, 'delta': 0.10},
        {'kappa': 2.0, 'delta': 0.10},  # default
        {'kappa': 3.0, 'delta': 0.10},
        {'kappa': 2.0, 'delta': 0.05},
        {'kappa': 2.0, 'delta': 0.15}
    ]

    model_path = 'results/trained_models/attention_gin_model.pth'
    dataset_path = 'data_packages/tox21_model_full_package/data/tox21/tox21.csv'
    # Reduced n per cell: 5 cells x a full run would exceed a single day's LLM
    # token budget. 12 toxic-predicted molecules/cell keeps the whole sweep within
    # ~100k tokens; the resulting rates carry more variance (reported as such).
    n_molecules = int(os.getenv('SENS_N', '12'))

    results = []

    # Save original init methods
    original_val_init = FaithfulnessValidator.__init__
    original_map_init = SubstructureMapper.__init__

    try:
        for cell in grid:
            kappa = cell['kappa']
            delta = cell['delta']
            print(f"\nRunning sensitivity for kappa={kappa}, delta={delta}...")
            
            # Patch constructor to override values dynamically
            def make_patched_val_init(k, d):
                def patched_val_init(self, *args, **kwargs):
                    original_val_init(self, *args, **kwargs)
                    self.kappa = k
                    self.causal_drop_threshold = d
                return patched_val_init
            
            def make_patched_map_init(k):
                def patched_map_init(self, *args, **kwargs):
                    original_map_init(self, *args, **kwargs)
                    self.relative_factor = k
                return patched_map_init
            
            FaithfulnessValidator.__init__ = make_patched_val_init(kappa, delta)
            SubstructureMapper.__init__ = make_patched_map_init(kappa)

            try:
                stats = run_faithful_evaluation(
                    model_path=model_path,
                    dataset_path=dataset_path,
                    output_dir=f'results/sensitivity_kappa_{kappa}_delta_{delta}',
                    n_molecules=n_molecules,
                    validate_faithfulness=True
                )
            except Exception as e:
                print(f"  cell kappa={kappa} delta={delta} FAILED: {e}")
                results.append({'kappa': kappa, 'delta': delta, 'error': str(e)})
                continue

            results.append({
                'kappa': kappa,
                'delta': delta,
                'n_evaluated': stats.get('n_evaluated'),
                'rejection_rate': stats['rejection_rate'],
                'mean_faithfulness': stats['mean_faithfulness'],
                'mean_faithfulness_claims': stats.get('mean_faithfulness_claims'),
                'n_with_claims': stats.get('n_with_claims')
            })
            
    finally:
        # Restore original classes
        FaithfulnessValidator.__init__ = original_val_init
        SubstructureMapper.__init__ = original_map_init

    # Print summary table
    print("\n" + "="*50)
    print("HYPERPARAMETER SENSITIVITY ANALYSIS RESULTS")
    print("="*50)
    print(f"{'kappa':6s} {'delta':6s} {'Rejection Rate':15s} {'Faithfulness':12s}")
    for r in results:
        print(f"{r['kappa']:<6.1f} {r['delta']:<6.2f} {r['rejection_rate']:<15.1%} {r['mean_faithfulness']:<12.3f}")
    print("="*50)

    # Save to JSON
    with open('results/sensitivity_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("Wrote results/sensitivity_results.json")

if __name__ == '__main__':
    main()
