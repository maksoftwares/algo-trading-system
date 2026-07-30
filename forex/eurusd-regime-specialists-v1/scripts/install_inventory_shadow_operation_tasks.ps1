param(
    [switch]$StartMainNow,
    [switch]$StartClockNow
)

$ErrorActionPreference = "Stop"
$runner = Join-Path $PSScriptRoot "run_inventory_shadow_operation_helper.ps1"
if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) {
    throw "inventory task runner is missing: $runner"
}

$powerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$quotedRunner = '"{0}"' -f $runner
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited
$triggers = @(
    (New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME),
    (New-ScheduledTaskTrigger -Daily -At "12:05 AM")
)
$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -RestartCount 5 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -StartWhenAvailable

$definitions = @(
    @{
        Name = "Codex-EURUSD-Inventory-0005-Shadow"
        Campaign = "0005"
        Start = [bool]$StartMainNow
    },
    @{
        Name = "Codex-EURUSD-Inventory-Clock-Shadow"
        Campaign = "CLOCK"
        Start = [bool]$StartClockNow
    }
)

foreach ($definition in $definitions) {
    $arguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File {0} -Campaign {1}' -f $quotedRunner, $definition.Campaign
    $action = New-ScheduledTaskAction `
        -Execute $powerShell `
        -Argument $arguments `
        -WorkingDirectory (Split-Path -Parent $runner)
    $task = New-ScheduledTask `
        -Action $action `
        -Trigger $triggers `
        -Principal $principal `
        -Settings $settings `
        -Description "Disarmed EURUSD prospective inventory shadow evidence collector; broker actions are prohibited."
    Register-ScheduledTask `
        -TaskName $definition.Name `
        -InputObject $task `
        -Force | Out-Null
    if ($definition.Start) {
        Start-ScheduledTask -TaskName $definition.Name
    }
}

Get-ScheduledTask |
    Where-Object TaskName -In $definitions.Name |
    Sort-Object TaskName |
    Select-Object TaskName, State
