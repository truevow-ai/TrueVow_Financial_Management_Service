# Test Supabase REST API Connection using PowerShell
# This bypasses PostgreSQL port 5432 and uses HTTPS (port 443) instead

Write-Host "================================================================================"
Write-Host "SUPABASE REST API CONNECTION TEST (PowerShell)"
Write-Host "================================================================================"

# Supabase Financial Management credentials
$PROJECT_URL = "https://ififhzrbhadmtedyvzhb.supabase.co"
$SERVICE_ROLE_KEY = "$env:SUPABASE_SERVICE_KEY"

Write-Host "Project URL: $PROJECT_URL"
Write-Host "Using Service Role Key: $($SERVICE_ROLE_KEY.Substring(0,20))..."
Write-Host ""

# Test 1: Basic connectivity
Write-Host "TEST 1: Basic connectivity to Supabase REST API"
Write-Host "--------------------------------------------------------------------------------"
try {
    $response = Invoke-WebRequest -Uri "$PROJECT_URL/rest/v1/" -Method Get -TimeoutSec 10 -UseBasicParsing
    Write-Host "[OK] REST API reachable: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($response.Content.Substring(0, [Math]::Min(200, $response.Content.Length)))"
} catch {
    Write-Host "[FAIL] Connection failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "This means HTTPS (port 443) is also blocked on your network."
    exit 1
}

Write-Host ""

# Test 2: Authenticated request
Write-Host "TEST 2: Authenticated request with Service Role Key"
Write-Host "--------------------------------------------------------------------------------"
$headers = @{
    "apikey" = $SERVICE_ROLE_KEY
    "Authorization" = "Bearer $SERVICE_ROLE_KEY"
}

try {
    $response = Invoke-WebRequest -Uri "$PROJECT_URL/rest/v1/" -Method Get -Headers $headers -TimeoutSec 10 -UseBasicParsing
    Write-Host "Status: $($response.StatusCode)"
    Write-Host "[OK] Successfully authenticated with Supabase REST API!" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Authentication failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 3: Check if legal_entity table exists
Write-Host "TEST 3: Check if legal_entity table exists"
Write-Host "--------------------------------------------------------------------------------"
try {
    $response = Invoke-WebRequest -Uri "$PROJECT_URL/rest/v1/legal_entity?select=*&limit=1" -Method Get -Headers $headers -TimeoutSec 10 -UseBasicParsing
    Write-Host "Status: $($response.StatusCode)"
    
    if ($response.StatusCode -eq 200) {
        $data = $response.Content | ConvertFrom-Json
        Write-Host "[OK] legal_entity table exists! Found $($data.Count) records" -ForegroundColor Green
        if ($data.Count -gt 0) {
            Write-Host "Sample record: $($data[0] | ConvertTo-Json -Compress)"
        }
    }
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 404) {
        Write-Host "[WARN] legal_entity table does not exist yet (migrations not run)" -ForegroundColor Yellow
    } else {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# Test 4: Check alembic_version table
Write-Host "TEST 4: Check if alembic_version table exists (migration status)"
Write-Host "--------------------------------------------------------------------------------"
try {
    $response = Invoke-WebRequest -Uri "$PROJECT_URL/rest/v1/alembic_version?select=*" -Method Get -Headers $headers -TimeoutSec 10 -UseBasicParsing
    Write-Host "Status: $($response.StatusCode)"
    
    if ($response.StatusCode -eq 200) {
        $data = $response.Content | ConvertFrom-Json
        if ($data.Count -gt 0) {
            Write-Host "[OK] Migrations have been run! Current version: $($data[0].version_num)" -ForegroundColor Green
        } else {
            Write-Host "[WARN] alembic_version table exists but is empty (no migrations run yet)" -ForegroundColor Yellow
        }
    }
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 404) {
        Write-Host "[WARN] alembic_version table does not exist (migrations never run)" -ForegroundColor Yellow
    } else {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "================================================================================"
Write-Host "SUMMARY"
Write-Host "================================================================================"
Write-Host "If all tests passed, REST API is working!"
Write-Host "We can use Supabase REST API to:"
Write-Host "  - Check table existence"
Write-Host "  - Query data"
Write-Host "  - Insert/update/delete records"
Write-Host ""
Write-Host "However, to run Alembic migrations, we still need PostgreSQL access."
Write-Host "Alternative: Generate SQL migration scripts and apply via Supabase Dashboard."
Write-Host "================================================================================"
