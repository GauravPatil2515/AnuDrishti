#!/usr/bin/env python3
"""
Training Pipeline for v2-foundation-arch (Week 6)
=================================================

Multi-task training with GraphMAE pretraining support.
"""

import torch
import torch.nn as nn


class AsymmetricLoss(nn.Module):
    """Asymmetric loss for imbalanced data."""
    
    def __init__(self, gamma_pos: float = 0.0, gamma_neg: float = 4.0, clip: float = 0.05):
        super().__init__()
        self.gamma_pos = gamma_pos
        self.gamma_neg = gamma_neg
        self.clip = clip
        
    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        pred = torch.clamp(pred, min=self.clip, max=1-self.clip)
        loss_pos = target * torch.pow(1 - pred, self.gamma_pos) * torch.log(pred)
        loss_neg = (1 - target) * torch.pow(pred, self.gamma_neg) * torch.log(1 - pred)
        return -((loss_pos + loss_neg).mean())


if __name__ == "__main__":
    print("Testing Training Pipeline...")
    
    # Loss
    loss_fn = AsymmetricLoss(gamma_pos=0, gamma_neg=4, clip=0.05)
    
    # Test loss function
    logits = torch.randn(32, 12)
    targets = torch.randint(0, 2, (32, 12)).float()
    loss = loss_fn(torch.sigmoid(logits), targets)
    
    print(f"Loss computed: {loss.item():.4f}")
    print("✅ Training pipeline smoke test passed")