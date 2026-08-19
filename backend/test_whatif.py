import sys
import os
sys.path.insert(0, '.')

try:
    from models.unified_predictor import UnifiedADMETPredictor
    from utils.counterfactual_generator import CounterfactualGenerator
    print("Imports successful")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

predictor = UnifiedADMETPredictor(enable_ensemble=False)
cf_gen = CounterfactualGenerator()

# Test molecules
test_molecules = [
    ('nitrobenzene', 'c1ccccc1[N+](=O)[O-]'),
    ('benzene', 'c1ccccc1'),
    ('phenol', 'c1ccccc1[OH]'),
    ('aniline', 'c1ccccc1[NH2]'),
    ('nitromethane', 'C[N+](=O)[O-]'),
    ('toluene', 'Cc1ccccc1'),
    ('chlorobenzene', 'c1ccccc1Cl'),
]

for name, smiles in test_molecules:
    print(f'\n{name}: {smiles}')
    try:
        # Get baseline
        base_res = predictor.predict(smiles)
        base_tox = base_res.get('summary', {}).get('average_toxicity_probability', 0.0)
        print(f'  Baseline toxicity: {base_tox:.3f}')
        
        # Generate candidates (sync mode, small n_variants)
        candidates = cf_gen.generate_optimization_candidates(smiles, n_variants=6)
        print(f'  Generated {len(candidates)} candidates')
        
        # Evaluate each candidate
        higher_found = False
        for i, cf in enumerate(candidates):
            try:
                cf_res = predictor.predict(cf.modified_smiles)
                cf_tox = cf_res.get('summary', {}).get('average_toxicity_probability', 0.0)
                change = cf_tox - base_tox
                if change > 0.01:  # significant increase
                    print(f'    {i}: {cf.modification_description} -> {cf.modified_smiles}')
                    print(f'        Toxicity: {cf_tox:.3f} (change: +{change:.3f}) HIGHER!')
                    higher_found = True
                elif change < -0.01:
                    print(f'    {i}: {cf.modification_description} -> {cf.modified_smiles}')
                    print(f'        Toxicity: {cf_tox:.3f} (change: {change:.3f}) lower')
                else:
                    print(f'    {i}: {cf.modification_description} -> {cf.modified_smiles}')
                    print(f'        Toxicity: {cf_tox:.3f} (change: {change:.3f}) ~same')
            except Exception as e:
                print(f'    {i}: Error predicting {cf.modified_smiles}: {e}')
        if not higher_found:
            print('  No candidates with significantly higher toxicity found.')
    except Exception as e:
        print(f'  Error processing {name}: {e}')
