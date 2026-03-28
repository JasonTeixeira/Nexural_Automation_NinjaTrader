from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import plotly.graph_objects as go

from nexural_research.analyze.equity import equity_curve_from_trades, drawdown_from_equity
from nexural_research.analyze.heatmap import time_heatmap
from nexural_research.analyze.metrics import metrics_by, metrics_from_trades


def _fmt_money(x: float) -> str:
    try:
        return f"${x:,.2f}"
    except Exception:
        return str(x)


def _df_to_html_table(df: pd.DataFrame, *, max_rows: int = 50) -> str:
    if df is None:
        return ""
    d = df.head(max_rows).copy()
    return d.to_html(index=False, escape=True)


def build_trades_report_html(df_trades: pd.DataFrame, *, title: str = "Nexural Research Report") -> str:
    """Generate a single-file HTML report for a trades dataset."""

    m = metrics_from_trades(df_trades)
    eq = equity_curve_from_trades(df_trades)
    dd = drawdown_from_equity(eq.equity)

    fig_equity = go.Figure()
    fig_equity.add_trace(go.Scatter(x=eq.ts, y=eq.equity, mode="lines", name="Equity"))
    fig_equity.update_layout(title="Equity Curve", xaxis_title="Time", yaxis_title="PnL (cum)")

    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(x=eq.ts, y=dd, mode="lines", name="Drawdown"))
    fig_dd.update_layout(title="Drawdown", xaxis_title="Time", yaxis_title="Drawdown")

    heat = time_heatmap(df_trades, ts_col="exit_time" if "exit_time" in df_trades.columns else "entry_time")
    fig_heat = go.Figure(
        data=go.Heatmap(
            z=heat.to_numpy(),
            x=[str(c) for c in heat.columns],
            y=[str(i) for i in heat.index],
            colorscale="RdYlGn",
            colorbar=dict(title="PnL"),
        )
    )
    fig_heat.update_layout(title="PnL Heatmap (Day-of-week x Hour)", xaxis_title="Hour", yaxis_title="Day")

    # Breakdown tables
    strat = metrics_by(df_trades, "strategy") if "strategy" in df_trades.columns else pd.DataFrame()
    inst = metrics_by(df_trades, "instrument") if "instrument" in df_trades.columns else pd.DataFrame()

    metrics_html = "".join(
        f"<tr><td>{k}</td><td>{_fmt_money(v) if 'profit' in k or 'drawdown' in k else v}</td></tr>"
        for k, v in asdict(m).items()
    )

    parts = [
        "<!doctype html>",
        "<html>",
        "<head>",
        "<meta charset='utf-8' />",
        f"<title>{title}</title>",
        "<style>",
        "body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:20px;}",
        ".grid{display:grid;grid-template-columns:1fr;gap:18px;}",
        "table{border-collapse:collapse;}",
        "td,th{border:1px solid #ddd;padding:6px 8px;font-size:13px;}",
        "th{background:#f6f6f6;text-align:left;}",
        "</style>",
        "</head>",
        "<body>",
        f"<h1>{title}</h1>",
        "<h2>Summary</h2>",
        "<table>",
        "<thead><tr><th>Metric</th><th>Value</th></tr></thead>",
        f"<tbody>{metrics_html}</tbody>",
        "</table>",
        "<div class='grid'>",
        fig_equity.to_html(full_html=False, include_plotlyjs="cdn"),
        fig_dd.to_html(full_html=False, include_plotlyjs=False),
        fig_heat.to_html(full_html=False, include_plotlyjs=False),
        "</div>",
        "<h2>By Strategy</h2>",
        _df_to_html_table(strat, max_rows=200),
        "<h2>By Instrument</h2>",
        _df_to_html_table(inst, max_rows=200),
        "</body>",
        "</html>",
    ]

    return "\n".join(parts)
