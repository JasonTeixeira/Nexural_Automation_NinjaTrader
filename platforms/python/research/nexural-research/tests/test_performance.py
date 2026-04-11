"""API response time benchmarks — every endpoint must respond under target latency.

Targets:
- Health endpoints: < 50ms
- Simple metrics: < 200ms
- Complex analysis: < 2000ms
- Monte Carlo/Bootstrap: < 5000ms
- Export: < 3000ms
"""

import time
import io
import numpy as np
import pytest
from fastapi.testclient import TestClient
from nexural_research.api.app import app


@pytest.fixture(scope="module")
def client():
    c = TestClient(app)
    csv = "trade_id,symbol,entry_time,exit_time,net_pnl,strategy\n" + "\n".join(
        f"T{i},NQ,2025-01-{1+i//10:02d} {9+i%8}:30,2025-01-{1+i//10:02d} {9+i%8}:45,{(-1)**i*(50+i*3):.2f},PerfStrat"
        for i in range(100)
    )
    c.post("/api/upload?session_id=perf_test", files={"file": ("perf.csv", io.BytesIO(csv.encode()), "text/csv")})
    return c


def timed_get(client, url, max_ms):
    """Call endpoint and assert response time under threshold."""
    start = time.perf_counter()
    r = client.get(url)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert r.status_code == 200, f"{url} returned {r.status_code}"
    assert elapsed_ms < max_ms, f"{url} took {elapsed_ms:.0f}ms (limit: {max_ms}ms)"
    return elapsed_ms


class TestHealthPerformance:
    def test_health_fast(self, client):
        timed_get(client, "/api/health", 100)

    def test_health_ready_fast(self, client):
        timed_get(client, "/api/health/ready", 100)

    def test_sessions_fast(self, client):
        timed_get(client, "/api/sessions", 100)


class TestMetricsPerformance:
    def test_core_metrics(self, client):
        timed_get(client, "/api/analysis/metrics?session_id=perf_test", 500)

    def test_risk_return(self, client):
        timed_get(client, "/api/analysis/risk-return?session_id=perf_test", 500)

    def test_expectancy(self, client):
        timed_get(client, "/api/analysis/expectancy?session_id=perf_test", 500)

    def test_institutional(self, client):
        timed_get(client, "/api/analysis/institutional?session_id=perf_test", 500)

    def test_dependency(self, client):
        timed_get(client, "/api/analysis/dependency?session_id=perf_test", 500)

    def test_distribution(self, client):
        timed_get(client, "/api/analysis/distribution?session_id=perf_test", 500)

    def test_improvements(self, client):
        timed_get(client, "/api/analysis/improvements?session_id=perf_test", 2000)

    def test_hurst(self, client):
        timed_get(client, "/api/analysis/hurst?session_id=perf_test", 1000)

    def test_acf(self, client):
        timed_get(client, "/api/analysis/acf?session_id=perf_test", 500)

    def test_information_ratio(self, client):
        timed_get(client, "/api/analysis/information-ratio?session_id=perf_test", 500)


class TestComplexAnalysisPerformance:
    def test_comprehensive(self, client):
        timed_get(client, "/api/analysis/comprehensive?session_id=perf_test", 3000)

    def test_rolling_correlation(self, client):
        timed_get(client, "/api/analysis/rolling-correlation?session_id=perf_test", 1000)

    def test_parameter_sweep(self, client):
        timed_get(client, "/api/analysis/parameter-sweep?session_id=perf_test&stop_steps=3&target_steps=3&size_steps=2", 5000)

    def test_stress_tail(self, client):
        timed_get(client, "/api/stress/tail-amplification?session_id=perf_test", 2000)

    def test_stress_historical(self, client):
        timed_get(client, "/api/stress/historical?session_id=perf_test", 2000)

    def test_stress_sensitivity(self, client):
        timed_get(client, "/api/stress/sensitivity?session_id=perf_test&size_steps=4&stop_steps=4", 5000)


class TestRobustnessPerformance:
    def test_monte_carlo(self, client):
        timed_get(client, "/api/robustness/monte-carlo?session_id=perf_test&n=100", 5000)

    def test_parametric_mc(self, client):
        timed_get(client, "/api/robustness/parametric-monte-carlo?session_id=perf_test&n_simulations=100", 5000)

    def test_block_bootstrap(self, client):
        timed_get(client, "/api/robustness/block-bootstrap?session_id=perf_test&n_simulations=100", 5000)

    def test_walk_forward(self, client):
        timed_get(client, "/api/robustness/walk-forward?session_id=perf_test", 2000)

    def test_rolling_walk_forward(self, client):
        timed_get(client, "/api/robustness/rolling-walk-forward?session_id=perf_test", 2000)

    def test_deflated_sharpe(self, client):
        timed_get(client, "/api/robustness/deflated-sharpe?session_id=perf_test", 2000)

    def test_regime(self, client):
        timed_get(client, "/api/robustness/regime?session_id=perf_test", 2000)


class TestChartPerformance:
    def test_equity(self, client):
        timed_get(client, "/api/charts/equity?session_id=perf_test", 500)

    def test_heatmap(self, client):
        timed_get(client, "/api/charts/heatmap?session_id=perf_test", 500)

    def test_distribution(self, client):
        timed_get(client, "/api/charts/distribution?session_id=perf_test", 500)

    def test_trades(self, client):
        timed_get(client, "/api/charts/trades?session_id=perf_test&limit=50", 500)

    def test_rolling_metrics(self, client):
        timed_get(client, "/api/charts/rolling-metrics?session_id=perf_test&window=10", 500)

    def test_drawdowns(self, client):
        timed_get(client, "/api/charts/drawdowns?session_id=perf_test", 500)


class TestExportPerformance:
    def test_export_json(self, client):
        timed_get(client, "/api/export/json?session_id=perf_test", 5000)

    def test_export_csv(self, client):
        timed_get(client, "/api/export/csv?session_id=perf_test", 1000)

    def test_export_excel(self, client):
        timed_get(client, "/api/export/excel?session_id=perf_test", 5000)

    def test_export_pdf(self, client):
        timed_get(client, "/api/export/pdf-report?session_id=perf_test", 5000)

    def test_report_html(self, client):
        timed_get(client, "/api/report/html?session_id=perf_test", 3000)
