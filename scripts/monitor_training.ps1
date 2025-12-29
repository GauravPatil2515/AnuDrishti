# Training Monitor Script (Windows PowerShell)
# Monitors training progress and displays key metrics

param(
    [string]$LogFile = "train.log",
    [int]$RefreshSeconds = 10
)

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "TRAINING MONITOR" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Log file: $LogFile" -ForegroundColor Yellow
Write-Host "Refresh: ${RefreshSeconds}s (Ctrl+C to stop)" -ForegroundColor Gray
Write-Host ""

$lastSize = 0

while ($true) {
    Clear-Host
    
    Write-Host "=" * 70 -ForegroundColor Cyan
    Write-Host "TRAINING PROGRESS - $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Green
    Write-Host "=" * 70 -ForegroundColor Cyan
    
    if (Test-Path $LogFile) {
        # Get last 30 lines
        $lines = Get-Content $LogFile -Tail 30
        
        # Parse for key metrics
        $epoch = ($lines | Select-String "Epoch\s+(\d+)" | Select-Object -Last 1).Matches.Groups[1].Value
        $trainLoss = ($lines | Select-String "Train Loss:\s+([\d\.]+)" | Select-Object -Last 1).Matches.Groups[1].Value
        $valLoss = ($lines | Select-String "Val Loss:\s+([\d\.]+)" | Select-Object -Last 1).Matches.Groups[1].Value
        $valScore = ($lines | Select-String "Val ROC-AUC:\s+([\d\.]+)" | Select-Object -Last 1).Matches.Groups[1].Value
        
        if ($epoch) {
            Write-Host "`nCurrent Epoch: $epoch" -ForegroundColor Yellow
        }
        if ($trainLoss) {
            Write-Host "Train Loss:    $trainLoss" -ForegroundColor White
        }
        if ($valLoss) {
            Write-Host "Val Loss:      $valLoss" -ForegroundColor White
        }
        if ($valScore) {
            Write-Host "Val ROC-AUC:   $valScore" -ForegroundColor Cyan
            
            # Color code performance
            $score = [double]$valScore
            if ($score -ge 0.85) {
                Write-Host "               ✓ Excellent! " -ForegroundColor Green -NoNewline
            } elseif ($score -ge 0.80) {
                Write-Host "               ✓ Good! " -ForegroundColor Green -NoNewline
            } elseif ($score -ge 0.75) {
                Write-Host "               ⚠ Acceptable " -ForegroundColor Yellow -NoNewline
            } else {
                Write-Host "               ✗ Low " -ForegroundColor Red -NoNewline
            }
            Write-Host "(Target: ≥0.82)" -ForegroundColor Gray
        }
        
        Write-Host "`n" + ("-" * 70) -ForegroundColor Gray
        Write-Host "Recent Log:" -ForegroundColor Yellow
        $lines | Select-Object -Last 10 | ForEach-Object {
            if ($_ -match "error|fail|exception") {
                Write-Host "  $_" -ForegroundColor Red
            } elseif ($_ -match "warning") {
                Write-Host "  $_" -ForegroundColor Yellow
            } elseif ($_ -match "best|saved") {
                Write-Host "  $_" -ForegroundColor Green
            } else {
                Write-Host "  $_" -ForegroundColor Gray
            }
        }
        
        # File size check (to see if still writing)
        $currentSize = (Get-Item $LogFile).Length
        if ($currentSize -eq $lastSize) {
            Write-Host "`n⚠️  Log file not changing - training may have stopped" -ForegroundColor Yellow
        }
        $lastSize = $currentSize
        
    } else {
        Write-Host "Waiting for log file: $LogFile" -ForegroundColor Yellow
    }
    
    Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Gray
    
    Start-Sleep -Seconds $RefreshSeconds
}
