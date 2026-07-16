#!/usr/bin/env python3
"""
Asymmetric Loss for Molecular Property Prediction
=================================================

Addresses severe class imbalance in datasets like ClinToff (~6:1).
Based on "Asymmetric Loss for Multi-class Object Detection" (CVPR 2021).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class AsymmetricLoss(nn.Module):
    """
    Asymmetric Loss (ASL) - better than Focal Loss for imbalanced data.
    
    gamma_pos: Focusing parameter for positive class (default: 0, no focusing)
    gamma_neg: Focusing parameter for negative class (default: 4, strong focusing)
    clip: Probability clipping threshold (default: 0.05)
    """
    
    def __init__(self, gamma_pos: float = 0.0, gamma_neg: float = 4.0, clip: float = 0.05):
        super().__init__()
        self.gamma_pos = gamma_pos
        self.gamma_neg = gamma_neg
        self.clip = clip
        
    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """
        Args:
            pred: [B, C] predicted probabilities (after sigmoid)
            target: [B, C] binary labels (0 or 1)
            
        Returns:
            Scalar loss
        """
        # Clip predictions
        pred = torch.clamp(pred, min=self.clip, max=1-self.clip)
        
        # Asymmetric focusing
        loss_pos = target * torch.pow(1 - pred, self.gamma_pos) * torch.log(pred)
        loss_neg = (1 - target) * torch.pow(pred, self.gamma_neg) * torch.log(1 - pred)
        
        loss = -(loss_pos + loss_neg)
        
        return loss.mean()


class UncertaintyWeightedLoss(nn.Module):
    """
    Multi-task loss with learnable uncertainty weights.
    Based on Kendall et al. "Multi-Task Learning Using Uncertainty..."
    """
    
    def __init__(self, n_tasks: int):
        super().__init__()
        # Learnable log-variance parameters
        self.log_vars = nn.Parameter(torch.zeros(n_tasks))
        
    def forward(self, preds: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Args:
            preds: [B, C] predictions
            targets: [B, C] targets
            
        Returns:
            Weighted sum of task losses
        """
        losses = []
        for i in range(preds.shape[1]):
            loss = F.binary_cross_entropy_with_logits(preds[:, i], targets[:, i])
            precision = torch.exp(-self.log_vars[i])
            losses.append(precision * loss + self.log_vars[i])
            
        return sum(losses)


if __name__ == "__main__":
    print("Testing Asymmetric Loss...")
    
    # Fake predictions and targets (imbalanced)
    pred = torch.sigmoid(torch.randn(100, 12))  # 100 molecules, 12 tasks
    
    # Imbalanced targets (90 negative, 10 positive per task)
    targets = torch.zeros(100, 12)
    targets[:10, :] = 1
    
    asl = AsymmetricLoss(gamma_pos=0, gamma_neg=4, clip=0.05)
    loss = asl(pred, targets)
    print(f"Asymmetric Loss: {loss.item():.4f}")
    
    uwl = UncertaintyWeightedLoss(n_tasks=12)
    uwl_loss = uwl(pred, targets)
    print(f"Uncertainty Weighted Loss: {uwl_loss.item():.4f}")
    
    print("✅ Loss functions smoke test passed")