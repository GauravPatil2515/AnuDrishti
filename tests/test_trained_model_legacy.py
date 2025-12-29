#!/usr/bin/env python3
"""Quick test of trained Attention-GIN model."""

import sys
from pathlib import Path

# Add paths
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR.parent / 'backend' / 'models'))

import torch
from rdkit import Chem

# Test molecules
TEST_SMILES = [
    ("CCO", "Ethanol", "Low toxicity"),
    ("c1ccccc1", "Benzene", "Moderate toxicity"),
    ("c1ccc([N+](=O)[O-])cc1", "Nitrobenzene", "High toxicity"),
    ("ClC1=CC=C(Cl)C=C1", "Dichlorobenzene", "High toxicity"),
]

def main():
    print("=" * 60)
    print("ATTENTION-GIN MODEL TEST")
    print("=" * 60)
    
    # Find model
    model_dir = SCRIPT_DIR.parent / 'backend' / 'models' / 'training_tox21_v2'
    model_files = list(model_dir.glob('**/attention_gin_model.pth'))
    
    if not model_files:
        print("❌ No trained model found!")
        return
    
    model_path = model_files[0]
    print(f"\n✅ Found trained model: {model_path}")
    
    # Load model
    from attention_ginet import AttentionGINet
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"✅ Using device: {device}")
    
    model = AttentionGINet(num_tasks=12)
    state_dict = torch.load(model_path, map_location=device, weights_only=False)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    
    print(f"✅ Model loaded successfully!")
    print(f"   Parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Test predictions
    print("\n" + "-" * 60)
    print("PREDICTIONS:")
    print("-" * 60)
    
    from torch_geometric.data import Data
    
    # Import dataset utilities for feature encoding
    tox21_path = SCRIPT_DIR.parent / 'MODELS' / 'tox21_model_full_package'
    sys.path.insert(0, str(tox21_path))
    from dataset.dataset_test import ATOM_LIST, CHIRALITY_LIST, BOND_LIST, BONDDIR_LIST
    
    import numpy as np
    
    for smiles, name, expected in TEST_SMILES:
        try:
            # Convert SMILES to graph
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                print(f"❌ Failed to parse: {smiles}")
                continue
            
            mol = Chem.AddHs(mol)
            
            # Node features
            type_idx = []
            chirality_idx = []
            for atom in mol.GetAtoms():
                type_idx.append(ATOM_LIST.index(atom.GetAtomicNum()))
                chirality_idx.append(CHIRALITY_LIST.index(atom.GetChiralTag()))
            
            x1 = torch.tensor(type_idx, dtype=torch.long).view(-1, 1)
            x2 = torch.tensor(chirality_idx, dtype=torch.long).view(-1, 1)
            x = torch.cat([x1, x2], dim=-1)
            
            # Edge features
            row, col, edge_feat = [], [], []
            for bond in mol.GetBonds():
                start, end = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
                row += [start, end]
                col += [end, start]
                edge_feat.extend([
                    [BOND_LIST.index(bond.GetBondType()), BONDDIR_LIST.index(bond.GetBondDir())],
                    [BOND_LIST.index(bond.GetBondType()), BONDDIR_LIST.index(bond.GetBondDir())]
                ])
            
            if len(row) == 0:
                edge_index = torch.empty((2, 0), dtype=torch.long)
                edge_attr = torch.empty((0, 2), dtype=torch.long)
            else:
                edge_index = torch.tensor([row, col], dtype=torch.long)
                edge_attr = torch.tensor(np.array(edge_feat), dtype=torch.long)
            
            data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
            data.batch = torch.zeros(x.size(0), dtype=torch.long)
            data = data.to(device)
            
            # Predict
            with torch.no_grad():
                features, predictions, attention_info = model(data, return_attention=True)
            
            # Get toxicity scores
            probs = torch.sigmoid(predictions).cpu().numpy()[0]
            avg_toxicity = float(np.mean(probs))
            max_toxicity = float(np.max(probs))
            
            # Get top attention atoms
            attention = attention_info['attention_weights'].cpu().numpy()
            top_atoms = np.argsort(attention)[-3:][::-1]
            
            # Result
            risk = "HIGH" if avg_toxicity > 0.5 else "MODERATE" if avg_toxicity > 0.3 else "LOW"
            
            print(f"\n{name} ({smiles})")
            print(f"  Expected: {expected}")
            print(f"  Predicted: {risk} risk ({avg_toxicity*100:.1f}% avg toxicity)")
            print(f"  Max endpoint: {max_toxicity*100:.1f}%")
            print(f"  Top attention atoms: {top_atoms.tolist()}")
            
        except Exception as e:
            print(f"❌ Error with {name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ MODEL TEST COMPLETE!")
    print("=" * 60)
    print("\nTraining Results Summary:")
    print("  Best Validation ROC-AUC: 0.7734 (epoch 17)")
    print("  Early stopping at epoch: 32")
    print("  Model saved: attention_gin_model.pth")
    print("\nNext Steps:")
    print("  1. Run faithful_xai_demo.py to test explanations")
    print("  2. Run run_faithful_eval.py for full evaluation")

if __name__ == "__main__":
    main()
