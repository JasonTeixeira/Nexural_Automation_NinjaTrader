"""Multi-format CSV importers — TradingView, MetaTrader 4/5, Interactive Brokers, TradeStation.

Expands the addressable market from NinjaTrader-only to all major platforms.
Each parser normalizes to the standard DataFrame format with columns:
  profit, entry_time, exit_time, instrument, strategy, quantity, commission, mae, mfe
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from nexural_research.utils.logging import info, warn


def load_tradingview_csv(path: str | Path) -> pd.DataFrame:
    """Parse TradingView Strategy Tester export.

    TradingView exports with columns like:
    Trade #, Type, Signal, Date/Time, Price, Contracts, Profit, Cum. Profit, Run-up, Drawdown
    """
    p = Path(path)
    info(f"Loading TradingView CSV: {p}")

    try:
        df = pd.read_csv(p, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(p, encoding="latin-1")

    # Normalize column names
    df.columns = [c.strip().lower().replace(" ", "_").replace(".", "").replace("/", "_") for c in df.columns]

    # Map TradingView columns to standard format
    renames = {}
    col_map = {
        "profit": ["profit", "profit_usd", "net_profit", "p&l", "pnl"],
        "entry_time": ["date_time", "entry_date", "open_date", "date"],
        "exit_time": ["exit_date", "close_date"],
        "instrument": ["symbol", "ticker", "market"],
        "quantity": ["contracts", "qty", "shares", "lots", "size"],
        "commission": ["commission", "fees"],
    }

    for target, aliases in col_map.items():
        if target not in df.columns:
            for alias in aliases:
                if alias in df.columns:
                    renames[alias] = target
                    break

    if renames:
        info(f"TradingView column mappings: {renames}")
        df = df.rename(columns=renames)

    # Handle run-up/drawdown as MFE/MAE
    for src, tgt in [("run-up", "mfe"), ("run_up", "mfe"), ("runup", "mfe"), ("drawdown", "mae")]:
        if src in df.columns and tgt not in df.columns:
            df[tgt] = pd.to_numeric(df[src], errors="coerce").fillna(0).abs()

    # Parse profit
    if "profit" in df.columns:
        df["profit"] = pd.to_numeric(df["profit"], errors="coerce").fillna(0)

    # Parse times
    for col in ["entry_time", "exit_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # If no exit_time, estimate from entry_time
    if "exit_time" not in df.columns and "entry_time" in df.columns:
        df["exit_time"] = df["entry_time"] + pd.Timedelta(minutes=15)

    if "profit" not in df.columns:
        warn("No profit column found in TradingView export")

    return df


def load_metatrader_csv(path: str | Path) -> pd.DataFrame:
    """Parse MetaTrader 4/5 trade history export.

    MT4/MT5 exports with columns like:
    Ticket, Open Time, Type, Size, Item, Price, S/L, T/P, Close Time, Close Price, Commission, Swap, Profit
    """
    p = Path(path)
    info(f"Loading MetaTrader CSV: {p}")

    try:
        df = pd.read_csv(p, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(p, encoding="latin-1")

    df.columns = [c.strip().lower().replace(" ", "_").replace("/", "_") for c in df.columns]

    renames = {
        "open_time": "entry_time",
        "close_time": "exit_time",
        "item": "instrument",
        "size": "quantity",
    }

    # Only rename if column exists
    renames = {k: v for k, v in renames.items() if k in df.columns}
    df = df.rename(columns=renames)

    if "profit" in df.columns:
        df["profit"] = pd.to_numeric(df["profit"], errors="coerce").fillna(0)

    # Add swap and commission to profit if available
    if "swap" in df.columns and "commission" in df.columns:
        swap = pd.to_numeric(df["swap"], errors="coerce").fillna(0)
        comm = pd.to_numeric(df["commission"], errors="coerce").fillna(0)
        df["commission"] = comm.abs()
        # MT4/5 profit already includes swap, but commission might be separate
        # Keep profit as-is, store commission separately

    for col in ["entry_time", "exit_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Filter out non-trade rows (balance, withdrawal, etc.)
    if "type" in df.columns:
        trade_types = ["buy", "sell", "buy limit", "sell limit", "buy stop", "sell stop"]
        mask = df["type"].str.lower().isin(trade_types)
        if mask.any():
            df = df[mask].copy()

    return df


def load_interactive_brokers_csv(path: str | Path) -> pd.DataFrame:
    """Parse Interactive Brokers trade confirmation/activity export.

    IB exports vary but common columns:
    Symbol, Date/Time, Quantity, T.Price, C.Price, Proceeds, Comm/Fee, Basis, Realized P/L, MTM P/L
    """
    p = Path(path)
    info(f"Loading Interactive Brokers CSV: {p}")

    try:
        df = pd.read_csv(p, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(p, encoding="latin-1")

    df.columns = [c.strip().lower().replace(" ", "_").replace("/", "_").replace(".", "") for c in df.columns]

    renames = {}
    col_map = {
        "profit": ["realized_p_l", "realized_pnl", "realized_pl", "mtm_p_l", "pnl", "profit_loss"],
        "entry_time": ["date_time", "datetime", "trade_date", "date"],
        "instrument": ["symbol", "ticker", "underlying"],
        "quantity": ["quantity", "qty", "shares"],
        "commission": ["comm_fee", "commission", "comm", "fees"],
    }

    for target, aliases in col_map.items():
        if target not in df.columns:
            for alias in aliases:
                if alias in df.columns:
                    renames[alias] = target
                    break

    if renames:
        info(f"IB column mappings: {renames}")
        df = df.rename(columns=renames)

    if "profit" in df.columns:
        df["profit"] = pd.to_numeric(df["profit"], errors="coerce").fillna(0)

    if "entry_time" in df.columns:
        df["entry_time"] = pd.to_datetime(df["entry_time"], errors="coerce")

    if "exit_time" not in df.columns and "entry_time" in df.columns:
        df["exit_time"] = df["entry_time"] + pd.Timedelta(minutes=1)

    return df


def load_tradestation_csv(path: str | Path) -> pd.DataFrame:
    """Parse TradeStation trade history export.

    TradeStation columns:
    Symbol, Trade #, Entry Date, Entry Price, Entry Time, Exit Date, Exit Price, Exit Time,
    Profit/Loss, # Contracts, Entry Name, Exit Name
    """
    p = Path(path)
    info(f"Loading TradeStation CSV: {p}")

    try:
        df = pd.read_csv(p, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(p, encoding="latin-1")

    df.columns = [c.strip().lower().replace(" ", "_").replace("/", "_").replace("#", "n") for c in df.columns]

    renames = {
        "profit_loss": "profit",
        "n_contracts": "quantity",
        "entry_name": "strategy",
    }
    renames = {k: v for k, v in renames.items() if k in df.columns}
    df = df.rename(columns=renames)

    # Combine date + time columns if separate
    if "entry_date" in df.columns and "entry_time" not in df.columns:
        if "entry_time_col" in df.columns:
            df["entry_time"] = pd.to_datetime(df["entry_date"] + " " + df["entry_time_col"], errors="coerce")
        else:
            df["entry_time"] = pd.to_datetime(df["entry_date"], errors="coerce")

    if "exit_date" in df.columns and "exit_time" not in df.columns:
        if "exit_time_col" in df.columns:
            df["exit_time"] = pd.to_datetime(df["exit_date"] + " " + df["exit_time_col"], errors="coerce")
        else:
            df["exit_time"] = pd.to_datetime(df["exit_date"], errors="coerce")

    if "profit" in df.columns:
        df["profit"] = pd.to_numeric(df["profit"], errors="coerce").fillna(0)

    return df


def detect_and_load(path: str | Path) -> tuple[pd.DataFrame, str]:
    """Auto-detect CSV format and load with the appropriate parser.

    Returns (DataFrame, platform_name).
    """
    p = Path(path)

    try:
        df_raw = pd.read_csv(p, nrows=5, encoding="utf-8")
    except UnicodeDecodeError:
        df_raw = pd.read_csv(p, nrows=5, encoding="latin-1")

    cols = set(c.strip().lower() for c in df_raw.columns)

    # TradingView: has "Trade #" or "Signal" or "Run-up"
    if any(k in cols for k in ["trade_#", "trade #", "signal", "run-up", "runup"]):
        return load_tradingview_csv(p), "tradingview"

    # MetaTrader: has "Ticket" or "Open Time" + "Close Time"
    if "ticket" in cols or ("open time" in cols and "close time" in cols) or ("open_time" in cols):
        return load_metatrader_csv(p), "metatrader"

    # Interactive Brokers: has "Realized P/L" or "Comm/Fee" or "Proceeds"
    if any(k in cols for k in ["realized p/l", "realized_p_l", "comm/fee", "proceeds"]):
        return load_interactive_brokers_csv(p), "interactive_brokers"

    # TradeStation: has "Entry Name" or "Exit Name" or "# Contracts"
    if any(k in cols for k in ["entry name", "exit name", "# contracts", "entry_name"]):
        return load_tradestation_csv(p), "tradestation"

    # Fall back to NinjaTrader parser
    from nexural_research.ingest.nt_csv import load_nt_trades_csv
    return load_nt_trades_csv(p), "ninjatrader"
