# MedToXAi Platform - Server Manager (PowerShell)
# Checks and starts both backend and frontend servers

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  MedToXAi Platform - Server Manager" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

$projectRoot = "c:\Users\GAURAV PATIL\Downloads\medtox-scan-ai"

# Function to check if port is listening
function Test-Port {
    param($Port)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -InformationLevel Quiet
        return $connection
    } catch {
        return $false
    }
}

# Check Backend
Write-Host "🔍 Checking Backend Server..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -UseBasicParsing -TimeoutSec 3
    if ($response.StatusCode -eq 200) {
        Write-Host " ✅ RUNNING" -ForegroundColor Green
        $backendRunning = $true
    }
} catch {
    Write-Host " ❌ NOT RUNNING" -ForegroundColor Red
    $backendRunning = $false
    
    Write-Host "   🔧 Starting backend server..." -ForegroundColor Yellow
    Start-Process python -ArgumentList "app.py" -WorkingDirectory "$projectRoot\backend" -WindowStyle Minimized
    Start-Sleep -Seconds 4
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -UseBasicParsing -TimeoutSec 3
        Write-Host "   ✅ Backend started successfully!" -ForegroundColor Green
        $backendRunning = $true
    } catch {
        Write-Host "   ⚠️ Backend may still be starting..." -ForegroundColor Yellow
    }
}

# Check Frontend
Write-Host "`n🔍 Checking Frontend Server..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 3
    if ($response.StatusCode -eq 200) {
        Write-Host " ✅ RUNNING" -ForegroundColor Green
        $frontendRunning = $true
    }
} catch {
    Write-Host " ❌ NOT RUNNING" -ForegroundColor Red
    $frontendRunning = $false
    
    Write-Host "   🔧 Starting frontend server..." -ForegroundColor Yellow
    Write-Host "   📝 This will take 30-60 seconds to compile..." -ForegroundColor Yellow
    Start-Process npm -ArgumentList "start" -WorkingDirectory "$projectRoot\frontend" -WindowStyle Normal
    Write-Host "   ✅ Frontend is starting (new window opened)!" -ForegroundColor Green
}

# Summary
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  Server Status Summary" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

Write-Host "Backend API:  " -NoNewline
if ($backendRunning) {
    Write-Host "http://localhost:5000" -ForegroundColor Green
} else {
    Write-Host "Starting..." -ForegroundColor Yellow
}

Write-Host "Frontend UI:  " -NoNewline
if ($frontendRunning) {
    Write-Host "http://localhost:3000" -ForegroundColor Green
} else {
    Write-Host "Compiling... (wait 30-60s)" -ForegroundColor Yellow
}

Write-Host "`n============================================`n" -ForegroundColor Cyan

if (-not $frontendRunning) {
    Write-Host "⏳ Waiting for frontend to compile..." -ForegroundColor Yellow
    Write-Host "   The browser will open automatically when ready.`n" -ForegroundColor Cyan
    
    # Wait up to 60 seconds for frontend
    $maxWait = 60
    $waited = 0
    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds 5
        $waited += 5
        try {
            $test = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2
            if ($test.StatusCode -eq 200) {
                Write-Host "✅ Frontend is ready!" -ForegroundColor Green
                Start-Process "http://localhost:3000"
                break
            }
        } catch {
            Write-Host "   Still compiling... ($waited seconds)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "✅ Platform is ready!" -ForegroundColor Green
    Write-Host "`n🌐 Opening browser..." -ForegroundColor Cyan
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:3000"
}

Write-Host "`n🎉 MedToXAi Platform is operational!`n" -ForegroundColor Green
