#!/usr/bin/env python3
import os
import sys
import torch
import numpy as np
from pathlib import Path

project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir / "backend"))
sys.path.insert(0, str(project_dir / "training"))

from train_clintox import load_clintox_data, AttentionGINet, evaluate
from torch_geometric.data import DataLoader

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")
    
    data_dir = project_dir / "MODELS" / "clintox_model_package" / "data" / "clintox"
    _, _, test_data = load_clintox_data(data_dir)
    test_loader = DataLoader(test_data, batch_size=32)
    
    model = AttentionGINet(num_tasks=2)
    model.load_state_dict(torch.load(project_dir / "results" / "trained_models" / "clintox_gin_model.pth", map_location=device))
    model = model.to(device)
    
    test_roc, test_rocs = evaluate(model, test_loader, device)
    print(f"ClinTox Test ROC-AUC (avg): {test_roc:.4f}")
    print(f"   - FDA_APPROVED: {test_rocs[0]:.4f}")
    print(f"   - CT_TOX: {test_rocs[1]:.4f}")

if __name__ == "__main__":
    main()
