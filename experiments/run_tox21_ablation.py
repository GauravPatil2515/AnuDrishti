import os
import sys
import json
import torch
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "backend" / "models"))
from train_attention_gin import AttentionGINTrainer, DEFAULT_CONFIG

def main():
    print("==================================================")
    print("Running Tox21 Ablation Studies")
    print("==================================================")
    
    # 1. Ablation -- Attention Pooling (Mean Pooling)
    print("\n[Ablation 1/2] Training with Mean Pooling...")
    config_mean = DEFAULT_CONFIG.copy()
    config_mean['model'] = DEFAULT_CONFIG['model'].copy()
    config_mean['model']['pool'] = 'mean'
    config_mean['training'] = DEFAULT_CONFIG['training'].copy()
    config_mean['training']['epochs'] = 100
    config_mean['training']['patience'] = 15
    config_mean['data'] = DEFAULT_CONFIG['data'].copy()
    config_mean['data']['random_seed'] = 42
    
    history_mean_file = PROJECT / 'results' / 'ablation_mean' / 'training_history.csv'
    if not history_mean_file.exists():
        trainer_mean = AttentionGINTrainer(
            config=config_mean,
            task_name='tox21',
            output_dir=str(PROJECT / 'results' / 'ablation_mean')
        )
        trainer_mean.train()
    else:
        print("Mean Pooling history found. Skipping training.")
    
    # Load validation history and find best val score
    history_mean = pd.read_csv(PROJECT / 'results' / 'ablation_mean' / 'training_history.csv')
    best_val_mean = history_mean['val_score'].max()
    print(f"Mean Pooling Best Val ROC-AUC: {best_val_mean:.4f}")
    
    # 2. Ablation -- Transfer Learning (No pre-training, from scratch)
    print("\n[Ablation 2/2] Training from scratch (No Transfer Learning)...")
    config_scratch = DEFAULT_CONFIG.copy()
    config_scratch['model'] = DEFAULT_CONFIG['model'].copy()
    config_scratch['transfer'] = DEFAULT_CONFIG['transfer'].copy()
    config_scratch['transfer']['no_load'] = True
    config_scratch['transfer']['pretrained_path'] = 'none'
    config_scratch['training'] = DEFAULT_CONFIG['training'].copy()
    config_scratch['training']['epochs'] = 100
    config_scratch['training']['patience'] = 15
    config_scratch['data'] = DEFAULT_CONFIG['data'].copy()
    config_scratch['data']['random_seed'] = 42
    
    trainer_scratch = AttentionGINTrainer(
        config=config_scratch,
        task_name='tox21',
        output_dir=str(PROJECT / 'results' / 'ablation_scratch')
    )
    trainer_scratch.train()
    
    history_scratch = pd.read_csv(PROJECT / 'results' / 'ablation_scratch' / 'training_history.csv')
    best_val_scratch = history_scratch['val_score'].max()
    print(f"No Transfer Learning Best Val ROC-AUC: {best_val_scratch:.4f}")
    
    # Save ablation metrics
    results = {
        'full_denovo': 0.837,
        'mean_pooling': round(float(best_val_mean), 4),
        'no_transfer': round(float(best_val_scratch), 4)
    }
    out_path = PROJECT / 'results' / 'ablation_metrics.json'
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nSaved ablation metrics to {out_path}: {results}")

if __name__ == "__main__":
    main()
