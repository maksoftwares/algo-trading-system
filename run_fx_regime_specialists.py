from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parent / "forex" / "fx-regime-specialists-gold-trajectory-v1"
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from fx_regime_specialists.campaign import (  # noqa: E402
    SPECIALIST_NAMES,
    active_fx_days,
    aggregate_fx_h1,
    build_state_table,
    generate_signals,
    load_context_h1,
    load_fx_m5,
    metric_block,
    remove_top_winners,
    route_portfolio,
    serialize,
    sha256_file,
    simulate_specialist,
    summarize_specialist,
    verify_preregistration,
)


def main() -> int:
    config_path = PACKAGE_ROOT / "config" / "frozen_campaign.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_root = PACKAGE_ROOT / "outputs"
    cache_root = output_root / "cache"
    output_root.mkdir(parents=True, exist_ok=True)
    prereg_hashes = verify_preregistration(PACKAGE_ROOT)

    start = pd.Timestamp(config["data"]["start_utc"])
    end = pd.Timestamp(config["data"]["end_utc"])
    raw_root = Path(config["data"]["dukascopy_raw_root"])
    bar_root = Path(config["data"]["fx_bar_root"])

    context = {}
    context_manifests = {}
    for symbol in config["data"]["context_symbols"]:
        context[symbol], context_manifests[symbol] = load_context_h1(
            raw_root, symbol, start, end, cache_root
        )
    m5 = {
        symbol: load_fx_m5(bar_root, symbol, start, end)
        for symbol in config["data"]["trade_symbols"]
    }
    h1 = {symbol: aggregate_fx_h1(frame) for symbol, frame in m5.items()}
    state = build_state_table(
        context["DOLLARIDXUSD"],
        context["USTBONDTRUSD"],
        h1,
        config["classifier"],
    )
    signals = generate_signals(state, config)
    trades = {}
    summaries = {}
    for name, signal_frame in signals.items():
        specialist_cfg = config["specialists"][name]
        symbol = specialist_cfg["symbol"]
        trades[name] = simulate_specialist(
            signal_frame,
            m5[symbol],
            specialist_cfg,
            config["execution"],
            config["quarantine"],
        )
        summaries[name] = summarize_specialist(
            trades[name], config["windows"], config["admission"]
        )
        trades[name].to_csv(output_root / f"{name}_trades.csv", index=False)

    admitted = [name for name, summary in summaries.items() if summary["admitted"]]
    portfolio = route_portfolio(trades, admitted, config["router"])
    if not portfolio.empty:
        portfolio.to_csv(output_root / "routed_portfolio_trades.csv", index=False)
    first_window = min(pd.Timestamp(value[0]) for value in config["windows"].values())
    last_window = max(pd.Timestamp(value[1]) for value in config["windows"].values())
    active_days = active_fx_days(m5, first_window, last_window)
    portfolio_overall = metric_block(portfolio)
    portfolio_top_removed = metric_block(remove_top_winners(portfolio))
    portfolio_stressed = metric_block(portfolio, "extra_half_pip_stress_r") if not portfolio.empty else metric_block(portfolio)
    portfolio_windows = {}
    for name, (window_start, window_end) in config["windows"].items():
        if portfolio.empty:
            subset = portfolio
        else:
            subset = portfolio[
                (portfolio["entry_time_utc"] >= pd.Timestamp(window_start))
                & (portfolio["entry_time_utc"] <= pd.Timestamp(window_end))
            ]
        portfolio_windows[name] = metric_block(subset)
    frequency = len(portfolio) / active_days if active_days else 0.0
    portfolio_survivor = bool(admitted) and (
        portfolio_overall["profit_factor"] >= config["admission"]["portfolio_minimum_profit_factor"]
        and all(block["net_r"] > 0 for block in portfolio_windows.values())
        and portfolio_top_removed["net_r"] > 0
        and portfolio_stressed["net_r"] > 0
        and frequency >= config["admission"]["portfolio_minimum_active_day_frequency"]
    )
    portfolio_status = (
        "NO_PORTFOLIO_FORMED"
        if not admitted
        else ("RESEARCH_PORTFOLIO_SURVIVOR" if portfolio_survivor else "ROUTED_PORTFOLIO_REJECTED")
    )

    coverage = {
        "context": context_manifests,
        "fx": {
            symbol: {
                "path": str(bar_root / f"{symbol}_M5_BIDASK.parquet"),
                "sha256": sha256_file(bar_root / f"{symbol}_M5_BIDASK.parquet"),
                "m5_rows": len(frame),
                "first_utc": frame.index.min().isoformat(),
                "last_utc": frame.index.max().isoformat(),
                "h1_rows": len(h1[symbol]),
            }
            for symbol, frame in m5.items()
        },
        "common_h1_rows": len(state),
        "common_first_utc": state.index.min().isoformat(),
        "common_last_utc": state.index.max().isoformat(),
        "active_fx_days": active_days,
    }
    regime_counts = (
        state.groupby(["direction", "volatility", "phase"], dropna=False)
        .size()
        .sort_values(ascending=False)
        .rename("bars")
        .reset_index()
        .to_dict(orient="records")
    )
    result = {
        "campaign_id": config["campaign_id"],
        "status": portfolio_status,
        "research_only": True,
        "preregistration_hashes": prereg_hashes,
        "config_sha256": sha256_file(config_path),
        "coverage": coverage,
        "regime_counts": regime_counts,
        "signals": {name: len(frame) for name, frame in signals.items()},
        "specialists": summaries,
        "admitted_specialists": admitted,
        "portfolio": {
            "status": portfolio_status,
            "overall": portfolio_overall,
            "windows": portfolio_windows,
            "top_5_percent_winners_removed": portfolio_top_removed,
            "extra_half_pip_round_trip": portfolio_stressed,
            "active_fx_days": active_days,
            "trades_per_active_fx_day": frequency,
        },
        "boundary": {
            "mt5_or_broker_runtime_used": False,
            "orders_or_accounts_touched": False,
            "threshold_search_used": False,
            "post_outcome_parameter_edits_used": False,
            "all_history_is_development_evidence": True,
        },
    }
    result = serialize(result)
    json_path = output_root / "CAMPAIGN_RESULT.json"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    (output_root / "DATA_COVERAGE.json").write_text(
        json.dumps(serialize(coverage), indent=2), encoding="utf-8"
    )
    report_path = PACKAGE_ROOT / "FOREX_REGIME_SPECIALIST_CAMPAIGN_VERDICT_2026_07_27.md"
    report_path.write_text(render_report(result), encoding="utf-8")
    print(json.dumps({"status": portfolio_status, "specialists": summaries, "portfolio": result["portfolio"]}, indent=2, default=str))
    return 0


def render_report(result: dict) -> str:
    lines = [
        "# Forex Regime-Specialist Campaign Verdict — 2026-07-27",
        "",
        f"Status: `{result['status']}`",
        "",
        "Boundary: offline research only. No MT5, broker, account, chart, EA attachment, or order action occurred.",
        "",
        "## Outcome",
        "",
        "| Specialist | Signals | Trades | PF | Net R | Max DD R | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for name, summary in result["specialists"].items():
        overall = summary["overall"]
        lines.append(
            f"| {SPECIALIST_NAMES[name]} | {result['signals'][name]} | {overall['trades']} | "
            f"{fmt(overall['profit_factor'])} | {fmt(overall['net_r'])} | "
            f"{fmt(overall['max_drawdown_r'])} | `{summary['status']}` |"
        )
    lines += [
        "",
        "## Chronological Standalone Evidence",
        "",
    ]
    for name, summary in result["specialists"].items():
        lines += [
            f"### {SPECIALIST_NAMES[name]}",
            "",
            "| Window | Trades | PF | Net R | Expectancy R |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        for window, block in summary["windows"].items():
            lines.append(
                f"| {window} | {block['trades']} | {fmt(block['profit_factor'])} | "
                f"{fmt(block['net_r'])} | {fmt(block['expectancy_r'])} |"
            )
        lines += [
            "",
            f"- Top-5%-winner removal net: {fmt(summary['top_5_percent_winners_removed']['net_r'])}R.",
            f"- Additional 0.5-pip round-trip stress net: {fmt(summary['extra_half_pip_round_trip']['net_r'])}R.",
            "",
        ]
    portfolio = result["portfolio"]
    lines += [
        "## Router",
        "",
        f"- Admitted specialists: {', '.join(result['admitted_specialists']) if result['admitted_specialists'] else 'none'}.",
        f"- Router decision: `{portfolio['status']}`.",
        f"- Routed trades: {portfolio['overall']['trades']}.",
        f"- Routed PF: {fmt(portfolio['overall']['profit_factor'])}.",
        f"- Trades per active FX day: {fmt(portfolio['trades_per_active_fx_day'], 4)} versus the diagnostic target of 1.0.",
        "",
        "A failed component was not rescued by combination. If no expert passed standalone admission, no portfolio was formed.",
        "",
        "## Interpretation",
        "",
        "This campaign applies the Gold regime-specialist discipline, but it does not assume that the Gold result or these Forex mechanisms are valid. The frozen thresholds were evaluated once. No outcome-driven repair is included in this verdict.",
        "",
        "All historical windows are development evidence. Even a research survivor would require a separately preregistered confirmation and broker-authoritative parity work before any demo discussion.",
        "",
        "## Reproduction",
        "",
        "Run from the repository root with the project environment that provides pandas, NumPy, and PyArrow:",
        "",
        "```powershell",
        "python run_fx_regime_specialists.py",
        "```",
        "",
        f"Preregistration hashes verified: `{result['preregistration_hashes']}`.",
        f"Frozen config SHA-256: `{result['config_sha256']}`.",
    ]
    return "\n".join(lines) + "\n"


def fmt(value, digits: int = 4) -> str:
    if isinstance(value, str):
        return value
    return f"{float(value):.{digits}f}"


if __name__ == "__main__":
    raise SystemExit(main())
