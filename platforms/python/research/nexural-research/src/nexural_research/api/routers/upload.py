"""Upload and session management endpoints."""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from nexural_research.api.auth import AuthContext, require_auth

from nexural_research.api.compat import adapt_sessions
from nexural_research.api.sessions import MAX_SESSIONS, MAX_UPLOAD_SIZE, delete_persisted_session, persist_session, sessions
from nexural_research.ingest.detect import ExportKind, detect_export_kind
from nexural_research.ingest.multi_format import detect_and_load
from nexural_research.ingest.nt_csv import load_nt_trades_csv
from nexural_research.ingest.nt_executions_csv import load_nt_executions_csv
from nexural_research.ingest.nt_optimization_csv import load_nt_optimization_csv

router = APIRouter(tags=["sessions"])


async def _parse_upload_from_bytes(content: bytes, filename: str) -> tuple[pd.DataFrame, str]:
    """Parse uploaded CSV bytes, auto-detecting the export type."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="wb") as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        detected = detect_export_kind(tmp_path)
        kind = detected.kind

        if kind == ExportKind.TRADES:
            df = load_nt_trades_csv(tmp_path)
        elif kind == ExportKind.EXECUTIONS:
            df = load_nt_executions_csv(tmp_path)
        elif kind == ExportKind.OPTIMIZATION:
            df = load_nt_optimization_csv(tmp_path)
        else:
            # Try multi-format auto-detection (TradingView, MetaTrader, IB, TradeStation)
            try:
                df, platform = detect_and_load(tmp_path)
                if "profit" in df.columns:
                    kind = ExportKind.TRADES
                    from nexural_research.utils.logging import info
                    info(f"Auto-detected {platform} format")
                else:
                    raise HTTPException(400, f"Could not detect export type. Supported: NinjaTrader, TradingView, MetaTrader, Interactive Brokers, TradeStation")
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(400, f"Could not detect export type: {detected.reason}")
    finally:
        tmp_path.unlink(missing_ok=True)

    return df, kind.value


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...), session_id: str = Query(default="default"), auth: AuthContext = Depends(require_auth)):
    """Upload a NinjaTrader CSV export. Auto-detects Trades/Executions/Optimization."""
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            413,
            f"File too large ({len(content) / 1024 / 1024:.1f}MB). Maximum is {MAX_UPLOAD_SIZE // 1024 // 1024}MB.",
        )
    if session_id not in sessions and len(sessions) >= MAX_SESSIONS:
        raise HTTPException(429, f"Maximum sessions ({MAX_SESSIONS}) reached. Delete old sessions first.")

    df, kind = await _parse_upload_from_bytes(content, file.filename or "upload.csv")

    sessions[session_id] = {
        "df": df,
        "kind": kind,
        "filename": file.filename,
        "n_rows": len(df),
        "columns": list(df.columns),
        "created_at": time.time(),
    }

    # Persist to disk for restart survival
    persist_session(session_id, df, kind, file.filename)

    return {
        "session_id": session_id,
        "kind": kind,
        "filename": file.filename,
        "n_rows": len(df),
        "columns": list(df.columns),
        "preview": json.loads(df.head(10).to_json(orient="records", date_format="iso")),
    }


@router.get("/sessions")
def list_sessions():
    """List active analysis sessions."""
    raw = {
        sid: {"kind": s["kind"], "filename": s["filename"], "n_rows": s["n_rows"]}
        for sid, s in sessions.items()
    }
    return adapt_sessions(raw, sessions)


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    sessions.pop(session_id, None)
    delete_persisted_session(session_id)
    return {"deleted": session_id}
