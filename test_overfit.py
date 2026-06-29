import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
from torch_geometric.data import DataLoader

sys.path.insert(0, str(Path('.').resolve()))

from experiments.benchmark_xai import XAIBenchmark, BENCHMARK_MOLECULES

print("🔥 RUNNING OVERFIT TEST (Model Architecture Sanity Check) 🔥\n")

try:
    benchmark = XAIBenchmark(model_path='results/trained_models/attention_gin_model.pth', num_tasks=12)
    device = benchmark.device
    
    subset = []
    for mol in BENCHMARK_MOLECULES[:10]:
        data = benchmark._smiles_to_data(mol.smiles)
        if data is not None:
            data.y = torch.randint(0, 2, (1, 12)).float()
            subset.append(data)
            
    from backend.models.attention_ginet import AttentionGINet
    test_model = AttentionGINet(num_tasks=12).to(device)
    
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(test_model.parameters(), lr=0.01)
    
    test_model.train()
    print("Epoch | Loss")
    print("-" * 20)
    for epoch in range(1, 51):
        total_loss = 0
        for data in subset:
            data = data.to(device)
            optimizer.zero_grad()
            _, preds, _ = test_model(data)
            loss = criterion(preds, data.y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        if epoch % 10 == 0 or epoch == 1:
            print(f"{epoch:<5} | {total_loss/len(subset):.4f}")
            
    test_model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for data in subset:
             data = data.to(device)
             _, preds, _ = test_model(data)
             preds = (torch.sigmoid(preds) > 0.5).float()
             correct += (preds == data.y).sum().item()
             total += 12
             
    acc = correct / total
    print(f"\nFinal Overfit Accuracy: {acc*100:.2f}%")
    
    if acc > 0.90:
        print("✅ RESULT: Architecture is functionally sound. It can learn and overfit small data distributions.")
    else:
        print("❌ RED FLAG: Model cannot overfit small data. Architecture or loss calculation is fundamentally broken!")
except Exception as e:
    print(f"Error: {e}")
