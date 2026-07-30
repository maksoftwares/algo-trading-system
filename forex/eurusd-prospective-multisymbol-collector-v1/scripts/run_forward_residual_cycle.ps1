param(
    [string]$CommonFiles = "C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\Common\Files",
    [string]$StateRoot = "C:\MT5PortableProspectiveCollector\EURUSDForwardState",
    [string]$UvExecutable = "C:\Users\ZHAO ZHU INFORMATION\.local\bin\uv.exe"
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $PackageRoot "run_forward_residual_regime_specialist.py"
$FeatureCsv = Join-Path $CommonFiles "EURUSD_PROSPECTIVE_M5_FEATURES_V1.csv"
$OutputDir = Join-Path $StateRoot "residual"
$OperationsLog = Join-Path $StateRoot "OPERATIONS.log"

function Write-OperationsLog {
    param([string]$Message)
    New-Item -ItemType Directory -Path $StateRoot -Force | Out-Null
    $Timestamp = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    Add-Content -LiteralPath $OperationsLog -Value "$Timestamp $Message" -Encoding UTF8
}

New-Item -ItemType Directory -Path $StateRoot -Force | Out-Null
try {
    foreach ($Path in @($UvExecutable, $Runner, $FeatureCsv)) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "Required residual-cycle path missing: $Path"
        }
    }
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    & $UvExecutable run --offline --with pandas --with numpy python $Runner `
        --feature-csv $FeatureCsv `
        --output-dir $OutputDir `
        --enforce-append-only | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Forward residual-regime process failed"
    }
    $SummaryPath = Join-Path $OutputDir "FORWARD_RESIDUAL_SUMMARY.json"
    $Summary = Get-Content -Raw -LiteralPath $SummaryPath | ConvertFrom-Json
    if ($Summary.demo_order_authorized) {
        throw "Residual process unexpectedly authorized demo orders"
    }
    if ($Summary.admission.demo_order_authorized) {
        throw "Residual admission unexpectedly authorized demo orders"
    }
    Write-OperationsLog (
        "RESIDUAL_OK status=$($Summary.status) " +
        "resolved=$($Summary.resolved_residual_days) " +
        "eligible=$($Summary.admission.eligible_trades) " +
        "admission=$($Summary.admission.status)"
    )
    exit 0
}
catch {
    Write-OperationsLog "RESIDUAL_FAIL detail=$($_.Exception.Message)"
    Write-Error $_
    exit 1
}
