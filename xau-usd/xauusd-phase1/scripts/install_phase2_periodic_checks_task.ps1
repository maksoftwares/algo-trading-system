param(
    [string]$TaskName = "phase2-periodic-readiness-check",
    [string]$Phase1Root = "C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1",
    [string]$PythonExe = "C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\.venv\Scripts\python.exe",
    [string]$FilesDir = "C:\MT5PortableGoldMission\MQL5\Files",
    [string]$SpreadFilesDir = "C:\MT5PortableSpreadLogger\MQL5\Files",
    [string]$CompileLog = "C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log",
    [int]$IntervalMinutes = 60,
    [switch]$WhatIfOnly
)

$ErrorActionPreference = "Stop"

function Assert-PathPresent {
    param(
        [string]$Label,
        [string]$PathValue
    )
    if (-not (Test-Path -LiteralPath $PathValue)) {
        throw "$Label does not exist: $PathValue"
    }
}

if ($IntervalMinutes -lt 15) {
    throw "IntervalMinutes must be at least 15 to avoid noisy report churn."
}

Assert-PathPresent -Label "Phase1Root" -PathValue $Phase1Root
Assert-PathPresent -Label "PythonExe" -PathValue $PythonExe
Assert-PathPresent -Label "FilesDir" -PathValue $FilesDir
Assert-PathPresent -Label "SpreadFilesDir" -PathValue $SpreadFilesDir

$ScriptPath = Join-Path $Phase1Root "scripts\run_phase1_periodic_checks.py"
Assert-PathPresent -Label "run_phase1_periodic_checks.py" -PathValue $ScriptPath

$ActionArgs = @(
    "`"$ScriptPath`"",
    "--files-dir", "`"$FilesDir`"",
    "--spread-files-dir", "`"$SpreadFilesDir`"",
    "--compile-log", "`"$CompileLog`"",
    "--root", "`"$Phase1Root`""
) -join " "

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument $ActionArgs -WorkingDirectory $Phase1Root
$Trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Write-Host "TaskName: $TaskName"
Write-Host "Phase1Root: $Phase1Root"
Write-Host "Command: $PythonExe $ActionArgs"
Write-Host "IntervalMinutes: $IntervalMinutes"

if ($WhatIfOnly) {
    Write-Host "WhatIfOnly set. Scheduled task was not registered."
    exit 0
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Runs Phase 1/2 dry-run readiness checks and dashboard refresh. Does not start MT5 or authorize demo trading." `
    -Force | Out-Null

Write-Host "Registered scheduled task: $TaskName"
Write-Host "Run the task once manually, then inspect outputs\reports\PHASE1_EXTERNAL_HEALTH.json and PHASE2_READINESS_REPORT.md."
