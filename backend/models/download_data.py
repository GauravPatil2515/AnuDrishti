#!/usr/bin/env python3
"""Download Tox21 dataset for training."""

import os
import urllib.request
import gzip
import shutil
from pathlib import Path

def download_tox21():
    """Download Tox21 dataset from DeepChem."""
    
    # Create data directory
    data_dir = Path(__file__).parent.parent.parent / "data_packages" / "tox21_model_full_package" / "data" / "tox21"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = data_dir / "tox21.csv"
    
    if output_file.exists():
        print(f"✅ Dataset already exists: {output_file}")
        return str(output_file)
    
    print("⬇️  Downloading Tox21 dataset...")
    
    # DeepChem AWS URL
    url = "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz"
    
    gz_file = data_dir / "tox21.csv.gz"
    
    try:
        # Download
        print(f"   URL: {url}")
        urllib.request.urlretrieve(url, gz_file)
        print(f"   Downloaded: {gz_file}")
        
        # Extract
        print("   Extracting...")
        with gzip.open(gz_file, 'rb') as f_in:
            with open(output_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Clean up
        gz_file.unlink()
        
        print(f"✅ Dataset saved: {output_file}")
        
        # Verify
        with open(output_file, 'r') as f:
            lines = len(f.readlines())
        print(f"   Total samples: {lines - 1}")
        
        return str(output_file)
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        
        # Try alternative: Kaggle format
        print("   Trying alternative source...")
        alt_url = "https://raw.githubusercontent.com/deepchem/deepchem/master/datasets/tox21.csv.gz"
        
        try:
            urllib.request.urlretrieve(alt_url, gz_file)
            with gzip.open(gz_file, 'rb') as f_in:
                with open(output_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            gz_file.unlink()
            print(f"✅ Dataset saved from alternative: {output_file}")
            return str(output_file)
        except:
            print("❌ Alternative also failed")
            return None

if __name__ == "__main__":
    path = download_tox21()
    if path:
        print(f"\n✅ Ready for training!")
        print(f"Dataset: {path}")
    else:
        print("\n❌ Please download manually from:")
        print("   https://www.kaggle.com/datasets/tox21/tox21")
