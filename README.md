# Nexural Trading Systems (Order Flow Templates + Examples)

[![docs-and-metadata](https://github.com/JasonTeixeira/Nexural_Automation/actions/workflows/docs-and-metadata.yml/badge.svg)](https://github.com/JasonTeixeira/Nexural_Automation/actions/workflows/docs-and-metadata.yml)
[![module-catalog](https://github.com/JasonTeixeira/Nexural_Automation/actions/workflows/module-catalog.yml/badge.svg)](https://github.com/JasonTeixeira/Nexural_Automation/actions/workflows/module-catalog.yml)
[![python-research-ci](https://github.com/JasonTeixeira/Nexural_Automation/actions/workflows/python-research-ci.yml/badge.svg)](https://github.com/JasonTeixeira/Nexural_Automation/actions/workflows/python-research-ci.yml)

A practical, open-source monorepo for:
- **NinjaTrader 8** strategies and indicators (primary)
- **TradingView Pine Script v5** indicators and strategies (secondary)
- shared **order flow** research notes, validation checklists, and reusable templates
- **Python** research/analytics tooling for NinjaTrader exports

> This project is for **research, education, and simulation-first development**. It is not a signal service.

---

## Quick safety note (please read)
- **Not financial advice.**
- **No guarantees.** Nothing here is guaranteed profitable.
- Futures and leveraged trading can result in **substantial losses**.
- If you use any code from this repo, you are responsible for **validation, simulation, configuration, risk controls, and compliance**.

Full disclaimer: **[DISCLAIMER.md](DISCLAIMER.md)**.

---

## What you’ll find here

### Templates (recommended starting point)
- `templates/strategy-template/`
- `templates/indicator-template/`

Each module template includes:
- `metadata.yaml`
- `README.md` (logic + assumptions + failure modes)
- `parameters.md`
- `notes.md`
- `changelog.md`
- `src/`, `screenshots/`, `test-results/`

### Example modules
- NinjaTrader strategy example: `platforms/ninjatrader/Strategies/AbsorptionReversal/`
- TradingView indicator example: `platforms/tradingview/indicators/VWAPReversion/`

---

## Supported platforms
- **NinjaTrader 8** (NinjaScript/C#) — primary focus
- **TradingView** (Pine Script v5)
- **Python** (research tooling included)

See: **[docs/supported-platforms.md](docs/supported-platforms.md)**

---

## Core principles
- **Simulation-first**: treat live trading as a separate, high-risk deployment step.
- **Clarity over cleverness**: readable code + documented assumptions.
- **Reproducibility**: parameter tables, test notes, and data assumptions.
- **No hype**: no marketing language and no performance claims.

---

## Repo layout (where to look)
- `docs/` — architecture, installation, conventions, safety policies
- `platforms/` — platform-specific modules
- `templates/` — standardized module templates
- `configs/` — example presets (markets/sessions/risk)
- `tests-notes/` — validation and sim checklists
- `.github/` — issue templates, PR template, CI

---

## Quick start

### Python research (recommended)

```powershell
./scripts/setup.ps1
```

See: **[GETTING_STARTED.md](GETTING_STARTED.md)**

### NinjaTrader users
1. Browse `platforms/ninjatrader/`.
2. Start from a template: copy `templates/strategy-template/` into `platforms/ninjatrader/Strategies/<StrategyName>/`.
3. Fill out the docs first (`metadata.yaml`, `README.md`, `parameters.md`).
4. Add NinjaScript code under `src/`.

### TradingView users
1. Browse `platforms/tradingview/`.
2. For indicators, start from `templates/indicator-template/` and place your `.pine` under `src/`.

### Contributors
- Read **[CONTRIBUTING.md](CONTRIBUTING.md)**
- Then read: **[docs/contribution-workflow.md](docs/contribution-workflow.md)**

---

## Roadmap
See **[ROADMAP.md](ROADMAP.md)**.

Current status: early scaffold with templates + examples. The next focus is adding well-documented NinjaTrader order-flow modules.

---

## Start here (recommended reading order)
1. `DISCLAIMER.md`
2. `docs/architecture.md`
3. `docs/naming-conventions.md`
4. `templates/strategy-template/README.md`
5. `CONTRIBUTING.md`
