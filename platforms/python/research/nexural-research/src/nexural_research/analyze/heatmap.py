from __future__ import annotations

import pandas as pd


def time_heatmap(
    df_trades: pd.DataFrame,
    *,
    ts_col: str = "exit_time",
    value_col: str = "profit",
    agg: str = "sum",
) -> pd.DataFrame:
    """Return a day-of-week x hour heatmap table.

    This is designed to feed a Plotly heatmap.
    """

    if ts_col not in df_trades.columns:
        raise ValueError(f"missing timestamp column: {ts_col}")
    if value_col not in df_trades.columns:
        raise ValueError(f"missing value column: {value_col}")

    ts = pd.to_datetime(df_trades[ts_col], errors="coerce")
    v = pd.to_numeric(df_trades[value_col], errors="coerce").fillna(0.0)
    df = pd.DataFrame({"ts": ts, "v": v}).dropna(subset=["ts"])

    df["dow"] = df["ts"].dt.day_name().astype(str)
    df["hour"] = df["ts"].dt.hour.astype(int)

    if agg == "sum":
        table = df.pivot_table(index="dow", columns="hour", values="v", aggfunc="sum", fill_value=0.0)
    elif agg == "mean":
        table = df.pivot_table(index="dow", columns="hour", values="v", aggfunc="mean", fill_value=0.0)
    elif agg == "count":
        table = df.pivot_table(index="dow", columns="hour", values="v", aggfunc="count", fill_value=0)
    else:
        raise ValueError(f"unsupported agg: {agg}")

    # Stable ordering (Mon..Sun)
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    table = table.reindex([d for d in order if d in table.index])
    # Ensure all hours 0..23 exist
    for h in range(24):
        if h not in table.columns:
            table[h] = 0.0
    table = table[sorted(table.columns)]

    return table
