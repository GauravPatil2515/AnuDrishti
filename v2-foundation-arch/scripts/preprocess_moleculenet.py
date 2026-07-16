#!/usr/bin/env python3
"""
Preprocess MoleculeNet datasets for v2-foundation-arch training.
"""

import deepchem as dc
from pathlib import Path

def download_tox21():
    tasks, datasets, transformers = dc.molnet.load_tox21()
    return datasets

def download_bbbp():
    tasks, datasets, transformers = dc.molnet.load_bbbp()
    return datasets

def download_clintox():
    tasks, datasets, transformers = dc.molnet.load_clintox()
    return datasets

if __name__ == "__main__":
    print("Downloading MoleculeNet datasets...")
    
    for loader, name in [(download_tox21, 'tox21'), (download_bbbp, 'bbbp'), (download_clintox, 'clintox')]:
        try:
            loader()
            print(f"✅ {name} downloaded")
        except Exception as e:
            print(f"❌ {name} failed: {e}")
    
    print("Dataset preparation complete")