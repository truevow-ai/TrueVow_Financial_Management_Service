# Quick check of database state via Supabase REST API
$PROJECT_URL = "https://ififhzrbhadmtedyvzhb.supabase.co"
$SERVICE_ROLE_KEY = "$env:SUPABASE_SERVICE_KEY"

$headers = @{
    "apikey" = $SERVICE_ROLE_KEY
    "Authorization" = "Bearer $SERVICE_ROLE_KEY"
}

Write-Host "Checking database migration status..." -ForegroundColor Cyan
Write-Host ""

# Check alembic_version table
try {
    $response = Invoke-WebRequest -Uri "$PROJECT_URL/rest/v1/alembic_version?select=*" -Headers $headers -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    
    if ($data.Count -gt 0) {
        Write-Host "[SUCCESS] Database migrations ARE applied!" -ForegroundColor Green
        Write-Host "Current migration version: $($data[0].version_num)" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next step: Start the backend server" -ForegroundColor Yellow
    } else {
        Write-Host "[INFO] alembic_version table exists but is empty" -ForegroundColor Yellow
        Write-Host "Migrations need to be applied" -ForegroundColor Yellow
    }
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 404) {
        Write-Host "[INFO] alembic_version table does not exist" -ForegroundColor Yellow
        Write-Host "Database schema needs to be created" -ForegroundColor Yellow
    } else {
        Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# Check if legal_entity table exists
Write-Host "Checking for legal_entity table..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$PROJECT_URL/rest/v1/legal_entity?select=id,entity_name&limit=1" -Headers $headers -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    
    Write-Host "[SUCCESS] legal_entity table exists!" -ForegroundColor Green
    Write-Host "Records found: $($data.Count)" -ForegroundColor Green
    
    if ($data.Count -gt 0) {
        Write-Host "Sample entity: $($data[0].entity_name)" -ForegroundColor Cyan
    }
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 404) {
        Write-Host "[INFO] legal_entity table does not exist yet" -ForegroundColor Yellow
    } else {
        Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    }
}
