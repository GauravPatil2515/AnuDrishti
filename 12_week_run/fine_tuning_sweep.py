#!/usr/bin/env python3
"""
Fine-tuning sweep for pre-trained GIN encoder.
Runs multiple seeds with different pre-trained weights.
"""

import subprocess
import os
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def run_finetuning(seed, pretrained_weight, task="tox21", epochs=30):
    """Run fine-tuning for a given seed and pre-trained weight."""
    cmd = [
        sys.executable, "backend/models/train_attention_gin.py",
        "--task", task,
        "--epochs", str(epochs),
        "--batch_size", "32",
        "--lr", "1e-4",
        "--pretrained", pretrained_weight,
        "--seed", str(seed),
        "--output_dir", f"./finetune_sweep/seed{seed}_{Path(pretrained_weight).stem}"
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode == 0, result.stdout, result.stderr

def main():
    """Run fine-tuning sweep."""
    print("Starting fine-tuning sweep...")
    
    seeds = [42, 123, 456]
    weights = [
        "./pretrained/gin_supervised_masking.pth",
        "./pretrained/gin_supervised_contextpred.pth",
        "./pretrained/attr_masking_gin.pth"  # from our pre-training
    ]
    
    # Filter to existing weights
    existing_weights = [w for w in weights if os.path.exists(w)]
    if not existing_weights:
        print("No pre-trained weights found. Please run week 6 and 7 first.")
        return
    
    print(f"Testing seeds: {seeds}")
    print(f"Testing weights: {existing_weights}")
    
    results = {}
    
    for seed in seeds:
        for weight in existing_weights:
            if os.path.exists(weight):
                weight_name = os.path.basename(weight)
                print(f"\nRunning seed {seed} with weight {weight_name}")
                success, stdout, stderr = run_finetuning(seed, weight)
                
                if success:
                    # Extract final metrics from output
                    lines = (stdout + "\n" + stderr).split('\n')
                    val_auc = None
                    test_auc = None
                    for line in lines:
                        if "Best validation ROC-AUC:" in line:
                            val_auc = float(line.split(":")[1].strip())
                        elif "mean_roc_auc:" in line:
                            test_auc = float(line.split(":")[1].strip())
                    
                    result_str = f"Val AUC: {val_auc:.4f}" if val_auc else "No metrics found"
                    if test_auc:
                        result_str += f", Test AUC: {test_auc:.4f}"
                    
                    print(f"  Success: {result_str}")
                    results[(seed, weight_name)] = {
                        'success': True, 'val_auc': val_auc, 'test_auc': test_auc,
                        'stdout': stdout, 'stderr': stderr
                    }
                else:
                    print(f"  Failed: {stderr[:200]}...")
                    results[(seed, weight_name)] = {
                        'success': False, 'stdout': stdout, 'stderr': stderr
                    }
            else:
                print(f"Skipping {weight} - file not found")
    
    # Print summary
    print("\n" + "="*50)
    print("FINE-TUNING SWEEP SUMMARY")
    print("="*50)
    for (seed, weight), result in results.items():
        if result['success']:
            val_auc = result['val_auc'] or 'N/A'
            test_auc = result['test_auc'] or 'N/A'
            print(f"Seed {seed:3d} + {weight:25s}: Val AUC = {val_auc:>6}, Test AUC = {test_auc:>6}")
        else:
            print(f"Seed {seed:3d} + {weight:25s}: FAILED")
    
    # Find best combination
    successful = [(k, v) for k, v in results.items() if v['success'] and v['val_auc'] is not None]
    if successful:
        best = max(successful, key=lambda x: x[1]['val_auc'])
        (best_seed, best_weight), best_result = best
        print(f"\nBEST: Seed {best_seed} + {best_weight} (Val AUC: {best_result['val_auc']:.4f})")

if __name__ == "__main__":
    main()
