#!/usr/bin/env python3
"""
Master Training Script for ADMET GIN Models
============================================
Trains all ADMET property prediction models sequentially.

Usage:
    python train_all_models.py --config training_config.yaml
    python train_all_models.py --model bbbp  # Train single model
"""

import os
import sys
import yaml
import argparse
import shutil
from pathlib import Path
from datetime import datetime

# Add project paths
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))
sys.path.insert(0, str(project_dir / "backend"))

def load_config(config_path):
    """Load training configuration"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logging(model_name):
    """Setup logging for training"""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{model_name}_{timestamp}.log"
    
    # Also create a "latest" symlink
    latest_log = log_dir / "latest.log"
    if latest_log.exists():
        latest_log.unlink()
    
    return log_file

def check_data_availability(config, model_name):
    """Check if training data is available for the model"""
    model_config = config['models'][model_name]
    package_dir = project_dir / model_config['package_dir']
    
    print(f"\n📂 Checking data for {model_config['name']}...")
    
    if not package_dir.exists():
        print(f"   ❌ Package directory not found: {package_dir}")
        return False
    
    # Check for data directory
    data_dir = package_dir / "data"
    if not data_dir.exists():
        print(f"   ❌ Data directory not found: {data_dir}")
        return False
    
    # Check for required files
    required_files = ["dataset.csv", "train.csv", "valid.csv", "test.csv"]
    data_files = list(data_dir.glob("*.csv"))
    
    if len(data_files) == 0:
        print(f"   ❌ No CSV files found in {data_dir}")
        return False
    
    print(f"   ✅ Found {len(data_files)} data files")
    for f in data_files[:3]:
        print(f"      - {f.name}")
    if len(data_files) > 3:
        print(f"      ... and {len(data_files) - 3} more")
    
    return True

def train_model(config, model_name):
    """Train a single model"""
    model_config = config['models'][model_name]
    
    print(f"\n{'='*60}")
    print(f"🚀 Training: {model_config['name']}")
    print(f"{'='*60}")
    
    # Check if already trained
    if model_config.get('status') == 'trained':
        print(f"   ⚠️ Model already trained. Skipping.")
        print(f"   Output: {model_config['output_file']}")
        return True
    
    # Check data availability
    if not check_data_availability(config, model_name):
        print(f"   ❌ Cannot train: missing data")
        return False
    
    package_dir = project_dir / model_config['package_dir']
    
    # Determine training settings
    is_classification = model_config['type'] == 'classification'
    train_config = config['classification'] if is_classification else config['regression']
    
    print(f"\n📊 Training Configuration:")
    print(f"   Type: {model_config['type']}")
    print(f"   Tasks: {model_config['num_tasks']}")
    print(f"   Epochs: {train_config['epochs']}")
    print(f"   Batch Size: {train_config['batch_size']}")
    print(f"   Learning Rate: {train_config['learning_rate']}")
    print(f"   Target: {model_config['target_metric']} {'≥' if is_classification else '≤'} {model_config['target_value']}")
    
    # Build training command
    finetune_script = package_dir / "finetune.py"
    if not finetune_script.exists():
        print(f"   ❌ finetune.py not found in {package_dir}")
        return False
    
    # Change to package directory and run training
    original_dir = os.getcwd()
    os.chdir(package_dir)
    
    try:
        # Import and run finetune
        sys.path.insert(0, str(package_dir))
        
        print(f"\n🔄 Starting training...")
        print(f"   This may take {train_config['epochs'] * 2} - {train_config['epochs'] * 3} minutes...")
        
        # Run the training
        import importlib.util
        spec = importlib.util.spec_from_file_location("finetune", finetune_script)
        finetune_module = importlib.util.module_from_spec(spec)
        
        # This would execute the training
        # For now, print what would happen
        print(f"\n   ⚠️ Training not executed automatically.")
        print(f"   Run manually:")
        print(f"   cd {package_dir}")
        print(f"   python finetune.py --epochs {train_config['epochs']} --batch_size {train_config['batch_size']}")
        
        return False  # Return False since we didn't actually train
        
    except Exception as e:
        print(f"   ❌ Training failed: {e}")
        return False
    finally:
        os.chdir(original_dir)

def copy_trained_model(config, model_name, checkpoint_path):
    """Copy trained checkpoint to results folder"""
    model_config = config['models'][model_name]
    output_path = project_dir / model_config['output_file']
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(checkpoint_path, output_path)
    
    print(f"   ✅ Model saved to: {output_path}")
    return True

def print_status(config):
    """Print status of all models"""
    print("\n" + "="*60)
    print("📋 MODEL TRAINING STATUS")
    print("="*60)
    
    for model_name, model_config in config['models'].items():
        status_icon = "✅" if model_config.get('status') == 'trained' else "❌"
        output_exists = (project_dir / model_config['output_file']).exists()
        file_icon = "📦" if output_exists else "⚪"
        
        print(f"\n{status_icon} {model_config['name']}")
        print(f"   Type: {model_config['type']}")
        print(f"   Tasks: {model_config['num_tasks']}")
        print(f"   Target: {model_config['target_metric']} {'≥' if model_config['type'] == 'classification' else '≤'} {model_config['target_value']}")
        print(f"   {file_icon} Output: {model_config['output_file']}")

def main():
    parser = argparse.ArgumentParser(description="Train ADMET GIN Models")
    parser.add_argument('--config', type=str, default='training/training_config.yaml',
                       help='Path to training configuration')
    parser.add_argument('--model', type=str, default=None,
                       help='Train specific model (e.g., bbbp, caco2)')
    parser.add_argument('--status', action='store_true',
                       help='Print status of all models')
    parser.add_argument('--check-data', action='store_true',
                       help='Check data availability for all models')
    
    args = parser.parse_args()
    
    # Load configuration
    config_path = project_dir / args.config
    if not config_path.exists():
        print(f"❌ Config not found: {config_path}")
        return
    
    config = load_config(config_path)
    
    print("="*60)
    print("🧬 ADMET GIN Model Training System")
    print("="*60)
    
    # Print status if requested
    if args.status:
        print_status(config)
        return
    
    # Check data if requested
    if args.check_data:
        print("\n📂 Checking data availability for all models...")
        for model_name in config['models']:
            check_data_availability(config, model_name)
        return
    
    # Train specific model or all
    if args.model:
        if args.model not in config['models']:
            print(f"❌ Unknown model: {args.model}")
            print(f"   Available: {list(config['models'].keys())}")
            return
        train_model(config, args.model)
    else:
        # Train all models
        print("\n🔄 Training all untrained models...")
        for model_name in config['models']:
            train_model(config, model_name)
    
    # Print final status
    print_status(config)

if __name__ == "__main__":
    main()
