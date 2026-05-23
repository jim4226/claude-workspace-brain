# claude-workspace-brain installer (Windows PowerShell wrapper around _install.py)
#
# Usage from a cloned repo:
#   .\install.ps1 [-Target <path>] [-Force] [-Yes] [-WithStopHook]
#
# Usage as a one-liner (clones into %LOCALAPPDATA% and installs to cwd):
#   irm https://raw.githubusercontent.com/jim4226/claude-workspace-brain/main/install.ps1 | iex
[CmdletBinding()]
param(
  [string]$Target = (Get-Location).Path,
  [switch]$Force,
  [switch]$Yes,
  [switch]$WithStopHook
)

$ErrorActionPreference = "Stop"

$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { $null }

if (-not $scriptDir -or -not (Test-Path (Join-Path $scriptDir "template"))) {
  $cacheDir = Join-Path $env:LOCALAPPDATA "claude-workspace-brain"
  Write-Host "Bootstrap: cloning repo into $cacheDir ..."
  if (Test-Path $cacheDir) { Remove-Item -Recurse -Force $cacheDir }
  git clone --depth=1 https://github.com/jim4226/claude-workspace-brain.git $cacheDir
  if ($LASTEXITCODE -ne 0) { throw "git clone failed" }
  $scriptDir = $cacheDir
}

$python = $env:PYTHON_BIN
if (-not $python) {
  $python = (Get-Command python -ErrorAction SilentlyContinue).Source
  if (-not $python) {
    $python = (Get-Command py -ErrorAction SilentlyContinue).Source
  }
}
if (-not $python) { throw "Python 3.8+ required (set `$env:PYTHON_BIN to override)." }

$args = @("$scriptDir\_install.py", "--target", $Target)
if ($Force) { $args += "--force" }
if ($Yes) { $args += "--yes" }
if ($WithStopHook) { $args += "--with-stop-hook" }

& $python @args
exit $LASTEXITCODE
