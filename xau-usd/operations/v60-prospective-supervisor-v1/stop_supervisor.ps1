$ErrorActionPreference = "Stop"

$configPath = Join-Path $PSScriptRoot "config\runtime_supervisor_v1.json"
$config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json
$processes = @(Get-CimInstance Win32_Process)
$stopped = @()

foreach ($worker in $config.workers) {
    $matches = @($processes | Where-Object {
        $_.Name -eq "python.exe" -and
        $_.CommandLine -and
        $_.CommandLine -like ("*" + [string]$worker.command_marker + "*")
    })
    foreach ($process in $matches) {
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
        $stopped += [int]$process.ProcessId
    }
}

$supervisorPattern = "(?i)v60-prospective-supervisor-v1[\\/]runtime_supervisor\.ps1"
$supervisors = @($processes | Where-Object {
    $_.ProcessId -ne $PID -and
    $_.Name -in @("powershell.exe", "pwsh.exe") -and
    $_.CommandLine -and
    $_.CommandLine -match $supervisorPattern
})
foreach ($process in $supervisors) {
    Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
    $stopped += [int]$process.ProcessId
}

[ordered]@{
    schema_version = "xauusd_v60_supervisor_stop_v1"
    stopped_process_ids = @($stopped | Sort-Object -Unique)
    terminal_was_not_stopped = $true
} | ConvertTo-Json
