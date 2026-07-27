from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "forex" / "fx-regime-specialists-gold-trajectory-v1"
sys.path.insert(0, str(PACKAGE / "src"))

from fx_regime_specialists.campaign import (  # noqa: E402
    active_fx_days,
    aggregate_fx_h1,
    build_state_table,
    load_context_h1,
    load_fx_m5,
    metric_block,
    remove_top_winners,
    serialize,
    sha256_file,
    summarize_specialist,
)
from fx_regime_specialists.seed_decomposition import (  # noqa: E402
    assign_regime_ownership,
    generate_seed_signals,
    simulate_s1_cycle_exit,
)


def verify_lock() -> dict[str, str]:
    lock_path = PACKAGE / "FOREX_S1_ESTABLISHED_ALIGNED_CYCLE_EXIT_PREREG_2026_07_27.sha256.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("locked_before_cycle_exit_outcomes") is not True:
        raise RuntimeError("Cycle-exit trial was not locked before outcomes")
    checked = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE / relative)
        if actual != expected:
            raise RuntimeError(f"Cycle-exit preregistration hash mismatch: {relative}")
        checked[relative] = actual
    return checked


def main() -> int:
    lock_hashes = verify_lock()
    cycle_path = PACKAGE / "config" / "frozen_s1_cycle_exit.json"
    seed_path = PACKAGE / "config" / "frozen_seed_decomposition.json"
    base_path = PACKAGE / "config" / "frozen_campaign.json"
    cycle = json.loads(cycle_path.read_text(encoding="utf-8"))
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    base = json.loads(base_path.read_text(encoding="utf-8"))
    output = PACKAGE / "outputs" / "s1_cycle_exit"
    cache = PACKAGE / "outputs" / "cache"
    output.mkdir(parents=True, exist_ok=True)

    start = pd.Timestamp(cycle["data"]["start_utc"])
    end = pd.Timestamp(cycle["data"]["end_utc"])
    bar_root = Path(seed["data"]["fx_bar_root"])
    raw_root = Path(base["data"]["dukascopy_raw_root"])
    dxy, dxy_manifest = load_context_h1(raw_root, "DOLLARIDXUSD", start, end, cache)
    bond, bond_manifest = load_context_h1(raw_root, "USTBONDTRUSD", start, end, cache)
    m5 = {symbol: load_fx_m5(bar_root, symbol, start, end) for symbol in ("EURUSD", "GBPUSD", "USDJPY")}
    h1 = {symbol: aggregate_fx_h1(frame) for symbol, frame in m5.items()}
    state = build_state_table(dxy, bond, h1, base["classifier"])
    raw_signals = generate_seed_signals(m5["USDJPY"], seed["base_seed"])
    owned_signals = assign_regime_ownership(raw_signals, state)
    trades = simulate_s1_cycle_exit(
        owned_signals, m5["USDJPY"], seed["base_seed"], seed["execution"]
    )
    trades.to_csv(output / "FULL_TRADE_LEDGER.csv", index=False)
    full_summary = summarize_specialist(trades, cycle["windows"], cycle["admission"])
    admission_failures = []
    for window, block in full_summary["windows"].items():
        if block["trades"] < cycle["admission"]["minimum_trades_each_window"]:
            admission_failures.append(
                f"{window}: {block['trades']} trades < {cycle['admission']['minimum_trades_each_window']}"
            )
        if block["profit_factor"] < cycle["admission"]["minimum_profit_factor_each_window"]:
            admission_failures.append(
                f"{window}: PF {block['profit_factor']:.4f} < {cycle['admission']['minimum_profit_factor_each_window']:.2f}"
            )
        if block["expectancy_r"] <= cycle["admission"]["minimum_expectancy_r_each_window"]:
            admission_failures.append(
                f"{window}: expectancy {block['expectancy_r']:.4f}R <= {cycle['admission']['minimum_expectancy_r_each_window']:.2f}R"
            )

    six_start, six_end = map(pd.Timestamp, cycle["data"]["last_six_completed_months"])
    last_six = trades[
        (trades["entry_time_utc"] >= six_start) & (trades["entry_time_utc"] <= six_end)
    ].copy()
    last_six.to_csv(output / "LAST_6_MONTHS_TRADE_LEDGER.csv", index=False)
    monthly = {}
    for month_start in pd.date_range(six_start, six_end, freq="MS"):
        month_end = month_start + pd.offsets.MonthEnd(1) + pd.Timedelta(hours=23, minutes=59, seconds=59)
        subset = last_six[
            (last_six["entry_time_utc"] >= month_start) & (last_six["entry_time_utc"] <= month_end)
        ]
        monthly[month_start.strftime("%Y-%m")] = {
            **metric_block(subset),
            "pnl_usd_0_01_lot": float(subset["pnl_usd_0_01_lot"].sum()) if not subset.empty else 0.0,
        }
    last_six_overall = {
        **metric_block(last_six),
        "pnl_usd_0_01_lot": float(last_six["pnl_usd_0_01_lot"].sum()) if not last_six.empty else 0.0,
    }
    last_six_stress = metric_block(last_six, "extra_half_pip_stress_r")
    last_six_top_removed = metric_block(remove_top_winners(last_six))
    by_direction = {
        direction: metric_block(rows)
        for direction, rows in last_six.groupby("side")
    }
    by_exit = {
        reason: metric_block(rows)
        for reason, rows in last_six.groupby("exit_reason")
    }
    active_days = active_fx_days({"USDJPY": m5["USDJPY"]}, six_start, six_end)
    last_six_result = {
        "window": [six_start.isoformat(), six_end.isoformat()],
        "historical_status": "DEVELOPMENT_EVIDENCE_NOT_UNTOUCHED_CONFIRMATION",
        "overall": last_six_overall,
        "extra_half_pip_round_trip": last_six_stress,
        "top_5_percent_winners_removed": last_six_top_removed,
        "monthly": monthly,
        "direction": by_direction,
        "exit_reason": by_exit,
        "active_fx_days": active_days,
        "trades_per_active_fx_day": len(last_six) / active_days if active_days else 0.0,
    }
    result = serialize(
        {
            "campaign_id": cycle["campaign_id"],
            "status": full_summary["status"],
            "research_only": True,
            "preregistration_hashes": lock_hashes,
            "config_sha256": sha256_file(cycle_path),
            "source_hashes": {
                "classifier_config": sha256_file(base_path),
                "seed_config": sha256_file(seed_path),
                "dxy_source_chain": dxy_manifest["source_chain_sha256"],
                "bond_source_chain": bond_manifest["source_chain_sha256"],
                "usdjpy_m5": sha256_file(bar_root / "USDJPY_M5_BIDASK.parquet"),
            },
            "signal_census": {
                "raw_seed_signals": len(raw_signals),
                "owned_s1_signals": int((owned_signals["ownership"] == "s1_established_aligned_breakout").sum()),
                "executed_cycle_exit_trades": len(trades),
            },
            "full_history": full_summary,
            "admission_failures": admission_failures,
            "last_six_months": last_six_result,
            "boundary": {
                "only_change": "next_setup_cycle_exit",
                "signal_or_regime_threshold_changed": False,
                "stop_or_target_changed": False,
                "mt5_or_broker_runtime_used": False,
                "last_six_months_used_for_promotion": False,
            },
        }
    )
    (output / "RESULT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    verdict = PACKAGE / "FOREX_S1_ESTABLISHED_ALIGNED_CYCLE_EXIT_VERDICT_2026_07_27.md"
    verdict.write_text(render_full_verdict(result), encoding="utf-8")
    six_report = PACKAGE / "FOREX_S1_LAST_6_MONTHS_BACKTEST_2026_01_TO_2026_06.md"
    six_report.write_text(render_six_months(result), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


def render_full_verdict(result: dict) -> str:
    full = result["full_history"]
    overall = full["overall"]
    lines = [
        "# S1 Established-Aligned Next-Cycle Exit Verdict — 2026-07-27",
        "",
        f"Status: `{result['status']}`",
        "",
        "Boundary: offline research only. The sole change was the hash-locked next-active-06:00 UTC lifecycle exit.",
        "",
        "## Full-History Result",
        "",
        f"- Trades: {overall['trades']}",
        f"- PF: {fmt(overall['profit_factor'])}",
        f"- Net: {fmt(overall['net_r'])}R",
        f"- Expectancy: {fmt(overall['expectancy_r'])}R",
        f"- Win rate: {pct(overall['win_rate'])}",
        f"- Maximum drawdown: {fmt(overall['max_drawdown_r'])}R",
        f"- Executed-trade change versus frozen S1: {overall['trades'] - 70:+d}",
        "",
        "| Window | Trades | PF | Net R | Expectancy R | Max DD R |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for window, block in full["windows"].items():
        lines.append(
            f"| {window} | {block['trades']} | {fmt(block['profit_factor'])} | "
            f"{fmt(block['net_r'])} | {fmt(block['expectancy_r'])} | {fmt(block['max_drawdown_r'])} |"
        )
    lines += [
        "",
        f"- Top-5%-winner removal net: {fmt(full['top_5_percent_winners_removed']['net_r'])}R.",
        f"- Additional 0.5-pip round-trip stress net: {fmt(full['extra_half_pip_round_trip']['net_r'])}R.",
        "",
        "## Admission Failures",
        "",
        *[f"- {failure}" for failure in result["admission_failures"]],
        "",
        "The lifecycle hypothesis is closed because it did not increase the sample. No further exit tuning is authorized by this result.",
        "",
        "The result remains historical development evidence even if every gate passes.",
    ]
    return "\n".join(lines) + "\n"


def render_six_months(result: dict) -> str:
    six = result["last_six_months"]
    overall = six["overall"]
    lines = [
        "# S1 Last Six Completed Months Backtest — January to June 2026",
        "",
        f"Status: `{six['historical_status']}`",
        "",
        "This is the requested historical backtest. These months were already inside the adaptive-exam archive and are not untouched confirmation.",
        "",
        "## Summary",
        "",
        f"- Trades: {overall['trades']}",
        f"- PF: {fmt(overall['profit_factor'])}",
        f"- Net: {fmt(overall['net_r'])}R",
        f"- Illustrative 0.01-lot P/L: ${overall['pnl_usd_0_01_lot']:.2f}",
        f"- Expectancy: {fmt(overall['expectancy_r'])}R/trade",
        f"- Win rate: {pct(overall['win_rate'])}",
        f"- Maximum drawdown: {fmt(overall['max_drawdown_r'])}R",
        f"- Extra 0.5-pip stress: {fmt(six['extra_half_pip_round_trip']['net_r'])}R",
        f"- After removing the largest winner: {fmt(six['top_5_percent_winners_removed']['net_r'])}R",
        f"- Active FX days: {six['active_fx_days']}",
        f"- Trades per active FX day: {six['trades_per_active_fx_day']:.4f}",
        "",
        "## Monthly",
        "",
        "| Month | Trades | PF | Net R | Win rate | Max DD R | 0.01-lot USD |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for month, block in six["monthly"].items():
        lines.append(
            f"| {month} | {block['trades']} | {fmt(block['profit_factor'])} | "
            f"{fmt(block['net_r'])} | {pct(block['win_rate'])} | "
            f"{fmt(block['max_drawdown_r'])} | ${block['pnl_usd_0_01_lot']:.2f} |"
        )
    lines += [
        "",
        "## Direction",
        "",
        "| Side | Trades | PF | Net R |",
        "| --- | ---: | ---: | ---: |",
    ]
    for side, block in six["direction"].items():
        lines.append(f"| {side} | {block['trades']} | {fmt(block['profit_factor'])} | {fmt(block['net_r'])} |")
    lines += [
        "",
        "## Exit Reasons",
        "",
        "| Exit | Trades | Net R |",
        "| --- | ---: | ---: |",
    ]
    for reason, block in six["exit_reason"].items():
        lines.append(f"| {reason} | {block['trades']} | {fmt(block['net_r'])} |")
    lines += [
        "",
        "Execution uses next-M5 bid/ask prices, embedded spread, 0.1 pip adverse slippage per side, and stop-first resolution on ambiguous bars.",
        "The positive normalized result is concentrated: removing the largest winner leaves the six-month slice negative.",
        "",
        "The complete ledger is stored at `outputs/s1_cycle_exit/LAST_6_MONTHS_TRADE_LEDGER.csv`.",
    ]
    return "\n".join(lines) + "\n"


def fmt(value: float | str) -> str:
    if isinstance(value, str):
        return value
    if not math.isfinite(float(value)):
        return "Infinity"
    return f"{float(value):.4f}"


def pct(value: float) -> str:
    return f"{100.0 * float(value):.2f}%"


if __name__ == "__main__":
    raise SystemExit(main())
