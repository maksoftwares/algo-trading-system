[CmdletBinding()]
param(
    [string]$TerminalRoot = "C:\MT5PortableTier1BestEA",
    [string]$ProfileName = "Default"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedLogin = 1033030
$ExpectedServer = "Capital.ComMena-Demo"
$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $PackageRoot "..\..\..")).Path
$Phase1Experts = Join-Path $RepoRoot "xau-usd\xauusd-phase1\mt5\Experts"
$ExpertsDirectory = Join-Path $TerminalRoot "MQL5\Experts"
$ProfileDirectory = Join-Path $TerminalRoot "MQL5\Profiles\Charts\$ProfileName"
$RuntimeDirectory = Join-Path $TerminalRoot "MQL5\Files\v60_canonical_demo_v2"
$TerminalExe = Join-Path $TerminalRoot "terminal64.exe"
$CompileRoot = if (Test-Path -LiteralPath (Join-Path $TerminalRoot "MQL5\Include\Trade\Trade.mqh")) {
    $TerminalRoot
} else {
    "C:\MT5PortableGoldMission"
}
$MetaEditor = Join-Path $CompileRoot "MetaEditor64.exe"
$CompileExpertsDirectory = Join-Path $CompileRoot "MQL5\Experts"

if (-not (Test-Path -LiteralPath $TerminalExe -PathType Leaf)) {
    throw "Target terminal is absent: $TerminalExe"
}
if (-not (Test-Path -LiteralPath $MetaEditor -PathType Leaf)) {
    throw "Target MetaEditor is absent: $MetaEditor"
}

$runningTarget = Get-CimInstance Win32_Process -Filter "Name='terminal64.exe'" |
    Where-Object { $_.ExecutablePath -eq $TerminalExe }
if ($runningTarget) {
    throw "Stop only the verified target terminal before installing its offline chart profile"
}

New-Item -ItemType Directory -Force -Path $ExpertsDirectory, $CompileExpertsDirectory, $ProfileDirectory, $RuntimeDirectory | Out-Null

$sourceFiles = @(
    "XauProspectiveTelemetryCollector.mq5",
    "A1XauM5MomentumContinuationExecutor.mq5"
)
foreach ($name in $sourceFiles) {
    $source = Join-Path $Phase1Experts $name
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Required EA source is absent: $source"
    }
    Copy-Item -LiteralPath $source -Destination (Join-Path $ExpertsDirectory $name) -Force
    Copy-Item -LiteralPath $source -Destination (Join-Path $CompileExpertsDirectory $name) -Force
}

foreach ($name in $sourceFiles) {
    $targetSource = Join-Path $CompileExpertsDirectory $name
    $log = Join-Path $RuntimeDirectory ($name + ".compile.log")
    $process = Start-Process -FilePath $MetaEditor -ArgumentList @(
        "/portable",
        "/compile:`"$targetSource`"",
        "/log:`"$log`""
    ) -WindowStyle Hidden -PassThru -Wait
    $compiled = [System.IO.Path]::ChangeExtension($targetSource, ".ex5")
    if (-not (Test-Path -LiteralPath $compiled -PathType Leaf)) {
        throw "Compiled EA is absent after MetaEditor returned $($process.ExitCode): $compiled"
    }
    $compileText = Get-Content -LiteralPath $log -Raw -ErrorAction SilentlyContinue
    if ($compileText -notmatch "(?im)Result:\s+0 errors") {
        throw "MetaEditor reported compile errors for $name; inspect $log"
    }
    Copy-Item -LiteralPath $compiled -Destination (Join-Path $ExpertsDirectory ([System.IO.Path]::GetFileName($compiled))) -Force
}

function Read-IniSection {
    param(
        [Parameter(Mandatory)] [string]$Path,
        [Parameter(Mandatory)] [string]$Section
    )
    $result = [ordered]@{}
    $inside = $false
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if ($trimmed -match '^\[(.+)\]$') {
            $inside = $Matches[1] -eq $Section
            continue
        }
        if (-not $inside -or $trimmed.Length -eq 0 -or $trimmed.StartsWith(';')) {
            continue
        }
        $parts = $line -split '=', 2
        if ($parts.Count -eq 2) {
            $result[$parts[0].Trim()] = $parts[1].Trim()
        }
    }
    return $result
}

function New-ExpertBlock {
    param(
        [Parameter(Mandatory)] [string]$Name,
        [Parameter(Mandatory)] [System.Collections.IDictionary]$Inputs
    )
    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.Add('<expert>')
    $lines.Add("name=$Name")
    $lines.Add("path=Experts\$Name.ex5")
    $lines.Add('expertmode=0')
    $lines.Add('<inputs>')
    foreach ($key in $Inputs.Keys) {
        $lines.Add("$key=$($Inputs[$key])")
    }
    $lines.Add('</inputs>')
    $lines.Add('</expert>')
    return $lines -join "`r`n"
}

function Write-Chart {
    param(
        [Parameter(Mandatory)] [string]$TemplateText,
        [Parameter(Mandatory)] [string]$Destination,
        [Parameter(Mandatory)] [long]$ChartId,
        [Parameter(Mandatory)] [string]$ExpertBlock
    )
    $text = [regex]::Replace($TemplateText, '(?m)^id=\d+\r?$', "id=$ChartId", 1)
    $text = [regex]::Replace($text, '<expert>[\s\S]*?</expert>', [System.Text.RegularExpressions.MatchEvaluator]{ param($match) $ExpertBlock }, 1)
    [System.IO.File]::WriteAllText($Destination, $text, [System.Text.Encoding]::Unicode)
}

$templatePath = Join-Path $ProfileDirectory "chart02.chr"
if (-not (Test-Path -LiteralPath $templatePath -PathType Leaf)) {
    $templatePath = Join-Path $ProfileDirectory "chart01.chr"
}
if (-not (Test-Path -LiteralPath $templatePath -PathType Leaf)) {
    throw "No existing XAUUSD chart is available as a profile template"
}
$templateText = [System.IO.File]::ReadAllText($templatePath, [System.Text.Encoding]::Unicode)
if ($templateText -notmatch '(?m)^symbol=XAUUSD\r?$') {
    throw "Chart template is not XAUUSD"
}
if ($templateText -notmatch '<expert>[\s\S]*?</expert>') {
    throw "Chart template has no replaceable expert block"
}

$backup = Join-Path $RuntimeDirectory ("profile_backup_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Force -Path $backup | Out-Null
Get-ChildItem -LiteralPath $ProfileDirectory -Filter '*.chr' |
    Copy-Item -Destination $backup -Force

$telemetryInputs = [ordered]@{
    InpRunId = "V60_V2_TELEMETRY_1033030"
    InpDryRunOnly = "true"
    InpTargetSymbol = "XAUUSD"
    InpExpectedServerMarker = "Demo"
    InpAllowedAccountLoginsCsv = "$ExpectedLogin"
    InpCollectTicks = "true"
    InpCollectMarketDepth = "true"
    InpCollectTradeTransactions = "true"
    InpHeartbeatSeconds = "5"
    InpFlushEveryRows = "100"
    InpFilePrefix = "xau_prospective"
}

$sensorDefinitions = @(
    [ordered]@{
        Chart = "chart04.chr"
        ChartId = 260103304
        RunId = "V60_V2_BREAK_AND_RUN_SENSOR"
        SignalLog = "v60_v2_break_and_run_signal_log.csv"
        Ini = "C:\MT5A1M5MomentumBacktest\Config\A1XauM5Momentum_OWNER_GOAL_RR2_PROFIT_LOCK_EXAM_202207_202606_XAUUSD_M5_rr2_lock100_010.ini"
        Magic = "969001"
    },
    [ordered]@{
        Chart = "chart05.chr"
        ChartId = 260103305
        RunId = "V60_V2_DOWNSIDE_RETEST_SENSOR"
        SignalLog = "v60_v2_downside_retest_signal_log.csv"
        Ini = "C:\MT5A1M5MomentumBacktest\Config\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_impulse_retest_body45.ini"
        Magic = "969002"
    },
    [ordered]@{
        Chart = "chart06.chr"
        ChartId = 260103306
        RunId = "V60_V2_OPENING_REVERSAL_SENSOR"
        SignalLog = "v60_v2_opening_reversal_signal_log.csv"
        Ini = "C:\MT5A1M5MomentumBacktest\Config\A1XauM5Momentum_OWNER_GOAL_ORREV_STEP4_EXAM_202207_202606_XAUUSD_M5_orrev_london_firm_stop15.ini"
        Magic = "969003"
    }
)

Write-Chart -TemplateText $templateText -Destination (Join-Path $ProfileDirectory "chart02.chr") -ChartId 260103302 -ExpertBlock (New-ExpertBlock -Name "XauProspectiveTelemetryCollector" -Inputs $telemetryInputs)

foreach ($sensor in $sensorDefinitions) {
    if (-not (Test-Path -LiteralPath $sensor.Ini -PathType Leaf)) {
        throw "Frozen sensor tester input is absent: $($sensor.Ini)"
    }
    $inputs = Read-IniSection -Path $sensor.Ini -Section "TesterInputs"
    $inputs["InpAllowDemoTrading"] = "false"
    $inputs["InpAllowedAccountLogin"] = "$ExpectedLogin"
    $inputs["InpExpectedServerMarker"] = "Demo"
    $inputs["InpTargetSymbol"] = "XAUUSD"
    $inputs["InpMagicNumber"] = $sensor.Magic
    $inputs["InpKillSwitchFileName"] = "v60_v2_observer_only_kill_switch.txt"
    $inputs["InpRunId"] = $sensor.RunId
    $inputs["InpStartupLogFileName"] = ($sensor.SignalLog -replace '_signal_log\.csv$', '_startup_log.csv')
    $inputs["InpSignalLogFileName"] = $sensor.SignalLog
    $inputs["InpOrderLogFileName"] = ($sensor.SignalLog -replace '_signal_log\.csv$', '_order_log.csv')
    $inputs["InpManagementLogFileName"] = ($sensor.SignalLog -replace '_signal_log\.csv$', '_management_log.csv')
    $inputs["InpOrderComment"] = "V60_V2_OBSERVER_ONLY"
    Write-Chart -TemplateText $templateText -Destination (Join-Path $ProfileDirectory $sensor.Chart) -ChartId $sensor.ChartId -ExpertBlock (New-ExpertBlock -Name "A1XauM5MomentumContinuationExecutor" -Inputs $inputs)
}

$chartFiles = Get-ChildItem -LiteralPath $ProfileDirectory -Filter '*.chr'
$profileText = ($chartFiles | ForEach-Object {
    [System.IO.File]::ReadAllText($_.FullName, [System.Text.Encoding]::Unicode)
}) -join "`n"

$forbidden = @(
    "Phase2ExperimentalDemoExecutor",
    "A3MlPredictionObserver",
    "InpMlShadowReadEnabled=true"
)
foreach ($term in $forbidden) {
    if ($profileText.Contains($term)) {
        throw "Forbidden legacy or ML term remains in chart profile: $term"
    }
}
foreach ($required in @(
    "AccountEquityGuardianShadow",
    "Account1DailyProfitFloorGuardian",
    "XauProspectiveTelemetryCollector",
    "V60_V2_BREAK_AND_RUN_SENSOR",
    "V60_V2_DOWNSIDE_RETEST_SENSOR",
    "V60_V2_OPENING_REVERSAL_SENSOR"
)) {
    if (-not $profileText.Contains($required)) {
        throw "Required deterministic profile component is absent: $required"
    }
}
if (($profileText -split 'InpAllowDemoTrading=true').Count -gt 1) {
    throw "An observer sensor has demo trading enabled"
}

$manifest = [ordered]@{
    schema_version = "xauusd_v60_canonical_mt5_profile_v2"
    installed_at_utc = [DateTime]::UtcNow.ToString("o")
    terminal = $TerminalExe
    compile_terminal = $CompileRoot
    account_login = $ExpectedLogin
    account_server = $ExpectedServer
    profile = $ProfileName
    chart_count = $chartFiles.Count
    algo_trading_expected_enabled = $false
    execution_enabled = $false
    ml_runtime_authorized = $false
    ml_shadow_authorized = $false
    backup = $backup
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $RuntimeDirectory "profile_install_manifest.json") -Encoding utf8
$manifest | ConvertTo-Json -Depth 5
