#!/usr/bin/env python3
"""
Attention-GINet: Graph Isomorphism Network with Global Attention Pooling
=========================================================================
Novel architecture for explainable molecular toxicity prediction.
Extends GINet with learnable attention mechanism for identifying toxic substructures.

Paper: DeNovo-XAI: Interpretable Molecular Toxicity Prediction through
       LLM-Augmented Graph Neural Networks

Author: DeNovo-XAI Team
"""

import torch
from torch import nn
import torch.nn.functional as F
from torch_geometric.nn import MessagePassing, GlobalAttention
from torch_geometric.utils import add_self_loops
from torch_geometric.nn import global_add_pool, global_mean_pool, global_max_pool

# Atom and bond type constants (matching dataset standards)
NUM_ATOM_TYPE = 119  # Including extra mask tokens
NUM_CHIRALITY_TAG = 3
NUM_BOND_TYPE = 5    # Including aromatic and self-loop edge
NUM_BOND_DIRECTION = 3


class GINEConv(MessagePassing):
    """
    Graph Isomorphism Network with Edge features (GINE) Convolution Layer.
    Implements message passing with edge embeddings for bond information.
    """
    
    def __init__(self, emb_dim):
        super(GINEConv, self).__init__(aggr='add')
        
        # MLP for node transformation
        self.mlp = nn.Sequential(
            nn.Linear(emb_dim, 2 * emb_dim),
            nn.ReLU(),
            nn.Linear(2 * emb_dim, emb_dim)
        )
        
        # Edge embeddings for bond type and direction
        self.edge_embedding1 = nn.Embedding(NUM_BOND_TYPE, emb_dim)
        self.edge_embedding2 = nn.Embedding(NUM_BOND_DIRECTION, emb_dim)
        
        # Xavier initialization for better training
        nn.init.xavier_uniform_(self.edge_embedding1.weight.data)
        nn.init.xavier_uniform_(self.edge_embedding2.weight.data)
    
    def forward(self, x, edge_index, edge_attr):
        """Forward pass with edge feature incorporation."""
        # Add self-loops
        edge_index = add_self_loops(edge_index, num_nodes=x.size(0))[0]
        
        # Self-loop edge attributes (bond type 4 = self-loop)
        self_loop_attr = torch.zeros(x.size(0), 2, device=edge_attr.device, dtype=edge_attr.dtype)
        self_loop_attr[:, 0] = 4  # Self-loop bond type
        edge_attr = torch.cat((edge_attr, self_loop_attr), dim=0)
        
        # Compute edge embeddings
        edge_embeddings = (self.edge_embedding1(edge_attr[:, 0].long()) + 
                          self.edge_embedding2(edge_attr[:, 1].long()))
        
        return self.propagate(edge_index, x=x, edge_attr=edge_embeddings)
    
    def message(self, x_j, edge_attr):
        """Message function: combine neighbor features with edge features."""
        return x_j + edge_attr
    
    def update(self, aggr_out):
        """Update function: transform aggregated messages through MLP."""
        return self.mlp(aggr_out)


class AttentionGINet(nn.Module):
    """
    Attention-augmented Graph Isomorphism Network for Explainable Toxicity Prediction.
    
    Key Innovation:
    - Replaces standard global pooling with GlobalAttention mechanism
    - Learns importance weights for each atom in the molecule
    - Returns attention weights for interpretability
    
    Architecture:
        Input → Node Embeddings → 5x GINEConv → GlobalAttention → Prediction
                                                    ↓
                                            Attention Weights (Explainability)
    
    Args:
        task (str): 'classification' or 'regression'
        num_layer (int): Number of GNN layers (default: 5)
        emb_dim (int): Embedding dimension (default: 300)  
        feat_dim (int): Feature dimension after pooling (default: 512)
        drop_ratio (float): Dropout rate (default: 0.3)
        num_tasks (int): Number of prediction tasks
        pred_n_layer (int): Number of prediction head layers (default: 2)
        pred_act (str): Activation function ('relu' or 'softplus')
    
    Returns:
        features: Graph-level features [batch_size, feat_dim]
        predictions: Task predictions [batch_size, num_tasks]
        attention_weights: Per-atom importance scores [num_atoms]
    """
    
    def __init__(
        self,
        task='classification',
        num_layer=5,
        emb_dim=300,
        feat_dim=512,
        drop_ratio=0.3,
        num_tasks=1,
        pred_n_layer=2,
        pred_act='softplus'
    ):
        super(AttentionGINet, self).__init__()
        
        self.num_layer = num_layer
        self.emb_dim = emb_dim
        self.feat_dim = feat_dim
        self.drop_ratio = drop_ratio
        self.task = task
        self.num_tasks = num_tasks
        
        # ═══════════════════════════════════════════════════════════════
        # Node Embeddings
        # ═══════════════════════════════════════════════════════════════
        self.x_embedding1 = nn.Embedding(NUM_ATOM_TYPE, emb_dim)
        self.x_embedding2 = nn.Embedding(NUM_CHIRALITY_TAG, emb_dim)
        nn.init.xavier_uniform_(self.x_embedding1.weight.data)
        nn.init.xavier_uniform_(self.x_embedding2.weight.data)
        
        # ═══════════════════════════════════════════════════════════════
        # GNN Layers (5x GINEConv + BatchNorm)
        # ═══════════════════════════════════════════════════════════════
        self.gnns = nn.ModuleList()
        self.batch_norms = nn.ModuleList()
        for _ in range(num_layer):
            self.gnns.append(GINEConv(emb_dim))
            self.batch_norms.append(nn.BatchNorm1d(emb_dim))
        
        # ═══════════════════════════════════════════════════════════════
        # 🔥 NOVEL: Global Attention Pooling (Key Innovation)
        # ═══════════════════════════════════════════════════════════════
        # Gate network learns which atoms are important for toxicity
        self.gate_nn = nn.Sequential(
            nn.Linear(emb_dim, emb_dim // 2),
            nn.ReLU(),
            nn.BatchNorm1d(emb_dim // 2),
            nn.Linear(emb_dim // 2, 1)
        )
        self.attention_pool = GlobalAttention(gate_nn=self.gate_nn)
        
        # Also keep mean pool for comparison (ablation study)
        self.mean_pool = global_mean_pool
        
        # ═══════════════════════════════════════════════════════════════
        # Feature Projection
        # ═══════════════════════════════════════════════════════════════
        self.feat_lin = nn.Linear(emb_dim, feat_dim)
        
        # ═══════════════════════════════════════════════════════════════
        # Prediction Head
        # ═══════════════════════════════════════════════════════════════
        out_dim = num_tasks
        self.pred_n_layer = max(1, pred_n_layer)
        
        if pred_act == 'relu':
            pred_head = [
                nn.Linear(feat_dim, feat_dim // 2),
                nn.ReLU(inplace=True)
            ]
            for _ in range(self.pred_n_layer - 1):
                pred_head.extend([
                    nn.Linear(feat_dim // 2, feat_dim // 2),
                    nn.ReLU(inplace=True)
                ])
        elif pred_act == 'softplus':
            pred_head = [
                nn.Linear(feat_dim, feat_dim // 2),
                nn.Softplus()
            ]
            for _ in range(self.pred_n_layer - 1):
                pred_head.extend([
                    nn.Linear(feat_dim // 2, feat_dim // 2),
                    nn.Softplus()
                ])
        else:
            raise ValueError(f'Undefined activation: {pred_act}')
        
        pred_head.append(nn.Linear(feat_dim // 2, out_dim))
        self.pred_head = nn.Sequential(*pred_head)
        
        # ═══════════════════════════════════════════════════════════════
        # 🔥 NOVEL: Multi-Task Attention & ECFP6 Feature Fusion
        # ═══════════════════════════════════════════════════════════════
        self.task_gate_nns = nn.ModuleList([
            nn.Sequential(
                nn.Linear(emb_dim, emb_dim // 2),
                nn.ReLU(),
                nn.BatchNorm1d(emb_dim // 2),
                nn.Linear(emb_dim // 2, 1)
            )
            for _ in range(num_tasks)
        ])
        self.task_attention_pools = nn.ModuleList([
            GlobalAttention(gate_nn=gate) for gate in self.task_gate_nns
        ])
        
        # Fingerprint projection layer (ECFP6 has 2048 dimensions)
        self.fp_proj = nn.Linear(2048, feat_dim)
        # Fusion layer to map concatenated GNN + projected ECFP features back to feat_dim
        self.fusion_layer = nn.Linear(feat_dim * 2, feat_dim)
        
        # Storage for attention weights (for explainability)
        self._last_attention_weights = None
        self._last_node_features = None
    
    def forward(self, data, return_attention=True, fp_features=None):
        """
        Forward pass with optional attention weight extraction and ECFP6 fusion.
        
        Args:
            data: PyTorch Geometric Data object with x, edge_index, edge_attr, batch
            return_attention: If True, compute and store attention weights
            fp_features: ECFP6 fingerprint features [batch_size, 2048] (optional)
        
        Returns:
            Tuple of (features, predictions, attention_info) where attention_info is:
            - attention_weights: Importance score per atom [num_atoms]
            - batch: Batch assignment for each atom
        """
        x = data.x
        edge_index = data.edge_index
        edge_attr = data.edge_attr
        batch = data.batch
        
        # ══════════════════════════════════════════════════════════════════
        # Node Embedding
        # ══════════════════════════════════════════════════════════════════
        h = self.x_embedding1(x[:, 0]) + self.x_embedding2(x[:, 1])
        
        # ═══════════════════════════════════════════════════════════════════
        # Message Passing (5 layers)
        # ══════════════════════════════════════════════════════════════════
        for layer in range(self.num_layer):
            h = self.gnns[layer](h, edge_index, edge_attr)
            h = self.batch_norms[layer](h)
            
            if layer == self.num_layer - 1:
                # Last layer: only dropout
                h = F.dropout(h, self.drop_ratio, training=self.training)
            else:
                # Other layers: ReLU + dropout
                h = F.dropout(F.relu(h), self.drop_ratio, training=self.training)
        
        # Store node features for explainability
        self._last_node_features = h.detach()
        
        # ══════════════════════════════════════════════════════════════════
        # 🔥 Multi-task Attention Pooling (Novel)
        # ══════════════════════════════════════════════════════════════════
        task_attention_weights = []
        task_features = []
        
        # Compute attention scores and pool for each task
        for task_idx in range(self.num_tasks):
            gate_scores = self.task_gate_nns[task_idx](h)  # [num_atoms, 1]
            attention_weights = self._compute_attention_weights(gate_scores, batch)
            task_attention_weights.append(attention_weights)
            
            # Apply attention pooling for this task
            h_pooled_task = self.task_attention_pools[task_idx](h, batch)
            task_features.append(h_pooled_task)
        
        # Store attention weights for first task (for backward compatibility)
        self._last_attention_weights = task_attention_weights[0].detach()
        
        # ══════════════════════════════════════════════════════════════════
        # Feature Projection, Fusion, and Predictions per task
        # ══════════════════════════════════════════════════════════════════
        predictions_list = []
        for task_idx in range(self.num_tasks):
            h_pooled_task = task_features[task_idx]
            features_task = self.feat_lin(h_pooled_task)
            
            # Feature Fusion: ECFP6 + GNN (if fingerprints provided)
            if fp_features is not None:
                # Project ECFP6 fingerprints
                fp_projected = F.relu(self.fp_proj(fp_features))  # [batch_size, feat_dim]
                
                # Concatenate GNN features and fingerprint features
                combined_features = torch.cat([features_task, fp_projected], dim=1)  # [batch_size, feat_dim*2]
                
                # Fuse features
                features_task = F.relu(self.fusion_layer(combined_features))  # [batch_size, feat_dim]
            
            pred_task = self.pred_head(features_task)  # [batch_size, num_tasks]
            predictions_list.append(pred_task[:, task_idx])
            
        predictions = torch.stack(predictions_list, dim=1)  # [batch_size, num_tasks]
        
        # For compatibility/extracting representations, project first task's features
        features = self.feat_lin(task_features[0])
        if fp_features is not None:
            fp_projected = F.relu(self.fp_proj(fp_features))
            combined_features = torch.cat([features, fp_projected], dim=1)
            features = F.relu(self.fusion_layer(combined_features))
        
        if return_attention:
            attention_info = {
                'attention_weights': task_attention_weights[0],  # Tensor of attention weights for first task (backward compatibility)
                'task_attention_weights': task_attention_weights,  # List of attention weights for all tasks
                'batch': batch,
                'node_features': self._last_node_features
            }
            return features, predictions, attention_info
        else:
            return features, predictions
    def _compute_attention_weights(self, gate_scores, batch):
        """
        Compute normalized attention weights per graph.
        Uses softmax normalization within each graph in the batch.
        
        Args:
            gate_scores: Raw gate outputs [num_atoms, 1]
            batch: Batch assignment tensor [num_atoms]
            
        Returns:
            Normalized attention weights [num_atoms]
        """
        # Softmax normalization per graph
        gate_scores = gate_scores.squeeze(-1)  # [num_atoms]
        
        # Get unique graphs in batch
        num_graphs = batch.max().item() + 1
        attention_weights = torch.zeros_like(gate_scores)
        
        for i in range(num_graphs):
            mask = (batch == i)
            if mask.sum() > 0:
                graph_scores = gate_scores[mask]
                graph_attention = F.softmax(graph_scores, dim=0)
                attention_weights[mask] = graph_attention
        
        return attention_weights
    
    def get_attention_weights(self):
        """Get the most recent attention weights after forward pass."""
        return self._last_attention_weights
    
    def get_node_features(self):
        """Get the most recent node features after forward pass."""
        return self._last_node_features
    
    def load_pretrained_ginet(self, state_dict, strict=False):
        """
        Load weights from a pre-trained GINet model.
        Initializes attention layer randomly (will be fine-tuned).
        
        Args:
            state_dict: State dict from pre-trained GINet
            strict: If True, raise error on missing keys
        """
        own_state = self.state_dict()
        loaded_keys = []
        skipped_keys = []
        
        for name, param in state_dict.items():
            if name in own_state:
                if own_state[name].shape == param.shape:
                    own_state[name].copy_(param)
                    loaded_keys.append(name)
                else:
                    skipped_keys.append(f"{name} (shape mismatch)")
            else:
                skipped_keys.append(name)
        
        print(f"✅ Loaded {len(loaded_keys)} layers from pre-trained GINet")
        if skipped_keys:
            print(f"⚠️ Skipped {len(skipped_keys)} layers (attention layer will be trained)")
        
        return loaded_keys, skipped_keys


class AttentionGINetWrapper:
    """
    Wrapper class for easy inference with attention extraction.
    Provides high-level API for toxicity prediction with explanations.
    """
    
    def __init__(self, model_path, num_tasks, device='cpu'):
        self.device = torch.device(device)
        self.model = AttentionGINet(num_tasks=num_tasks)
        
        # Load checkpoint
        checkpoint = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(checkpoint)
        self.model.to(self.device)
        self.model.eval()
    
    def predict_with_explanation(self, data):
        """
        Make prediction and return attention-based explanation.
        
        Args:
            data: PyTorch Geometric Data object
            
        Returns:
            dict with predictions, attention_weights, and top_atoms
        """
        data = data.to(self.device)
        
        with torch.no_grad():
            features, predictions, attention_info = self.model(data, return_attention=True)
        
        # Get top-k most important atoms
        attention_weights = attention_info['attention_weights'].cpu().numpy()
        top_k = min(5, len(attention_weights))
        top_indices = attention_weights.argsort()[-top_k:][::-1]
        
        return {
            'predictions': predictions.cpu().numpy(),
            'features': features.cpu().numpy(),
            'attention_weights': attention_weights,
            'top_atoms': top_indices.tolist(),
            'top_scores': attention_weights[top_indices].tolist()
        }


# ═══════════════════════════════════════════════════════════════════════════
# Test Code
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Testing Attention-GINet Architecture...")
    print("=" * 60)
    
    # Create model
    model = AttentionGINet(
        task='classification',
        num_layer=5,
        emb_dim=300,
        feat_dim=512,
        drop_ratio=0.3,
        num_tasks=12  # Tox21 endpoints
    )
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"✅ Model created successfully")
    print(f"   Total parameters: {total_params:,}")
    print(f"   Trainable parameters: {trainable_params:,}")
    
    # Test forward pass with dummy data
    from torch_geometric.data import Data
    
    # Create dummy molecule (5 atoms, 4 bonds)
    x = torch.randint(0, 119, (5, 2))  # [num_atoms, 2]
    edge_index = torch.tensor([[0, 1, 1, 2, 2, 3, 3, 4],  # Source nodes
                               [1, 0, 2, 1, 3, 2, 4, 3]], dtype=torch.long)  # Target nodes
    edge_attr = torch.randint(0, 5, (8, 2))  # [num_edges, 2]
    batch = torch.zeros(5, dtype=torch.long)  # All atoms belong to graph 0
    
    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, batch=batch)
    
    # Forward pass
    model.eval()
    with torch.no_grad():
        features, predictions, attention_info = model(data)
    
    print(f"\n✅ Forward pass successful")
    print(f"   Features shape: {features.shape}")
    print(f"   Predictions shape: {predictions.shape}")
    print(f"   Attention weights shape: {attention_info['attention_weights'].shape}")
    print(f"   Attention weights: {attention_info['attention_weights'].numpy()}")
    
    # Verify attention weights sum to 1
    attn_sum = attention_info['attention_weights'].sum().item()
    print(f"   Attention sum: {attn_sum:.4f} (should be ~1.0)")
    
    print("\n✅ Attention-GINet ready for training!")
