param(
    [string]$M15StateRoot = "C:\MT5PortableM15RegimeShadow\EURUSDM15ShadowState",
    [string]$CollectorStateRoot = "C:\MT5PortableProspectiveCollector\EURUSDForwardState",
    [string]$CommonFiles = "C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\Common\Files",
    [string]$UvExecutable = "C:\Users\ZHAO ZHU INFORMATION\.local\bin\uv.exe"
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $PackageRoot "run_forward_combined_residual_portfolio.py"
$M15Outcomes = Join-Path $M15StateRoot "adjudicator\FORWARD_OUTCOMES.json"
$M15Summary = Join-Path $M15StateRoot "adjudicator\FORWARD_SUMMARY.json"
$DailyDecisions = Join-Path $CollectorStateRoot "learner\FORWARD_DECISIONS.json"
$DailySummary = Join-Path $CollectorStateRoot "learner\FORWARD_SUMMARY.json"
$ResidualDecisions = Join-Path $CollectorStateRoot "residual\FORWARD_RESIDUAL_DECISIONS.json"
$ResidualSummary = Join-Path $CollectorStateRoot "residual\FORWARD_RESIDUAL_SUMMARY.json"
$FeatureCsv = Join-Path $CommonFiles "EURUSD_PROSPECTIVE_M5_FEATURES_V1.csv"
$OutputDir = Join-Path $M15StateRoot "combined_residual_v2"
$OperationsLog = Join-Path $M15StateRoot "OPERATIONS.log"

function Write-OperationsLog {
    param([string]$Message)
    New-Item -ItemType Directory -Path $M15StateRoot -Force | Out-Null
    $Timestamp = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    Add-Content -LiteralPath $OperationsLog -Value "$Timestamp $Message" -Encoding UTF8
}

try {
    foreach ($Path in @(
        $UvExecutable,
        $Runner,
        $M15Outcomes,
        $M15Summary,
        $DailyDecisions,
        $DailySummary,
        $ResidualDecisions,
        $ResidualSummary,
        $FeatureCsv
    )) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "Required combined-residual path missing: $Path"
        }
    }
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    & $UvExecutable run --offline --with pandas --with numpy python $Runner `
        --m15-outcomes $M15Outcomes `
        --m15-summary $M15Summary `
        --daily-decisions $DailyDecisions `
        --daily-summary $DailySummary `
        --residual-decisions $ResidualDecisions `
        --residual-summary $ResidualSummary `
        --feature-csv $FeatureCsv `
        --output-dir $OutputDir `
        --enforce-append-only | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Combined residual forward portfolio failed"
    }
    $Summary = Get-Content -Raw -LiteralPath (
        Join-Path $OutputDir "FORWARD_SUMMARY.json"
    ) | ConvertFrom-Json
    if ($Summary.demo_order_authorized) {
        throw "Combined residual monitor unexpectedly authorized demo orders"
    }
    if ($Summary.admission.demo_order_authorized) {
        throw "Combined residual admission unexpectedly authorized demo orders"
    }
    Write-OperationsLog (
        "COMBINED_RESIDUAL_OK status=$($Summary.admission.status) " +
        "days=$($Summary.admission.complete_validation_weekdays) " +
        "trades=$($Summary.admission.combined_trades) " +
        "frequency=$($Summary.admission.trades_per_complete_weekday) " +
        "coverage=$($Summary.admission.weekday_trade_coverage)"
    )
    exit 0
}
catch {
    Write-OperationsLog "COMBINED_RESIDUAL_FAIL detail=$($_.Exception.Message)"
    Write-Error $_
    exit 1
}
