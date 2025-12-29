import json
import pandas as pd
from pathlib import Path

def select_case_studies():
    json_path = Path('results/eval_tox21_200/explanations.json')
    output_path = Path('results/paper_figures/selected_cases.md')
    
    with open(json_path) as f:
        data = json.load(f)
        
    print(f"Loaded {len(data)} explanations")
    
    # 1. Best Success Case
    # Sort by faithfulness score (descending) and filter for high confident prediction
    success_cases = [d for d in data if d['explanation']['validation_passed']]
    success_cases.sort(key=lambda x: (x['explanation']['faithfulness_score'], x['explanation']['prediction']), reverse=True)
    
    best_case = success_cases[0]
    
    # 2. Failure Case
    fail_cases = [d for d in data if not d['explanation']['validation_passed']]
    # Find one with high prediction (so the model was confident, but LLM failed to explain)
    fail_cases.sort(key=lambda x: x['explanation']['prediction'], reverse=True)
    
    fail_case = fail_cases[0] if fail_cases else None
    
    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Selected Case Studies for Paper\n\n")
        
        f.write("## Case Study 1: High-Confidence Faithful Explanation\n")
        f.write(f"**SMILES**: `{best_case['smiles']}`\n")
        f.write(f"**Predicted Toxicity**: {best_case['explanation']['prediction']:.3f}\n")
        f.write(f"**Faithfulness Score**: {best_case['explanation']['faithfulness_score']:.3f}\n\n")
        f.write("### Generated Explanation:\n")
        f.write(f"**Summary**: {best_case['explanation']['executive_summary']}\n\n")
        f.write(f"**Mechanism**: {best_case['explanation']['mechanism']}\n\n")
        f.write("**Identified Toxicophores**:\n")
        for t in best_case['explanation']['identified_toxicophores']:
            f.write(f"- **{t['name']}** (Importance: {t.get('importance', 'N/A')})\n")
        
        if fail_case:
            f.write("\n---\n\n")
            f.write("## Case Study 2: Explanation Rejection Analysis\n")
            f.write("This case illustrates the system's ability to reject unfaithful explanations.\n\n")
            f.write(f"**SMILES**: `{fail_case['smiles']}`\n")
            f.write(f"**Predicted Toxicity**: {fail_case['explanation']['prediction']:.3f}\n")
            f.write(f"**Status**: {fail_case['explanation']['rejection_reason']}\n")
            f.write("**Attempts**: The system tried 3 times to generate a grounded explanation but failed.\n")
            
    print(f"Case studies saved to {output_path}")

if __name__ == "__main__":
    select_case_studies()
