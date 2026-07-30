[CmdletBinding()]
param(
    [string]$TerminalRoot = "C:\MT5PortableTier1BestEA",
    [switch]$InstallMt5Profile,
    [switch]$EnableAlgoTrading
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $PackageRoot "..\..\..")).Path
$Venv = Join-Path $PackageRoot ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"
$Requirements = Join-Path $PackageRoot "requirements-runtime.lock.txt"
$Verify = Join-Path $PackageRoot "recovery\verify_recovery.py"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is required. Install it from https://docs.astral.sh/uv/ and rerun."
}

& uv python install 3.14.4
if ($LASTEXITCODE -ne 0) {
    throw "Unable to install the locked Python runtime"
}
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    & uv venv --python 3.14.4 $Venv
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to create the V60 virtual environment"
    }
}
& uv pip sync --python $Python $Requirements
if ($LASTEXITCODE -ne 0) {
    throw "Unable to install the locked V60 Python dependencies"
}
& $Python $Verify
if ($LASTEXITCODE -ne 0) {
    throw "Repository recovery verification failed"
}

if ($InstallMt5Profile) {
    & (Join-Path $PackageRoot "restore_mt5_profile.ps1") -TerminalRoot $TerminalRoot
}
if ($EnableAlgoTrading) {
    if (-not $InstallMt5Profile) {
        throw "Use -InstallMt5Profile together with -EnableAlgoTrading"
    }
    & (Join-Path $PackageRoot "set_terminal_algo_trading.ps1") `
        -State Enabled `
        -TerminalRoot $TerminalRoot
}

[ordered]@{
    schema_version = "xauusd_v60_demo_restore_v1"
    status = "PREPARED"
    repo_root = $RepoRoot
    python = $Python
    mt5_profile_installed = [bool]$InstallMt5Profile
    algo_trading_enabled = [bool]$EnableAlgoTrading
    next = "Start MT5, verify demo login 1033030, then run xau-usd\operations\v60-prospective-supervisor-v1\start_supervisor.ps1"
} | ConvertTo-Json -Depth 3
