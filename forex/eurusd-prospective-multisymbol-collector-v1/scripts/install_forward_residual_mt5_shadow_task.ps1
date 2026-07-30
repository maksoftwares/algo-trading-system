param(
    [string]$TaskName = "Codex-EURUSD-Forward-Residual-MT5-Shadow",
    [switch]$StartNow
)

$ErrorActionPreference = "Stop"
$OperationsScript = Join-Path $PSScriptRoot "run_forward_residual_mt5_shadow_bridge.ps1"
if (-not (Test-Path -LiteralPath $OperationsScript)) {
    throw "Residual MT5 shadow operations script missing: $OperationsScript"
}
if ((Get-TimeZone).Id -ne "Arabian Standard Time") {
    throw "Daily 00:04 trigger requires Arabian Standard Time"
}

$PowerShell = Join-Path $PSHOME "powershell.exe"
$Arguments = (
    "-NoProfile -NonInteractive -ExecutionPolicy Bypass " +
    "-File `"$OperationsScript`""
)
$Action = New-ScheduledTaskAction -Execute $PowerShell -Argument $Arguments
$Trigger = New-ScheduledTaskTrigger -Daily -At "00:04"
$Settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
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
    -Description "Read-only MT5 quote bridge for EURUSD residual live signals" `
    -Force | Out-Null

if ($StartNow) {
    Start-ScheduledTask -TaskName $TaskName
}

Get-ScheduledTask -TaskName $TaskName |
    Select-Object TaskName, State, TaskPath
