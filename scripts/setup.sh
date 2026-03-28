#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
proj="$repo_root/platforms/python/research/nexural-research"

echo "[setup] repoRoot: $repo_root"
echo "[setup] project:  $proj"

cd "$proj"

if [ ! -d ".venv" ]; then
  echo "[setup] Creating venv..."
  python3 -m venv .venv
fi

python=".venv/bin/python"

echo "[setup] Upgrading pip..."
"$python" -m pip install --upgrade pip

echo "[setup] Installing pinned dev dependencies..."
"$python" -m pip install -r requirements-dev.lock.txt

echo "[setup] Installing nexural-research (editable)..."
"$python" -m pip install -e .

echo "[setup] Running ruff..."
"$python" -m ruff check .

echo "[setup] Running pytest..."
"$python" -m pytest -q

echo "[setup] Generating sample report..."
"$python" -m nexural_research.cli report --input data/exports/sample_trades.csv

echo "[setup] Done."
