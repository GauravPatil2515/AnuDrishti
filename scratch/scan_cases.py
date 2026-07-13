import json
from pathlib import Path

def scan_cases():
    json_path = Path('results/eval_tox21_200/explanations.json')
    with open(json_path) as f:
        data = json.load(f)
        
    print(f"Total cases: {len(data)}")
    
    # Filter for passed validation and at least one identified toxicophore
    good_cases = []
    for d in data:
        exp = d.get('explanation', {})
        if exp.get('validation_passed') and exp.get('identified_toxicophores') and len(exp['identified_toxicophores']) > 0:
            good_cases.append(d)
            
    print(f"Passed and has toxicophores: {len(good_cases)}")
    
    # Sort by prediction probability and faithfulness
    good_cases.sort(key=lambda x: (x['explanation']['prediction'], x['explanation']['faithfulness_score']), reverse=True)
    
    for i, gc in enumerate(good_cases[:10]):
        print(f"\n[{i}] SMILES: {gc['smiles']}")
        print(f"    Prediction: {gc['explanation']['prediction']:.3f}")
        print(f"    Faithfulness: {gc['explanation']['faithfulness_score']:.3f}")
        print(f"    Summary: {gc['explanation']['executive_summary']}")
        print(f"    Toxicophores: {[t['name'] for t in gc['explanation']['identified_toxicophores']]}")

if __name__ == "__main__":
    scan_cases()
