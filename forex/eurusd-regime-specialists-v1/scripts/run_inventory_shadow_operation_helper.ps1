param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("0005", "CLOCK")]
    [string]$Campaign
)

$ErrorActionPreference = "Stop"
$packageRoot = Split-Path -Parent $PSScriptRoot
$uv = "C:\Users\ZHAO ZHU INFORMATION\.local\bin\uv.exe"
if (-not (Test-Path -LiteralPath $uv -PathType Leaf)) {
    throw "uv executable is missing: $uv"
}

if ($Campaign -eq "0005") {
    $pythonScript = Join-Path $packageRoot "run_prospective_neutral_inventory_unwind_0005_daily_operations.py"
    $operationRoot = "D:\AlgoTradingData\prospective\eurusd-neutral-inventory-unwind-0005-v1\operations"
} else {
    $pythonScript = Join-Path $packageRoot "run_prospective_inventory_clock_operations_safe.py"
    $operationRoot = "D:\AlgoTradingData\prospective\eurusd-neutral-inventory-clock-transfer-v1\operations"
}

if (-not (Test-Path -LiteralPath $pythonScript -PathType Leaf)) {
    throw "inventory operation script is missing: $pythonScript"
}
New-Item -ItemType Directory -Path $operationRoot -Force | Out-Null
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$stdout = Join-Path $operationRoot ("task_{0}_{1}.stdout.log" -f $Campaign.ToLowerInvariant(), $stamp)
$stderr = Join-Path $operationRoot ("task_{0}_{1}.stderr.log" -f $Campaign.ToLowerInvariant(), $stamp)

Set-Location -LiteralPath $packageRoot
& $uv run --offline --with pandas --with numpy --with pyarrow --with scikit-learn python $pythonScript 1>> $stdout 2>> $stderr
exit $LASTEXITCODE
