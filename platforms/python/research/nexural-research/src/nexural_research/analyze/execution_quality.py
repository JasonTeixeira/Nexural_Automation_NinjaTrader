from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ExecutionQualityMetrics:
    n_exec: int
    commission_sum: float
    profit_sum: float
    n_market: int
    n_limit: int
    n_stop: int
    slippage_mean: float
    slippage_std: float


def _norm(s: Any) -> str:
    return str(s).strip().lower()


def execution_quality_from_executions(df_exec: pd.DataFrame) -> ExecutionQualityMetrics:
    """Compute baseline execution-quality metrics from an executions export.

    Uses simple heuristics:
    - order type classification via `type` column
    - slippage computed where we have a reference price:
      - Limit: fill_price - limit_price
      - Stop: fill_price - stop_price
      - Market: slippage unknown (ignored)
    """

    if "fill_price" not in df_exec.columns:
        raise ValueError("executions dataframe missing required column: fill_price")

    df = df_exec.copy()

    comm = pd.to_numeric(df.get("commission", 0.0), errors="coerce").fillna(0.0)
    prof = pd.to_numeric(df.get("profit", 0.0), errors="coerce").fillna(0.0)
    n_exec = int(len(df))

    types = df.get("type")
    if types is None:
        types = pd.Series([""] * n_exec)
    types_norm = types.map(_norm)
    n_market = int((types_norm == "market").sum())
    n_limit = int((types_norm == "limit").sum())
    n_stop = int((types_norm == "stop").sum())

    fill = pd.to_numeric(df["fill_price"], errors="coerce")
    limit_price = pd.to_numeric(df.get("limit_price"), errors="coerce") if "limit_price" in df.columns else None
    stop_price = pd.to_numeric(df.get("stop_price"), errors="coerce") if "stop_price" in df.columns else None

    slips: list[float] = []
    if limit_price is not None:
        mask = (types_norm == "limit") & limit_price.notna() & fill.notna()
        slips.extend((fill[mask] - limit_price[mask]).astype(float).tolist())
    if stop_price is not None:
        mask = (types_norm == "stop") & stop_price.notna() & fill.notna()
        slips.extend((fill[mask] - stop_price[mask]).astype(float).tolist())

    if slips:
        sl_mean = float(np.mean(slips))
        sl_std = float(np.std(slips))
    else:
        sl_mean = 0.0
        sl_std = 0.0

    return ExecutionQualityMetrics(
        n_exec=n_exec,
        commission_sum=float(comm.sum()),
        profit_sum=float(prof.sum()),
        n_market=n_market,
        n_limit=n_limit,
        n_stop=n_stop,
        slippage_mean=sl_mean,
        slippage_std=sl_std,
    )


def execution_quality_by(df_exec: pd.DataFrame, by: str) -> pd.DataFrame:
    """Group execution-quality metrics by a column (e.g. strategy, instrument, account)."""

    if by not in df_exec.columns:
        raise ValueError(f"missing column for grouping: {by}")

    rows: list[dict[str, Any]] = []
    for key, g in df_exec.groupby(by, dropna=False):
        m = execution_quality_from_executions(g)
        d = asdict(m)
        d[by] = str(key)
        rows.append(d)
    out = pd.DataFrame(rows)
    if "profit_sum" in out.columns:
        out = out.sort_values("profit_sum", ascending=False)
    return out
