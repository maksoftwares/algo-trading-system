from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from run_a3_signal_quality_offline_discovery import (
    Bar,
    RawSignal,
    VirtualTrade,
    apply_b0_comparisons,
    average_range,
    body_to_range,
    build_data_manifest,
    candidate_metrics,
    close_location,
    derive_m15,
    derive_weekly,
    exit_index_for_trade,
    fmt_time,
    generate_breakout_retest_signals,
    load_bars,
    parse_time,
    pct,
    render_markdown,
    sha256,
    simulate_trade,
    trade_net_r,
    with_indicators,
    write_csv,
    write_json,
)


PHASE0_BARS = Path("..") / "xauusd-phase0" / "data" / "processed" / "bars" / "dukascopy" / "XAUUSD"
DISCOVERY_START = datetime(2025, 1, 2)
DISCOVERY_END = datetime(2025, 7, 1)
WARMUP_START = datetime(2024, 1, 1)
CANDIDATE_ID = "A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2"
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "A3_SIGNAL_QUALITY_EXTENDED_DISCOVERY_V2_CANDIDATE_2026_06_18.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "A3_SIGNAL_QUALITY_EXTENDED_DISCOVERY_V2_CANDIDATE_2026_06_18.md"
DEFAULT_TRADES_CSV = Path("outputs") / "reports" / "A3_SIGNAL_QUALITY_EXTENDED_DISCOVERY_V2_CANDIDATE_TRADES_2026_06_18.csv"


def run_extended_discovery(
    phase1_root: Path,
    *,
    output_json: Path | None = None,
    output_md: Path | None = None,
    trades_csv: Path | None = None,
) -> dict[str, Any]:
    phase1_root = phase1_root.resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = (output_md or phase1_root / DEFAULT_OUTPUT_MD).resolve()
    trades_csv = (trades_csv or phase1_root / DEFAULT_TRADES_CSV).resolve()
    phase0_bars = (phase1_root / PHASE0_BARS).resolve()

    m5_path = phase0_bars / "M5" / "XAUUSD_dukascopy_M5_20250102_20250701.csv"
    h1_path = phase0_bars / "H1" / "XAUUSD_dukascopy_H1_20160101_20250701_derived_from_m5.csv"
    d1_path = phase0_bars / "D1" / "XAUUSD_dukascopy_D1_20160101_20250701_derived_from_m5.csv"

    m5 = load_phase0_bars(m5_path, DISCOVERY_START, DISCOVERY_END)
    h1 = with_indicators(load_phase0_bars(h1_path, WARMUP_START, DISCOVERY_END), ema_periods=(20,))
    d1 = with_indicators(load_phase0_bars(d1_path, WARMUP_START, DISCOVERY_END), ema_periods=(20, 50))
    m15 = with_indicators(derive_m15(m5), ema_periods=(20,))
    weekly = derive_weekly(d1["bars"])

    raw_signals = generate_breakout_retest_signals(m5, h1, d1, weekly)
    raw_outcomes = {signal.signal_id: simulate_trade(signal, m5) for signal in raw_signals}
    candidates: dict[str, Callable[[RawSignal], bool]] = {
        "B0_RAW_ALL_SESSION": lambda _signal: True,
        CANDIDATE_ID: lambda signal: soft_retest_v2(signal, m5),
    }
    metrics, trades = evaluate_candidate_predicates(raw_signals, raw_outcomes, m5, candidates)
    selected = next(row for row in metrics if row["candidate_id"] == CANDIDATE_ID)
    decision = "SELECT_CANDIDATE_FOR_V2_LOCK" if selected["v2_registration_eligible"] else "STOP_NO_CANDIDATE"
    manifest = build_data_manifest(
        [m5_path, h1_path, d1_path],
        extra={
            "source": "phase0_dukascopy_offline_bars",
            "discovery_start_utc": fmt_time(DISCOVERY_START),
            "discovery_end_utc": fmt_time(DISCOVERY_END),
            "raw_signals": len(raw_signals),
            "candidate_id": CANDIDATE_ID,
        },
    )
    payload = {
        "account": "1033669",
        "boundary": (
            "Offline historical discovery only. Uses phase0 Dukascopy XAUUSD bars. "
            "No MT5 runtime, profile, preset, order, position, or broker action touched."
        ),
        "candidate_id": CANDIDATE_ID,
        "decision": decision,
        "status": "PASS",
        "data_status": "HISTORICAL_DISCOVERY_NOT_PROMOTION_EVIDENCE",
        "candidate_rule": candidate_rule(),
        "candidate_metrics": metrics,
        "data_manifest": manifest,
        "outputs": {
            "json": str(output_json),
            "markdown": str(output_md),
            "trades_csv": str(trades_csv),
        },
    }
    write_json(output_json, payload)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_extended_markdown(payload), encoding="utf-8")
    write_csv(trades_csv, [asdict(row) for row in trades], list(asdict(trades[0]).keys()) if trades else list(asdict(empty_trade()).keys()))
    return payload


def soft_retest_v2(signal: RawSignal, m5: list[Bar]) -> bool:
    bars_after_break = signal.retest_index - signal.break_index
    if bars_after_break < 1 or bars_after_break > 15:
        return False
    retest_atr = average_range(m5, signal.confirmation_index, 2, 14)
    if retest_atr <= 0.0:
        return False
    retest = m5[signal.retest_index]
    confirmation = m5[signal.confirmation_index]
    if signal.direction == "LONG":
        if (retest.close - signal.level_price) / retest_atr < 0.05:
            return False
        if confirmation.close <= signal.level_price:
            return False
    else:
        if (signal.level_price - retest.close) / retest_atr < 0.05:
            return False
        if confirmation.close >= signal.level_price:
            return False
    body_range = body_to_range(confirmation)
    if body_range is None or body_range < 0.45:
        return False
    loc = close_location(confirmation)
    if loc is None:
        return False
    if signal.direction == "LONG":
        return loc >= 0.60
    return loc <= 0.40


def candidate_rule() -> dict[str, Any]:
    return {
        "candidate_id": CANDIDATE_ID,
        "family": "breakout_retest",
        "bars_after_break": "1..15 completed M5 bars",
        "retest_atr_window": "14 completed M5 bars from the retest bar back through 13 older bars; this includes the completed retest bar.",
        "retest_close_margin": "LONG retest close >= level + 0.05 ATR; SHORT retest close <= level - 0.05 ATR",
        "confirmation_body_to_range": ">= 0.45",
        "confirmation_directional_close_location": "LONG close location >= 0.60; SHORT close location <= 0.40",
        "exit_model": "fixed 1.50R, unchanged",
        "position_model": "one virtual position per candidate",
    }


def evaluate_candidate_predicates(
    raw_signals: list[RawSignal],
    raw_outcomes: dict[str, VirtualTrade | None],
    m5: list[Bar],
    candidates: dict[str, Callable[[RawSignal], bool]],
) -> tuple[list[dict[str, Any]], list[VirtualTrade]]:
    metrics_rows: list[dict[str, Any]] = []
    all_trades: list[VirtualTrade] = []
    for candidate_id, predicate in candidates.items():
        opened_trades: list[VirtualTrade] = []
        accepted = 0
        blocked_raw_final_rs: list[float] = []
        available_at_index = -1
        for signal in raw_signals:
            raw_trade = raw_outcomes.get(signal.signal_id)
            keep = predicate(signal)
            if keep:
                accepted += 1
                if raw_trade is not None and signal.confirmation_index > available_at_index:
                    clone = VirtualTrade(**asdict(raw_trade))
                    clone.candidate_id = candidate_id
                    opened_trades.append(clone)
                    all_trades.append(clone)
                    available_at_index = exit_index_for_trade(raw_trade, m5)
            elif raw_trade is not None:
                blocked_raw_final_rs.append(trade_net_r(raw_trade))
        metrics = candidate_metrics(
            candidate_id,
            raw_signals,
            accepted,
            opened_trades,
            blocked_raw_final_rs,
            None,
            None,
            None,
        )
        metrics["sample_rows"] = [asdict(row) for row in opened_trades[:5]]
        metrics["blocked_bucket_expectancy_r"] = round(sum(blocked_raw_final_rs) / len(blocked_raw_final_rs), 4) if blocked_raw_final_rs else None
        metrics["kept_bucket_expectancy_r"] = metrics["expectancy_r"]
        metrics["blocked_bucket_worse_than_kept"] = (
            metrics["blocked_bucket_expectancy_r"] is not None
            and metrics["expectancy_r"] is not None
            and metrics["blocked_bucket_expectancy_r"] < metrics["expectancy_r"]
        )
        metrics["candidate_role"] = "SELECTED_V2_DISCOVERY_CANDIDATE" if candidate_id == CANDIDATE_ID else "BASELINE"
        metrics["promotion_evidence"] = False
        metrics["data_limitation"] = "Historical phase0 Dukascopy M5-bar replay only; requires fresh validation."
        metrics["direction_counts"] = direction_counts(opened_trades)
        metrics_rows.append(metrics)
    apply_b0_comparisons(metrics_rows)
    return metrics_rows, all_trades


def direction_counts(trades: list[VirtualTrade]) -> dict[str, int]:
    counts = {"LONG": 0, "SHORT": 0}
    for trade in trades:
        counts[trade.direction] = counts.get(trade.direction, 0) + 1
    return counts


def load_phase0_bars(path: Path, start: datetime, end: datetime) -> list[Bar]:
    bars: list[Bar] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            bar_start = parse_time(row.get("bar_start_utc") or row.get("timestamp_utc") or "")
            bar_end = parse_time(row.get("bar_end_utc") or row.get("timestamp_utc") or "")
            if bar_start is None or bar_start < start or bar_start >= end:
                continue
            spread_raw = row.get("spread_close_points") or row.get("spread_median_points") or "0"
            try:
                spread = float(spread_raw)
            except ValueError:
                spread = 0.0
            bars.append(
                Bar(
                    start=bar_start,
                    end=bar_end or bar_start,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    spread=spread,
                )
            )
    return bars


def render_extended_markdown(payload: dict[str, Any]) -> str:
    selected = next(row for row in payload["candidate_metrics"] if row["candidate_id"] == payload["candidate_id"])
    b0 = next(row for row in payload["candidate_metrics"] if row["candidate_id"] == "B0_RAW_ALL_SESSION")
    lines = [
        "# A3 Signal Quality Extended Discovery V2 Candidate - 2026-06-18",
        "",
        f"Status: `{payload['status']}`",
        f"Decision: `{payload['decision']}`",
        "",
        payload["boundary"],
        "",
        "## Selected Candidate",
        "",
        f"Candidate: `{payload['candidate_id']}`",
        "",
        "| Metric | B0 | Candidate |",
        "| --- | ---: | ---: |",
        f"| Accepted signals | {b0['accepted_signals']} | {selected['accepted_signals']} |",
        f"| Signal retention | {b0['signal_retention_pct']}% | {selected['signal_retention_pct']}% |",
        f"| Opened virtual trades | {b0['opened_virtual_trades']} | {selected['opened_virtual_trades']} |",
        f"| Trade retention vs B0 | {b0['virtual_trade_retention_pct']}% | {selected['virtual_trade_retention_pct']}% |",
        f"| Median weekly trade retention | {b0['median_weekly_trade_retention_pct']}% | {selected['median_weekly_trade_retention_pct']}% |",
        f"| Net profit factor | {b0['profit_factor']} | {selected['profit_factor']} |",
        f"| Gross profit factor | {b0['gross_profit_factor']} | {selected['gross_profit_factor']} |",
        f"| Net expectancy R | {b0['expectancy_r']} | {selected['expectancy_r']} |",
        f"| Gross expectancy R | {b0['gross_expectancy_r']} | {selected['gross_expectancy_r']} |",
        f"| P95 cost R | {b0['p95_cost_r']} | {selected['p95_cost_r']} |",
        f"| Win rate | {b0['win_rate_pct']}% | {selected['win_rate_pct']}% |",
        f"| Bad-signal loss share | {b0['bad_signal_loss_share_pct']}% | {selected['bad_signal_loss_share_pct']}% |",
        f"| Bad-signal improvement | {b0['bad_signal_loss_share_improvement_pct']}% | {selected['bad_signal_loss_share_improvement_pct']}% |",
        f"| Max consecutive losses | {b0['max_consecutive_losses']} | {selected['max_consecutive_losses']} |",
        f"| Max drawdown R | {b0['max_drawdown_r']} | {selected['max_drawdown_r']} |",
        "",
        "## Candidate Rule",
        "",
    ]
    for key, value in payload["candidate_rule"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This selects a V2 hypothesis candidate for a fresh validation window.",
            "- This is not promotion evidence and does not authorize A3 reactivation.",
            "- PF, expectancy, net R, drawdown, and eligibility are computed on net R after subtracting `cost_r`; if a source has zero/unavailable spread, that source is not cost-validating.",
            "- The June 2026 SQ-03 window remains too small for the 100-trade gate; its maximum one-position schedule is below 100.",
            "",
            "## Outputs",
            "",
        ]
    )
    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def empty_trade() -> VirtualTrade:
    return VirtualTrade("", "", "", "", "", 0.0, 0.0, 0.0, 0.0, "", 0.0, 0.0, 0.0, "", "", "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run offline historical A3 signal-quality V2 candidate discovery.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    payload = run_extended_discovery(args.root)
    print(f"A3 extended discovery: {payload['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
