#!/usr/bin/env python3
"""Quick test script for AttentionGINet"""
import sys
sys.path.insert(0, 'backend/models')

import torch
from torch_geometric.data import Data

# Test AttentionGINet
from attention_ginet import AttentionGINet

print("Testing AttentionGINet...")
model = AttentionGINet(num_tasks=12)
print(f"✅ Model created: {sum(p.numel() for p in model.parameters()):,} parameters")

# Create dummy data
x = torch.randint(0, 119, (5, 2))
edge_index = torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]], dtype=torch.long)
edge_attr = torch.randint(0, 5, (4, 2))
batch = torch.zeros(5, dtype=torch.long)
data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, batch=batch)

# Forward pass
model.eval()
with torch.no_grad():
    features, predictions, attention_info = model(data)

print(f"✅ Forward pass successful")
print(f"   Features shape: {features.shape}")
print(f"   Predictions shape: {predictions.shape}")
print(f"   Attention shape: {attention_info['attention_weights'].shape}")
print(f"   Attention sum: {attention_info['attention_weights'].sum().item():.4f}")

print("\n✅ All AttentionGINet tests PASSED!")
