#!/usr/bin/env python3
"""
Faithful XAI Evaluation Script
===============================
Comprehensive evaluation of faithful explanations on test sets.

Usage:
    python run_faithful_eval.py --model path/to/model.pth --output results/

Author: DeNovo-XAI Research Team
"""

import sys
import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import logging

# Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger('FaithfulEval')

# Add paths
SCRIPT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = SCRIPT_DIR.parent / 'backend'
sys.path.insert(0, str(BACKEND_DIR / 'models'))
sys.path.insert(0, str(BACKEND_DIR / 'utils'))


def load_test_data(dataset_path, split='test', task_cols=None):
    """Load test split from dataset."""
    df = pd.read_csv(dataset_path)
    
    # Simple split (last 10%)
    n = len(df)
    test_start = int(n * 0.9)
    df_test = df.iloc[test_start:].reset_index(drop=True)
    
    logger.info(f"Loaded {len(df_test)} test molecules")
    return df_test


def run_faithful_evaluation(
    model_path: str,
    dataset_path: str,
    output_dir: str,
    n_molecules: int = 100,
    validate_faithfulness: bool = True,
    disable_causal: bool = False,
    disable_counterfactual: bool = False,
    disable_grounding: bool = False,
    attention_threshold: float = 0.1,
    allow_mock: bool = False,
    min_prediction: float = 0.5
):
    """
    Run comprehensive faithful explanation evaluation.
    
    Args:
        model_path: Path to trained model
        dataset_path: Path to dataset CSV
        output_dir: Output directory
        n_molecules: Number of molecules to evaluate
        validate_faithfulness: Whether to run validation
        disable_*: Disable specific tests (for ablation)
        attention_threshold: Minimum attention for claims
    """
    import torch
    from attention_ginet import AttentionGINet
    from substructure_mapper import SubstructureMapper
    from counterfactual_generator import CounterfactualGenerator
    from faithfulness_validator import FaithfulnessValidator
    from constrained_explainer import ConstrainedExplainer
    from reasoner import get_llm_provider, assert_real_llm
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 70)
    logger.info("FAITHFUL XAI EVALUATION")
    logger.info("=" * 70)
    
    # 1. Load model
    logger.info(f"\n[1/6] Loading model from {model_path}...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    model = AttentionGINet(num_tasks=12)
    state_dict = torch.load(model_path, map_location=device)
    
    if 'model_state_dict' in state_dict:
        model.load_state_dict(state_dict['model_state_dict'])
    else:
        model.load_state_dict(state_dict)
    
    model.to(device)
    model.eval()
    logger.info(f"✅ Model loaded on {device}")
    
    # 2. Initialize components
    logger.info("\n[2/6] Initializing components...")
    
    substructure_mapper = SubstructureMapper()
    counterfactual_generator = CounterfactualGenerator()
    
    # Faithfulness validator with configurable tests
    validator = FaithfulnessValidator(
        model=model,
        counterfactual_generator=counterfactual_generator if not disable_counterfactual else None,
        attention_threshold=attention_threshold
    )
    
    # LLM: real provider (Groq/OpenAI). Refuses to silently fall back to a mock,
    # which is what previously injected fabricated numbers into results.
    llm = get_llm_provider(allow_mock=allow_mock)
    assert_real_llm(llm) if not allow_mock else None
    logger.info(f"LLM provider: {type(llm).__name__} "
                f"(model={getattr(llm, 'MODEL_ID', 'n/a')}, mock={getattr(llm, 'is_mock', False)})")
    
    explainer = ConstrainedExplainer(
        model=model,
        llm_provider=llm,
        substructure_mapper=substructure_mapper,
        faithfulness_validator=validator,
        attention_threshold=attention_threshold
    )
    
    logger.info("✅ All components initialized")
    
    # 3. Load test data
    logger.info(f"\n[3/6] Loading test data from {dataset_path}...")
    df_test = load_test_data(dataset_path)

    # Faithfulness of a toxicity explanation is only meaningful when the model
    # predicts the molecule as toxic (there must be a positive decision to
    # explain, and the causal test -- "removing the driver drops the prediction"
    # -- is undefined for an already-negative prediction). We therefore scan the
    # full test split and evaluate the first n_molecules whose max-endpoint
    # probability exceeds min_prediction, rather than the first n rows.
    logger.info(f"✅ Scanning {len(df_test)} test molecules for toxic-predicted "
                f"(max-endpoint prob >= {min_prediction}), target n={n_molecules}")
    
    # 4. Run evaluation
    logger.info(f"\n[4/6] Running evaluation...")
    logger.info(f"   Validation: {validate_faithfulness}")
    logger.info(f"   Tests: {'Causal' if not disable_causal else 'X-Causal'}, "
                f"{'Counterfactual' if not disable_counterfactual else 'X-CF'}, "
                f"{'Grounding' if not disable_grounding else 'X-Grounding'}")
    
    results = []
    explanations = []
    
    for idx, row in tqdm(df_test.iterrows(), total=len(df_test), desc="Evaluating"):
        if idx > 0 and idx % 10 == 0:
            logger.info(f"Processed {idx}/{len(df_test)} molecules...")
            
        smiles = row['smiles']
        
        try:
            # Convert SMILES to graph and predict
            data = smiles_to_data(smiles, device)
            if data is None:
                continue
            
            with torch.no_grad():
                features, predictions, attention_info = model(data, return_attention=True)

            # Toxicity signal = strongest endpoint (the one the molecule is most
            # flagged on). Averaging over 12 tasks dilutes any positive signal.
            probs = torch.sigmoid(predictions).cpu().numpy()[0]
            avg_toxicity = float(np.max(probs))

            # Skip molecules the model does not predict as toxic.
            if avg_toxicity < min_prediction:
                continue

            # Get attention
            attention_weights = attention_info['attention_weights'].cpu().numpy()
            
            # Generate explanation
            explanation = explainer.explain(
                smiles=smiles,
                prediction=avg_toxicity,
                attention_weights=attention_weights,
                validate=validate_faithfulness
            )
            
            # Store result
            result = {
                'smiles': smiles,
                'prediction': avg_toxicity,
                'faithfulness_score': explanation.faithfulness_score,
                'validation_passed': explanation.validation_passed,
                'rejection_reason': explanation.rejection_reason,
                'generation_attempts': explanation.generation_attempts,
                'n_toxicophores': len(explanation.identified_toxicophores)
            }
            
            # Add detailed scores if available
            details = getattr(explanation, 'faithfulness_details', {})
            if details:
                result['score_causal'] = details.get('causal_consistency', {}).get('score')
                result['score_counterfactual'] = details.get('counterfactual_sensitivity', {}).get('score')
                result['score_grounding'] = details.get('grounding', {}).get('score')
                
            results.append(result)
            
            # Store full explanation
            explanations.append({
                'smiles': smiles,
                'explanation': explanation.to_dict()
            })

            if len(results) >= n_molecules:
                break

        except Exception as e:
            logger.error(f"Failed on {smiles}: {e}")
            continue
    
    logger.info(f"✅ Evaluated {len(results)} molecules")
    
    # 5. Analyze results
    logger.info(f"\n[5/6] Analyzing results...")
    
    df_results = pd.DataFrame(results)
    
    # Faithfulness is only meaningfully defined for explanations that make at least
    # one falsifiable structural claim (n_toxicophores > 0). Molecules where the
    # mapper finds no toxicophore have nothing to verify, so their score is vacuous;
    # we report the claim-bearing subset separately to avoid inflating the headline.
    df_claims = df_results[df_results['n_toxicophores'] > 0]

    # Compute statistics
    stats = {
        'n_evaluated': len(df_results),
        'mean_faithfulness': df_results['faithfulness_score'].mean(),
        'std_faithfulness': df_results['faithfulness_score'].std(),
        'median_faithfulness': df_results['faithfulness_score'].median(),
        'rejection_rate': (1 - df_results['validation_passed'].mean()),
        'mean_generation_attempts': df_results['generation_attempts'].mean(),
        'mean_toxicophores_per_molecule': df_results['n_toxicophores'].mean(),
        # Claim-bearing subset (primary numbers for the paper)
        'n_with_claims': int(len(df_claims)),
        'n_without_claims': int(len(df_results) - len(df_claims)),
        'mean_faithfulness_claims': df_claims['faithfulness_score'].mean() if len(df_claims) else None,
        'std_faithfulness_claims': df_claims['faithfulness_score'].std() if len(df_claims) else None,
        'median_faithfulness_claims': df_claims['faithfulness_score'].median() if len(df_claims) else None,
        'rejection_rate_claims': (1 - df_claims['validation_passed'].mean()) if len(df_claims) else None,
        # Component means (present only when faithfulness_details were recorded);
        # enables the constrained-vs-unconstrained component breakdown.
        'mean_grounding': (df_results['score_grounding'].dropna().mean()
                           if 'score_grounding' in df_results.columns else None),
        'mean_causal': (df_results['score_causal'].dropna().mean()
                        if 'score_causal' in df_results.columns else None),
    }

    logger.info("Statistics (all molecules):")
    logger.info(f"  Mean Faithfulness Score: {stats['mean_faithfulness']:.3f} ± {stats['std_faithfulness']:.3f}")
    logger.info(f"  Median FS: {stats['median_faithfulness']:.3f}")
    logger.info(f"  Rejection Rate: {stats['rejection_rate']:.1%}")
    logger.info(f"  Avg Generation Attempts: {stats['mean_generation_attempts']:.2f}")
    logger.info(f"  Molecules with >=1 claim: {stats['n_with_claims']} "
                f"(without claims: {stats['n_without_claims']})")
    if stats['mean_faithfulness_claims'] is not None:
        logger.info("Statistics (claim-bearing subset):")
        logger.info(f"  Mean Faithfulness: {stats['mean_faithfulness_claims']:.3f} "
                    f"± {stats['std_faithfulness_claims']:.3f}")
        logger.info(f"  Rejection Rate: {stats['rejection_rate_claims']:.1%}")
    
    # 6. Save results
    logger.info(f"\n[6/6] Saving results to {output_dir}...")
    
    # Save results CSV
    df_results.to_csv(output_dir / 'results.csv', index=False)
    
    # Save statistics
    with open(output_dir / 'statistics.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Save full explanations
    with open(output_dir / 'explanations.json', 'w') as f:
        json.dump(explanations, f, indent=2)
    
    # Save rejection analysis
    if 'rejection_reason' in df_results.columns:
        rejection_counts = df_results['rejection_reason'].value_counts()
        rejection_counts.to_csv(output_dir / 'rejection_reasons.csv')
    
    logger.info("✅ Results saved")
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("EVALUATION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Faithfulness Score: {stats['mean_faithfulness']:.3f}")
    logger.info(f"Rejection Rate: {stats['rejection_rate']:.1%}")
    
    return stats


def smiles_to_data(smiles, device):
    """Convert SMILES to PyTorch Geometric Data."""
    try:
        from rdkit import Chem
        import torch
        from torch_geometric.data import Data
        
        # Load dataset utilities
        project_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(project_dir / 'data_packages' / 'tox21_model_full_package'))
        from dataset.dataset_test import ATOM_LIST, CHIRALITY_LIST, BOND_LIST, BONDDIR_LIST
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        mol = Chem.AddHs(mol)
        
        # Node features
        type_idx = []
        chirality_idx = []
        for atom in mol.GetAtoms():
            type_idx.append(ATOM_LIST.index(atom.GetAtomicNum()))
            chirality_idx.append(CHIRALITY_LIST.index(atom.GetChiralTag()))
        
        x1 = torch.tensor(type_idx, dtype=torch.long).view(-1, 1)
        x2 = torch.tensor(chirality_idx, dtype=torch.long).view(-1, 1)
        x = torch.cat([x1, x2], dim=-1)
        
        # Edge features
        row, col, edge_feat = [], [], []
        for bond in mol.GetBonds():
            start, end = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
            row += [start, end]
            col += [end, start]
            edge_feat.extend([
                [BOND_LIST.index(bond.GetBondType()), BONDDIR_LIST.index(bond.GetBondDir())],
                [BOND_LIST.index(bond.GetBondType()), BONDDIR_LIST.index(bond.GetBondDir())]
            ])
        
        if len(row) == 0:
            edge_index = torch.empty((2, 0), dtype=torch.long)
            edge_attr = torch.empty((0, 2), dtype=torch.long)
        else:
            edge_index = torch.tensor([row, col], dtype=torch.long)
            edge_attr = torch.tensor(np.array(edge_feat), dtype=torch.long)
        
        data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
        data.batch = torch.zeros(x.size(0), dtype=torch.long)
        
        return data.to(device)
        
    except Exception as e:
        logger.error(f"Failed to convert {smiles}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Run Faithful XAI Evaluation')
    
    parser.add_argument('--model', type=str, required=True,
                       help='Path to trained model')
    parser.add_argument('--dataset', type=str,
                       default='../data_packages/tox21_model_full_package/data/tox21/tox21.csv',
                       help='Path to dataset CSV')
    parser.add_argument('--output', type=str, default='./results/faithful_eval',
                       help='Output directory')
    parser.add_argument('--n-molecules', type=int, default=100,
                       help='Number of molecules to evaluate')
    parser.add_argument('--no-validation', action='store_true',
                       help='Skip faithfulness validation')
    
    # Ablation flags
    parser.add_argument('--disable-causal', action='store_true',
                       help='Disable causal consistency test')
    parser.add_argument('--disable-counterfactual', action='store_true',
                       help='Disable counterfactual sensitivity test')
    parser.add_argument('--disable-grounding', action='store_true',
                       help='Disable grounding test')
    
    parser.add_argument('--attention-threshold', type=float, default=0.1,
                       help='Attention threshold for claims')
    parser.add_argument('--allow-mock', action='store_true',
                       help='DEV ONLY: permit MockLLMProvider. Never use for paper numbers.')
    parser.add_argument('--min-prediction', type=float, default=0.5,
                       help='Only evaluate molecules whose max-endpoint toxicity >= this (default 0.5)')

    args = parser.parse_args()
    
    run_faithful_evaluation(
        model_path=args.model,
        dataset_path=args.dataset,
        output_dir=args.output,
        n_molecules=args.n_molecules,
        validate_faithfulness=not args.no_validation,
        disable_causal=args.disable_causal,
        disable_counterfactual=args.disable_counterfactual,
        disable_grounding=args.disable_grounding,
        attention_threshold=args.attention_threshold,
        allow_mock=args.allow_mock,
        min_prediction=args.min_prediction
    )


if __name__ == '__main__':
    main()
