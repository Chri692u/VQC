<#
Usage:
    powershell -ExecutionPolicy Bypass -File .\clean_win.ps1

Removes only generated build output and language caches. It preserves source,
the Python virtual environment, and TypeScript node_modules.
#>

$ErrorActionPreference = 'Stop'

$targets = @(
    (Join-Path $PSScriptRoot 'compiled'),
    (Join-Path $PSScriptRoot 'python\compiled'),
    (Join-Path $PSScriptRoot 'python\__pycache__'),
    (Join-Path $PSScriptRoot 'python\bindings\__pycache__'),
    (Join-Path $PSScriptRoot 'python\examples\__pycache__'),
    (Join-Path $PSScriptRoot 'python\tests\__pycache__'),
    (Join-Path $PSScriptRoot 'typescript\compiled'),
    (Join-Path $PSScriptRoot 'typescript\vqc.js'),
    (Join-Path $PSScriptRoot 'typescript\bindings\index.js'),
    (Join-Path $PSScriptRoot 'typescript\bindings\vqc_account.js'),
    (Join-Path $PSScriptRoot 'typescript\bindings\vqc_currency.js'),
    (Join-Path $PSScriptRoot 'typescript\bindings\vqc_dafny_core.js'),
    (Join-Path $PSScriptRoot 'typescript\bindings\vqc_types.js')
)

foreach ($target in $targets) {
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}
