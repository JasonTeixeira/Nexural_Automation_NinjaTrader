"""Strategy Improvement Engine — automated actionable recommendations.

Analyzes trade data and generates specific, quantified suggestions for:
- Time-of-day / day-of-week filters
- Position sizing adjustments
- Stop-loss / take-profit optimization
- Session restrictions
- Drawdown recovery analysis
- Trade clustering detection
- MAE/MFE efficiency analysis
- Commission impact quantification
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from nexural_research.analyze.advanced_metrics import risk_return_metrics, expectancy_metrics


# ---------------------------------------------------------------------------
# Data classes for structured recommendations
# ---------------------------------------------------------------------------

@dataclass
class Recommendation:
    """A single actionable recommendation."""
    category: str          # "time_filter", "position_sizing", "risk_management", etc.
    priority: str          # "critical", "high", "medium", "low"
    title: str
    description: str
    current_value: str     # what the metric is now
    suggested_value: str   # what it should be
    expected_impact: str   # quantified improvement
    confidence: str        # "high", "medium", "low"


@dataclass
class TimeFilterSuggestion:
    """Specific time filter recommendation."""
    filter_type: str       # "remove_hours", "remove_days", "best_window"
    hours_to_remove: list[int] = field(default_factory=list)
    days_to_remove: list[str] = field(default_factory=list)
    best_hours: list[int] = field(default_factory=list)
    best_days: list[str] = field(default_factory=list)
    current_net: float = 0.0
    filtered_net: float = 0.0
    improvement_pct: float = 0.0
    trades_removed: int = 0
    trades_remaining: int = 0


@dataclass
class DrawdownRecovery:
    """Drawdown recovery analysis."""
    n_drawdowns: int
    avg_recovery_trades: float
    max_recovery_trades: int
    avg_recovery_time_hours: float
    max_recovery_time_hours: float
    currently_in_drawdown: bool
    current_drawdown_depth: float
    deepest_drawdown: float
    drawdown_periods: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TradeCluster:
    """A cluster of consecutive losses."""
    start_index: int
    end_index: int
    n_trades: int
    total_loss: float
    start_time: str
    end_time: str


@dataclass
class MaeMfeAnalysis:
    """MAE/MFE efficiency analysis."""
    has_mae_mfe: bool
    avg_mae: float = 0.0
    avg_mfe: float = 0.0
    entry_efficiency: float = 0.0    # % of MFE captured
    exit_efficiency: float = 0.0     # % of MFE captured at exit
    avg_heat: float = 0.0            # avg adverse excursion before profit
    trades_with_excess_mae: int = 0  # trades where MAE > 2x avg loss
    stop_too_wide_pct: float = 0.0
    suggested_stop: float = 0.0


@dataclass
class StrategyImprovementReport:
    """Complete strategy improvement report."""
    overall_grade: str               # "A", "B", "C", "D", "F"
    grade_explanation: str
    recommendations: list[Recommendation]
    time_filter: TimeFilterSuggestion | None
    drawdown_recovery: DrawdownRecovery
    loss_clusters: list[TradeCluster]
    mae_mfe: MaeMfeAnalysis
    commission_impact_pct: float     # commission as % of gross profit
    filtered_improvement: dict[str, Any]  # what metrics look like with suggested filters


# ---------------------------------------------------------------------------
# Core analysis functions
# ---------------------------------------------------------------------------

def _analyze_time_filters(df: pd.DataFrame) -> TimeFilterSuggestion:
    """Identify losing time slots and compute impact of removing them."""

    pnl = pd.to_numeric(df["profit"], errors="coerce").fillna(0.0)
    current_net = float(pnl.sum())

    ts_col = "exit_time" if "exit_time" in df.columns else "entry_time"
    if ts_col not in df.columns:
        return TimeFilterSuggestion(filter_type="none", current_net=current_net,
                                     filtered_net=current_net, trades_remaining=len(df))

    ts = pd.to_datetime(df[ts_col], errors="coerce")

    # Hour analysis
    hours = ts.dt.hour
    hour_pnl = pnl.groupby(hours).sum()
    losing_hours = sorted(hour_pnl[hour_pnl < 0].index.tolist())
    best_hours = sorted(hour_pnl[hour_pnl > 0].index.tolist())

    # Day analysis
    days = ts.dt.day_name()
    day_pnl = pnl.groupby(days).sum()
    losing_days = sorted(day_pnl[day_pnl < 0].index.tolist())
    best_days = sorted(day_pnl[day_pnl > 0].index.tolist())

    # Compute filtered result
    mask_keep = ~(hours.isin(losing_hours) | days.isin(losing_days))
    filtered_net = float(pnl[mask_keep].sum())
    trades_removed = int((~mask_keep).sum())

    improvement = ((filtered_net - current_net) / abs(current_net) * 100) if abs(current_net) > 0 else 0.0

    return TimeFilterSuggestion(
        filter_type="remove_losing_slots",
        hours_to_remove=losing_hours,
        days_to_remove=losing_days,
        best_hours=best_hours,
        best_days=best_days,
        current_net=round(current_net, 2),
        filtered_net=round(filtered_net, 2),
        improvement_pct=round(improvement, 1),
        trades_removed=trades_removed,
        trades_remaining=int(mask_keep.sum()),
    )


def _analyze_drawdown_recovery(df: pd.DataFrame) -> DrawdownRecovery:
    """Analyze drawdown periods and recovery characteristics."""

    pnl = pd.to_numeric(df["profit"], errors="coerce").fillna(0.0).to_numpy()
    eq = np.cumsum(pnl)
    peak = np.maximum.accumulate(eq)
    dd = eq - peak

    n = len(pnl)
    if n == 0:
        return DrawdownRecovery(n_drawdowns=0, avg_recovery_trades=0, max_recovery_trades=0,
                                avg_recovery_time_hours=0, max_recovery_time_hours=0,
                                currently_in_drawdown=False, current_drawdown_depth=0,
                                deepest_drawdown=0)

    # Find drawdown periods
    in_dd = dd < 0
    periods: list[dict[str, Any]] = []
    start = None

    for i in range(n):
        if in_dd[i] and start is None:
            start = i
        elif not in_dd[i] and start is not None:
            depth = float(np.min(dd[start:i]))
            periods.append({
                "start_trade": start,
                "end_trade": i,
                "recovery_trades": i - start,
                "depth": round(depth, 2),
            })
            start = None

    # Handle still in drawdown
    if start is not None:
        depth = float(np.min(dd[start:]))
        periods.append({
            "start_trade": start,
            "end_trade": n,
            "recovery_trades": n - start,
            "depth": round(depth, 2),
            "still_open": True,
        })

    recovery_trades = [p["recovery_trades"] for p in periods if not p.get("still_open")]

    # Time-based recovery
    ts_col = "exit_time" if "exit_time" in df.columns else "entry_time"
    recovery_hours: list[float] = []
    if ts_col in df.columns:
        ts = pd.to_datetime(df[ts_col], errors="coerce")
        for p in periods:
            if not p.get("still_open") and p["end_trade"] < len(ts):
                t_start = ts.iloc[p["start_trade"]]
                t_end = ts.iloc[p["end_trade"] - 1]
                if pd.notna(t_start) and pd.notna(t_end):
                    hours = (t_end - t_start).total_seconds() / 3600
                    recovery_hours.append(hours)
                    p["recovery_hours"] = round(hours, 1)

    return DrawdownRecovery(
        n_drawdowns=len(periods),
        avg_recovery_trades=round(float(np.mean(recovery_trades)), 1) if recovery_trades else 0.0,
        max_recovery_trades=max(recovery_trades) if recovery_trades else 0,
        avg_recovery_time_hours=round(float(np.mean(recovery_hours)), 1) if recovery_hours else 0.0,
        max_recovery_time_hours=round(max(recovery_hours), 1) if recovery_hours else 0.0,
        currently_in_drawdown=bool(dd[-1] < 0),
        current_drawdown_depth=round(float(dd[-1]), 2),
        deepest_drawdown=round(float(np.min(dd)), 2),
        drawdown_periods=periods[:20],  # cap for serialization
    )


def _detect_loss_clusters(df: pd.DataFrame, threshold: int = 3) -> list[TradeCluster]:
    """Detect clusters of consecutive losses."""

    pnl = pd.to_numeric(df["profit"], errors="coerce").fillna(0.0).to_numpy()
    is_loss = pnl < 0

    ts_col = "exit_time" if "exit_time" in df.columns else "entry_time"
    has_ts = ts_col in df.columns

    clusters: list[TradeCluster] = []
    start = None
    count = 0

    for i in range(len(pnl)):
        if is_loss[i]:
            if start is None:
                start = i
            count += 1
        else:
            if start is not None and count >= threshold:
                total_loss = float(np.sum(pnl[start:i]))
                start_time = str(df[ts_col].iloc[start]) if has_ts else ""
                end_time = str(df[ts_col].iloc[i - 1]) if has_ts else ""
                clusters.append(TradeCluster(
                    start_index=start, end_index=i - 1, n_trades=count,
                    total_loss=round(total_loss, 2),
                    start_time=start_time, end_time=end_time,
                ))
            start = None
            count = 0

    # Handle trailing cluster
    if start is not None and count >= threshold:
        total_loss = float(np.sum(pnl[start:]))
        start_time = str(df[ts_col].iloc[start]) if has_ts else ""
        end_time = str(df[ts_col].iloc[-1]) if has_ts else ""
        clusters.append(TradeCluster(
            start_index=start, end_index=len(pnl) - 1, n_trades=count,
            total_loss=round(total_loss, 2),
            start_time=start_time, end_time=end_time,
        ))

    return sorted(clusters, key=lambda c: c.total_loss)  # worst first


def _analyze_mae_mfe(df: pd.DataFrame) -> MaeMfeAnalysis:
    """Analyze MAE/MFE efficiency — how well entries/exits capture available edge."""

    has_mae = "mae" in df.columns
    has_mfe = "mfe" in df.columns

    if not has_mae and not has_mfe:
        return MaeMfeAnalysis(has_mae_mfe=False)

    pnl = pd.to_numeric(df["profit"], errors="coerce").fillna(0.0).to_numpy()
    mae = pd.to_numeric(df.get("mae", pd.Series(dtype=float)), errors="coerce").fillna(0.0).abs().to_numpy()
    mfe = pd.to_numeric(df.get("mfe", pd.Series(dtype=float)), errors="coerce").fillna(0.0).abs().to_numpy()

    avg_mae = float(np.mean(mae)) if has_mae else 0.0
    avg_mfe = float(np.mean(mfe)) if has_mfe else 0.0

    # Entry efficiency: how little adverse excursion before getting to profit
    # Lower MAE relative to profit = better entries
    winning_mask = pnl > 0
    if has_mfe and np.any(winning_mask) and avg_mfe > 0:
        # What % of MFE was captured as actual profit
        exit_eff = float(np.mean(pnl[winning_mask] / np.maximum(mfe[winning_mask], 1e-10))) * 100
    else:
        exit_eff = 0.0

    if has_mae and has_mfe and avg_mfe > 0:
        entry_eff = max(0, (1 - avg_mae / avg_mfe)) * 100
    else:
        entry_eff = 0.0

    # Average heat — how much adverse movement before profit
    avg_heat = float(np.mean(mae)) if has_mae else 0.0

    # Trades with excessive MAE
    avg_loss = abs(float(np.mean(pnl[pnl < 0]))) if np.any(pnl < 0) else 1.0
    excess_mae = int(np.sum(mae > 2 * avg_loss)) if has_mae else 0

    # Suggested stop based on MAE distribution
    if has_mae and len(mae) > 5:
        suggested_stop = float(np.percentile(mae[winning_mask], 95)) if np.any(winning_mask) else avg_mae * 1.5
    else:
        suggested_stop = 0.0

    return MaeMfeAnalysis(
        has_mae_mfe=True,
        avg_mae=round(avg_mae, 2),
        avg_mfe=round(avg_mfe, 2),
        entry_efficiency=round(entry_eff, 1),
        exit_efficiency=round(exit_eff, 1),
        avg_heat=round(avg_heat, 2),
        trades_with_excess_mae=excess_mae,
        stop_too_wide_pct=round(excess_mae / max(len(pnl), 1) * 100, 1),
        suggested_stop=round(suggested_stop, 2),
    )


def _grade_strategy(recs: list[Recommendation]) -> tuple[str, str]:
    """Assign overall letter grade based on recommendations."""
    critical = sum(1 for r in recs if r.priority == "critical")
    high = sum(1 for r in recs if r.priority == "high")
    medium = sum(1 for r in recs if r.priority == "medium")

    if critical >= 3:
        return "F", "Strategy has fundamental issues that must be addressed before live trading"
    if critical >= 1:
        return "D", "Critical problems detected — significant rework needed"
    if high >= 3:
        return "C", "Multiple high-priority improvements needed — promising but not ready"
    if high >= 1:
        return "B", "Solid foundation with specific improvements that would help"
    if medium >= 2:
        return "B+", "Good strategy with minor optimization opportunities"
    return "A", "Strong strategy — focus on execution and consistency"


def _compute_filtered_metrics(df: pd.DataFrame, tf: TimeFilterSuggestion) -> dict[str, Any]:
    """Compute what metrics look like after applying suggested time filters."""

    ts_col = "exit_time" if "exit_time" in df.columns else "entry_time"
    if ts_col not in df.columns:
        return {}

    ts = pd.to_datetime(df[ts_col], errors="coerce")
    hours = ts.dt.hour
    days = ts.dt.day_name()

    mask = ~(hours.isin(tf.hours_to_remove) | days.isin(tf.days_to_remove))
    df_filtered = df[mask].copy()

    if len(df_filtered) < 3:
        return {"error": "Too few trades after filtering"}

    pnl = pd.to_numeric(df_filtered["profit"], errors="coerce").fillna(0.0)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]

    return {
        "trades": len(df_filtered),
        "net_profit": round(float(pnl.sum()), 2),
        "win_rate": round(float(len(wins) / len(pnl) * 100), 1) if len(pnl) > 0 else 0,
        "profit_factor": round(float(wins.sum() / abs(losses.sum())), 2) if abs(losses.sum()) > 0 else float("inf"),
        "avg_trade": round(float(pnl.mean()), 2),
    }


# ---------------------------------------------------------------------------
# Main improvement report generator
# ---------------------------------------------------------------------------

def generate_improvement_report(df: pd.DataFrame) -> StrategyImprovementReport:
    """Generate the complete strategy improvement report with actionable recommendations."""

    pnl = pd.to_numeric(df["profit"], errors="coerce").fillna(0.0)
    n = len(pnl)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    win_rate = float(len(wins) / n) if n > 0 else 0
    avg_win = float(wins.mean()) if len(wins) > 0 else 0
    avg_loss = abs(float(losses.mean())) if len(losses) > 0 else 0
    pf = float(wins.sum() / abs(losses.sum())) if abs(losses.sum()) > 0 else float("inf")

    rr = risk_return_metrics(df)
    exp = expectancy_metrics(df)

    recommendations: list[Recommendation] = []

    # --- Time filter analysis ---
    tf = _analyze_time_filters(df)
    if tf.hours_to_remove or tf.days_to_remove:
        if tf.improvement_pct > 20:
            priority = "high"
        elif tf.improvement_pct > 5:
            priority = "medium"
        else:
            priority = "low"

        desc_parts = []
        if tf.hours_to_remove:
            desc_parts.append(f"Remove hours: {', '.join(f'{h}:00' for h in tf.hours_to_remove)}")
        if tf.days_to_remove:
            desc_parts.append(f"Remove days: {', '.join(tf.days_to_remove)}")

        recommendations.append(Recommendation(
            category="time_filter",
            priority=priority,
            title="Apply Time-of-Day / Day-of-Week Filters",
            description=". ".join(desc_parts) + f". This removes {tf.trades_removed} losing trades.",
            current_value=f"Net: ${tf.current_net:,.2f} ({n} trades)",
            suggested_value=f"Net: ${tf.filtered_net:,.2f} ({tf.trades_remaining} trades)",
            expected_impact=f"+{tf.improvement_pct}% net profit improvement",
            confidence="high" if n > 50 else "medium",
        ))

    # --- Win rate ---
    if win_rate < 0.4:
        recommendations.append(Recommendation(
            category="entry_quality",
            priority="critical",
            title="Improve Entry Signal Quality",
            description=f"Win rate of {win_rate*100:.1f}% is below the 40% threshold. Consider adding confirmation filters (volume, volatility, trend alignment) or tightening entry conditions.",
            current_value=f"{win_rate*100:.1f}%",
            suggested_value=">45% minimum for viability",
            expected_impact="Foundation for all other improvements",
            confidence="high",
        ))
    elif win_rate < 0.5 and avg_win < avg_loss * 1.5:
        recommendations.append(Recommendation(
            category="entry_quality",
            priority="high",
            title="Win Rate Below 50% Without Sufficient Payoff",
            description=f"Win rate {win_rate*100:.1f}% with payoff ratio {avg_win/avg_loss:.2f}x is marginal. Either improve win rate above 50% or increase payoff ratio above 2.0x.",
            current_value=f"WR: {win_rate*100:.1f}%, Payoff: {avg_win/avg_loss:.2f}x",
            suggested_value="WR > 50% OR Payoff > 2.0x",
            expected_impact="Positive expectancy",
            confidence="high",
        ))

    # --- Profit factor ---
    if pf < 1.0:
        recommendations.append(Recommendation(
            category="risk_management",
            priority="critical",
            title="Strategy is Net Negative — Profit Factor Below 1.0",
            description=f"Profit factor of {pf:.2f} means losses exceed gains. Do not trade live. Review entry/exit logic completely.",
            current_value=f"{pf:.2f}",
            suggested_value=">1.5 for viable, >2.0 for strong",
            expected_impact="Survival",
            confidence="high",
        ))
    elif pf < 1.5:
        recommendations.append(Recommendation(
            category="risk_management",
            priority="high",
            title="Profit Factor Marginal",
            description=f"Profit factor of {pf:.2f} leaves little room for slippage and commission in live trading.",
            current_value=f"{pf:.2f}",
            suggested_value=">1.5",
            expected_impact="Sufficient margin for live execution costs",
            confidence="high",
        ))

    # --- Position sizing ---
    kelly = exp.kelly_pct
    if kelly > 0 and kelly < 25:
        recommendations.append(Recommendation(
            category="position_sizing",
            priority="medium",
            title=f"Optimal Position Size: {exp.half_kelly_pct:.1f}% of Capital (Half-Kelly)",
            description=f"Full Kelly suggests {kelly:.1f}% per trade, but half-Kelly ({exp.half_kelly_pct:.1f}%) provides better risk-adjusted growth. Current edge supports this sizing.",
            current_value="Unknown (set by user)",
            suggested_value=f"{exp.half_kelly_pct:.1f}% of account per trade",
            expected_impact="Optimized geometric growth rate",
            confidence="medium" if n > 30 else "low",
        ))
    elif kelly <= 0:
        recommendations.append(Recommendation(
            category="position_sizing",
            priority="critical",
            title="Kelly Criterion Says: Do Not Trade",
            description=f"Kelly = {kelly:.1f}%. Negative or zero Kelly means the edge is insufficient to justify any position size.",
            current_value=f"Kelly: {kelly:.1f}%",
            suggested_value="Fix the strategy first",
            expected_impact="Capital preservation",
            confidence="high",
        ))

    # --- Sharpe ratio ---
    if rr.sharpe_ratio < 0.5:
        recommendations.append(Recommendation(
            category="risk_management",
            priority="high" if rr.sharpe_ratio < 0 else "medium",
            title="Low Risk-Adjusted Returns",
            description=f"Sharpe ratio of {rr.sharpe_ratio} is {'negative' if rr.sharpe_ratio < 0 else 'below institutional minimum of 0.5'}. Returns don't compensate for risk taken.",
            current_value=f"Sharpe: {rr.sharpe_ratio}",
            suggested_value=">1.0 for viable, >1.5 for institutional",
            expected_impact="Institutional-grade risk-adjusted performance",
            confidence="high",
        ))

    # --- Commission impact ---
    gross = float(wins.sum()) if len(wins) > 0 else 0
    comm_col = "commission" if "commission" in df.columns else None
    if comm_col:
        total_comm = abs(float(pd.to_numeric(df[comm_col], errors="coerce").fillna(0).sum()))
        comm_pct = (total_comm / gross * 100) if gross > 0 else 0
    else:
        total_comm = 0
        comm_pct = 0

    if comm_pct > 20:
        recommendations.append(Recommendation(
            category="execution",
            priority="high",
            title="Excessive Commission Impact",
            description=f"Commission consumes {comm_pct:.1f}% of gross profit (${total_comm:,.2f} total). Consider reducing trade frequency, increasing per-trade edge, or negotiating better rates.",
            current_value=f"{comm_pct:.1f}% of gross profit",
            suggested_value="<10% of gross profit",
            expected_impact=f"Save ${total_comm * 0.5:,.2f} if halved",
            confidence="high",
        ))

    # --- Drawdown recovery ---
    dd_recovery = _analyze_drawdown_recovery(df)
    if dd_recovery.max_recovery_trades > n * 0.3:
        recommendations.append(Recommendation(
            category="risk_management",
            priority="medium",
            title="Slow Drawdown Recovery",
            description=f"Worst drawdown took {dd_recovery.max_recovery_trades} trades to recover ({dd_recovery.max_recovery_trades/n*100:.0f}% of total). Consider tighter stops or drawdown-triggered position reduction.",
            current_value=f"{dd_recovery.max_recovery_trades} trades to recover",
            suggested_value="<20% of trade count",
            expected_impact="Faster recovery, lower psychological burden",
            confidence="medium",
        ))

    # --- Loss clusters ---
    clusters = _detect_loss_clusters(df, threshold=3)
    if clusters:
        worst = clusters[0]
        recommendations.append(Recommendation(
            category="risk_management",
            priority="medium",
            title=f"Loss Clustering Detected ({len(clusters)} cluster(s))",
            description=f"Worst cluster: {worst.n_trades} consecutive losses totaling ${abs(worst.total_loss):,.2f}. Consider adding a 'cool-down' period after N consecutive losses or reducing size.",
            current_value=f"{worst.n_trades} consecutive losses, ${abs(worst.total_loss):,.2f}",
            suggested_value="Max 3 consecutive losses before pause",
            expected_impact="Reduced emotional and capital damage",
            confidence="medium",
        ))

    # --- MAE/MFE ---
    mae_mfe = _analyze_mae_mfe(df)
    if mae_mfe.has_mae_mfe:
        if mae_mfe.exit_efficiency < 50:
            recommendations.append(Recommendation(
                category="exit_optimization",
                priority="high",
                title="Poor Exit Efficiency — Leaving Edge on the Table",
                description=f"Exit efficiency is {mae_mfe.exit_efficiency:.1f}% — you're only capturing {mae_mfe.exit_efficiency:.0f}% of maximum favorable excursion. Consider trailing stops or scaled exits.",
                current_value=f"{mae_mfe.exit_efficiency:.1f}% of MFE captured",
                suggested_value=">60% exit efficiency",
                expected_impact="Capture more of each winning trade",
                confidence="high",
            ))
        if mae_mfe.suggested_stop > 0:
            recommendations.append(Recommendation(
                category="risk_management",
                priority="medium",
                title=f"Data-Driven Stop-Loss: ${mae_mfe.suggested_stop:,.2f}",
                description=f"Based on 95th percentile of MAE on winning trades. Current avg adverse excursion is ${mae_mfe.avg_mae:,.2f}.",
                current_value=f"Avg MAE: ${mae_mfe.avg_mae:,.2f}",
                suggested_value=f"Stop at ${mae_mfe.suggested_stop:,.2f}",
                expected_impact="Tighter risk without cutting winners",
                confidence="high" if n > 30 else "medium",
            ))

    # --- Sample size warning ---
    if n < 30:
        recommendations.append(Recommendation(
            category="data_quality",
            priority="high",
            title="Insufficient Sample Size",
            description=f"Only {n} trades — statistical significance is very low. All metrics have wide confidence intervals. Need minimum 30 trades, ideally 100+.",
            current_value=f"{n} trades",
            suggested_value="100+ trades for reliable analysis",
            expected_impact="All metrics become trustworthy",
            confidence="high",
        ))

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    recommendations.sort(key=lambda r: priority_order.get(r.priority, 4))

    # Grade
    grade, grade_explanation = _grade_strategy(recommendations)

    # Filtered improvement metrics
    filtered = _compute_filtered_metrics(df, tf) if tf.hours_to_remove or tf.days_to_remove else {}

    return StrategyImprovementReport(
        overall_grade=grade,
        grade_explanation=grade_explanation,
        recommendations=recommendations,
        time_filter=tf,
        drawdown_recovery=dd_recovery,
        loss_clusters=clusters,
        mae_mfe=mae_mfe,
        commission_impact_pct=round(comm_pct, 1),
        filtered_improvement=filtered,
    )
