#!/usr/bin/env python3
"""
Training Script for Attention-GIN Model
========================================
Fine-tunes the Attention-GIN model for explainable toxicity prediction.
Supports transfer learning from pre-trained GINet weights.

Paper: DeNovo-XAI: Interpretable Molecular Toxicity Prediction through
       LLM-Augmented Graph Neural Networks

Features:
- Transfer learning from pre-trained GINet
- Attention layer training with frozen/unfrozen encoder
- Multi-task learning for all 12 Tox21 endpoints
- Early stopping with validation-based model selection
- TensorBoard logging for experiment tracking
- Checkpoint saving with attention weight analysis

Author: DeNovo-XAI Research Team
"""

import os
import sys
import yaml
import argparse
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
import json

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import Adam, AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR, ReduceLROnPlateau

from torch_geometric.loader import DataLoader
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AttentionGINTrainer')

# Add project paths
SCRIPT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent
MODELS_DIR = PROJECT_DIR / "MODELS"

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(BACKEND_DIR / 'models'))


# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_CONFIG = {
    # Model architecture
    'model': {
        'num_layer': 5,
        'emb_dim': 300,
        'feat_dim': 512,
        'drop_ratio': 0.2,      # Reduced for better learning
        'pred_n_layer': 2,
        'pred_act': 'softplus',
        'pool': 'attention'
    },
    
    # Training parameters - OPTIMIZED for ROC-AUC >= 0.82
    'training': {
        'batch_size': 32,       # Smaller batch for better generalization
        'epochs': 150,          # More epochs
        'learning_rate': 1e-4,  # Base encoder LR
        'attention_lr': 5e-4,   # Higher LR for attention layer
        'weight_decay': 1e-6,
        'patience': 50,         # High patience for convergence
        'min_delta': 1e-4,
        'grad_clip': 1.0,
        'use_focal_loss': True, # Enable focal loss for class imbalance (specifically ClinTox)
        'focal_loss_gamma': 2.0  # Gamma parameter for focal loss
    },
    
    # Transfer learning
        'transfer': {
            'freeze_encoder': False,
            'freeze_epochs': 0,
            'pretrained_path': './pretrained/gin_supervised_masking.pth',
            'load_prediction_head': False
        },

        # Data - Use scaffold split for better generalization
        'data': {
            'train_split': 0.8,
            'val_split': 0.1,
            'test_split': 0.1,
            'scaffold_split': True,   # Scaffold split for better generalization
            'random_seed': 42
        },

        # Logging
    'logging': {
        'log_interval': 50,
        'save_attention_maps': True,
        'tensorboard': True
    }
}


class EarlyStopping:
    """Early stopping to prevent overfitting."""
    
    def __init__(self, patience: int = 15, min_delta: float = 1e-4, mode: str = 'max'):
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        self.best_epoch = 0
    
    def __call__(self, score: float, epoch: int) -> bool:
        if self.best_score is None:
            self.best_score = score
            self.best_epoch = epoch
            return False
        
        if self.mode == 'max':
            improved = score > self.best_score + self.min_delta
        else:
            improved = score < self.best_score - self.min_delta
        
        if improved:
            self.best_score = score
            self.best_epoch = epoch
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        
        return self.early_stop


class AttentionGINTrainer:
    """
    Trainer for Attention-GIN model.
    Handles the complete training pipeline including:
    - Data loading and preprocessing
    - Model initialization and transfer learning
    - Training loop with validation
    - Logging and checkpointing
    - Attention weight analysis
    """
    
    def __init__(
        self,
        config: dict,
        task_name: str = 'tox21',
        output_dir: str = './training_outputs'
    ):
        """
        Initialize trainer.
        
        Args:
            config: Training configuration dictionary
            task_name: Name of the task (tox21, clintox, bbbp, etc.)
            output_dir: Directory for saving outputs
        """
        self.config = config
        self.task_name = task_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")
        
        # Task-specific settings
        self.task_config = self._get_task_config(task_name)
        self.num_tasks = self.task_config['num_tasks']
        self.task_type = self.task_config['task_type']
        
        # Initialize components
        self.model = None
        self.optimizer = None
        self.scheduler = None
        self.train_loader = None
        self.val_loader = None
        self.test_loader = None
        
        # Training state
        self.current_epoch = 0
        self.best_val_score = 0
        self.training_history = []
        
        # Setup TensorBoard
        if config['logging']['tensorboard']:
            try:
                from torch.utils.tensorboard import SummaryWriter
                self.writer = SummaryWriter(self.output_dir / 'tensorboard')
            except ImportError:
                logger.warning("TensorBoard not available")
                self.writer = None
        else:
            self.writer = None
    
    def _get_task_config(self, task_name: str) -> dict:
        """Get task-specific configuration."""
        tasks = {
            'tox21': {
                'num_tasks': 12,
                'task_type': 'classification',
                'target_cols': [
                    "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase",
                    "NR-ER", "NR-ER-LBD", "NR-PPAR-gamma",
                    "SR-ARE", "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53"
                ],
                'data_file': 'tox21.csv',
                'model_path': MODELS_DIR / 'tox21_model_full_package' / 'model.pth'
            },
            'clintox': {
                'num_tasks': 2,
                'task_type': 'classification',
                'target_cols': ['CT_TOX', 'FDA_APPROVED'],
                'data_file': 'clintox.csv',
                'model_path': MODELS_DIR / 'pretrained_gin_ClinTox_model.pth'
            },
            'bbbp': {
                'num_tasks': 1,
                'task_type': 'classification',
                'target_cols': ['p_np'],
                'data_file': 'bbbp.csv',
                'model_path': MODELS_DIR / 'bbbp_model_full_package' / 'model.pth'
            },
            'caco2': {
                'num_tasks': 1,
                'task_type': 'regression',
                'target_cols': ['Y'],
                'data_file': 'caco2.csv',
                'model_path': MODELS_DIR / 'caco2_model_full_package' / 'model.pth'
            }
        }
        
        if task_name not in tasks:
            raise ValueError(f"Unknown task: {task_name}. Available: {list(tasks.keys())}")
        
        return tasks[task_name]
    
    def setup_model(self, pretrained_path: str = None):
        """
        Initialize the Attention-GIN model.
        Optionally loads pre-trained weights.
        """
        from attention_ginet import AttentionGINet
        
        logger.info(f"Initializing Attention-GIN for {self.num_tasks} tasks")
        
        self.model = AttentionGINet(
            task=self.task_type,
            num_layer=self.config['model']['num_layer'],
            emb_dim=self.config['model']['emb_dim'],
            feat_dim=self.config['model']['feat_dim'],
            drop_ratio=self.config['model']['drop_ratio'],
            num_tasks=self.num_tasks,
            pred_n_layer=self.config['model']['pred_n_layer'],
            pred_act=self.config['model']['pred_act'],
            pool=self.config['model'].get('pool', 'attention')
        )
        
        # Load pre-trained weights if available
        pretrained_path = pretrained_path or self.config['transfer'].get('pretrained_path')
        if self.config['transfer'].get('no_load', False) or pretrained_path == 'none':
            logger.info("Training from scratch (explicitly requested).")
        elif pretrained_path and Path(pretrained_path).exists():
            self._load_pretrained_weights(pretrained_path)
        elif self.task_config['model_path'].exists() and not self.config['transfer'].get('no_load', False):
            self._load_pretrained_weights(self.task_config['model_path'])
        else:
            logger.info("No pre-trained weights found. Training from scratch.")
        
        self.model.to(self.device)
        
        # Count parameters
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        logger.info(f"Total parameters: {total_params:,}")
        logger.info(f"Trainable parameters: {trainable_params:,}")
        
        return self.model
    
    def _load_pretrained_weights(self, path: str):
        """Load pre-trained GINet weights into Attention-GIN."""
        logger.info(f"Loading pre-trained weights from: {path}")
        
        try:
            state_dict = torch.load(path, map_location=self.device, weights_only=False)
            loaded, skipped = self.model.load_pretrained_ginet(
                state_dict, 
                strict=False
            )
            logger.info(f"Loaded {len(loaded)} layers, skipped {len(skipped)} layers")
        except Exception as e:
            logger.error(f"Failed to load pre-trained weights: {e}")
    
    def setup_optimizer(self):
        """
        Setup optimizer with separate learning rates for different components.
        Attention layer gets higher learning rate for faster convergence.
        """
        # Separate parameters into groups
        attention_params = []
        encoder_params = []
        pred_head_params = []
        
        for name, param in self.model.named_parameters():
            if 'gate_nn' in name or 'attention' in name:
                attention_params.append(param)
            elif 'pred_head' in name:
                pred_head_params.append(param)
            else:
                encoder_params.append(param)
        
        # Create parameter groups with different learning rates
        param_groups = [
            {
                'params': encoder_params,
                'lr': self.config['training']['learning_rate'],
                'name': 'encoder'
            },
            {
                'params': attention_params,
                'lr': self.config['training']['attention_lr'],
                'name': 'attention'
            },
            {
                'params': pred_head_params,
                'lr': self.config['training']['learning_rate'],
                'name': 'pred_head'
            }
        ]
        
        self.optimizer = AdamW(
            param_groups,
            weight_decay=self.config['training']['weight_decay']
        )
        
        # Learning rate scheduler
        self.scheduler = CosineAnnealingLR(
            self.optimizer,
            T_max=self.config['training']['epochs'],
            eta_min=1e-6
        )
        
        logger.info("Optimizer setup complete")
        logger.info(f"  Encoder LR: {self.config['training']['learning_rate']}")
        logger.info(f"  Attention LR: {self.config['training']['attention_lr']}")
    
    def setup_data(self, data_path: str = None):
        """
        Setup data loaders for training, validation, and testing.
        
        Args:
            data_path: Path to the dataset CSV file
        """
        # Import dataset utilities
        try:
            from dataset.dataset_test import MolTestDatasetWrapper
        except ImportError:
            # Try finding it in MODELS directory
            tox21_path = MODELS_DIR / 'tox21_model_full_package' / 'dataset'
            if tox21_path.exists():
                sys.path.insert(0, str(MODELS_DIR / 'tox21_model_full_package'))
                from dataset.dataset_test import MolTestDatasetWrapper
            else:
                raise ImportError("Cannot find dataset_test module")
        
        # Use default data path if not provided
        if data_path is None:
            if self.task_name == 'tox21':
                data_path = MODELS_DIR / 'tox21_model_full_package' / 'data' / 'tox21' / 'tox21.csv'
            elif self.task_name == 'clintox':
                data_path = MODELS_DIR / 'clintox_model_package' / 'data' / 'clintox' / 'clintox.csv'
            elif self.task_name == 'bbbp':
                data_path = MODELS_DIR / 'bbbp_model_full_package' / 'data' / 'bbbp' / 'bbbp.csv'
            elif self.task_name == 'caco2':
                data_path = MODELS_DIR / 'caco2_model_full_package' / 'data' / 'caco2' / 'caco2.csv'
            else:
                data_path = MODELS_DIR / 'tox21_model_full_package' / 'data' / 'tox21' / 'tox21.csv'
        
        if not Path(data_path).exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")
        
        logger.info(f"Loading data from: {data_path}")
        
        # Create dataset wrapper with positional arguments
        # MolTestDatasetWrapper(batch_size, num_workers, valid_size, test_size, data_path, target, task, splitting)
        wrapper = MolTestDatasetWrapper(
            batch_size=self.config['training']['batch_size'],
            num_workers=2,
            valid_size=self.config['data']['val_split'],
            test_size=self.config['data']['test_split'],
            data_path=str(data_path),
            target=self.task_config['target_cols'],
            task=self.task_type,
            splitting='scaffold' if self.config['data']['scaffold_split'] else 'random'
        )
        
        self.train_loader, self.val_loader, self.test_loader = wrapper.get_data_loaders()
        
        logger.info(f"Data loaded:")
        logger.info(f"  Train: {len(self.train_loader.dataset)} samples")
        logger.info(f"  Val: {len(self.val_loader.dataset)} samples")
        logger.info(f"  Test: {len(self.test_loader.dataset)} samples")
    
    def train_epoch(self) -> dict:
        """
        Train for one epoch.
        
        Returns:
            Dictionary with training metrics
        """
        self.model.train()
        
        total_loss = 0
        n_batches = 0
        all_preds = []
        all_labels = []
        
        for batch_idx, data in enumerate(self.train_loader):
            data = data.to(self.device)
            
            self.optimizer.zero_grad()
            
            # Forward pass with attention
            fp_features = data.fp if hasattr(data, 'fp') else None
            features, predictions, attention_info = self.model(data, return_attention=True, fp_features=fp_features)
            
            # Compute loss
            loss = self._compute_loss(predictions, data.y)
            
            if torch.isnan(loss):
                logger.warning(f"NaN loss at batch {batch_idx}, skipping")
                continue
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping
            if self.config['training']['grad_clip'] > 0:
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(),
                    self.config['training']['grad_clip']
                )
            
            self.optimizer.step()
            
            total_loss += loss.item()
            n_batches += 1
            
            # Store predictions for metrics
            if self.task_type == 'classification':
                preds = torch.sigmoid(predictions).detach().cpu().numpy()
            else:
                preds = predictions.detach().cpu().numpy()
            
            all_preds.append(preds)
            all_labels.append(data.y.detach().cpu().numpy())
            
            # Log progress
            if batch_idx % self.config['logging']['log_interval'] == 0:
                logger.debug(f"Batch {batch_idx}/{len(self.train_loader)}, Loss: {loss.item():.4f}")
        
        # Compute epoch metrics
        avg_loss = total_loss / max(n_batches, 1)
        
        all_preds = np.concatenate(all_preds, axis=0)
        all_labels = np.concatenate(all_labels, axis=0)
        
        metrics = self._compute_metrics(all_preds, all_labels)
        metrics['loss'] = avg_loss
        
        return metrics
    
    def _compute_loss(self, predictions: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """Compute task-appropriate loss with missing value handling, class weighting, and Focal Loss."""
        if self.task_type == 'classification':
            # Compute per-task pos_weight for class imbalance (toxics are usually minority)
            # Calculate based on batch statistics to handle varying batch compositions
            pos_weights = []
            for i in range(self.num_tasks):
                task_labels = labels[:, i] if labels.ndim > 1 else labels
                # Mask out missing labels (-1)
                labeled_mask = task_labels != -1
                if labeled_mask.sum().item() > 0:
                    pos_count = (task_labels[labeled_mask] == 1).sum().float()
                    neg_count = (task_labels[labeled_mask] == 0).sum().float()
                    # Avoid division by zero
                    weight = neg_count / (pos_count + 1e-8)
                    # Cap weight to prevent instability
                    weight = min(weight, 50.0)
                else:
                    # Default weight if no labels in batch
                    weight = 1.0
                pos_weights.append(weight)
            
            pos_weight_tensor = torch.tensor(pos_weights, device=predictions.device, dtype=predictions.dtype)
            criterion = nn.BCEWithLogitsLoss(reduction='none', pos_weight=pos_weight_tensor)
            loss = criterion(predictions, labels.float())
            
            # Apply Focal Loss modulating factor if enabled
            if self.config['training'].get('use_focal_loss', False):
                gamma = self.config['training'].get('focal_loss_gamma', 2.0)
                probs = torch.sigmoid(predictions)
                # modulating factor is (1 - p_t)^gamma
                # where p_t = probs for label=1, and (1 - probs) for label=0
                modulating_factor = (labels.float() - probs).abs().pow(gamma)
                loss = modulating_factor * loss
            
            # Mask out missing labels (-1)
            is_labeled = (labels != -1).float()
            loss = loss * is_labeled
            
            # Average over labeled samples and tasks
            if is_labeled.sum() > 0:
                loss = loss.sum() / is_labeled.sum()
            else:
                loss = torch.tensor(0.0, device=predictions.device)
        else:
            criterion = nn.MSELoss(reduction='none')
            loss = criterion(predictions, labels.float())
            
            is_labeled = (labels != -1).float()
            loss = (loss * is_labeled).sum() / max(is_labeled.sum(), 1)
        return loss
    
    def _compute_metrics(self, predictions: np.ndarray, labels: np.ndarray) -> dict:
        """Compute evaluation metrics."""
        metrics = {}
        
        if self.task_type == 'classification':
            # Compute ROC-AUC for each task
            roc_aucs = []
            
            for i in range(self.num_tasks):
                task_labels = labels[:, i] if labels.ndim > 1 else labels
                task_preds = predictions[:, i] if predictions.ndim > 1 else predictions
                
                # Filter out missing labels
                mask = task_labels != -1
                if mask.sum() > 10:  # Need minimum samples
                    try:
                        roc_auc = roc_auc_score(task_labels[mask], task_preds[mask])
                        roc_aucs.append(roc_auc)
                    except ValueError:
                        pass  # Skip if only one class present
            
            metrics['mean_roc_auc'] = np.mean(roc_aucs) if roc_aucs else 0
            metrics['roc_aucs'] = roc_aucs
        else:
            # Regression metrics
            mask = labels.flatten() != -1
            if mask.sum() > 0:
                mse = np.mean((predictions.flatten()[mask] - labels.flatten()[mask]) ** 2)
                metrics['mse'] = mse
                metrics['rmse'] = np.sqrt(mse)
                metrics['mae'] = np.mean(np.abs(predictions.flatten()[mask] - labels.flatten()[mask]))
        
        return metrics
    
    @torch.no_grad()
    def validate(self) -> dict:
        """
        Evaluate on validation set.
        
        Returns:
            Dictionary with validation metrics
        """
        self.model.eval()
        
        total_loss = 0
        n_batches = 0
        all_preds = []
        all_labels = []
        
        for data in self.val_loader:
            data = data.to(self.device)
            
            fp_features = data.fp if hasattr(data, 'fp') else None
            result = self.model(data, return_attention=False, fp_features=fp_features)
            # Model returns (features, predictions) when return_attention=False
            if len(result) == 2:
                features, predictions = result
            else:
                features, predictions, _ = result
            
            loss = self._compute_loss(predictions, data.y)
            total_loss += loss.item()
            n_batches += 1
            
            if self.task_type == 'classification':
                preds = torch.sigmoid(predictions).cpu().numpy()
            else:
                preds = predictions.cpu().numpy()
            
            all_preds.append(preds)
            all_labels.append(data.y.cpu().numpy())
        
        avg_loss = total_loss / max(n_batches, 1)
        
        all_preds = np.concatenate(all_preds, axis=0)
        all_labels = np.concatenate(all_labels, axis=0)
        
        metrics = self._compute_metrics(all_preds, all_labels)
        metrics['loss'] = avg_loss
        
        return metrics
    
    def save_checkpoint(self, epoch: int, is_best: bool = False):
        """Save model checkpoint."""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'config': self.config,
            'task_name': self.task_name,
            'best_val_score': self.best_val_score
        }
        
        # Save latest
        torch.save(checkpoint, self.output_dir / 'checkpoint_latest.pth')
        
        # Save best
        if is_best:
            torch.save(checkpoint, self.output_dir / 'checkpoint_best.pth')
            # Also save just the model weights
            torch.save(self.model.state_dict(), self.output_dir / 'attention_gin_model.pth')
            logger.info(f"Saved best model at epoch {epoch}")
    
    def train(
        self,
        data_path: str = None,
        pretrained_path: str = None
    ):
        """
        Main training loop.
        
        Args:
            data_path: Path to dataset
            pretrained_path: Path to pre-trained weights
        """
        logger.info("=" * 60)
        logger.info("Starting Attention-GIN Training")
        logger.info("=" * 60)
        
        # Setup
        self.setup_model(pretrained_path)
        self.setup_optimizer()
        self.setup_data(data_path)
        
        # Early stopping
        early_stopping = EarlyStopping(
            patience=self.config['training']['patience'],
            min_delta=self.config['training']['min_delta'],
            mode='max' if self.task_type == 'classification' else 'min'
        )
        
        # Training loop
        for epoch in range(1, self.config['training']['epochs'] + 1):
            self.current_epoch = epoch
            
            # Handle encoder freezing for transfer learning
            if self.config['transfer']['freeze_encoder'] and epoch <= self.config['transfer']['freeze_epochs']:
                self._freeze_encoder(True)
            else:
                self._freeze_encoder(False)
            
            # Train
            train_metrics = self.train_epoch()
            
            # Validate
            val_metrics = self.validate()
            
            # Update scheduler
            self.scheduler.step()
            
            # Get primary metric
            if self.task_type == 'classification':
                val_score = val_metrics['mean_roc_auc']
                score_name = 'ROC-AUC'
            else:
                val_score = -val_metrics['rmse']  # Negative because we want to minimize
                score_name = 'RMSE'
            
            # Check for improvement
            is_best = False
            if self.task_type == 'classification':
                is_best = val_score > self.best_val_score
            else:
                is_best = val_score > self.best_val_score
            
            if is_best:
                self.best_val_score = val_score
            
            # Save checkpoint
            self.save_checkpoint(epoch, is_best)
            
            # Logging
            logger.info(
                f"Epoch {epoch:3d} | "
                f"Train Loss: {train_metrics['loss']:.4f} | "
                f"Val Loss: {val_metrics['loss']:.4f} | "
                f"Val {score_name}: {abs(val_score):.4f}"
                f"{' *' if is_best else ''}"
            )
            
            # TensorBoard logging
            if self.writer:
                self.writer.add_scalar('Loss/train', train_metrics['loss'], epoch)
                self.writer.add_scalar('Loss/val', val_metrics['loss'], epoch)
                self.writer.add_scalar(f'{score_name}/val', abs(val_score), epoch)
                self.writer.add_scalar('LR', self.optimizer.param_groups[0]['lr'], epoch)
            
            # Store history
            self.training_history.append({
                'epoch': epoch,
                'train_loss': train_metrics['loss'],
                'val_loss': val_metrics['loss'],
                'val_score': val_score
            })
            
            # Early stopping
            if early_stopping(val_score, epoch):
                logger.info(f"Early stopping at epoch {epoch}")
                logger.info(f"Best epoch: {early_stopping.best_epoch}")
                break
        
        # Final evaluation on test set
        self._final_evaluation()
        
        # Save training history
        self._save_training_history()
        
        logger.info("Training complete!")
        logger.info(f"Best validation {score_name}: {abs(self.best_val_score):.4f}")
    
    def _freeze_encoder(self, freeze: bool):
        """Freeze or unfreeze the GNN encoder layers."""
        for name, param in self.model.named_parameters():
            if 'gnns' in name or 'batch_norms' in name or 'x_embedding' in name:
                param.requires_grad = not freeze
    
    @torch.no_grad()
    def _final_evaluation(self):
        """Run final evaluation on test set."""
        logger.info("\n" + "=" * 60)
        logger.info("Final Evaluation on Test Set")
        logger.info("=" * 60)
        
        # Load best model
        best_path = self.output_dir / 'checkpoint_best.pth'
        if best_path.exists():
            checkpoint = torch.load(best_path, map_location=self.device, weights_only=False)
            self.model.load_state_dict(checkpoint['model_state_dict'])
        
        self.model.eval()
        
        all_preds = []
        all_labels = []
        all_attention = []
        
        for data in self.test_loader:
            data = data.to(self.device)
            
            fp_features = data.fp if hasattr(data, 'fp') else None
            features, predictions, attention_info = self.model(data, return_attention=True, fp_features=fp_features)
            
            if self.task_type == 'classification':
                preds = torch.sigmoid(predictions).cpu().numpy()
            else:
                preds = predictions.cpu().numpy()
            
            all_preds.append(preds)
            all_labels.append(data.y.cpu().numpy())
            all_attention.append(attention_info['attention_weights'].cpu().numpy())
        
        all_preds = np.concatenate(all_preds, axis=0)
        all_labels = np.concatenate(all_labels, axis=0)
        
        test_metrics = self._compute_metrics(all_preds, all_labels)
        
        logger.info("Test Set Results:")
        for key, value in test_metrics.items():
            if isinstance(value, float):
                logger.info(f"  {key}: {value:.4f}")
        
        # Save test results
        results = {
            'test_metrics': {k: v for k, v in test_metrics.items() if not isinstance(v, list)},
            'config': self.config,
            'task_name': self.task_name
        }
        
        with open(self.output_dir / 'test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
    
    def _save_training_history(self):
        """Save training history to CSV."""
        df = pd.DataFrame(self.training_history)
        df.to_csv(self.output_dir / 'training_history.csv', index=False)


# ═══════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Train Attention-GIN Model')
    
    parser.add_argument('--task', type=str, default='tox21',
                       choices=['tox21', 'clintox', 'bbbp', 'caco2'],
                       help='Task to train on')
    parser.add_argument('--data_path', type=str, default=None,
                       help='Path to dataset CSV')
    parser.add_argument('--pretrained', type=str, default=None,
                       help='Path to pre-trained model')
    parser.add_argument('--output_dir', type=str, default='./training_outputs',
                       help='Output directory')
    parser.add_argument('--epochs', type=int, default=100,
                       help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=64,
                       help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-4,
                       help='Learning rate')
    parser.add_argument('--freeze_encoder', action='store_true',
                       help='Freeze GNN encoder (train only attention)')
    parser.add_argument('--patience', type=int, default=50,
                       help='Early stopping patience')
    parser.add_argument('--no_focal_loss', action='store_true',
                       help='Disable focal loss')
    parser.add_argument('--focal_loss_gamma', type=float, default=2.0,
                       help='Focal loss gamma parameter')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed')
    parser.add_argument('--pool', type=str, default='attention',
                       choices=['attention', 'mean'],
                       help='Pooling type')
    
    args = parser.parse_args()
    
    # Update config with command line args
    config = DEFAULT_CONFIG.copy()
    config['model'] = DEFAULT_CONFIG['model'].copy()
    config['training'] = DEFAULT_CONFIG['training'].copy()
    config['transfer'] = DEFAULT_CONFIG['transfer'].copy()
    config['data'] = DEFAULT_CONFIG['data'].copy()
    config['logging'] = DEFAULT_CONFIG['logging'].copy()
    
    config['training']['epochs'] = args.epochs
    config['training']['batch_size'] = args.batch_size
    config['training']['learning_rate'] = args.lr
    config['transfer']['freeze_encoder'] = args.freeze_encoder
    config['training']['patience'] = args.patience
    config['training']['use_focal_loss'] = not args.no_focal_loss
    config['training']['focal_loss_gamma'] = args.focal_loss_gamma
    config['data']['random_seed'] = args.seed
    config['model']['pool'] = args.pool
    
    if args.pretrained:
        config['transfer']['pretrained_path'] = args.pretrained
    
    # Create output directory with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(args.output_dir) / f'{args.task}_{timestamp}'
    
    # Initialize and run trainer
    trainer = AttentionGINTrainer(
        config=config,
        task_name=args.task,
        output_dir=str(output_dir)
    )
    
    trainer.train(
        data_path=args.data_path,
        pretrained_path=args.pretrained
    )


if __name__ == '__main__':
    main()
