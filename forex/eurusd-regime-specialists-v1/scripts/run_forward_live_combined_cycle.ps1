param(
    [string]$M15StateRoot = "C:\MT5PortableM15RegimeShadow\EURUSDM15ShadowState",
    [string]$CollectorStateRoot = "C:\MT5PortableProspectiveCollector\EURUSDForwardState",
    [string]$CommonFiles = "C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\Common\Files",
    [string]$UvExecutable = "C:\Users\ZHAO ZHU INFORMATION\.local\bin\uv.exe"
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $PackageRoot "run_forward_live_combined_portfolio.py"
$M15Outcomes = Join-Path $M15StateRoot "adjudicator\FORWARD_OUTCOMES.json"
$M15Summary = Join-Path $M15StateRoot "adjudicator\FORWARD_SUMMARY.json"
$ResidualSignals = Join-Path (
    $CollectorStateRoot
) "residual_live\FORWARD_RESIDUAL_LIVE_SIGNALS.json"
$ResidualOutcomes = Join-Path (
    $CollectorStateRoot
) "residual_live_outcomes\FORWARD_RESIDUAL_LIVE_OUTCOMES.json"
$ResidualParity = Join-Path (
    $CollectorStateRoot
) "residual_live_outcomes\FORWARD_RESIDUAL_SELECTION_PARITY.json"
$ResidualSummary = Join-Path (
    $CollectorStateRoot
) "residual_live_outcomes\FORWARD_RESIDUAL_LIVE_OUTCOME_SUMMARY.json"
$FeatureCsv = Join-Path $CommonFiles "EURUSD_PROSPECTIVE_M5_FEATURES_V1.csv"
$OutputDir = Join-Path $M15StateRoot "combined_live_v3"
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
        $ResidualSignals,
        $ResidualOutcomes,
        $ResidualParity,
        $ResidualSummary,
        $FeatureCsv
    )) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "Required live-combined path missing: $Path"
        }
    }
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    & $UvExecutable run --offline --with pandas --with numpy python $Runner `
        --m15-outcomes $M15Outcomes `
        --m15-summary $M15Summary `
        --residual-live-signals $ResidualSignals `
        --residual-live-outcomes $ResidualOutcomes `
        --residual-selection-parity $ResidualParity `
        --residual-live-summary $ResidualSummary `
        --feature-csv $FeatureCsv `
        --output-dir $OutputDir `
        --enforce-append-only | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Live-only combined forward portfolio failed"
    }
    $Summary = Get-Content -Raw -LiteralPath (
        Join-Path $OutputDir "FORWARD_LIVE_SUMMARY.json"
    ) | ConvertFrom-Json
    if ($Summary.research_residual_outcomes_consumed -ne 0) {
        throw "Live-combined monitor consumed a research residual outcome"
    }
    if ($Summary.daily_learner_trades_consumed -ne 0) {
        throw "Live-combined monitor consumed a rejected daily-learner trade"
    }
    if ($Summary.demo_order_authorized) {
        throw "Live-combined monitor unexpectedly authorized demo orders"
    }
    if ($Summary.admission.demo_order_authorized) {
        throw "Live-combined admission unexpectedly authorized demo orders"
    }
    Write-OperationsLog (
        "COMBINED_LIVE_V3_OK status=$($Summary.admission.status) " +
        "days=$($Summary.admission.complete_validation_weekdays) " +
        "trades=$($Summary.admission.combined_trades) " +
        "frequency=$($Summary.admission.trades_per_complete_weekday) " +
        "coverage=$($Summary.admission.weekday_trade_coverage)"
    )
    exit 0
}
catch {
    Write-OperationsLog "COMBINED_LIVE_V3_FAIL detail=$($_.Exception.Message)"
    Write-Error $_
    exit 1
}
