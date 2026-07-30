$ErrorActionPreference = 'Stop'
$supervisor = Join-Path $PSScriptRoot 'runtime_supervisor.ps1'
$configPath = Join-Path $PSScriptRoot 'config\runtime_supervisor_v1.json'
$config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json
$runtime = [System.IO.Path]::GetFullPath([string]$config.runtime.directory)
$supervisorPattern = (
    '(?i)-File\s+["'']?[^"'']*' +
    'v60-prospective-supervisor-v1[\\/]runtime_supervisor\.ps1'
)

$existing = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -in @('powershell.exe', 'pwsh.exe') -and
    $_.CommandLine -and
    $_.CommandLine -match $supervisorPattern
})
if ($existing.Count -gt 0) {
    $existing | Select-Object ProcessId, Name, CreationDate, CommandLine
    exit 0
}

New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$stdout = Join-Path $runtime 'supervisor.stdout.log'
$stderr = Join-Path $runtime 'supervisor.stderr.log'
$process = Start-Process -FilePath 'powershell.exe' `
    -ArgumentList @(
        '-NoProfile',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        "`"$supervisor`""
    ) `
    -WorkingDirectory $PSScriptRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr `
    -PassThru

$process | Select-Object Id, ProcessName, StartTime
