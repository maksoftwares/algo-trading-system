param(
    [string]$Phase1Root,
    [string]$TemplatesDir,
    [string]$ReportsDir,
    [switch]$Force,
    [switch]$AllowOverwriteVerified
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Phase1Root)) {
    $Phase1Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
}

if ([string]::IsNullOrWhiteSpace($TemplatesDir)) {
    $TemplatesDir = Join-Path $Phase1Root "docs\templates"
}

if ([string]::IsNullOrWhiteSpace($ReportsDir)) {
    $ReportsDir = Join-Path $Phase1Root "outputs\reports"
}

$templateMap = @(
    @{ Template = "vps_ntp_sync.template.txt"; Target = "vps_ntp_sync.txt" },
    @{ Template = "vps_backup_config.template.txt"; Target = "vps_backup_config.txt" },
    @{ Template = "vps_rdp_recovery.template.txt"; Target = "vps_rdp_recovery.txt" },
    @{ Template = "vps_periodic_task.template.txt"; Target = "vps_periodic_task.txt" }
)

New-Item -ItemType Directory -Path $ReportsDir -Force | Out-Null

$items = @()
foreach ($item in $templateMap) {
    $source = Join-Path $TemplatesDir $item.Template
    $target = Join-Path $ReportsDir $item.Target

    if (-not (Test-Path -LiteralPath $source)) {
        throw "Missing template: $source"
    }

    $targetExists = Test-Path -LiteralPath $target
    $targetText = ""
    if ($targetExists) {
        $targetText = Get-Content -Raw -LiteralPath $target
    }

    $isVerified = $targetText -match "(?im)^\s*evidence_status\s*:\s*VERIFIED\s*$"
    if ($targetExists -and $isVerified -and -not $AllowOverwriteVerified) {
        $items += [pscustomobject]@{
            target = $target
            source = $source
            action = "SKIPPED_VERIFIED"
            reason = "Existing verified evidence was preserved."
        }
        continue
    }

    if ($targetExists -and -not $Force) {
        $items += [pscustomobject]@{
            target = $target
            source = $source
            action = "SKIPPED_EXISTING"
            reason = "Use -Force to refresh pending template evidence."
        }
        continue
    }

    Copy-Item -LiteralPath $source -Destination $target -Force
    $items += [pscustomobject]@{
        target = $target
        source = $source
        action = if ($targetExists) { "REFRESHED" } else { "CREATED" }
        reason = "Pending evidence template is ready to fill."
    }
}

$manifest = [pscustomobject]@{
    status = "PREPARED_PENDING_OWNER_VERIFICATION"
    created_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    authority = "Evidence workspace preparation only; does not authorize Phase 2, demo trading, broker execution, live capital, or MT5 runtime changes."
    phase1_root = $Phase1Root
    templates_dir = $TemplatesDir
    reports_dir = $ReportsDir
    allow_overwrite_verified = [bool]$AllowOverwriteVerified
    items = $items
}

$manifestPath = Join-Path $ReportsDir "vps_evidence_workspace_manifest.json"
$manifestJson = $manifest | ConvertTo-Json -Depth 5
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($manifestPath, $manifestJson, $utf8NoBom)

Write-Output "Phase 2 VPS evidence workspace prepared: $manifestPath"
foreach ($entry in $items) {
    Write-Output "$($entry.action): $($entry.target)"
}
