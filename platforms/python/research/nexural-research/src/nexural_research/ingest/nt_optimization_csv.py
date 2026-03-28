from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from nexural_research.utils.logging import info


def _normalize_cols(cols: list[str]) -> list[str]:
    out: list[str] = []
    for c in cols:
        c2 = str(c).strip().lower()
        c2 = c2.replace(".", "")
        c2 = c2.replace(" ", "_")
        c2 = c2.replace("-", "_")
        out.append(c2)
    return out


_NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")


def _to_float(x: Any) -> float | None:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip()
    if not s:
        return None
    s = s.replace("$", "").replace(",", "").replace("%", "")
    if not _NUM_RE.match(s):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_nt_optimization_csv(path: str | Path) -> pd.DataFrame:
    """Load NinjaTrader Strategy Analyzer *Optimization* results export.

    NinjaTrader optimization exports can vary by version and settings.
    This loader uses best-effort normalization:
    - column names normalized
    - common metric columns coerced to numeric
    - parameter columns are left as-is for now
    """

    p = Path(path)
    info(f"Loading NinjaTrader Optimization CSV: {p}")

    df = pd.read_csv(p)
    df.columns = _normalize_cols(list(df.columns))

    # Coerce common metrics if present.
    metric_cols = [
        "total_net_profit",
        "net_profit",
        "profit_factor",
        "max_drawdown",
        "max_drawdown_percent",
        "sharpe",
        "sortino",
        "ulcer_index",
        "trades",
        "win_rate",
        "percent_profitable",
        "avg_trade",
        "average_trade",
    ]
    for c in metric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].map(_to_float), errors="coerce")

    return df
