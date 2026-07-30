param(
    [string]$TaskName = "Codex-EURUSD-Forward-Combined-Residual-V2",
    [switch]$StartNow
)

$ErrorActionPreference = "Stop"
$OperationsScript = Join-Path $PSScriptRoot "run_forward_combined_residual_cycle.ps1"
if (-not (Test-Path -LiteralPath $OperationsScript)) {
    throw "Combined residual operations script missing: $OperationsScript"
}
if ((Get-TimeZone).Id -ne "Arabian Standard Time") {
    throw "Daily 06:25 trigger requires Arabian Standard Time"
}

$PowerShell = Join-Path $PSHOME "powershell.exe"
$Arguments = (
    "-NoProfile -NonInteractive -ExecutionPolicy Bypass " +
    "-File `"$OperationsScript`""
)
$Action = New-ScheduledTaskAction -Execute $PowerShell -Argument $Arguments
$Trigger = New-ScheduledTaskTrigger -Daily -At "06:25"
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
    -Description "Disarmed EURUSD combined residual forward admission monitor v2" `
    -Force | Out-Null

if ($StartNow) {
    Start-ScheduledTask -TaskName $TaskName
}

Get-ScheduledTask -TaskName $TaskName |
    Select-Object TaskName, State, TaskPath
