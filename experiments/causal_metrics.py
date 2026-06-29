import torch
import numpy as np
from typing import Dict
from scipy.integrate import simpson
import copy

def compute_causal_metrics(model, data, attention_weights, p_val=0.2, device='cuda') -> Dict[str, float]:
    """
    Computes strict causal XAI metrics:
    - Comprehensiveness: Prediction drop when top-k nodes are masked.
    - Sufficiency: Prediction confidence when ONLY top-k nodes are retained.
    - Deletion AUC: Area under the curve as nodes are progressively removed.
    - Stability: Cosine similarity of attention masks when the graph is perturbed.
    """
    model.eval()
    data = data.to(device)
    orig_prob = torch.sigmoid(model(data, return_attention=True)[1]).mean().item()
    
    num_nodes = data.x.size(0)
    k = max(1, int(np.ceil(p_val * num_nodes)))
    
    # Sort indices by descending attention weight
    sorted_indices = np.argsort(attention_weights)[::-1].copy()
    top_k_indices = sorted_indices[:k]
    
    # 1. Comprehensiveness (Mask top-k, evaluate drop)
    masked_comp = data.clone()
    masked_comp.x[top_k_indices] = 0.0
    with torch.no_grad():
        comp_prob = torch.sigmoid(model(masked_comp, return_attention=True)[1]).mean().item()
    comprehensiveness = max(0.0, orig_prob - comp_prob)
    
    # 2. Sufficiency (Retain ONLY top-k, mask others)
    masked_suff = data.clone()
    non_top_k = sorted_indices[k:]
    if len(non_top_k) > 0:
        masked_suff.x[non_top_k] = 0.0
    with torch.no_grad():
        suff_prob = torch.sigmoid(model(masked_suff, return_attention=True)[1]).mean().item()
    sufficiency = max(0.0, suff_prob) # How much confidence is retained
    
    # 3. Deletion AUC
    percentages = np.linspace(0.0, 1.0, num=11) # 0%, 10%, 20%... 100%
    deletion_probs = []
    
    for p in percentages:
        k_step = max(0, int(np.ceil(p * num_nodes)))
        step_mask_indices = sorted_indices[:k_step]
        
        step_data = data.clone()
        if len(step_mask_indices) > 0:
            step_data.x[step_mask_indices] = 0.0
            
        with torch.no_grad():
            p_prob = torch.sigmoid(model(step_data, return_attention=True)[1]).mean().item()
        deletion_probs.append(p_prob)
        
    deletion_auc = simpson(y=deletion_probs, x=percentages) # Area under prediction curve
    
    # 4. Stability (Perturbation: Node feature noise sigma=0.01)
    perturbed_data = data.clone()
    noise = torch.randn_like(perturbed_data.x.float()) * 0.01
    perturbed_data.x = perturbed_data.x.float() + noise
    perturbed_data.x = perturbed_data.x.long() # Cast back to long if it was initially
    
    with torch.no_grad():
        _, _, p_attn_info = model(perturbed_data, return_attention=True)
        perturbed_attention = p_attn_info['attention_weights'].cpu().numpy()
        
    # Cosine similarity between original attention and perturbed attention
    v1 = attention_weights / (np.linalg.norm(attention_weights) + 1e-9)
    v2 = perturbed_attention / (np.linalg.norm(perturbed_attention) + 1e-9)
    stability = float(np.dot(v1, v2))
    
    return {
        'comprehensiveness': comprehensiveness,
        'sufficiency': sufficiency,
        'deletion_auc': deletion_auc,
        'stability': stability,
        'faithfulness_score': np.sqrt(comprehensiveness * sufficiency) # Proxy for composite faithfulness
    }
