param(
    [ValidateSet("Health", "Daily")]
    [string]$Mode = "Health",
    [string]$TerminalRoot = "C:\MT5PortableProspectiveCollector",
    [string]$CommonFiles = "C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\Common\Files",
    [string]$StateRoot = "C:\MT5PortableProspectiveCollector\EURUSDForwardState",
    [string]$UvExecutable = "C:\Users\ZHAO ZHU INFORMATION\.local\bin\uv.exe"
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $PSScriptRoot
$AuditScript = Join-Path $PSScriptRoot "audit_live_demo_shadow.py"
$LearnerScript = Join-Path $PackageRoot "run_forward_selective_learner.py"
$FeatureCsv = Join-Path $CommonFiles "EURUSD_PROSPECTIVE_M5_FEATURES_V1.csv"
$EnvironmentCsv = Join-Path $CommonFiles "EURUSD_PROSPECTIVE_M5_ENVIRONMENT_V1.csv"
$HeartbeatCsv = Join-Path $CommonFiles "EURUSD_PROSPECTIVE_M5_HEARTBEAT_V1.csv"
$TerminalExecutable = Join-Path $TerminalRoot "terminal64.exe"
$TerminalExpert = Join-Path $TerminalRoot "MQL5\Experts\EurUsdProspectiveMultiSymbolCollector.ex5"
$TerminalPreset = Join-Path $TerminalRoot "MQL5\Presets\EURUSD_PROSPECTIVE_MULTISYMBOL_COLLECTOR_DEMO.set"
$TerminalConfig = Join-Path $TerminalRoot "Config\eurusd_prospective_multisymbol_collector_live_demo_shadow.ini"
$PackageExpert = Join-Path $PackageRoot "mt5\Experts\EurUsdProspectiveMultiSymbolCollector.ex5"
$PackagePreset = Join-Path $PackageRoot "mt5\Presets\EURUSD_PROSPECTIVE_MULTISYMBOL_COLLECTOR_DEMO.set"
$PackageConfig = Join-Path $PackageRoot "mt5\Config\EURUSD_PROSPECTIVE_MULTISYMBOL_COLLECTOR_LIVE_DEMO_SHADOW.ini"
$OperationsLog = Join-Path $StateRoot "OPERATIONS.log"

function Assert-ExactFile {
    param(
        [string]$Expected,
        [string]$Actual
    )
    if (-not (Test-Path -LiteralPath $Expected)) {
        throw "Missing package file: $Expected"
    }
    if (-not (Test-Path -LiteralPath $Actual)) {
        throw "Missing deployed file: $Actual"
    }
    $ExpectedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Expected).Hash
    $ActualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Actual).Hash
    if ($ExpectedHash -ne $ActualHash) {
        throw "Deployed artifact hash mismatch: $Actual"
    }
}

function Write-OperationsLog {
    param([string]$Message)
    New-Item -ItemType Directory -Path $StateRoot -Force | Out-Null
    $Timestamp = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    Add-Content -LiteralPath $OperationsLog -Value "$Timestamp $Message" -Encoding UTF8
}

function Get-CollectorProcess {
    $ExpectedPath = [System.IO.Path]::GetFullPath($TerminalExecutable)
    return Get-CimInstance Win32_Process -Filter "Name='terminal64.exe'" |
        Where-Object {
            $_.ExecutablePath -and
            [System.IO.Path]::GetFullPath($_.ExecutablePath) -eq $ExpectedPath
        } |
        Select-Object -First 1
}

function Invoke-HealthCycle {
    foreach ($Path in @(
        $UvExecutable,
        $AuditScript,
        $TerminalExecutable,
        $TerminalConfig
    )) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "Required operations path missing: $Path"
        }
    }
    Assert-ExactFile -Expected $PackageExpert -Actual $TerminalExpert
    Assert-ExactFile -Expected $PackagePreset -Actual $TerminalPreset
    Assert-ExactFile -Expected $PackageConfig -Actual $TerminalConfig

    $ConfigText = Get-Content -Raw -LiteralPath $TerminalConfig
    if ($ConfigText -notmatch "AllowLiveTrading=0") {
        throw "Terminal startup config does not disable live trading"
    }
    if ($ConfigText -notmatch "AllowDllImport=0") {
        throw "Terminal startup config does not disable DLL imports"
    }

    $Process = Get-CollectorProcess
    if (-not $Process) {
        $Started = Start-Process `
            -FilePath $TerminalExecutable `
            -ArgumentList @("/portable", "/config:$TerminalConfig") `
            -WindowStyle Hidden `
            -PassThru
        Write-OperationsLog "COLLECTOR_RESTARTED pid=$($Started.Id)"
        Start-Sleep -Seconds 8
        $Process = Get-CollectorProcess
        if (-not $Process) {
            throw "Collector terminal failed to remain running"
        }
    }

    $HealthOutput = Join-Path $StateRoot "health"
    & $UvExecutable run python $AuditScript `
        --common-files $CommonFiles `
        --output-dir $HealthOutput | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Live collector auditor process failed"
    }
    $Audit = Get-Content -Raw -LiteralPath (
        Join-Path $HealthOutput "LIVE_DEMO_AUDIT.json"
    ) | ConvertFrom-Json
    if ($Audit.status -eq "FAIL") {
        throw "Live collector health audit failed"
    }
    Write-OperationsLog (
        "HEALTH_OK status=$($Audit.status) " +
        "heartbeat_age=$($Audit.heartbeat_age_seconds) " +
        "feature_rows=$($Audit.feature_rows)"
    )
}

function Assert-SnapshotIntegrity {
    param([string]$Snapshot)
    $SumsPath = Join-Path $Snapshot "SHA256SUMS.txt"
    if (-not (Test-Path -LiteralPath $SumsPath)) {
        throw "Snapshot checksum ledger missing: $SumsPath"
    }
    $Expected = @{}
    foreach ($Line in Get-Content -LiteralPath $SumsPath) {
        if ([string]::IsNullOrWhiteSpace($Line)) {
            continue
        }
        if ($Line -notmatch "^([0-9a-f]{64})  (.+)$") {
            throw "Invalid snapshot checksum row: $Line"
        }
        $Name = $Matches[2]
        if ($Expected.ContainsKey($Name)) {
            throw "Duplicate snapshot checksum entry: $Name"
        }
        $Expected[$Name] = $Matches[1]
    }
    $ActualFiles = @(
        Get-ChildItem -LiteralPath $Snapshot -File |
            Where-Object { $_.Name -ne "SHA256SUMS.txt" }
    )
    if ($ActualFiles.Count -ne $Expected.Count) {
        throw "Snapshot file count does not match checksum ledger: $Snapshot"
    }
    foreach ($File in $ActualFiles) {
        if (-not $Expected.ContainsKey($File.Name)) {
            throw "Unexpected file in immutable snapshot: $($File.Name)"
        }
        $ActualHash = (
            Get-FileHash -Algorithm SHA256 -LiteralPath $File.FullName
        ).Hash.ToLowerInvariant()
        if ($ActualHash -ne $Expected[$File.Name]) {
            throw "Immutable snapshot hash mismatch: $($File.FullName)"
        }
    }
}

function Save-ImmutableDailySnapshot {
    $UtcDate = [DateTime]::UtcNow.ToString("yyyy-MM-dd")
    $SnapshotRoot = Join-Path $StateRoot "snapshots"
    $Snapshot = Join-Path $SnapshotRoot $UtcDate
    if (Test-Path -LiteralPath $Snapshot) {
        Assert-SnapshotIntegrity -Snapshot $Snapshot
        Get-ChildItem -LiteralPath $Snapshot -File |
            ForEach-Object { $_.IsReadOnly = $true }
        Write-OperationsLog "SNAPSHOT_REVERIFIED date=$UtcDate"
        return
    }
    foreach ($Path in @($FeatureCsv, $EnvironmentCsv, $HeartbeatCsv)) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "Missing collector ledger for daily snapshot: $Path"
        }
    }
    New-Item -ItemType Directory -Path $SnapshotRoot -Force | Out-Null
    $Staging = Join-Path $SnapshotRoot ($UtcDate + ".staging")
    if (Test-Path -LiteralPath $Staging) {
        throw "Incomplete prior snapshot staging directory exists: $Staging"
    }
    New-Item -ItemType Directory -Path $Staging | Out-Null
    Copy-Item -LiteralPath $FeatureCsv -Destination $Staging
    Copy-Item -LiteralPath $EnvironmentCsv -Destination $Staging
    Copy-Item -LiteralPath $HeartbeatCsv -Destination $Staging
    Get-ChildItem -LiteralPath $Staging -File | ForEach-Object {
        $Hash = Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName
        Add-Content `
            -LiteralPath (Join-Path $Staging "SHA256SUMS.txt") `
            -Value "$($Hash.Hash.ToLowerInvariant())  $($_.Name)" `
            -Encoding UTF8
    }
    Move-Item -LiteralPath $Staging -Destination $Snapshot
    Assert-SnapshotIntegrity -Snapshot $Snapshot
    Get-ChildItem -LiteralPath $Snapshot -File |
        ForEach-Object { $_.IsReadOnly = $true }
    Write-OperationsLog "SNAPSHOT_SAVED date=$UtcDate"
}

function Invoke-DailyLearner {
    Save-ImmutableDailySnapshot
    $LearnerOutput = Join-Path $StateRoot "learner"
    & $UvExecutable run python $LearnerScript `
        --feature-csv $FeatureCsv `
        --output-dir $LearnerOutput `
        --enforce-append-only | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Forward learner process failed"
    }
    $Summary = Get-Content -Raw -LiteralPath (
        Join-Path $LearnerOutput "FORWARD_SUMMARY.json"
    ) | ConvertFrom-Json
    if ($Summary.admission.demo_order_authorized) {
        throw "Forward research process unexpectedly authorized demo orders"
    }
    Write-OperationsLog (
        "DAILY_LEARNER_OK resolved=$($Summary.resolved_training_days) " +
        "eligible=$($Summary.admission.eligible_trades) " +
        "admission=$($Summary.admission.status)"
    )
}

New-Item -ItemType Directory -Path $StateRoot -Force | Out-Null
try {
    Invoke-HealthCycle
    if ($Mode -eq "Daily") {
        Invoke-DailyLearner
    }
    exit 0
}
catch {
    Write-OperationsLog "FAIL mode=$Mode detail=$($_.Exception.Message)"
    Write-Error $_
    exit 1
}
