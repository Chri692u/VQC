<#
Usage:
    powershell -ExecutionPolicy Bypass -File .\build_windows.ps1
    powershell -ExecutionPolicy Bypass -File .\build_windows.ps1 -CompileTarget py
    powershell -ExecutionPolicy Bypass -File .\build_windows.ps1 -CompileTarget cs

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
$entryFile = Join-Path $srcDir 'Execution.dfy'

$outputRoot = Join-Path $PSScriptRoot 'compiled'
$outputDir = Join-Path $outputRoot $CompileTarget

$outputExtension = $CompileTarget

$outputFile = Join-Path $outputDir ('VQC.' + $outputExtension)

if (Test-Path $outputDir) {
        Remove-Item -Recurse -Force $outputDir
}

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

& dafny build $entryFile --target:$CompileTarget --output:$outputFile
