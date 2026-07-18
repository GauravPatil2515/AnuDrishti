import os
import sys
import subprocess
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def main():
    print("=" * 60)
    print("STARTING ENTIRE DENOVO V2 PIPELINE EXECUTION ON GPU")
    print("=" * 60)
    
    scripts = [
        ("Week 7: Attribute Masking Pre-training", "12_week_run/attribute_masking_pretrain.py"),
        ("Week 8: Fine-Tuning Sweep (3 Seeds)", "12_week_run/fine_tuning_sweep.py"),
        ("Week 9: TabPFN Baseline", "12_week_run/baselines/tabpfn_baseline.py"),
        ("Week 9: SNN Baseline", "12_week_run/baselines/snn_baseline.py"),
        ("Week 10: GPT-4 Zero-shot Baseline", "12_week_run/gpt4_zero_shot.py"),
        ("Week 11: JKU Evaluation", "12_week_run/jku_evaluation.py")
    ]
    
    start_time = time.time()
    
    for name, path in scripts:
        print(f"\n>>> Running: {name}")
        print(f"    Path: {path}")
        print("-" * 40)
        
        full_path = PROJECT_ROOT / path
        
        # Execute script using sys.executable
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        
        try:
            subprocess.run(
                [sys.executable, str(full_path)],
                env=env,
                check=True,
                text=True
            )
            print(f"\n[PASS] Finished {name} successfully!")
        except subprocess.CalledProcessError as e:
            print(f"\n[FAIL] ERROR: {name} failed with exit code {e.returncode}")
            sys.exit(e.returncode)
            
    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"ALL PIPELINE STEPS COMPLETED IN {total_time/60:.2f} MINUTES")
    print("=" * 60)

if __name__ == "__main__":
    main()
