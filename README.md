# Nexural Automation — NinjaTrader Strategy Analysis & Development

[![CI](https://github.com/JasonTeixeira/Nexural_Automation/actions/workflows/ci.yml/badge.svg)](https://github.com/JasonTeixeira/Nexural_Automation/actions/workflows/ci.yml)
[![python-research-ci](https://github.com/JasonTeixeira/Nexural_Automation/actions/workflows/python-research-ci.yml/badge.svg)](https://github.com/JasonTeixeira/Nexural_Automation/actions/workflows/python-research-ci.yml)
[![docs-and-metadata](https://github.com/JasonTeixeira/Nexural_Automation/actions/workflows/docs-and-metadata.yml/badge.svg)](https://github.com/JasonTeixeira/Nexural_Automation/actions/workflows/docs-and-metadata.yml)
[![module-catalog](https://github.com/JasonTeixeira/Nexural_Automation/actions/workflows/module-catalog.yml/badge.svg)](https://github.com/JasonTeixeira/Nexural_Automation/actions/workflows/module-catalog.yml)

An open-source toolkit for NinjaTrader automation developers. Import your trade logs, get **50+ institutional-grade metrics**, **Monte Carlo simulations**, **overfitting detection**, **AI-powered strategy recommendations**, and **actionable improvement suggestions** — all from a professional desktop application running on your local machine.

> **Not financial advice.** This project is for research, education, and simulation-first development. See [DISCLAIMER.md](DISCLAIMER.md).

---

## Nexural Research — Strategy Analysis Dashboard

The flagship tool in this repo. A complete strategy analysis engine with a professional web dashboard.

### Install and Run (3 commands)

**Windows:**
```bat
git clone https://github.com/JasonTeixeira/Nexural_Automation.git
cd Nexural_Automation\platforms\python\research\nexural-research
install.bat
```
Then double-click **"Nexural Research"** on your Desktop.

**macOS / Linux:**
```bash
git clone https://github.com/JasonTeixeira/Nexural_Automation.git
cd Nexural_Automation/platforms/python/research/nexural-research
chmod +x install.sh && ./install.sh
./nexural-research
```

**Docker:**
```bash
cd platforms/python/research/nexural-research
docker compose up --build
# Open http://localhost:8000
```

**Requirements:** Python 3.11+ ([download](https://python.org/downloads)). Node.js is NOT required — the frontend comes pre-built.

### How to Use

1. **Export trades** from NinjaTrader Strategy Analyzer (File > Save as CSV)
2. **Launch the app** — it opens in your browser at `http://localhost:8000`
3. **Drag & drop** your CSV into the upload zone (auto-detects any NinjaTrader format)
4. **Explore the dashboard** — 10 analysis tabs with full institutional metrics
5. **Export results** — download filtered CSV, JSON metrics, or HTML report
6. **Ask the AI** — connect your Claude / GPT-4o / Perplexity key for strategy analysis

### What You Get

| Tab | What It Does |
|-----|-------------|
| **Overview** | Net profit, win rate, Sharpe, Sortino, Calmar, Kelly %, equity curve, drawdown, per-trade PnL |
| **Improvements** | Letter grade (A-F), actionable recommendations, time filter suggestions, loss cluster detection, MAE/MFE efficiency |
| **Advanced Metrics** | Trade dependency (Z-score), edge stability, Deflated Sharpe Ratio (overfitting), benchmark vs random, regime analysis |
| **Robustness** | Shuffle MC, parametric MC (3 distributions), block bootstrap, rolling walk-forward with bar charts |
| **Distribution** | Skewness, kurtosis, VaR 95%, CVaR, Jarque-Bera normality, PnL histogram |
| **Heatmap** | Day-of-week x hour PnL heatmap — find your best and worst trading times |
| **Trades** | Full searchable trade log |
| **Compare** | Upload 2 CSVs side-by-side, see delta for every metric |
| **AI Analyst** | Claude / GPT-4o / Perplexity with full strategy context (bring your own key) |
| **Settings** | API key configuration, provider selection |

### CSV Compatibility

Works with any NinjaTrader export format. Auto-detects 50+ column name variations:

| Your Column | Recognized As |
|------------|---------------|
| `net_pnl`, `pnl`, `realized_pnl`, `profit_loss` | `profit` |
| `symbol`, `ticker`, `contract` | `instrument` |
| `side`, `direction`, `buy_sell` | `market_pos` |
| `trade_id`, `trade_num` | `trade_number` |
| `qty`, `size`, `contracts` | `quantity` |

### API

When running, interactive API docs are at **http://localhost:8000/api/docs** with 26+ endpoints.

Full documentation: **[platforms/python/research/nexural-research/README.md](platforms/python/research/nexural-research/README.md)**

---

## What Else Is in This Repo

### NinjaTrader Modules
- Strategy and indicator templates with full documentation standards
- Example: `platforms/ninjatrader/Strategies/AbsorptionReversal/`

### TradingView Modules
- Pine Script v5 indicator templates
- Example: `platforms/tradingview/indicators/VWAPReversion/`

### Templates (start here for new modules)
- `templates/strategy-template/` — full strategy scaffold with docs
- `templates/indicator-template/` — full indicator scaffold with docs

---

## Quick Safety Note

- **Not financial advice.** Nothing here is guaranteed profitable.
- Futures and leveraged trading can result in **substantial losses**.
- You are responsible for validation, simulation, risk controls, and compliance.
- Full disclaimer: **[DISCLAIMER.md](DISCLAIMER.md)**

---

## Core Principles

- **Simulation-first**: treat live trading as a separate, high-risk deployment step
- **Clarity over cleverness**: readable code + documented assumptions
- **Reproducibility**: parameter tables, test notes, and data assumptions
- **No hype**: no marketing language and no performance claims

---

## Repo Layout

```
Nexural_Automation/
├── platforms/
│   ├── ninjatrader/         # NinjaScript strategies & indicators
│   ├── tradingview/         # Pine Script v5 modules
│   └── python/research/
│       └── nexural-research/   # <-- THE ANALYSIS DASHBOARD
│           ├── src/             # Python analysis engine (50+ metrics)
│           ├── frontend/        # React dashboard (pre-built)
│           ├── desktop/         # Electron wrapper
│           ├── tests/           # 97 tests
│           ├── install.bat      # Windows one-click install
│           ├── install.sh       # Mac/Linux install
│           └── launch.bat       # Windows launcher
├── templates/               # Strategy & indicator templates
├── docs/                    # Architecture, policies, guides
└── .github/workflows/       # CI: pytest + ruff + TypeScript
```

---

## Contributing

1. Read **[CONTRIBUTING.md](CONTRIBUTING.md)**
2. Fork, branch, code, test (`pytest`), submit PR
3. CI runs automatically — all checks must pass

---

## Roadmap

See **[ROADMAP.md](ROADMAP.md)**

---

## License

MIT — see **[LICENSE](LICENSE)**
