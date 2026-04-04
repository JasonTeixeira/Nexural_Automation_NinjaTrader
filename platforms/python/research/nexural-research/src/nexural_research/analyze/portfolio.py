"""Multi-strategy portfolio analysis and benchmark comparison.

Covers: correlation matrix, diversification benefit, combined equity,
portfolio optimization, and benchmark comparison (buy-and-hold, random entry).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from nexural_research.analyze.equity import max_drawdown


# ---------------------------------------------------------------------------
# Multi-strategy correlation & portfolio
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StrategyCorrelation:
    """Correlation between two strategies."""

    strategy_a: str
    strategy_b: str
    pearson_r: float
    pearson_p: float
    spearman_r: float
    spearman_p: float


@dataclass(frozen=True)
class PortfolioMetrics:
    """Combined portfolio metrics for multiple strategies."""

    n_strategies: int
    strategy_names: list[str]
    individual_net_profits: list[float]
    individual_sharpes: list[float]
    individual_max_drawdowns: list[float]
    combined_net_profit: float
    combined_sharpe: float
    combined_max_drawdown: float
    diversification_benefit: float  # % MDD reduction vs worst individual
    correlation_matrix: list[list[float]]
    correlations: list[StrategyCorrelation]
    optimal_weights: list[float]  # equal risk contribution weights


def portfolio_analysis(
    df_trades: pd.DataFrame,
    *,
    strategy_col: str = "strategy",
    ts_col: str = "exit_time",
) -> PortfolioMetrics:
    """Analyze a portfolio of multiple strategies from the same trades DataFrame."""

    if strategy_col not in df_trades.columns:
        raise ValueError(f"missing strategy column: {strategy_col}")

    strategies = sorted(df_trades[strategy_col].dropna().unique().tolist())
    n_strats = len(strategies)

    if n_strats < 2:
        # Single strategy — return basic metrics
        pnl = pd.to_numeric(df_trades["profit"], errors="coerce").fillna(0.0).to_numpy()
        eq = np.cumsum(pnl)
        std = float(np.std(pnl, ddof=1)) if len(pnl) > 1 else 1e-10
        sharpe = float(np.mean(pnl) / std * np.sqrt(252)) if std > 1e-10 else 0.0
        mdd = float(max_drawdown(pd.Series(eq)))

        return PortfolioMetrics(
            n_strategies=1,
            strategy_names=strategies if strategies else ["default"],
            individual_net_profits=[round(float(eq[-1]), 2)] if len(eq) > 0 else [0.0],
            individual_sharpes=[round(sharpe, 4)],
            individual_max_drawdowns=[round(mdd, 2)],
            combined_net_profit=round(float(eq[-1]), 2) if len(eq) > 0 else 0.0,
            combined_sharpe=round(sharpe, 4),
            combined_max_drawdown=round(mdd, 2),
            diversification_benefit=0.0,
            correlation_matrix=[[1.0]],
            correlations=[],
            optimal_weights=[1.0],
        )

    # Build daily PnL series for each strategy
    df = df_trades.copy()
    if ts_col in df.columns:
        df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
    elif "entry_time" in df.columns:
        ts_col = "entry_time"
        df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")

    df["profit_num"] = pd.to_numeric(df["profit"], errors="coerce").fillna(0.0)

    # Aggregate to daily level per strategy
    if ts_col in df.columns:
        df["date"] = df[ts_col].dt.date
        daily = df.groupby(["date", strategy_col])["profit_num"].sum().unstack(fill_value=0.0)
    else:
        # No timestamps — use trade index
        daily = pd.DataFrame()
        for s in strategies:
            mask = df[strategy_col] == s
            daily[s] = pd.to_numeric(df.loc[mask, "profit"], errors="coerce").fillna(0.0).reset_index(drop=True)
        daily = daily.fillna(0.0)

    # Ensure all strategies present
    for s in strategies:
        if s not in daily.columns:
            daily[s] = 0.0

    daily = daily[strategies].fillna(0.0)

    # Individual metrics
    individual_nets = []
    individual_sharpes = []
    individual_mdds = []

    for s in strategies:
        s_pnl = daily[s].to_numpy()
        eq = np.cumsum(s_pnl)
        individual_nets.append(round(float(eq[-1]) if len(eq) > 0 else 0.0, 2))
        std = float(np.std(s_pnl, ddof=1)) if len(s_pnl) > 1 else 1e-10
        individual_sharpes.append(round(float(np.mean(s_pnl) / std * np.sqrt(252)) if std > 1e-10 else 0.0, 4))
        individual_mdds.append(round(float(max_drawdown(pd.Series(eq))), 2))

    # Combined portfolio (equal weight)
    combined_pnl = daily.sum(axis=1).to_numpy()
    combined_eq = np.cumsum(combined_pnl)
    combined_net = round(float(combined_eq[-1]) if len(combined_eq) > 0 else 0.0, 2)
    combined_std = float(np.std(combined_pnl, ddof=1)) if len(combined_pnl) > 1 else 1e-10
    combined_sharpe = round(float(np.mean(combined_pnl) / combined_std * np.sqrt(252)) if combined_std > 1e-10 else 0.0, 4)
    combined_mdd = round(float(max_drawdown(pd.Series(combined_eq))), 2)

    # Diversification benefit: % improvement in MDD vs worst individual
    worst_individual_mdd = min(individual_mdds)  # most negative
    div_benefit = round(
        (1.0 - abs(combined_mdd) / abs(worst_individual_mdd)) * 100 if abs(worst_individual_mdd) > 1e-10 else 0.0,
        2,
    )

    # Correlation matrix
    corr_matrix = daily.corr().to_numpy().tolist()
    correlations = []
    for i in range(n_strats):
        for j in range(i + 1, n_strats):
            a_vals = daily[strategies[i]].to_numpy()
            b_vals = daily[strategies[j]].to_numpy()
            if len(a_vals) > 2:
                pr, pp = sp_stats.pearsonr(a_vals, b_vals)
                sr, sp_val = sp_stats.spearmanr(a_vals, b_vals)
            else:
                pr, pp, sr, sp_val = 0.0, 1.0, 0.0, 1.0
            correlations.append(StrategyCorrelation(
                strategy_a=strategies[i],
                strategy_b=strategies[j],
                pearson_r=round(float(pr), 4),
                pearson_p=round(float(pp), 6),
                spearman_r=round(float(sr), 4),
                spearman_p=round(float(sp_val), 6),
            ))

    # Simple equal risk contribution weights (inverse volatility)
    vols = [float(np.std(daily[s].to_numpy(), ddof=1)) for s in strategies]
    inv_vols = [1.0 / v if v > 1e-10 else 0.0 for v in vols]
    total_inv = sum(inv_vols)
    weights = [round(iv / total_inv, 4) if total_inv > 0 else 1.0 / n_strats for iv in inv_vols]

    return PortfolioMetrics(
        n_strategies=n_strats,
        strategy_names=strategies,
        individual_net_profits=individual_nets,
        individual_sharpes=individual_sharpes,
        individual_max_drawdowns=individual_mdds,
        combined_net_profit=combined_net,
        combined_sharpe=combined_sharpe,
        combined_max_drawdown=combined_mdd,
        diversification_benefit=div_benefit,
        correlation_matrix=[[round(c, 4) for c in row] for row in corr_matrix],
        correlations=correlations,
        optimal_weights=weights,
    )


# ---------------------------------------------------------------------------
# Benchmark comparison
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BenchmarkComparison:
    """Compare strategy against benchmarks."""

    strategy_net: float
    strategy_sharpe: float
    strategy_mdd: float
    buyhold_net: float
    buyhold_sharpe: float
    buyhold_mdd: float
    random_net_mean: float
    random_net_std: float
    random_sharpe_mean: float
    random_mdd_mean: float
    pct_better_than_random: float
    alpha_vs_random: float  # strategy Sharpe - random mean Sharpe


def benchmark_comparison(
    df_trades: pd.DataFrame,
    *,
    n_random_sims: int = 1000,
    seed: int = 42,
) -> BenchmarkComparison:
    """Compare strategy performance vs buy-and-hold and random entry benchmarks.

    Random entry benchmark: randomizes entry direction while keeping
    the same trade timing and holding periods, showing what random
    luck would produce with the same market exposure.
    """

    pnl = pd.to_numeric(df_trades["profit"], errors="coerce").fillna(0.0).to_numpy()
    n = len(pnl)

    if n == 0:
        return BenchmarkComparison(
            strategy_net=0.0, strategy_sharpe=0.0, strategy_mdd=0.0,
            buyhold_net=0.0, buyhold_sharpe=0.0, buyhold_mdd=0.0,
            random_net_mean=0.0, random_net_std=0.0, random_sharpe_mean=0.0,
            random_mdd_mean=0.0, pct_better_than_random=0.0, alpha_vs_random=0.0,
        )

    # Strategy metrics
    eq = np.cumsum(pnl)
    strat_net = float(eq[-1])
    strat_std = float(np.std(pnl, ddof=1)) if n > 1 else 1e-10
    strat_sharpe = float(np.mean(pnl) / strat_std * np.sqrt(252)) if strat_std > 1e-10 else 0.0
    strat_mdd = float(max_drawdown(pd.Series(eq)))

    # Buy-and-hold benchmark: assume the total PnL spread linearly
    # (best approximation without price data)
    bh_pnl = np.full(n, strat_net / n)
    bh_eq = np.cumsum(bh_pnl)
    bh_net = float(bh_eq[-1])
    bh_std = float(np.std(bh_pnl, ddof=1)) if n > 1 else 1e-10
    bh_sharpe = float(np.mean(bh_pnl) / bh_std * np.sqrt(252)) if bh_std > 1e-10 else 0.0
    bh_mdd = float(max_drawdown(pd.Series(bh_eq)))

    # Random entry benchmark: randomly flip trade signs
    rng = np.random.default_rng(seed)
    random_sharpes = np.zeros(n_random_sims)
    random_nets = np.zeros(n_random_sims)
    random_mdds = np.zeros(n_random_sims)

    abs_pnl = np.abs(pnl)
    for i in range(n_random_sims):
        signs = rng.choice([-1.0, 1.0], size=n)
        rand_pnl = abs_pnl * signs
        rand_eq = np.cumsum(rand_pnl)
        random_nets[i] = rand_eq[-1]
        r_std = float(np.std(rand_pnl, ddof=1))
        random_sharpes[i] = float(np.mean(rand_pnl) / r_std * np.sqrt(252)) if r_std > 1e-10 else 0.0
        peak = np.maximum.accumulate(rand_eq)
        random_mdds[i] = float(np.min(rand_eq - peak))

    pct_better = float(np.mean(strat_net > random_nets) * 100)
    alpha = strat_sharpe - float(np.mean(random_sharpes))

    return BenchmarkComparison(
        strategy_net=round(strat_net, 2),
        strategy_sharpe=round(strat_sharpe, 4),
        strategy_mdd=round(strat_mdd, 2),
        buyhold_net=round(bh_net, 2),
        buyhold_sharpe=round(bh_sharpe, 4),
        buyhold_mdd=round(bh_mdd, 2),
        random_net_mean=round(float(np.mean(random_nets)), 2),
        random_net_std=round(float(np.std(random_nets)), 2),
        random_sharpe_mean=round(float(np.mean(random_sharpes)), 4),
        random_mdd_mean=round(float(np.mean(random_mdds)), 2),
        pct_better_than_random=round(pct_better, 1),
        alpha_vs_random=round(alpha, 4),
    )
