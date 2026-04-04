"""Tests for the strategy improvement engine."""

import pandas as pd

from nexural_research.analyze.improvements import (
    generate_improvement_report,
    StrategyImprovementReport,
)


def _make_trades(profits: list[float], hours: list[int] | None = None) -> pd.DataFrame:
    n = len(profits)
    base = pd.Timestamp("2025-01-01 09:30:00")
    if hours is None:
        hours = [(9 + i % 8) for i in range(n)]
    return pd.DataFrame({
        "profit": profits,
        "entry_time": [base + pd.Timedelta(days=i // 8, hours=h) for i, h in enumerate(hours)],
        "exit_time": [base + pd.Timedelta(days=i // 8, hours=h, minutes=15) for i, h in enumerate(hours)],
        "instrument": "NQ",
        "strategy": "Test",
        "commission": [4.5] * n,
    })


class TestImprovementReport:
    def test_returns_report(self):
        df = _make_trades([100, -50, 80, -30, 60, -20, 90, -40, 70, -10])
        report = generate_improvement_report(df)
        assert isinstance(report, StrategyImprovementReport)
        assert report.overall_grade in ("A", "A-", "B+", "B", "B-", "C", "C-", "D", "F")
        assert len(report.grade_explanation) > 0

    def test_losing_strategy_gets_bad_grade(self):
        df = _make_trades([-100, -50, 10, -80, -60, 5, -90, -30, 15, -70])
        report = generate_improvement_report(df)
        assert report.overall_grade in ("D", "F")
        # Should have critical recommendations
        critical = [r for r in report.recommendations if r.priority == "critical"]
        assert len(critical) > 0

    def test_winning_strategy_gets_good_grade(self):
        df = _make_trades([100, 50, -30, 80, 60, -20, 90, 40, -10, 70] * 5)
        report = generate_improvement_report(df)
        assert report.overall_grade in ("A", "A-", "B+", "B")

    def test_time_filter_detected(self):
        # Good profits in morning, losses in afternoon
        profits = [100, 100, -200, -200] * 5
        hours = [9, 10, 14, 15] * 5
        df = _make_trades(profits, hours)
        report = generate_improvement_report(df)
        if report.time_filter:
            # Should suggest removing losing hours
            assert len(report.time_filter.hours_to_remove) > 0 or len(report.time_filter.days_to_remove) > 0

    def test_loss_clusters_detected(self):
        # 5 consecutive losses
        profits = [100, -50, -50, -50, -50, -50, 100]
        df = _make_trades(profits)
        report = generate_improvement_report(df)
        assert len(report.loss_clusters) > 0
        assert report.loss_clusters[0].n_trades >= 3

    def test_drawdown_recovery(self):
        df = _make_trades([100, -200, -100, 50, 50, 50, 100])
        report = generate_improvement_report(df)
        assert report.drawdown_recovery.n_drawdowns > 0
        assert report.drawdown_recovery.deepest_drawdown < 0

    def test_commission_impact(self):
        df = _make_trades([10, -5, 10, -5, 10])  # Small profits, $4.50 commission each
        report = generate_improvement_report(df)
        assert report.commission_impact_pct > 0

    def test_small_sample_warning(self):
        df = _make_trades([100, -50, 80])
        report = generate_improvement_report(df)
        sample_recs = [r for r in report.recommendations if r.category == "data_quality"]
        assert len(sample_recs) > 0

    def test_recommendations_sorted_by_priority(self):
        df = _make_trades([-100, -50, 10, -80, -60, 5])
        report = generate_improvement_report(df)
        priorities = [r.priority for r in report.recommendations]
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        values = [order.get(p, 4) for p in priorities]
        assert values == sorted(values)

    def test_mae_mfe_without_data(self):
        df = _make_trades([100, -50, 80])
        report = generate_improvement_report(df)
        assert report.mae_mfe.has_mae_mfe is False

    def test_mae_mfe_with_data(self):
        df = _make_trades([100, -50, 80, -30, 60])
        df["mae"] = [10, 50, 15, 30, 8]
        df["mfe"] = [120, 20, 100, 10, 80]
        report = generate_improvement_report(df)
        assert report.mae_mfe.has_mae_mfe is True
        assert report.mae_mfe.avg_mae > 0
        assert report.mae_mfe.avg_mfe > 0
