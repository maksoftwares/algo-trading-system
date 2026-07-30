[CmdletBinding()]
param(
    [string]$TerminalRoot = "C:\MT5PortableTier1BestEA",
    [string]$ProfileName = "Default"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $PackageRoot "..\..\..")).Path
$ConfigPath = Join-Path $PackageRoot "config\v60_canonical_demo_portfolio_v2.json"
$Config = Get-Content -Raw -LiteralPath $ConfigPath | ConvertFrom-Json
$Experts = Join-Path $TerminalRoot "MQL5\Experts"
$Profile = Join-Path $TerminalRoot "MQL5\Profiles\Charts\$ProfileName"
$Runtime = Join-Path $TerminalRoot "MQL5\Files\v60_canonical_demo_v2"
$MetaEditor = Join-Path $TerminalRoot "MetaEditor64.exe"
$TerminalExe = Join-Path $TerminalRoot "terminal64.exe"

$running = @(Get-CimInstance Win32_Process -Filter "Name='terminal64.exe'" |
    Where-Object { $_.ExecutablePath -eq $TerminalExe })
if ($running) {
    throw "Stop only the verified V60 terminal before applying the safety repair"
}

$guardianChart = Join-Path $Profile "chart03.chr"
if (-not (Test-Path -LiteralPath $guardianChart -PathType Leaf)) {
    throw "Guardian chart is absent: $guardianChart"
}

$expected = @($Config.preflight.expected_charts |
    Where-Object { $_.id -eq "DAILY_GUARDIAN" })
if ($expected.Count -ne 1) {
    throw "The canonical config does not define exactly one DAILY_GUARDIAN"
}

$backup = Join-Path $Runtime (
    "safety_repair_backup_" + (Get-Date -Format "yyyyMMdd_HHmmss")
)
New-Item -ItemType Directory -Force -Path $backup, $Experts | Out-Null
Copy-Item -LiteralPath $guardianChart -Destination $backup -Force

$sources = @(
    "Account1DailyProfitFloorGuardian.mq5",
    "XauProspectiveTelemetryCollector.mq5"
)
$phase1 = Join-Path $RepoRoot "xau-usd\xauusd-phase1\mt5\Experts"
foreach ($name in $sources) {
    $source = Join-Path $phase1 $name
    $target = Join-Path $Experts $name
    Copy-Item -LiteralPath $source -Destination $target -Force
    $log = Join-Path $Runtime ($name + ".safety_repair_compile.log")
    $process = Start-Process -FilePath $MetaEditor -ArgumentList @(
        "/portable",
        "/compile:`"$target`"",
        "/log:`"$log`""
    ) -WindowStyle Hidden -PassThru -Wait
    $compiled = [System.IO.Path]::ChangeExtension($target, ".ex5")
    if (-not (Test-Path -LiteralPath $compiled -PathType Leaf)) {
        throw "Compiled EA is absent after MetaEditor returned $($process.ExitCode)"
    }
    $compileText = Get-Content -Raw -LiteralPath $log
    if ($compileText -notmatch "(?im)Result:\s+0 errors,\s+0 warnings") {
        throw "MetaEditor did not produce a clean compile for $name"
    }
}

$encoding = [System.Text.Encoding]::Unicode
$chartText = [System.IO.File]::ReadAllText($guardianChart, $encoding)
$match = [regex]::Match(
    $chartText,
    "(?s)<expert>\r?\nname=Account1DailyProfitFloorGuardian\r?\n.*?</expert>"
)
if (-not $match.Success) {
    throw "Guardian expert block is absent from chart03.chr"
}
$block = $match.Value
foreach ($property in $expected[0].inputs.PSObject.Properties) {
    $key = [string]$property.Name
    $value = [string]$property.Value
    $linePattern = "(?m)^" + [regex]::Escape($key) + "=.*$"
    if ([regex]::IsMatch($block, $linePattern)) {
        $block = [regex]::Replace($block, $linePattern, "$key=$value")
    }
    else {
        $block = $block -replace "</inputs>", "$key=$value`r`n</inputs>"
    }
}
$updated = $chartText.Substring(0, $match.Index) +
    $block +
    $chartText.Substring($match.Index + $match.Length)
[System.IO.File]::WriteAllText($guardianChart, $updated, $encoding)

$halt = Join-Path (Join-Path $TerminalRoot "MQL5\Files") "tier1_bestea_kill_switch.txt"
$haltRemoved = $false
if (Test-Path -LiteralPath $halt) {
    $haltText = Get-Content -Raw -LiteralPath $halt
    if ($haltText.Contains("A1_DAILY_PROFIT_FLOOR_GUARDIAN")) {
        Copy-Item -LiteralPath $halt -Destination $backup -Force
        Remove-Item -LiteralPath $halt
        $haltRemoved = $true
    }
}

[ordered]@{
    schema_version = "xauusd_v60_safety_repair_deployment_v1"
    applied_at_utc = [DateTime]::UtcNow.ToString("o")
    terminal_root = $TerminalRoot
    guardian_chart = $guardianChart
    backup = $backup
    daily_profit_floor_enabled = $false
    daily_loss_stop_aed = -100.0
    close_scope_symbol = "XAUUSD"
    close_scope_magics = [string]$expected[0].inputs.InpAllowedPositionMagicsCsv
    guardian_owned_halt_removed = $haltRemoved
    minimum_balance_requirement_enabled = $false
    compiled_zero_errors_zero_warnings = $true
} | ConvertTo-Json -Depth 4
