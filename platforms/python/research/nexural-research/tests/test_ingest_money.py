from __future__ import annotations

from nexural_research.ingest.nt_csv import parse_money


def test_parse_money() -> None:
    assert parse_money("$94.24") == 94.24
    assert parse_money("($65.76)") == -65.76
    assert parse_money("") == 0.0
