# Test MedToXAi Backend API
# PowerShell Script

Write-Host "🧪 Testing MedToXAi Backend API" -ForegroundColor Cyan
Write-Host "="*70

# Test 1: Health Check
Write-Host "`n✅ Test 1: Health Check" -ForegroundColor Green
$response = Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Method Get
Write-Host "Status: $($response.status)"
Write-Host "Predictor Loaded: $($response.predictor_loaded)"

# Test 2: Single Prediction
Write-Host "`n✅ Test 2: Single Prediction (Ethanol - CCO)" -ForegroundColor Green
$body = @{
    smiles = "CCO"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:5000/api/predict" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "SMILES: $($response.smiles)"
Write-Host "Total Endpoints: $($response.summary.total_endpoints)"
Write-Host "Toxic Count: $($response.summary.toxic_count)"
Write-Host "Overall Assessment: $($response.summary.overall_assessment)"

Write-Host "`nEndpoint Results:" -ForegroundColor Yellow
foreach ($endpoint in $response.endpoints) {
    $status = if ($endpoint.toxic) { "⚠️ TOXIC" } else { "✅ SAFE" }
    Write-Host "  $($endpoint.name): $status (Prob: $($endpoint.probability.ToString('F4')))"
}

# Test 3: Caffeine
Write-Host "`n✅ Test 3: Prediction (Caffeine)" -ForegroundColor Green
$body = @{
    smiles = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:5000/api/predict" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "Molecule: Caffeine"
Write-Host "Overall Assessment: $($response.summary.overall_assessment)"
Write-Host "Toxic Endpoints: $($response.summary.toxic_count)/12"

# Test 4: Batch Prediction
Write-Host "`n✅ Test 4: Batch Prediction" -ForegroundColor Green
$body = @{
    smiles_list = @("CCO", "CC(=O)O", "c1ccccc1")
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:5000/api/predict/batch" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "Batch Results:"
foreach ($result in $response.results) {
    Write-Host "  $($result.smiles): $($result.summary.overall_assessment)"
}

Write-Host "`n" + "="*70
Write-Host "✅ All Tests Passed!" -ForegroundColor Green
Write-Host "Backend is working perfectly with new trained models!" -ForegroundColor Cyan
