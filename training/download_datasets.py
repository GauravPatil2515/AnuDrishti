#!/usr/bin/env python3
"""
ADMET Dataset Downloader
========================
Downloads datasets for all ADMET model training.

Datasets are from MoleculeNet and proprietary sources.
"""

import os
import sys
import requests
import pandas as pd
from pathlib import Path

# Dataset URLs (MoleculeNet and DeepChem)
DATASET_URLS = {
    'tox21': 'https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz',
    'clintox': 'https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/clintox.csv.gz',
    'bbbp': 'https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/BBBP.csv',
    'caco2': 'https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/caco2_wang.csv',
    'clearance': 'https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/clearance.csv',
    # HLM_CLint is often proprietary or part of larger datasets
}

# Expected columns for each dataset
DATASET_COLUMNS = {
    'tox21': ['smiles'] + [f'NR-{x}' for x in ['AR', 'AR-LBD', 'AhR', 'Aromatase', 'ER', 'ER-LBD', 'PPAR-gamma']] + 
             [f'SR-{x}' for x in ['ARE', 'ATAD5', 'HSE', 'MMP', 'p53']],
    'clintox': ['smiles', 'FDA_APPROVED', 'CT_TOX'],
    'bbbp': ['smiles', 'p_np'],  # p_np = permeability
    'caco2': ['smiles', 'permeability'],
    'clearance': ['smiles', 'clearance'],
}

def download_file(url, dest_path):
    """Download a file with progress indication"""
    print(f"  📥 Downloading from: {url}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(dest_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    pct = (downloaded / total_size) * 100
                    print(f"\r  Progress: {pct:.1f}%", end='', flush=True)
            print()
        
        print(f"  ✅ Saved to: {dest_path}")
        return True
        
    except Exception as e:
        print(f"  ❌ Download failed: {e}")
        return False

def prepare_dataset(df, dataset_name, output_dir):
    """Prepare dataset with train/valid/test splits"""
    print(f"\n  📊 Preparing {dataset_name} dataset...")
    print(f"     Total samples: {len(df)}")
    
    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Split: 80% train, 10% valid, 10% test
    n = len(df)
    train_end = int(n * 0.8)
    valid_end = int(n * 0.9)
    
    train_df = df.iloc[:train_end]
    valid_df = df.iloc[train_end:valid_end]
    test_df = df.iloc[valid_end:]
    
    print(f"     Train: {len(train_df)}")
    print(f"     Valid: {len(valid_df)}")
    print(f"     Test: {len(test_df)}")
    
    # Save splits
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_dir / f"{dataset_name}.csv", index=False)
    train_df.to_csv(output_dir / "train.csv", index=False)
    valid_df.to_csv(output_dir / "valid.csv", index=False)
    test_df.to_csv(output_dir / "test.csv", index=False)
    
    print(f"  ✅ Saved splits to: {output_dir}")
    return True

def download_tox21(models_dir):
    """Download and prepare Tox21 dataset"""
    print("\n" + "="*50)
    print("📦 Tox21 Toxicity Dataset")
    print("="*50)
    
    data_dir = models_dir / "tox21_model_full_package" / "data" / "tox21"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if already exists
    if (data_dir / "tox21.csv").exists():
        print("  ✅ Dataset already exists")
        return True
    
    # Download
    temp_file = data_dir / "tox21.csv.gz"
    if download_file(DATASET_URLS['tox21'], temp_file):
        # Decompress
        import gzip
        with gzip.open(temp_file, 'rb') as f_in:
            with open(data_dir / "tox21.csv", 'wb') as f_out:
                f_out.write(f_in.read())
        temp_file.unlink()
        
        # Prepare splits
        df = pd.read_csv(data_dir / "tox21.csv")
        return prepare_dataset(df, "tox21", data_dir)
    
    return False

def download_clintox(models_dir):
    """Download and prepare ClinTox dataset"""
    print("\n" + "="*50)
    print("📦 ClinTox Clinical Toxicity Dataset")
    print("="*50)
    
    # Create ClinTox package directory
    package_dir = models_dir / "clintox_model_package"
    if not package_dir.exists():
        # Copy structure from tox21
        print("  📁 Creating ClinTox package from Tox21 template...")
        import shutil
        tox21_dir = models_dir / "tox21_model_full_package"
        shutil.copytree(tox21_dir, package_dir, ignore=shutil.ignore_patterns('data', '*.pth', '__pycache__'))
    
    data_dir = package_dir / "data" / "clintox"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    if (data_dir / "clintox.csv").exists():
        print("  ✅ Dataset already exists")
        return True
    
    # Download
    temp_file = data_dir / "clintox.csv.gz"
    if download_file(DATASET_URLS['clintox'], temp_file):
        import gzip
        with gzip.open(temp_file, 'rb') as f_in:
            with open(data_dir / "clintox.csv", 'wb') as f_out:
                f_out.write(f_in.read())
        temp_file.unlink()
        
        df = pd.read_csv(data_dir / "clintox.csv")
        return prepare_dataset(df, "clintox", data_dir)
    
    return False

def download_bbbp(models_dir):
    """Download and prepare BBBP dataset"""
    print("\n" + "="*50)
    print("📦 BBBP Blood-Brain Barrier Dataset")
    print("="*50)
    
    data_dir = models_dir / "bbbp_model_full_package" / "data" / "bbbp"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    if (data_dir / "bbbp.csv").exists():
        print("  ✅ Dataset already exists")
        return True
    
    dest_file = data_dir / "bbbp.csv"
    if download_file(DATASET_URLS['bbbp'], dest_file):
        df = pd.read_csv(dest_file)
        # Rename columns to match expected format
        if 'p_np' in df.columns:
            df = df.rename(columns={'p_np': 'label'})
        return prepare_dataset(df, "bbbp", data_dir)
    
    return False

def download_caco2(models_dir):
    """Download and prepare Caco2 dataset"""
    print("\n" + "="*50)
    print("📦 Caco-2 Permeability Dataset")
    print("="*50)
    
    data_dir = models_dir / "caco2_model_full_package" / "data" / "caco2"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    if (data_dir / "caco2.csv").exists():
        print("  ✅ Dataset already exists")
        return True
    
    dest_file = data_dir / "caco2.csv"
    if download_file(DATASET_URLS['caco2'], dest_file):
        df = pd.read_csv(dest_file)
        return prepare_dataset(df, "caco2", data_dir)
    return False

def download_clearance(models_dir):
    """Download and prepare Clearance dataset"""
    print("\n" + "="*50)
    print("📦 Intrinsic Clearance Dataset")
    print("="*50)
    
    data_dir = models_dir / "clearance_model_full_package" / "data" / "clearance"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    if (data_dir / "clearance.csv").exists():
        print("  ✅ Dataset already exists")
        return True
    
    dest_file = data_dir / "clearance.csv"
    if download_file(DATASET_URLS['clearance'], dest_file):
        df = pd.read_csv(dest_file)
        return prepare_dataset(df, "clearance", data_dir)
    return False

def create_placeholder_data(models_dir, dataset_name, package_name):
    """Create placeholder data for proprietary datasets"""
    print(f"\n" + "="*50)
    print(f"⚠️ {dataset_name} - Proprietary Dataset")
    print("="*50)
    
    data_dir = models_dir / package_name / "data" / dataset_name.lower()
    data_dir.mkdir(parents=True, exist_ok=True)
    
    placeholder_file = data_dir / "README.md"
    
    with open(placeholder_file, 'w') as f:
        f.write(f"""# {dataset_name} Dataset

This dataset requires proprietary data that cannot be automatically downloaded.

## Options:

1. **Use MoleculeNet version (if available)**
   - Check https://moleculenet.org/datasets-1 for public datasets

2. **Use your own data**
   - Prepare a CSV file with columns: `smiles`, `label`
   - Split into train.csv, valid.csv, test.csv
   - Place in this directory

3. **Contact dataset providers**
   - Some ADMET datasets are available from ChEMBL, PubChem, or pharmaceutical databases

## Expected Format:

```csv
smiles,label
CCO,0.5
c1ccccc1,1.2
...
```
""")
    
    print(f"  📝 Created placeholder at: {placeholder_file}")
    print(f"  ⚠️ You need to provide your own data for {dataset_name}")
    return False

def main():
    print("="*60)
    print("🧬 ADMET Dataset Downloader")
    print("="*60)
    
    project_dir = Path(__file__).parent.parent
    models_dir = project_dir / "MODELS"
    
    print(f"\n📂 Models directory: {models_dir}")
    
    results = {}
    
    # Download available datasets
    results['tox21'] = download_tox21(models_dir)
    results['clintox'] = download_clintox(models_dir)
    results['bbbp'] = download_bbbp(models_dir)
    results['caco2'] = download_caco2(models_dir)
    results['clearance'] = download_clearance(models_dir)
    
    # Create placeholders for proprietary datasets
    results['hlm_clint'] = create_placeholder_data(models_dir, "HLM_CLint", "hlm_clint_model_full_package")
    
    # Summary
    print("\n" + "="*60)
    print("📋 DOWNLOAD SUMMARY")
    print("="*60)
    
    for name, success in results.items():
        status = "✅ Ready" if success else "⚠️ Needs data"
        print(f"  {name}: {status}")
    
    print("\n💡 Run training with: python training/train_all_models.py")

if __name__ == "__main__":
    main()
