param(
    [Parameter(Mandatory = $true)]
    [string]$Provider,

    [Parameter(Mandatory = $true)]
    [string]$Region,

    [Parameter(Mandatory = $true)]
    [string]$Endpoint,

    [int]$Port = 443,

    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,

    [string]$Python = ""
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path $Root).Path
$ReportsDir = Join-Path $Root "outputs\reports"
New-Item -ItemType Directory -Force -Path $ReportsDir | Out-Null

$PingPath = Join-Path $ReportsDir "vps_ping.txt"
$TracertPath = Join-Path $ReportsDir "vps_tracert.txt"
$TestNetPath = Join-Path $ReportsDir "vps_test_net.txt"

if (-not $Python) {
    $CandidatePython = Join-Path $Root "..\xauusd-phase0\.venv\Scripts\python.exe"
    if (Test-Path $CandidatePython) {
        $Python = (Resolve-Path $CandidatePython).Path
    } else {
        $Python = "python"
    }
}

Push-Location $Root
try {
    "provider=$Provider region=$Region endpoint=$Endpoint captured_at_utc=$((Get-Date).ToUniversalTime().ToString('o'))" |
        Out-File -FilePath (Join-Path $ReportsDir "vps_latency_capture_context.txt") -Encoding utf8

    ping $Endpoint | Tee-Object -FilePath $PingPath
    tracert $Endpoint | Tee-Object -FilePath $TracertPath
    Test-NetConnection $Endpoint -Port $Port | Tee-Object -FilePath $TestNetPath

    & $Python "scripts\generate_phase2_vps_latency_report.py" `
        --provider $Provider `
        --region $Region `
        --endpoint $Endpoint `
        --ping-output $PingPath `
        --tracert-output $TracertPath `
        --test-net-output $TestNetPath
} finally {
    Pop-Location
}
