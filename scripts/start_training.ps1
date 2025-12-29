# Simple Training Starter (Windows)
# Waits for setup then starts training

Write-Host "Waiting for dependencies..." -ForegroundColor Yellow

# Wait for dependencies
$ready = $false
$attempts = 0

while (-not $ready -and $attempts -lt 60) {
    try {
        $test = python -c "import torch; import torch_geometric; from rdkit import Chem; print('OK')" 2>&1
        if ($test -match "OK") {
            $ready = $true
        }
    } catch {
        # Still installing
    }
    
    if (-not $ready) {
        Write-Host "  Attempt $attempts/60..." -ForegroundColor Gray
        Start-Sleep -Seconds 30
        $attempts++
    }
}

if ($ready) {
    Write-Host "Dependencies ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Starting training..." -ForegroundColor Yellow
    Write-Host "This will take 8-12 hours" -ForegroundColor Gray
    Write-Host ""
    
    # Set API key from environment or prompt user
    if (-not $env:GROQ_API_KEY) {
        Write-Host "Please set GROQ_API_KEY environment variable" -ForegroundColor Yellow
        $env:GROQ_API_KEY = Read-Host "Enter your Groq API Key"
    }
    
    # Start training
    cd backend\models
    python train_attention_gin.py --task tox21 --batch_size 32 --epochs 80 --lr 5e-5 --output_dir training_tox21
} else {
    Write-Host "Dependencies not ready. Please wait for setup_windows.ps1 to complete" -ForegroundColor Red
}
