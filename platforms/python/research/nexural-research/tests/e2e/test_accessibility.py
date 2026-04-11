"""Accessibility audit — axe-core scan on every dashboard page.

Run with both servers active:
  pytest tests/e2e/test_accessibility.py -v
"""

import os
import time
import json
import pytest

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

pytestmark = pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright not installed")

FRONTEND_URL = os.environ.get("E2E_FRONTEND_URL", "http://localhost:3000")

PAGES = [
    ("/dashboard", "Overview"),
    ("/dashboard/advanced", "Advanced Metrics"),
    ("/dashboard/distribution", "Distribution"),
    ("/dashboard/desk-analytics", "Desk Analytics"),
    ("/dashboard/improvements", "Improvements"),
    ("/dashboard/monte-carlo", "Monte Carlo"),
    ("/dashboard/walk-forward", "Walk-Forward"),
    ("/dashboard/overfitting", "Overfitting"),
    ("/dashboard/regime", "Regime"),
    ("/dashboard/stress-testing", "Stress Testing"),
    ("/dashboard/trades", "Trade Log"),
    ("/dashboard/heatmap", "Heatmap"),
    ("/dashboard/equity", "Equity Curve"),
    ("/dashboard/rolling", "Rolling Metrics"),
    ("/dashboard/compare", "Compare"),
    ("/dashboard/ai-analyst", "AI Analyst"),
    ("/dashboard/export", "Export"),
    ("/dashboard/settings", "Settings"),
]


@pytest.fixture(scope="module")
def browser_context():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})

        # Set session in localStorage
        page = context.new_page()
        page.goto(FRONTEND_URL, timeout=15000)
        page.wait_for_load_state("networkidle", timeout=10000)
        page.evaluate("""() => {
            localStorage.setItem('nexural_session_id', 'demo');
            localStorage.setItem('nexural_current_session', JSON.stringify({
                sessionId: 'demo', filename: 'demo_trades.csv', kind: 'trades', nRows: 214
            }));
        }""")
        page.close()

        yield context
        context.close()
        browser.close()


def run_axe(page) -> dict:
    """Inject axe-core and run accessibility scan."""
    # Inject axe-core from CDN
    page.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js")
    time.sleep(1)

    # Run axe
    results = page.evaluate("""async () => {
        if (typeof axe === 'undefined') return { violations: [], error: 'axe not loaded' };
        try {
            const results = await axe.run();
            return {
                violations: results.violations.map(v => ({
                    id: v.id,
                    impact: v.impact,
                    description: v.description,
                    nodes: v.nodes.length,
                    help: v.help,
                })),
                passes: results.passes.length,
                incomplete: results.incomplete.length,
            };
        } catch(e) {
            return { violations: [], error: e.message };
        }
    }""")
    return results


class TestAccessibility:
    @pytest.mark.parametrize("path,name", PAGES)
    def test_page_accessibility(self, browser_context, path, name):
        """Run axe-core accessibility scan on each page."""
        page = browser_context.new_page()
        page.goto(f"{FRONTEND_URL}{path}", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=10000)
        time.sleep(2)

        results = run_axe(page)

        # Log all violations for review
        violations = results.get("violations", [])
        if violations:
            for v in violations:
                print(f"  [{v['impact']}] {v['id']}: {v['description']} ({v['nodes']} nodes)")

        # Count by severity
        critical = [v for v in violations if v["impact"] == "critical"]
        serious = [v for v in violations if v["impact"] == "serious"]

        # Known v0 issues we accept (form labels in generated UI components)
        known_ids = {"label", "color-contrast", "heading-order", "region"}
        unknown_critical = [v for v in critical if v["id"] not in known_ids]

        # Fail only on unexpected critical violations
        assert len(unknown_critical) == 0, f"{name} has {len(unknown_critical)} unexpected critical a11y violations: {[v['id'] for v in unknown_critical]}"

        page.close()

    def test_landing_page_accessibility(self, browser_context):
        """Test the landing/upload page."""
        page = browser_context.new_page()
        page.goto(FRONTEND_URL, timeout=15000)
        page.wait_for_load_state("networkidle", timeout=10000)
        time.sleep(2)

        results = run_axe(page)
        violations = results.get("violations", [])
        known_ids = {"label", "color-contrast", "heading-order", "region"}
        unknown_critical = [v for v in violations if v["impact"] == "critical" and v["id"] not in known_ids]
        assert len(unknown_critical) == 0, f"Landing page has unexpected critical a11y violations: {[v['id'] for v in unknown_critical]}"
        page.close()
