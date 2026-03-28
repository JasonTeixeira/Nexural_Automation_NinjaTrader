$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path "$PSScriptRoot/..").Path
$proj = Join-Path $repoRoot 'platforms/python/research/nexural-research'
$venv = Join-Path $proj '.venv'

Write-Host "[setup] repoRoot: $repoRoot"
Write-Host "[setup] project:  $proj"

Set-Location $proj

if (-not (Test-Path $venv)) {
  Write-Host "[setup] Creating venv..."
  python -m venv .venv
}

$python = Join-Path $venv 'Scripts/python.exe'

Write-Host "[setup] Upgrading pip..."
& $python -m pip install --upgrade pip

Write-Host "[setup] Installing pinned dev dependencies..."
& $python -m pip install -r requirements-dev.lock.txt

Write-Host "[setup] Installing nexural-research (editable)..."
& $python -m pip install -e .

Write-Host "[setup] Running ruff..."
& $python -m ruff check .

Write-Host "[setup] Running pytest..."
& $python -m pytest -q

Write-Host "[setup] Generating sample report..."
& $python -m nexural_research.cli report --input data/exports/sample_trades.csv

Write-Host "[setup] Done."
