param(
    [switch]$Once
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$configPath = Join-Path $PSScriptRoot 'config\runtime_supervisor_v1.json'
$statusRunner = Join-Path $PSScriptRoot 'runtime_status.py'
$config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json
$runtime = [System.IO.Path]::GetFullPath([string]$config.runtime.directory)
$processStatePath = Join-Path $runtime ([string]$config.runtime.process_state)

New-Item -ItemType Directory -Force -Path $runtime | Out-Null

function Resolve-RepoPath {
    param([string]$Value)
    if ([System.IO.Path]::IsPathRooted($Value)) {
        return [System.IO.Path]::GetFullPath($Value)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $repo $Value))
}

function Get-AllProcesses {
    return @(Get-CimInstance Win32_Process)
}

function Get-MatchingProcesses {
    param(
        [object[]]$Processes,
        [string]$Marker,
        [string]$Name
    )
    return @($Processes | Where-Object {
        $_.Name -eq $Name -and
        $_.CommandLine -and
        $_.CommandLine -like "*$Marker*"
    })
}

function Write-JsonAtomic {
    param(
        [string]$Path,
        [object]$Payload
    )
    $temporary = "$Path.tmp"
    $json = $Payload | ConvertTo-Json -Depth 12
    [System.IO.File]::WriteAllText(
        $temporary,
        $json,
        [System.Text.UTF8Encoding]::new($false)
    )
    Move-Item -Force -LiteralPath $temporary -Destination $Path
}

function Test-FreshStatusFallback {
    param([object]$Worker)
    if (-not $Worker.existing_status_path) {
        return $false
    }
    try {
        $path = Resolve-RepoPath ([string]$Worker.existing_status_path)
        $payload = Get-Content -Raw -LiteralPath $path | ConvertFrom-Json
        $updated = [DateTimeOffset]::Parse([string]$payload.updated_at_utc)
        $age = ([DateTimeOffset]::UtcNow - $updated.ToUniversalTime()).TotalSeconds
        return $age -le [double]$Worker.existing_status_max_age_seconds
    }
    catch {
        return $false
    }
}

function Reconcile-Workers {
    $processes = Get-AllProcesses
    $workerState = @()

    foreach ($worker in $config.workers) {
        $marker = [string]$worker.command_marker
        $matches = Get-MatchingProcesses -Processes $processes -Marker $marker -Name 'python.exe'
        $started = $false
        $statusFallback = $false
        $errorText = $null

        if ($matches.Count -eq 0) {
            $statusFallback = Test-FreshStatusFallback -Worker $worker
            if (-not $statusFallback) {
                $python = Resolve-RepoPath ([string]$worker.python)
                $script = Resolve-RepoPath ([string]$worker.script)
                try {
                    if (-not (Test-Path -LiteralPath $python)) {
                        throw "Python runtime is missing: $python"
                    }
                    if (-not (Test-Path -LiteralPath $script)) {
                        throw "Worker script is missing: $script"
                    }
                    $arguments = @("`"$script`"")
                    foreach ($argument in $worker.args) {
                        $arguments += [string]$argument
                    }
                    $stdout = Join-Path $runtime ("{0}.stdout.log" -f $worker.id)
                    $stderr = Join-Path $runtime ("{0}.stderr.log" -f $worker.id)
                    Start-Process -FilePath $python `
                        -ArgumentList $arguments `
                        -WorkingDirectory $repo `
                        -WindowStyle Hidden `
                        -RedirectStandardOutput $stdout `
                        -RedirectStandardError $stderr | Out-Null
                    $started = $true
                }
                catch {
                    $errorText = $_.Exception.Message
                }
            }
        }

        $workerState += [pscustomobject]@{
            id = [string]$worker.id
            running = (($matches.Count -gt 0) -or $statusFallback)
            process_ids = @($matches | ForEach-Object { [int]$_.ProcessId })
            started_this_cycle = $started
            status_fallback = $statusFallback
            error = $errorText
        }
    }

    if (@($workerState | Where-Object { $_.started_this_cycle }).Count -gt 0) {
        Start-Sleep -Seconds 3
        $processes = Get-AllProcesses
        foreach ($state in $workerState) {
            $worker = @($config.workers | Where-Object { $_.id -eq $state.id })[0]
            $matches = Get-MatchingProcesses `
                -Processes $processes `
                -Marker ([string]$worker.command_marker) `
                -Name 'python.exe'
            $statusFallback = Test-FreshStatusFallback -Worker $worker
            $state.running = (($matches.Count -gt 0) -or $statusFallback)
            $state.process_ids = @($matches | ForEach-Object { [int]$_.ProcessId })
            $state.status_fallback = $statusFallback
        }
    }

    $terminalMatches = @(Get-MatchingProcesses `
        -Processes $processes `
        -Marker ([string]$config.terminal.command_marker) `
        -Name 'terminal64.exe')
    $allWorkersRunning = @($workerState | Where-Object { -not $_.running }).Count -eq 0
    $statePayload = [ordered]@{
        schema_version = [string]$config.schema_version
        updated_at_utc = [DateTime]::UtcNow.ToString('o').Replace('+00:00', 'Z')
        terminal_running = ($terminalMatches.Count -gt 0)
        terminal_process_ids = @($terminalMatches | ForEach-Object { [int]$_.ProcessId })
        all_workers_running = $allWorkersRunning
        workers = $workerState
        strategy_or_risk_parameters_changed = $false
        broker_action_added = $false
    }
    Write-JsonAtomic -Path $processStatePath -Payload $statePayload
}

$statusPython = Resolve-RepoPath 'xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/.venv/Scripts/python.exe'

while ($true) {
    Reconcile-Workers
    & $statusPython $statusRunner --config $configPath --write
    $statusExit = $LASTEXITCODE
    if ($Once) {
        exit $statusExit
    }
    Start-Sleep -Seconds ([Math]::Max(30, [int]$config.poll_seconds))
}
