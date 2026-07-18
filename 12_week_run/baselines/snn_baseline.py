#!/usr/bin/env python3
"""
Self-Normalizing Neural Network (SNN) baseline for molecular property prediction.
Uses ECFP6 + MACCS + RDKit descriptors.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys
from rdkit.Chem import Descriptors
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class SNN(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 2048),
            nn.SELU(),
            nn.AlphaDropout(0.1),
            nn.Linear(2048, 1024),
            nn.SELU(),
            nn.AlphaDropout(0.1),
            nn.Linear(1024, 1)
        )
    
    def forward(self, x):
        return self.net(x)

def compute_features(smiles_list):
    """Compute ECFP6, MACCS, and RDKit descriptors."""
    features = []
    for smi in smiles_list:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            # Return zero vector for invalid smiles
            features.append([0.0] * (2048 + 167 + 200))  # ECFP6 + MACCS + selected descriptors
            continue
        
        # ECFP6
        ecfp = AllChem.GetMorganFingerprintAsBitVect(mol, 3, nBits=2048)
        ecfp_arr = np.array(ecfp)
        
        # MACCS
        maccs = MACCSkeys.GenMACCSKeys(mol)
        maccs_arr = np.array(maccs)
        
        # Selected RDKit descriptors
        desc_list = [
            Descriptors.MolWt, Descriptors.MolLogP, Descriptors.TPSA,
            Descriptors.NumHDonors, Descriptors.NumHAcceptors,
            Descriptors.NumRotatableBonds, Descriptors.NumAromaticRings,
            Descriptors.NumSaturatedRings, Descriptors.NumAliphaticRings,
            Descriptors.RingCount, Descriptors.HeavyAtomCount,
            Descriptors.NHOHCount, Descriptors.NOCount, Descriptors.NumValenceElectrons
        ]
        desc_vals = []
        for desc_func in desc_list:
            try:
                val = desc_func(mol)
            except:
                val = 0.0
            desc_vals.append(val)
        # Pad or truncate to 200 dimensions
        if len(desc_vals) < 200:
            desc_vals += [0.0] * (200 - len(desc_vals))
        else:
            desc_vals = desc_vals[:200]
        desc_arr = np.array(desc_vals)
        
        # Concatenate
        combined = np.concatenate([ecfp_arr, maccs_arr, desc_arr])
        features.append(combined)
    
    return np.array(features)

def run_snn(csv_path, target_col, test_size=0.2, epochs=100, lr=1e-3):
    """Run SNN baseline."""
    df = pd.read_csv(csv_path)
    X = compute_features(df['smiles'].tolist())
    y = df[target_col].values
    
    # Standardize features
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
    
    # Convert to tensors
    X_train_t = torch.FloatTensor(X_train)
    y_train_t = torch.FloatTensor(y_train).unsqueeze(1)
    X_test_t = torch.FloatTensor(X_test)
    y_test_t = torch.FloatTensor(y_test).unsqueeze(1)
    
    model = SNN(X_train_t.shape[1])
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        outputs = model(X_train_t)
        loss = criterion(outputs, y_train_t)
        loss.backward()
        optimizer.step()
        
        if (epoch+1) % 20 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")
    
    # Evaluate
    model.eval()
    with torch.no_grad():
        test_outputs = model(X_test_t)
        test_probs = torch.sigmoid(test_outputs).numpy()
        auc = roc_auc_score(y_test, test_probs)
    
    return auc

if __name__ == "__main":
    # Example usage - adjust path as needed
    data_path = "./data/tox21.csv"  # Update this path
    if not os.path.exists(data_path):
        print(f"Warning: Data file not found at {data_path}")
        print("Please update the path to your Tox21 CSV file")
        # Create a dummy dataset for demonstration
        print("Creating dummy dataset for demonstration...")
        os.makedirs("./data", exist_ok=True)
        import pandas as pd
        dummy_df = pd.DataFrame({
            'smiles': ['CCO', 'CCC', 'CCN', 'c1ccccc1O', 'C1CCCCC1'] * 20,
            'NR-AR': [0, 1, 0, 1, 0] * 20
        })
        dummy_df.to_csv(data_path, index=False)
        print(f"Created dummy dataset at {data_path}")
    
    try:
        auc = run_snn(data_path, "NR-AR")
        print(f"SNN AUC for NR-AR: {auc:.4f}")
    except Exception as e:
        print(f"Error running SNN: {e}")
        print("Make sure you have installed: pip install torch rdkit pandas scikit-learn")
