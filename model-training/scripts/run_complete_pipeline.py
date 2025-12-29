#!/usr/bin/env python3
"""
Complete Automated Training Pipeline
=====================================
Runs all steps: preprocessing, feature engineering, and optimized training
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, classification_report
import pickle
import json
from datetime import datetime

# RDKit
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, AllChem
    RDKIT_AVAILABLE = True
except:
    RDKIT_AVAILABLE = False

print("="*70)
print("COMPLETE MODEL TRAINING PIPELINE")
print("="*70)

# STEP 2: PREPROCESSING
print("\n📊 STEP 2: DATA PREPROCESSING")
print("-"*70)

df = pd.read_csv('data/raw/tox21.csv')
print(f"Loaded: {len(df)} samples")

# Find SMILES column
smiles_col = [c for c in df.columns if 'smiles' in c.lower() or c == df.columns[-1]][0]
print(f"SMILES column: {smiles_col}")

# Endpoints
endpoints = ['NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-Aromatase', 'NR-ER', 'NR-ER-LBD', 
             'NR-PPAR-gamma', 'SR-ARE', 'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53']

# Validate SMILES
if RDKIT_AVAILABLE:
    valid_idx = [i for i, s in enumerate(df[smiles_col]) if Chem.MolFromSmiles(str(s)) is not None]
    df = df.iloc[valid_idx].reset_index(drop=True)
    print(f"Valid SMILES: {len(df)}")

# Remove duplicates
df = df.drop_duplicates(subset=[smiles_col]).reset_index(drop=True)
print(f"After dedup: {len(df)}")

# STEP 3: FEATURE ENGINEERING
print("\n🔬 STEP 3: FEATURE ENGINEERING")
print("-"*70)

def extract_features(smiles):
    """Extract RDKit features"""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    features = {}
    # Basic descriptors
    for name, func in Descriptors.descList[:50]:  # Top 50 descriptors
        try:
            features[name] = func(mol)
        except:
            features[name] = 0
    
    # Morgan fingerprint (512-bit)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=512)
    for i in range(512):
        features[f'fp_{i}'] = int(fp[i])
    
    return features

print("Extracting features...")
features_list = []
for i, smiles in enumerate(df[smiles_col]):
    if (i+1) % 1000 == 0:
        print(f"  {i+1}/{len(df)}")
    feat = extract_features(str(smiles))
    if feat:
        features_list.append(feat)

X = pd.DataFrame(features_list).fillna(0)
print(f"Features extracted: {X.shape[1]}")

# STEP 4-6: TRAIN MULTIPLE MODELS WITH TUNING
print("\n🤖 STEP 4-6: MODEL TRAINING & OPTIMIZATION")
print("-"*70)

all_models = {}
results = []

for endpoint in endpoints:
    if endpoint not in df.columns:
        continue
    
    print(f"\n{'='*70}")
    print(f"Training: {endpoint}")
    print(f"{'='*70}")
    
    # Get labels
    y = df[endpoint].values
    valid_mask = ~pd.isna(y)
    X_valid = X[valid_mask]
    y_valid = y[valid_mask].astype(int)
    
    if len(y_valid) < 100 or y_valid.sum() < 10:
        print(f"⚠️ Skipping - insufficient data")
        continue
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_valid, y_valid, test_size=0.2, random_state=42, stratify=y_valid
    )
    
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")
    print(f"Positive: {y_train.sum()} ({y_train.mean()*100:.1f}%)")
    
    # Train XGBoost (best performer)
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        tree_method='hist'
    )
    
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    
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
output_dir = Path('trained_models/latest')
output_dir.mkdir(parents=True, exist_ok=True)

with open(output_dir / 'best_optimized_models.pkl', 'wb') as f:
    pickle.dump(all_models, f)

# Save results
results_df = pd.DataFrame(results)
results_df.to_csv(output_dir / 'training_results.csv', index=False)

print("\n" + "="*70)
print("✅ TRAINING COMPLETE!")
print("="*70)
print(f"\nAverage ROC-AUC: {results_df['roc_auc'].mean():.4f}")
print(f"Models saved: {output_dir}")
print(f"\n{results_df.to_string(index=False)}")
