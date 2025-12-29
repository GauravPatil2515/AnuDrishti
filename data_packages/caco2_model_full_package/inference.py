#!/usr/bin/env python3
"""
Model Inference Script for ADMET Prediction

This script loads a trained model and performs inference on new data.
Supports all ADMET tasks: BBBP, caco2, clearance, HLM_CLint, tox21

Usage:
    python inference.py --model_path path/to/model.pth --data_path path/to/data.csv --task_name caco2 --output results.csv

Author: Enhanced ADMET Pipeline
"""

import os
import sys
import argparse
import yaml
import numpy as np
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

import torch
from torch.utils.data import DataLoader
from torch_geometric.loader import DataLoader as GeoDataLoader
from sklearn.metrics import roc_auc_score, mean_absolute_error, root_mean_squared_error, precision_score, recall_score, f1_score, balanced_accuracy_score

from dataset.dataset_test import MolTestDatasetWrapper

def load_config(config_path='config_finetune.yaml'):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config

def setup_task_config(config, task_name):
    """Setup configuration for specific task"""
    # Set task-specific parameters
    if task_name == 'BBBP':
        config['dataset']['task'] = 'classification'
        config['dataset']['data_path'] = f'data/BBBP/BBBP.csv'
        target_list = ["p_np"]
    elif task_name == 'caco2':
        config['dataset']['task'] = 'regression'
        config['dataset']['data_path'] = f'data/caco2/caco2.csv'
        target_list = ["Y"]
    elif task_name == 'clearance':
        config['dataset']['task'] = 'regression'
        config['dataset']['data_path'] = f'data/clearance/clearance_hepatocyte_log.csv'
        target_list = ["clearance_hepatocyte_az"]
    elif task_name == 'HLM_CLint':
        config['dataset']['task'] = 'regression'
        config['dataset']['data_path'] = f'data/HLM_CLint/LOG_HLM_CLint.csv'
        target_list = ["LOG HLM_CLint (mL/min/kg)"]
    elif task_name == 'tox21':
        config['dataset']['task'] = 'classification'
        config['dataset']['data_path'] = f'data/tox21/tox21.csv'
        target_list = [
            "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase", "NR-ER", "NR-ER-LBD",
            "NR-PPAR-gamma", "SR-ARE", "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53"
        ]
    else:
        raise ValueError(f"Unknown task: {task_name}")

    config['num_tasks'] = len(target_list)
    config['dataset']['target'] = target_list
    config['task_name'] = task_name

    return config

def load_model(model_path, config, device):
    """Load trained model from checkpoint"""
    if config['model_type'] == 'gin':
        from models.ginet_finetune import GINet
        model = GINet(config['dataset']['task'], num_tasks=config['num_tasks'], **config["model"])
    elif config['model_type'] == 'gcn':
        from models.gcn_finetune import GCN
        model = GCN(config['dataset']['task'], num_tasks=config['num_tasks'], **config["model"])
    else:
        raise ValueError(f"Unknown model type: {config['model_type']}")

    # Load state dict
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    print(f"Loaded model from {model_path}")
    return model

def create_inference_dataset(data_path, config):
    """Create dataset for inference"""
    from dataset.dataset_test import MolTestDataset

    # Create a custom dataset that returns both data and smiles
    class InferenceDataset(MolTestDataset):
        def __getitem__(self, index):
            data = super().__getitem__(index)
            smiles = self.smiles_data[index]
            return data, smiles

    # Create dataset
    dataset = InferenceDataset(
        data_path=data_path,
        target=config['dataset']['target'],
        task=config['dataset']['task']
    )

    return dataset

def run_inference(model, dataloader, device, task_type):
    """Run inference on the data"""
    predictions = []
    labels = []
    smiles_list = []

    with torch.no_grad():
        for batch in dataloader:
            data, smiles_batch = batch
            data = data.to(device)

            # Forward pass
            _, pred = model(data)

            # Apply sigmoid for classification
            if task_type == 'classification':
                pred = torch.sigmoid(pred)

            # Convert to numpy
            if device == 'cpu':
                pred_np = pred.numpy()
                if hasattr(data, 'y'):
                    labels.extend(data.y.numpy())
            else:
                pred_np = pred.cpu().numpy()
                if hasattr(data, 'y'):
                    labels.extend(data.y.cpu().numpy())

            predictions.extend(pred_np)
            smiles_list.extend(smiles_batch)

    return np.array(predictions), np.array(labels) if labels else None, smiles_list

def calculate_metrics(predictions, labels, task_type, task_name):
    """Calculate performance metrics"""
    if labels is None or len(labels) == 0:
        print("No ground truth labels provided - skipping metrics calculation")
        return {}

    metrics = {}

    if task_type == 'classification':
        if task_name == 'BBBP':
            # Binary classification
            pred_binary = (predictions > 0.5).astype(int)
            metrics['roc_auc'] = roc_auc_score(labels, predictions)
            metrics['precision'] = precision_score(labels, pred_binary, zero_division=0)
            metrics['recall'] = recall_score(labels, pred_binary, zero_division=0)
            metrics['f1'] = f1_score(labels, pred_binary, zero_division=0)
            metrics['balanced_accuracy'] = balanced_accuracy_score(labels, pred_binary)
        else:
            # Multi-task classification (e.g., Tox21)
            roc_auc_list = []
            for i in range(labels.shape[1]):
                task_labels = labels[:, i]
                task_preds = predictions[:, i]
                is_labeled = (task_labels != -1)
                if is_labeled.sum() > 0:
                    try:
                        roc_auc_list.append(roc_auc_score(task_labels[is_labeled], task_preds[is_labeled]))
                    except:
                        pass
            metrics['mean_roc_auc'] = np.mean(roc_auc_list) if roc_auc_list else 0.0

    else:  # regression
        # Handle missing labels
        is_labeled = (labels != -1).flatten()
        if is_labeled.sum() > 0:
            metrics['mae'] = mean_absolute_error(labels[is_labeled], predictions[is_labeled])
            metrics['rmse'] = root_mean_squared_error(labels[is_labeled], predictions[is_labeled])

    return metrics

def save_results(predictions, smiles_list, labels, metrics, output_path, task_type, task_name):
    """Save inference results to file"""
    results = []

    for i, (pred, smiles) in enumerate(zip(predictions, smiles_list)):
        result = {'smiles': smiles}

        if task_type == 'classification':
            if task_name == 'BBBP':
                result['prediction_probability'] = pred[0]
                result['prediction_class'] = 1 if pred[0] > 0.5 else 0
            else:  # Multi-task
                for j, p in enumerate(pred):
                    result[f'prediction_{j}'] = p
        else:  # regression
            result['prediction'] = pred[0] if len(pred) == 1 else pred

        # Add ground truth if available
        if labels is not None and len(labels) > 0:
            if task_type == 'classification':
                if task_name == 'BBBP':
                    result['true_label'] = labels[i][0] if len(labels[i]) > 0 else None
                else:
                    for j, true_val in enumerate(labels[i]):
                        result[f'true_label_{j}'] = true_val
            else:
                result['true_label'] = labels[i][0] if len(labels[i]) > 0 else None

        results.append(result)

    # Create DataFrame and save
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)

    # Save metrics to separate file if available
    if metrics:
        metrics_path = output_path.replace('.csv', '_metrics.txt')
        with open(metrics_path, 'w', encoding='utf-8') as f:
            f.write("Performance Metrics\n")
            f.write("=" * 20 + "\n")
            for key, value in metrics.items():
                f.write(f"{key}: {value:.4f}\n")
        print(f"Metrics saved to {metrics_path}")

    print(f"Results saved to {output_path}")
    print(f"Processed {len(results)} molecules")

    # Print metrics
    if metrics:
        print("\nPerformance Metrics:")
        for key, value in metrics.items():
            print(f"{key}: {value:.4f}")

    return df

def main():
    parser = argparse.ArgumentParser(description='ADMET Model Inference')
    parser.add_argument('--model_path', type=str, required=True,
                       help='Path to trained model checkpoint (.pth file)')
    parser.add_argument('--data_path', type=str, required=True,
                       help='Path to input data CSV file')
    parser.add_argument('--task_name', type=str, required=True,
                       choices=['BBBP', 'caco2', 'clearance', 'HLM_CLint', 'tox21'],
                       help='ADMET task name')
    parser.add_argument('--output', type=str, default='inference_results.csv',
                       help='Output CSV file path')
    parser.add_argument('--config', type=str, default='config_finetune.yaml',
                       help='Configuration file path')
    parser.add_argument('--batch_size', type=int, default=32,
                       help='Batch size for inference')
    parser.add_argument('--gpu', type=str, default='cuda:0',
                       help='GPU device to use')

    args = parser.parse_args()

    # Create results folder structure
    results_base_dir = 'results'
    os.makedirs(results_base_dir, exist_ok=True)

    # Create timestamped subfolder for this run
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    task_name = args.task_name.lower()
    results_dir = os.path.join(results_base_dir, f'{task_name}_{timestamp}')
    os.makedirs(results_dir, exist_ok=True)

    # Update output path to use the results folder
    if args.output == 'inference_results.csv':  # default value
        args.output = os.path.join(results_dir, f'{task_name}_predictions.csv')
    else:
        # If custom output path provided, place it in results folder
        args.output = os.path.join(results_dir, os.path.basename(args.output))

    print(f"📁 Results will be saved to: {results_dir}")

    # Setup device
    device = torch.device(args.gpu if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    # Load and setup configuration
    config = load_config(args.config)
    config = setup_task_config(config, args.task_name)
    config['batch_size'] = args.batch_size
    config['gpu'] = args.gpu

    print(f"Running inference for task: {args.task_name}")
    print(f"Model: {args.model_path}")
    print(f"Data: {args.data_path}")

    # Load model
    model = load_model(args.model_path, config, device)

    # Create inference dataset
    print("Loading data...")
    dataset = create_inference_dataset(args.data_path, config)
    dataloader = GeoDataLoader(dataset, batch_size=config['batch_size'], shuffle=False)

    # Run inference
    print("Running inference...")
    predictions, labels, smiles_list = run_inference(model, dataloader, device, config['dataset']['task'])

    # Calculate metrics if labels available
    metrics = calculate_metrics(predictions, labels, config['dataset']['task'], args.task_name)

    # Save results
    save_results(predictions, smiles_list, labels, metrics, args.output,
                config['dataset']['task'], args.task_name)

    print("✅ Inference completed successfully!")

if __name__ == "__main__":
    main()