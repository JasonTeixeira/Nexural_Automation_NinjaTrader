from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import pandas as pd

from nexural_research.ingest.nt_executions_csv import is_likely_executions_export
from nexural_research.utils.logging import info


class ExportKind(str, Enum):
    TRADES = "trades"
    EXECUTIONS = "executions"
    OPTIMIZATION = "optimization"


@dataclass(frozen=True)
class DetectedExport:
    kind: ExportKind
    reason: str


def _norm_cols(cols: list[str]) -> set[str]:
    out: set[str] = set()
    for c in cols:
        c2 = str(c).strip().lower().replace(".", "").replace(" ", "_").replace("-", "_")
        out.add(c2)
    return out


def detect_export_kind(path: str | Path) -> DetectedExport:
    """Best-effort detection of NinjaTrader export type.

    Supports:
    - Strategy Analyzer Trades export
    - Executions export
    - Optimization results export (best-effort heuristics; formats can vary)
    """

    p = Path(path)
    info(f"Detecting export type: {p.name}")

    # Read a small sample for classification.
    df = pd.read_csv(p, nrows=50)
    cols = _norm_cols(list(df.columns))

    # Executions sample detector already exists.
    if is_likely_executions_export(df):
        return DetectedExport(kind=ExportKind.EXECUTIONS, reason="has required executions columns")

    # Trades export heuristics
    if {"trade_number", "entry_time", "exit_time", "profit"}.issubset(cols):
        return DetectedExport(kind=ExportKind.TRADES, reason="has required trades columns")

    # Optimization results: formats vary. We look for common telltales.
    # Examples seen in NT exports include columns like: 'Parameter', 'Value', 'Fitness',
    # 'Total net profit', 'Profit factor', 'Max drawdown', 'Sharpe', etc.
    optimization_markers = {
        "total_net_profit",
        "profit_factor",
        "max_drawdown",
        "sharpe",
        "parameter",
        "fitness",
        "generation",
        "iteration",
        "optimization",
    }
    if len(cols.intersection(optimization_markers)) >= 2:
        return DetectedExport(kind=ExportKind.OPTIMIZATION, reason="matched optimization markers")

    # Fallback: treat as trades (most common) but caller should validate.
    return DetectedExport(kind=ExportKind.TRADES, reason="fallback")
