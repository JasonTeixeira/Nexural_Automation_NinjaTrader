from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from nexural_research.analyze.metrics import metrics_from_trades
from nexural_research.analyze.execution_quality import execution_quality_from_executions
from nexural_research.analyze.robustness import monte_carlo_max_drawdown, walk_forward_split
from nexural_research.analyze.advanced_metrics import (
    comprehensive_analysis,
)
from nexural_research.analyze.advanced_robustness import (
    parametric_monte_carlo,
    rolling_walk_forward,
    deflated_sharpe_ratio,
    regime_analysis,
)
from nexural_research.analyze.portfolio import portfolio_analysis, benchmark_comparison
from nexural_research.cli_helpers import default_run_id, ensure_parent_dir
from nexural_research.ingest.detect import ExportKind, detect_export_kind
from nexural_research.ingest.nt_csv import load_nt_trades_csv, save_processed
from nexural_research.ingest.nt_executions_csv import load_nt_executions_csv
from nexural_research.ingest.nt_optimization_csv import load_nt_optimization_csv
from nexural_research.registry.duckdb_registry import RunRegistry
from nexural_research.report.html import build_trades_report_html
from nexural_research.utils.paths import paths


def _cmd_ingest(args: argparse.Namespace) -> int:
    project = paths()
    in_path = Path(args.input) if args.input else (project.root / "data" / "exports" / "sample_trades.csv")
    detected = detect_export_kind(in_path)

    kind: ExportKind = detected.kind
    # Default output naming by kind.
    out_path = (
        Path(args.output)
        if args.output
        else (project.root / "data" / "processed" / f"{kind.value}.parquet")
    )

    if kind == ExportKind.TRADES:
        df = load_nt_trades_csv(in_path)
    elif kind == ExportKind.EXECUTIONS:
        df = load_nt_executions_csv(in_path)
    elif kind == ExportKind.OPTIMIZATION:
        df = load_nt_optimization_csv(in_path)
    else:
        raise ValueError(f"unsupported export kind: {kind}")

    save_processed(df, out_path)

    # Run registry (best-effort): store run record + trade metrics when available.
    if not args.no_registry:
        run_id = args.run_id or default_run_id(kind.value)
        reg = RunRegistry(project.experiments / "runs.duckdb")
        reg.register_run(run_id=run_id, kind=kind.value, input_path=in_path, processed_path=out_path)

        if kind == ExportKind.TRADES:
            tm = metrics_from_trades(df)
            reg.upsert_trade_metrics(run_id, tm)
            reg.store_trades(run_id, df)
        elif kind == ExportKind.EXECUTIONS:
            reg.store_executions(run_id, df)
            eqm = execution_quality_from_executions(df)
            reg.upsert_execution_quality_metrics(run_id, eqm)
        elif kind == ExportKind.OPTIMIZATION:
            reg.store_optimizations(run_id, df)

    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    project = paths()
    reg = RunRegistry(project.experiments / "runs.duckdb")
    a = reg.get_trade_metrics(str(args.run_a))
    b = reg.get_trade_metrics(str(args.run_b))
    if not a:
        raise SystemExit(f"No trade metrics found for run: {args.run_a}")
    if not b:
        raise SystemExit(f"No trade metrics found for run: {args.run_b}")

    # Simple diff print.
    keys = sorted(set(a.keys()) | set(b.keys()))
    print(f"Compare runs: {args.run_a} vs {args.run_b}")
    print("metric,a,b,delta")
    for k in keys:
        if k == "run_id":
            continue
        av = a.get(k)
        bv = b.get(k)
        # Only numeric deltas
        try:
            da = float(av) if av is not None else None
            db = float(bv) if bv is not None else None
            delta = (db - da) if (da is not None and db is not None) else None
        except Exception:
            delta = None
        print(f"{k},{av},{bv},{delta}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    project = paths()
    in_path = Path(args.input) if args.input else (project.root / "data" / "exports" / "sample_trades.csv")

    detected = detect_export_kind(in_path)
    if detected.kind != ExportKind.TRADES:
        raise SystemExit(
            f"report currently supports Trades export only; got {detected.kind.value} ({detected.reason})."
        )

    df = load_nt_trades_csv(in_path)
    run_id = args.run_id or default_run_id("report")
    out_dir = Path(args.out_dir) if args.out_dir else (project.reports / run_id)
    out_html = ensure_parent_dir(out_dir / "report.html")
    html = build_trades_report_html(df, title=args.title or f"Nexural Research Report ({run_id})")
    out_html.write_text(html, encoding="utf-8")

    if not args.no_registry:
        reg = RunRegistry(project.experiments / "runs.duckdb")
        reg.register_run(
            run_id=run_id,
            kind="report",
            input_path=in_path,
            processed_path=None,
            report_path=out_html,
        )
        reg.upsert_trade_metrics(run_id, metrics_from_trades(df))
        reg.store_trades(run_id, df)

    print(out_html)
    return 0


def _cmd_execq(args: argparse.Namespace) -> int:
    project = paths()
    in_path = Path(args.input) if args.input else (project.root / "data" / "exports" / "sample_executions.csv")
    detected = detect_export_kind(in_path)
    if detected.kind != ExportKind.EXECUTIONS:
        raise SystemExit(
            f"execq currently supports Executions export only; got {detected.kind.value} ({detected.reason})."
        )

    df = load_nt_executions_csv(in_path)
    m = execution_quality_from_executions(df)
    print(m)

    if not args.no_registry:
        run_id = args.run_id or default_run_id("execq")
        reg = RunRegistry(project.experiments / "runs.duckdb")
        reg.register_run(run_id=run_id, kind="execq", input_path=in_path, processed_path=None, report_path=None)
        reg.store_executions(run_id, df)
        reg.upsert_execution_quality_metrics(run_id, m)

    return 0


def _cmd_robust(args: argparse.Namespace) -> int:
    project = paths()
    in_path = Path(args.input) if args.input else (project.root / "data" / "exports" / "sample_trades.csv")
    detected = detect_export_kind(in_path)
    if detected.kind != ExportKind.TRADES:
        raise SystemExit(
            f"robust currently supports Trades export only; got {detected.kind.value} ({detected.reason})."
        )

    df = load_nt_trades_csv(in_path)
    mc = monte_carlo_max_drawdown(df, n=int(args.mc_n), seed=int(args.seed))
    wf = walk_forward_split(df, split=float(args.split))
    print("MonteCarloMaxDrawdown:")
    print(mc)
    print("WalkForwardSplit:")
    print(wf)
    return 0


def _cmd_analyze(args: argparse.Namespace) -> int:
    """Run the full institutional analysis suite."""
    project = paths()
    in_path = Path(args.input) if args.input else (project.root / "data" / "exports" / "sample_trades.csv")
    detected = detect_export_kind(in_path)
    if detected.kind != ExportKind.TRADES:
        raise SystemExit(f"analyze requires Trades export; got {detected.kind.value}")

    df = load_nt_trades_csv(in_path)
    result = comprehensive_analysis(df, risk_free_rate=float(args.risk_free_rate))

    print("=" * 70)
    print("NEXURAL RESEARCH — COMPREHENSIVE STRATEGY ANALYSIS")
    print("=" * 70)

    sections = {
        "Risk/Return Metrics": asdict(result.risk_return),
        "Expectancy & Position Sizing": asdict(result.expectancy),
        "Trade Dependency": asdict(result.dependency),
        "Return Distribution": asdict(result.distribution),
        "Time-Decay / Edge Stability": asdict(result.time_decay),
    }

    for title, data in sections.items():
        print(f"\n--- {title} ---")
        for k, v in data.items():
            print(f"  {k:30s} : {v}")

    # Additional analyses
    print(f"\n--- Deflated Sharpe Ratio (overfitting test, {args.n_trials} trials) ---")
    dsr = deflated_sharpe_ratio(df, n_trials=int(args.n_trials))
    for k, v in asdict(dsr).items():
        print(f"  {k:30s} : {v}")

    print(f"\n--- Parametric Monte Carlo ({args.mc_n} sims, {args.mc_dist}) ---")
    pmc = parametric_monte_carlo(df, n_simulations=int(args.mc_n), distribution=args.mc_dist)
    for k, v in asdict(pmc).items():
        print(f"  {k:30s} : {v}")

    print(f"\n--- Rolling Walk-Forward ({args.wf_windows} windows) ---")
    rwf = rolling_walk_forward(df, n_windows=int(args.wf_windows), anchored=args.anchored)
    print(f"  {'n_windows':30s} : {rwf.n_windows}")
    print(f"  {'aggregate_oos_net':30s} : {rwf.aggregate_oos_net}")
    print(f"  {'aggregate_oos_sharpe':30s} : {rwf.aggregate_oos_sharpe}")
    print(f"  {'avg_efficiency':30s} : {rwf.avg_efficiency}")
    print(f"  {'walk_forward_efficiency':30s} : {rwf.walk_forward_efficiency}")
    print(f"  {'pct_profitable_oos':30s} : {rwf.pct_profitable_oos}%")
    for w in rwf.windows:
        print(f"    Window {w.window_id}: IS={w.in_sample_net:>10.2f} (Sharpe {w.in_sample_sharpe:.2f})  OOS={w.out_sample_net:>10.2f} (Sharpe {w.out_sample_sharpe:.2f})  Eff={w.efficiency:.2f}")

    print("\n--- Regime Analysis ---")
    ra = regime_analysis(df)
    for k, v in asdict(ra).items():
        if k != "interpretation":
            print(f"  {k:30s} : {v}")
    print(f"  {'interpretation':30s} : {ra.interpretation}")

    print("\n--- Benchmark Comparison ---")
    bm = benchmark_comparison(df)
    for k, v in asdict(bm).items():
        print(f"  {k:30s} : {v}")

    if "strategy" in df.columns and df["strategy"].nunique() > 1:
        print(f"\n--- Portfolio Analysis ({df['strategy'].nunique()} strategies) ---")
        pa = portfolio_analysis(df)
        for k, v in asdict(pa).items():
            if k not in ("correlations", "windows"):
                print(f"  {k:30s} : {v}")

    print("\n" + "=" * 70)
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    """Start the API server with web dashboard."""
    from nexural_research.api.app import run_server
    print(f"Starting Nexural Research server on http://{args.host}:{args.port}")
    print("API docs available at http://localhost:{}/api/docs".format(args.port))
    run_server(host=args.host, port=int(args.port), reload=args.reload)
    return 0


def _cmd_list_runs(args: argparse.Namespace) -> int:
    project = paths()
    reg = RunRegistry(project.experiments / "runs.duckdb")
    df = reg.list_runs(limit=int(args.limit))
    # Avoid rich dependency here; keep it simple.
    if df.empty:
        print("(no runs)")
        return 0
    # Pretty print CSV-ish.
    print(df.to_string(index=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="nexural-research", description="Nexural research utilities")
    sub = p.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Ingest a NinjaTrader export CSV (Trades / Executions / Optimization)")
    ingest.add_argument("--input", "-i", help="Path to NinjaTrader CSV export")
    ingest.add_argument("--output", "-o", help="Output path (.parquet or .csv)")
    ingest.add_argument("--run-id", help="Optional run id (default: timestamp-based)")
    ingest.add_argument("--no-registry", action="store_true", help="Do not record run in DuckDB registry")
    ingest.set_defaults(func=_cmd_ingest)

    report = sub.add_parser("report", help="Generate HTML report (Trades export)")
    report.add_argument("--input", "-i", help="Path to NinjaTrader Trades CSV export")
    report.add_argument("--out-dir", "-o", help="Output directory for report (default: reports/<run_id>)")
    report.add_argument("--title", help="Report title")
    report.add_argument("--run-id", help="Optional run id (default: timestamp-based)")
    report.add_argument("--no-registry", action="store_true", help="Do not record run in DuckDB registry")
    report.set_defaults(func=_cmd_report)

    runs = sub.add_parser("runs", help="List registered runs")
    runs.add_argument("--limit", default=50)
    runs.set_defaults(func=_cmd_list_runs)

    compare = sub.add_parser("compare", help="Compare trade metrics between two runs")
    compare.add_argument("--run-a", required=True)
    compare.add_argument("--run-b", required=True)
    compare.set_defaults(func=_cmd_compare)

    execq = sub.add_parser("execq", help="Execution quality metrics (Executions export)")
    execq.add_argument("--input", "-i", help="Path to NinjaTrader Executions CSV export")
    execq.add_argument("--run-id", help="Optional run id (default: timestamp-based)")
    execq.add_argument("--no-registry", action="store_true", help="Do not record run in DuckDB registry")
    execq.set_defaults(func=_cmd_execq)

    robust = sub.add_parser("robust", help="Robustness analytics (Trades export)")
    robust.add_argument("--input", "-i", help="Path to NinjaTrader Trades CSV export")
    robust.add_argument("--mc-n", default=1000, help="Monte Carlo permutations")
    robust.add_argument("--seed", default=42, help="Random seed")
    robust.add_argument("--split", default=0.7, help="Walk-forward split fraction")
    robust.set_defaults(func=_cmd_robust)

    # --- New: Full institutional analysis ---
    analyze = sub.add_parser("analyze", help="Full institutional-grade analysis suite")
    analyze.add_argument("--input", "-i", help="Path to NinjaTrader Trades CSV export")
    analyze.add_argument("--risk-free-rate", default=0.0, help="Annual risk-free rate (e.g. 0.05 for 5%%)")
    analyze.add_argument("--mc-n", default=5000, help="Monte Carlo simulations")
    analyze.add_argument("--mc-dist", default="empirical", choices=["empirical", "normal", "t"], help="MC distribution")
    analyze.add_argument("--n-trials", default=100, help="Number of trials for Deflated Sharpe Ratio")
    analyze.add_argument("--wf-windows", default=5, help="Walk-forward windows")
    analyze.add_argument("--anchored", action="store_true", help="Use anchored walk-forward")
    analyze.set_defaults(func=_cmd_analyze)

    # --- New: API server ---
    serve = sub.add_parser("serve", help="Start the web API server & dashboard")
    serve.add_argument("--host", default="0.0.0.0", help="Server host")
    serve.add_argument("--port", default=8000, help="Server port")
    serve.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    serve.set_defaults(func=_cmd_serve)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
