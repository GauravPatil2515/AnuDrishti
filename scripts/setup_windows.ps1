# Setup Script for Windows (PowerShell)
# Run this to configure your environment for Faithful XAI

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=" * 69 -ForegroundColor Cyan
Write-Host "FAITHFUL XAI - Windows Setup Script" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan

# 1. Set Groq API Key
Write-Host "`n[1/5] Setting up Groq API Key..." -ForegroundColor Yellow
if (-not $env:GROQ_API_KEY) {
    Write-Host "   Get your free API key from: https://console.groq.com" -ForegroundColor Gray
    $apiKey = Read-Host "   Enter your Groq API Key"
    $env:GROQ_API_KEY = $apiKey
    [System.Environment]::SetEnvironmentVariable('GROQ_API_KEY', $apiKey, 'User')
    Write-Host "   ✅ API key saved to environment" -ForegroundColor Green
} else {
    Write-Host "   ✅ API key already set" -ForegroundColor Green
}


# 2. Check Python
Write-Host "`n[2/5] Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "   ✅ $pythonVersion" -ForegroundColor Green

# 3. Check CUDA/GPU
Write-Host "`n[3/5] Checking NVIDIA GPU..." -ForegroundColor Yellow
try {
    $gpuInfo = nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>&1
    Write-Host "   ✅ GPU detected: $gpuInfo" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  nvidia-smi not found - GPU may not be available" -ForegroundColor Red
}

# 4. Install Dependencies
Write-Host "`n[4/5] Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "   This may take 5-10 minutes..." -ForegroundColor Gray

# Check if already installed
$torchInstalled = python -c "import torch; print('✅ PyTorch already installed')" 2>$null
if ($torchInstalled) {
    Write-Host "   $torchInstalled" -ForegroundColor Green
} else {
    Write-Host "   Installing PyTorch with CUDA 11.8..." -ForegroundColor Gray
    pip install torch==2.1.0+cu118 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --quiet
}

Write-Host "   Installing PyTorch Geometric..." -ForegroundColor Gray
pip install torch_geometric torch_scatter torch_sparse torch_cluster -f https://data.pyg.org/whl/torch-2.1.0+cu118.html --quiet

Write-Host "   Installing RDKit, Groq, and utilities..." -ForegroundColor Gray
pip install rdkit groq tensorboard matplotlib seaborn pandas scikit-learn --quiet

Write-Host "   ✅ All dependencies installed" -ForegroundColor Green

# 5. Test Installation
Write-Host "`n[5/5] Testing installation..." -ForegroundColor Yellow

# Test PyTorch + CUDA
$cudaTest = python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}'); print(f'PyTorch: {torch.__version__}')" 2>&1
Write-Host "   $cudaTest" -ForegroundColor Green

# Test RDKit
$rdkitTest = python -c "from rdkit import Chem; mol = Chem.MolFromSmiles('CCO'); print('✅ RDKit working')" 2>&1
Write-Host "   $rdkitTest" -ForegroundColor Green

# Test Groq
$groqTest = python -c "from groq import Groq; print('✅ Groq client available')" 2>&1
Write-Host "   $groqTest" -ForegroundColor Green

Write-Host "`n" + "=" * 70 -ForegroundColor Cyan
Write-Host "SETUP COMPLETE!" -ForegroundColor Green -BackgroundColor Black
Write-Host "=" * 70 -ForegroundColor Cyan

Write-Host "`n🚀 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Test the demo:" -ForegroundColor White
Write-Host "      cd experiments" -ForegroundColor Gray
Write-Host "      python faithful_xai_demo.py --use-groq --smiles 'c1ccccc1'" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Start training (overnight):" -ForegroundColor White
Write-Host "      cd backend/models" -ForegroundColor Gray
Write-Host "      python train_attention_gin.py --task tox21 --config config_rtx3050.yaml" -ForegroundColor Gray
Write-Host ""
Write-Host "   Training will take ~8-12 hours on RTX 3050" -ForegroundColor Yellow
Write-Host ""
