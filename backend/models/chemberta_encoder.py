#!/usr/bin/env python3
"""
ChemBERTa Encoder for SMILES-based molecular representation
===========================================================
Provides a transformer-based SMILES encoder for ensemble with GNN predictions.
Uses the pre-trained ChemBERTa-zinc-base-v1 model from HuggingFace.

This is part of Phase 3 advanced ML upgrades for SIH 2026.
"""

import torch
import torch.nn as nn
import os

TRANSFORMERS_AVAILABLE = False
AutoTokenizer = None
AutoModel = None

def _try_import_transformers():
    global TRANSFORMERS_AVAILABLE, AutoTokenizer, AutoModel
    if TRANSFORMERS_AVAILABLE:
        return True
    try:
        from transformers import AutoTokenizer as _AutoTokenizer, AutoModel as _AutoModel
        AutoTokenizer = _AutoTokenizer
        AutoModel = _AutoModel
        TRANSFORMERS_AVAILABLE = True
        return True
    except ImportError as e:
        print(f"⚠️ Transformers not available: {e}")
        TRANSFORMERS_AVAILABLE = False
        return False


class ChemBERTaEncoder:
    """
    Wrapper for ChemBERTa pre-trained model to encode SMILES strings
    into fixed-dimensional embeddings.
    """
    
    def __init__(self, model_name="seyonec/ChemBERTa-zinc-base-v1", device=None, max_length=128):
        """
        Initialize ChemBERTa encoder.
        
        Args:
            model_name: HuggingFace model identifier
            device: torch device (auto-detect if None)
            max_length: Maximum token sequence length
        """
        self.model_name = model_name
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.max_length = max_length
        self.tokenizer = None
        self.model = None
        self.is_loaded = False
        self.embedding_dim = 768  # ChemBERTa base hidden size
        
    def load(self):
        """Load the tokenizer and model."""
        if self.is_loaded:
            return True
            
        # Try to import transformers lazily
        _try_import_transformers()
            
        if not TRANSFORMERS_AVAILABLE:
            print(f"⚠️ Transformers not available, ChemBERTa encoder disabled")
            self.is_loaded = False
            return False
            
        try:
            print(f"🔄 Loading ChemBERTa encoder: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True
            print(f"✅ ChemBERTa encoder loaded on {self.device}")
            return True
        except Exception as e:
            print(f"⚠️ ChemBERTa encoder optional load skipped ({e}). Falling back to GNN structural features.")
            self.is_loaded = False
            return False
    
    def encode(self, smiles: str) -> torch.Tensor:
        """
        Encode a SMILES string to [CLS] embedding.
        
        Args:
            smiles: SMILES string
            
        Returns:
            Tensor of shape [1, 768] (batch=1, hidden_dim)
        """
        if not self.is_loaded:
            self.load()
            
        if not self.is_loaded:
            raise RuntimeError("ChemBERTa encoder not loaded")
            
        try:
            tokens = self.tokenizer(
                smiles,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.max_length
            )
            
            tokens = {k: v.to(self.device) for k, v in tokens.items()}
            
            with torch.no_grad():
                output = self.model(**tokens)
                # Get [CLS] token embedding (first token)
                cls_embedding = output.last_hidden_state[:, 0, :]  # [1, 768]
                
            return cls_embedding
        except Exception as e:
            print(f"⚠️ ChemBERTa encoding failed: {e}")
            # Return zero embedding as fallback
            return torch.zeros(1, self.embedding_dim, device=self.device)
    
    def encode_batch(self, smiles_list: list) -> torch.Tensor:
        """
        Encode a batch of SMILES strings.
        
        Args:
            smiles_list: List of SMILES strings
            
        Returns:
            Tensor of shape [batch_size, 768]
        """
        if not self.is_loaded:
            self.load()
            
        if not self.is_loaded:
            raise RuntimeError("ChemBERTa encoder not loaded")
            
        try:
            tokens = self.tokenizer(
                smiles_list,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.max_length
            )
            
            tokens = {k: v.to(self.device) for k, v in tokens.items()}
            
            with torch.no_grad():
                output = self.model(**tokens)
                cls_embeddings = output.last_hidden_state[:, 0, :]  # [batch, 768]
                
            return cls_embeddings
        except Exception as e:
            print(f"⚠️ ChemBERTa batch encoding failed: {e}")
            return torch.zeros(len(smiles_list), self.embedding_dim, device=self.device)


class ChemBERTaClassifier(nn.Module):
    """
    ChemBERTa-based classifier for toxicity prediction.
    Can be used as standalone or ensemble component.
    """
    
    def __init__(self, num_tasks=12, dropout=0.3, model_name="seyonec/ChemBERTa-zinc-base-v1"):
        super().__init__()
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("Transformers not available, ChemBERTaClassifier cannot be initialized")
        self.encoder = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Sequential(
            nn.Linear(768, 512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, num_tasks)
        )
        
    def forward(self, input_ids, attention_mask=None):
        """Forward pass through encoder and classifier."""
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls_embedding = outputs.last_hidden_state[:, 0, :]  # [CLS] token
        x = self.dropout(cls_embedding)
        logits = self.classifier(x)
        return logits
    
    def predict_proba(self, input_ids, attention_mask=None):
        """Get probabilities via sigmoid."""
        logits = self.forward(input_ids, attention_mask)
        return torch.sigmoid(logits)
    
    def predict_mc_dropout(self, input_ids, attention_mask=None, n_samples=50):
        """
        MC Dropout inference for uncertainty quantification.
        """
        self.train()  # Enable dropout
        for m in self.modules():
            if isinstance(m, nn.BatchNorm1d) or isinstance(m, nn.BatchNorm2d):
                m.eval()
        
        all_preds = []
        with torch.no_grad():
            for _ in range(n_samples):
                logits = self.forward(input_ids, attention_mask)
                probs = torch.sigmoid(logits)
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


# ==============================================================================
# Convenience function for quick loading
# ==============================================================================
_chemberta_instance = None

def get_chemberta_encoder(device=None):
    """Get or create singleton ChemBERTa encoder instance."""
    global _chemberta_instance
    if _chemberta_instance is None:
        _chemberta_instance = ChemBERTaEncoder(device=device)
        _chemberta_instance.load()
    return _chemberta_instance


if __name__ == "__main__":
    # Test the encoder
    print("Testing ChemBERTa encoder...")
    encoder = get_chemberta_encoder()
    
    if encoder.is_loaded:
        test_smiles = ["CC(=O)Oc1ccccc1C(=O)O", "c1ccccc1", "CCO"]
        for smi in test_smiles:
            emb = encoder.encode(smi)
            print(f"  {smi} -> embedding shape: {emb.shape}")
    else:
        print("Failed to load encoder")