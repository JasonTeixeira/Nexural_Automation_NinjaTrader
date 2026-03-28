from __future__ import annotations

from pathlib import Path

from nexural_research.ingest.detect import ExportKind, detect_export_kind


def test_detect_trades_export() -> None:
    root = Path(__file__).resolve().parent.parent
    p = root / "data" / "exports" / "sample_trades.csv"
    d = detect_export_kind(p)
    assert d.kind == ExportKind.TRADES


def test_detect_executions_export() -> None:
    root = Path(__file__).resolve().parent.parent
    p = root / "data" / "exports" / "sample_executions.csv"
    d = detect_export_kind(p)
    assert d.kind == ExportKind.EXECUTIONS


def test_detect_optimization_export() -> None:
    root = Path(__file__).resolve().parent.parent
    p = root / "data" / "exports" / "sample_optimization.csv"
    d = detect_export_kind(p)
    assert d.kind == ExportKind.OPTIMIZATION
