#!/usr/bin/env python3
"""
Tox21 Data Preprocessing Script
================================
Converts Tox21 SDF file to CSV format and prepares data for model training

Usage:
    python preprocess_data.py --input data/raw/tox21_10k_data_all.sdf --output data/processed/
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# RDKit imports
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    RDKIT_AVAILABLE = True
    print("✅ RDKit available")
except ImportError:
    RDKIT_AVAILABLE = False
    print("⚠️ RDKit not available - install with: pip install rdkit-pypi")
    sys.exit(1)


class Tox21Preprocessor:
    """Preprocess Tox21 SDF data for model training"""
    
    def __init__(self, input_file, output_dir):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Tox21 endpoints
        self.endpoints = [
            'NR-AR',
            'NR-AR-LBD',
            'NR-AhR',
            'NR-ER',
            'NR-ER-LBD',
            'NR-PPAR-gamma',
            'NR-Aromatase',
            'SR-ARE',
            'SR-ATAD5',
            'SR-HSE',
            'SR-MMP',
            'SR-p53'
        ]
    
    def read_sdf(self):
        """Read SDF file and extract molecules with properties"""
        print(f"\n📖 Reading SDF file: {self.input_file}")
        
        if not self.input_file.exists():
            raise FileNotFoundError(f"SDF file not found: {self.input_file}")
        
        # Read SDF file
        suppl = Chem.SDMolSupplier(str(self.input_file))
        
        data = []
        total_mols = 0
        valid_mols = 0
        
        for mol in suppl:
            total_mols += 1
            
            if mol is None:
                continue
            
            try:
                # Get SMILES
                smiles = Chem.MolToSmiles(mol)
                
                # Get properties
                props = mol.GetPropsAsDict()
                
                # Create row
                row = {'smiles': smiles}
                
                # Extract endpoint data
                for endpoint in self.endpoints:
                    # Tox21 uses different naming conventions
                    # Try multiple possible property names
                    possible_names = [
                        endpoint,
                        f'TOX21_{endpoint}',
                        f'{endpoint}_active',
                        endpoint.replace('-', '_')
                    ]
                    
                    value = None
                    for name in possible_names:
                        if name in props:
                            value = props[name]
                            break
                    
                    # Convert to binary (0/1)
                    if value is not None:
                        if isinstance(value, str):
                            if value.lower() in ['active', '1', 'true', 'yes']:
                                row[endpoint] = 1
                            elif value.lower() in ['inactive', '0', 'false', 'no']:
                                row[endpoint] = 0
                            else:
                                row[endpoint] = np.nan
                        else:
                            row[endpoint] = int(value) if value in [0, 1] else np.nan
                    else:
                        row[endpoint] = np.nan
                
                data.append(row)
                valid_mols += 1
                
                if valid_mols % 1000 == 0:
                    print(f"  Processed {valid_mols} valid molecules...")
                
            except Exception as e:
                print(f"  ⚠️ Error processing molecule {total_mols}: {e}")
                continue
        
        print(f"\n✅ Read {valid_mols} valid molecules from {total_mols} total")
        
        return pd.DataFrame(data)
    
    def validate_smiles(self, df):
        """Validate SMILES strings"""
        print("\n🔍 Validating SMILES...")
        
        valid_indices = []
        for i, smiles in enumerate(df['smiles']):
            mol = Chem.MolFromSmiles(smiles)
            if mol is not None:
                valid_indices.append(i)
        
        df_valid = df.iloc[valid_indices].reset_index(drop=True)
        
        print(f"  Valid SMILES: {len(df_valid)}/{len(df)}")
        
        return df_valid
    
    def remove_duplicates(self, df):
        """Remove duplicate SMILES"""
        print("\n🔄 Removing duplicates...")
        
        initial_count = len(df)
        df_unique = df.drop_duplicates(subset=['smiles']).reset_index(drop=True)
        
        print(f"  Removed {initial_count - len(df_unique)} duplicates")
        print(f"  Unique molecules: {len(df_unique)}")
        
        return df_unique
    
    def analyze_data(self, df):
        """Analyze dataset statistics"""
        print("\n📊 Dataset Statistics")
        print("=" * 70)
        
        print(f"\nTotal molecules: {len(df)}")
        print(f"Total endpoints: {len(self.endpoints)}")
        
        print("\nEndpoint Statistics:")
        print("-" * 70)
        print(f"{'Endpoint':<20} {'Total':<10} {'Positive':<10} {'Negative':<10} {'Pos %':<10}")
        print("-" * 70)
        
        stats = []
        for endpoint in self.endpoints:
            if endpoint in df.columns:
                total = df[endpoint].notna().sum()
                positive = (df[endpoint] == 1).sum()
                negative = (df[endpoint] == 0).sum()
                pos_pct = (positive / total * 100) if total > 0 else 0
                
                print(f"{endpoint:<20} {total:<10} {positive:<10} {negative:<10} {pos_pct:<10.1f}%")
                
                stats.append({
                    'endpoint': endpoint,
                    'total': total,
                    'positive': positive,
                    'negative': negative,
                    'positive_pct': pos_pct
                })
        
        print("-" * 70)
        
        # Save statistics
        stats_df = pd.DataFrame(stats)
        stats_file = self.output_dir / 'dataset_statistics.csv'
        stats_df.to_csv(stats_file, index=False)
        print(f"\n✅ Statistics saved to: {stats_file}")
        
        return stats_df
    
    def split_data(self, df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
        """Split data into train/val/test sets"""
        print("\n✂️ Splitting data...")
        
        # Shuffle data
        df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        n = len(df_shuffled)
        train_size = int(n * train_ratio)
        val_size = int(n * val_ratio)
        
        train_df = df_shuffled[:train_size]
        val_df = df_shuffled[train_size:train_size + val_size]
        test_df = df_shuffled[train_size + val_size:]
        
        print(f"  Train: {len(train_df)} ({train_ratio*100:.0f}%)")
        print(f"  Val:   {len(val_df)} ({val_ratio*100:.0f}%)")
        print(f"  Test:  {len(test_df)} ({test_ratio*100:.0f}%)")
        
        return train_df, val_df, test_df
    
    def save_data(self, df, train_df, val_df, test_df):
        """Save processed data"""
        print("\n💾 Saving processed data...")
        
        # Save full dataset
        full_file = self.output_dir / 'tox21_data.csv'
        df.to_csv(full_file, index=False)
        print(f"  ✅ Full dataset: {full_file}")
        
        # Save splits
        train_file = self.output_dir / 'train_set.csv'
        val_file = self.output_dir / 'val_set.csv'
        test_file = self.output_dir / 'test_set.csv'
        
        train_df.to_csv(train_file, index=False)
        val_df.to_csv(val_file, index=False)
        test_df.to_csv(test_file, index=False)
        
        print(f"  ✅ Train set: {train_file}")
        print(f"  ✅ Val set:   {val_file}")
        print(f"  ✅ Test set:  {test_file}")
        
        # Save metadata
        metadata = {
            'processed_at': datetime.now().isoformat(),
            'input_file': str(self.input_file),
            'total_molecules': len(df),
            'train_size': len(train_df),
            'val_size': len(val_df),
            'test_size': len(test_df),
            'endpoints': self.endpoints,
            'train_ratio': 0.7,
            'val_ratio': 0.15,
            'test_ratio': 0.15
        }
        
        import json
        metadata_file = self.output_dir / 'preprocessing_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"  ✅ Metadata: {metadata_file}")
    
    def process(self):
        """Run complete preprocessing pipeline"""
        print("\n" + "=" * 70)
        print("TOX21 DATA PREPROCESSING PIPELINE")
        print("=" * 70)
        
        # Step 1: Read SDF
        df = self.read_sdf()
        
        # Step 2: Validate SMILES
        df = self.validate_smiles(df)
        
        # Step 3: Remove duplicates
        df = self.remove_duplicates(df)
        
        # Step 4: Analyze data
        stats = self.analyze_data(df)
        
        # Step 5: Split data
        train_df, val_df, test_df = self.split_data(df)
        
        # Step 6: Save data
        self.save_data(df, train_df, val_df, test_df)
        
        print("\n" + "=" * 70)
        print("✅ PREPROCESSING COMPLETE!")
        print("=" * 70)
        
        print(f"\nOutput directory: {self.output_dir}")
        print(f"Total molecules: {len(df)}")
        print(f"Ready for training: YES")
        
        return df, train_df, val_df, test_df


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Preprocess Tox21 SDF data')
    parser.add_argument('--input', type=str, required=True, help='Input SDF file')
    parser.add_argument('--output', type=str, required=True, help='Output directory')
    parser.add_argument('--train-ratio', type=float, default=0.7, help='Train set ratio')
    parser.add_argument('--val-ratio', type=float, default=0.15, help='Validation set ratio')
    parser.add_argument('--test-ratio', type=float, default=0.15, help='Test set ratio')
    
    args = parser.parse_args()
    
    # Create preprocessor
    preprocessor = Tox21Preprocessor(args.input, args.output)
    
    # Process data
    df, train_df, val_df, test_df = preprocessor.process()
    
    print("\n🎉 Data is ready for model training!")
    print("\nNext steps:")
    print("1. Review the data: cat data/processed/tox21_data.csv")
    print("2. Check statistics: cat data/processed/dataset_statistics.csv")
    print("3. Train models: python scripts/train_models.py --data data/processed/tox21_data.csv")


if __name__ == "__main__":
    main()
