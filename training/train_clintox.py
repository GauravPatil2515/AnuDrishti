#!/usr/bin/env python3
"""
ClinTox Model Training Script
=============================
Trains Attention-GINet on Clinical Toxicity dataset.

Dataset: ClinTox (1,491 molecules)
Tasks: 2 binary classification tasks
  - FDA_APPROVED: FDA approval status
  - CT_TOX: Clinical trial toxicity
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
from sklearn.metrics import roc_auc_score, accuracy_score
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

def load_clintox_data(data_dir):
    """Load ClinTox dataset"""
    train_df = pd.read_csv(data_dir / "train.csv")
    valid_df = pd.read_csv(data_dir / "valid.csv")
    test_df = pd.read_csv(data_dir / "test.csv")
    
    def process_split(df, name):
        data_list = []
        for _, row in df.iterrows():
            smiles = row['smiles']
            # ClinTox has 2 tasks
            labels = [row['FDA_APPROVED'], row['CT_TOX']]
            
            graph = smiles_to_graph(smiles)
            if graph is not None:
                graph.y = torch.tensor(labels, dtype=torch.float)
                data_list.append(graph)
        
        print(f"  {name}: {len(data_list)}/{len(df)} molecules processed")
        return data_list
    
    print("Loading ClinTox dataset...")
    train_data = process_split(train_df, "Train")
    valid_data = process_split(valid_df, "Valid")
    test_data = process_split(test_df, "Test")
    
    return train_data, valid_data, test_data

class AttentionGINet(nn.Module):
    """Attention-augmented GIN for ClinTox (multi-task)"""
    
    def __init__(self, num_tasks=2, emb_dim=300, drop_ratio=0.3):
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
        
        # Predictor (multi-task)
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

def train_epoch(model, loader, optimizer, criterion, device, num_tasks=2):
    model.train()
    total_loss = 0
    
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        out = model(batch)
        y = batch.y
        
        # Reshape y from [batch*num_tasks] to [batch, num_tasks]
        y = y.view(-1, num_tasks)
        
        loss = criterion(out, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * batch.num_graphs
    
    return total_loss / len(loader.dataset)

def evaluate(model, loader, device, num_tasks=2):
    model.eval()
    y_true = []
    y_pred = []
    
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch)
            prob = torch.sigmoid(out).cpu().numpy()
            
            # Reshape y from [batch*num_tasks] to [batch, num_tasks]
            y = batch.y.view(-1, num_tasks).cpu().numpy()
            
            y_true.append(y)
            y_pred.append(prob)
    
    y_true = np.vstack(y_true)
    y_pred = np.vstack(y_pred)
    
    # Calculate ROC-AUC for each task
    roc_aucs = []
    for i in range(y_true.shape[1]):
        mask = ~np.isnan(y_true[:, i])
        if mask.sum() > 0:
            try:
                roc_auc = roc_auc_score(y_true[mask, i], y_pred[mask, i])
                roc_aucs.append(roc_auc)
            except:
                roc_aucs.append(0.5)
    
    return np.mean(roc_aucs), roc_aucs

def train_clintox():
    print("=" * 60)
    print("🧬 ClinTox Model Training")
    print("   Clinical Toxicity Prediction (2 tasks)")
    print("=" * 60)
    
    # Configuration
    config = {
        'epochs': 100,
        'batch_size': 32,
        'lr': 0.0001,
        'emb_dim': 300,
        'dropout': 0.3,
        'patience': 50,
        'seed': 42,
        'num_tasks': 2
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
    data_dir = project_dir / "MODELS" / "clintox_model_package" / "data" / "clintox"
    train_data, valid_data, test_data = load_clintox_data(data_dir)
    
    train_loader = DataLoader(train_data, batch_size=config['batch_size'], shuffle=True)
    valid_loader = DataLoader(valid_data, batch_size=config['batch_size'])
    test_loader = DataLoader(test_data, batch_size=config['batch_size'])
    
    # Model
    model = AttentionGINet(num_tasks=config['num_tasks'], emb_dim=config['emb_dim'], drop_ratio=config['dropout'])
    model = model.to(device)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"\n🔧 Model Parameters: {total_params:,}")
    
    # Optimizer and loss
    optimizer = optim.Adam(model.parameters(), lr=config['lr'])
    criterion = nn.BCEWithLogitsLoss()
    
    # Training loop
    best_val_roc = 0
    best_epoch = 0
    patience_counter = 0
    
    output_dir = project_dir / "results" / "trained_models"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🚀 Starting training for {config['epochs']} epochs...")
    print("-" * 60)
    
    for epoch in range(1, config['epochs'] + 1):
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_roc, val_rocs = evaluate(model, valid_loader, device)
        
        if val_roc > best_val_roc:
            best_val_roc = val_roc
            best_epoch = epoch
            patience_counter = 0
            
            # Save best model
            torch.save(model.state_dict(), output_dir / "clintox_gin_model.pth")
            print(f"Epoch {epoch:3d} | Loss: {train_loss:.4f} | Val ROC-AUC: {val_roc:.4f} (FDA: {val_rocs[0]:.3f}, TOX: {val_rocs[1]:.3f}) ⭐ NEW BEST")
        else:
            patience_counter += 1
            if epoch % 10 == 0:
                print(f"Epoch {epoch:3d} | Loss: {train_loss:.4f} | Val ROC-AUC: {val_roc:.4f}")
        
        if patience_counter >= config['patience']:
            print(f"\n⏹️ Early stopping at epoch {epoch}")
            break
    
    # Final evaluation
    print("\n" + "=" * 60)
    print("📊 FINAL EVALUATION")
    print("=" * 60)
    
    # Load best model
    model.load_state_dict(torch.load(output_dir / "clintox_gin_model.pth"))
    
    test_roc, test_rocs = evaluate(model, test_loader, device)
    
    print(f"\n✅ Best Validation ROC-AUC: {best_val_roc:.4f} (Epoch {best_epoch})")
    print(f"✅ Test ROC-AUC (avg): {test_roc:.4f}")
    print(f"   - FDA_APPROVED: {test_rocs[0]:.4f}")
    print(f"   - CT_TOX: {test_rocs[1]:.4f}")
    print(f"\n💾 Model saved to: {output_dir / 'clintox_gin_model.pth'}")
    
    return best_val_roc, test_roc

if __name__ == "__main__":
    train_clintox()
