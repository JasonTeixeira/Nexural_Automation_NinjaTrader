"""Tests for portfolio analysis and benchmark comparison."""

import numpy as np
import pandas as pd

from nexural_research.analyze.portfolio import (
    benchmark_comparison,
    portfolio_analysis,
)


def _make_trades(profits: list[float], strategies: list[str] | None = None) -> pd.DataFrame:
    n = len(profits)
    base = pd.Timestamp("2025-01-01 09:30:00")
    return pd.DataFrame({
        "profit": profits,
        "exit_time": [base + pd.Timedelta(hours=i) for i in range(n)],
        "instrument": "NQ",
        "strategy": strategies or (["StratA"] * n),
    })


class TestPortfolioAnalysis:
    def test_single_strategy(self):
        df = _make_trades([100, -50, 80, -30])
        result = portfolio_analysis(df)
        assert result.n_strategies == 1

    def test_multi_strategy(self):
        profits = [100, -50, 80, -30, 60, -20]
        strats = ["Fade", "Fade", "Fade", "Momentum", "Momentum", "Momentum"]
        df = _make_trades(profits, strats)
        result = portfolio_analysis(df)
        assert result.n_strategies == 2
        assert len(result.strategy_names) == 2
        assert len(result.individual_sharpes) == 2
        assert len(result.correlation_matrix) == 2
        assert len(result.correlations) == 1  # 1 pair
        assert len(result.optimal_weights) == 2
        assert abs(sum(result.optimal_weights) - 1.0) < 0.01

    def test_correlation_bounds(self):
        profits = [100, -50, 80, -30, 60, -20] * 5
        strats = (["A", "A", "A", "B", "B", "B"]) * 5
        df = _make_trades(profits, strats)
        result = portfolio_analysis(df)
        for corr in result.correlations:
            assert -1.0 <= corr.pearson_r <= 1.0
            assert -1.0 <= corr.spearman_r <= 1.0


class TestBenchmarkComparison:
    def test_profitable_vs_random(self):
        rng = np.random.default_rng(42)
        profits = (rng.normal(50, 30, 100)).tolist()
        df = _make_trades(profits)
        result = benchmark_comparison(df, n_random_sims=200, seed=42)
        assert result.strategy_net > 0
        assert result.pct_better_than_random > 50  # should beat most random

    def test_losing_vs_random(self):
        rng = np.random.default_rng(42)
        profits = (rng.normal(-50, 30, 100)).tolist()
        df = _make_trades(profits)
        result = benchmark_comparison(df, n_random_sims=200, seed=42)
        assert result.strategy_net < 0
        assert result.pct_better_than_random < 50

    def test_empty(self):
        df = _make_trades([])
        result = benchmark_comparison(df)
        assert result.strategy_net == 0.0
