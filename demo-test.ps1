[CmdletBinding()]
param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [switch]$KeepData
)

$ErrorActionPreference = "Stop"

function Assert-Condition {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "[STEP] $Message" -ForegroundColor Cyan
}

function Write-Pass {
    param([string]$Message)
    Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Yellow
}

try {
    $testId = [guid]::NewGuid().ToString()
    $payloadObject = @{
        event   = "demo.test"
        source  = "demo-test.ps1"
        testId  = $testId
        orderId = 12345
    }
    $payloadJson = $payloadObject | ConvertTo-Json -Compress

    Write-Step "Checking health endpoint"
    $health = Invoke-RestMethod -Method GET -Uri "$BaseUrl/api/health"
    Assert-Condition ($health.status -eq "ok") "Health check did not return status=ok."
    Write-Pass "Health endpoint responded with status=ok"

    Write-Step "Posting a webhook event"
    $postResult = Invoke-RestMethod -Method POST -Uri "$BaseUrl/webhook" -ContentType "application/json" -Body $payloadJson
    Assert-Condition ($postResult.message -eq "Webhook received") "Webhook POST did not return the expected success message."
    Assert-Condition (-not [string]::IsNullOrWhiteSpace($postResult.event_id)) "Webhook POST did not return an event_id."
    Write-Pass "Webhook accepted the payload"

    Write-Step "Reading event log"
    $eventsResult = Invoke-RestMethod -Method GET -Uri "$BaseUrl/api/events"
    Assert-Condition ($null -ne $eventsResult.events) "Event log response did not include an events collection."

    $matchedEvent = $eventsResult.events | Where-Object {
        $_.payload.testId -eq $testId
    } | Select-Object -First 1

    Assert-Condition ($null -ne $matchedEvent) "The posted webhook event was not found in the event log."
    Assert-Condition ($matchedEvent.payload.event -eq "demo.test") "The stored event payload did not match the test data."
    Write-Pass "Event log contains the posted webhook event"

    if (-not $KeepData) {
        Write-Step "Clearing event log"
        $clearResult = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/events/clear"
        Assert-Condition ($clearResult.message -eq "Event log cleared") "Clear endpoint did not return the expected success message."
        Write-Pass "Event log cleared"
    }
    else {
        Write-Info "Skipping clear step because -KeepData was supplied"
    }

    Write-Host ""
    Write-Host "Demo verification completed successfully." -ForegroundColor Green
    exit 0
}
catch {
    Write-Host ""
    Write-Host "Demo verification failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
