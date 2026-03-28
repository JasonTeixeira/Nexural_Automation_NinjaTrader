# Getting Started (Nexural Automation)

This repo is a **simulation-first** collection of NinjaTrader 8 + TradingView modules, plus a **Python research toolkit** for analyzing NinjaTrader exports.

## 0) Clone

```bash
git clone https://github.com/JasonTeixeira/Nexural_Automation.git
cd Nexural_Automation
```

## 1) Python research toolkit (recommended)

The Python research package lives at:

`platforms/python/research/nexural-research`

### Windows (PowerShell)

```powershell
./scripts/setup.ps1
```

### macOS/Linux (bash)

```bash
./scripts/setup.sh
```

### What the setup scripts do
- create a local virtualenv under `platforms/python/research/nexural-research/.venv`
- install pinned dependencies from `requirements-dev.lock.txt`
- install `nexural-research` in editable mode
- run `ruff` + `pytest`
- generate a sample HTML report from `data/exports/sample_trades.csv`

After it runs, you should see a report at:
`platforms/python/research/nexural-research/reports/<run_id>/report.html`

## 2) NinjaTrader 8 modules

Browse:
- `platforms/ninjatrader/Strategies/`
- `platforms/ninjatrader/Indicators/`

To create a new strategy module:
1. Copy `templates/strategy-template/` → `platforms/ninjatrader/Strategies/<StrategyName>/`
2. Fill out `metadata.yaml`, `README.md`, `parameters.md` first
3. Add your NinjaScript under `src/`

## 3) TradingView modules

Browse:
- `platforms/tradingview/`

## Recommended reading order
1. `DISCLAIMER.md`
2. `docs/installation.md`
3. `docs/architecture.md`
4. `docs/backtesting-policy.md`
5. `CONTRIBUTING.md`
