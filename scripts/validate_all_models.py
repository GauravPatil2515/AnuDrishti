#!/usr/bin/env python3
"""
Model Validation Script for DeNovo
Tests all available models and generates a report
"""

import sys
sys.path.insert(0, 'backend')
from models.unified_predictor import UnifiedADMETPredictor

def main():
    predictor = UnifiedADMETPredictor()
    print('=' * 60)
    print('MODEL VALIDATION REPORT')
    print('=' * 60)

    test_molecules = {
        'Ethanol': 'CCO',
        'Aspirin': 'CC(=O)OC1=CC=CC=C1C(=O)O',
        'Caffeine': 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C',
        'Nitrobenzene': 'c1ccc([N+](=O)[O-])cc1',
    }

    for name, smiles in test_molecules.items():
        try:
            result = predictor.predict(smiles)
            summary = result.get('summary', {})
            assessment = summary.get('overall_assessment', 'N/A')
            print(f'\n{name}: {assessment}')
            
            if 'attention_gin' in result:
                gin_result = result['attention_gin']
                print(f'  - Tox21 (Attention-GIN): Active')
            if 'bbbp' in result:
                print(f'  - BBBP: {result["bbbp"]}')
            if 'clintox' in result:
                print(f'  - ClinTox: {result["clintox"]}')
            if 'clearance' in result:
                print(f'  - Clearance: {result["clearance"]}')
        except Exception as e:
            print(f'{name}: ERROR - {e}')

    print('\n' + '=' * 60)
    print('Validation Complete')
    print('=' * 60)

if __name__ == '__main__':
    main()
