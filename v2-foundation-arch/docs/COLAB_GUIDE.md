# Free Colab Training Guide

## Quick Start on Colab

### Cell 1: Setup
```python
!pip install torch==2.1.0 torch-geometric transformers optuna deepchem==2.8.0 rdkit-pypi

from google.colab import drive
drive.mount('/content/drive')
```

### Cell 2: Clone Repository
```python
!git clone https://github.com/GauravPatil2515/Faithful-LLM-Augmented-Explainability-for-Graph-Neural-Network-Based-Molecular-Toxicity-Prediction
%cd Faithful-LLM-Augmented-Explainability-for-Graph-Neural-Network-Based-Molecular-Toxicity-Prediction
```

### Cell 3-4: Pretraining (2 sessions)
```python
# Session 3-4: GraphMAE pretraining
!python v2-foundation-arch/experiments/training/train_colab_free.py --mode pretrain --epochs 50 --batch_size 8 --checkpoint_dir '/content/drive/MyDrive/checkpoints'
```

### Cell 5-7: Fine-tuning (3 sessions)
```python
# Session 5-7: Fine-tune on MoleculeNet
!python v2-foundation-arch/experiments/training/train_colab_free.py --mode train --epochs 100 --batch_size 8 --checkpoint_dir '/content/drive/MyDrive/checkpoints'
```

### Cell 8-9: Optuna search (2 sessions)
```python
# Session 8-9: Hyperparameter search
!python v2-foundation-arch/experiments/optuna_search/optuna_integration.py
```

## Expected Timeline (Free Colab)

| Session | Phase | Time | Output |
|---------|-------|------|--------|
| 1 | Setup | 10 min | Environment ready |
| 2-4 | Pretraining | 3 × 12h = 36h | checkpoint_epoch50.pt |
| 5-7 | Fine-tuning | 3 × 12h = 36h | model_final.pt |
| 8-9 | Optuna | 2 × 12h = 24h | best_params.json |
| **Total** | | **~100 hours** | **~5 days** |

## Important Notes
- Save checkpoints every 8 hours to Google Drive
- Training is split across multiple Colab sessions
- Each session starts from last checkpoint
- Total estimated: **5-7 days** on Free Colab