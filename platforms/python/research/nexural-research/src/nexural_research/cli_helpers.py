from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path


def default_run_id(prefix: str = "run") -> str:
    return f"{prefix}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"


def ensure_parent_dir(path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
