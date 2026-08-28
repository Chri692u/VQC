<#
Usage:
    powershell -ExecutionPolicy Bypass -File .\compile_python.ps1
#>

$ErrorActionPreference = 'Stop'

$entryFile = Join-Path $PSScriptRoot 'dafny\Account.dfy'
$outputDirectory = Join-Path $PSScriptRoot 'python\compiled'
$outputFile = Join-Path $outputDirectory 'VQC.py'

if (-not (Get-Command dafny -ErrorAction SilentlyContinue)) {
    throw 'Dafny is required. Install Dafny and ensure "dafny" is on PATH.'
}

if (-not (Test-Path -LiteralPath $entryFile)) {
    throw "Dafny entry file not found: $entryFile"
}

if (Test-Path -LiteralPath $outputDirectory) {
    Remove-Item -LiteralPath $outputDirectory -Recurse -Force
}
New-Item -ItemType Directory -Path $outputDirectory | Out-Null

Push-Location $PSScriptRoot
try {
    & dafny build $entryFile --target:py --output:$outputFile
    if ($LASTEXITCODE -ne 0) {
        throw "Dafny Python compilation failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}
