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

$srcDir = Join-Path $PSScriptRoot 'src'
$entryFile = Join-Path $srcDir 'Account.dfy'

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
