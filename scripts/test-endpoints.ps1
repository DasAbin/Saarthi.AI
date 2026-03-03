# Test API Endpoints Script (PowerShell)

param(
    [Parameter(Mandatory=$true)]
    [string]$ApiUrl
)

Write-Host "🧪 Testing Saarthi.AI API Endpoints..." -ForegroundColor Cyan
Write-Host "API URL: $ApiUrl" -ForegroundColor Yellow
Write-Host ""

# Health check
Write-Host "1. Testing /health..." -ForegroundColor Green
try {
    $response = Invoke-RestMethod -Uri "$ApiUrl/health" -Method Get
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test query
Write-Host "2. Testing /query..." -ForegroundColor Green
try {
    $body = @{
        query = "What is PMAY?"
        language = "en"
    } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiUrl/query" -Method Post -Body $body -ContentType "application/json"
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test recommend
Write-Host "3. Testing /recommend..." -ForegroundColor Green
try {
    $body = @{
        age = 35
        state = "Maharashtra"
        income = 200000
        occupation = "Farmer"
    } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiUrl/recommend" -Method Post -Body $body -ContentType "application/json"
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test grievance
Write-Host "4. Testing /grievance..." -ForegroundColor Green
try {
    $body = @{
        issue_type = "Water Supply"
        description = "No water supply for 3 days"
        location = "Ward 5, Sector 12, Mumbai"
    } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiUrl/grievance" -Method Post -Body $body -ContentType "application/json"
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Failed: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "✅ Testing complete!" -ForegroundColor Green
