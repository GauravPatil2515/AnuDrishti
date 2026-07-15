import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score
from rdkit import Chem
from rdkit.Chem import AllChem

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "MODELS" / "tox21_model_full_package"))
from dataset.dataset_test import MolTestDatasetWrapper

def get_morgan_fp(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=3, nBits=2048)
    arr = np.zeros((2048,), dtype=np.float32)
    AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def load_csv_dataset(data_dir, target_cols):
    train_df = pd.read_csv(data_dir / "train.csv")
    valid_df = pd.read_csv(data_dir / "valid.csv")
    test_df = pd.read_csv(data_dir / "test.csv")
    
    def process_df(df):
        X, y = [], []
        for _, row in df.iterrows():
            fp = get_morgan_fp(row['smiles'])
            if fp is not None:
                X.append(fp)
                if len(target_cols) == 1:
                    y.append([float(row[target_cols[0]])])
                else:
                    y.append([float(row[col]) for col in target_cols])
        return np.array(X), np.array(y)
        
    X_train, y_train = process_df(train_df)
    X_valid, y_valid = process_df(valid_df)
    X_test, y_test = process_df(test_df)
    
    return X_train, y_train, X_test, y_test

def main():
    print("==================================================")
    print("Evaluating Random Forest & XGBoost Baselines")
    print("==================================================")
    
    results = {}
    
    # 1. BBBP
    print("\n--- BBBP ---")
    bbbp_dir = PROJECT / "data_packages" / "bbbp_model_full_package" / "data" / "bbbp"
    X_train, y_train, X_test, y_test = load_csv_dataset(bbbp_dir, ['p_np'])
    
    # Train RF
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train.ravel())
    rf_preds = rf.predict_proba(X_test)[:, 1]
    rf_auc = roc_auc_score(y_test.ravel(), rf_preds)
    
    # Train XGBoost
    xgb = XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss', n_jobs=-1)
    xgb.fit(X_train, y_train.ravel())
    xgb_preds = xgb.predict_proba(X_test)[:, 1]
    xgb_auc = roc_auc_score(y_test.ravel(), xgb_preds)
    
    print(f"BBBP RF Test ROC-AUC: {rf_auc:.4f}")
    print(f"BBBP XGBoost Test ROC-AUC: {xgb_auc:.4f}")
    results['bbbp'] = {'rf': rf_auc, 'xgb': xgb_auc}
    
    # 2. ClinTox
    print("\n--- ClinTox ---")
    clintox_dir = PROJECT / "data_packages" / "clintox_model_package" / "data" / "clintox"
    target_cols = ['FDA_APPROVED', 'CT_TOX']
    X_train, y_train, X_test, y_test = load_csv_dataset(clintox_dir, target_cols)
    
    rf_aucs = []
    xgb_aucs = []
    
    for i in range(len(target_cols)):
        y_tr_task = y_train[:, i]
        mask_tr = ~np.isnan(y_tr_task) & (y_tr_task != -1)
        
        y_te_task = y_test[:, i]
        mask_te = ~np.isnan(y_te_task) & (y_te_task != -1)
        
        # Fit RF
        rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        rf.fit(X_train[mask_tr], y_tr_task[mask_tr])
        rf_preds = rf.predict_proba(X_test[mask_te])[:, 1]
        rf_auc = roc_auc_score(y_te_task[mask_te], rf_preds)
        rf_aucs.append(rf_auc)
        
        # Fit XGBoost
        xgb = XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss', n_jobs=-1)
        xgb.fit(X_train[mask_tr], y_tr_task[mask_tr])
        xgb_preds = xgb.predict_proba(X_test[mask_te])[:, 1]
        xgb_auc = roc_auc_score(y_te_task[mask_te], xgb_preds)
        xgb_aucs.append(xgb_auc)
        
    print(f"ClinTox RF Test ROC-AUC: {np.mean(rf_aucs):.4f} (FDA: {rf_aucs[0]:.4f}, TOX: {rf_aucs[1]:.4f})")
    print(f"ClinTox XGBoost Test ROC-AUC: {np.mean(xgb_aucs):.4f} (FDA: {xgb_aucs[0]:.4f}, TOX: {xgb_aucs[1]:.4f})")
    results['clintox'] = {'rf': np.mean(rf_aucs), 'xgb': np.mean(xgb_aucs)}
    
    # 3. Tox21
    print("\n--- Tox21 ---")
    tox21_data_path = PROJECT / "data_packages" / "tox21_model_full_package" / "data" / "tox21" / "tox21.csv"
    tox21_targets = [
        "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase",
        "NR-ER", "NR-ER-LBD", "NR-PPAR-gamma",
        "SR-ARE", "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53"
    ]
    
    import torch
    torch.manual_seed(42)
    np.random.seed(42)
    
    wrapper = MolTestDatasetWrapper(
        batch_size=32,
        num_workers=2,
        valid_size=0.1,
        test_size=0.1,
        data_path=str(tox21_data_path),
        target=tox21_targets,
        task="classification",
        splitting="random"
    )
    
    train_loader, _, test_loader = wrapper.get_data_loaders()
    
    def get_xy_from_loader(loader):
        X, y = [], []
        for batch in loader:
            fps = batch.fp.cpu().numpy()
            labels = batch.y.cpu().numpy()
            X.append(fps)
            y.append(labels)
        return np.concatenate(X, axis=0), np.concatenate(y, axis=0)
        
    X_train, y_train = get_xy_from_loader(train_loader)
    X_test, y_test = get_xy_from_loader(test_loader)
    
    rf_aucs = []
    xgb_aucs = []
    
    for i in range(len(tox21_targets)):
        y_tr_task = y_train[:, i]
        mask_tr = ~np.isnan(y_tr_task) & (y_tr_task != -1)
        
        y_te_task = y_test[:, i]
        mask_te = ~np.isnan(y_te_task) & (y_te_task != -1)
        
        if mask_tr.sum() == 0 or mask_te.sum() == 0:
            continue
            
        # Fit RF
        rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        rf.fit(X_train[mask_tr], y_tr_task[mask_tr])
        rf_preds = rf.predict_proba(X_test[mask_te])[:, 1]
        rf_auc = roc_auc_score(y_te_task[mask_te], rf_preds)
        rf_aucs.append(rf_auc)
        
        # Fit XGBoost
        xgb = XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss', n_jobs=-1)
        xgb.fit(X_train[mask_tr], y_tr_task[mask_tr])
        xgb_preds = xgb.predict_proba(X_test[mask_te])[:, 1]
        xgb_auc = roc_auc_score(y_te_task[mask_te], xgb_preds)
        xgb_aucs.append(xgb_auc)
        
    print(f"Tox21 RF Test ROC-AUC: {np.mean(rf_aucs):.4f}")
    print(f"Tox21 XGBoost Test ROC-AUC: {np.mean(xgb_aucs):.4f}")
    results['tox21'] = {'rf': np.mean(rf_aucs), 'xgb': np.mean(xgb_aucs)}
    
    import json
    out_path = PROJECT / "results" / "baseline_ml_metrics.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nSaved ML baselines to {out_path}")

if __name__ == "__main__":
    main()
