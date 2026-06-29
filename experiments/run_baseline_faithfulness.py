"""
Compute faithfulness score for UNCONSTRAINED LLM baseline.
This is the missing comparison that makes your 36.5% number meaningful.

Usage:
    python experiments/run_baseline_faithfulness.py \
        --model results/trained_models/attention_gin_model.pth \
        --n_molecules 200 \
        --output results/baseline_faithfulness.json
"""

import argparse
import json
import numpy as np
from tqdm import tqdm
from rdkit import Chem
import os

# Load your existing modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from models.unified_predictor import UnifiedPredictor
from models.faithfulness_validator import validate_explanation
from utils.substructure_mapper import get_high_attention_atoms, TOXICOPHORES
from utils.counterfactual_generator import generate_counterfactuals
from dotenv import load_dotenv

load_dotenv()  # loads GROQ_API_KEY from .env

UNCONSTRAINED_PROMPT = """
You are an expert toxicologist. Given the SMILES string of a molecule and
its predicted toxicity score, explain WHY the model might have predicted
this toxicity level. Cite specific functional groups or substructures.

Molecule SMILES: {smiles}
Predicted toxicity probability: {prob:.3f}

Provide a 2-3 sentence explanation citing the key chemical features.
"""

CONSTRAINED_PROMPT = """
You are an expert toxicologist. The following chemical substructures were
identified as important by the prediction model (high attention weights):

Evidence substructures: {evidence}

Given the molecule SMILES: {smiles}
Predicted toxicity probability: {prob:.3f}

Explain the toxicity using ONLY the listed evidence substructures.
Do not cite features not in the evidence list.
"""

def run_baseline_experiment(predictor, test_smiles_list, groq_client, output_path):
    """Compare constrained vs unconstrained LLM faithfulness."""
    results = {
        'constrained': [],    # DeNovo with validation
        'unconstrained': [],  # Direct LLM, no validation
        'molecules': []
    }

    for smiles in tqdm(test_smiles_list[:200], desc="Evaluating molecules"):
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue

        try:
            # Get GNN prediction + attention
            pred_result = predictor.predict_with_attention(smiles)
            prob = pred_result['toxicity_prob']
            attention = pred_result['attention_weights']  # np.array shape [N]
            # Note: predictor.predict_with_attention returns (features, predictions, attention_info)
            # but our UnifiedPredictor.predict_with_attention? We need to check.
            # Actually, UnifiedPredictor does not have predict_with_attention.
            # We need to use the AttentionGINet model directly.
            # Let's adjust: we will get the model from predictor.models['attention_gin']['model']
            # and call its predict_with_explanation or similar.
            # For simplicity, we'll assume predictor has a method to get attention.
            # We'll implement a helper.
            # Since we are in a script, we can access the model directly.
            # Let's do:
            # model = predictor.models['attention_gin']['model']
            # Then we need to convert smiles to graph and get attention.
            # We'll reuse the predictor's _smiles_to_graph method.
            pass
        except Exception as e:
            print(f"Skipping {smiles}: {e}")
            continue

    # Compute statistics
    u_scores = np.array(results['unconstrained'])
    c_scores = np.array(results['constrained'])

    summary = {
        'n_molecules': len(results['molecules']),
        'unconstrained': {
            'mean': float(np.mean(u_scores)),
            'median': float(np.median(u_scores)),
            'std': float(np.std(u_scores))
        },
        'constrained_denovo': {
            'mean': float(np.mean(c_scores)),
            'median': float(np.median(c_scores)),
            'std': float(np.std(c_scores))
        },
        'improvement': float(np.mean(c_scores) - np.mean(u_scores)),
        'rejection_rate': float(np.mean(c_scores < 0.6))  # using acceptance threshold
    }

    # Statistical test
    from scipy import stats
    t_stat, p_value = stats.ttest_rel(c_scores, u_scores)
    summary['paired_ttest'] = {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'significant': bool(p_value < 0.05)
    }

    print("\n=== BASELINE FAITHFULNESS RESULTS ===")
    print(f"N molecules: {summary['n_molecules']}")
    print(f"Unconstrained LLM: {summary['unconstrained']['mean']:.3f} ± {summary['unconstrained']['std']:.3f}")
    print(f"DeNovo constrained: {summary['constrained_denovo']['mean']:.3f} ± {summary['constrained_denovo']['std']:.3f}")
    print(f"Improvement: +{summary['improvement']:.3f}")
    print(f"p-value: {summary['paired_ttest']['p_value']:.4f} ({'significant' if summary['paired_ttest']['significant'] else 'not significant'})")

    with open(output_path, 'w') as f:
        json.dump({**summary, 'raw': results}, f, indent=2)

    return summary

def extract_claimed_atoms(explanation_text, mol, toxicophore_smarts):
    """
    Simple heuristic: find which toxicophores are mentioned in text,
    return their matched atom indices in the molecule.
    """
    claimed = []
    text_lower = explanation_text.lower()
    for name, smarts in toxicophore_smarts.items():
        # Check if toxicophore name appears in explanation
        name_variants = [name, name.replace('_', ' '), name.replace('_', '-')]
        if any(v in text_lower for v in name_variants):
            pattern = Chem.MolFromSmarts(smarts)
            if pattern and mol.HasSubstructMatch(pattern):
                match = mol.GetSubstructMatch(pattern)
                claimed.extend(list(match))
    return list(set(claimed))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True, help='Path to Tox21 model')
    parser.add_argument('--n_molecules', type=int, default=200)
    parser.add_argument('--output', default='results/baseline_faithfulness.json')
    args = parser.parse_args()

    # Initialize predictor
    predictor = UnifiedPredictor()
    # Ensure the model is loaded; if not, load it manually
    if not predictor.is_loaded:
        predictor._load_all_models()

    # Get the attention-GIN model for attention extraction
    from models.attention_ginet import AttentionGINet
    import torch
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    attn_model = AttentionGINet(num_tasks=12)  # Tox21 has 12 endpoints
    attn_model.load_state_dict(torch.load(args.model, map_location=device))
    attn_model.to(device)
    attn_model.eval()

    # We'll need a helper to get attention and prediction from the model
    from torch_geometric.data import Data
    from rdkit import Chem
    from torch_geometric.utils import from_smiles
    # Actually, we can use the predictor has _smiles_to_graph method
    # Let's define a function to get prediction and attention
    def get_pred_and_attention(smiles):
        # Use predictor's internal methods to get graph and then run model
        data = predictor._smiles_to_graph(smiles)
        if data is None:
            return None, None
        from torch_geometric.data import Batch
        batch = Batch.from_data_list([data]).to(device)
        with torch.no_grad():
            _, output, attn_info = attn_model(batch, return_attention=True)
            prob = torch.sigmoid(output).cpu().numpy()[0]
            attention = attn_info['attention_weights'].cpu().numpy()
        return prob, attention

    # For simplicity, we'll rely on predictor.predict_with_attention if we add it to UnifiedPredictor.
    # Instead, let's modify UnifiedPredictor to have a predict_with_attention method.
    # But we cannot modify the class in this script? We can monkey-patch.
    # Given time, we'll assume we have a function that returns prob and attention.
    # We'll implement a simple version using the model directly.

    # Load Groq client
    from groq import Groq
    groq_client = Groq(api_key=os.environ['GROQ_API_KEY'])

    # Load Tox21 test set
    import pandas as pd
    df = pd.read_csv('data_packages/tox21_model_full_package/data/tox21/tox21.csv')
    test_smiles = df['smiles'].dropna().tolist()[-args.n_molecules:]  # last n as "test"

    # We'll need to implement the loop using our get_pred_and_attention
    # Let's rewrite the main loop here.
    results = {
        'constrained': [],
        'unconstrained': [],
        'molecules': []
    }

    for smiles in tqdm(test_smiles, desc="Evaluating molecules"):
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue

        try:
            prob, attention = get_pred_and_attention(smiles)
            if prob is None:
                continue

            # Get evidence (high attention substructures)
            evidence = get_high_attention_atoms(mol, attention, tau=0.1)
            evidence_names = [e['name'] for e in evidence]

            # Get counterfactuals
            cf_results = generate_counterfactuals(
                mol, [(e['name'], e['smarts']) for e in evidence],
                lambda m: get_pred_and_attention(Chem.MolToSmiles(m))[0] if Chem.MolToSmiles(m) else 0.0
            )

            # --- UNCONSTRAINED BASELINE ---
            unconc_response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{
                    "role": "user",
                    "content": UNCONSTRAINED_PROMPT.format(smiles=smiles, prob=prob)
                }]
            )
            unconc_text = unconc_response.choices[0].message.content

            unconc_claimed = extract_claimed_atoms(unconc_text, mol, TOXICOPHORES)
            unconc_score = validate_explanation(
                unconc_text,
                unconc_claimed,
                attention,
                cf_results
            )

            # --- CONSTRAINED (DENOVO) ---
            conc_response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{
                    "role": "user",
                    "content": CONSTRAINED_PROMPT.format(
                        smiles=smiles,
                        prob=prob,
                        evidence=", ".join(evidence_names) if evidence_names else "none identified"
                    )
                }]
            )
            conc_text = conc_response.choices[0].message.content
            # For constrained, the claimed atoms are the evidence atoms
            conc_claimed = [e['atom_indices'] for e in evidence]
            conc_claimed_flat = [i for sublist in conc_claimed for i in sublist]

            conc_score = validate_explanation(
                conc_text,
                conc_claimed_flat,
                attention,
                cf_results
            )

            results['unconstrained'].append(unconc_score['faithfulness_score'])
            results['constrained'].append(conc_score['faithfulness_score'])
            results['molecules'].append(smiles)

        except Exception as e:
            print(f"Skipping {smiles}: {e}")
            continue

    # Compute statistics
    u_scores = np.array(results['unconstrained'])
    c_scores = np.array(results['constrained'])

    summary = {
        'n_molecules': len(results['molecules']),
        'unconstrained': {
            'mean': float(np.mean(u_scores)) if len(u_scores) > 0 else 0.0,
            'median': float(np.median(u_scores)) if len(u_scores) > 0 else 0.0,
            'std': float(np.std(u_scores)) if len(u_scores) > 0 else 0.0
        },
        'constrained_denovo': {
            'mean': float(np.mean(c_scores)) if len(c_scores) > 0 else 0.0,
            'median': float(np.median(c_scores)) if len(c_scores) > 0 else 0.0,
            'std': float(np.std(c_scores)) if len(c_scores) > 0 else 0.0
        },
        'improvement': float(np.mean(c_scores) - np.mean(u_scores)) if len(c_scores) > 0 else 0.0,
        'rejection_rate': float(np.mean(c_scores < 0.6)) if len(c_scores) > 0 else 0.0
    }

    # Statistical test
    if len(c_scores) > 1:
        from scipy import stats
        t_stat, p_value = stats.ttest_rel(c_scores, u_scores)
        summary['paired_ttest'] = {
            't_statistic': float(t_stat) if not np.isnan(t_stat) else 0.0,
            'p_value': float(p_value) if not np.isnan(p_value) else 1.0,
            'significant': bool(p_value < 0.05) if not np.isnan(p_value) else False
        }
    else:
        summary['paired_ttest'] = {
            't_statistic': 0.0,
            'p_value': 1.0,
            'significant': False
        }

    print("\n=== BASELINE FAITHFULNESS RESULTS ===")
    print(f"N molecules: {summary['n_molecules']}")
    print(f"Unconstrained LLM: {summary['unconstrained']['mean']:.3f} ± {summary['unconstrained']['std']:.3f}")
    print(f"DeNovo constrained: {summary['constrained_denovo']['mean']:.3f} ± {summary['constrained_denovo']['std']:.3f}")
    print(f"Improvement: +{summary['improvement']:.3f}")
    print(f"p-value: {summary['paired_ttest']['p_value']:.4f} ({'significant' if summary['paired_ttest']['significant'] else 'not significant'})")

    with open(args.output, 'w') as f:
        json.dump({**summary, 'raw': results}, f, indent=2)

    print(f"Results saved to {args.output}")