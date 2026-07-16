#!/usr/bin/env python3
"""
Free Colab Setup Script (v2-foundation-arch)
============================================

Installs required packages for Colab.
Run this first cell in Colab.

!git clone your-repo
!pip install torch-geometric transformers optuna rdkit-pypi deepchem
"""

# Install commands for Colab
INSTALL_CMDS = '''
# Cell 1: Setup
!pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118

!pip install torch-geometric -f https://data.pyg.org/whl/torch-2.1.0+cu118.html

!pip install transformers==4.40.0 optuna rdkit-pypi deepchem==2.8.0

# Cell 2: Mount Drive
from google.colab import drive
drive.mount('/content/drive')

# Cell 3: Training
!python v2-foundation-arch/experiments/training/train_colab_free.py --mode pretrain --checkpoint_dir '/content/drive/MyDrive/denovo_checkpoints'
'''

# Reduced batch sizes for 6-16GB VRAM
COLAB_CONFIGS = {
    'batch_size': 8,      # Instead of 64
    'accum_steps': 4,     # Gradient accumulation
    'max_epochs': 200,    # More epochs, smaller batches
    'lr': 5e-5,           # Lower learning rate
    'grad_ckpt': True,    # Gradient checkpointing
}

print("Free Colab Setup Ready")
print("Copy INSTALL_CMDS to Colab cells")