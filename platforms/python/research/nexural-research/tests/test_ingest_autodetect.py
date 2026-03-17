from __future__ import annotations

from pathlib import Path

import pandas as pd

from nexural_research.ingest.nt_executions_csv import is_likely_executions_export


def test_autodetect_executions_sample() -> None:
    here = Path(__file__).resolve().parent
    root = here.parent
    sample = root / "data" / "exports" / "sample_executions.csv"
    df = pd.read_csv(sample, nrows=5)
    assert is_likely_executions_export(df) is True


def test_autodetect_trades_sample() -> None:
    here = Path(__file__).resolve().parent
    root = here.parent
    sample = root / "data" / "exports" / "sample_trades.csv"
    df = pd.read_csv(sample, nrows=5)
    assert is_likely_executions_export(df) is False
