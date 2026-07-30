param(
    [string]$TaskName = "Codex-EURUSD-Forward-Live-Combined-V3",
    [switch]$StartNow
)

$ErrorActionPreference = "Stop"
$OperationsScript = Join-Path $PSScriptRoot "run_forward_live_combined_cycle.ps1"
if (-not (Test-Path -LiteralPath $OperationsScript)) {
    throw "Live-combined operations script missing: $OperationsScript"
}
if ((Get-TimeZone).Id -ne "Arabian Standard Time") {
    throw "Daily 06:30 trigger requires Arabian Standard Time"
}

$PowerShell = Join-Path $PSHOME "powershell.exe"
$Arguments = (
    "-NoProfile -NonInteractive -ExecutionPolicy Bypass " +
    "-File `"$OperationsScript`""
)
$Action = New-ScheduledTaskAction -Execute $PowerShell -Argument $Arguments
$Trigger = New-ScheduledTaskTrigger -Daily -At "06:30"
$Settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
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
    -Description "Disarmed EURUSD live-only combined forward admission monitor v3" `
    -Force | Out-Null

if ($StartNow) {
    Start-ScheduledTask -TaskName $TaskName
}

Get-ScheduledTask -TaskName $TaskName |
    Select-Object TaskName, State, TaskPath
