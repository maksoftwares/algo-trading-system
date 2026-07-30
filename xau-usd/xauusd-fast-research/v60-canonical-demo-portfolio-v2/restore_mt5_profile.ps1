[CmdletBinding()]
param(
    [string]$TerminalRoot = "C:\MT5PortableTier1BestEA",
    [string]$ProfileName = "Default"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $PackageRoot "..\..\..")).Path
$TerminalExe = Join-Path $TerminalRoot "terminal64.exe"
$MetaEditor = Join-Path $TerminalRoot "MetaEditor64.exe"
$Experts = Join-Path $TerminalRoot "MQL5\Experts"
$Profile = Join-Path $TerminalRoot "MQL5\Profiles\Charts\$ProfileName"
$Snapshot = Join-Path $PackageRoot "recovery\mt5-profile\Default"
$Runtime = Join-Path $TerminalRoot "MQL5\Files\v60_canonical_demo_v2"
$SourceRoot = Join-Path $RepoRoot "xau-usd\xauusd-phase1\mt5\Experts"

foreach ($required in @($TerminalExe, $MetaEditor, $Snapshot)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Recovery prerequisite is absent: $required"
    }
}
$running = @(Get-CimInstance Win32_Process -Filter "Name='terminal64.exe'" |
    Where-Object { $_.ExecutablePath -eq $TerminalExe })
if ($running) {
    throw "Stop only the V60 terminal before restoring its EAs and chart profile"
}

New-Item -ItemType Directory -Force -Path $Experts, $Profile, $Runtime | Out-Null
$backup = Join-Path $Runtime ("recovery_backup_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Force -Path $backup | Out-Null
Get-ChildItem -LiteralPath $Profile -Filter "chart*.chr" -ErrorAction SilentlyContinue |
    Move-Item -Destination $backup -Force

$sourceFiles = @(
    "A1XauM5MomentumContinuationExecutor.mq5",
    "Account1DailyProfitFloorGuardian.mq5",
    "AccountEquityGuardianShadow.mq5",
    "XauProspectiveTelemetryCollector.mq5"
)
foreach ($name in $sourceFiles) {
    $source = Join-Path $SourceRoot $name
    $target = Join-Path $Experts $name
    Copy-Item -LiteralPath $source -Destination $target -Force
    $log = Join-Path $Runtime ($name + ".recovery_compile.log")
    Start-Process -FilePath $MetaEditor -ArgumentList @(
        "/portable",
        "/compile:`"$target`"",
        "/log:`"$log`""
    ) -WindowStyle Hidden -PassThru -Wait | Out-Null
    $compiled = [System.IO.Path]::ChangeExtension($target, ".ex5")
    if (-not (Test-Path -LiteralPath $compiled -PathType Leaf)) {
        throw "Compiled EA is absent: $compiled"
    }
    $compileText = Get-Content -Raw -LiteralPath $log
    if ($compileText -notmatch "(?im)Result:\s+0 errors,\s+0 warnings") {
        throw "MetaEditor did not produce a clean compile for $name"
    }
}

Get-ChildItem -LiteralPath $Snapshot -Filter "chart*.chr" |
    Copy-Item -Destination $Profile -Force
$installed = @(Get-ChildItem -LiteralPath $Profile -Filter "chart*.chr")
if ($installed.Count -ne 6) {
    throw "The restored profile must contain exactly six charts"
}

[ordered]@{
    schema_version = "xauusd_v60_mt5_profile_recovery_v1"
    restored_at_utc = [DateTime]::UtcNow.ToString("o")
    terminal_root = $TerminalRoot
    profile = $ProfileName
    chart_count = $installed.Count
    compiled_eas = $sourceFiles
    backup = $backup
    account_login_expected = 1033030
    account_server_expected = "Capital.ComMena-Demo"
    live_authorized = $false
} | ConvertTo-Json -Depth 4
