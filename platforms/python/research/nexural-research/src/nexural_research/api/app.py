"""FastAPI backend for Nexural Research.

Provides REST API endpoints for the full analysis suite:
- CSV upload & auto-detection
- Core metrics, advanced metrics, robustness testing
- Monte Carlo simulations (shuffle, parametric, block bootstrap)
- Walk-forward analysis (single split, rolling, anchored)
- Portfolio analysis & benchmark comparison
- Overfitting detection (Deflated Sharpe Ratio)
- Regime analysis
- Report generation
- Run history
"""

from __future__ import annotations

import io
import json
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from nexural_research.analyze.advanced_metrics import (
    comprehensive_analysis,
    distribution_metrics,
    expectancy_metrics,
    risk_return_metrics,
    time_decay_analysis,
    trade_dependency_analysis,
)
from nexural_research.analyze.advanced_robustness import (
    block_bootstrap_monte_carlo,
    deflated_sharpe_ratio,
    parametric_monte_carlo,
    regime_analysis,
    rolling_walk_forward,
)
from nexural_research.analyze.equity import (
    drawdown_from_equity,
    equity_curve_from_trades,
)
from nexural_research.analyze.execution_quality import execution_quality_from_executions
from nexural_research.analyze.heatmap import time_heatmap
from nexural_research.analyze.metrics import metrics_by, metrics_from_trades
from nexural_research.analyze.improvements import generate_improvement_report
from nexural_research.analyze.portfolio import benchmark_comparison, portfolio_analysis
from nexural_research.analyze.robustness import monte_carlo_max_drawdown, walk_forward_split
from nexural_research.ingest.detect import ExportKind, detect_export_kind
from nexural_research.ingest.nt_csv import load_nt_trades_csv
from nexural_research.ingest.nt_executions_csv import load_nt_executions_csv
from nexural_research.ingest.nt_optimization_csv import load_nt_optimization_csv
from nexural_research.report.html import build_trades_report_html

app = FastAPI(
    title="Nexural Research API",
    description="Institutional-grade strategy analysis engine for NinjaTrader trade data",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Return detailed error messages instead of raw 500s."""
    import traceback
    tb = traceback.format_exc()
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__,
            "traceback": tb.split("\n")[-3:],
        },
    )

# In-memory session store for uploaded data
_sessions: dict[str, dict[str, Any]] = {}


def _safe_serialize(obj: Any) -> Any:
    """Recursively convert dataclasses / non-JSON types for JSON output."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _safe_serialize(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [_safe_serialize(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, float) and (obj == float("inf") or obj == float("-inf")):
        return str(obj)
    return obj


async def _parse_upload(file: UploadFile) -> tuple[pd.DataFrame, str]:
    """Parse an uploaded CSV file, auto-detecting the export type."""
    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="wb") as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    detected = detect_export_kind(tmp_path)
    kind = detected.kind

    if kind == ExportKind.TRADES:
        df = load_nt_trades_csv(tmp_path)
    elif kind == ExportKind.EXECUTIONS:
        df = load_nt_executions_csv(tmp_path)
    elif kind == ExportKind.OPTIMIZATION:
        df = load_nt_optimization_csv(tmp_path)
    else:
        raise HTTPException(400, f"Could not detect export type: {detected.reason}")

    tmp_path.unlink(missing_ok=True)
    return df, kind.value


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Upload & Session Management
# ---------------------------------------------------------------------------

@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...), session_id: str = Query(default="default")):
    """Upload a NinjaTrader CSV export. Auto-detects Trades/Executions/Optimization."""
    df, kind = await _parse_upload(file)

    _sessions[session_id] = {
        "df": df,
        "kind": kind,
        "filename": file.filename,
        "n_rows": len(df),
        "columns": list(df.columns),
    }

    return {
        "session_id": session_id,
        "kind": kind,
        "filename": file.filename,
        "n_rows": len(df),
        "columns": list(df.columns),
        "preview": json.loads(df.head(10).to_json(orient="records", date_format="iso")),
    }


@app.get("/api/sessions")
def list_sessions():
    """List active analysis sessions."""
    return {
        sid: {"kind": s["kind"], "filename": s["filename"], "n_rows": s["n_rows"]}
        for sid, s in _sessions.items()
    }


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    _sessions.pop(session_id, None)
    return {"deleted": session_id}


def _get_trades(session_id: str) -> pd.DataFrame:
    if session_id not in _sessions:
        raise HTTPException(404, f"Session not found: {session_id}. Upload a CSV first.")
    s = _sessions[session_id]
    if s["kind"] != "trades":
        raise HTTPException(400, f"This endpoint requires Trades data, got {s['kind']}")
    return s["df"]


def _get_executions(session_id: str) -> pd.DataFrame:
    if session_id not in _sessions:
        raise HTTPException(404, f"Session not found: {session_id}")
    s = _sessions[session_id]
    if s["kind"] != "executions":
        raise HTTPException(400, f"This endpoint requires Executions data, got {s['kind']}")
    return s["df"]


# ---------------------------------------------------------------------------
# Core Metrics
# ---------------------------------------------------------------------------

@app.get("/api/analysis/metrics")
def get_metrics(session_id: str = Query(default="default")):
    """Get core trade metrics (n_trades, win_rate, profit_factor, etc.)."""
    df = _get_trades(session_id)
    m = metrics_from_trades(df)
    return _safe_serialize(m)


@app.get("/api/analysis/metrics/by/{group}")
def get_metrics_by(group: str, session_id: str = Query(default="default")):
    """Get metrics grouped by a column (strategy, instrument, etc.)."""
    df = _get_trades(session_id)
    result = metrics_by(df, group)
    return json.loads(result.to_json(orient="records"))


# ---------------------------------------------------------------------------
# Advanced Metrics
# ---------------------------------------------------------------------------

@app.get("/api/analysis/risk-return")
def get_risk_return(
    session_id: str = Query(default="default"),
    risk_free_rate: float = Query(default=0.0),
):
    """Sharpe, Sortino, Calmar, Omega, MAR, Tail ratio, etc."""
    df = _get_trades(session_id)
    return _safe_serialize(risk_return_metrics(df, risk_free_rate=risk_free_rate))


@app.get("/api/analysis/expectancy")
def get_expectancy(session_id: str = Query(default="default")):
    """Expectancy, Kelly Criterion, Optimal f, payoff ratio."""
    df = _get_trades(session_id)
    return _safe_serialize(expectancy_metrics(df))


@app.get("/api/analysis/dependency")
def get_dependency(session_id: str = Query(default="default")):
    """Trade dependency analysis (Z-score, serial correlation, streaks)."""
    df = _get_trades(session_id)
    return _safe_serialize(trade_dependency_analysis(df))


@app.get("/api/analysis/distribution")
def get_distribution(session_id: str = Query(default="default")):
    """Return distribution analysis (skew, kurtosis, VaR, CVaR, normality test)."""
    df = _get_trades(session_id)
    return _safe_serialize(distribution_metrics(df))


@app.get("/api/analysis/time-decay")
def get_time_decay(
    session_id: str = Query(default="default"),
    window_size: int = Query(default=50),
):
    """Edge stability / time-decay analysis."""
    df = _get_trades(session_id)
    return _safe_serialize(time_decay_analysis(df, window_size=window_size))


@app.get("/api/analysis/comprehensive")
def get_comprehensive(
    session_id: str = Query(default="default"),
    risk_free_rate: float = Query(default=0.0),
):
    """Run the complete institutional analysis suite."""
    df = _get_trades(session_id)
    result = comprehensive_analysis(df, risk_free_rate=risk_free_rate)
    return _safe_serialize(result)


# ---------------------------------------------------------------------------
# Robustness Testing
# ---------------------------------------------------------------------------

@app.get("/api/robustness/monte-carlo")
def get_monte_carlo(
    session_id: str = Query(default="default"),
    n: int = Query(default=1000),
    seed: int = Query(default=42),
):
    """Original shuffle-based Monte Carlo (max drawdown distribution)."""
    df = _get_trades(session_id)
    return _safe_serialize(monte_carlo_max_drawdown(df, n=n, seed=seed))


@app.get("/api/robustness/parametric-monte-carlo")
def get_parametric_mc(
    session_id: str = Query(default="default"),
    n_simulations: int = Query(default=5000),
    distribution: str = Query(default="empirical"),
    seed: int = Query(default=42),
):
    """Parametric Monte Carlo (empirical/normal/t-distribution)."""
    df = _get_trades(session_id)
    return _safe_serialize(parametric_monte_carlo(
        df, n_simulations=n_simulations, distribution=distribution, seed=seed,
    ))


@app.get("/api/robustness/block-bootstrap")
def get_block_bootstrap(
    session_id: str = Query(default="default"),
    n_simulations: int = Query(default=2000),
    block_size: int | None = Query(default=None),
    seed: int = Query(default=42),
):
    """Block bootstrap Monte Carlo (preserves autocorrelation)."""
    df = _get_trades(session_id)
    return _safe_serialize(block_bootstrap_monte_carlo(
        df, n_simulations=n_simulations, block_size=block_size, seed=seed,
    ))


@app.get("/api/robustness/walk-forward")
def get_walk_forward(
    session_id: str = Query(default="default"),
    split: float = Query(default=0.7),
):
    """Simple walk-forward split."""
    df = _get_trades(session_id)
    return _safe_serialize(walk_forward_split(df, split=split))


@app.get("/api/robustness/rolling-walk-forward")
def get_rolling_wf(
    session_id: str = Query(default="default"),
    n_windows: int = Query(default=5),
    in_sample_pct: float = Query(default=0.7),
    anchored: bool = Query(default=False),
):
    """Rolling or anchored walk-forward analysis with multiple windows."""
    df = _get_trades(session_id)
    result = rolling_walk_forward(
        df, n_windows=n_windows, in_sample_pct=in_sample_pct, anchored=anchored,
    )
    return _safe_serialize(result)


@app.get("/api/robustness/deflated-sharpe")
def get_deflated_sharpe(
    session_id: str = Query(default="default"),
    n_trials: int = Query(default=100),
):
    """Deflated Sharpe Ratio for overfitting detection."""
    df = _get_trades(session_id)
    return _safe_serialize(deflated_sharpe_ratio(df, n_trials=n_trials))


@app.get("/api/robustness/regime")
def get_regime(
    session_id: str = Query(default="default"),
    n_regimes: int = Query(default=3),
    window: int = Query(default=20),
):
    """Volatility regime detection & performance analysis."""
    df = _get_trades(session_id)
    return _safe_serialize(regime_analysis(df, n_regimes=n_regimes, window=window))


# ---------------------------------------------------------------------------
# Portfolio & Benchmark
# ---------------------------------------------------------------------------

@app.get("/api/analysis/portfolio")
def get_portfolio(session_id: str = Query(default="default")):
    """Multi-strategy portfolio analysis with correlation & diversification."""
    df = _get_trades(session_id)
    return _safe_serialize(portfolio_analysis(df))


@app.get("/api/analysis/benchmark")
def get_benchmark(
    session_id: str = Query(default="default"),
    n_random_sims: int = Query(default=1000),
):
    """Compare strategy vs buy-and-hold and random entry benchmarks."""
    df = _get_trades(session_id)
    return _safe_serialize(benchmark_comparison(df, n_random_sims=n_random_sims))


# ---------------------------------------------------------------------------
# Charts Data
# ---------------------------------------------------------------------------

@app.get("/api/charts/equity")
def get_equity_curve(session_id: str = Query(default="default")):
    """Equity curve data for charting."""
    df = _get_trades(session_id)
    eq = equity_curve_from_trades(df)
    dd = drawdown_from_equity(eq.equity)
    return {
        "timestamps": eq.ts.dt.strftime("%Y-%m-%dT%H:%M:%S").tolist(),
        "equity": eq.equity.round(2).tolist(),
        "pnl": eq.pnl.round(2).tolist(),
        "drawdown": dd.round(2).tolist(),
    }


@app.get("/api/charts/heatmap")
def get_heatmap(
    session_id: str = Query(default="default"),
    agg: str = Query(default="sum"),
):
    """PnL heatmap data (day-of-week x hour)."""
    df = _get_trades(session_id)
    ts_col = "exit_time" if "exit_time" in df.columns else "entry_time"
    heat = time_heatmap(df, ts_col=ts_col, agg=agg)
    return {
        "days": heat.index.tolist(),
        "hours": [int(h) for h in heat.columns.tolist()],
        "values": heat.round(2).values.tolist(),
    }


@app.get("/api/charts/distribution")
def get_pnl_distribution(session_id: str = Query(default="default"), bins: int = Query(default=50)):
    """PnL histogram data for distribution chart."""
    df = _get_trades(session_id)
    pnl = pd.to_numeric(df["profit"], errors="coerce").fillna(0.0).to_numpy()
    counts, edges = __import__("numpy").histogram(pnl, bins=bins)
    centers = [(edges[i] + edges[i + 1]) / 2 for i in range(len(edges) - 1)]
    return {
        "centers": [round(c, 2) for c in centers],
        "counts": counts.tolist(),
        "edges": [round(e, 2) for e in edges.tolist()],
    }


@app.get("/api/charts/trades")
def get_trades_data(session_id: str = Query(default="default"), limit: int = Query(default=500)):
    """Raw trades data for the trades table."""
    df = _get_trades(session_id)
    return json.loads(df.head(limit).to_json(orient="records", date_format="iso"))


# ---------------------------------------------------------------------------
# Execution Quality
# ---------------------------------------------------------------------------

@app.get("/api/analysis/execution-quality")
def get_execution_quality(session_id: str = Query(default="default")):
    """Execution quality metrics (slippage, commission, order types)."""
    df = _get_executions(session_id)
    return _safe_serialize(execution_quality_from_executions(df))


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

@app.get("/api/report/html", response_class=HTMLResponse)
def generate_html_report(
    session_id: str = Query(default="default"),
    title: str = Query(default="Nexural Research Report"),
):
    """Generate a full HTML report."""
    df = _get_trades(session_id)
    html = build_trades_report_html(df, title=title)
    return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# Entry point for running the API server
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Strategy Improvement Engine
# ---------------------------------------------------------------------------

@app.get("/api/analysis/improvements")
def get_improvements(session_id: str = Query(default="default")):
    """Generate the full strategy improvement report with actionable recommendations."""
    df = _get_trades(session_id)
    report = generate_improvement_report(df)
    return _safe_serialize(report)


# ---------------------------------------------------------------------------
# Export Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/export/json")
def export_json(session_id: str = Query(default="default")):
    """Export all metrics as a single JSON payload."""
    df = _get_trades(session_id)
    from nexural_research.analyze.advanced_metrics import comprehensive_analysis
    from nexural_research.analyze.advanced_robustness import deflated_sharpe_ratio, regime_analysis
    from nexural_research.analyze.portfolio import benchmark_comparison as bm_compare

    comp = comprehensive_analysis(df)
    dsr = deflated_sharpe_ratio(df)
    regime = regime_analysis(df)
    bm = bm_compare(df, n_random_sims=500)
    improvements = generate_improvement_report(df)
    core = metrics_from_trades(df)

    return {
        "core_metrics": _safe_serialize(core),
        "risk_return": _safe_serialize(comp.risk_return),
        "expectancy": _safe_serialize(comp.expectancy),
        "dependency": _safe_serialize(comp.dependency),
        "distribution": _safe_serialize(comp.distribution),
        "time_decay": _safe_serialize(comp.time_decay),
        "deflated_sharpe": _safe_serialize(dsr),
        "regime": _safe_serialize(regime),
        "benchmark": _safe_serialize(bm),
        "improvements": _safe_serialize(improvements),
    }


@app.get("/api/export/csv")
def export_csv(session_id: str = Query(default="default"), filtered: bool = Query(default=False)):
    """Export trades as CSV. If filtered=true, applies recommended time filters."""
    from fastapi.responses import StreamingResponse

    df = _get_trades(session_id)

    if filtered:
        report = generate_improvement_report(df)
        tf = report.time_filter
        if tf and (tf.hours_to_remove or tf.days_to_remove):
            ts_col = "exit_time" if "exit_time" in df.columns else "entry_time"
            if ts_col in df.columns:
                ts = pd.to_datetime(df[ts_col], errors="coerce")
                mask = ~(ts.dt.hour.isin(tf.hours_to_remove) | ts.dt.day_name().isin(tf.days_to_remove))
                df = df[mask].copy()

    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)

    filename = f"trades_{'filtered' if filtered else 'full'}_{session_id}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/export/comparison")
def export_comparison(
    session_a: str = Query(...),
    session_b: str = Query(...),
):
    """Compare two sessions side-by-side."""
    df_a = _get_trades(session_a)
    df_b = _get_trades(session_b)

    from nexural_research.analyze.advanced_metrics import comprehensive_analysis

    comp_a = comprehensive_analysis(df_a)
    comp_b = comprehensive_analysis(df_b)
    core_a = metrics_from_trades(df_a)
    core_b = metrics_from_trades(df_b)
    imp_a = generate_improvement_report(df_a)
    imp_b = generate_improvement_report(df_b)

    def delta(a: float, b: float) -> dict:
        diff = b - a
        pct = (diff / abs(a) * 100) if abs(a) > 1e-10 else 0.0
        return {"a": round(a, 4), "b": round(b, 4), "delta": round(diff, 4), "pct_change": round(pct, 2)}

    return {
        "session_a": session_a,
        "session_b": session_b,
        "trades": {"a": len(df_a), "b": len(df_b)},
        "grade": {"a": imp_a.overall_grade, "b": imp_b.overall_grade},
        "net_profit": delta(core_a.net_profit, core_b.net_profit),
        "win_rate": delta(core_a.win_rate, core_b.win_rate),
        "profit_factor": delta(core_a.profit_factor, core_b.profit_factor),
        "max_drawdown": delta(core_a.max_drawdown, core_b.max_drawdown),
        "sharpe": delta(comp_a.risk_return.sharpe_ratio, comp_b.risk_return.sharpe_ratio),
        "sortino": delta(comp_a.risk_return.sortino_ratio, comp_b.risk_return.sortino_ratio),
        "calmar": delta(comp_a.risk_return.calmar_ratio, comp_b.risk_return.calmar_ratio),
        "expectancy": delta(comp_a.expectancy.expectancy, comp_b.expectancy.expectancy),
        "kelly": delta(comp_a.expectancy.kelly_pct, comp_b.expectancy.kelly_pct),
        "equity_a": _safe_serialize(equity_curve_from_trades(df_a)),
        "equity_b": _safe_serialize(equity_curve_from_trades(df_b)),
    }


# ---------------------------------------------------------------------------
# AI Strategy Analyst
# ---------------------------------------------------------------------------

class AiRequest(BaseModel):
    api_key: str
    provider: str = "anthropic"  # "anthropic" or "openai"
    message: str
    session_id: str = "default"


class AiResponse(BaseModel):
    response: str
    provider: str
    context_tokens_approx: int


@app.post("/api/ai/analyze", response_model=AiResponse)
async def ai_analyze(req: AiRequest):
    """Send trade data to AI (Claude or GPT) for natural-language analysis.

    Users provide their own API key. The system builds rich context from
    the analysis engine and sends it to the AI for interpretation.
    """
    from nexural_research.api.ai_analyst import (
        build_strategy_context,
        query_anthropic,
        query_openai,
        query_perplexity,
    )

    if req.session_id not in _sessions:
        raise HTTPException(404, f"Session not found: {req.session_id}")
    s = _sessions[req.session_id]
    if s["kind"] != "trades":
        raise HTTPException(400, "AI analysis requires Trades data")

    df = s["df"]
    context = build_strategy_context(df)

    try:
        if req.provider == "anthropic":
            response = await query_anthropic(req.api_key, context, req.message)
        elif req.provider == "openai":
            response = await query_openai(req.api_key, context, req.message)
        elif req.provider == "perplexity":
            response = await query_perplexity(req.api_key, context, req.message)
        else:
            raise HTTPException(400, f"Unsupported provider: {req.provider}")
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "auth" in error_msg.lower():
            raise HTTPException(401, "Invalid API key. Please check your key in Settings.")
        raise HTTPException(502, f"AI provider error: {error_msg}")

    return AiResponse(
        response=response,
        provider=req.provider,
        context_tokens_approx=len(context) // 4,
    )


@app.post("/api/ai/context-preview")
async def ai_context_preview(session_id: str = Query(default="default")):
    """Preview the context that would be sent to the AI."""
    from nexural_research.api.ai_analyst import build_strategy_context

    if session_id not in _sessions:
        raise HTTPException(404, f"Session not found: {session_id}")
    s = _sessions[session_id]
    if s["kind"] != "trades":
        raise HTTPException(400, "Context preview requires Trades data")

    context = build_strategy_context(s["df"])
    return {"context": context, "approx_tokens": len(context) // 4}


# ---------------------------------------------------------------------------
# Static frontend serving (production)
# ---------------------------------------------------------------------------

def _find_static_dir() -> Path | None:
    """Locate the built frontend assets. Checks multiple locations."""
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "static",       # Docker / packaged
        Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist",  # Dev build
    ]
    for d in candidates:
        if d.is_dir() and (d / "index.html").exists():
            return d
    return None

_static_dir = _find_static_dir()
if _static_dir:
    from fastapi.staticfiles import StaticFiles

    # Serve index.html for the root and any non-API path (SPA fallback)
    @app.get("/", response_class=HTMLResponse)
    def serve_index():
        return (_static_dir / "index.html").read_text(encoding="utf-8")

    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")


# ---------------------------------------------------------------------------
# Demo mode: load built-in sample data on startup
# ---------------------------------------------------------------------------

def _load_demo_data() -> None:
    """Pre-load sample data so the app has something to show on first launch."""
    sample_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "exports"
    sample = sample_dir / "sample_trades.csv"
    if sample.exists() and "demo" not in _sessions:
        try:
            from nexural_research.ingest.nt_csv import load_nt_trades_csv
            df = load_nt_trades_csv(sample)
            _sessions["demo"] = {
                "df": df, "kind": "trades", "filename": "demo_trades.csv",
                "n_rows": len(df), "columns": list(df.columns),
            }
        except Exception:
            pass

_load_demo_data()


# ---------------------------------------------------------------------------
# Entry point for running the API server
# ---------------------------------------------------------------------------

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    import uvicorn
    uvicorn.run("nexural_research.api.app:app", host=host, port=port, reload=reload)


def launch(port: int = 8000) -> None:
    """Launch the full application: start server and open browser."""
    import webbrowser
    import threading
    import uvicorn

    url = f"http://localhost:{port}"
    threading.Timer(2.0, lambda: webbrowser.open(url)).start()
    print("\n  Nexural Research v1.0.0")
    print(f"  Dashboard:  {url}")
    print(f"  API Docs:   {url}/api/docs")
    print("  Press Ctrl+C to stop\n")
    uvicorn.run("nexural_research.api.app:app", host="127.0.0.1", port=port)


if __name__ == "__main__":
    launch()
