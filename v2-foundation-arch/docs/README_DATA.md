# Datasets

## MoleculeNet
- Tox21: 7,836 molecules, 12 toxicity endpoints
- BBBP: 2,050 molecules, blood-brain barrier penetration
- ClinTox: 1,418 molecules, clinical trial toxicity
- SIDER: 1,427 molecules, drug side effects
- BACE: 1,513 molecules, blood-brain barrier permeability

## Data Processing
1. Download from MoleculeNet or DeepChem
2. Scaffold split (80/10/10) for train/val/test
3. RDKit processing for 3D conformers
4. SMILES tokenization with ChemBERTa vocab

## Expected Data Structure
```
data/
├── raw/
│   ├── tox21.csv
│   ├── bbbp.csv
│   └── clintox.csv
├── processed/
│   ├── tox21.pt
│   ├── bbbp.pt
│   └── clintox.pt
└── splits/
    ├── tox21_train.pt
    ├── tox21_val.pt
    └── tox21_test.pt
```

## Preprocessing Script
```python
python v2-foundation-arch/scripts/preprocess_moleculenet.py
```