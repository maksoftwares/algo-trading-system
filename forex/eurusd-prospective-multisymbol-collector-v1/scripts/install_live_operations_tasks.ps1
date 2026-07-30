param(
    [string]$HealthTaskName = "Codex-EURUSD-Prospective-Health",
    [string]$DailyTaskName = "Codex-EURUSD-Forward-Learner"
)

$ErrorActionPreference = "Stop"
$OperationsScript = Join-Path $PSScriptRoot "run_live_forward_cycle.ps1"
if (-not (Test-Path -LiteralPath $OperationsScript)) {
    throw "Operations script missing: $OperationsScript"
}
if ((Get-TimeZone).Id -ne "Arabian Standard Time") {
    throw "Daily 18:10 trigger requires Arabian Standard Time"
}

$PowerShell = Join-Path $PSHOME "powershell.exe"
$HealthArguments = (
    "-NoProfile -NonInteractive -ExecutionPolicy Bypass " +
    "-File `"$OperationsScript`" -Mode Health"
)
$DailyArguments = (
    "-NoProfile -NonInteractive -ExecutionPolicy Bypass " +
    "-File `"$OperationsScript`" -Mode Daily"
)
$HealthAction = New-ScheduledTaskAction `
    -Execute $PowerShell `
    -Argument $HealthArguments
$DailyAction = New-ScheduledTaskAction `
    -Execute $PowerShell `
    -Argument $DailyArguments
$HealthTrigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$DailyTrigger = New-ScheduledTaskTrigger -Daily -At "18:10"
$Settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
$UserId = "$env:USERDOMAIN\$env:USERNAME"
$Principal = New-ScheduledTaskPrincipal `
    -UserId $UserId `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $HealthTaskName `
    -Action $HealthAction `
    -Trigger $HealthTrigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Read-only EURUSD prospective collector health and restart guard" `
    -Force | Out-Null
Register-ScheduledTask `
    -TaskName $DailyTaskName `
    -Action $DailyAction `
    -Trigger $DailyTrigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Forward-only EURUSD daily learner at 14:10 UTC / 18:10 Dubai" `
    -Force | Out-Null

Get-ScheduledTask -TaskName $HealthTaskName, $DailyTaskName |
    Select-Object TaskName, State, TaskPath

