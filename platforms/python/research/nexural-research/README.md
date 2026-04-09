# Nexural Research v2.0

**Institutional-grade strategy analysis engine for NinjaTrader traders and quant desks.**

Upload your NinjaTrader trade logs. Get 71+ institutional metrics, Monte Carlo simulations, stress testing, overfitting detection, parameter sweep optimization, and AI-powered analysis with response validation — all running locally on your machine.

**470 tests | 93% coverage | 58 API endpoints | 71+ metrics | 3 AI providers**

---

## Quick Start

```bash
# Clone
git clone https://github.com/JasonTeixeira/Nexural_Automation.git
cd Nexural_Automation/platforms/python/research/nexural-research

# Install
pip install -e "."

# Run backend
python -m uvicorn nexural_research.api.app:app --port 8000

# Run frontend (separate terminal)
cd frontend-v0
npm install
npm run dev
```

Open **http://localhost:3000** — upload a NinjaTrader CSV and start analyzing.

**API docs:** http://localhost:8000/api/docs

---

## What You Get

### 71+ Metrics Across 14 Analysis Modules

| Category | Metrics |
|----------|---------|
| **Core** | Net profit, win rate, profit factor, max drawdown, Ulcer Index |
| **Risk-Adjusted** | Sharpe, Sortino, Calmar, Omega, MAR, Tail ratio, Gain-to-Pain, Risk of Ruin |
| **Expectancy** | Kelly Criterion, Half-Kelly, Optimal f (Ralph Vince), payoff ratio, edge ratio |
| **Trade Dependency** | Z-score runs test, serial correlation, streak analysis |
| **Distribution** | Skewness, kurtosis, Jarque-Bera, VaR 95%, CVaR/Expected Shortfall |
| **Institutional** | Recovery factor, time under water %, profit/day, trade frequency, DD duration |
| **Desk Analytics** | Hurst exponent, ACF (20 lags), rolling correlation, Information Ratio |
| **Time Decay** | Rolling Sharpe regression for edge degradation detection |

### Robustness Testing

- **Parametric Monte Carlo** — Empirical, normal, or Student's t (up to 100K sims)
- **Block Bootstrap** — Preserves autocorrelation (Politis & Romano cube-root)
- **Rolling Walk-Forward** — Multi-window IS/OOS with efficiency tracking
- **Deflated Sharpe Ratio** — Bailey & Lopez de Prado (2014) overfitting detection
- **Regime Analysis** — Volatility regime detection with per-regime performance

### Stress Testing

- **Tail Amplification** — What if your worst trades were 2-3x worse?
- **Historical Stress** — Worst 5/10/20/50 trade stretches
- **Parameter Sensitivity** — 3D grid (stop × target × size) with robustness score and overfitting detection

### AI Strategy Analyst (BYOK — Bring Your Own Key)

- **Claude** (Anthropic), **GPT-4o** (OpenAI), **Perplexity** (Sonar Pro)
- Full 71-metric context sent to AI — not just charts, real data
- **Multi-turn conversation** with persistent strategy context
- **Response validation** — AI claims cross-referenced against actual metrics with confidence score
- **Context preview** — see exactly what the AI sees before you ask

### Strategy Comparison

- **Upload 2-10 CSVs** — ranked comparison matrix
- Composite weighted scoring (Sharpe 25%, Sortino 15%, PF 15%, etc.)
- Per-metric winners, best overall / risk-adjusted / most robust
- Side-by-side delta tables with % change

### Parameter Sweep Automation

- Define stop/target/size ranges, run all combinations
- Ranked by composite score (Sharpe + PF + win rate + Calmar)
- Automatic overfitting detection (boundary optima, scattered results)
- Stability score (0-100)

### Exports

- **JSON** — All metrics in one payload
- **CSV** — Raw or filtered trades
- **Excel** — Multi-sheet workbook (Summary, Trades, Metrics, Recommendations, Equity Curve)
- **PDF Report** — 2-page executive summary with grade, metrics grid, stress tests, recommendations
- **HTML Report** — Full interactive report

### Strategy Improvement Engine

- **Letter grade** (A through F) with explanation
- **Actionable recommendations** — time filters, position sizing, stop-loss placement
- **Drawdown recovery analysis** — periods, depth, recovery time
- **Loss cluster detection** — consecutive losing streaks
- **MAE/MFE efficiency** — entry/exit quality with data-driven stop suggestions

---

## Architecture

```
nexural-research/
├── src/nexural_research/
│   ├── analyze/           14 analysis modules (8,400+ lines)
│   │   ├── advanced_metrics.py      Sharpe, Sortino, Kelly, 61+ metrics
│   │   ├── advanced_analytics.py    Hurst, ACF, rolling correlation, IR
│   │   ├── advanced_robustness.py   MC, bootstrap, walk-forward, DSR
│   │   ├── stress_testing.py        Tail amplification, sensitivity
│   │   ├── parameter_sweep.py       3D optimization with overfitting
│   │   ├── comparison.py            Multi-strategy ranked matrix
│   │   ├── improvements.py          Grade engine + recommendations
│   │   └── ...
│   ├── api/               Router-based FastAPI (58 endpoints)
│   │   ├── app.py                   Slim factory with lifespan
│   │   ├── routers/                 7 focused routers
│   │   ├── middleware/              Rate limiter, request ID, metrics, security headers
│   │   ├── auth.py                  API key auth (SHA-256)
│   │   ├── cache.py                 LRU with TTL
│   │   ├── ai_validator.py          Cross-reference AI claims vs data
│   │   └── sessions.py             Persistent sessions (Parquet)
│   ├── db/                SQLAlchemy models (SQLite/PostgreSQL)
│   ├── export/            Excel + PDF report generators
│   └── ingest/            NinjaTrader CSV parser (50+ column aliases)
├── frontend-v0/           Next.js 16 dashboard (20+ pages)
├── tests/                 470 tests at 93% coverage
├── k8s/                   Kubernetes manifests
├── OPERATIONS.md          Operations runbook
├── DATA_DICTIONARY.md     Every metric explained
└── docker-compose.yml     App + PostgreSQL + Redis
```

---

## API (58 Endpoints)

Interactive docs at **http://localhost:8000/api/docs**

| Category | Endpoints | Examples |
|----------|-----------|---------|
| **Analysis** | 17 | `/api/analysis/metrics`, `/api/analysis/comprehensive`, `/api/analysis/hurst` |
| **Robustness** | 7 | `/api/robustness/parametric-monte-carlo`, `/api/robustness/deflated-sharpe` |
| **Stress Testing** | 3 | `/api/stress/tail-amplification`, `/api/stress/sensitivity` |
| **Charts** | 6 | `/api/charts/equity`, `/api/charts/heatmap`, `/api/charts/rolling-metrics` |
| **Export** | 7 | `/api/export/json`, `/api/export/excel`, `/api/export/pdf-report` |
| **AI** | 4 | `/api/ai/analyze`, `/api/ai/conversation`, `/api/ai/validate` |
| **Sessions** | 3 | `/api/upload`, `/api/sessions`, `/api/compare/matrix` |
| **Health** | 6 | `/api/health`, `/api/health/ready`, `/api/health/deep`, `/metrics` |

All endpoints also available at `/api/v1/` prefix.

---

## Configuration (Environment Variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXURAL_AUTH_ENABLED` | `false` | Enable API key authentication |
| `NEXURAL_API_KEYS` | (empty) | Comma-separated valid API keys |
| `NEXURAL_RATE_LIMIT` | `600` | Requests per minute per IP |
| `NEXURAL_MAX_UPLOAD_MB` | `100` | Maximum CSV upload size |
| `NEXURAL_MAX_SESSIONS` | `1000` | Maximum concurrent sessions |
| `NEXURAL_SESSION_TTL_HOURS` | `24` | Auto-expire sessions after N hours |
| `NEXURAL_DATABASE_URL` | `sqlite:///data/nexural.db` | Database (SQLite or PostgreSQL) |
| `NEXURAL_REDIS_URL` | (empty) | Redis for shared sessions |
| `NEXURAL_CORS_ORIGINS` | `localhost:*` | Allowed CORS origins |

---

## Testing

```bash
# Backend tests (470)
pytest tests/ --ignore=tests/e2e

# E2E browser tests (26) — requires both servers running
pytest tests/e2e/

# With coverage
pytest tests/ --cov=nexural_research

# Tab-by-tab API audit
python tests/audit_tabs.py

# Load testing
pip install locust
locust -f tests/load/locustfile.py --headless -u 50 -r 10 --run-time 60s --host http://localhost:8000
```

---

## Docker

```bash
# Full stack (app + PostgreSQL + Redis)
docker compose up -d

# Development mode
docker compose --profile dev up
```

---

## Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml
```

Includes: Deployment (3 replicas), Service, HPA (2-10 pods), PVC (50Gi).

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `pytest tests/`
4. Submit a pull request

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

---

## Documentation

- **[OPERATIONS.md](OPERATIONS.md)** — Deployment, monitoring, alerting, incident response
- **[DATA_DICTIONARY.md](DATA_DICTIONARY.md)** — Every metric explained with formulas
- **[V0_FRONTEND_BLUEPRINT.md](V0_FRONTEND_BLUEPRINT.md)** — Frontend specification

---

## License

MIT — see [LICENSE](../../LICENSE)

---

## Disclaimer

This software is for research and educational purposes only. It analyzes historical trade data and does not execute trades, provide financial advice, or guarantee future performance. Past performance does not guarantee future results. All trading involves risk of loss.
