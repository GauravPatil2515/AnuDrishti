#!/usr/bin/env python3
"""
Download Tox21 Dataset
======================
Downloads Tox21 dataset from official sources

Usage:
    python download_data.py --dataset tox21 --output data/raw/
"""

import os
import argparse
import requests
from pathlib import Path
from tqdm import tqdm


class Tox21Downloader:
    """Download Tox21 dataset"""
    
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Tox21 data URLs
        self.urls = {
            'tox21_train': 'https://tripod.nih.gov/tox21/challenge/download?id=tox21_10k_data_all',
            'tox21_test': 'https://tripod.nih.gov/tox21/challenge/download?id=tox21_10k_challenge_test',
            'tox21_score': 'https://tripod.nih.gov/tox21/challenge/download?id=tox21_10k_challenge_score'
        }
    
    def download_file(self, url, filename):
        """Download file with progress bar"""
        filepath = self.output_dir / filename
        
        print(f"\n📥 Downloading: {filename}")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f, tqdm(
                total=total_size,
                unit='B',
                unit_scale=True,
                desc=filename
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
            
            print(f"✅ Downloaded: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Error downloading {filename}: {e}")
            return False
    
    def download_tox21(self):
        """Download Tox21 dataset"""
        print("\n" + "=" * 70)
        print("DOWNLOADING TOX21 DATASET")
        print("=" * 70)
        
        success_count = 0
        
        for name, url in self.urls.items():
            filename = f"{name}.sdf"
            if self.download_file(url, filename):
                success_count += 1
        
        print("\n" + "=" * 70)
        print(f"✅ Downloaded {success_count}/{len(self.urls)} files")
        print("=" * 70)
        
        if success_count > 0:
            print(f"\nFiles saved to: {self.output_dir}")
            print("\nNext steps:")
            print("1. Preprocess data: python scripts/preprocess_data.py")
            print("2. Train models: python scripts/train_models.py")


def create_sample_data(output_dir):
    """Create sample Tox21 data for testing"""
    import pandas as pd
    import numpy as np
    
    print("\n📝 Creating sample Tox21 data for testing...")
    
    # Sample SMILES strings (common molecules)
    sample_smiles = [
        'CCO',  # Ethanol
        'CC(=O)O',  # Acetic acid
        'c1ccccc1',  # Benzene
        'CC(C)O',  # Isopropanol
        'CC(=O)Nc1ccc(O)cc1',  # Paracetamol
        'CC(C)Cc1ccc(C(C)C(=O)O)cc1',  # Ibuprofen
        'CN1C=NC2=C1C(=O)N(C(=O)N2C)C',  # Caffeine
        'CC(C)(C)NCC(COc1ccccc1)O',  # Propranolol
        'CC1=CC=C(C=C1)C(=O)O',  # p-Toluic acid
        'c1ccc2c(c1)ccc3c2ccc4c3cccc4',  # Anthracene
    ]
    
    # Duplicate to create more samples
    smiles_list = sample_smiles * 100  # 1000 samples
    
    # Create random labels for 12 endpoints
    endpoints = [
        'NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-ER', 'NR-ER-LBD', 'NR-PPAR-gamma',
        'NR-Aromatase', 'SR-ARE', 'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53'
    ]
    
    data = {'smiles': smiles_list}
    
    np.random.seed(42)
    for endpoint in endpoints:
        # Create imbalanced labels (more 0s than 1s)
        data[endpoint] = np.random.choice([0, 1], size=len(smiles_list), p=[0.85, 0.15])
    
    df = pd.DataFrame(data)
    
    # Save sample data
    output_path = Path(output_dir) / 'processed'
    output_path.mkdir(parents=True, exist_ok=True)
    
    sample_file = output_path / 'tox21_sample_data.csv'
    df.to_csv(sample_file, index=False)
    
    print(f"✅ Sample data created: {sample_file}")
    print(f"   Samples: {len(df)}")
    print(f"   Endpoints: {len(endpoints)}")
    print("\nYou can use this for testing:")
    print(f"python scripts/train_models.py --data {sample_file}")
    
    return df


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Download Tox21 dataset')
    parser.add_argument('--dataset', type=str, default='tox21', choices=['tox21', 'sample'],
                       help='Dataset to download (tox21 or sample for testing)')
    parser.add_argument('--output', type=str, default='data/raw',
                       help='Output directory')
    
    args = parser.parse_args()
    
    if args.dataset == 'sample':
        # Create sample data for testing
        create_sample_data(args.output.replace('raw', ''))
    else:
        # Download real Tox21 data
        downloader = Tox21Downloader(args.output)
        downloader.download_tox21()
        
        print("\n" + "=" * 70)
        print("⚠️ NOTE: If download fails, please download manually:")
        print("=" * 70)
        print("\n1. Visit: https://tripod.nih.gov/tox21/challenge/")
        print("2. Click 'Data' tab")
        print("3. Download 'Training Data' (tox21_10k_data_all.sdf)")
        print(f"4. Place in: {args.output}/")
        print("\nOr use sample data for testing:")
        print("python scripts/download_data.py --dataset sample")


if __name__ == "__main__":
    main()
