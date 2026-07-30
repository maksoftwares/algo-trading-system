param(
    [string]$TaskName = "Codex-EURUSD-Forward-Residual-Live-Outcome",
    [switch]$StartNow
)

$ErrorActionPreference = "Stop"
$OperationsScript = Join-Path $PSScriptRoot "run_forward_residual_live_outcome_cycle.ps1"
if (-not (Test-Path -LiteralPath $OperationsScript)) {
    throw "Residual live-outcome operations script missing: $OperationsScript"
}
if ((Get-TimeZone).Id -ne "Arabian Standard Time") {
    throw "Daily 06:20 trigger requires Arabian Standard Time"
}

$PowerShell = Join-Path $PSHOME "powershell.exe"
$Arguments = (
    "-NoProfile -NonInteractive -ExecutionPolicy Bypass " +
    "-File `"$OperationsScript`""
)
$Action = New-ScheduledTaskAction -Execute $PowerShell -Argument $Arguments
$Trigger = New-ScheduledTaskTrigger -Daily -At "06:20"
$Settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 20)
$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Raw-tick EURUSD residual live outcome and selection parity" `
    -Force | Out-Null

if ($StartNow) {
    Start-ScheduledTask -TaskName $TaskName
}

Get-ScheduledTask -TaskName $TaskName |
    Select-Object TaskName, State, TaskPath
