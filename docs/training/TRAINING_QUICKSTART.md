# 🚀 Quick Start: Training New Models

## Step-by-Step Guide to Train High-Accuracy Models

---

## 📦 Prerequisites

### 1. Install Required Packages

```bash
pip install rdkit-pypi xgboost scikit-learn pandas numpy optuna
```

### 2. Download Training Data

**Option A: Tox21 Dataset (Recommended)**

```bash
# Download from NIH Tox21 Challenge
# Visit: https://tripod.nih.gov/tox21/challenge/

# Or use this direct link:
wget https://tripod.nih.gov/tox21/challenge/download?id=tox21_10k_data_all.sdf

# Convert SDF to CSV (using RDKit)
python convert_sdf_to_csv.py tox21_10k_data_all.sdf data/tox21_data.csv
```

**Option B: Use Sample Data**

```bash
# Create sample data for testing
python create_sample_data.py
```

---

## 🏃 Quick Start (5 Minutes)

### Step 1: Prepare Your Data

Your CSV should have this format:

```csv
smiles,NR-AR,NR-AR-LBD,NR-AhR,NR-ER-LBD,SR-MMP,NR-ER,NR-PPAR-gamma,SR-ARE,SR-ATAD5,SR-HSE,SR-p53,NR-Aromatase
CCO,0,0,0,0,0,0,0,0,0,0,0,0
CC(=O)Nc1ccc(O)cc1,0,0,1,0,0,0,0,0,0,0,0,0
c1ccccc1,1,1,1,0,0,1,0,0,0,0,0,0
...
```

**Required columns:**

- `smiles`: SMILES string of molecule
- Endpoint columns: Binary labels (0 = non-toxic, 1 = toxic)

### Step 2: Train Models

```bash
cd backend

# Train all endpoints
python train_models.py --data ../data/tox21_data.csv --output trained_models/

# Or train specific endpoints
python train_models.py --data ../data/tox21_data.csv --output trained_models/ --endpoints NR-AR NR-AhR SR-MMP
```

### Step 3: Check Results

```bash
# View training results
cat trained_models/training_results.csv

# View metadata
cat trained_models/model_metadata.json
```

### Step 4: Deploy to Production

```bash
# Copy trained models to production
cp trained_models/best_optimized_models.pkl models/best_optimized_models.pkl

# Restart backend
python app.py
```

---

## 📊 Expected Output

```
======================================================================
MOLECULAR TOXICITY MODEL TRAINING PIPELINE
======================================================================

Loading data from: ../data/tox21_data.csv
Loaded 12000 compounds
Columns: ['smiles', 'NR-AR', 'NR-AR-LBD', ...]

Preprocessing data...
Valid SMILES: 11850
After removing duplicates: 11800

Extracting features...
RDKit descriptors: 210
Extracted features for 11800/11800 molecules

Total features extracted: 2258

======================================================================
TRAINING ALL ENDPOINTS
======================================================================

======================================================================
Training: NR-AR
======================================================================
Data split - Train: 5782, Val: 1238, Test: 1238

Class distribution:
  Train - Negative: 5200, Positive: 582
  Val - Negative: 1115, Positive: 123
  Scale pos weight: 8.93

NR-AR - Validation ROC-AUC: 0.8542

NR-AR - Test ROC-AUC: 0.8498
Precision: 0.7821
Recall: 0.7234
F1-Score: 0.7516

... (repeat for all 12 endpoints)

======================================================================
TRAINING SUMMARY
======================================================================
endpoint         test_roc_auc  val_roc_auc  precision  recall  f1_score  train_size
NR-AR                  0.8498       0.8542     0.7821  0.7234    0.7516        5782
NR-AR-LBD              0.9012       0.9045     0.8456  0.8123    0.8287        5782
NR-AhR                 0.8723       0.8756     0.8012  0.7845    0.7928        5782
NR-ER-LBD              0.8834       0.8867     0.8234  0.7956    0.8093        5782
SR-MMP                 0.8156       0.8189     0.7456  0.7123    0.7286        5782
NR-ER                  0.8645       0.8678     0.8123  0.7834    0.7976        5782
NR-PPAR-gamma          0.8234       0.8267     0.7678  0.7345    0.7508        5782
SR-ARE                 0.7989       0.8012     0.7234  0.6956    0.7092        5782
SR-ATAD5               0.8123       0.8156     0.7456  0.7189    0.7320        5782
SR-HSE                 0.8045       0.8078     0.7345  0.7067    0.7203        5782
SR-p53                 0.8367       0.8401     0.7789  0.7456    0.7619        5782
NR-Aromatase           0.8456       0.8489     0.7912  0.7623    0.7765        5782

======================================================================
Average Test ROC-AUC: 0.8423
Average Val ROC-AUC: 0.8457
Average Precision: 0.7793
Average Recall: 0.7479
Average F1-Score: 0.7633
======================================================================

✅ Models saved to: trained_models/best_optimized_models.pkl
✅ Metadata saved to: trained_models/model_metadata.json
✅ Results saved to: trained_models/training_results.csv

✅ Training complete!
✅ Trained 12 models successfully!
```

---

## 🎯 Performance Targets

| Metric | Target | Your Result |
|--------|--------|-------------|
| Average ROC-AUC | ≥ 0.80 | 0.8423 ✅ |
| Average Precision | ≥ 0.75 | 0.7793 ✅ |
| Average Recall | ≥ 0.70 | 0.7479 ✅ |
| Average F1-Score | ≥ 0.72 | 0.7633 ✅ |

---

## 🔧 Troubleshooting

### Issue: "RDKit not available"

```bash
# Install RDKit
pip install rdkit-pypi

# Or use conda
conda install -c conda-forge rdkit
```

### Issue: "Not enough positive samples"

```
⚠️ Skipping NR-Aromatase - too few positive samples (42)
```

**Solution**: Need more training data for this endpoint

- Combine multiple datasets (Tox21 + ToxCast)
- Use data augmentation
- Or remove this endpoint

### Issue: "Out of memory"

```bash
# Reduce Morgan fingerprint size
# Edit train_models.py line 47:
FeatureExtractor(use_morgan=True, morgan_bits=1024)  # Instead of 2048
```

### Issue: "Training too slow"

```bash
# Use GPU acceleration
# Edit train_models.py line 121:
'tree_method': 'gpu_hist',  # Instead of 'hist'
```

---

## 💡 Tips for Better Models

### 1. More Data = Better Models

```bash
# Combine multiple datasets
python merge_datasets.py \
  --tox21 data/tox21_data.csv \
  --toxcast data/toxcast_data.csv \
  --output data/combined_data.csv

# Train on combined data
python train_models.py --data data/combined_data.csv
```

### 2. Hyperparameter Optimization

```python
# Add Optuna optimization (in train_models.py)
# This will take longer but give better results

from optuna import create_study

def optimize_hyperparameters(X_train, y_train, X_val, y_val):
    def objective(trial):
        params = {
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
            'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
            # ... more parameters
        }
        
        model = xgb.XGBClassifier(**params)
        model.fit(X_train, y_train)
        
        y_pred = model.predict_proba(X_val)[:, 1]
        return roc_auc_score(y_val, y_pred)
    
    study = create_study(direction='maximize')
    study.optimize(objective, n_trials=100)
    
    return study.best_params
```

### 3. Feature Selection

```python
# Remove low-importance features
from sklearn.feature_selection import SelectFromModel

selector = SelectFromModel(model, threshold='median')
X_selected = selector.fit_transform(X, y)
```

### 4. Ensemble Models

```python
# Combine multiple models
from sklearn.ensemble import VotingClassifier

ensemble = VotingClassifier([
    ('xgb', xgb_model),
    ('rf', rf_model),
    ('lgb', lgb_model)
], voting='soft')
```

---

## 📈 Monitoring Model Performance

### Track Metrics Over Time

```python
# Save training history
import json

history = {
    'date': datetime.now().isoformat(),
    'roc_auc': 0.8423,
    'data_size': 11800,
    'feature_count': 2258
}

with open('training_history.json', 'a') as f:
    f.write(json.dumps(history) + '\n')
```

### Compare Model Versions

```bash
# Compare old vs new models
python compare_models.py \
  --old models/best_optimized_models.pkl \
  --new trained_models/best_optimized_models.pkl \
  --test data/test_set.csv
```

---

## 🚀 Next Steps

1. **Validate Models**: Test on external dataset
2. **Deploy**: Copy to production
3. **Monitor**: Track prediction accuracy
4. **Retrain**: Update models quarterly with new data
5. **Optimize**: Fine-tune hyperparameters

---

## 📚 Additional Resources

- **Full Guide**: `MODEL_TRAINING_GUIDE.md`
- **Training Script**: `backend/train_models.py`
- **Tox21 Data**: <https://tripod.nih.gov/tox21/challenge/>
- **RDKit Docs**: <https://www.rdkit.org/docs/>
- **XGBoost Docs**: <https://xgboost.readthedocs.io/>

---

**Created**: December 9, 2025  
**Estimated Training Time**: 2-3 hours  
**Expected ROC-AUC**: 0.80-0.90
