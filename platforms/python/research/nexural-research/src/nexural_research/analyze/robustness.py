from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from nexural_research.analyze.equity import max_drawdown


@dataclass(frozen=True)
class MonteCarloDrawdownSummary:
    n: int
    mdd_p05: float
    mdd_p25: float
    mdd_p50: float
    mdd_p75: float
    mdd_p95: float


def monte_carlo_max_drawdown(
    df_trades: pd.DataFrame,
    *,
    n: int = 1000,
    seed: int = 42,
    profit_col: str = "profit",
) -> MonteCarloDrawdownSummary:
    """Monte Carlo resampling of trade sequence.

    This shuffles the trade PnL sequence and computes max drawdown.
    Net profit is invariant, but drawdown characteristics vary with ordering.
    """

    pnl = pd.to_numeric(df_trades.get(profit_col), errors="coerce").fillna(0.0).to_numpy()
    if pnl.size == 0:
        return MonteCarloDrawdownSummary(n=0, mdd_p05=0.0, mdd_p25=0.0, mdd_p50=0.0, mdd_p75=0.0, mdd_p95=0.0)

    rng = np.random.default_rng(int(seed))
    mdds = np.zeros(int(n), dtype=float)
    for i in range(int(n)):
        shuffled = rng.permutation(pnl)
        eq = pd.Series(shuffled).cumsum()
        mdds[i] = max_drawdown(eq)

    qs = np.quantile(mdds, [0.05, 0.25, 0.50, 0.75, 0.95])
    return MonteCarloDrawdownSummary(
        n=int(n),
        mdd_p05=float(qs[0]),
        mdd_p25=float(qs[1]),
        mdd_p50=float(qs[2]),
        mdd_p75=float(qs[3]),
        mdd_p95=float(qs[4]),
    )


@dataclass(frozen=True)
class WalkForwardSplitMetrics:
    split: float
    in_sample_n: int
    out_sample_n: int
    in_sample_net_profit: float
    out_sample_net_profit: float


def walk_forward_split(df_trades: pd.DataFrame, *, split: float = 0.7, ts_col: str = "exit_time") -> WalkForwardSplitMetrics:
    """Simple walk-forward scaffolding: chronological split and compare net PnL."""

    if ts_col not in df_trades.columns:
        ts_col = "entry_time" if "entry_time" in df_trades.columns else ts_col

    df = df_trades.copy()
    if ts_col in df.columns:
        df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
        df = df.dropna(subset=[ts_col]).sort_values(ts_col, kind="mergesort")

    n = len(df)
    k = int(max(0, min(n, round(n * float(split)))))
    df_in = df.iloc[:k]
    df_out = df.iloc[k:]

    pnl_in = float(pd.to_numeric(df_in.get("profit"), errors="coerce").fillna(0.0).sum())
    pnl_out = float(pd.to_numeric(df_out.get("profit"), errors="coerce").fillna(0.0).sum())

    return WalkForwardSplitMetrics(
        split=float(split),
        in_sample_n=int(len(df_in)),
        out_sample_n=int(len(df_out)),
        in_sample_net_profit=pnl_in,
        out_sample_net_profit=pnl_out,
    )
