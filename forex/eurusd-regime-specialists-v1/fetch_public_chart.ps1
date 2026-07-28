param(
    [Parameter(Mandatory = $true)]
    [string]$Url
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 60
$response.Content
