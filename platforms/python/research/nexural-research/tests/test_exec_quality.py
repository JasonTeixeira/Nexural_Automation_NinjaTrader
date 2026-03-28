from __future__ import annotations

from pathlib import Path

from nexural_research.analyze.execution_quality import execution_quality_from_executions
from nexural_research.ingest.nt_executions_csv import load_nt_executions_csv


def test_execution_quality_smoke() -> None:
    root = Path(__file__).resolve().parent.parent
    p = root / "data" / "exports" / "sample_executions.csv"
    df = load_nt_executions_csv(p)
    m = execution_quality_from_executions(df)
    assert m.n_exec == 4
