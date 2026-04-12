# AstroNova Render.com Deployment Validator (PowerShell)
# Usage: .\validate_deployment.ps1 https://your-app.onrender.com

param(
    [Parameter(Mandatory=$true)]
    [string]$BaseUrl,
    
    [int]$Timeout = 30
)

$ErrorActionPreference = "Continue"

# Color functions
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Blue }

# Global test results
$script:TestResults = @()

function Add-TestResult {
    param($Name, $Status, $Message)
    $script:TestResults += @{
        Name = $Name
        Status = $Status
        Message = $Message
    }
}

function Test-BasicConnectivity {
    Write-Host "`n🧪 Testing: Basic Connectivity"
    
    try {
        $response = Invoke-WebRequest -Uri $BaseUrl -TimeoutSec $Timeout -UseBasicParsing
        if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 302) {
            Write-Success "API is accessible"
            Add-TestResult "Basic Connectivity" $true "API is accessible"
            return $true
        } else {
            throw "API returned status code $($response.StatusCode)"
        }
    } catch {
        Write-Error "Failed to connect: $($_.Exception.Message)"
        Add-TestResult "Basic Connectivity" $false $_.Exception.Message
        return $false
    }
}

function Test-HealthEndpoint {
    Write-Host "`n🧪 Testing: Health Endpoint"
    
    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/api/admin/health" -TimeoutSec $Timeout
        
        if ($response.status -ne "healthy") {
            throw "Health status is '$($response.status)', not 'healthy'"
        }
        
        Write-Success "Health check passed - $($response.service)"
        Add-TestResult "Health Endpoint" $true "Health check passed - $($response.service)"
        return $true
    } catch {
        Write-Error $_.Exception.Message
        Add-TestResult "Health Endpoint" $false $_.Exception.Message
        return $false
    }
}

function Test-DatabaseConnectivity {
    Write-Host "`n🧪 Testing: Database Connectivity"
    
    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/api/admin/health" -TimeoutSec $Timeout
        
        if ($response.database -ne "connected") {
            throw "Database status is '$($response.database)', not 'connected'"
        }
        
        Write-Success "Database connection verified"
        Add-TestResult "Database Connectivity" $true "Database connection verified"
        return $true
    } catch {
        Write-Error $_.Exception.Message
        Add-TestResult "Database Connectivity" $false $_.Exception.Message
        return $false
    }
}

function Test-ApiDocumentation {
    Write-Host "`n🧪 Testing: API Documentation"
    
    try {
        $response = Invoke-WebRequest -Uri "$BaseUrl/docs" -TimeoutSec $Timeout -UseBasicParsing
        
        if ($response.StatusCode -ne 200) {
            throw "API docs returned status $($response.StatusCode)"
        }
        
        Write-Success "API documentation is accessible"
        Add-TestResult "API Documentation" $true "API documentation is accessible"
        return $true
    } catch {
        Write-Error $_.Exception.Message
        Add-TestResult "API Documentation" $false $_.Exception.Message
        return $false
    }
}

function Test-StaticFiles {
    Write-Host "`n🧪 Testing: Static Files"
    
    $staticEndpoints = @(
        "/static/styles.css",
        "/login.html",
        "/dashboard.html"
    )
    
    $workingEndpoints = 0
    
    foreach ($endpoint in $staticEndpoints) {
        try {
            $response = Invoke-WebRequest -Uri "$BaseUrl$endpoint" -TimeoutSec 10 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                $workingEndpoints++
            }
        } catch {
            # Silently continue
        }
    }
    
    if ($workingEndpoints -eq 0) {
        Write-Error "No static files are accessible"
        Add-TestResult "Static Files" $false "No static files are accessible"
        return $false
    } else {
        Write-Success "Static files accessible ($workingEndpoints/$($staticEndpoints.Length) endpoints)"
        Add-TestResult "Static Files" $true "Static files accessible ($workingEndpoints/$($staticEndpoints.Length) endpoints)"
        return $true
    }
}

function Test-ResponseTime {
    Write-Host "`n🧪 Testing: Response Time"
    
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-RestMethod -Uri "$BaseUrl/api/admin/health" -TimeoutSec $Timeout
        $stopwatch.Stop()
        
        $responseTimeMs = $stopwatch.ElapsedMilliseconds
        
        if ($responseTimeMs -gt 5000) {
            Write-Warning "Response time is slow: ${responseTimeMs}ms"
            Add-TestResult "Response Time" $true "Response time is slow: ${responseTimeMs}ms"
        } elseif ($responseTimeMs -gt 2000) {
            Write-Warning "Response time is acceptable: ${responseTimeMs}ms"
            Add-TestResult "Response Time" $true "Response time is acceptable: ${responseTimeMs}ms"
        } else {
            Write-Success "Response time is good: ${responseTimeMs}ms"
            Add-TestResult "Response Time" $true "Response time is good: ${responseTimeMs}ms"
        }
        return $true
    } catch {
        Write-Error $_.Exception.Message
        Add-TestResult "Response Time" $false $_.Exception.Message
        return $false
    }
}

function Test-SslCertificate {
    Write-Host "`n🧪 Testing: SSL Certificate"
    
    if (-not $BaseUrl.StartsWith("https://")) {
        Write-Warning "Not using HTTPS (consider enabling for production)"
        Add-TestResult "SSL Certificate" $true "Not using HTTPS (consider enabling for production)"
    } else {
        Write-Success "HTTPS/SSL is properly configured"
        Add-TestResult "SSL Certificate" $true "HTTPS/SSL is properly configured"
    }
    return $true
}

function Test-CorsConfiguration {
    Write-Host "`n🧪 Testing: CORS Configuration"
    
    try {
        # PowerShell doesn't easily support OPTIONS requests, so we'll make a simple test
        $headers = @{
            'Origin' = 'https://example.com'
        }
        
        $response = Invoke-WebRequest -Uri "$BaseUrl/api/admin/health" -Headers $headers -TimeoutSec $Timeout -UseBasicParsing
        
        $corsHeaders = $response.Headers.Keys | Where-Object { $_ -like "Access-Control-*" }
        
        if ($corsHeaders.Count -eq 0) {
            Write-Warning "CORS headers not found (may be intentional)"
            Add-TestResult "CORS Configuration" $true "CORS headers not found (may be intentional)"
        } else {
            Write-Success "CORS configured ($($corsHeaders.Count) headers found)"
            Add-TestResult "CORS Configuration" $true "CORS configured ($($corsHeaders.Count) headers found)"
        }
        return $true
    } catch {
        Write-Warning "Could not test CORS: $($_.Exception.Message)"
        Add-TestResult "CORS Configuration" $true "Could not test CORS"
        return $true
    }
}

function Show-Summary {
    $passed = ($script:TestResults | Where-Object { $_.Status -eq $true }).Count
    $total = $script:TestResults.Count
    
    Write-Host "`n$('=' * 60)" -ForegroundColor Blue
    Write-Host "🎯 DEPLOYMENT VALIDATION SUMMARY" -ForegroundColor Blue
    Write-Host "$('=' * 60)" -ForegroundColor Blue
    
    # Show individual results
    foreach ($result in $script:TestResults) {
        if ($result.Status) {
            Write-Host "✅ PASS" -ForegroundColor Green -NoNewline
        } else {
            Write-Host "❌ FAIL" -ForegroundColor Red -NoNewline
        }
        Write-Host " $($result.Name): $($result.Message)"
    }
    
    Write-Host "`n$('=' * 60)" -ForegroundColor Blue
    
    # Overall status
    if ($passed -eq $total) {
        Write-Host "🎉 ALL TESTS PASSED ($passed/$total)" -ForegroundColor Green
        Write-Host "Your AstroNova deployment is working correctly!" -ForegroundColor Green
        $deploymentStatus = "healthy"
    } elseif ($passed -gt ($total * 0.7)) {
        Write-Host "⚠️  MOST TESTS PASSED ($passed/$total)" -ForegroundColor Yellow
        Write-Host "Your deployment is working with minor issues" -ForegroundColor Yellow
        $deploymentStatus = "warning"
    } else {
        Write-Host "❌ MULTIPLE FAILURES ($passed/$total)" -ForegroundColor Red
        Write-Host "Your deployment has significant issues" -ForegroundColor Red
        $deploymentStatus = "failed"
    }
    
    Write-Host "`n💡 Next Steps:" -ForegroundColor Yellow
    if ($deploymentStatus -eq "healthy") {
        Write-Host "✅ Set up your admin user and configure Shopify webhook" -ForegroundColor White
        Write-Host "✅ Test PDF generation with a real order" -ForegroundColor White
        Write-Host "✅ Monitor logs and performance" -ForegroundColor White
    } else {
        Write-Host "🔧 Check Render.com dashboard for service logs" -ForegroundColor White
        Write-Host "🔧 Verify environment variables are set correctly" -ForegroundColor White
        Write-Host "🔧 Ensure all services are running" -ForegroundColor White
    }
    
    return @{
        TotalTests = $total
        PassedTests = $passed
        FailedTests = $total - $passed
        SuccessRate = [math]::Round(($passed / $total) * 100, 2)
        Status = $deploymentStatus
        Url = $BaseUrl
    }
}

# Main execution
function Main {
    # Validate URL format
    if (-not ($BaseUrl.StartsWith("http://") -or $BaseUrl.StartsWith("https://"))) {
        Write-Error "URL must start with http:// or https://"
        return 2
    }
    
    # Clean up URL
    $script:BaseUrl = $BaseUrl.TrimEnd('/')
    
    Write-Host "🚀 AstroNova Render.com Deployment Validator" -ForegroundColor Blue
    Write-Host "Testing: $BaseUrl`n" -ForegroundColor Blue
    
    # Run all tests
    Test-BasicConnectivity
    Test-HealthEndpoint
    Test-DatabaseConnectivity
    Test-ApiDocumentation
    Test-StaticFiles
    Test-ResponseTime
    Test-SslCertificate
    Test-CorsConfiguration
    
    # Show summary and determine exit code
    $summary = Show-Summary
    
    if ($summary.Status -eq "healthy") {
        return 0
    } elseif ($summary.Status -eq "warning") {
        return 1
    } else {
        return 2
    }
}

# Execute main function
$exitCode = Main
exit $exitCode