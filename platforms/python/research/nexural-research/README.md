# Nexural Research (NinjaTrader Strategy Analysis)

A local, Python-based research environment to **import, analyze, compare, and iterate** on NinjaTrader strategy results.

This workspace is designed for:
- ingesting **NinjaTrader CSV trade exports**
- diagnosing long vs short behavior
- time-of-day/day-of-week breakdowns
- exit type and trade duration analysis
- comparing parameter sets and strategy versions
- producing charts/reports you can re-run consistently

## Safety note
This tooling is for **research and simulation-first development**.
Trading futures and using automation is risky. You are responsible for your own validation and live execution.

---

## CLI

You can ingest **either** NinjaTrader export type (Trades or Executions). The CLI auto-detects which one you provided.

`ash
python -m pip install -e .

# Trades export
nexural-research ingest --input data/exports/sample_trades.csv --output data/processed/trades.parquet

# Executions export
nexural-research ingest --input data/exports/sample_executions.csv --output data/processed/executions.parquet
`

If --input is omitted, it defaults to data/exports/sample_trades.csv.

## Project structure
- `data/raw/` — untouched CSV exports (ignored by git)
- `data/processed/` — cleaned parquet outputs (ignored by git)
- `data/exports/` — a convenient “drop folder” for new exports (ignored by git)
- `configs/` — YAML configs for runs and parameter sets
- `experiments/` — run registry + comparisons
- `reports/` — generated charts and summaries
- `src/` — the actual library code
- `notebooks/` — starter notebooks (analysis entry points)

---

## VS Code setup (recommended)

### 1) Create a virtual environment
From a terminal in this folder:

```bash
python -m venv .venv
```

Activate:
- **Windows PowerShell**:
  ```powershell
  .\\.venv\\Scripts\\Activate.ps1
  ```
- **Windows cmd**:
  ```bat
  .\\.venv\\Scripts\\activate.bat
  ```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Select interpreter in VS Code
`Ctrl+Shift+P` → **Python: Select Interpreter** → choose `.venv`.

### 4) Run notebooks
Start with:
- `notebooks/import_and_clean_trade_log.ipynb`

---

## Typical workflow
1. Export trades from NinjaTrader (Backtest or Strategy Analyzer).
2. Drop the CSV into `data/exports/`.
3. Run the import notebook to normalize + save parquet.
4. Run analysis notebooks to find weak regimes (shorts, time-of-day, exit types).
5. Record the run in the experiment registry with strategy version + parameters.
6. Compare runs and iterate.

---

## First 3 things to export from NinjaTrader
1. **Trade export (this CSV)** — trades with entry/exit, PnL, MAE/MFE.
2. **Strategy parameters** for the run (export or copy/paste into YAML).
3. **Performance summary** (if available) to cross-check totals and assumptions.

---

## Next steps
Once the baseline workflow is solid, we can add:
- automated cataloging of exports
- file watching (`watchdog`) to auto-import new CSVs
- a FastAPI service for local dashboards
- Discord/webhook notifications (optional)
