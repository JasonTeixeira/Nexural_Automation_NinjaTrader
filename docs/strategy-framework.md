# Strategy Framework Philosophy

## Principles
- **Order flow context first** (liquidity, absorption, imbalance, initiative vs. responsive flows).
- **Risk model is part of the strategy** (position sizing, max loss, session rules).
- **Simulation-first workflow**.
- **Reproducibility over hype**.

## What we require in every strategy README
- intent + setup conditions
- entries/exits in plain language
- parameter definitions and units
- failure modes / when not to trade
- instrument/session assumptions
- test notes (data range, sim environment)

## Backtesting limitations
Order flow signals are sensitive to:
- data vendor differences
- replay/sim fill assumptions
- market microstructure changes

See `docs/backtesting-policy.md`.
