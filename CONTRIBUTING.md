# Contributing to Nexural Trading Systems

Thanks for your interest in contributing.

This project aims to be a **professional, research-oriented monorepo** for order flow tools, automation templates, and multi-platform strategy development.

## Ground rules
1. **Simulation-first.** Do not submit code that implies “guaranteed profits” or encourages irresponsible live trading.
2. **No performance marketing.** No hype, no unverifiable claims, no screenshots implying income without context.
3. **Document assumptions.** Every module must include its intent, assumptions, and known failure modes.
4. **Keep it reusable.** Favor clarity and composability over cleverness.
5. **Respect licensing.** Only contribute code you have the right to share.

## What you can contribute
- NinjaTrader 8 strategies/indicators (NinjaScript/C#)
- TradingView Pine Script v5 indicators/strategies
- shared utilities (where platform allows)
- docs, research notes, checklists, and examples

## Module standard (required)
Every strategy/indicator module must be a folder containing:
- `src/` (source code)
- `README.md` (overview + logic summary + usage)
- `parameters.md` (parameter table with defaults/units)
- `notes.md` (research notes, regimes, limitations)
- `changelog.md`
- `metadata.yaml` (module metadata)
- `screenshots/` (optional)
- `test-results/` (optional)

Use the templates:
- `templates/strategy-template/`
- `templates/indicator-template/`

## How to submit a change
1. Fork the repo.
2. Create a feature branch:
   - `feature/<short-name>`
   - `fix/<short-name>`
   - `docs/<short-name>`
3. Make your changes.
4. Ensure docs and CI checks pass.
5. Open a PR and fill out the PR template.

## Contributor acknowledgement
By submitting a pull request, you agree that your contribution is licensed under the repository’s **Apache-2.0** license.

## Security
If you discover a security issue, see **SECURITY.md**.
