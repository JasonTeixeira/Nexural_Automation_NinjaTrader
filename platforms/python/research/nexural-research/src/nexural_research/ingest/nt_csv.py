from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from nexural_research.utils.logging import info, warn


_PARENS_NEG = re.compile(r"^\((?P<num>[-+]?\d*\.?\d+)\)$")


def _parse_money(x: Any) -> float:
    """Parse NinjaTrader currency fields.

    Examples:
    - "$94.24" -> 94.24
    - "($65.76)" -> -65.76
    - "" / NaN -> 0.0
    """
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return 0.0
    s = str(x).strip()
    if not s:
        return 0.0
    s = s.replace("$", "").replace(",", "")
    m = _PARENS_NEG.match(s)
    if m:
        return -float(m.group("num"))
    try:
        return float(s)
    except ValueError:
        warn(f"Unable to parse money value: {x!r}; defaulting to 0")
        return 0.0


# Public API used by tests
def parse_money(x: Any) -> float:
    return _parse_money(x)


def _normalize_cols(cols: list[str]) -> list[str]:
    out: list[str] = []
    for c in cols:
        c2 = c.strip().lower()
        c2 = c2.replace(".", "")
        c2 = c2.replace(" ", "_")
        c2 = c2.replace("-", "_")
        out.append(c2)
    return out


def load_nt_trades_csv(path: str | Path) -> pd.DataFrame:
    """Load a NinjaTrader trade export CSV into a normalized DataFrame.

    This handles common NinjaTrader column names such as:
    - Trade number
    - Market pos.
    - Entry time / Exit time
    - Profit / Cum. net profit
    - MAE/MFE/ETD/Bars
    """
    p = Path(path)
    info(f"Loading NinjaTrader CSV: {p}")

    df = pd.read_csv(p)
    df.columns = _normalize_cols(list(df.columns))

    # Canonical column mapping
    rename = {
        "trade_number": "trade_number",
        "trade_number_": "trade_number",
        "trade_number__": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
        "trade_number": "trade_number",
    }

    # handle NinjaTrader specific names
    mapping = {
        "trade_number": "trade_number",
        "instrument": "instrument",
        "account": "account",
        "strategy": "strategy",
        "market_pos": "market_pos",
        "market_pos_": "market_pos",
        "market_pos": "market_pos",
        "market_pos__": "market_pos",
        "market_pos__": "market_pos",
        "market_pos_": "market_pos",
        "market_pos": "market_pos",
        "market_pos_": "market_pos",
        "market_pos": "market_pos",
        "market_pos_": "market_pos",
        "market_pos": "market_pos",
        "market_pos_": "market_pos",
        "market_pos": "market_pos",
        "market_pos_": "market_pos",
        "market_pos": "market_pos",
        "market_pos_": "market_pos",
        "market_pos": "market_pos",
        "market_pos_": "market_pos",
        "market_pos": "market_pos",
        "market_pos_": "market_pos",
        "market_pos": "market_pos",
        "market_pos_": "market_pos",
        "market_pos": "market_pos",
        "market_pos_": "market_pos",
        "market_pos": "market_pos",
        "market_pos_": "market_pos",
        "qty": "qty",
        "entry_price": "entry_price",
        "exit_price": "exit_price",
        "entry_time": "entry_time",
        "exit_time": "exit_time",
        "entry_name": "entry_name",
        "exit_name": "exit_name",
        "profit": "profit",
        "cum_net_profit": "cum_net_profit",
        "commission": "commission",
        "clearing_fee": "clearing_fee",
        "exchange_fee": "exchange_fee",
        "ip_fee": "ip_fee",
        "nfa_fee": "nfa_fee",
        "mae": "mae",
        "mfe": "mfe",
        "etd": "etd",
        "bars": "bars",
    }

    # Specific NinjaTrader export headers after normalization
    mapping.update(
        {
            "trade_number": "trade_number",
            "market_pos": "market_pos",
            "market_pos_": "market_pos",
            "market_pos__": "market_pos",
            "market_pos_": "market_pos",
            "market_pos": "market_pos",
            "market_pos_": "market_pos",
            "market_pos": "market_pos",
            "market_pos_": "market_pos",
            "market_pos": "market_pos",
            "market_pos_": "market_pos",
            "market_pos": "market_pos",
            "market_pos_": "market_pos",
        }
    )

    # NinjaTrader uses 'market_pos.' => normalized 'market_pos'
    # but sometimes comes through as 'market_pos_' depending on punctuation.
    if "market_pos" not in df.columns and "market_pos_" in df.columns:
        df = df.rename(columns={"market_pos_": "market_pos"})

    # Normalize time
    for col in ("entry_time", "exit_time"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Normalize money
    for col in ("profit", "cum_net_profit", "commission", "mae", "mfe", "etd"):
        if col in df.columns:
            df[col] = df[col].map(parse_money)

    # Normalize market_pos values
    if "market_pos" in df.columns:
        df["market_pos"] = df["market_pos"].astype(str).str.strip().str.title()

    # Duration
    if "entry_time" in df.columns and "exit_time" in df.columns:
        df["duration_seconds"] = (df["exit_time"] - df["entry_time"]).dt.total_seconds()

    return df


def save_processed(df: pd.DataFrame, out_path: str | Path) -> Path:
    """Save processed output as parquet or csv based on file extension."""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix.lower() == ".parquet":
        df.to_parquet(p, index=False)
    elif p.suffix.lower() == ".csv":
        df.to_csv(p, index=False)
    else:
        raise ValueError(f"Unsupported output format: {p.suffix}")
    info(f"Saved processed data: {p}")
    return p
