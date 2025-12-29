#!/usr/bin/env python3
"""
Clearance Model Training Script
================================
Trains Attention-GINet on Intrinsic Clearance dataset.

Dataset: Clearance 
Task: Regression (predicting clearance rate)
"""

import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.metrics import mean_squared_error, r2_score
from torch_geometric.data import Data, DataLoader

# Add paths
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir / "backend"))

from rdkit import Chem

# Constants for atom/bond featurization
ATOM_LIST = list(range(1, 119))
CHIRALITY_LIST = [
    Chem.rdchem.ChiralType.CHI_UNSPECIFIED,
    Chem.rdchem.ChiralType.CHI_TETRAHEDRAL_CW,
    Chem.rdchem.ChiralType.CHI_TETRAHEDRAL_CCW,
    Chem.rdchem.ChiralType.CHI_OTHER
]
BOND_LIST = [
    Chem.rdchem.BondType.SINGLE,
    Chem.rdchem.BondType.DOUBLE,
    Chem.rdchem.BondType.TRIPLE,
    Chem.rdchem.BondType.AROMATIC
]
BONDDIR_LIST = [
    Chem.rdchem.BondDir.NONE,
    Chem.rdchem.BondDir.ENDUPRIGHT,
    Chem.rdchem.BondDir.ENDDOWNRIGHT
]

def smiles_to_graph(smiles):
    """Convert SMILES to PyG Data object"""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    # Atom features
    atom_features = []
    for atom in mol.GetAtoms():
        atom_type = atom.GetAtomicNum()
        chirality = atom.GetChiralTag()
        atom_features.append([
            ATOM_LIST.index(atom_type) if atom_type in ATOM_LIST else len(ATOM_LIST),
            CHIRALITY_LIST.index(chirality) if chirality in CHIRALITY_LIST else 0
        ])
    
    x = torch.tensor(atom_features, dtype=torch.long)
    
    # Edge features
    edge_index = []
    edge_attr = []
    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        bond_type = bond.GetBondType()
        bond_dir = bond.GetBondDir()
        
        bond_feat = [
            BOND_LIST.index(bond_type) if bond_type in BOND_LIST else len(BOND_LIST),
            BONDDIR_LIST.index(bond_dir) if bond_dir in BONDDIR_LIST else 0
        ]
        
        edge_index.extend([[i, j], [j, i]])
        edge_attr.extend([bond_feat, bond_feat])
    
    if len(edge_index) == 0:
        edge_index = torch.zeros((2, 0), dtype=torch.long)
        edge_attr = torch.zeros((0, 2), dtype=torch.long)
    else:
        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        edge_attr = torch.tensor(edge_attr, dtype=torch.long)
    
    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)

def load_clearance_data(data_dir):
    """Load Clearance dataset"""
    train_df = pd.read_csv(data_dir / "train.csv")
    valid_df = pd.read_csv(data_dir / "valid.csv")
    test_df = pd.read_csv(data_dir / "test.csv")
    
    # Find the label column (might be 'clearance', 'Y', 'label', etc.)
    label_col = None
    for col in ['clearance', 'Y', 'label', 'value']:
        if col in train_df.columns:
            label_col = col
            break
    
    if label_col is None:
        # Use the second column as label
        label_col = train_df.columns[1]
    
    print(f"  Using label column: {label_col}")
    
    def process_split(df, name):
        data_list = []
        for _, row in df.iterrows():
            smiles = row['smiles'] if 'smiles' in df.columns else row.iloc[0]
            label = row[label_col]
            
            if pd.isna(label):
                continue
            
            graph = smiles_to_graph(smiles)
            if graph is not None:
                # Log-transform target for better regression distribution
                log_label = np.log1p(float(label))
                graph.y = torch.tensor([log_label], dtype=torch.float)
                data_list.append(graph)
        
        print(f"  {name}: {len(data_list)}/{len(df)} molecules processed")
        return data_list

    print("Loading Clearance dataset...")
    train_data = process_split(train_df, "Train")
    valid_data = process_split(valid_df, "Valid")
    test_data = process_split(test_df, "Test")
    
    return train_data, valid_data, test_data

class AttentionGINet(nn.Module):
    """Attention-augmented GIN for Clearance (regression)"""
    
    def __init__(self, num_tasks=1, emb_dim=300, drop_ratio=0.3):
        super().__init__()
        from torch_geometric.nn import GINEConv
        from torch_geometric.nn.aggr import AttentionalAggregation
        
        self.num_layer = 5
        self.emb_dim = emb_dim
        self.drop_ratio = drop_ratio
        
        # Embeddings
        self.x_embedding1 = nn.Embedding(120, emb_dim)
        self.x_embedding2 = nn.Embedding(4, emb_dim)
        
        # GIN layers
        self.convs = nn.ModuleList()
        self.batch_norms = nn.ModuleList()
        
        for _ in range(self.num_layer):
            mlp = nn.Sequential(
                nn.Linear(emb_dim, 2 * emb_dim),
                nn.BatchNorm1d(2 * emb_dim),
                nn.ReLU(),
                nn.Linear(2 * emb_dim, emb_dim)
            )
            conv = GINEConv(mlp, edge_dim=emb_dim)
            self.convs.append(conv)
            self.batch_norms.append(nn.BatchNorm1d(emb_dim))
        
        # Edge embedding
        self.edge_embedding1 = nn.Embedding(5, emb_dim)
        self.edge_embedding2 = nn.Embedding(3, emb_dim)
        
        # Attention pooling
        gate_nn = nn.Sequential(
            nn.Linear(emb_dim, emb_dim),
            nn.ReLU(),
            nn.Linear(emb_dim, 1)
        )
        self.pool = AttentionalAggregation(gate_nn)
        
        # Predictor (regression - no activation at end)
        self.pred = nn.Sequential(
            nn.Linear(emb_dim, emb_dim // 2),
            nn.ReLU(),
            nn.Dropout(drop_ratio),
            nn.Linear(emb_dim // 2, num_tasks)
        )
    
    def forward(self, data):
        x, edge_index, edge_attr, batch = data.x, data.edge_index, data.edge_attr, data.batch
        
        # Node embedding
        h = self.x_embedding1(x[:, 0]) + self.x_embedding2(x[:, 1])
        
        # Edge embedding
        edge_emb = self.edge_embedding1(edge_attr[:, 0]) + self.edge_embedding2(edge_attr[:, 1])
        
        # Message passing
        for i in range(self.num_layer):
            h = self.convs[i](h, edge_index, edge_emb)
            h = self.batch_norms[i](h)
            h = nn.functional.relu(h)
            h = nn.functional.dropout(h, p=self.drop_ratio, training=self.training)
        
        # Pooling
        h_graph = self.pool(h, batch)
        
        # Prediction
        out = self.pred(h_graph)
        return out

def train_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        out = model(batch)
        y = batch.y.view(-1, 1)
        
        loss = criterion(out, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * batch.num_graphs
    
    return total_loss / len(loader.dataset)

def evaluate(model, loader, device):
    model.eval()
    y_true = []
    y_pred = []
    
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch)
            
            y_true.extend(batch.y.cpu().numpy().flatten())
            y_pred.extend(out.cpu().numpy().flatten())
    
    # Convert back from log scale for RMSE calculation
    y_true = np.expm1(np.array(y_true))
    y_pred = np.expm1(np.array(y_pred))
    
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    
    return rmse, r2

def train_clearance():
    print("=" * 60)
    print("🧬 Clearance Model Training")
    print("   Intrinsic Clearance Prediction (Regression)")
    print("=" * 60)
    
    # Configuration
    config = {
        'epochs': 150,
        'batch_size': 32,
        'lr': 0.0001,
        'emb_dim': 300,
        'dropout': 0.3,
        'patience': 50,
        'seed': 42
    }
    
    # Set seed
    torch.manual_seed(config['seed'])
    np.random.seed(config['seed'])
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\n📱 Device: {device}")
    if device.type == 'cuda':
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
    
    # Load data
    data_dir = project_dir / "MODELS" / "clearance_model_full_package" / "data" / "clearance"
    train_data, valid_data, test_data = load_clearance_data(data_dir)
    
    train_loader = DataLoader(train_data, batch_size=config['batch_size'], shuffle=True)
    valid_loader = DataLoader(valid_data, batch_size=config['batch_size'])
    test_loader = DataLoader(test_data, batch_size=config['batch_size'])
    
    # Model
    model = AttentionGINet(num_tasks=1, emb_dim=config['emb_dim'], drop_ratio=config['dropout'])
    model = model.to(device)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"\n🔧 Model Parameters: {total_params:,}")
    
    # Optimizer and loss (MSE for regression)
    optimizer = optim.Adam(model.parameters(), lr=config['lr'])
    criterion = nn.MSELoss()
    
    # Training loop
    best_val_rmse = float('inf')
    best_epoch = 0
    patience_counter = 0
    
    output_dir = project_dir / "results" / "trained_models"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🚀 Starting training for {config['epochs']} epochs...")
    print("-" * 60)
    
    for epoch in range(1, config['epochs'] + 1):
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_rmse, val_r2 = evaluate(model, valid_loader, device)
        
        if val_rmse < best_val_rmse:
            best_val_rmse = val_rmse
            best_epoch = epoch
            patience_counter = 0
            
            # Save best model
            torch.save(model.state_dict(), output_dir / "clearance_gin_model.pth")
            print(f"Epoch {epoch:3d} | Loss: {train_loss:.4f} | Val RMSE: {val_rmse:.4f} | R²: {val_r2:.4f} ⭐ NEW BEST")
        else:
            patience_counter += 1
            if epoch % 10 == 0:
                print(f"Epoch {epoch:3d} | Loss: {train_loss:.4f} | Val RMSE: {val_rmse:.4f} | R²: {val_r2:.4f}")
        
        if patience_counter >= config['patience']:
            print(f"\n⏹️ Early stopping at epoch {epoch}")
            break
    
    # Final evaluation
    print("\n" + "=" * 60)
    print("📊 FINAL EVALUATION")
    print("=" * 60)
    
    # Load best model
    model.load_state_dict(torch.load(output_dir / "clearance_gin_model.pth"))
    
    test_rmse, test_r2 = evaluate(model, test_loader, device)
    
    print(f"\n✅ Best Validation RMSE: {best_val_rmse:.4f} (Epoch {best_epoch})")
    print(f"✅ Test RMSE: {test_rmse:.4f}")
    print(f"✅ Test R²: {test_r2:.4f}")
    print(f"\n💾 Model saved to: {output_dir / 'clearance_gin_model.pth'}")
    
    return best_val_rmse, test_rmse

if __name__ == "__main__":
    train_clearance()
