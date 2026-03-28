# Nexural Research (NinjaTrader Strategy Analysis)

A local, Python-based research environment to **import, analyze, compare, and iterate** on NinjaTrader strategy results.

## What it supports (v0.2)
- Ingest NinjaTrader CSV exports:
  - Strategy Analyzer **Trades** export
  - **Executions** export
  - **Optimization results** export (best-effort loader; formats vary)
- Generate a professional, single-file **HTML report** from Trades exports:
  - equity curve + drawdown
  - PnL heatmap by day-of-week x hour
  - by-strategy and by-instrument breakdown
- Local run registry (DuckDB) to track run artifacts and metrics

## What it supports (v0.3)
- Stores **full normalized datasets** into DuckDB for each run:
  - `trades`, `executions`, `optimizations`
- Adds **execution quality** analytics (Executions export)
- Adds **robustness** scaffolding (Trades export)
  - Monte Carlo max drawdown distribution (shuffle trade sequence)
  - Simple walk-forward split (chronological)

## CLI

You can ingest NinjaTrader export types (Trades / Executions / Optimization). The CLI auto-detects which one you provided.

```bash
python -m pip install -e .

# Optional: install the full research stack (not required for the baseline report)
python -m pip install -r requirements.txt

# Reproducible dev/test install (pinned) with pip-tools
python -m pip install pip-tools
pip-sync requirements-dev.lock.txt
python -m pip install -e .

# Trades export
nexural-research ingest --input data/exports/sample_trades.csv --output data/processed/trades.parquet

# Executions export
nexural-research ingest --input data/exports/sample_executions.csv --output data/processed/executions.parquet

# Optimization results export
nexural-research ingest --input data/exports/sample_optimization.csv --output data/processed/optimization.parquet
```

If `--input` is omitted, it defaults to `data/exports/sample_trades.csv`.

### Generate a report

```bash
nexural-research report --input data/exports/sample_trades.csv
```

This will print a path like:
`reports/report_YYYYMMDD_HHMMSS/report.html`

### Run registry

Runs are stored in:
- `experiments/runs.duckdb`

List runs:

```bash
nexural-research runs --limit 20
```

Compare two runs (trade metrics):

```bash
nexural-research compare --run-a trades_YYYYMMDD_HHMMSS --run-b report_YYYYMMDD_HHMMSS
```

### Execution quality (Executions export)

```bash
nexural-research execq --input data/exports/sample_executions.csv
```

### Robustness (Trades export)

```bash
nexural-research robust --input data/exports/sample_trades.csv --mc-n 2000 --seed 7 --split 0.7
```
