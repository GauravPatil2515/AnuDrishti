#!/usr/bin/env python3
"""
Colab Notebook Script - Copy/Paste into Colab cells
===============================================

This is the EXACT code you need to run in Google Colab.
Each cell marked for periodic execution.

Remedy for laptop shutdowns: All checkpoints save to Google Drive.
"""

# CELL 1: Install Dependencies
INSTALL_CELL = '''
# Install PyTorch 2.x with CUDA
!pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cu118

# Install PyTorch Geometric (CRITICAL - exact version match)
!pip install torch-geometric -f https://data.pyg.org/whl/torch-2.1.0+cu118.html

# Install remaining packages
!pip install transformers==4.40.0 optuna==3.6.1 rdkit-pypi deepchem==2.8.0

# Verify CUDA availability
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
'''

# CELL 2: Mount Drive + Clone Repo
MOUNT_CELL = '''
from google.colab import drive
drive.mount('/content/drive')

# Clone repository
!git clone https://github.com/GauravPatil2515/Faithful-LLM-Augmented-Explainability-for-Graph-Neural-Network-Based-Molecular-Toxicity-Prediction
%cd "Faithful-LLM-Augmented-Explainability-for-Graph-Neural-Network-Based-Molecular-Toxicity-Prediction"
'''

# CELL 3-4: SMILES Pretraining (2 sessions, 12h each)
PRETRAIN_CELL = '''
# SMILES-only pretraining for Free Colab
# Reduces VRAM to 8GB (fits T4/K80)

!python v2-foundation-arch/experiments/training/train_colab_free.py \\
    --mode pretrain \\
    --epochs 50 \\
    --batch_size 8 \\
    --checkpoint_dir "/content/drive/MyDrive/denovo_checkpoints"

# Output saved to: /content/drive/MyDrive/denovo_checkpoints/
'''

# CELL 5-7: Multimodal Training (3 sessions, 12h each)
TRAIN_CELL = '''
# Multi-task training on MoleculeNet
# Loads pretrained weights if available

!python v2-foundation-arch/experiments/training/train_colab_free.py \\
    --mode train \\
    --epochs 100 \\
    --batch_size 8 \\
    --checkpoint_dir "/content/drive/MyDrive/denovo_checkpoints"
'''

# CELL 8-9: Optuna Search (2 sessions)
OPTUNA_CELL = '''
# Hyperparameter optimization

!python v2-foundation-arch/experiments/optuna_search/optuna_integration.py
'''

# RESUME SCRIPT (for after laptop shutdown)
RESUME_SCRIPT = '''
# Resume training from last checkpoint
# Run this after reconnecting - finds latest epoch

import torch
from pathlib import Path

ckpt_dir = Path("/content/drive/MyDrive/denovo_checkpoints")
checkpoints = sorted(ckpt_dir.glob("checkpoint_epoch*.pt"))

if checkpoints:
    latest = checkpoints[-1]
    print(f"Resuming from: {latest}")
    # Training script will auto-load this
else:
    print("No checkpoint found - starting fresh")
'''

print("Copy each CELL_* into a separate Colab cell")
print("Checkpoints saved to: /content/drive/MyDrive/denovo_checkpoints/")
print("Resume automatically - script loads latest checkpoint")