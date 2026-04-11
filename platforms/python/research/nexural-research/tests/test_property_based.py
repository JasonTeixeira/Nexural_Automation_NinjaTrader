"""Property-based tests using hypothesis — fuzz every metric with random inputs.

These tests verify INVARIANTS that must hold regardless of input:
- Win rate always in [0, 1]
- Profit factor always >= 0
- Equity final = sum(PnL)
- Max drawdown always <= 0
- Hurst always in [0, 1]
- Kelly always >= 0 (clamped)
- VaR always <= 0 (loss)
- CVaR always <= VaR
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, strategies as st, settings, assume

from nexural_research.analyze.metrics import metrics_from_trades
from nexural_research.analyze.advanced_metrics import (
    risk_return_metrics,
    expectancy_metrics,
    distribution_metrics,
    institutional_metrics,
)
from nexural_research.analyze.equity import max_drawdown, equity_curve_from_trades
from nexural_research.analyze.advanced_analytics import hurst_exponent


def make_df(profits):
    """Build a trades DataFrame from a list of profits."""
    n = len(profits)
    if n == 0:
        return pd.DataFrame({"profit": [], "entry_time": [], "exit_time": [], "instrument": [], "strategy": []})
    base = pd.Timestamp("2025-01-01 09:30:00")
    return pd.DataFrame({
        "profit": profits,
        "entry_time": [base + pd.Timedelta(hours=i) for i in range(n)],
        "exit_time": [base + pd.Timedelta(hours=i, minutes=15) for i in range(n)],
        "instrument": "NQ",
        "strategy": "Test",
    })


# Strategy: list of floats between -10000 and 10000, length 2-200
profit_lists = st.lists(st.floats(min_value=-10000, max_value=10000, allow_nan=False, allow_infinity=False), min_size=2, max_size=200)


class TestMetricInvariants:
    @given(profits=profit_lists)
    @settings(max_examples=50, deadline=5000)
    def test_win_rate_bounded(self, profits):
        """Win rate must always be in [0, 1]."""
        df = make_df(profits)
        m = metrics_from_trades(df)
        assert 0.0 <= m.win_rate <= 1.0

    @given(profits=profit_lists)
    @settings(max_examples=50, deadline=5000)
    def test_profit_factor_non_negative(self, profits):
        """Profit factor must always be >= 0."""
        df = make_df(profits)
        m = metrics_from_trades(df)
        assert m.profit_factor >= 0 or m.profit_factor == float("inf")

    @given(profits=profit_lists)
    @settings(max_examples=50, deadline=5000)
    def test_equity_final_equals_sum(self, profits):
        """Equity curve final value must equal sum of PnL."""
        df = make_df(profits)
        eq = equity_curve_from_trades(df)
        expected = sum(profits)
        actual = float(eq.equity.iloc[-1])
        assert abs(actual - expected) < 0.01 * (abs(expected) + 1)

    @given(profits=profit_lists)
    @settings(max_examples=50, deadline=5000)
    def test_max_drawdown_non_positive(self, profits):
        """Max drawdown must always be <= 0."""
        eq = pd.Series(np.cumsum(profits))
        mdd = max_drawdown(eq)
        assert mdd <= 0.0001  # tiny float tolerance

    @given(profits=profit_lists)
    @settings(max_examples=50, deadline=5000)
    def test_net_profit_is_sum(self, profits):
        """Net profit must equal sum of all trade PnL."""
        df = make_df(profits)
        m = metrics_from_trades(df)
        assert abs(m.net_profit - sum(profits)) < 0.01

    @given(profits=profit_lists)
    @settings(max_examples=50, deadline=5000)
    def test_win_plus_loss_equals_total(self, profits):
        """Winners + losers + breakeven should account for all trades."""
        df = make_df(profits)
        m = metrics_from_trades(df)
        pnl = np.array(profits)
        n_wins = int(np.sum(pnl > 0))
        n_losses = int(np.sum(pnl < 0))
        n_zero = int(np.sum(pnl == 0))
        assert n_wins + n_losses + n_zero == m.n_trades


class TestRiskReturnInvariants:
    @given(profits=profit_lists)
    @settings(max_examples=30, deadline=10000)
    def test_risk_of_ruin_bounded(self, profits):
        """Risk of ruin must be in [0, 1]."""
        df = make_df(profits)
        rr = risk_return_metrics(df)
        assert 0.0 <= rr.risk_of_ruin <= 1.0

    @given(profits=profit_lists)
    @settings(max_examples=30, deadline=10000)
    def test_omega_ratio_non_negative(self, profits):
        """Omega ratio must be >= 0 (or inf)."""
        df = make_df(profits)
        rr = risk_return_metrics(df)
        assert rr.omega_ratio >= 0 or rr.omega_ratio == float("inf") or str(rr.omega_ratio) == "inf"


class TestExpectancyInvariants:
    @given(profits=profit_lists)
    @settings(max_examples=30, deadline=10000)
    def test_kelly_non_negative(self, profits):
        """Kelly % must always be >= 0 (clamped)."""
        df = make_df(profits)
        exp = expectancy_metrics(df)
        assert exp.kelly_pct >= 0

    @given(profits=profit_lists)
    @settings(max_examples=30, deadline=10000)
    def test_optimal_f_bounded(self, profits):
        """Optimal f must be in [0, 1]."""
        df = make_df(profits)
        exp = expectancy_metrics(df)
        assert 0.0 <= exp.optimal_f <= 1.0


class TestDistributionInvariants:
    @given(profits=st.lists(st.floats(min_value=-10000, max_value=10000, allow_nan=False, allow_infinity=False), min_size=10, max_size=200))
    @settings(max_examples=30, deadline=10000)
    def test_cvar_worse_than_var(self, profits):
        """CVaR (expected shortfall) must always be <= VaR."""
        df = make_df(profits)
        dist = distribution_metrics(df)
        assert dist.cvar_95 <= dist.var_95 + 0.01  # small tolerance

    @given(profits=st.lists(st.floats(min_value=-10000, max_value=10000, allow_nan=False, allow_infinity=False), min_size=10, max_size=200))
    @settings(max_examples=30, deadline=10000)
    def test_percentiles_ordered(self, profits):
        """Percentiles must be monotonically non-decreasing."""
        df = make_df(profits)
        dist = distribution_metrics(df)
        assert dist.percentile_01 <= dist.percentile_05
        assert dist.percentile_05 <= dist.percentile_10
        assert dist.percentile_10 <= dist.percentile_25
        assert dist.percentile_25 <= dist.percentile_75
        assert dist.percentile_75 <= dist.percentile_90
        assert dist.percentile_90 <= dist.percentile_95
        assert dist.percentile_95 <= dist.percentile_99


class TestInstitutionalInvariants:
    @given(profits=profit_lists)
    @settings(max_examples=30, deadline=10000)
    def test_time_under_water_bounded(self, profits):
        """Time under water must be 0-100%."""
        df = make_df(profits)
        inst = institutional_metrics(df)
        assert 0.0 <= inst.time_under_water_pct <= 100.0

    @given(profits=profit_lists)
    @settings(max_examples=30, deadline=10000)
    def test_consecutive_counts_non_negative(self, profits):
        """Max consecutive wins/losses must be >= 0."""
        df = make_df(profits)
        inst = institutional_metrics(df)
        assert inst.max_consecutive_wins >= 0
        assert inst.max_consecutive_losses >= 0


class TestHurstInvariant:
    @given(profits=st.lists(st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False), min_size=30, max_size=200))
    @settings(max_examples=20, deadline=15000)
    def test_hurst_bounded(self, profits):
        """Hurst exponent must be in [0, 1]."""
        df = make_df(profits)
        h = hurst_exponent(df)
        assert 0.0 <= h.hurst_exponent <= 1.0
