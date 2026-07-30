param(
    [string]$CommonFiles = "C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\Common\Files",
    [string]$StateRoot = "C:\MT5PortableProspectiveCollector\EURUSDForwardState",
    [string]$UvExecutable = "C:\Users\ZHAO ZHU INFORMATION\.local\bin\uv.exe"
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $PackageRoot "run_forward_residual_live_signal_publisher.py"
$FeatureCsv = Join-Path $CommonFiles "EURUSD_PROSPECTIVE_M5_FEATURES_V1.csv"
$ResidualDecisions = Join-Path $StateRoot "residual\FORWARD_RESIDUAL_DECISIONS.json"
$OutputDir = Join-Path $StateRoot "residual_live"
$OperationsLog = Join-Path $StateRoot "OPERATIONS.log"

function Write-OperationsLog {
    param([string]$Message)
    New-Item -ItemType Directory -Path $StateRoot -Force | Out-Null
    $Timestamp = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    Add-Content -LiteralPath $OperationsLog -Value "$Timestamp $Message" -Encoding UTF8
}

try {
    foreach ($Path in @(
        $UvExecutable,
        $Runner,
        $FeatureCsv,
        $ResidualDecisions
    )) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "Required residual live-signal path missing: $Path"
        }
    }
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    & $UvExecutable run --offline --with pandas --with numpy python $Runner `
        --feature-csv $FeatureCsv `
        --residual-decisions $ResidualDecisions `
        --output-dir $OutputDir | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Residual live-signal publisher failed"
    }
    $Summary = Get-Content -Raw -LiteralPath (
        Join-Path $OutputDir "FORWARD_RESIDUAL_LIVE_SIGNAL_SUMMARY.json"
    ) | ConvertFrom-Json
    if ($Summary.demo_order_authorized) {
        throw "Residual live publisher unexpectedly authorized orders"
    }
    Write-OperationsLog (
        "RESIDUAL_LIVE_SIGNAL_OK status=$($Summary.status) " +
        "decisions=$($Summary.published_decisions) " +
        "eligible=$($Summary.eligible_signals)"
    )
    exit 0
}
catch {
    Write-OperationsLog "RESIDUAL_LIVE_SIGNAL_FAIL detail=$($_.Exception.Message)"
    Write-Error $_
    exit 1
}
