param(
    [string]$TerminalRoot = "C:\MT5PortableRsiHealthObserver",
    [string]$CommonFiles = "C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\Common\Files",
    [string]$PythonExecutable = "C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $PSScriptRoot
$TerminalExecutable = Join-Path $TerminalRoot "terminal64.exe"
$TerminalExpert = Join-Path $TerminalRoot "MQL5\Experts\EurUsdRsiHealthGateProspectiveObserver.ex5"
$TerminalPreset = Join-Path $TerminalRoot "MQL5\Presets\EURUSD_RSI_HEALTH_GATE_PROSPECTIVE_OBSERVER.set"
$TerminalConfig = Join-Path $TerminalRoot "Config\EURUSD_RSI_HEALTH_GATE_PROSPECTIVE_OBSERVER_LIVE_DEMO.ini"
$PackageExpert = Join-Path $PackageRoot "mt5\Experts\EurUsdRsiHealthGateProspectiveObserver.ex5"
$PackagePreset = Join-Path $PackageRoot "mt5\Presets\EURUSD_RSI_HEALTH_GATE_PROSPECTIVE_OBSERVER.set"
$PackageConfig = Join-Path $PackageRoot "mt5\Config\EURUSD_RSI_HEALTH_GATE_PROSPECTIVE_OBSERVER_LIVE_DEMO.ini"
$AuditCsv = Join-Path $CommonFiles "EURUSD_RSI_HEALTH_GATE_PROSPECTIVE_OBSERVER.csv"
$AuditScript = Join-Path $PSScriptRoot "audit_rsi_health_gate_observer.py"
$StateRoot = Join-Path $TerminalRoot "EURUSDRsiHealthObserverState"
$HealthRoot = Join-Path $StateRoot "health"
$OperationsLog = Join-Path $StateRoot "OPERATIONS.log"

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

function Get-ObserverProcess {
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
        $TerminalExecutable,
        $TerminalConfig,
        $PythonExecutable,
        $AuditScript
    )) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "Required observer health path missing: $Path"
        }
    }
    Assert-ExactFile -Expected $PackageExpert -Actual $TerminalExpert
    Assert-ExactFile -Expected $PackagePreset -Actual $TerminalPreset
    Assert-ExactFile -Expected $PackageConfig -Actual $TerminalConfig

    $ConfigText = Get-Content -Raw -LiteralPath $TerminalConfig
    foreach ($Required in @("AllowLiveTrading=0", "AllowDllImport=0")) {
        if ($ConfigText -notmatch [regex]::Escape($Required)) {
            throw "Observer terminal config missing safety setting: $Required"
        }
    }
    $PresetText = Get-Content -Raw -LiteralPath $TerminalPreset
    foreach ($Required in @(
        "InpRequireDemoAccount=true",
        "InpResetPersistentState=false",
        "InpProspectiveStartUtc=2026.08.01 00:00"
    )) {
        if ($PresetText -notmatch [regex]::Escape($Required)) {
            throw "Observer preset is not frozen safely: $Required"
        }
    }

    $Process = Get-ObserverProcess
    if (-not $Process) {
        $Process = Start-Process `
            -FilePath $TerminalExecutable `
            -ArgumentList @("/portable", "/config:`"$TerminalConfig`"") `
            -WindowStyle Hidden `
            -PassThru
        Write-OperationsLog "OBSERVER_RESTARTED pid=$($Process.Id)"
        Start-Sleep -Seconds 8
        $Process = Get-ObserverProcess
        if (-not $Process) {
            throw "RSI health-gate observer terminal failed to remain running"
        }
    }
    if (-not (Test-Path -LiteralPath $AuditCsv)) {
        throw "RSI health-gate observer audit ledger is missing"
    }
    & $PythonExecutable $AuditScript `
        --audit-csv $AuditCsv `
        --output-dir $HealthRoot | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "RSI health-gate observer audit failed"
    }
    $Audit = Get-Content -Raw -LiteralPath (
        Join-Path $HealthRoot "OBSERVER_HEALTH.json"
    ) | ConvertFrom-Json
    if ($Audit.status -eq "FAIL" -or $Audit.demo_order_authorized) {
        throw "RSI health-gate observer is not safely disarmed"
    }
    Write-OperationsLog (
        "HEALTH_OK status=$($Audit.status) " +
        "opens=$($Audit.virtual_opens) closes=$($Audit.virtual_closes) " +
        "admitted=$($Audit.health_admitted_opens) " +
        "raw_pf=$($Audit.raw_virtual_profit_factor) " +
        "admitted_pf=$($Audit.admitted_virtual_profit_factor) " +
        "pid=$($Process.ProcessId)"
    )
    exit 0
}
catch {
    Write-OperationsLog "FAIL detail=$($_.Exception.Message)"
    Write-Error $_
    exit 1
}
