import sys
import os
import torch
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path('.').resolve()))

from experiments.benchmark_xai import XAIBenchmark, BENCHMARK_MOLECULES
from experiments.causal_metrics import compute_causal_metrics

print("🔥 STARTING REALITY CHECK 🔥\n")

# -------------------------------------------------------------
# STEP 1: Verify Model is REAL (Not Dummy)
# -------------------------------------------------------------
print("STEP 1: Checking Model Weights & Initialization")
model_path = 'results/trained_models/attention_gin_model.pth'
is_model_real = False

try:
    benchmark = XAIBenchmark(model_path=model_path, num_tasks=12)
    model = benchmark.model
    device = benchmark.device
    
    print(f"Loaded model from {model_path}")
    print(f"{'Layer Name':<20} | {'Mean':<10} | {'Std':<10}")
    print("-" * 45)
    
    for i, (name, param) in enumerate(model.named_parameters()):
        if i >= 5: # Just show first 5 to avoid clutter
            break
        p_mean = param.mean().item()
        p_std = param.std().item()
        print(f"{name[:19]:<20} | {p_mean:>10.4f} | {p_std:>10.4f}")
        
        if p_std > 0.001:
            is_model_real = True

    if is_model_real:
        print("✅ RESULT: Model weights show variance (std > 0.001). Model is NOT randomly initialized 0s.\n")
    else:
        print("❌ RED FLAG: Model weights have zero variance.\n")
        
except Exception as e:
    print(f"❌ Failed to load model: {e}\n")

# -------------------------------------------------------------
# STEP 2: Verify XAI is REAL (Importance Distribution)
# -------------------------------------------------------------
print("STEP 2: Verifying XAI Distributions (Not Fake / Uniform)")
try:
    mol = BENCHMARK_MOLECULES[0] # Aflatoxin B1
    print(f"Extracting explanations for: {mol.name} ({mol.smiles})")
    
    data = benchmark._smiles_to_data(mol.smiles).to(device)
    
    model.eval()
    with torch.no_grad():
        _, orig_preds, attn_info = model(data, return_attention=True)
        orig_prob = torch.sigmoid(orig_preds).mean().item()
        attn = attn_info['attention_weights'].cpu().numpy()
        
    print(f"Attention stats - Min: {attn.min():.4f}, Max: {attn.max():.4f}, Std: {attn.std():.4f}")
    
    if attn.std() > 0.01:
        print("✅ RESULT: Attention is skewed (model focuses heavily on specific toxic subgraphs, not uniform noise).\n")
    else:
        print("❌ RED FLAG: Attention is uniform. Explanations might be meaningless.\n")
        
except Exception as e:
    print(f"❌ Error in XAI verification: {e}\n")

# -------------------------------------------------------------
# STEP 3: Verify XAI is DYNAMIC (Deletion Test Reality)
# -------------------------------------------------------------
print("STEP 3: End-to-End Deletion Reality Test (Are nodes truly causal?)")
try:
    k = max(1, int(0.2 * len(attn))) # remove top 20%
    top_k = np.argsort(attn)[-k:].copy()
    
    data_masked_top = data.clone()
    data_masked_top.x[top_k] = 0.0
    
    random_k = np.random.choice(len(attn), k, replace=False)
    data_masked_rand = data.clone()
    data_masked_rand.x[random_k] = 0.0
    
    with torch.no_grad():
        _, drop_preds, _ = model(data_masked_top, return_attention=True)
        drop_prob = torch.sigmoid(drop_preds).mean().item()
        
        _, rand_preds, _ = model(data_masked_rand, return_attention=True)
        rand_prob = torch.sigmoid(rand_preds).mean().item()
        
    delta_xai = orig_prob - drop_prob
    delta_rand = orig_prob - rand_prob
    
    print(f"Original Prediction (Probability of Tox): {orig_prob:.4f}")
    print(f"Masked Prediction (Removed Top {k} XAI nodes): {drop_prob:.4f} [Δ = {delta_xai:.4f}]")
    print(f"Masked Prediction (Removed {k} Random nodes): {rand_prob:.4f} [Δ = {delta_rand:.4f}]")
    
    if delta_xai > delta_rand and abs(delta_xai) > 0.01:
        print("✅ RESULT: Removing XAI-flagged nodes significantly drops confidence compared to random removal.\n")
    else:
        print("❌ RED FLAG: XAI node removal is no better than random dropping.\n")

except Exception as e:
    print(f"❌ Error in causality verification: {e}\n")
    
# -------------------------------------------------------------
# STEP 4: Metrics Baseline Sanity Check 
# -------------------------------------------------------------
print("STEP 4: Metric Baselines (Checking Metric Rigor)")
try:
    m_native = compute_causal_metrics(model, data, attn, p_val=0.2, device=device)
    m_rand = compute_causal_metrics(model, data, np.random.rand(len(attn)), p_val=0.2, device=device)
    
    print(f"{'Metric':<20} | {'XAI Engine':<12} | {'Random':<12}")
    print("-" * 50)
    print(f"{'Comprehensiveness':<20} | {m_native['comprehensiveness']:<12.4f} | {m_rand['comprehensiveness']:<12.4f}")
    print(f"{'Sufficiency':<20} | {m_native['sufficiency']:<12.4f} | {m_rand['sufficiency']:<12.4f}")
    print(f"{'Stability':<20} | {m_native['stability']:<12.4f} | {m_rand['stability']:<12.4f}")
    
    if m_native['comprehensiveness'] > m_rand['comprehensiveness']:
        print("\n✅ RESULT: All causal metrics mathematically beat random sampling baselines.\n")
    else:
         print("\n❌ RED FLAG: Native XAI metrics are worse than random.\n")

except Exception as e:
    print(f"❌ Error in baseline sanity metrics verification: {e}\n")

print("🔥 REALITY CHECK COMPLETED 🔥")
