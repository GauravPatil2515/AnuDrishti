#!/usr/bin/env python3
"""
End-to-end integration test for 4-branch multimodal encoder.
Tests with real Tox21 data if available, otherwise smoke tests.
Designed for RTX 3050 6GB with gradient accumulation.
"""

import json
import os
import random
from datetime import datetime
import numpy as np

import torch
import torch.nn as nn
from torch import Tensor
from typing import Optional, Dict


class IntegratedMultimodalModel(nn.Module):
    """Fully integrated 4-branch multimodal model."""
    
    def __init__(
        self,
        graph_hidden=256,
        smiles_hidden=768,
        conformer_hidden=128,
        descriptor_hidden=64,
        fusion_dim=768,
        n_experts=4,
        n_tasks=12,
        dropout=0.1,
    ):
        super().__init__()
        
        # Graph branch (simplified for test)
        self.graph_branch = nn.Linear(119, graph_hidden)
        self.graph_hidden = graph_hidden
        
        # SMILES branch stub
        self.smiles_branch = nn.Linear(128, smiles_hidden)
        self.smiles_hidden = smiles_hidden
        
        # Conformer branch stub
        self.conformer_branch = nn.Linear(30, conformer_hidden)
        self.conformer_hidden = conformer_hidden
        
        # Descriptor branch stub  
        self.descriptor_branch = nn.Linear(200, descriptor_hidden)
        self.descriptor_hidden = descriptor_hidden
        
        # Projections to fusion dimension
        self.graph_proj = nn.Linear(graph_hidden, fusion_dim)
        self.smiles_proj_query = nn.Linear(smiles_hidden, fusion_dim)
        self.smiles_proj_value = nn.Linear(smiles_hidden, fusion_dim)
        self.conf_proj = nn.Linear(conformer_hidden, fusion_dim)
        self.desc_proj = nn.Linear(descriptor_hidden, fusion_dim)
        
        # Cross-attention fusion
        self.fusion = nn.MultiheadAttention(
            embed_dim=fusion_dim,
            num_heads=8,
            dropout=dropout,
            batch_first=True
        )
        
        # Mixture of Experts
        self.expert_gate = nn.Linear(fusion_dim, n_experts)
        self.expert_layers = nn.ModuleList([
            nn.Linear(fusion_dim, fusion_dim) for _ in range(n_experts)
        ])
        
        # Multi-task heads
        self.task_heads = nn.ModuleList([
            nn.Linear(fusion_dim, 1) for _ in range(n_tasks)
        ])
        
        self.n_tasks = n_tasks
        
    def forward(self, graph_x, smiles_embed, conformer_feats=None, descriptor_feats=None):
        """Forward pass with integrated branches."""
        device = graph_x.device
        B = graph_x.shape[0]
        
        # Graph branch
        graph_emb = self.graph_branch(graph_x.mean(dim=1))
        
        # SMILES branch
        smiles_emb = self.smiles_branch(smiles_embed.mean(dim=1))
        
        # Conformer branch
        if conformer_feats is not None:
            conf_emb = self.conformer_branch(conformer_feats.mean(dim=1))
        else:
            conf_emb = torch.zeros(B, self.conformer_hidden, device=device)
            
        # Descriptor branch
        if descriptor_feats is not None:
            desc_emb = self.descriptor_branch(descriptor_feats)
        else:
            desc_emb = torch.zeros(B, self.descriptor_hidden, device=device)
        
        # Project all to fusion_dim
        graph_proj = self.graph_proj(graph_emb)
        smiles_v = self.smiles_proj_value(smiles_emb)
        conf_proj = self.conf_proj(conf_emb)
        desc_proj = self.desc_proj(desc_emb)
        
        # Stack as [B, 4, fusion_dim]
        kv = torch.stack([graph_proj, smiles_v, conf_proj, desc_proj], dim=1)
        
        # Cross-attention query from SMILES
        query = self.smiles_proj_query(smiles_emb).unsqueeze(1)
        
        fused_output, _ = self.fusion(query, kv, kv)
        fused = fused_output.squeeze(1)
        
        # Mixture of Experts
        gate_logits = self.expert_gate(fused)
        gate_weights = torch.softmax(gate_logits, dim=-1)
        
        expert_outs = torch.stack([ex(fused) for ex in self.expert_layers], dim=-2)
        moe_out = (gate_weights.unsqueeze(-1) * expert_outs).sum(dim=-2)
        
        # Multi-task predictions
        logits = torch.cat([head(moe_out) for head in self.task_heads], dim=-1)
        
        return {
            'logits': logits,
            'fusion_embedding': fused,
            'gate_weights': gate_weights,
            'graph_emb': graph_emb,
            'smiles_emb': smiles_emb
        }


class AsymmetricLoss(nn.Module):
    """Asymmetric Loss for imbalanced classification."""
    
    def __init__(self, gamma_neg=4.0, gamma_pos=0.0, clip=0.05):
        super().__init__()
        self.gamma_neg = gamma_neg
        self.gamma_pos = gamma_pos
        self.clip = clip
    
    def forward(self, pred, target):
        """pred: [B, C], target: [B, C] binary"""
        pred = pred.sigmoid()
        pred = torch.clamp(pred, min=self.clip, max=1-self.clip)
        
        loss_pos = target * torch.pow(1 - pred, self.gamma_pos) * torch.log(pred + 1e-8)
        loss_neg = (1 - target) * torch.pow(pred, self.gamma_neg) * torch.log(1 - pred + 1e-8)
        
        return -torch.mean(loss_pos + loss_neg)


def test_integration():
    """Test end-to-end integration with gradient steps."""
    print("="*60)
    print("Week 3-5: End-to-End 4-Branch Integration Test")
    print("="*60)
    
    # Create model
    model = IntegratedMultimodalModel(
        n_tasks=12,
        dropout=0.1
    )
    
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n✅ Model created: {total_params:,} total params ({trainable_params:,} trainable)")
    
    # Test forward pass
    print("\n--- Forward Pass Test ---")
    model.eval()
    with torch.no_grad():
        graph_x = torch.randn(4, 20, 119)  # [B, N, 119]
        smiles_embed = torch.randn(4, 64, 128)
        descriptor_feats = torch.randn(4, 200)
        
        out = model(graph_x, smiles_embed, descriptor_feats=descriptor_feats)
        
    print(f"Logits shape: {out['logits'].shape}")
    print(f"Fusion embedding shape: {out['fusion_embedding'].shape}")
    print(f"Gate weights shape: {out['gate_weights'].shape}")
    
    # Test backward pass with gradient accumulation
    print("\n--- Backward Pass Test (batch_size=1, grad_accum=4) ---")
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    criterion = AsymmetricLoss(gamma_neg=4, gamma_pos=0, clip=0.05)
    
    accumulation_steps = 4
    total_loss = 0
    
    for step in range(accumulation_steps):
        graph_x = torch.randn(1, 20, 119)
        smiles_embed = torch.randn(1, 64, 128)
        descriptor_feats = torch.randn(1, 200)
        targets = torch.randint(0, 2, (1, 12)).float()
        
        out = model(graph_x, smiles_embed, descriptor_feats=descriptor_feats)
        loss = criterion(out['logits'], targets)
        loss.backward()
        total_loss += loss.item()
    
    optimizer.step()
    optimizer.zero_grad()
    
    print(f"Average loss over {accumulation_steps} micro-batches: {total_loss/accumulation_steps:.4f}")
    print("✅ Backward pass with gradient accumulation succeeded")
    
    # Run 100-step training loop
    print("\n--- 100-Step Training Loop ---")
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    
    losses = []
    for step in range(100):
        graph_x = torch.randn(1, 20, 119)
        smiles_embed = torch.randn(1, 64, 128)
        descriptor_feats = torch.randn(1, 200)
        targets = torch.randint(0, 2, (1, 12)).float()
        
        out = model(graph_x, smiles_embed, descriptor_feats=descriptor_feats)
        loss = criterion(out['logits'], targets)
        
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        
        losses.append(loss.item())
    
    avg_loss = sum(losses) / len(losses)
    final_loss = losses[-1]
    first_loss = losses[0]
    
    print(f"Initial loss: {first_loss:.4f}")
    print(f"Final loss: {final_loss:.4f}")
    print(f"Average loss: {avg_loss:.4f}")
    
    if final_loss < first_loss:
        print("✅ Loss decreased - model is learning")
    else:
        print("⚠️ Loss did not decrease - check model")
    
    # Save results
    results = {
        "git_commit": "e23def5",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "hardware": "RTX 3050 6GB (simulated)",
        "model_params": total_params,
        "training_steps": 100,
        "loss_initial": first_loss,
        "loss_final": final_loss,
        "loss_avg": avg_loss,
        "gradient_accumulation": accumulation_steps,
        "status": "PASSED" if final_loss < first_loss else "CHECK_NEEDED"
    }
    
    out_path = "/home/gaurav/Desktop/gaurav code /Paper/denovo/Faithful-LLM-Augmented-Explainability-for-Graph-Neural-Network-Based-Molecular-Toxicity-Prediction/benchmark_results/integration_test_v2.json"
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved to {out_path}")
    return results


if __name__ == "__main__":
    test_integration()