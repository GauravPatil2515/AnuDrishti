import sys
sys.path.insert(0, '.')

from utils.counterfactual_generator import CounterfactualGenerator
from models.unified_predictor import UnifiedADMETPredictor

cf_gen = CounterfactualGenerator()
predictor = UnifiedADMETPredictor(enable_ensemble=False)

def test_molecule(name, smiles, expected_to_reduce=True):
    print(f"\n{'='*60}")
    print(f"Testing {name}: {smiles}")
    print('='*60)
    
    try:
        # Get baseline
        base_res = predictor.predict(smiles)
        base_tox = 0.0
        if 'summary' in base_res:
            base_tox = float(base_res.get('summary', {}).get('average_toxicity_probability', 0.0) or 0.0)
        print(f"Baseline toxicity: {base_tox:.3f}")
        
        # Generate candidates
        candidates = cf_gen.generate_optimization_candidates(smiles, n_variants=6)
        print(f"Generated {len(candidates)} raw candidates")
        
        # Process as the fixed code would (simulate the logic in tasks.py)
        filtered = []
        skipped = []
        for cf in candidates:
            try:
                cf_res = predictor.predict(cf.modified_smiles)
                cf_tox = 0.0
                if 'summary' in cf_res:
                    cf_tox = float(cf_res.get('summary', {}).get('average_toxicity_probability', 0.0) or 0.0)
                toxicity_reduction = base_tox - cf_tox  # positive = reduction
                
                if toxicity_reduction < -0.01:  # this means cf_tox > base_tox + 0.01 (increase)
                    skipped.append((cf, cf_tox, toxicity_reduction))
                else:
                    filtered.append((cf, cf_tox, toxicity_reduction))
                    
            except Exception as e:
                print(f"  Error predicting {cf.modified_smiles}: {e}")
                skipped.append((cf, None, None))  # error case
        
        print(f"  Kept: {len(filtered)} candidates")
        print(f"  Skipped: {len(skipped)} candidates (increase toxicity or error)")
        
        if filtered:
            print("  Kept candidates:")
            for cf, cf_tox, reduction in filtered:
                status = "REDUCTION" if reduction > 0.01 else "INCREASE" if reduction < -0.01 else "NO CHANGE"
                print(f"    {cf.modification_description:30} -> {cf.modified_smiles:25} {cf_tox:.3f} ({reduction:+.3f}) {status}")
        
        if skipped:
            print("  Skipped candidates:")
            for cf, cf_tox, reduction in skipped:
                if cf_tox is not None:
                    status = "REDUCTION" if reduction > 0.01 else "INCREASE" if reduction < -0.01 else "NO CHANGE"
                    print(f"    {cf.modification_description:30} -> {cf.modified_smiles:25} {cf_tox:.3f} ({reduction:+.3f}) {status}")
                else:
                    print(f"    {cf.modification_description:30} -> {cf.modified_smiles:25} ERROR")
        
        # Check if any kept candidates actually increase toxicity (they shouldn't)
        increases = [f for f in filtered if f[2] < -0.01]
        if increases:
            print(f"\n  ❌ FAILURE: {len(increases)} kept candidates increase toxicity!")
            for cf, cf_tox, reduction in increases:
                print(f"     {cf.modification_description}: {cf_tox:.3f} (change {reduction:+.3f})")
            return False
        else:
            print(f"\n  ✅ SUCCESS: No kept candidates increase toxicity")
            return True
            
    except Exception as e:
        print(f"  Error processing {name}: {e}")
        return False

# Test molecules
test_cases = [
    ("nitrobenzene", "c1ccccc1[N+](=O)[O-]"),
    ("benzene", "c1ccccc1"),
    ("phenol", "c1ccccc1[OH]"),
    ("aniline", "c1ccccc1[NH2]"),
    ("nitromethane", "C[N+](=O)[O-]"),
    ("toluene", "Cc1ccccc1"),
    ("chlorobenzene", "c1ccccc1Cl"),
    ("pyridine", "c1ccncc1"),
]

all_passed = True
for name, smiles in test_cases:
    passed = test_molecule(name, smiles)
    if not passed:
        all_passed = False

print(f"\n{'='*60}")
if all_passed:
    print("🎉 ALL TESTS PASSED: Fix is working correctly!")
else:
    print("❌ SOME TESTS FAILED: Fix needs more work")
print('='*60)
