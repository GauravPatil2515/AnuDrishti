#!/usr/bin/env python3
"""
TabPFN baseline for molecular property prediction.
"""

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def load_and_featurize(csv_path, target_col):
    """Load dataset and compute ECFP6 fingerprints."""
    df = pd.read_csv(csv_path)
    # Convert SMILES to ECFP6
    fps = []
    for smi in df['smiles']:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            fps.append([0]*2048)
        else:
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, 3, nBits=2048)
            fps.append(list(fp))
    X = np.array(fps)
    y = df[target_col].values
    return X, y

def run_tabpfn(csv_path, target_col, test_size=0.2):
    """Run TabPFN baseline."""
    try:
        from tabpfn import TabPFNClassifier
    except ImportError:
        print("TabPFN not installed. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tabpfn"])
        from tabpfn import TabPFNClassifier
    
    X, y = load_and_featurize(csv_path, target_col)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
    
    clf = TabPFNClassifier(device='cpu', N_ensemble_configurations=32)
    clf.fit(X_train, y_train)
    probs = clf.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, probs)
    return auc

if __name__ == "__main__":
    # Example usage - adjust path as needed
    data_path = "./data/tox21.csv"  # Update this path
    if not os.path.exists(data_path):
        print(f"Warning: Data file not found at {data_path}")
        print("Please update the path to your Tox21 CSV file")
        # Create a dummy dataset for demonstration
        print("Creating dummy dataset for demonstration...")
        os.makedirs("./data", exist_ok=True)
        dummy_df = pd.DataFrame({
            'smiles': ['CCO', 'CCC', 'CCN', 'c1ccccc1O', 'C1CCCCC1'] * 20,
            'NR-AR': [0, 1, 0, 1, 0] * 20
        })
        dummy_df.to_csv(data_path, index=False)
        print(f"Created dummy dataset at {data_path}")
    
    try:
        auc = run_tabpfn(data_path, "NR-AR")
        print(f"TabPFN AUC for NR-AR: {auc:.4f}")
    except Exception as e:
        print(f"Error running TabPFN: {e}")
        print("Make sure you have installed: pip install torch rdkit pandas scikit-learn")
