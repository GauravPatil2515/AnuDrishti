#!/usr/bin/env python3
"""
Create final comparison table for paper.
This script generates a CSV template for the final comparison table.
"""

import os
from datetime import datetime

def main():
    # Define the template for the comparison table
    # NOTE: Replace TBD values with actual experimental results
    template = """Dataset,Method,TOX21_AUROC,BBBP_AUROC,ClinTox_AUROC
Tox21,Ours (V2-foundation-arch),TBD,TBD,TBD
Tox21,ChemProp (D-MPNN),0.8023,0.8971,0.7589
Tox21,Uni-Mol [Literature],0.918,0.924,0.931
Tox21,Mole-BERT [Literature],TBD,TBD,TBD
BBBP,Ours (V2-foundation-arch),TBD,TBD,TBD
BBBP,ChemProp (D-MPNN),0.8023,0.8971,0.7589
BBBP,Uni-Mol [Literature],0.918,0.924,0.931
BBBP,Mole-BERT [Literature],TBD,TBD,TBD
ClinTox,Ours (V2-foundation-arch),TBD,TBD,TBD
ClinTox,ChemProp (D-MPNn),0.8023,0.8971,0.7589
ClinTox,Uni-Mol [Literature],0.918,0.924,0.931
ClinTox,Mole-BERT [Literature],TBD,TBD,TBD
"""

    # Create the output directory if it doesn't exist
    output_dir = "/home/gaurav/Desktop/gaurav code /Paper/denovo/Faithful-LLM-Augmented-Explainability-for-Graph-Neural-Network-Based-Molecular-Toxicity-Prediction/benchmark_results"
    os.makedirs(output_dir, exist_ok=True)

    # Write the template to a CSV file
    output_path = os.path.join(output_dir, "final_comparison_table.csv")
    with open(output_path, 'w') as f:
        f.write(template)

    print(f"Created template for final comparison table at: {output_path}")
    print("NOTE: Replace TBD values with actual experimental results before paper submission.")

if __name__ == "__main__":
    main()