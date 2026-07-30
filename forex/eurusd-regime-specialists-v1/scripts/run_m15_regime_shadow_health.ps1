param(
    [string]$TerminalRoot = "C:\MT5PortableM15RegimeShadow",
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
$AuditScript = Join-Path $PSScriptRoot "audit_m15_regime_shadow.py"
$StateRoot = Join-Path $TerminalRoot "EURUSDM15ShadowState"
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
    foreach ($Path in @($UvExecutable, $AuditScript, $TerminalExecutable, $TerminalConfig)) {
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
    Write-OperationsLog (
        "HEALTH_OK status=$($Audit.status) " +
        "signals=$($Audit.signals) blocked=$($Audit.blocked_signals) " +
        "pid=$($Process.ProcessId)"
    )
    exit 0
}
catch {
    Write-OperationsLog "FAIL detail=$($_.Exception.Message)"
    Write-Error $_
    exit 1
}
