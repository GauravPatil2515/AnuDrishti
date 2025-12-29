#!/usr/bin/env python3
"""
Download Tox21 Dataset from Kaggle
===================================
Downloads the Tox21 CSV dataset from Kaggle

Usage:
    python download_kaggle_tox21.py --output data/raw/
"""

import os
import sys
import argparse
from pathlib import Path

def download_from_kaggle(output_dir):
    """Download Tox21 dataset from Kaggle"""
    
    print("\n" + "=" * 70)
    print("DOWNLOADING TOX21 DATASET FROM KAGGLE")
    print("=" * 70)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Try to import kagglehub
        import kagglehub
        
        print("\n📥 Downloading dataset from Kaggle...")
        print("Dataset: epicskills/tox21-dataset")
        
        # Download latest version
        path = kagglehub.dataset_download("epicskills/tox21-dataset")
        
        print(f"\n✅ Downloaded to: {path}")
        
        # Copy to our data directory
        import shutil
        source_file = Path(path) / "tox21.csv"
        dest_file = output_path / "tox21.csv"
        
        if source_file.exists():
            shutil.copy(source_file, dest_file)
            print(f"✅ Copied to: {dest_file}")
            
            # Check file size
            file_size = dest_file.stat().st_size / (1024 * 1024)  # MB
            print(f"📊 File size: {file_size:.2f} MB")
            
            return True
        else:
            print(f"⚠️ File not found: {source_file}")
            return False
            
    except ImportError:
        print("\n❌ kagglehub not installed")
        print("\nInstall with:")
        print("  pip install kagglehub")
        print("\nOr download manually:")
        print("1. Visit: https://www.kaggle.com/datasets/epicskills/tox21-dataset")
        print("2. Click 'Download' button")
        print(f"3. Extract tox21.csv to: {output_path}/")
        return False
        
    except Exception as e:
        print(f"\n❌ Error downloading: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you have Kaggle API credentials set up")
        print("2. Run: kaggle datasets download -d epicskills/tox21-dataset")
        print("3. Or download manually from Kaggle website")
        return False


def setup_kaggle_api():
    """Guide user to set up Kaggle API"""
    
    print("\n" + "=" * 70)
    print("KAGGLE API SETUP")
    print("=" * 70)
    
    print("\n📝 To use Kaggle API, you need to:")
    print("\n1. Create a Kaggle account (if you don't have one)")
    print("   Visit: https://www.kaggle.com/")
    
    print("\n2. Get your API credentials:")
    print("   - Go to: https://www.kaggle.com/settings")
    print("   - Scroll to 'API' section")
    print("   - Click 'Create New API Token'")
    print("   - This downloads kaggle.json")
    
    print("\n3. Place kaggle.json in:")
    print("   Windows: C:\\Users\\<YourUsername>\\.kaggle\\kaggle.json")
    print("   Linux/Mac: ~/.kaggle/kaggle.json")
    
    print("\n4. Install kagglehub:")
    print("   pip install kagglehub")
    
    print("\n5. Run this script again:")
    print("   python download_kaggle_tox21.py")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Download Tox21 dataset from Kaggle')
    parser.add_argument('--output', type=str, default='data/raw',
                       help='Output directory')
    parser.add_argument('--setup', action='store_true',
                       help='Show Kaggle API setup instructions')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_kaggle_api()
        return
    
    # Try to download
    success = download_from_kaggle(args.output)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ DOWNLOAD COMPLETE!")
        print("=" * 70)
        print("\n📋 Next steps:")
        print("1. Check the data:")
        print(f"   head {args.output}/tox21.csv")
        print("\n2. Train models:")
        print(f"   python scripts/train_models.py --data {args.output}/tox21.csv")
    else:
        print("\n" + "=" * 70)
        print("⚠️ DOWNLOAD FAILED")
        print("=" * 70)
        print("\n📋 Manual download:")
        print("1. Visit: https://www.kaggle.com/datasets/epicskills/tox21-dataset")
        print("2. Click 'Download' (525 KB)")
        print(f"3. Extract tox21.csv to: {args.output}/")
        print("\nOr run: python download_kaggle_tox21.py --setup")


if __name__ == "__main__":
    main()
