#!/usr/bin/env python3
"""
GPS (Graph Transformer) Model for Molecular Property Prediction
================================================================
Implementation of GPS (Graph Transformer with Spectral/Structural Encodings)
based on "Recipe for a General, Powerful, Scalable Graph Transformer" 
(Rampasek et al., NeurIPS 2022).

This provides a SOTA Graph Transformer architecture as an alternative/ensemble
to the Attention-GIN for SIH 2026 Phase 3 upgrades.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GPSConv, GINEConv, global_mean_pool
from torch_geometric.nn.aggr import AttentionalAggregation
from torch_geometric.data import Data, Batch
import math


class GPSModel(nn.Module):
    """
    GPS (Graph Transformer) model for molecular property prediction.
    
    Architecture:
    - Node/edge embeddings
    - Multiple GPSConv layers (local GINEConv + global attention)
    - Global pooling (AttentionalAggregation)
    - Prediction head
    """
    
    def __init__(
        self,
        num_tasks=1,
        num_layers=5,
        emb_dim=300,
        drop_ratio=0.3,
        attn_dropout=0.1,
        heads=4,
        act="relu",
        node_encoder=None,
        edge_encoder=None
    ):
        super().__init__()
        
        self.num_tasks = num_tasks
        self.num_layers = num_layers
        self.emb_dim = emb_dim
        self.drop_ratio = drop_ratio
        
        # Node encoder: atom type + chirality
        self.node_encoder = nn.Sequential(
            nn.Embedding(120, emb_dim),  # atom types 1-118
            nn.Embedding(4, emb_dim)     # chirality 0-3
        ) if node_encoder is None else node_encoder
        
        # Custom forward for combined encoder
        self.node_emb1 = nn.Embedding(120, emb_dim)
        self.node_emb2 = nn.Embedding(4, emb_dim)
        
        # Edge encoder: bond type + bond direction
        self.edge_emb1 = nn.Embedding(5, emb_dim)   # bond types
        self.edge_emb2 = nn.Embedding(3, emb_dim)   # bond directions
        
        # GPS Convolution layers
        self.convs = nn.ModuleList()
        self.batch_norms = nn.ModuleList()
        
        for i in range(num_layers):
            # Local message passing: GINEConv
            mlp = nn.Sequential(
                nn.Linear(emb_dim, 2 * emb_dim),
                nn.BatchNorm1d(2 * emb_dim),
                nn.ReLU(),
                nn.Linear(2 * emb_dim, emb_dim)
            )
            local_conv = GINEConv(mlp, edge_dim=emb_dim)
            
            # Global attention (transformer-style)
            gps_conv = GPSConv(
                channels=emb_dim,
                conv=local_conv,
                heads=heads,
                dropout=attn_dropout,
                act=act,
                act_kwargs=None
            )
            
            self.convs.append(gps_conv)
            self.batch_norms.append(nn.BatchNorm1d(emb_dim))
        
        # Global pooling with attention
        gate_nn = nn.Sequential(
            nn.Linear(emb_dim, emb_dim),
            nn.ReLU(),
            nn.Linear(emb_dim, 1)
        )
        self.pool = AttentionalAggregation(gate_nn)
        
        # Prediction head
        self.predictor = nn.Sequential(
            nn.Linear(emb_dim, emb_dim // 2),
            nn.ReLU(),
            nn.Dropout(drop_ratio),
            nn.Linear(emb_dim // 2, emb_dim // 4),
            nn.ReLU(),
            nn.Dropout(drop_ratio),
            nn.Linear(emb_dim // 4, num_tasks)
        )
        
        self.dropout = nn.Dropout(drop_ratio)
        
    def forward(self, data):
        """
        Forward pass.
        
        Args:
            data: PyG Data or Batch object with x, edge_index, edge_attr, batch
            
        Returns:
            logits: [batch_size, num_tasks] or [num_tasks] for single graph
        """
        x, edge_index, edge_attr, batch = data.x, data.edge_index, data.edge_attr, data.batch
        
        # Node embeddings: atom type + chirality
        if x.dim() == 2 and x.size(1) >= 2:
            # x[:, 0] = atom type, x[:, 1] = chirality
            h = self.node_emb1(x[:, 0].clamp(0, 119)) + self.node_emb2(x[:, 1].clamp(0, 3))
        else:
            # Fallback for different feature formats
            h = self.node_emb1(x.squeeze().clamp(0, 119)) if x.dim() == 1 else self.node_emb1(x[:, 0].clamp(0, 119))
        
        # Edge embeddings
        if edge_attr is not None and edge_attr.dim() == 2 and edge_attr.size(1) >= 2:
            edge_emb = self.edge_emb1(edge_attr[:, 0].clamp(0, 4)) + self.edge_emb2(edge_attr[:, 1].clamp(0, 2))
        else:
            edge_emb = torch.zeros(edge_index.size(1), self.emb_dim, device=x.device)
        
        # GPS layers
        for i in range(self.num_layers):
            h = self.convs[i](h, edge_index, batch=batch, edge_attr=edge_emb)
            h = self.batch_norms[i](h)
            h = F.relu(h)
            h = self.dropout(h)
        
        # Global pooling
        h_graph = self.pool(h, batch)
        
        # Prediction
        out = self.predictor(h_graph)
        return out
    
    def predict_mc_dropout(self, data, n_samples=50):
        """
        MC Dropout inference for epistemic uncertainty.
        
        Args:
            data: PyG Batch object
            n_samples: Number of stochastic forward passes
            
        Returns:
            dict with mean, std, ci_low, ci_high
        """
        self.train()  # Enable dropout
        for m in self.modules():
            if isinstance(m, (nn.BatchNorm1d, nn.BatchNorm2d)):
                m.eval()
        
        all_preds = []
        with torch.no_grad():
            for _ in range(n_samples):
                out = self(data)
                probs = torch.sigmoid(out)
                all_preds.append(probs)
        
        self.eval()
        all_preds = torch.stack(all_preds, dim=0)  # [n_samples, batch, num_tasks]
        
        mean = all_preds.mean(dim=0)
        std = all_preds.std(dim=0)
        ci_low = torch.quantile(all_preds, 0.025, dim=0)
        ci_high = torch.quantile(all_preds, 0.975, dim=0)
        
        return {
            'mean': mean,
            'std': std,
            'ci_low': ci_low,
            'ci_high': ci_high,
            'n_samples': n_samples
        }
    
    def get_graph_embedding(self, data):
        """Extract graph-level embedding (before prediction head)."""
        self.eval()
        with torch.no_grad():
            x, edge_index, edge_attr, batch = data.x, data.edge_index, data.edge_attr, data.batch
            
            h = self.node_emb1(x[:, 0].clamp(0, 119)) + self.node_emb2(x[:, 1].clamp(0, 3))
            edge_emb = self.edge_emb1(edge_attr[:, 0].clamp(0, 4)) + self.edge_emb2(edge_attr[:, 1].clamp(0, 2))
            
            for i in range(self.num_layers):
                h = self.convs[i](h, edge_index, batch=batch, edge_attr=edge_emb)
                h = self.batch_norms[i](h)
                h = F.relu(h)
            
            h_graph = self.pool(h, batch)
            return h_graph


class GPSForTox21(GPSModel):
    """GPS model specialized for Tox21 12-endpoint prediction."""
    
    def __init__(self, **kwargs):
        super().__init__(num_tasks=12, **kwargs)
        self.endpoints = [
            'NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-Aromatase', 'NR-ER', 'NR-ER-LBD',
            'NR-PPAR-gamma', 'SR-ARE', 'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53'
        ]


def create_gps_model(num_tasks=1, **kwargs):
    """Factory function to create GPS model."""
    return GPSModel(num_tasks=num_tasks, **kwargs)


if __name__ == "__main__":
    # Test model creation
    print("Testing GPS model...")
    model = GPSModel(num_tasks=12)
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Test with dummy data
    from torch_geometric.data import Data
    import torch
    
    # Dummy molecule: 5 atoms, 6 edges
    x = torch.tensor([[6, 0], [6, 0], [8, 0], [7, 0], [6, 0]], dtype=torch.long)  # atom types + chirality
    edge_index = torch.tensor([[0, 1, 1, 2, 2, 3], [1, 0, 2, 1, 3, 2]], dtype=torch.long)
    edge_attr = torch.tensor([[1, 0], [1, 0], [2, 0], [1, 0], [1, 0], [1, 0]], dtype=torch.long)
    batch = torch.tensor([0, 0, 0, 0, 0], dtype=torch.long)
    
    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
    data.batch = batch
    
    out = model(data)
    print(f"Output shape: {out.shape}")
    print("GPS model test passed!")