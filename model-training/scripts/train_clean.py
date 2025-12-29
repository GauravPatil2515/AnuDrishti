#!/usr/bin/env python3
"""
Optimized Model Training Pipeline
==================================
Clean training with progress tracking and no warnings
"""

import warnings
warnings.filterwarnings('ignore')

import os
os.environ['PYTHONWARNINGS'] = 'ignore'

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
import xgboost as xgb
from sklearn.metrics import roc_auc_score
import pickle
import json
from datetime import datetime
from tqdm import tqdm

# RDKit with warnings suppressed
from rdkit import Chem, RDLogger
RDLogger.DisableLog('rdApp.*')
from rdkit.Chem import Descriptors, AllChem

print("="*70)
print("OPTIMIZED MODEL TRAINING PIPELINE")
print("="*70)

# Load data
print("\n📊 Loading dataset...")
df = pd.read_csv('data/raw/tox21.csv')
print(f"✅ Loaded {len(df):,} samples")

# Find SMILES column
smiles_col = df.columns[-1]
print(f"✅ SMILES column: {smiles_col}")

# Endpoints
endpoints = ['NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-Aromatase', 'NR-ER', 'NR-ER-LBD', 
             'NR-PPAR-gamma', 'SR-ARE', 'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53']

# Validate SMILES
print("\n🔍 Validating SMILES...")
valid_idx = []
for i in tqdm(range(len(df)), desc="Validating"):
    mol = Chem.MolFromSmiles(str(df[smiles_col].iloc[i]))
    if mol is not None:
        valid_idx.append(i)

df = df.iloc[valid_idx].reset_index(drop=True)
print(f"✅ Valid: {len(df):,} molecules")

# Remove duplicates
df = df.drop_duplicates(subset=[smiles_col]).reset_index(drop=True)
print(f"✅ Unique: {len(df):,} molecules")

# Feature extraction
print("\n🔬 Extracting features...")

def extract_features_fast(smiles):
    """Fast feature extraction"""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    features = []
    
    # Top 50 RDKit descriptors
    for name, func in Descriptors.descList[:50]:
        try:
            features.append(func(mol))
        except:
            features.append(0)
    
    # Morgan fingerprint (256-bit for speed)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=256)
    features.extend([int(fp[i]) for i in range(256)])
    
    return features

features_list = []
for smiles in tqdm(df[smiles_col], desc="Features"):
    feat = extract_features_fast(str(smiles))
    if feat:
        features_list.append(feat)

X = pd.DataFrame(features_list).fillna(0)

# Clean data: replace inf with large values and ensure no NaN
X = X.replace([np.inf, -np.inf], np.nan)
X = X.fillna(0)

# Ensure all values are finite
X = X.clip(-1e10, 1e10)

print(f"✅ Features: {X.shape[1]} per molecule")

# Train models
print("\n🤖 Training models...")
all_models = {}
results = []

for endpoint in endpoints:
    if endpoint not in df.columns:
        continue
    
    print(f"\n{'='*70}")
    print(f"Training: {endpoint}")
    
    # Get labels
    y = df[endpoint].values
    valid_mask = ~pd.isna(y)
    X_valid = X[valid_mask]
    y_valid = y[valid_mask].astype(int)
    
    if len(y_valid) < 100 or y_valid.sum() < 10:
        print(f"⚠️  Skipped - insufficient data")
        continue
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_valid, y_valid, test_size=0.2, random_state=42, stratify=y_valid
    )
    
    print(f"   Train: {len(X_train):,} | Test: {len(X_test):,}")
    print(f"   Positive: {y_train.sum():,} ({y_train.mean()*100:.1f}%)")
    
    # Train XGBoost
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=float(scale_pos_weight) if scale_pos_weight != np.inf else 1.0,
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    print("   Training...", end=" ")
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict_proba(X_test)[:, 1]
    roc_auc = roc_auc_score(y_test, y_pred)
    
    print(f"✅ ROC-AUC: {roc_auc:.4f}")
    
    all_models[endpoint] = {
        'model': model,
        'roc_auc': roc_auc,
        'endpoint': endpoint,
        'trained_at': datetime.now().isoformat()
    }
    
    results.append({
        'endpoint': endpoint,
        'roc_auc': roc_auc,
        'train_size': len(X_train)
    })

# Save models
print("\n💾 Saving models...")
output_dir = Path('trained_models/latest')
output_dir.mkdir(parents=True, exist_ok=True)

with open(output_dir / 'best_optimized_models.pkl', 'wb') as f:
    pickle.dump(all_models, f)

# Save results
results_df = pd.DataFrame(results)
results_df.to_csv(output_dir / 'training_results.csv', index=False)

# Save metadata
metadata = {
    'trained_at': datetime.now().isoformat(),
    'total_samples': len(df),
    'feature_count': X.shape[1],
    'models_trained': len(all_models),
    'average_roc_auc': results_df['roc_auc'].mean()
}

with open(output_dir / 'metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print("\n" + "="*70)
print("✅ TRAINING COMPLETE!")
print("="*70)
print(f"\nModels trained: {len(all_models)}")
print(f"Average ROC-AUC: {results_df['roc_auc'].mean():.4f}")
print(f"Saved to: {output_dir}")
print(f"\n{results_df.to_string(index=False)}")
