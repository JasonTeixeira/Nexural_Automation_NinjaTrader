"""Advanced robustness testing: parametric Monte Carlo, block bootstrap,
rolling walk-forward analysis, Deflated Sharpe Ratio, and parameter
sensitivity analysis.

These go well beyond what NinjaTrader provides and are used by
institutional quant teams to validate strategy robustness.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

import numpy as np
import pandas as pd
from scipy import stats as sp_stats



# ---------------------------------------------------------------------------
# Parametric Monte Carlo
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ParametricMonteCarloResult:
    """Monte Carlo simulation using fitted distribution parameters."""

    n_simulations: int
    n_trades_per_sim: int
    distribution: str  # "normal", "t", "empirical"
    final_equity_mean: float
    final_equity_std: float
    final_equity_p05: float
    final_equity_p25: float
    final_equity_p50: float
    final_equity_p75: float
    final_equity_p95: float
    mdd_mean: float
    mdd_p50: float
    mdd_p95: float
    mdd_p99: float
    prob_profitable: float  # % of sims that end positive
    prob_drawdown_50pct: float  # % of sims with >50% drawdown of peak equity


def parametric_monte_carlo(
    df_trades: pd.DataFrame,
    *,
    n_simulations: int = 5000,
    n_trades_per_sim: int | None = None,
    seed: int = 42,
    distribution: str = "empirical",
) -> ParametricMonteCarloResult:
    """Run parametric Monte Carlo simulation.

    distribution options:
    - "empirical": resample from actual trade returns with replacement (bootstrap)
    - "normal": fit normal distribution and simulate
    - "t": fit Student's t-distribution and simulate (better for fat tails)
    """

    pnl = pd.to_numeric(df_trades["profit"], errors="coerce").fillna(0.0).to_numpy()
    n = len(pnl)
    if n == 0:
        return ParametricMonteCarloResult(**{f.name: 0.0 for f in fields(ParametricMonteCarloResult)},)

    if n_trades_per_sim is None:
        n_trades_per_sim = n

    rng = np.random.default_rng(seed)
    final_equities = np.zeros(n_simulations)
    max_drawdowns = np.zeros(n_simulations)

    for i in range(n_simulations):
        if distribution == "empirical":
            sim_pnl = rng.choice(pnl, size=n_trades_per_sim, replace=True)
        elif distribution == "normal":
            sim_pnl = rng.normal(loc=np.mean(pnl), scale=np.std(pnl, ddof=1), size=n_trades_per_sim)
        elif distribution == "t":
            df_param, loc, scale = sp_stats.t.fit(pnl)
            sim_pnl = sp_stats.t.rvs(df_param, loc=loc, scale=scale, size=n_trades_per_sim, random_state=rng)
        else:
            raise ValueError(f"unsupported distribution: {distribution}")

        eq = np.cumsum(sim_pnl)
        final_equities[i] = eq[-1]
        peak = np.maximum.accumulate(eq)
        dd = eq - peak
        max_drawdowns[i] = float(np.min(dd))

    eq_pcts = np.percentile(final_equities, [5, 25, 50, 75, 95])
    mdd_abs = np.abs(max_drawdowns)

    # Probability of >50% drawdown relative to peak equity at that point
    # Simplified: use max drawdowns vs final equity
    peak_equities = final_equities + mdd_abs  # rough peak estimate
    prob_dd50 = float(np.mean(mdd_abs > 0.5 * np.maximum(peak_equities, 1e-10)))

    return ParametricMonteCarloResult(
        n_simulations=n_simulations,
        n_trades_per_sim=n_trades_per_sim,
        distribution=distribution,
        final_equity_mean=round(float(np.mean(final_equities)), 2),
        final_equity_std=round(float(np.std(final_equities)), 2),
        final_equity_p05=round(float(eq_pcts[0]), 2),
        final_equity_p25=round(float(eq_pcts[1]), 2),
        final_equity_p50=round(float(eq_pcts[2]), 2),
        final_equity_p75=round(float(eq_pcts[3]), 2),
        final_equity_p95=round(float(eq_pcts[4]), 2),
        mdd_mean=round(float(np.mean(max_drawdowns)), 2),
        mdd_p50=round(float(np.percentile(max_drawdowns, 50)), 2),
        mdd_p95=round(float(np.percentile(max_drawdowns, 5)), 2),  # worst 5% of MDD
        mdd_p99=round(float(np.percentile(max_drawdowns, 1)), 2),
        prob_profitable=round(float(np.mean(final_equities > 0) * 100), 2),
        prob_drawdown_50pct=round(float(prob_dd50 * 100), 2),
    )


# ---------------------------------------------------------------------------
# Block Bootstrap Monte Carlo
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BlockBootstrapResult:
    """Block bootstrap preserves autocorrelation structure."""

    n_simulations: int
    block_size: int
    sharpe_mean: float
    sharpe_std: float
    sharpe_p05: float
    sharpe_p95: float
    sharpe_ci_lower: float  # 95% CI
    sharpe_ci_upper: float
    net_profit_p05: float
    net_profit_p95: float
    mdd_p50: float
    mdd_p95: float


def block_bootstrap_monte_carlo(
    df_trades: pd.DataFrame,
    *,
    n_simulations: int = 2000,
    block_size: int | None = None,
    seed: int = 42,
) -> BlockBootstrapResult:
    """Block bootstrap Monte Carlo that preserves trade autocorrelation.

    Useful when trades have serial dependency (momentum/mean-reversion regimes).
    """

    pnl = pd.to_numeric(df_trades["profit"], errors="coerce").fillna(0.0).to_numpy()
    n = len(pnl)
    if n < 10:
        return BlockBootstrapResult(**{f.name: 0 if "int" in str(type(getattr(BlockBootstrapResult, f.name, 0))) else 0.0 for f in fields(BlockBootstrapResult)})

    # Auto block size: cube root of n (Politis & Romano)
    if block_size is None:
        block_size = max(3, int(np.ceil(n ** (1 / 3))))

    rng = np.random.default_rng(seed)
    sharpes = np.zeros(n_simulations)
    net_profits = np.zeros(n_simulations)
    max_drawdowns = np.zeros(n_simulations)

    n_blocks = int(np.ceil(n / block_size))

    for i in range(n_simulations):
        # Sample blocks with replacement
        blocks = []
        for _ in range(n_blocks):
            start = rng.integers(0, max(1, n - block_size + 1))
            blocks.append(pnl[start : start + block_size])
        sim_pnl = np.concatenate(blocks)[:n]

        eq = np.cumsum(sim_pnl)
        net_profits[i] = eq[-1]

        std = float(np.std(sim_pnl, ddof=1))
        sharpes[i] = float(np.mean(sim_pnl) / std * np.sqrt(252)) if std > 1e-10 else 0.0

        peak = np.maximum.accumulate(eq)
        max_drawdowns[i] = float(np.min(eq - peak))

    s_pcts = np.percentile(sharpes, [2.5, 5, 95, 97.5])
    p_pcts = np.percentile(net_profits, [5, 95])

    return BlockBootstrapResult(
        n_simulations=n_simulations,
        block_size=block_size,
        sharpe_mean=round(float(np.mean(sharpes)), 4),
        sharpe_std=round(float(np.std(sharpes)), 4),
        sharpe_p05=round(float(s_pcts[1]), 4),
        sharpe_p95=round(float(s_pcts[2]), 4),
        sharpe_ci_lower=round(float(s_pcts[0]), 4),
        sharpe_ci_upper=round(float(s_pcts[3]), 4),
        net_profit_p05=round(float(p_pcts[0]), 2),
        net_profit_p95=round(float(p_pcts[1]), 2),
        mdd_p50=round(float(np.percentile(max_drawdowns, 50)), 2),
        mdd_p95=round(float(np.percentile(max_drawdowns, 5)), 2),
    )


# ---------------------------------------------------------------------------
# Rolling Walk-Forward Analysis
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WalkForwardWindow:
    """Metrics for a single walk-forward window."""

    window_id: int
    in_sample_start: str
    in_sample_end: str
    out_sample_start: str
    out_sample_end: str
    in_sample_n: int
    out_sample_n: int
    in_sample_net: float
    out_sample_net: float
    in_sample_sharpe: float
    out_sample_sharpe: float
    efficiency: float  # out-of-sample / in-sample performance ratio


@dataclass(frozen=True)
class RollingWalkForwardResult:
    """Complete rolling walk-forward analysis."""

    n_windows: int
    in_sample_pct: float
    anchored: bool
    windows: list[WalkForwardWindow]
    aggregate_oos_net: float
    aggregate_oos_sharpe: float
    avg_efficiency: float
    efficiency_std: float
    pct_profitable_oos: float
    walk_forward_efficiency: float  # aggregate OOS / aggregate IS


def rolling_walk_forward(
    df_trades: pd.DataFrame,
    *,
    n_windows: int = 5,
    in_sample_pct: float = 0.7,
    anchored: bool = False,
    ts_col: str = "exit_time",
) -> RollingWalkForwardResult:
    """Rolling or anchored walk-forward analysis with multiple windows.

    - Rolling: fixed-size IS window slides forward
    - Anchored: IS window always starts at the beginning, grows
    """

    if ts_col not in df_trades.columns:
        ts_col = "entry_time" if "entry_time" in df_trades.columns else ts_col

    df = df_trades.copy()
    if ts_col in df.columns:
        df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
        df = df.dropna(subset=[ts_col]).sort_values(ts_col, kind="mergesort").reset_index(drop=True)

    n = len(df)
    if n < 20:
        return RollingWalkForwardResult(
            n_windows=0, in_sample_pct=in_sample_pct, anchored=anchored,
            windows=[], aggregate_oos_net=0.0, aggregate_oos_sharpe=0.0,
            avg_efficiency=0.0, efficiency_std=0.0, pct_profitable_oos=0.0,
            walk_forward_efficiency=0.0,
        )

    # Calculate window boundaries
    total_oos = int(n * (1 - in_sample_pct))
    oos_per_window = max(1, total_oos // n_windows)

    windows: list[WalkForwardWindow] = []
    all_oos_pnl: list[float] = []
    all_is_pnl: list[float] = []

    for w in range(n_windows):
        if anchored:
            is_start = 0
            is_end = int(n * in_sample_pct) + w * oos_per_window
        else:
            is_start = w * oos_per_window
            is_end = is_start + int(n * in_sample_pct / n_windows * (n_windows - 0))
            is_end = min(is_start + int(n * in_sample_pct), n)

        oos_start = is_end
        oos_end = min(oos_start + oos_per_window, n)

        if oos_start >= n or oos_end <= oos_start:
            break

        df_is = df.iloc[is_start:is_end]
        df_oos = df.iloc[oos_start:oos_end]

        is_pnl = pd.to_numeric(df_is["profit"], errors="coerce").fillna(0.0).to_numpy()
        oos_pnl = pd.to_numeric(df_oos["profit"], errors="coerce").fillna(0.0).to_numpy()

        is_net = float(np.sum(is_pnl))
        oos_net = float(np.sum(oos_pnl))

        is_std = float(np.std(is_pnl, ddof=1)) if len(is_pnl) > 1 else 1e-10
        oos_std = float(np.std(oos_pnl, ddof=1)) if len(oos_pnl) > 1 else 1e-10

        is_sharpe = float(np.mean(is_pnl) / is_std) if is_std > 1e-10 else 0.0
        oos_sharpe = float(np.mean(oos_pnl) / oos_std) if oos_std > 1e-10 else 0.0

        efficiency = oos_sharpe / is_sharpe if abs(is_sharpe) > 1e-10 else 0.0

        ts_col_safe = ts_col if ts_col in df.columns else None
        is_start_ts = str(df_is[ts_col].iloc[0]) if ts_col_safe and len(df_is) > 0 else ""
        is_end_ts = str(df_is[ts_col].iloc[-1]) if ts_col_safe and len(df_is) > 0 else ""
        oos_start_ts = str(df_oos[ts_col].iloc[0]) if ts_col_safe and len(df_oos) > 0 else ""
        oos_end_ts = str(df_oos[ts_col].iloc[-1]) if ts_col_safe and len(df_oos) > 0 else ""

        windows.append(WalkForwardWindow(
            window_id=w,
            in_sample_start=is_start_ts,
            in_sample_end=is_end_ts,
            out_sample_start=oos_start_ts,
            out_sample_end=oos_end_ts,
            in_sample_n=len(df_is),
            out_sample_n=len(df_oos),
            in_sample_net=round(is_net, 2),
            out_sample_net=round(oos_net, 2),
            in_sample_sharpe=round(is_sharpe, 4),
            out_sample_sharpe=round(oos_sharpe, 4),
            efficiency=round(efficiency, 4),
        ))

        all_oos_pnl.extend(oos_pnl.tolist())
        all_is_pnl.extend(is_pnl.tolist())

    efficiencies = [w.efficiency for w in windows]
    oos_nets = [w.out_sample_net for w in windows]

    agg_oos = sum(all_oos_pnl)
    agg_is = sum(all_is_pnl)
    agg_oos_std = float(np.std(all_oos_pnl, ddof=1)) if len(all_oos_pnl) > 1 else 1e-10
    agg_oos_sharpe = float(np.mean(all_oos_pnl) / agg_oos_std) if agg_oos_std > 1e-10 else 0.0

    return RollingWalkForwardResult(
        n_windows=len(windows),
        in_sample_pct=in_sample_pct,
        anchored=anchored,
        windows=windows,
        aggregate_oos_net=round(agg_oos, 2),
        aggregate_oos_sharpe=round(agg_oos_sharpe, 4),
        avg_efficiency=round(float(np.mean(efficiencies)), 4) if efficiencies else 0.0,
        efficiency_std=round(float(np.std(efficiencies)), 4) if len(efficiencies) > 1 else 0.0,
        pct_profitable_oos=round(float(np.mean([n > 0 for n in oos_nets]) * 100), 1) if oos_nets else 0.0,
        walk_forward_efficiency=round(agg_oos / agg_is, 4) if abs(agg_is) > 1e-10 else 0.0,
    )


# ---------------------------------------------------------------------------
# Deflated Sharpe Ratio (overfitting detection)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DeflatedSharpeResult:
    """Deflated Sharpe Ratio — tests whether the observed Sharpe is
    statistically significant after accounting for multiple testing."""

    observed_sharpe: float
    deflated_sharpe: float
    p_value: float
    is_significant: bool  # at 5% level
    n_trials_assumed: int
    expected_max_sharpe: float
    interpretation: str


def deflated_sharpe_ratio(
    df_trades: pd.DataFrame,
    *,
    n_trials: int = 100,
    risk_free_rate: float = 0.0,
) -> DeflatedSharpeResult:
    """Compute the Deflated Sharpe Ratio (Bailey & Lopez de Prado, 2014).

    This adjusts for:
    - Multiple testing (how many strategies/parameters were tried)
    - Non-normal returns (skewness, kurtosis)
    - Sample length

    A DSR that is significant means the strategy is unlikely to be a
    result of overfitting from trying many parameter combinations.
    """

    pnl = pd.to_numeric(df_trades["profit"], errors="coerce").fillna(0.0).to_numpy()
    n = len(pnl)

    if n < 10:
        return DeflatedSharpeResult(
            observed_sharpe=0.0, deflated_sharpe=0.0, p_value=1.0,
            is_significant=False, n_trials_assumed=n_trials,
            expected_max_sharpe=0.0,
            interpretation="insufficient data for deflated Sharpe analysis",
        )

    mean_ret = float(np.mean(pnl)) - risk_free_rate / 252.0
    std_ret = float(np.std(pnl, ddof=1))
    if std_ret < 1e-10:
        std_ret = 1e-10

    observed_sharpe = mean_ret / std_ret * np.sqrt(252)
    skew = float(sp_stats.skew(pnl))
    kurt = float(sp_stats.kurtosis(pnl))

    # Expected maximum Sharpe ratio under null (from n_trials independent tests)
    # E[max(SR)] ≈ sqrt(2 * ln(n_trials)) - (euler_gamma + ln(ln(n_trials))) / (2 * sqrt(2 * ln(n_trials)))
    euler_gamma = 0.5772156649
    if n_trials > 1:
        v = np.sqrt(2.0 * np.log(n_trials))
        expected_max_sr = v - (euler_gamma + np.log(np.log(n_trials))) / (2.0 * v)
    else:
        expected_max_sr = 0.0

    # Standard error of Sharpe ratio with non-normality adjustment
    sr = observed_sharpe / np.sqrt(252)  # per-trade Sharpe
    se_var = (1.0 - skew * sr + (kurt - 1) / 4.0 * sr ** 2) / (n - 1.0)
    se_sr = np.sqrt(max(se_var, 1e-10))

    if se_sr < 1e-10:
        se_sr = 1e-10

    # Deflated Sharpe: test if observed SR > expected max SR under null
    # PSR = Prob[SR* > SR0] where SR0 = expected max
    psr_stat = (sr - expected_max_sr / np.sqrt(252)) / se_sr
    p_value = 1.0 - float(sp_stats.norm.cdf(psr_stat))

    is_sig = p_value < 0.05

    if is_sig:
        interp = f"Strategy Sharpe ({observed_sharpe:.2f}) survives deflation (p={p_value:.4f}). Unlikely to be overfit."
    else:
        interp = f"Strategy Sharpe ({observed_sharpe:.2f}) does NOT survive deflation (p={p_value:.4f}). Potential overfitting from {n_trials} trials."

    return DeflatedSharpeResult(
        observed_sharpe=round(float(observed_sharpe), 4),
        deflated_sharpe=round(float(psr_stat), 4),
        p_value=round(float(p_value), 6),
        is_significant=is_sig,
        n_trials_assumed=n_trials,
        expected_max_sharpe=round(float(expected_max_sr), 4),
        interpretation=interp,
    )


# ---------------------------------------------------------------------------
# Regime Detection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegimeAnalysisResult:
    """Volatility and performance regime analysis."""

    n_regimes: int
    regime_labels: list[str]
    regime_counts: list[int]
    regime_avg_pnl: list[float]
    regime_sharpe: list[float]
    regime_win_rate: list[float]
    regime_avg_drawdown: list[float]
    current_regime: str
    interpretation: str


def regime_analysis(
    df_trades: pd.DataFrame,
    *,
    n_regimes: int = 3,
    window: int = 20,
) -> RegimeAnalysisResult:
    """Detect volatility regimes and analyze strategy performance in each.

    Uses rolling volatility to classify trades into low/medium/high
    volatility regimes, then compares performance across regimes.
    """

    pnl = pd.to_numeric(df_trades["profit"], errors="coerce").fillna(0.0)
    n = len(pnl)

    if n < window * 2:
        return RegimeAnalysisResult(
            n_regimes=0, regime_labels=[], regime_counts=[], regime_avg_pnl=[],
            regime_sharpe=[], regime_win_rate=[], regime_avg_drawdown=[],
            current_regime="unknown",
            interpretation="insufficient data for regime analysis",
        )

    # Rolling volatility
    rolling_vol = pnl.rolling(window=window, min_periods=window // 2).std().bfill()

    # Classify into regimes using quantiles
    if n_regimes == 3:
        labels = ["low_volatility", "medium_volatility", "high_volatility"]
        q33 = rolling_vol.quantile(0.33)
        q66 = rolling_vol.quantile(0.66)
        regime = pd.Series("medium_volatility", index=pnl.index)
        regime[rolling_vol <= q33] = "low_volatility"
        regime[rolling_vol >= q66] = "high_volatility"
    elif n_regimes == 2:
        labels = ["low_volatility", "high_volatility"]
        q50 = rolling_vol.quantile(0.50)
        regime = pd.Series("high_volatility", index=pnl.index)
        regime[rolling_vol <= q50] = "low_volatility"
    else:
        # Generic quantile-based
        labels = [f"regime_{i}" for i in range(n_regimes)]
        quantiles = np.linspace(0, 1, n_regimes + 1)
        thresholds = [rolling_vol.quantile(q) for q in quantiles]
        regime = pd.Series(labels[-1], index=pnl.index)
        for i in range(n_regimes - 1):
            regime[rolling_vol <= thresholds[i + 1]] = labels[i]

    # Analyze each regime
    actual_labels = []
    counts = []
    avg_pnls = []
    sharpes = []
    win_rates = []
    avg_dds = []

    for label in labels:
        mask = regime == label
        if mask.sum() == 0:
            continue
        rpnl = pnl[mask].to_numpy()
        actual_labels.append(label)
        counts.append(int(mask.sum()))
        avg_pnls.append(round(float(np.mean(rpnl)), 2))
        std = float(np.std(rpnl, ddof=1)) if len(rpnl) > 1 else 1e-10
        sharpes.append(round(float(np.mean(rpnl) / std) if std > 1e-10 else 0.0, 4))
        win_rates.append(round(float(np.mean(rpnl > 0) * 100), 1))

        eq = np.cumsum(rpnl)
        peak = np.maximum.accumulate(eq)
        dd = eq - peak
        avg_dds.append(round(float(np.mean(dd)), 2))

    current = str(regime.iloc[-1])

    # Interpretation
    if len(sharpes) >= 2:
        best = actual_labels[np.argmax(sharpes)]
        worst = actual_labels[np.argmin(sharpes)]
        interp = f"Best performance in {best} regime (Sharpe {max(sharpes):.2f}), worst in {worst} (Sharpe {min(sharpes):.2f}). Currently in {current}."
    else:
        interp = "Insufficient regime diversity for comparison."

    return RegimeAnalysisResult(
        n_regimes=len(actual_labels),
        regime_labels=actual_labels,
        regime_counts=counts,
        regime_avg_pnl=avg_pnls,
        regime_sharpe=sharpes,
        regime_win_rate=win_rates,
        regime_avg_drawdown=avg_dds,
        current_regime=current,
        interpretation=interp,
    )
