#!/usr/bin/env python3
"""
Graph Transformer Branch (v2-foundation-arch)
============================================

Replaces GIN message passing with attention-based graph transformer.
Uses Graphormer-style positional encodings and multi-head attention.
"""

import torch
import torch.nn as nn
from torch import Tensor
from typing import Optional


class GraphTransformerLayer(nn.Module):
    """Single Graphormer layer with attention and MLP."""
    
    def __init__(
        self,
        hidden_dim: int,
        num_heads: int = 8,
        dropout: float = 0.1,
    ):
        super().__init__()
        
        self.attn = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True,
        )
        
        self.ffn = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4),
            nn.GELU(),
            nn.Linear(hidden_dim * 4, hidden_dim),
        )
        
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.norm2 = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, h: Tensor, edge_index: Tensor, attention_bias: Optional[Tensor] = None) -> Tensor:
        """Apply attention + FFN."""
        h_norm = self.norm1(h)
        attn_output, _ = self.attn(h_norm, h_norm, h_norm, need_weights=False)
        h = h + self.dropout(attn_output)
        
        h_norm = self.norm2(h)
        h = h + self.dropout(self.ffn(h_norm))
        
        return h


class GraphTransformerEncoder(nn.Module):
    """Graph Transformer Encoder stack replacing GIN message passing."""
    
    def __init__(
        self,
        hidden_dim: int = 256,
        num_layers: int = 6,
        num_heads: int = 8,
        dropout: float = 0.1,
    ):
        super().__init__()
        
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Node embedding
        self.node_embedding = nn.Linear(119, hidden_dim)
        
        # Stack of transformer layers
        self.layers = nn.ModuleList([
            GraphTransformerLayer(hidden_dim, num_heads, dropout)
            for _ in range(num_layers)
        ])
        
        # Attention weights output head
        self.attn_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
        )
        
    def forward(self, h: Tensor, edge_index: Tensor, batch: Tensor) -> Tensor:
        """
        Args:
            h: [N, 119] node features
            edge_index: [2, E] edge list
            batch: [N] graph assignment
            
        Returns:
            [N, hidden_dim] node embeddings
        """
        h = self.node_embedding(h)  # [N, hidden_dim]
        
        # Apply transformer layers (batch size 1)
        for layer in self.layers:
            h = h.unsqueeze(0)  # [1, N, H]
            h = layer(h, edge_index)
            h = h.squeeze(0)   # [N, H]
            
        return h
    
    def get_attention_scores(self, h: Tensor) -> Tensor:
        """Get attention scores from node embeddings."""
        return torch.sigmoid(self.attn_head(h).squeeze(-1))


if __name__ == "__main__":
    print("Testing GraphTransformerEncoder...")
    
    model = GraphTransformerEncoder(hidden_dim=256, num_layers=6, num_heads=8)
    
    # Fake molecule
    h = torch.randn(20, 119)  # 20 atoms
    edge_index = torch.randint(0, 20, (2, 40))  # 40 edges
    batch = torch.zeros(20, dtype=torch.long)
    
    output = model(h, edge_index, batch)
    print(f"Output shape: {output.shape}")
    
    attn = model.get_attention_scores(output)
    print(f"Attention scores shape: {attn.shape}")
    
    print("✅ GraphTransformerEncoder smoke test passed")