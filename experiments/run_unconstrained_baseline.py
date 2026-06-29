#!/usr/bin/env python3
"""
Unconstrained LLM Baseline
==========================
Companion to ``run_faithful_eval.py``. Evaluates the *unconstrained* LLM
explanation baseline: the same molecule and the same GNN prediction are shown
to the same LLM, but WITHOUT the attention-derived evidence list and WITHOUT the
grounding constraint. The LLM is simply asked which toxicophores drive the
prediction.

Crucially, the resulting free-text claims are scored by the EXACT SAME
FaithfulnessValidator (grounding + causal-consistency, F = sqrt(S_causal *
S_grounding)). This isolates the effect of the reject-and-retry / constrained
generation mechanism: any gap between this baseline and the constrained DeNovo
pipeline is attributable to the constraint, not to a different metric.

This directly produces the constrained-vs-unconstrained delta reported in the
paper's Faithfulness Analysis.

Usage:
    python run_unconstrained_baseline.py \
        --model results/trained_models/attention_gin_model.pth \
        --output results/baseline_unconstrained_tox21 --n-molecules 200

Author: DeNovo-XAI Research Team
"""

import sys
import json
import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger('UnconstrainedBaseline')

SCRIPT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = SCRIPT_DIR.parent / 'backend'
sys.path.insert(0, str(SCRIPT_DIR))            # reuse smiles_to_data / load_test_data
sys.path.insert(0, str(BACKEND_DIR / 'models'))
sys.path.insert(0, str(BACKEND_DIR / 'utils'))


# Unconstrained prompt: molecule + prediction only. No attention evidence list,
# no "only cite high-attention atoms" instruction. This is the standard post-hoc
# rationalization setting that the constrained pipeline is meant to improve upon.
UNCONSTRAINED_PROMPT = """You are a toxicology expert analyzing a molecular toxicity prediction.

Molecule (SMILES): {smiles}
Predicted Toxicity: {prediction:.1%}

Identify the structural features (toxicophores) most likely responsible for this
toxicity prediction. Output MUST be valid JSON in this EXACT structure:

{{
  "executive_summary": "2-3 sentence summary of the toxicity risk",
  "primary_toxicophore": {{
    "name": "name of the most important toxic group",
    "mechanism": "brief mechanism explanation"
  }},
  "secondary_features": [
    {{"name": "feature name", "contribution": "how it contributes"}}
  ],
  "overall_mechanism": "detailed mechanism (2-3 sentences)",
  "confidence": 0.0-1.0
}}
"""


def parse_llm_json(response):
    """Robustly parse JSON from an LLM response, stripping markdown fences."""
    try:
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
        return json.loads(response.strip())
    except json.JSONDecodeError:
        return None


def map_claims_to_evidence(llm_output, smiles, toxicophore_db):
    """Map an unconstrained LLM's free-text toxicophore names to known SMARTS
    patterns and concrete atom indices in the molecule.

    The atoms are matched on the explicit-hydrogen molecule so indices align with
    the GNN attention vector (which is computed over Chem.AddHs(mol)). A claimed
    group that is not actually present in the molecule yields an empty atom list,
    which the validator correctly treats as ungrounded / non-causal -- exactly the
    failure mode an unconstrained LLM is prone to.
    """
    from rdkit import Chem

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return []
    mol = Chem.AddHs(mol)

    # Normalize DB keys for fuzzy name matching.
    db_keys = {k.replace('_', ' ').lower(): k for k in toxicophore_db}

    def best_db_match(name):
        if not name:
            return None
        n = name.replace('_', ' ').lower()
        # Exact / substring match in either direction.
        for norm, key in db_keys.items():
            if norm in n or n in norm:
                return key
        # Token overlap fallback.
        n_tokens = set(n.split())
        for norm, key in db_keys.items():
            if n_tokens & set(norm.split()):
                return key
        return None

    # Collect claimed names from primary + secondary.
    claimed_names = []
    primary = llm_output.get('primary_toxicophore', {}) or {}
    if primary.get('name'):
        claimed_names.append(primary['name'])
    for sec in llm_output.get('secondary_features', []) or []:
        if isinstance(sec, dict) and sec.get('name'):
            claimed_names.append(sec['name'])

    evidence = []
    seen = set()
    for name in claimed_names:
        key = best_db_match(name)
        if key is None or key in seen:
            # Unmapped claim still counts as a claim, but with no SMARTS it cannot
            # be grounded or causally tested -> correctly penalized by the validator.
            evidence.append({'name': name, 'smarts_pattern': None, 'atom_indices': []})
            continue
        seen.add(key)
        smarts = toxicophore_db[key]['smarts']
        patt = Chem.MolFromSmarts(smarts)
        atoms = []
        if patt is not None:
            for match in mol.GetSubstructMatches(patt):
                atoms.extend(match)
        evidence.append({
            'name': name,
            'smarts_pattern': smarts,
            'atom_indices': sorted(set(atoms)),
        })
    return evidence


def run_unconstrained_baseline(model_path, dataset_path, output_dir, n_molecules=200):
    import torch
    from attention_ginet import AttentionGINet
    from faithfulness_validator import FaithfulnessValidator
    from counterfactual_generator import CounterfactualGenerator
    from substructure_mapper import TOXICOPHORES
    from reasoner import GroqLLMProvider, MockLLMProvider
    from run_faithful_eval import smiles_to_data, load_test_data

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 70)
    logger.info("UNCONSTRAINED LLM BASELINE")
    logger.info("=" * 70)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = AttentionGINet(num_tasks=12)
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict.get('model_state_dict', state_dict))
    model.to(device).eval()
    logger.info(f"Model loaded on {device}")

    validator = FaithfulnessValidator(
        model=model,
        counterfactual_generator=CounterfactualGenerator(),
    )

    try:
        llm = GroqLLMProvider()
        if not llm.is_available():
            logger.warning("Groq unavailable -> Mock LLM (baseline numbers will be meaningless)")
            llm = MockLLMProvider()
    except Exception:
        llm = MockLLMProvider()

    df_test = load_test_data(dataset_path)
    if len(df_test) > n_molecules:
        df_test = df_test.head(n_molecules)
    logger.info(f"Evaluating {len(df_test)} molecules (unconstrained)")

    results = []
    for idx, row in tqdm(df_test.iterrows(), total=len(df_test), desc="Baseline"):
        smiles = row['smiles']
        try:
            data = smiles_to_data(smiles, device)
            if data is None:
                continue
            with torch.no_grad():
                _, predictions, attention_info = model(data, return_attention=True)
            probs = torch.sigmoid(predictions).cpu().numpy()[0]
            avg_toxicity = float(np.mean(probs))
            attention_weights = attention_info['attention_weights'].cpu().numpy()

            # Unconstrained generation: no evidence list provided.
            prompt = UNCONSTRAINED_PROMPT.format(smiles=smiles, prediction=avg_toxicity)
            response = llm.generate(prompt, max_tokens=800, temperature=0.2)
            llm_output = parse_llm_json(response)
            if llm_output is None:
                results.append({
                    'smiles': smiles, 'prediction': avg_toxicity,
                    'faithfulness_score': 0.0, 'validation_passed': False,
                    'n_claims': 0, 'score_causal': None, 'score_grounding': None,
                    'parse_failed': True,
                })
                continue

            claims = map_claims_to_evidence(llm_output, smiles, TOXICOPHORES)
            explanation = {'identified_toxicophores': claims}

            # Score with the SAME validator used by the constrained pipeline.
            fs = validator.validate(
                explanation, smiles, avg_toxicity, attention_weights,
                run_counterfactual_test=False,  # only causal+grounding feed F
            )
            results.append({
                'smiles': smiles,
                'prediction': avg_toxicity,
                'faithfulness_score': fs.overall_score,
                'validation_passed': fs.passed,
                'n_claims': fs.n_claims,
                'score_causal': fs.causal_consistency.score,
                'score_grounding': fs.grounding.score,
                'parse_failed': False,
            })
        except Exception as e:
            logger.error(f"Failed on {smiles[:40]}: {e}")
            continue

    df = pd.DataFrame(results)
    df_claims = df[df['n_claims'] > 0] if len(df) else df

    stats = {
        'baseline': 'unconstrained_llm',
        'n_evaluated': int(len(df)),
        'mean_faithfulness': float(df['faithfulness_score'].mean()) if len(df) else None,
        'std_faithfulness': float(df['faithfulness_score'].std()) if len(df) else None,
        'median_faithfulness': float(df['faithfulness_score'].median()) if len(df) else None,
        'rejection_rate': float(1 - df['validation_passed'].mean()) if len(df) else None,
        'mean_grounding': float(df['score_grounding'].dropna().mean()) if len(df) else None,
        'mean_causal': float(df['score_causal'].dropna().mean()) if len(df) else None,
        'n_with_claims': int(len(df_claims)),
        'n_without_claims': int(len(df) - len(df_claims)),
        'mean_faithfulness_claims': float(df_claims['faithfulness_score'].mean()) if len(df_claims) else None,
        'parse_failure_rate': float(df['parse_failed'].mean()) if len(df) else None,
    }

    df.to_csv(output_dir / 'results.csv', index=False)
    with open(output_dir / 'statistics.json', 'w') as f:
        json.dump(stats, f, indent=2)

    logger.info("=" * 70)
    logger.info("UNCONSTRAINED BASELINE COMPLETE")
    if stats['mean_faithfulness'] is not None:
        logger.info(f"Mean F (all):          {stats['mean_faithfulness']:.3f}")
        logger.info(f"Mean F (claim-bearing): "
                    f"{stats['mean_faithfulness_claims'] if stats['mean_faithfulness_claims'] is None else round(stats['mean_faithfulness_claims'],3)}")
        logger.info(f"Mean grounding:        {stats['mean_grounding']:.3f}")
        logger.info(f"Mean causal:           {stats['mean_causal']:.3f}")
    logger.info("Compare these against results/<constrained eval>/statistics.json")
    return stats


def main():
    parser = argparse.ArgumentParser(description='Unconstrained LLM faithfulness baseline')
    parser.add_argument('--model', required=True, help='Path to trained model')
    parser.add_argument('--dataset', type=str,
                        default='../data_packages/tox21_model_full_package/data/tox21/tox21.csv',
                        help='Path to dataset CSV')
    parser.add_argument('--output', type=str, default='./results/baseline_unconstrained',
                        help='Output directory')
    parser.add_argument('--n-molecules', type=int, default=200)
    args = parser.parse_args()

    run_unconstrained_baseline(
        model_path=args.model,
        dataset_path=args.dataset,
        output_dir=args.output,
        n_molecules=args.n_molecules,
    )


if __name__ == '__main__':
    main()
