import numpy as np
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from collections import defaultdict
import random

def generate_scaffold(smiles, include_chirality=False):
    """Compute the Bemis-Murcko scaffold for a SMILES string."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return ""
    scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=include_chirality)
    return scaffold

def scaffold_split(smiles_list, fractions=(0.7, 0.15, 0.15), balanced=True, seed=42):
    """
    Split dataset by Bemis-Murcko scaffolds.
    Returns the indices for train, val, and test sets.
    """
    assert sum(fractions) == 1.0, "Split fractions must sum to 1."
    
    scaffolds = defaultdict(list)
    for i, smiles in enumerate(smiles_list):
        scaffold = generate_scaffold(smiles)
        scaffolds[scaffold].append(i)
        
    # Sort scaffolds by size (descending) to place large scaffolds first
    scaffold_sets = [scaffold_set for (scaffold, scaffold_set) in sorted(scaffolds.items(), key=lambda x: (len(x[1]), x[1][0]), reverse=True)]
    
    random.seed(seed)
    if not balanced:
        random.shuffle(scaffold_sets)
        
    n_total = len(smiles_list)
    train_cutoff = fractions[0] * n_total
    val_cutoff = (fractions[0] + fractions[1]) * n_total
    
    train_idx, val_idx, test_idx = [], [], []
    train_scaffolds, val_scaffolds, test_scaffolds = set(), set(), set()
    
    for scaffold_set in scaffold_sets:
        # We need the scaffold string for logging purposes. It's safe to recompute or we can get it from the indices.
        scaffold_str = generate_scaffold(smiles_list[scaffold_set[0]])
        
        if len(train_idx) + len(scaffold_set) > train_cutoff and fractions[2] > 0 and fractions[1] > 0:
            if len(val_idx) + len(scaffold_set) > val_cutoff:
                test_idx.extend(scaffold_set)
                test_scaffolds.add(scaffold_str)
            else:
                val_idx.extend(scaffold_set)
                val_scaffolds.add(scaffold_str)
        else:
            train_idx.extend(scaffold_set)
            train_scaffolds.add(scaffold_str)
            
    print(f"Total Unique Scaffolds: {len(scaffolds)}")
    print(f"Train Scaffolds: {len(train_scaffolds)} | Val Scaffolds: {len(val_scaffolds)} | Test Scaffolds: {len(test_scaffolds)}")
    
    # Check leakage
    train_test_overlap = train_scaffolds.intersection(test_scaffolds)
    if len(train_test_overlap) > 0:
        print(f"WARNING: Scaffold leakage detected! Overlap: {len(train_test_overlap)}")
    else:
        print("SUCCESS: 0 Scaffold leakage between Train and Test.")
        
    return train_idx, val_idx, test_idx
