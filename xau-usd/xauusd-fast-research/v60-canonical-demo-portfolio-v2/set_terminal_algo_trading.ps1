[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet("Enabled", "Disabled")]
    [string]$State,
    [string]$TerminalRoot = "C:\MT5PortableTier1BestEA"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$terminal = Join-Path $TerminalRoot "terminal64.exe"
$common = Join-Path $TerminalRoot "Config\common.ini"
$runtime = Join-Path $TerminalRoot "MQL5\Files\v60_canonical_demo_v2"
if (-not (Test-Path -LiteralPath $terminal -PathType Leaf)) {
    throw "Target terminal is absent: $terminal"
}
if (-not (Test-Path -LiteralPath $common -PathType Leaf)) {
    throw "Target terminal common.ini is absent: $common"
}
$running = Get-CimInstance Win32_Process -Filter "Name='terminal64.exe'" |
    Where-Object { $_.ExecutablePath -eq $terminal }
if ($running) {
    throw "Stop the verified target terminal before changing offline Algo Trading state"
}

New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$backup = Join-Path $runtime ("common_ini_backup_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".ini")
Copy-Item -LiteralPath $common -Destination $backup -Force

$text = [System.IO.File]::ReadAllText($common)
$sectionMatches = [regex]::Matches($text, '(?ms)^\[Experts\]\s*.*?(?=^\[|\z)')
if ($sectionMatches.Count -ne 1) {
    throw "common.ini must contain exactly one [Experts] section"
}
$enabled = if ($State -eq "Enabled") { "1" } else { "0" }
$sectionMatch = $sectionMatches[0]
$section = $sectionMatch.Value
if ($section -notmatch '(?m)^Enabled=[01]\r?$') {
    throw "common.ini [Experts] section has no recognized Enabled flag"
}
$updatedSection = [regex]::Replace($section, '(?m)^Enabled=[01]\r?$', "Enabled=$enabled", 1)
$updated = $text.Substring(0, $sectionMatch.Index) + $updatedSection + $text.Substring($sectionMatch.Index + $sectionMatch.Length)
[System.IO.File]::WriteAllText($common, $updated, [System.Text.UTF8Encoding]::new($false))

$verified = [System.IO.File]::ReadAllText($common)
$verifiedSection = [regex]::Match($verified, '(?ms)^\[Experts\]\s*.*?(?=^\[|\z)').Value
if ($verifiedSection -notmatch "(?m)^Enabled=$enabled\r?$") {
    throw "Algo Trading state did not persist"
}

[ordered]@{
    terminal = $terminal
    state = $State
    enabled_value = [int]$enabled
    backup = $backup
    changed_at_utc = [DateTime]::UtcNow.ToString("o")
} | ConvertTo-Json
