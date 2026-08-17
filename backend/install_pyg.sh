#!/bin/bash
# Install PyTorch Geometric dependencies for local development
# Run this script inside the backend directory after activating your venv

set -e

echo "Installing PyTorch CPU..."
pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cpu

echo "Installing PyTorch Geometric dependencies (CPU)..."
pip install \
    torch-scatter==2.1.2 \
    torch-sparse==0.6.18 \
    torch-cluster==1.6.3 \
    torch-spline-conv==1.2.2 \
    torch-geometric==2.6.1 \
    --index-url https://data.pyg.org/whl/torch-2.4.0+cpu.html

echo "Installing remaining requirements..."
pip install -r requirements.txt

echo "✅ PyTorch Geometric installation complete"
echo "Run: python -c \"import torch; import torch_geometric; print(torch.__version__, torch_geometric.__version__)\""