#!/usr/bin/env python3
"""
Step 1: Data Analysis and Exploration
======================================
Analyze Tox21 dataset to understand structure and quality
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

class Tox21DataAnalyzer:
    """Analyze Tox21 dataset"""
    
    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self.df = None
        self.endpoints = [
            'NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-Aromatase',
            'NR-ER', 'NR-ER-LBD', 'NR-PPAR-gamma',
            'SR-ARE', 'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53'
        ]
    
    def load_data(self):
        """Load dataset"""
        print("📖 Loading dataset...")
        self.df = pd.read_csv(self.data_path)
        print(f"✅ Loaded {len(self.df)} samples")
        print(f"   Columns: {len(self.df.columns)}")
        return self.df
    
    def basic_info(self):
        """Display basic information"""
        print("\n" + "="*70)
        print("BASIC DATASET INFORMATION")
        print("="*70)
        
        print(f"\nShape: {self.df.shape}")
        print(f"Columns: {list(self.df.columns)}")
        print(f"\nData types:\n{self.df.dtypes}")
        print(f"\nMemory usage: {self.df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        # Check for SMILES column
        smiles_col = None
        for col in self.df.columns:
            if 'smiles' in col.lower() or 'mol' in col.lower():
                smiles_col = col
                break
        
        if smiles_col:
            print(f"\n✅ SMILES column found: {smiles_col}")
        else:
            print("\n⚠️ No SMILES column found - checking last column")
            smiles_col = self.df.columns[-1]
        
        return smiles_col
    
    def analyze_missing_values(self):
        """Analyze missing values"""
        print("\n" + "="*70)
        print("MISSING VALUES ANALYSIS")
        print("="*70)
        
        missing = self.df.isnull().sum()
        missing_pct = (missing / len(self.df)) * 100
        
        missing_df = pd.DataFrame({
            'Column': missing.index,
            'Missing': missing.values,
            'Percentage': missing_pct.values
        })
        
        print("\n", missing_df[missing_df['Missing'] > 0].to_string(index=False))
        
        return missing_df
    
    def analyze_endpoints(self):
        """Analyze endpoint distributions"""
        print("\n" + "="*70)
        print("ENDPOINT ANALYSIS")
        print("="*70)
        
        stats = []
        for endpoint in self.endpoints:
            if endpoint in self.df.columns:
                total = self.df[endpoint].notna().sum()
                positive = (self.df[endpoint] == 1).sum()
                negative = (self.df[endpoint] == 0).sum()
                pos_pct = (positive / total * 100) if total > 0 else 0
                
                stats.append({
                    'Endpoint': endpoint,
                    'Total': total,
                    'Positive': positive,
                    'Negative': negative,
                    'Pos%': f"{pos_pct:.1f}%",
                    'Imbalance': f"{negative/positive:.1f}:1" if positive > 0 else "N/A"
                })
        
        stats_df = pd.DataFrame(stats)
        print("\n", stats_df.to_string(index=False))
        
        return stats_df
    
    def run_analysis(self):
        """Run complete analysis"""
        print("\n" + "="*70)
        print("TOX21 DATA ANALYSIS")
        print("="*70)
        
        self.load_data()
        smiles_col = self.basic_info()
        missing_df = self.analyze_missing_values()
        stats_df = self.analyze_endpoints()
        
        # Save analysis
        output_dir = self.data_path.parent / 'analysis'
        output_dir.mkdir(exist_ok=True)
        
        stats_df.to_csv(output_dir / 'endpoint_statistics.csv', index=False)
        missing_df.to_csv(output_dir / 'missing_values.csv', index=False)
        
        print(f"\n✅ Analysis saved to: {output_dir}")
        
        return {
            'smiles_column': smiles_col,
            'stats': stats_df,
            'missing': missing_df
        }

if __name__ == "__main__":
    analyzer = Tox21DataAnalyzer('data/raw/tox21.csv')
    results = analyzer.run_analysis()
