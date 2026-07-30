param(
    [string]$StateRoot = "C:\MT5PortableProspectiveCollector\EURUSDForwardState",
    [string]$UvExecutable = "C:\Users\ZHAO ZHU INFORMATION\.local\bin\uv.exe"
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $PackageRoot "run_forward_residual_mt5_shadow_bridge.py"
$LiveSignals = Join-Path $StateRoot "residual_live\FORWARD_RESIDUAL_LIVE_SIGNALS.json"
$OutputDir = Join-Path $StateRoot "residual_mt5_shadow"
$OperationsLog = Join-Path $StateRoot "OPERATIONS.log"

function Write-OperationsLog {
    param([string]$Message)
    New-Item -ItemType Directory -Path $StateRoot -Force | Out-Null
    $Timestamp = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    Add-Content -LiteralPath $OperationsLog -Value "$Timestamp $Message" -Encoding UTF8
}

try {
    foreach ($Path in @($UvExecutable, $Runner, $LiveSignals)) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "Required residual MT5 shadow path missing: $Path"
        }
    }
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    & $UvExecutable run --offline --with MetaTrader5 python $Runner `
        --live-signals $LiveSignals `
        --output-dir $OutputDir | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Residual MT5 shadow bridge failed"
    }
    $Summary = Get-Content -Raw -LiteralPath (
        Join-Path $OutputDir "FORWARD_RESIDUAL_MT5_SHADOW_SUMMARY.json"
    ) | ConvertFrom-Json
    if ($Summary.order_api_calls -ne 0) {
        throw "Residual MT5 shadow bridge reported an order API call"
    }
    if ($Summary.position_mutation_attempts -ne 0) {
        throw "Residual MT5 shadow bridge reported a position mutation"
    }
    if ($Summary.demo_order_authorized) {
        throw "Residual MT5 shadow bridge unexpectedly authorized orders"
    }
    Write-OperationsLog (
        "RESIDUAL_MT5_SHADOW_OK status=$($Summary.status) " +
        "receipts=$($Summary.receipts) " +
        "captured=$($Summary.shadow_entries_captured) " +
        "order_calls=$($Summary.order_api_calls)"
    )
    exit 0
}
catch {
    Write-OperationsLog "RESIDUAL_MT5_SHADOW_FAIL detail=$($_.Exception.Message)"
    Write-Error $_
    exit 1
}
