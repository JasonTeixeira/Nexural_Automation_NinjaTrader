from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from nexural_research.analyze.metrics import TradeMetrics
from nexural_research.analyze.execution_quality import ExecutionQualityMetrics
from nexural_research.utils.hashing import sha256_file


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    created_at: str
    kind: str
    input_path: str
    input_sha256: str
    processed_path: str | None
    report_path: str | None


class RunRegistry:
    """A minimal local run registry stored in DuckDB."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _conn(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path))

    def _init_schema(self) -> None:
        con = self._conn()
        try:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                  run_id TEXT PRIMARY KEY,
                  created_at TEXT NOT NULL,
                  kind TEXT NOT NULL,
                  input_path TEXT NOT NULL,
                  input_sha256 TEXT NOT NULL,
                  processed_path TEXT,
                  report_path TEXT
                );
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_metrics (
                  run_id TEXT PRIMARY KEY,
                  n_trades BIGINT,
                  gross_profit DOUBLE,
                  gross_loss DOUBLE,
                  net_profit DOUBLE,
                  win_rate DOUBLE,
                  profit_factor DOUBLE,
                  avg_trade DOUBLE,
                  avg_win DOUBLE,
                  avg_loss DOUBLE,
                  max_drawdown DOUBLE,
                  ulcer_index DOUBLE
                );
                """
            )

            con.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_quality_metrics (
                  run_id TEXT PRIMARY KEY,
                  n_exec BIGINT,
                  commission_sum DOUBLE,
                  profit_sum DOUBLE,
                  n_market BIGINT,
                  n_limit BIGINT,
                  n_stop BIGINT,
                  slippage_mean DOUBLE,
                  slippage_std DOUBLE
                );
                """
            )

            # Store full normalized datasets.
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS trades (
                  run_id TEXT,
                  ts TIMESTAMP,
                  instrument TEXT,
                  strategy TEXT,
                  profit DOUBLE,
                  mae DOUBLE,
                  mfe DOUBLE,
                  etd DOUBLE
                );
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS executions (
                  run_id TEXT,
                  ts TIMESTAMP,
                  instrument TEXT,
                  strategy TEXT,
                  action TEXT,
                  type TEXT,
                  quantity DOUBLE,
                  fill_price DOUBLE,
                  limit_price DOUBLE,
                  stop_price DOUBLE,
                  commission DOUBLE,
                  profit DOUBLE
                );
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS optimizations (
                  run_id TEXT,
                  strategy TEXT,
                  instrument TEXT,
                  total_net_profit DOUBLE,
                  profit_factor DOUBLE,
                  max_drawdown DOUBLE,
                  sharpe DOUBLE,
                  trades BIGINT
                );
                """
            )
        finally:
            con.close()

    def register_run(
        self,
        *,
        run_id: str,
        kind: str,
        input_path: str | Path,
        processed_path: str | Path | None = None,
        report_path: str | Path | None = None,
    ) -> RunRecord:
        inp = Path(input_path)
        record = RunRecord(
            run_id=run_id,
            created_at=datetime.now(UTC).isoformat(),
            kind=str(kind),
            input_path=str(inp),
            input_sha256=sha256_file(inp),
            processed_path=str(Path(processed_path)) if processed_path else None,
            report_path=str(Path(report_path)) if report_path else None,
        )

        con = self._conn()
        try:
            con.execute(
                """
                INSERT OR REPLACE INTO runs
                (run_id, created_at, kind, input_path, input_sha256, processed_path, report_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    record.run_id,
                    record.created_at,
                    record.kind,
                    record.input_path,
                    record.input_sha256,
                    record.processed_path,
                    record.report_path,
                ],
            )
        finally:
            con.close()
        return record

    def upsert_trade_metrics(self, run_id: str, metrics: TradeMetrics) -> None:
        d = asdict(metrics)
        con = self._conn()
        try:
            con.execute(
                """
                INSERT OR REPLACE INTO trade_metrics
                (run_id, n_trades, gross_profit, gross_loss, net_profit, win_rate, profit_factor,
                 avg_trade, avg_win, avg_loss, max_drawdown, ulcer_index)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    run_id,
                    d["n_trades"],
                    d["gross_profit"],
                    d["gross_loss"],
                    d["net_profit"],
                    d["win_rate"],
                    d["profit_factor"],
                    d["avg_trade"],
                    d["avg_win"],
                    d["avg_loss"],
                    d["max_drawdown"],
                    d["ulcer_index"],
                ],
            )
        finally:
            con.close()

    def upsert_execution_quality_metrics(self, run_id: str, metrics: ExecutionQualityMetrics) -> None:
        d = asdict(metrics)
        con = self._conn()
        try:
            con.execute(
                """
                INSERT OR REPLACE INTO execution_quality_metrics
                (run_id, n_exec, commission_sum, profit_sum, n_market, n_limit, n_stop, slippage_mean, slippage_std)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    run_id,
                    d["n_exec"],
                    d["commission_sum"],
                    d["profit_sum"],
                    d["n_market"],
                    d["n_limit"],
                    d["n_stop"],
                    d["slippage_mean"],
                    d["slippage_std"],
                ],
            )
        finally:
            con.close()

    def store_trades(self, run_id: str, df: pd.DataFrame) -> None:
        # Normalize minimal columns
        df2 = pd.DataFrame()
        df2["run_id"] = run_id
        ts_col = "exit_time" if "exit_time" in df.columns else ("entry_time" if "entry_time" in df.columns else None)
        df2["ts"] = pd.to_datetime(df[ts_col], errors="coerce") if ts_col else pd.NaT
        df2["instrument"] = df.get("instrument")
        df2["strategy"] = df.get("strategy")
        df2["profit"] = pd.to_numeric(df.get("profit"), errors="coerce")
        df2["mae"] = pd.to_numeric(df.get("mae"), errors="coerce") if "mae" in df.columns else None
        df2["mfe"] = pd.to_numeric(df.get("mfe"), errors="coerce") if "mfe" in df.columns else None
        df2["etd"] = pd.to_numeric(df.get("etd"), errors="coerce") if "etd" in df.columns else None
        con = self._conn()
        try:
            con.execute("DELETE FROM trades WHERE run_id = ?", [run_id])
            con.register("_t", df2)
            con.execute("INSERT INTO trades SELECT * FROM _t")
        finally:
            con.close()

    def store_executions(self, run_id: str, df: pd.DataFrame) -> None:
        df2 = pd.DataFrame()
        df2["run_id"] = run_id
        df2["ts"] = pd.to_datetime(df.get("time"), errors="coerce") if "time" in df.columns else pd.NaT
        df2["instrument"] = df.get("instrument")
        df2["strategy"] = df.get("strategy")
        df2["action"] = df.get("action")
        df2["type"] = df.get("type")
        df2["quantity"] = pd.to_numeric(df.get("quantity"), errors="coerce")
        df2["fill_price"] = pd.to_numeric(df.get("fill_price"), errors="coerce")
        df2["limit_price"] = pd.to_numeric(df.get("limit_price"), errors="coerce") if "limit_price" in df.columns else None
        df2["stop_price"] = pd.to_numeric(df.get("stop_price"), errors="coerce") if "stop_price" in df.columns else None
        df2["commission"] = pd.to_numeric(df.get("commission"), errors="coerce") if "commission" in df.columns else None
        df2["profit"] = pd.to_numeric(df.get("profit"), errors="coerce") if "profit" in df.columns else None
        con = self._conn()
        try:
            con.execute("DELETE FROM executions WHERE run_id = ?", [run_id])
            con.register("_e", df2)
            con.execute("INSERT INTO executions SELECT * FROM _e")
        finally:
            con.close()

    def store_optimizations(self, run_id: str, df: pd.DataFrame) -> None:
        df2 = pd.DataFrame()
        df2["run_id"] = run_id
        df2["strategy"] = df.get("strategy")
        df2["instrument"] = df.get("instrument")
        # best-effort mapping
        df2["total_net_profit"] = pd.to_numeric(df.get("total_net_profit"), errors="coerce")
        df2["profit_factor"] = pd.to_numeric(df.get("profit_factor"), errors="coerce")
        df2["max_drawdown"] = pd.to_numeric(df.get("max_drawdown"), errors="coerce")
        df2["sharpe"] = pd.to_numeric(df.get("sharpe"), errors="coerce")
        df2["trades"] = pd.to_numeric(df.get("trades"), errors="coerce")
        con = self._conn()
        try:
            con.execute("DELETE FROM optimizations WHERE run_id = ?", [run_id])
            con.register("_o", df2)
            con.execute("INSERT INTO optimizations SELECT * FROM _o")
        finally:
            con.close()

    def list_runs(self, limit: int = 50) -> pd.DataFrame:
        con = self._conn()
        try:
            return con.execute(
                "SELECT * FROM runs ORDER BY created_at DESC LIMIT ?",
                [int(limit)],
            ).fetchdf()
        finally:
            con.close()

    def get_trade_metrics(self, run_id: str) -> dict[str, Any] | None:
        con = self._conn()
        try:
            df = con.execute("SELECT * FROM trade_metrics WHERE run_id = ?", [run_id]).fetchdf()
            if df is None or df.empty:
                return None
            return {str(k): (v if not pd.isna(v) else None) for k, v in df.iloc[0].to_dict().items()}
        finally:
            con.close()
