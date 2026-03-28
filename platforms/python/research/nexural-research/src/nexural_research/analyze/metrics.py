from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from nexural_research.analyze.equity import equity_curve_from_trades, max_drawdown, ulcer_index


@dataclass(frozen=True)
class TradeMetrics:
    n_trades: int
    gross_profit: float
    gross_loss: float
    net_profit: float
    win_rate: float
    profit_factor: float
    avg_trade: float
    avg_win: float
    avg_loss: float
    max_drawdown: float
    ulcer_index: float


def _safe_div(n: float, d: float) -> float:
    if d == 0:
        return 0.0
    return float(n / d)


def metrics_from_trades(df_trades: pd.DataFrame) -> TradeMetrics:
    """Compute baseline metrics from a trades dataframe.

    Expected columns:
    - profit (currency)

    Optional columns:
    - mae / mfe / etd (for deeper stats; not used yet in baseline metrics)
    """

    if "profit" not in df_trades.columns:
        raise ValueError("trades dataframe missing required column: profit")

    pnl = pd.to_numeric(df_trades["profit"], errors="coerce").fillna(0.0)
    n = int(len(pnl))
    net = float(pnl.sum())
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gross_profit = float(wins.sum())
    gross_loss = float(-losses.sum())

    win_rate = _safe_div(float((pnl > 0).sum()), float(n)) if n else 0.0
    profit_factor = _safe_div(gross_profit, gross_loss) if gross_loss else (float("inf") if gross_profit > 0 else 0.0)
    avg_trade = _safe_div(net, float(n)) if n else 0.0
    avg_win = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(losses.mean()) if len(losses) else 0.0

    eq = equity_curve_from_trades(df_trades)
    mdd = max_drawdown(eq.equity)
    ui = ulcer_index(eq.equity)

    return TradeMetrics(
        n_trades=n,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        net_profit=net,
        win_rate=float(win_rate),
        profit_factor=float(profit_factor) if np.isfinite(profit_factor) else float("inf"),
        avg_trade=float(avg_trade),
        avg_win=float(avg_win),
        avg_loss=float(avg_loss),
        max_drawdown=float(mdd),
        ulcer_index=float(ui),
    )


def metrics_by(df_trades: pd.DataFrame, by: str) -> pd.DataFrame:
    """Group metrics by a column (e.g. strategy, instrument)."""

    if by not in df_trades.columns:
        raise ValueError(f"missing column for grouping: {by}")

    rows: list[dict[str, Any]] = []
    for key, g in df_trades.groupby(by, dropna=False):
        m = metrics_from_trades(g)
        d = asdict(m)
        d[by] = str(key)
        rows.append(d)
    out = pd.DataFrame(rows)
    # nice ordering
    if "net_profit" in out.columns:
        out = out.sort_values("net_profit", ascending=False)
    return out
