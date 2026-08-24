<#
Usage:
    powershell -ExecutionPolicy Bypass -File .\build_win.ps1
    powershell -ExecutionPolicy Bypass -File .\build_win.ps1 -CompileTarget py
    powershell -ExecutionPolicy Bypass -File .\build_win.ps1 -CompileTarget js

Dafny target examples:
    - cs  = C#
    - py  = Python
    - js  = JavaScript
#>

param(
        [string]$CompileTarget = 'py'
)

$ErrorActionPreference = 'Stop'

$srcDir = Join-Path $PSScriptRoot 'dafny'
$entryFile = Join-Path $srcDir 'Account.dfy'

if (-not (Get-Command dafny -ErrorAction SilentlyContinue)) {
        throw 'Dafny is required. Install Dafny and ensure "dafny" is on PATH.'
}

if (-not (Test-Path -LiteralPath $entryFile)) {
        throw "Dafny entry file not found: $entryFile"
}

switch ($CompileTarget) {
        'js' {
                $buildDirectory = Join-Path $PSScriptRoot 'typescript'
                $outputDir = Join-Path $buildDirectory 'compiled'
                $outputFile = Join-Path $outputDir 'VQC.js'
        }
        'py' {
                $buildDirectory = $PSScriptRoot
                $outputDir = Join-Path $PSScriptRoot 'python\compiled'
                $outputFile = Join-Path $outputDir 'VQC.py'
        }
        default {
                $buildDirectory = $PSScriptRoot
                $outputRoot = Join-Path $PSScriptRoot 'compiled'
                $outputDir = Join-Path $outputRoot $CompileTarget
                $outputFile = Join-Path $outputDir ('VQC.' + $CompileTarget)
        }
}

if ($CompileTarget -eq 'py') {
        $pythonExecutable = Join-Path $PSScriptRoot 'python\.venv\Scripts\python.exe'
        if (-not (Test-Path -LiteralPath $pythonExecutable)) {
                throw 'Python virtual environment not found. Create python\.venv and install python\requirements.txt.'
        }

        & $pythonExecutable -c 'import alpaca, dotenv, schedule'
        if ($LASTEXITCODE -ne 0) {
                throw 'Python dependencies are missing. Run python\.venv\Scripts\python.exe -m pip install -r python\requirements.txt.'
        }
}

if ($CompileTarget -eq 'js') {
        if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
                throw 'Node.js is required for the JavaScript target. Install Node.js and ensure "node" is on PATH.'
        }

        $bigNumberPackage = Join-Path $PSScriptRoot 'typescript\node_modules\bignumber.js\package.json'
        if (-not (Test-Path -LiteralPath $bigNumberPackage)) {
                throw 'TypeScript dependency bignumber.js is missing. Run "cd typescript; npm install".'
        }

        $typeScriptCompiler = Join-Path $PSScriptRoot 'typescript\node_modules\.bin\tsc.cmd'
        if (-not (Test-Path -LiteralPath $typeScriptCompiler) -and
            -not (Get-Command tsc -ErrorAction SilentlyContinue)) {
                throw 'TypeScript compiler is missing. Install TypeScript globally or run "cd typescript; npm install" after adding it locally.'
        }
}

if (Test-Path $outputDir) {
        Remove-Item -Recurse -Force $outputDir
}

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

Push-Location $buildDirectory
try {
        & dafny build $entryFile --target:$CompileTarget --output:$outputFile
        if ($CompileTarget -eq 'js') {
                Add-Content -LiteralPath $outputFile -Value "`nmodule.exports = { BigNumber, _dafny, Types, Validation, Currency, Orders, AccountOps };"
        }
} finally {
        Pop-Location
}
