from __future__ import annotations

from pathlib import Path

from nexural_research.ingest.nt_csv import load_nt_trades_csv
from nexural_research.report.html import build_trades_report_html


def test_build_report_html_smoke() -> None:
    here = Path(__file__).resolve().parent
    root = here.parent
    sample = root / "data" / "exports" / "sample_trades.csv"
    df = load_nt_trades_csv(sample)
    html = build_trades_report_html(df, title="Test Report")
    assert "<!doctype html>" in html
    assert "Equity Curve" in html
    assert "PnL Heatmap" in html
