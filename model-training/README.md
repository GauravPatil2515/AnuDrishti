# 🧠 Model Training Pipeline

Complete pipeline for training molecular toxicity prediction models with high accuracy.

## 📋 Overview

This directory contains everything needed to train production-grade toxicity prediction models:

- **Data Management**: Download, preprocess, and manage training data
- **Feature Engineering**: Extract molecular descriptors using RDKit
- **Model Training**: Train XGBoost models with hyperparameter optimization
- **Evaluation**: Comprehensive model evaluation and validation
- **Deployment**: Export trained models for production use

## 🗂️ Directory Structure

```
model-training/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
│
├── data/                        # Training data
│   ├── raw/                     # Raw downloaded data
│   ├── processed/               # Preprocessed data
│   └── README.md                # Data documentation
│
├── notebooks/                   # Jupyter notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   └── 03_model_evaluation.ipynb
│
├── scripts/                     # Training scripts
│   ├── download_data.py         # Download Tox21/ToxCast
│   ├── preprocess_data.py       # Data preprocessing
│   ├── train_models.py          # Model training
│   └── evaluate_models.py       # Model evaluation
│
├── trained_models/              # Output models
│   ├── latest/                  # Latest trained models
│   └── v1.0/                    # Versioned models
│
└── logs/                        # Training logs
    └── training_history.json
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd model-training
pip install -r requirements.txt
```

### 2. Download Training Data

```bash
# Download Tox21 dataset
python scripts/download_data.py --dataset tox21 --output data/raw/

# Or manually download from:
# https://tripod.nih.gov/tox21/challenge/
```

### 3. Preprocess Data

```bash
# Convert and preprocess data
python scripts/preprocess_data.py \
  --input data/raw/tox21_10k_data_all.sdf \
  --output data/processed/tox21_data.csv
```

### 4. Train Models

```bash
# Train all 12 endpoints
python scripts/train_models.py \
  --data data/processed/tox21_data.csv \
  --output trained_models/latest/

# Train specific endpoints
python scripts/train_models.py \
  --data data/processed/tox21_data.csv \
  --output trained_models/latest/ \
  --endpoints NR-AR NR-AhR SR-MMP
```

### 5. Evaluate Models

```bash
# Evaluate trained models
python scripts/evaluate_models.py \
  --models trained_models/latest/best_optimized_models.pkl \
  --test data/processed/test_set.csv
```

### 6. Deploy to Production

```bash
# Copy trained models to backend
cp trained_models/latest/best_optimized_models.pkl ../backend/models/
```

## 📊 Expected Results

### Training Time

- **Per Endpoint**: 10-15 minutes
- **All 12 Endpoints**: 2-3 hours
- **With Optimization**: 4-6 hours

### Performance Metrics

| Endpoint | Target ROC-AUC | Expected Precision | Expected Recall |
|----------|----------------|-------------------|-----------------|
| NR-AR | 0.85+ | 0.78+ | 0.72+ |
| NR-AR-LBD | 0.90+ | 0.85+ | 0.81+ |
| NR-AhR | 0.85+ | 0.80+ | 0.78+ |
| NR-ER-LBD | 0.88+ | 0.82+ | 0.80+ |
| SR-MMP | 0.82+ | 0.75+ | 0.71+ |
| NR-ER | 0.87+ | 0.81+ | 0.78+ |
| NR-PPAR-gamma | 0.83+ | 0.77+ | 0.73+ |
| SR-ARE | 0.80+ | 0.72+ | 0.70+ |
| SR-ATAD5 | 0.82+ | 0.75+ | 0.72+ |
| SR-HSE | 0.81+ | 0.73+ | 0.71+ |
| SR-p53 | 0.84+ | 0.78+ | 0.75+ |
| NR-Aromatase | 0.85+ | 0.79+ | 0.76+ |

**Average**: ROC-AUC 0.84+, Precision 0.78+, Recall 0.75+

## 🔬 Data Sources

### Primary: Tox21 Dataset

- **Source**: <https://tripod.nih.gov/tox21/challenge/>
- **Size**: ~12,000 compounds
- **Endpoints**: 12 toxicity assays
- **Quality**: High-quality, experimentally validated

### Secondary: ToxCast

- **Source**: <https://www.epa.gov/chemical-research/toxicity-forecaster-toxcasttm-data>
- **Size**: ~9,000 compounds
- **Endpoints**: 700+ assays
- **Quality**: EPA-validated

### Augmentation: ChEMBL

- **Source**: <https://www.ebi.ac.uk/chembl/>
- **Size**: 2M+ compounds (filtered subset)
- **Quality**: Curated pharmaceutical data

## 🛠️ Advanced Usage

### Hyperparameter Optimization

```bash
# Use Optuna for hyperparameter tuning
python scripts/train_models.py \
  --data data/processed/tox21_data.csv \
  --output trained_models/optimized/ \
  --optimize \
  --n-trials 100
```

### Custom Feature Engineering

```python
# Edit scripts/train_models.py
feature_extractor = FeatureExtractor(
    use_rdkit=True,        # RDKit descriptors
    use_morgan=True,       # Morgan fingerprints
    use_chembert=True,     # ChemBERT embeddings (slower)
    morgan_radius=3,       # Fingerprint radius
    morgan_bits=4096       # Fingerprint size
)
```

### Ensemble Models

```python
# Combine multiple models
from sklearn.ensemble import VotingClassifier

ensemble = VotingClassifier([
    ('xgb', xgb_model),
    ('rf', rf_model),
    ('lgb', lgb_model)
], voting='soft')
```

## 📈 Monitoring

### Training Progress

```bash
# View training logs
tail -f logs/training_history.json

# View tensorboard (if enabled)
tensorboard --logdir logs/tensorboard
```

### Model Performance

```bash
# Compare model versions
python scripts/compare_models.py \
  --model1 trained_models/v1.0/best_optimized_models.pkl \
  --model2 trained_models/v2.0/best_optimized_models.pkl
```

## 🐛 Troubleshooting

### Issue: RDKit Installation Fails

```bash
# Try conda instead
conda install -c conda-forge rdkit

# Or use system package
# Ubuntu: sudo apt-get install python3-rdkit
# macOS: brew install rdkit
```

### Issue: Out of Memory

```bash
# Reduce batch size
python scripts/train_models.py --batch-size 16

# Or reduce Morgan fingerprint size
python scripts/train_models.py --morgan-bits 1024
```

### Issue: Training Too Slow

```bash
# Use GPU acceleration (if available)
python scripts/train_models.py --device cuda

# Or reduce number of estimators
python scripts/train_models.py --n-estimators 200
```

## 📚 Additional Resources

- **[Model Training Guide](../docs/training/MODEL_TRAINING_GUIDE.md)** - Comprehensive guide
- **[Training Quickstart](../docs/training/TRAINING_QUICKSTART.md)** - Quick reference
- **[RDKit Documentation](https://www.rdkit.org/docs/)** - RDKit reference
- **[XGBoost Documentation](https://xgboost.readthedocs.io/)** - XGBoost reference

## 🤝 Contributing

When adding new training features:

1. Update this README
2. Add tests for new functionality
3. Document hyperparameters
4. Update training scripts
5. Add example notebooks

## 📄 License

Same as main project (MIT License)

---

**Last Updated**: 2025-12-09  
**Version**: 1.0  
**Status**: Production Ready
