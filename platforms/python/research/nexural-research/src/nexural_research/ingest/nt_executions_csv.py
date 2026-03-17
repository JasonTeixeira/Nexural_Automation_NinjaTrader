from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from nexural_research.ingest.nt_csv import parse_money
from nexural_research.utils.logging import info


def _normalize_cols(cols: list[str]) -> list[str]:
    out: list[str] = []
    for c in cols:
        c2 = c.strip().lower()
        c2 = c2.replace(".", "")
        c2 = c2.replace(" ", "_")
        c2 = c2.replace("-", "_")
        out.append(c2)
    return out


def load_nt_executions_csv(path: str | Path) -> pd.DataFrame:
    """Load a NinjaTrader *Executions* export CSV.

    This is a separate file type from the Strategy Analyzer *Trades* export.
    Executions are per-fill events.
    """

    p = Path(path)
    info(f"Loading NinjaTrader Executions CSV: {p}")

    df = pd.read_csv(p)
    df.columns = _normalize_cols(list(df.columns))

    # Normalize time
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")

    # Normalize money-like columns (if present)
    for col in ("commission", "profit"):
        if col in df.columns:
            df[col] = df[col].map(parse_money)

    # Normalize numeric prices
    for col in ("limit_price", "stop_price", "fill_price"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Normalize quantity
    for col in ("quantity", "qty"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Some exports use Market position, some use Market pos.
    if "market_position" in df.columns:
        df["market_position"] = df["market_position"].astype(str).str.strip().str.title()

    return df


def is_likely_executions_export(df: pd.DataFrame) -> bool:
    cols = set(_normalize_cols(list(df.columns)))
    return {"time", "action", "fill_price"}.issubset(cols)
