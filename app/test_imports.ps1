#!/powershell
Write-Host "🧪 Testing import fixes..." -ForegroundColor Cyan

if (Test-Path "app") { 
    Push-Location app 
}

Write-Host ""
Write-Host "1️⃣ Testing fallback.py..." -ForegroundColor Yellow
python -c @"
try:
    import fallback
    print('✅ fallback.py imports successfully')
    print(f'App: {fallback.app}')
except Exception as e:
    print(f'❌ fallback.py failed: {e}')
    import traceback
    traceback.print_exc()
"@

Write-Host ""
Write-Host "2️⃣ Testing main_minimal.py..." -ForegroundColor Yellow
python -c @"
try:
    import main_minimal
    print('✅ main_minimal.py imports successfully')
    print(f'App: {main_minimal.app}')
except Exception as e:
    print(f'❌ main_minimal.py failed: {e}')
    import traceback
    traceback.print_exc()
"@

Write-Host ""
Write-Host "3️⃣ Testing main.py..." -ForegroundColor Yellow
python -c @"
try:
    import main
    print('✅ main.py imports successfully')
    print(f'App: {main.app}')
except Exception as e:
    print(f'❌ main.py failed: {e}')
    import traceback
    traceback.print_exc()
"@

Write-Host ""
Write-Host "🎯 Testing uvicorn startup..." -ForegroundColor Yellow
Write-Host "Starting server on port 8001 for 5 seconds..."

$job = Start-Job -ScriptBlock { python -m uvicorn fallback:app --host 0.0.0.0 --port 8001 }
Start-Sleep 2

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -TimeoutSec 3
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Health check passed" -ForegroundColor Green
    } else {
        Write-Host "❌ Health check failed with status $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Health check failed: $_" -ForegroundColor Red
}

Stop-Job $job -ErrorAction SilentlyContinue
Remove-Job $job -ErrorAction SilentlyContinue

if (Get-Location | Where-Object { $_.Path -like "*app" }) {
    Pop-Location
}

Write-Host ""
Write-Host "🎉 Import test complete!" -ForegroundColor Green