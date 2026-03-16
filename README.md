# Nexural Trading Systems Monorepo (Order Flow Automation)

**Status:** early-stage, community-ready scaffold (**templates + examples**) for order flow / futures automation.

## Read this first (Legal + Risk)
This repository is published openly for **educational and research purposes only**.

Trading futures, derivatives, and leveraged products involves **substantial risk of loss** and is not suitable for all investors. **You can lose more than your initial investment.**

**No Financial Advice / No Guarantees**
- Nothing in this repo constitutes financial, investment, legal, accounting, or tax advice.
- No strategy, indicator, template, or example in this repo is guaranteed to be profitable.

**Assumption of Risk / Responsibility**
By using any code or information in this repository, you agree that you are solely responsible for:
- validating logic,
- backtesting,
- simulation testing,
- live deployment,
- configuration, risk controls, broker/exchange settings, and operational monitoring.

**No Liability**
To the maximum extent permitted by law, **Jason Teixeira and Nexural** (and all contributors/maintainers) disclaim all liability for any losses, damages, claims, or costs arising from your use of this repository.

See **[DISCLAIMER.md](DISCLAIMER.md)** and **[LICENSE](LICENSE)**.

---

## What this repo is
A production-quality, contributor-friendly **monorepo** for:
- **NinjaTrader 8** strategy templates and examples (order flow / futures)
- **NinjaTrader 8** indicator templates and examples
- **TradingView Pine Script v5** indicator/strategy templates and examples
- Future expansion: **Python** research/analytics/backtesting tooling

## Repository layout (high level)
- **docs/**: architecture, installation, conventions, risk/backtesting policy
- **platforms/**: platform-specific code
  - **platforms/ninjatrader/**
  - **platforms/tradingview/**
  - **platforms/python/** (future-ready)
- **templates/**: standard module templates for strategies/indicators
- **examples/**: workflows, screenshots, sample configs
- **configs/**: market/session/risk presets and examples
- **scripts/**: repo tools (validation, release tooling)
- **tests-notes/**: validation checklists and known limitations
- **.github/**: issue templates, PR template, CI workflows

## Quickstart: add a new module
1) Copy a template folder:
   - `templates/strategy-template/` → `platforms/ninjatrader/Strategies/<StrategyName>/` (or TradingView)
   - `templates/indicator-template/` → `platforms/ninjatrader/Indicators/<IndicatorName>/` (or TradingView)
2) Fill in `metadata.yaml`, `README.md`, and `parameters.md`.
3) Add code to `src/`.
4) Add test notes and (optionally) screenshots.
5) Open a PR.

## Contributing
Read **[CONTRIBUTING.md](CONTRIBUTING.md)** and the workflow in **docs/contribution-workflow.md**.

## License
Apache-2.0. See **[LICENSE](LICENSE)**.
