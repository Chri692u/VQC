<#
Usage:
    powershell -ExecutionPolicy Bypass -File .\build_windows.ps1
    powershell -ExecutionPolicy Bypass -File .\build_windows.ps1 -CompileTarget py
    powershell -ExecutionPolicy Bypass -File .\build_windows.ps1 -CompileTarget cs

Common Dafny targets:
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

# /compile:0 tells Dafny to stop after generating target source.
# /spillTargetCode:3 writes the target code even if verification fails.
& dafny /compileTarget:$CompileTarget /compile:0 /spillTargetCode:3 /out:$outputFile $entryFile
