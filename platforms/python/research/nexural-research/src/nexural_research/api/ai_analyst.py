"""AI Strategy Analyst — connects to Claude or OpenAI to provide
natural-language analysis and recommendations based on trade data.

Users bring their own API key. The system builds rich context from
the analysis engine and sends it to the AI for interpretation.
"""

from __future__ import annotations


import pandas as pd

from nexural_research.analyze.metrics import metrics_from_trades
from nexural_research.analyze.advanced_metrics import (
    risk_return_metrics,
    expectancy_metrics,
    trade_dependency_analysis,
    distribution_metrics,
    time_decay_analysis,
)
from nexural_research.analyze.advanced_robustness import (
    deflated_sharpe_ratio,
    regime_analysis,
)
from nexural_research.analyze.portfolio import benchmark_comparison


def build_strategy_context(df_trades: pd.DataFrame) -> str:
    """Build a comprehensive context string from trade data for the AI."""

    core = metrics_from_trades(df_trades)
    rr = risk_return_metrics(df_trades)
    exp = expectancy_metrics(df_trades)
    dep = trade_dependency_analysis(df_trades)
    dist = distribution_metrics(df_trades)
    decay = time_decay_analysis(df_trades)
    dsr = deflated_sharpe_ratio(df_trades, n_trials=100)
    regime = regime_analysis(df_trades)
    bench = benchmark_comparison(df_trades, n_random_sims=500)

    instruments = df_trades["instrument"].unique().tolist() if "instrument" in df_trades.columns else ["unknown"]
    strategies = df_trades["strategy"].unique().tolist() if "strategy" in df_trades.columns else ["unknown"]

    context = f"""## Strategy Analysis Data

### Instruments: {', '.join(str(i) for i in instruments)}
### Strategies: {', '.join(str(s) for s in strategies)}
### Total Trades: {core.n_trades}

### Core Performance Metrics
- Net Profit: ${core.net_profit:,.2f}
- Gross Profit: ${core.gross_profit:,.2f} | Gross Loss: ${core.gross_loss:,.2f}
- Win Rate: {core.win_rate*100:.1f}%
- Profit Factor: {core.profit_factor:.4f}
- Average Trade: ${core.avg_trade:,.2f}
- Average Win: ${core.avg_win:,.2f} | Average Loss: ${core.avg_loss:,.2f}
- Max Drawdown: ${core.max_drawdown:,.2f}
- Ulcer Index: {core.ulcer_index:.4f}

### Risk-Adjusted Returns
- Sharpe Ratio: {rr.sharpe_ratio} (annualized)
- Sortino Ratio: {rr.sortino_ratio}
- Calmar Ratio: {rr.calmar_ratio}
- Omega Ratio: {rr.omega_ratio}
- Tail Ratio: {rr.tail_ratio}
- Gain-to-Pain Ratio: {rr.gain_to_pain_ratio}
- Risk of Ruin: {rr.risk_of_ruin*100:.2f}%

### Expectancy & Position Sizing
- Expectancy per trade: ${exp.expectancy:,.4f}
- Payoff Ratio: {exp.payoff_ratio}
- Kelly Criterion: {exp.kelly_pct}%
- Half Kelly: {exp.half_kelly_pct}%
- Optimal f: {exp.optimal_f}

### Trade Dependency Analysis
- Z-Score: {dep.z_score} — {dep.z_interpretation}
- Serial Correlation (lag-1): {dep.serial_correlation} (p={dep.serial_p_value})
- Max Win Streak: {dep.streak_max_wins} | Max Loss Streak: {dep.streak_max_losses}
- Avg Win Streak: {dep.streak_avg_wins} | Avg Loss Streak: {dep.streak_avg_losses}

### Return Distribution
- Mean: ${dist.mean:,.4f} | Median: ${dist.median:,.4f} | Std Dev: ${dist.std:,.4f}
- Skewness: {dist.skewness} | Kurtosis: {dist.kurtosis}
- Normally Distributed: {dist.is_normal} (JB p={dist.jarque_bera_p})
- VaR 95%: ${dist.var_95:,.2f} | CVaR 95%: ${dist.cvar_95:,.2f}

### Edge Stability
- {decay.decay_interpretation}

### Overfitting Detection (Deflated Sharpe Ratio)
- Observed Sharpe: {dsr.observed_sharpe}
- {dsr.interpretation}

### Regime Analysis
- {regime.interpretation}
- Regimes: {', '.join(f'{label} (n={cnt}, avg=${avg:.2f}, Sharpe={sr:.2f})' for label, cnt, avg, sr in zip(regime.regime_labels, regime.regime_counts, regime.regime_avg_pnl, regime.regime_sharpe))}

### Benchmark Comparison
- Strategy Net: ${bench.strategy_net:,.2f} | Sharpe: {bench.strategy_sharpe}
- Random Entry Mean Net: ${bench.random_net_mean:,.2f} | Sharpe: {bench.random_sharpe_mean}
- Outperforms {bench.pct_better_than_random}% of random strategies
- Alpha vs Random: {bench.alpha_vs_random}
"""
    return context


SYSTEM_PROMPT = """You are an elite quantitative strategy analyst working at an institutional trading firm. You analyze NinjaTrader backtesting results with the rigor of a prop desk quant.

Your role:
1. Provide brutally honest assessment — never sugarcoat bad results
2. Identify specific, actionable improvements the trader can make
3. Think like a risk manager: capital preservation comes first
4. Reference specific metrics to support every claim
5. Suggest concrete parameter adjustments, filter additions, or structural changes
6. Compare against institutional benchmarks (Sharpe > 1.5 is good, > 2.5 is excellent)
7. Flag any signs of overfitting, curve-fitting, or data mining bias
8. Consider market microstructure and execution realism

Format your responses with clear sections, bullet points, and specific numbers. Be the analyst that helps traders build genuinely profitable automation systems, not one that tells them what they want to hear."""


async def query_anthropic(api_key: str, context: str, user_message: str) -> str:
    """Send analysis to Claude API."""
    import httpx

    messages = [
        {"role": "user", "content": f"{context}\n\n---\n\nTrader's question: {user_message}"},
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 4096,
                "system": SYSTEM_PROMPT,
                "messages": messages,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]


async def query_openai(api_key: str, context: str, user_message: str) -> str:
    """Send analysis to OpenAI API."""
    import httpx

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{context}\n\n---\n\nTrader's question: {user_message}"},
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o",
                "max_tokens": 4096,
                "messages": messages,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def query_perplexity(api_key: str, context: str, user_message: str) -> str:
    """Send analysis to Perplexity API.

    Uses Perplexity's sonar-pro model which has real-time web access,
    enabling it to cross-reference market conditions and current data.
    """
    import httpx

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\nYou also have web access. When relevant, cross-reference current market conditions, recent news about the traded instruments, and known quantitative research to enhance your analysis."},
        {"role": "user", "content": f"{context}\n\n---\n\nTrader's question: {user_message}"},
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar-pro",
                "max_tokens": 4096,
                "messages": messages,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
