param(
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,
    [Parameter(Mandatory = $true)]
    [string]$StartDate,
    [Parameter(Mandatory = $true)]
    [string]$EndDate
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$rawRoot = Join-Path $OutputRoot "raw"
[IO.Directory]::CreateDirectory($rawRoot) | Out-Null
$start = [DateTime]::ParseExact(
    $StartDate,
    "yyyy-MM-dd",
    [Globalization.CultureInfo]::InvariantCulture
)
$end = [DateTime]::ParseExact(
    $EndDate,
    "yyyy-MM-dd",
    [Globalization.CultureInfo]::InvariantCulture
)
$downloaded = 0
$cached = 0
$date = $start
while ($date -le $end) {
    if (
        $date.DayOfWeek -ne [DayOfWeek]::Saturday -and
        $date.DayOfWeek -ne [DayOfWeek]::Sunday
    ) {
        $compact = $date.ToString("yyyyMMdd")
        $path = Join-Path $rawRoot "$compact.csv"
        if (Test-Path -LiteralPath $path) {
            $cached += 1
        }
        else {
            $query = (
                "reportDate=$compact&format=csv&volumeQueryType=O" +
                "&symbolType=U&symbol=FXE&reportType=D" +
                "&accountType=C&productKind=OSTK&porc=BOTH"
            )
            $url = (
                "https://marketdata.theocc.com/volume-query?" +
                $query
            )
            $success = $false
            for ($attempt = 1; $attempt -le 3; $attempt += 1) {
                try {
                    $response = Invoke-WebRequest `
                        -Uri $url `
                        -UseBasicParsing `
                        -TimeoutSec 60
                    [IO.File]::WriteAllBytes(
                        $path,
                        [byte[]]$response.Content
                    )
                    $success = $true
                    break
                }
                catch {
                    if ($attempt -eq 3) {
                        throw
                    }
                    Start-Sleep -Seconds ([Math]::Pow(3, $attempt - 1))
                }
            }
            if (-not $success) {
                throw "Failed to acquire $compact"
            }
            $downloaded += 1
            Start-Sleep -Milliseconds 75
        }
        $processed = $downloaded + $cached
        if ($processed % 25 -eq 0) {
            Write-Output (
                "processed=$processed downloaded=$downloaded " +
                "cached=$cached last=$compact"
            )
        }
    }
    $date = $date.AddDays(1)
}
Write-Output (
    "complete downloaded=$downloaded cached=$cached " +
    "start=$StartDate end=$EndDate"
)
