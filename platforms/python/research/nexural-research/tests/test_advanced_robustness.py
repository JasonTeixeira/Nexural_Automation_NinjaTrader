"""Tests for the advanced robustness module."""

import numpy as np
import pandas as pd

from nexural_research.analyze.advanced_robustness import (
    block_bootstrap_monte_carlo,
    deflated_sharpe_ratio,
    parametric_monte_carlo,
    regime_analysis,
    rolling_walk_forward,
)


def _make_trades(profits: list[float]) -> pd.DataFrame:
    n = len(profits)
    base = pd.Timestamp("2025-01-01 09:30:00")
    return pd.DataFrame({
        "profit": profits,
        "exit_time": [base + pd.Timedelta(hours=i) for i in range(n)],
        "strategy": "Test",
    })


class TestParametricMonteCarlo:
    def test_empirical(self):
        df = _make_trades([100, -50, 80, -30, 60] * 20)
        result = parametric_monte_carlo(df, n_simulations=100, distribution="empirical", seed=42)
        assert result.n_simulations == 100
        assert result.prob_profitable > 0

    def test_normal(self):
        df = _make_trades([100, -50, 80, -30, 60] * 20)
        result = parametric_monte_carlo(df, n_simulations=100, distribution="normal", seed=42)
        assert result.distribution == "normal"
        assert result.final_equity_p50 != 0

    def test_t_distribution(self):
        df = _make_trades([100, -50, 80, -30, 60] * 20)
        result = parametric_monte_carlo(df, n_simulations=100, distribution="t", seed=42)
        assert result.distribution == "t"

    def test_empty(self):
        df = _make_trades([])
        result = parametric_monte_carlo(df, n_simulations=10)
        assert result.n_simulations == 0.0 or result.prob_profitable == 0.0


class TestBlockBootstrap:
    def test_basic(self):
        profits = [100, -50, 80, -30, 60, -20, 40, 90, -10, 70] * 5
        df = _make_trades(profits)
        result = block_bootstrap_monte_carlo(df, n_simulations=100, seed=42)
        assert result.n_simulations == 100
        assert result.block_size >= 3
        assert result.sharpe_ci_lower <= result.sharpe_ci_upper

    def test_small_sample(self):
        df = _make_trades([100, -50])
        result = block_bootstrap_monte_carlo(df, n_simulations=10)
        assert result.sharpe_mean == 0.0  # too few trades


class TestRollingWalkForward:
    def test_basic(self):
        profits = [100, -50, 80, -30, 60, -20, 40, 90, -10, 70] * 10
        df = _make_trades(profits)
        result = rolling_walk_forward(df, n_windows=3)
        assert result.n_windows > 0
        assert len(result.windows) > 0
        for w in result.windows:
            assert w.in_sample_n > 0
            assert w.out_sample_n > 0

    def test_anchored(self):
        profits = [100, -50, 80, -30] * 20
        df = _make_trades(profits)
        result = rolling_walk_forward(df, n_windows=3, anchored=True)
        assert result.anchored is True

    def test_insufficient_data(self):
        df = _make_trades([100, -50])
        result = rolling_walk_forward(df, n_windows=5)
        assert result.n_windows == 0


class TestDeflatedSharpe:
    def test_strong_strategy(self):
        rng = np.random.default_rng(42)
        # Moderate Sharpe to avoid numerical edge cases
        profits = (rng.normal(10, 50, 200)).tolist()
        df = _make_trades(profits)
        result = deflated_sharpe_ratio(df, n_trials=5)
        assert result.observed_sharpe > 0
        assert np.isfinite(result.p_value)
        assert 0 <= result.p_value <= 1

    def test_weak_strategy_many_trials(self):
        rng = np.random.default_rng(42)
        profits = (rng.normal(5, 100, 50)).tolist()
        df = _make_trades(profits)
        result = deflated_sharpe_ratio(df, n_trials=1000)
        # Weak strategy with many trials should NOT survive
        assert result.is_significant is False

    def test_insufficient_data(self):
        df = _make_trades([100])
        result = deflated_sharpe_ratio(df)
        assert "insufficient" in result.interpretation


class TestRegimeAnalysis:
    def test_basic(self):
        rng = np.random.default_rng(42)
        # Mix of volatile and calm periods
        calm = rng.normal(10, 20, 50).tolist()
        volatile = rng.normal(-5, 100, 50).tolist()
        profits = calm + volatile
        df = _make_trades(profits)
        result = regime_analysis(df, n_regimes=3, window=10)
        assert result.n_regimes > 0
        assert len(result.regime_labels) > 0
        assert result.current_regime != "unknown"

    def test_insufficient_data(self):
        df = _make_trades([100, -50, 80])
        result = regime_analysis(df, window=20)
        assert "insufficient" in result.interpretation
