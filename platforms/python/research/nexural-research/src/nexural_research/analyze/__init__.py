"""Analytics engine: metrics, equity curves, drawdowns, heatmaps."""

from __future__ import annotations

__all__ = [
    "metrics_from_trades",
    "equity_curve_from_trades",
    "drawdown_from_equity",
    "time_heatmap",
    "execution_quality_from_executions",
    "monte_carlo_max_drawdown",
    "walk_forward_split",
]

from .equity import equity_curve_from_trades as equity_curve_from_trades
from .equity import drawdown_from_equity as drawdown_from_equity
from .heatmap import time_heatmap as time_heatmap
from .metrics import metrics_from_trades as metrics_from_trades
from .execution_quality import execution_quality_from_executions as execution_quality_from_executions
from .robustness import monte_carlo_max_drawdown as monte_carlo_max_drawdown
from .robustness import walk_forward_split as walk_forward_split
