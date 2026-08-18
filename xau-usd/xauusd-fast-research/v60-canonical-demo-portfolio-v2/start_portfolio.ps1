param(
    [switch]$Once
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$runner = Join-Path $PSScriptRoot 'run_portfolio.py'
$feedRunner = Join-Path $PSScriptRoot 'run_feeds.py'
$researchFeedRunner = Join-Path $PSScriptRoot 'run_research_feeds.py'
$mlOverlay = Join-Path $PSScriptRoot 'config\v60_portable_ml_topup_v4_overlay.json'
$protectionOverlay = Join-Path $PSScriptRoot 'config\v60_drawdown_protection_v1_overlay.json'
$runtime = 'C:\MT5PortableTier1BestEA\MQL5\Files\v60_canonical_demo_v2'

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python runtime is missing: $python"
}

if ($Once) {
    & $python $feedRunner --once
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python $runner --once --protection-overlay $protectionOverlay --ml-overlay $mlOverlay
    $portfolioExitCode = $LASTEXITCODE
    & $python $researchFeedRunner --once
    exit $portfolioExitCode
}

$feedExisting = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'python.exe' -and
    $_.CommandLine -like '*v60-canonical-demo-portfolio-v2*run_feeds.py*'
}
if (-not $feedExisting) {
    New-Item -ItemType Directory -Force -Path $runtime | Out-Null
    Start-Process -FilePath $python `
        -ArgumentList @("`"$feedRunner`"") `
        -WorkingDirectory $repo `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $runtime 'feeds_stdout.log') `
        -RedirectStandardError (Join-Path $runtime 'feeds_stderr.log') | Out-Null
}

$researchFeedExisting = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'python.exe' -and
    $_.CommandLine -like '*v60-canonical-demo-portfolio-v2*run_research_feeds.py*'
}
if (-not $researchFeedExisting) {
    New-Item -ItemType Directory -Force -Path $runtime | Out-Null
    Start-Process -FilePath $python `
        -ArgumentList @("`"$researchFeedRunner`"") `
        -WorkingDirectory $repo `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $runtime 'research_feeds_stdout.log') `
        -RedirectStandardError (Join-Path $runtime 'research_feeds_stderr.log') | Out-Null
}

$existing = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'python.exe' -and
    $_.CommandLine -like '*v60-canonical-demo-portfolio-v2*run_portfolio.py*'
}
if ($existing) {
    $existing | Select-Object ProcessId, Name, CreationDate, CommandLine
    exit 0
}

New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$stdout = Join-Path $runtime 'executor_stdout.log'
$stderr = Join-Path $runtime 'executor_stderr.log'
$process = Start-Process -FilePath $python `
    -ArgumentList @(
        "`"$runner`"",
        "--protection-overlay",
        "`"$protectionOverlay`"",
        "--ml-overlay",
        "`"$mlOverlay`""
    ) `
    -WorkingDirectory $repo `
    -WindowStyle Hidden `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr `
    -PassThru

$process | Select-Object Id, ProcessName, StartTime
