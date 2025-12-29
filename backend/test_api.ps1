# PowerShell API Testing Script for Enhanced Backend
# Run this with: .\test_api.ps1

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Testing Enhanced MedToXAi API" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Test 1: Health Check
Write-Host "`n[TEST 1] Health Check" -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Method Get
Write-Host "Status: $($response.status)" -ForegroundColor Green
Write-Host "RDKit Enabled: $($response.rdkit_enabled)" -ForegroundColor Green
Write-Host "Total Endpoints: $($response.total_endpoints)" -ForegroundColor Green
Write-Host "Rate Limiting: $($response.rate_limiting_enabled)" -ForegroundColor Green

# Test 2: Get Endpoints
Write-Host "`n[TEST 2] Get Available Endpoints" -ForegroundColor Yellow
$endpoints = Invoke-RestMethod -Uri "http://localhost:5000/api/endpoints" -Method Get
Write-Host "Total Endpoints: $($endpoints.count)" -ForegroundColor Green
Write-Host "Endpoints:" -ForegroundColor Green
foreach ($ep in $endpoints.endpoints) {
    Write-Host "  - $($ep.id): $($ep.name)" -ForegroundColor Cyan
}

# Test 3: Validate SMILES
Write-Host "`n[TEST 3] SMILES Validation" -ForegroundColor Yellow
$body = @{
    smiles = "CCO"
} | ConvertTo-Json

$validation = Invoke-RestMethod -Uri "http://localhost:5000/api/validate/smiles" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "Original: $($validation.original_smiles)" -ForegroundColor Green
Write-Host "Valid: $($validation.is_valid)" -ForegroundColor Green
Write-Host "Canonical: $($validation.canonical_smiles)" -ForegroundColor Green
Write-Host "Method: $($validation.validation_method)" -ForegroundColor Green

# Test 4: Predict Toxicity
Write-Host "`n[TEST 4] Toxicity Prediction (Ethanol)" -ForegroundColor Yellow
Start-Sleep -Seconds 2  # Wait to avoid rate limit

$predBody = @{
    smiles = "CCO"
    molecule_name = "Ethanol"
} | ConvertTo-Json

$prediction = Invoke-RestMethod -Uri "http://localhost:5000/api/predict" `
    -Method Post `
    -ContentType "application/json" `
    -Body $predBody

Write-Host "Molecule: $($prediction.smiles)" -ForegroundColor Green
Write-Host "Overall Toxicity: $($prediction.overall_toxicity)" -ForegroundColor Green
Write-Host "Toxic Endpoints: $($prediction.toxic_endpoints)" -ForegroundColor Green
Write-Host "Risk Category: $($prediction.risk_category)" -ForegroundColor Green
Write-Host "Feature Method: $($prediction.feature_method)" -ForegroundColor Green

Write-Host "`nEndpoint Results:" -ForegroundColor Yellow
foreach ($ep in $prediction.predictions.PSObject.Properties) {
    $name = $ep.Name
    $data = $ep.Value
    $color = if ($data.prediction -eq "Toxic") { "Red" } else { "Green" }
    Write-Host "  $name : $($data.prediction) ($($data.probability))" -ForegroundColor $color
}

# Test 5: Rate Limit Status
Write-Host "`n[TEST 5] Rate Limit Status" -ForegroundColor Yellow
Start-Sleep -Seconds 2  # Wait to avoid rate limit

$rateLimit = Invoke-RestMethod -Uri "http://localhost:5000/api/rate-limit/status" -Method Get
Write-Host "Client ID: $($rateLimit.rate_limit_info.client_id)" -ForegroundColor Green
Write-Host "`nRate Limit Tiers:" -ForegroundColor Yellow
foreach ($tier in $rateLimit.rate_limit_info.tiers.PSObject.Properties) {
    $name = $tier.Name
    $data = $tier.Value
    Write-Host "  $name : $($data.remaining)/$($data.rate_limit) remaining" -ForegroundColor Cyan
}

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "All Tests Completed!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
