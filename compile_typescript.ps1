<#
Usage:
    powershell -ExecutionPolicy Bypass -File .\compile_typescript.ps1
#>

$ErrorActionPreference = 'Stop'

$entryFile = Join-Path $PSScriptRoot 'dafny\Account.dfy'
$typeScriptDirectory = Join-Path $PSScriptRoot 'typescript'
$outputDirectory = Join-Path $typeScriptDirectory 'compiled'
$outputFile = Join-Path $outputDirectory 'VQC.js'
$nodeModules = Join-Path $typeScriptDirectory 'node_modules'

if (-not (Get-Command dafny -ErrorAction SilentlyContinue)) {
    throw 'Dafny is required. Install Dafny and ensure "dafny" is on PATH.'
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw 'Node.js and npm are required and must be available on PATH.'
}

if (-not (Test-Path -LiteralPath $entryFile)) {
    throw "Dafny entry file not found: $entryFile"
}

if (-not (Test-Path -LiteralPath $nodeModules)) {
    throw 'TypeScript dependencies are missing. Run "npm install" in the typescript directory.'
}

if (Test-Path -LiteralPath $outputDirectory) {
    Remove-Item -LiteralPath $outputDirectory -Recurse -Force
}
New-Item -ItemType Directory -Path $outputDirectory | Out-Null

Push-Location $typeScriptDirectory
try {
    & dafny build $entryFile --target:js --output:$outputFile
    if ($LASTEXITCODE -ne 0) {
        throw "Dafny JavaScript compilation failed with exit code $LASTEXITCODE."
    }

    Add-Content -LiteralPath $outputFile -Value "`nmodule.exports = { BigNumber, _dafny, Types, Validation, Currency, Orders, AccountOps };"

    & npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "TypeScript compilation failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}
