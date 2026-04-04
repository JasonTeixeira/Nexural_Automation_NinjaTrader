"""Tests for CSV column alias mapping — critical for supporting various NinjaTrader export formats."""


import pandas as pd
import pytest

from nexural_research.ingest.nt_csv import load_nt_trades_csv, _apply_column_aliases, _normalize_cols


class TestNormalizeCols:
    def test_lowercases(self):
        assert _normalize_cols(["Profit", "NET PNL"]) == ["profit", "net_pnl"]

    def test_strips_dots(self):
        assert _normalize_cols(["Market Pos."]) == ["market_pos"]

    def test_replaces_spaces_and_dashes(self):
        assert _normalize_cols(["entry-time", "exit time"]) == ["entry_time", "exit_time"]


class TestApplyColumnAliases:
    def test_net_pnl_mapped(self):
        df = pd.DataFrame({"net_pnl": [100, -50], "symbol": ["NQ", "NQ"]})
        result = _apply_column_aliases(df)
        assert "profit" in result.columns
        assert "instrument" in result.columns

    def test_pnl_mapped(self):
        df = pd.DataFrame({"pnl": [100], "ticker": ["ES"]})
        result = _apply_column_aliases(df)
        assert "profit" in result.columns
        assert "instrument" in result.columns

    def test_side_mapped(self):
        df = pd.DataFrame({"side": ["BUY"], "qty": [1]})
        result = _apply_column_aliases(df)
        assert "market_pos" in result.columns
        assert "quantity" in result.columns

    def test_canonical_names_preserved(self):
        df = pd.DataFrame({"profit": [100], "instrument": ["NQ"]})
        result = _apply_column_aliases(df)
        assert list(result.columns) == ["profit", "instrument"]

    def test_no_double_mapping(self):
        # If both profit and net_pnl exist, profit should stay
        df = pd.DataFrame({"profit": [100], "net_pnl": [95]})
        result = _apply_column_aliases(df)
        assert result["profit"].iloc[0] == 100  # original profit kept


class TestLoadNtTradesCsv:
    def test_standard_nt_format(self, tmp_path):
        csv = tmp_path / "trades.csv"
        csv.write_text(
            "Trade Number,Instrument,Entry time,Exit time,Profit,Commission\n"
            "1,NQ,2025-01-01 09:30,2025-01-01 09:45,94.24,5.76\n"
            "2,NQ,2025-01-01 10:00,2025-01-01 10:15,-65.76,5.76\n"
        )
        df = load_nt_trades_csv(csv)
        assert "profit" in df.columns
        assert "instrument" in df.columns
        assert len(df) == 2
        assert df["profit"].iloc[0] == 94.24

    def test_custom_column_format(self, tmp_path):
        csv = tmp_path / "custom.csv"
        csv.write_text(
            "trade_id,symbol,side,entry_time,exit_time,net_pnl,commission,strategy\n"
            "T1,NQ,BUY,2025-01-01 09:30,2025-01-01 09:45,195.5,4.5,Fade\n"
            "T2,NQ,SELL,2025-01-01 10:00,2025-01-01 10:15,-204.5,4.5,Fade\n"
        )
        df = load_nt_trades_csv(csv)
        assert "profit" in df.columns
        assert "instrument" in df.columns
        assert "market_pos" in df.columns
        assert "trade_number" in df.columns
        assert df["profit"].iloc[0] == 195.5

    def test_gross_pnl_with_commission(self, tmp_path):
        csv = tmp_path / "gross.csv"
        csv.write_text(
            "trade_id,symbol,entry_time,exit_time,gross_pnl,commission\n"
            "T1,NQ,2025-01-01 09:30,2025-01-01 09:45,200,4.5\n"
        )
        df = load_nt_trades_csv(csv)
        assert "profit" in df.columns
        # profit should be gross - commission
        assert df["profit"].iloc[0] == pytest.approx(195.5, abs=0.1)

    def test_duration_computed(self, tmp_path):
        csv = tmp_path / "dur.csv"
        csv.write_text(
            "trade_id,symbol,entry_time,exit_time,net_pnl\n"
            "T1,NQ,2025-01-01 09:30:00,2025-01-01 09:45:00,100\n"
        )
        df = load_nt_trades_csv(csv)
        assert "duration_seconds" in df.columns
        assert df["duration_seconds"].iloc[0] == 900.0  # 15 minutes
