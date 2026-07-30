param(
    [string]$TerminalRoot = "C:\MT5PortableM15RegimeShadow",
    [string]$CollectorStateRoot = "C:\MT5PortableProspectiveCollector\EURUSDForwardState",
    [string]$CommonFiles = "C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\Common\Files",
    [string]$UvExecutable = "C:\Users\ZHAO ZHU INFORMATION\.local\bin\uv.exe"
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $PSScriptRoot
$TerminalExecutable = Join-Path $TerminalRoot "terminal64.exe"
$TerminalExpert = Join-Path $TerminalRoot "MQL5\Experts\EurUsdM15RegimePortfolioControlledDemo.ex5"
$TerminalPreset = Join-Path $TerminalRoot "MQL5\Presets\EURUSD_M15_REGIME_PORTFOLIO_SHADOW_DEMO.set"
$TerminalConfig = Join-Path $TerminalRoot "Config\EURUSD_M15_REGIME_PORTFOLIO_LIVE_DEMO_SHADOW.ini"
$PackageExpert = Join-Path $PackageRoot "mt5\Experts\EurUsdM15RegimePortfolioControlledDemo.ex5"
$PackagePreset = Join-Path $PackageRoot "mt5\Presets\EURUSD_M15_REGIME_PORTFOLIO_SHADOW_DEMO.set"
$PackageConfig = Join-Path $PackageRoot "mt5\Config\EURUSD_M15_REGIME_PORTFOLIO_LIVE_DEMO_SHADOW.ini"
$AuditCsv = Join-Path $CommonFiles "EURUSD_M15_REGIME_PORTFOLIO_SHADOW_DEMO.csv"
$FeatureCsv = Join-Path $CommonFiles "EURUSD_PROSPECTIVE_M5_FEATURES_V1.csv"
$AuditScript = Join-Path $PSScriptRoot "audit_m15_regime_shadow.py"
$AdjudicatorScript = Join-Path $PackageRoot "run_m15_regime_forward_adjudicator.py"
$CombinedScript = Join-Path $PackageRoot "run_forward_combined_frequency_portfolio.py"
$StateRoot = Join-Path $TerminalRoot "EURUSDM15ShadowState"
$OperationsLog = Join-Path $StateRoot "OPERATIONS.log"
$DailyLearnerRoot = Join-Path $CollectorStateRoot "learner"
$DailyDecisions = Join-Path $DailyLearnerRoot "FORWARD_DECISIONS.json"
$DailySummary = Join-Path $DailyLearnerRoot "FORWARD_SUMMARY.json"

function Assert-ExactFile {
    param([string]$Expected, [string]$Actual)
    if (-not (Test-Path -LiteralPath $Expected)) {
        throw "Missing package artifact: $Expected"
    }
    if (-not (Test-Path -LiteralPath $Actual)) {
        throw "Missing deployed artifact: $Actual"
    }
    if (
        (Get-FileHash -Algorithm SHA256 -LiteralPath $Expected).Hash -ne
        (Get-FileHash -Algorithm SHA256 -LiteralPath $Actual).Hash
    ) {
        throw "Deployed artifact hash mismatch: $Actual"
    }
}

function Write-OperationsLog {
    param([string]$Message)
    New-Item -ItemType Directory -Path $StateRoot -Force | Out-Null
    $Timestamp = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    Add-Content -LiteralPath $OperationsLog -Value "$Timestamp $Message" -Encoding UTF8
}

function Get-ShadowProcess {
    $ExpectedPath = [System.IO.Path]::GetFullPath($TerminalExecutable)
    return Get-CimInstance Win32_Process -Filter "Name='terminal64.exe'" |
        Where-Object {
            $_.ExecutablePath -and
            [System.IO.Path]::GetFullPath($_.ExecutablePath) -eq $ExpectedPath
        } |
        Select-Object -First 1
}

try {
    foreach ($Path in @(
        $UvExecutable,
        $AuditScript,
        $AdjudicatorScript,
        $CombinedScript,
        $TerminalExecutable,
        $TerminalConfig,
        $FeatureCsv,
        $DailyDecisions,
        $DailySummary
    )) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "Required health path missing: $Path"
        }
    }
    Assert-ExactFile -Expected $PackageExpert -Actual $TerminalExpert
    Assert-ExactFile -Expected $PackagePreset -Actual $TerminalPreset
    Assert-ExactFile -Expected $PackageConfig -Actual $TerminalConfig
    $ConfigText = Get-Content -Raw -LiteralPath $TerminalConfig
    if ($ConfigText -notmatch "AllowLiveTrading=0") {
        throw "Terminal startup config does not disable trading"
    }
    if ($ConfigText -notmatch "AllowDllImport=0") {
        throw "Terminal startup config does not disable DLL imports"
    }
    $PresetText = Get-Content -Raw -LiteralPath $TerminalPreset
    foreach ($Required in @(
        "InpShadowMode=true",
        "InpEnableDemoOrders=false",
        "InpEmergencyStop=true",
        "InpTesterOrdersEnabled=false",
        "InpDemoArmToken=DISARMED"
    )) {
        if ($PresetText -notmatch [regex]::Escape($Required)) {
            throw "Deployed shadow preset is not safely disarmed: $Required"
        }
    }

    $Process = Get-ShadowProcess
    if (-not $Process) {
        $Started = Start-Process `
            -FilePath $TerminalExecutable `
            -ArgumentList @("/portable", "/config:`"$TerminalConfig`"") `
            -WindowStyle Hidden `
            -PassThru
        Write-OperationsLog "SHADOW_RESTARTED pid=$($Started.Id)"
        Start-Sleep -Seconds 8
        $Process = Get-ShadowProcess
        if (-not $Process) {
            throw "M15 regime shadow terminal failed to remain running"
        }
    }
    if (-not (Test-Path -LiteralPath $AuditCsv)) {
        throw "M15 regime shadow audit ledger is missing"
    }
    $AuditOutput = Join-Path $StateRoot "health"
    & $UvExecutable run python $AuditScript `
        --audit-csv $AuditCsv `
        --output-dir $AuditOutput | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "M15 regime shadow auditor failed"
    }
    $Audit = Get-Content -Raw -LiteralPath (
        Join-Path $AuditOutput "LIVE_SHADOW_AUDIT.json"
    ) | ConvertFrom-Json
    if ($Audit.status -eq "FAIL") {
        throw "M15 regime shadow health audit failed"
    }
    $AdjudicatorOutput = Join-Path $StateRoot "adjudicator"
    & $UvExecutable run python $AdjudicatorScript `
        --signal-csv $AuditCsv `
        --feature-csv $FeatureCsv `
        --output-dir $AdjudicatorOutput `
        --enforce-append-only | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "M15 regime forward adjudicator failed"
    }
    $Forward = Get-Content -Raw -LiteralPath (
        Join-Path $AdjudicatorOutput "FORWARD_SUMMARY.json"
    ) | ConvertFrom-Json
    if ($Forward.demo_order_authorized) {
        throw "M15 forward process unexpectedly authorized demo orders"
    }
    $M15Outcomes = Join-Path $AdjudicatorOutput "FORWARD_OUTCOMES.json"
    $M15Summary = Join-Path $AdjudicatorOutput "FORWARD_SUMMARY.json"
    $CombinedOutput = Join-Path $StateRoot "combined"
    & $UvExecutable run python $CombinedScript `
        --m15-outcomes $M15Outcomes `
        --m15-summary $M15Summary `
        --daily-decisions $DailyDecisions `
        --daily-summary $DailySummary `
        --feature-csv $FeatureCsv `
        --output-dir $CombinedOutput `
        --enforce-append-only | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "combined forward frequency portfolio failed"
    }
    $Combined = Get-Content -Raw -LiteralPath (
        Join-Path $CombinedOutput "FORWARD_SUMMARY.json"
    ) | ConvertFrom-Json
    if ($Combined.demo_order_authorized) {
        throw "combined forward portfolio unexpectedly authorized demo orders"
    }
    Write-OperationsLog (
        "HEALTH_OK status=$($Audit.status) " +
        "signals=$($Audit.signals) blocked=$($Audit.blocked_signals) " +
        "resolved=$($Forward.admission.resolved_trades) " +
        "pending=$($Forward.admission.pending_signals) " +
        "admission=$($Forward.admission.status) " +
        "combined_days=$($Combined.admission.complete_validation_weekdays) " +
        "combined_trades=$($Combined.admission.combined_trades) " +
        "frequency=$($Combined.admission.trades_per_complete_weekday) " +
        "combined_admission=$($Combined.admission.status) " +
        "pid=$($Process.ProcessId)"
    )
    exit 0
}
catch {
    Write-OperationsLog "FAIL detail=$($_.Exception.Message)"
    Write-Error $_
    exit 1
}
