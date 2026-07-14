import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from backend.models.train_attention_gin import AttentionGINTrainer, DEFAULT_CONFIG

def main():
    tasks = ['bbbp', 'clintox', 'tox21']
    epochs = {
        'bbbp': 50,
        'clintox': 50,
        'tox21': 50
    }
    patience = {
        'bbbp': 15,
        'clintox': 15,
        'tox21': 15
    }
    batch_size = 64
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_dir = PROJECT_DIR / 'results' / f'cpu_runs_{timestamp}'
    run_dir.mkdir(parents=True, exist_ok=True)
    
    summary = {}
    
    for task in tasks:
        print(f"\n============================================================")
        print(f"STARTING CPU TRAINING RUN FOR TASK: {task.upper()}")
        print(f"============================================================")
        
        # Configure task-specific settings
        config = DEFAULT_CONFIG.copy()
        config['training']['epochs'] = epochs[task]
        config['training']['patience'] = patience[task]
        config['training']['batch_size'] = batch_size
        config['training']['use_focal_loss'] = True
        config['training']['focal_loss_gamma'] = 2.0
        
        # Disable pretrained weights file warning if not found
        # (It prints an error, but proceeds with training from scratch)
        config['transfer']['pretrained_path'] = None # train from scratch as a CPU baseline
        
        task_output_dir = run_dir / task
        task_output_dir.mkdir(parents=True, exist_ok=True)
        
        trainer = AttentionGINTrainer(
            config=config,
            task_name=task,
            output_dir=str(task_output_dir)
        )
        
        try:
            trainer.train()
            
            # Load results
            results_path = task_output_dir / 'test_results.json'
            if results_path.exists():
                with open(results_path) as f:
                    res_data = json.load(f)
                summary[task] = res_data['test_metrics']
                print(f"Finished {task}! Test Metrics: {res_data['test_metrics']}")
            else:
                print(f"Warning: test_results.json not found for {task}")
                summary[task] = "Failed to locate results"
        except Exception as e:
            print(f"Error training task {task}: {e}")
            summary[task] = f"Error: {str(e)}"
            
    # Save final summary
    print("\n============================================================")
    print("ALL CPU TRAINING RUNS COMPLETED")
    print("============================================================")
    
    summary_path = run_dir / 'summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=4)
        
    print(f"\nSaved summary to: {summary_path}")
    
    # Print nice table
    print("\nSummary Table:")
    print(f"{'Task':12s} | {'ROC-AUC':10s} | {'Accuracy':10s} | {'Precision':10s} | {'Recall':10s} | {'F1-Score':10s}")
    print("-" * 75)
    for task, metrics in summary.items():
        if isinstance(metrics, dict):
            auc = metrics.get('mean_roc_auc', metrics.get('roc_auc', 0.0))
            acc = metrics.get('accuracy', 0.0)
            prec = metrics.get('precision', 0.0)
            rec = metrics.get('recall', 0.0)
            f1 = metrics.get('f1_score', 0.0)
            print(f"{task:12s} | {auc:10.4f} | {acc:10.4f} | {prec:10.4f} | {rec:10.4f} | {f1:10.4f}")
        else:
            print(f"{task:12s} | {metrics}")

if __name__ == '__main__':
    main()
