from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_SHADOW_FILES_DIR = Path("C:/MT5PortableShadowFixObservers/MQL5/Files")
DEFAULT_ACTUAL_TRADES = Path("outputs") / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "OBSERVER_OUTCOME_RESOLUTION_REPORT.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "OBSERVER_OUTCOME_RESOLUTION_REPORT.md"
DEFAULT_OUTPUT_CSV = Path("outputs") / "reports" / "OBSERVER_OUTCOME_RESOLUTION_ROWS.csv"
DEFAULT_SCOREBOARD_JSON = Path("outputs") / "reports" / "OBSERVER_SHADOW_POLICY_SCOREBOARD.json"
DEFAULT_SCOREBOARD_MD = Path("outputs") / "reports" / "OBSERVER_SHADOW_POLICY_SCOREBOARD.md"
DEFAULT_SCOREBOARD_CSV = Path("outputs") / "reports" / "OBSERVER_SHADOW_POLICY_SCOREBOARD.csv"
DEFAULT_SIGNAL_GLOB = "shadow_fix_observer_signal_log_*.csv"
DEFAULT_COST_MODEL = Path("..") / "xauusd-phase0" / "outputs" / "reports" / "cost_model_measured.csv"

ROUND_RETEST_CLONE_CANDIDATES = {"symbol_normalized_round_retest_v0", "round_number_retest_v0"}
WEAKNESS_TIME_BLOCKS = {"Morning 06:00-11:59", "Afternoon 12:00-15:59"}


def generate_observer_outcome_resolution(
    phase1_root: Path,
    shadow_files_dir: Path = DEFAULT_SHADOW_FILES_DIR,
    actual_trades_csv: Path | None = None,
    bars_dir: Path | None = None,
    output_json: Path | None = None,
    signal_glob: str = DEFAULT_SIGNAL_GLOB,
    scoreboard_json: Path | None = None,
    cost_model_csv: Path | None = None,
    scoreboard_mode: str = "all_resolved",
) -> Path:
    phase1_root = phase1_root.resolve()
    shadow_files_dir = shadow_files_dir.resolve()
    actual_trades_csv = (actual_trades_csv or phase1_root / DEFAULT_ACTUAL_TRADES).resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_MD
    output_csv = output_json.with_suffix(".csv") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_CSV
    scoreboard_json = (scoreboard_json or phase1_root / DEFAULT_SCOREBOARD_JSON).resolve()
    cost_model_csv = (cost_model_csv or phase1_root / DEFAULT_COST_MODEL).resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)

    signals = [row for row in _read_shadow_rows(shadow_files_dir, signal_glob) if _truthy(row.get("would_signal"))]
    actual_rows = _read_csv(actual_trades_csv)
    actual_index = _actual_index(actual_rows)
    cost_model = _load_cost_model(cost_model_csv)
    bars_cache: dict[str, list[dict[str, str]]] = {}
    resolved_rows = [
        _resolve_signal(row, actual_index, bars_dir.resolve() if bars_dir else None, bars_cache, cost_model)
        for row in signals
    ]
    scoreboard_rows = _scoreboard_rows(resolved_rows, mode=scoreboard_mode)
    broker_fill_scoreboards = _dimension_scoreboards(
        [row for row in resolved_rows if row.get("evidence_tier") == "BROKER"]
    )
    replay_reference_scoreboards = _dimension_scoreboards(
        [row for row in resolved_rows if row.get("evidence_tier") == "REPLAY"]
    )
    bar_quality = _bar_quality_report(bars_dir.resolve(), signals) if bars_dir else []
    payload: dict[str, Any] = {
        "status": _status(resolved_rows, bool(bars_dir)),
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Read-only outcome resolution for observer signals. It joins to exported broker trades and optionally "
            "replays executor-faithful synthetic SL/TP against supplied M5 bars. It does not touch MT5 runtime, "
            "orders, positions, profiles, charts, or running EAs."
        ),
        "replay_model": "executor_v2",
        "scoreboard_mode": scoreboard_mode,
        "shadow_files_dir": str(shadow_files_dir),
        "signal_glob": signal_glob,
        "actual_trades_csv": str(actual_trades_csv),
        "bars_dir": str(bars_dir.resolve()) if bars_dir else "",
        "cost_model_csv": str(cost_model_csv),
        "signal_count": len(signals),
        "actual_trade_rows": len(actual_rows),
        "resolved_count": sum(1 for row in resolved_rows if row.get("evidence_tier") in {"BROKER", "REPLAY"}),
        "broker_join_resolved_count": sum(1 for row in resolved_rows if row.get("evidence_tier") == "BROKER"),
        "replay_resolved_count": sum(1 for row in resolved_rows if row.get("evidence_tier") == "REPLAY"),
        "unresolved_count": sum(1 for row in resolved_rows if row["resolution_status"].startswith("UNRESOLVED")),
        "by_evidence_tier": _counter(resolved_rows, "evidence_tier", "resolution_status"),
        "by_resolution_status": _counter(resolved_rows, "resolution_status"),
        "by_resolution_source": _counter(resolved_rows, "resolution_source", "resolution_status"),
        "broker_fill_scoreboards": broker_fill_scoreboards,
        "replay_reference_scoreboards": replay_reference_scoreboards,
        "by_candidate": _counter(resolved_rows, "candidate"),
        "by_candidate_status": _counter(resolved_rows, "candidate", "resolution_status"),
        "by_proposed_v2_action": _counter(resolved_rows, "proposed_v2_shadow_action", "resolution_status"),
        "by_time_bucket": _counter(resolved_rows, "time_bucket", "resolution_status"),
        "bar_quality": bar_quality,
        "scoreboard_rows": scoreboard_rows,
        "scoreboard_json": str(scoreboard_json),
        "scoreboard_md": str(scoreboard_json.with_suffix(".md")),
        "scoreboard_csv": str(scoreboard_json.with_suffix(".csv")),
        "notes": [
            "Broker-trade join is the preferred proof when the demo EA actually took the same signal.",
            "Rows with evidence_tier=BROKER use actual broker state, profit, and exit data as the authoritative outcome.",
            "Rows with evidence_tier=REPLAY are secondary reference evidence only; broker-tier scoreboards should be used for current decisions.",
            "M5 replay is only used when a bars_dir is provided and matching June 2026 bars exist.",
            "Replay model executor_v2 simulates Phase2ExperimentalDemoExecutor.SendDemoMarketOrder: next-M5-open entry, measured spread adjustment, stop floor, synthetic SL/TP, and adverse-first same-bar exits.",
            "Replay uses adverse-first same-bar ordering, so if SL and TP are both touched in the same M5 bar the row is scored as SL.",
            "Rows without broker match or bars are left unresolved; no outcome is guessed.",
            "Observer LONG/SHORT directions are normalized to broker BUY/SELL only for matching and replay; the original direction is preserved.",
            "Replay rows include gross R, estimated cost R, and net R. v1 plan-replay columns are retained only for calibration diffing.",
            "Portfolio-level totals must use the family rollup because clone EAs can emit duplicate same-family signals.",
            "Proposed v2 shadow policy blocks the round-retest clone family: symbol_normalized_round_retest_v0 and round_number_retest_v0.",
        ],
    }
    _write_csv(output_csv, resolved_rows, _resolved_fields())
    _write_scoreboard(scoreboard_json, scoreboard_rows, payload)
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return output_json


def _read_shadow_rows(files_dir: Path, signal_glob: str = DEFAULT_SIGNAL_GLOB) -> list[dict[str, str]]:
    if not files_dir.exists():
        return []
    rows: list[dict[str, str]] = []
    for path in sorted(files_dir.glob(signal_glob)):
        for row in _read_csv(path):
            row["_source_file"] = path.name
            rows.append(row)
    return rows


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def _actual_index(rows: list[dict[str, str]]) -> dict[tuple[str, str, str, str], list[dict[str, str]]]:
    index: dict[tuple[str, str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        minute = _minute_key(row.get("entry_time", ""))
        if not minute:
            continue
        key = (
            row.get("candidate", ""),
            row.get("symbol", "").upper(),
            _normalise_trade_direction(row.get("direction", "")),
            minute,
        )
        if not key[2]:
            continue
        index.setdefault(key, []).append(row)
    return index


def _resolve_signal(
    row: dict[str, str],
    actual_index: dict[tuple[str, str, str, str], list[dict[str, str]]],
    bars_dir: Path | None,
    bars_cache: dict[str, list[dict[str, str]]],
    cost_model: dict[tuple[str, str], dict[str, str]],
) -> dict[str, str]:
    resolved = _base_resolved_row(row)
    if not resolved["normalized_direction"]:
        resolved["resolution_status"] = "UNRESOLVED_UNKNOWN_DIRECTION"
        return resolved
    broker_match = _find_broker_match(row, actual_index)
    if broker_match:
        resolved.update(_broker_resolution(broker_match))
        return resolved
    replay = _replay_resolution(row, bars_dir, bars_cache, cost_model) if bars_dir else None
    if replay:
        resolved.update(replay)
        return resolved
    resolved["resolution_status"] = "UNRESOLVED_NO_BROKER_MATCH_NO_REPLAY_BARS"
    return resolved


def _base_resolved_row(row: dict[str, str]) -> dict[str, str]:
    proposed_action, proposed_reason = _proposed_v2_action(row)
    fixed_action = row.get("fixed_shadow_action") or proposed_action
    fixed_reason = row.get("fixed_shadow_reason") or proposed_reason
    spread_points = row.get("spread_points", "")
    candidate = row.get("candidate", "")
    return {
        "timestamp_broker": row.get("timestamp_broker", ""),
        "m5_bar_time": row.get("m5_bar_time", ""),
        "time_bucket": row.get("time_bucket", ""),
        "candidate": candidate,
        "family": _family_for_candidate(candidate),
        "lane": _lane_for_candidate(candidate),
        "regime": row.get("regime", "") or row.get("dirstate_regime", "") or row.get("stage", "") or "UNKNOWN",
        "symbol": row.get("symbol", ""),
        "direction": row.get("direction", ""),
        "normalized_direction": _normalise_trade_direction(row.get("direction", "")),
        "legacy_shadow_action": row.get("shadow_action", ""),
        "legacy_shadow_reason": row.get("shadow_reason", ""),
        "proposed_v2_shadow_action": proposed_action,
        "proposed_v2_shadow_reason": proposed_reason,
        "trend_veto_action": row.get("trend_veto_action", ""),
        "trend_veto_reason": row.get("trend_veto_reason", ""),
        "fixed_shadow_action": fixed_action,
        "fixed_shadow_reason": fixed_reason,
        "entry_price": row.get("entry_price", ""),
        "stop_loss": row.get("stop_loss", ""),
        "take_profit": row.get("take_profit", ""),
        "stop_distance_points": row.get("stop_distance_points", ""),
        "spread_points": spread_points,
        "cost_bucket": _cost_bucket(spread_points),
        "evidence_tier": "",
        "resolution_status": "UNRESOLVED",
        "resolution_source": "",
        "matched_position_ticket": "",
        "actual_state": "",
        "actual_profit_aed": "",
        "actual_exit_time": "",
        "actual_exit_price": "",
        "replay_model": "",
        "replay_entry_time": "",
        "replay_entry_price": "",
        "replay_synthetic_stop_loss": "",
        "replay_synthetic_take_profit": "",
        "replay_signal_risk_points": "",
        "replay_spread_points": "",
        "replay_bars_scanned": "",
        "replay_exit_time": "",
        "replay_exit_price": "",
        "gross_outcome_r": "",
        "estimated_cost_r": "",
        "cost_source": "",
        "net_outcome_r": "",
        "v1_resolution_status": "",
        "v1_resolution_source": "",
        "v1_replay_bars_scanned": "",
        "v1_replay_exit_time": "",
        "v1_replay_exit_price": "",
        "v1_gross_outcome_r": "",
        "v1_estimated_cost_r": "",
        "v1_cost_source": "",
        "v1_net_outcome_r": "",
        "_source_file": row.get("_source_file", ""),
    }


def _proposed_v2_action(row: dict[str, str]) -> tuple[str, str]:
    candidate = row.get("candidate", "")
    symbol = row.get("symbol", "").upper()
    time_bucket = row.get("time_bucket", "")
    if candidate in ROUND_RETEST_CLONE_CANDIDATES:
        return "BLOCK", "BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY"
    if candidate == "session_extreme_retest_v0":
        return "BLOCK", "BLOCK_WEAK_EA_SESSION_EXTREME_RETEST"
    if symbol == "XAUUSD" and time_bucket in WEAKNESS_TIME_BLOCKS:
        return "BLOCK", "BLOCK_XAUUSD_MORNING_AFTERNOON"
    return "KEEP", "KEEP"


def _family_for_candidate(candidate: str) -> str:
    value = str(candidate or "").strip()
    if value in {"breakout_retest", "swing_breakout_retest_v0", "p2weakness_br_v1"}:
        return "breakout"
    if value in ROUND_RETEST_CLONE_CANDIDATES:
        return "round"
    if value.startswith("session_extreme_retest_v0"):
        return "session"
    if value.startswith("WR50_"):
        return "wr50"
    if "repair_v1" in value:
        return "repair"
    return "other"


def _lane_for_candidate(candidate: str) -> str:
    value = str(candidate or "").strip()
    if value in {"breakout_retest", "swing_breakout_retest_v0"}:
        return "accepted_same_family"
    if value in ROUND_RETEST_CLONE_CANDIDATES:
        return "accepted_round_family"
    if value.startswith("session_extreme_retest_v0"):
        return "provisional_session_family"
    if "repair_v1" in value:
        return "repair_experiment"
    if value.startswith("WR50_"):
        return "wr50_experiment"
    if value == "p2weakness_br_v1":
        return "phase2x_experiment"
    return "other"


def _cost_bucket(spread_points: str | None) -> str:
    spread = _float(spread_points)
    if spread is None:
        return "UNKNOWN"
    if spread <= 30.0:
        return "LOW_<=30pt"
    if spread <= 50.0:
        return "MEDIUM_31_50pt"
    if spread <= 75.0:
        return "HIGH_51_75pt"
    return "EXTREME_>75pt"


def _find_broker_match(
    row: dict[str, str],
    actual_index: dict[tuple[str, str, str, str], list[dict[str, str]]],
) -> dict[str, str] | None:
    minute = _minute_key(row.get("m5_bar_time", ""))
    if not minute:
        return None
    candidate = row.get("candidate", "")
    symbol = row.get("symbol", "").upper()
    direction = _normalise_trade_direction(row.get("direction", ""))
    if not direction:
        return None
    candidates: list[dict[str, str]] = []
    for offset in (-1, 0, 1):
        nearby = _offset_minute(minute, offset)
        candidates.extend(actual_index.get((candidate, symbol, direction, nearby), []))
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item.get("entry_time", ""))[0]


def _broker_resolution(row: dict[str, str]) -> dict[str, str]:
    state = row.get("state", "")
    profit = _float(row.get("profit_aed"))
    if state == "OPEN":
        status = "BROKER_MATCH_OPEN"
    elif profit is not None and profit > 0:
        status = "BROKER_CLOSED_WIN"
    elif profit is not None and profit < 0:
        status = "BROKER_CLOSED_LOSS"
    else:
        status = "BROKER_CLOSED_FLAT_OR_UNKNOWN"
    return {
        "resolution_status": status,
        "resolution_source": "broker_trade_join",
        "evidence_tier": "BROKER",
        "matched_position_ticket": row.get("position_ticket", ""),
        "actual_state": state,
        "actual_profit_aed": row.get("profit_aed", ""),
        "actual_exit_time": row.get("exit_time", ""),
        "actual_exit_price": row.get("exit_price", ""),
    }


def _replay_resolution(
    row: dict[str, str],
    bars_dir: Path | None,
    bars_cache: dict[str, list[dict[str, str]]],
    cost_model: dict[tuple[str, str], dict[str, str]],
) -> dict[str, str] | None:
    v1 = _replay_resolution_plan_v1(row, bars_dir, bars_cache, cost_model)
    v2 = _replay_resolution_executor_v2(row, bars_dir, bars_cache, cost_model)
    if v2 is None:
        return None
    v2.update(_v1_diff_fields(v1))
    return v2


def _v1_diff_fields(v1: dict[str, str] | None) -> dict[str, str]:
    if not v1:
        return {
            "v1_resolution_status": "UNRESOLVED_REPLAY_MISSING",
            "v1_resolution_source": "",
            "v1_replay_bars_scanned": "",
            "v1_replay_exit_time": "",
            "v1_replay_exit_price": "",
            "v1_gross_outcome_r": "",
            "v1_estimated_cost_r": "",
            "v1_cost_source": "",
            "v1_net_outcome_r": "",
        }
    return {
        "v1_resolution_status": v1.get("resolution_status", ""),
        "v1_resolution_source": v1.get("resolution_source", ""),
        "v1_replay_bars_scanned": v1.get("replay_bars_scanned", ""),
        "v1_replay_exit_time": v1.get("replay_exit_time", ""),
        "v1_replay_exit_price": v1.get("replay_exit_price", ""),
        "v1_gross_outcome_r": v1.get("gross_outcome_r", ""),
        "v1_estimated_cost_r": v1.get("estimated_cost_r", ""),
        "v1_cost_source": v1.get("cost_source", ""),
        "v1_net_outcome_r": v1.get("net_outcome_r", ""),
    }


def _replay_resolution_plan_v1(
    row: dict[str, str],
    bars_dir: Path | None,
    bars_cache: dict[str, list[dict[str, str]]],
    cost_model: dict[tuple[str, str], dict[str, str]],
) -> dict[str, str] | None:
    if bars_dir is None:
        return None
    symbol = row.get("symbol", "").upper()
    direction = _normalise_trade_direction(row.get("direction", ""))
    entry = _float(row.get("entry_price"))
    stop = _float(row.get("stop_loss"))
    target = _float(row.get("take_profit"))
    start = _parse_time(row.get("m5_bar_time", ""))
    if not symbol or direction not in {"BUY", "SELL"} or entry is None or stop is None or target is None or start is None:
        return None
    if entry <= 0.0 or stop <= 0.0 or target <= 0.0:
        return None

    bars = bars_cache.setdefault(symbol, _load_m5_bars(bars_dir, symbol))
    if not bars:
        return None
    scanned = 0
    for bar in bars:
        bar_time = _parse_time(bar.get("bar_start_utc") or bar.get("timestamp_utc") or bar.get("time") or "")
        if bar_time is None or bar_time < start:
            continue
        high = _float(bar.get("high") or bar.get("mid_high") or bar.get("ask_high") or bar.get("bid_high"))
        low = _float(bar.get("low") or bar.get("mid_low") or bar.get("ask_low") or bar.get("bid_low"))
        if high is None or low is None:
            continue
        scanned += 1
        if direction == "BUY":
            hit_stop = low <= stop
            hit_target = high >= target
        else:
            hit_stop = high >= stop
            hit_target = low <= target
        if hit_stop or hit_target:
            adverse_first_status = "REPLAY_SL" if hit_stop else "REPLAY_TP"
            gross_r = _gross_replay_r(adverse_first_status, entry, stop, target)
            cost = _estimated_cost_r(row, cost_model)
            net_r = gross_r - cost["cost_r"] if gross_r is not None and cost["cost_r"] is not None else None
            return {
                "resolution_status": adverse_first_status,
                "resolution_source": "m5_bar_replay_plan_v1_adverse_first",
                "evidence_tier": "REPLAY",
                "replay_bars_scanned": str(scanned),
                "replay_exit_time": bar.get("bar_end_utc") or bar.get("timestamp_utc") or "",
                "replay_exit_price": str(stop if adverse_first_status == "REPLAY_SL" else target),
                "gross_outcome_r": _fmt_float(gross_r),
                "estimated_cost_r": _fmt_float(cost["cost_r"]),
                "cost_source": cost["source"],
                "net_outcome_r": _fmt_float(net_r),
            }
    return {
        "resolution_status": "UNRESOLVED_REPLAY_NO_SL_TP_HIT",
        "resolution_source": "m5_bar_replay_plan_v1_adverse_first",
        "evidence_tier": "",
        "replay_bars_scanned": str(scanned),
    }


def _replay_resolution_executor_v2(
    row: dict[str, str],
    bars_dir: Path | None,
    bars_cache: dict[str, list[dict[str, str]]],
    cost_model: dict[tuple[str, str], dict[str, str]],
) -> dict[str, str] | None:
    if bars_dir is None:
        return None
    symbol = row.get("symbol", "").upper()
    direction = _normalise_trade_direction(row.get("direction", ""))
    plan_stop = _float(row.get("stop_loss"))
    start = _parse_time(row.get("m5_bar_time", ""))
    if not symbol or direction not in {"BUY", "SELL"} or plan_stop is None or start is None:
        return None
    if plan_stop <= 0.0:
        return None

    bars = bars_cache.setdefault(symbol, _load_m5_bars(bars_dir, symbol))
    if not bars:
        return None

    entry_bar = _next_m5_bar_after(bars, start)
    if entry_bar is None:
        return _executor_unresolved("UNRESOLVED_REPLAY_NO_EXECUTOR_ENTRY_BAR", 0)

    entry_time = _bar_start(entry_bar)
    open_price = _bar_open(entry_bar)
    if entry_time is None or open_price is None:
        return _executor_unresolved("UNRESOLVED_REPLAY_MISSING_EXECUTOR_ENTRY_OPEN", 0)

    spread = _spread_points_for(symbol, entry_time, row, cost_model)
    spread_points = spread["spread_points"]
    if spread_points is None:
        return _executor_unresolved("UNRESOLVED_REPLAY_MISSING_EXECUTOR_SPREAD", 0)

    point = _point_size(symbol)
    spread_price = spread_points * point
    half_spread = spread_price / 2.0
    synthetic_entry = open_price + half_spread if direction == "BUY" else open_price - half_spread
    stop_floor = _stop_floor_price(symbol, spread_price)
    signal_risk = max(abs(synthetic_entry - plan_stop), stop_floor)
    if signal_risk <= 0.0:
        return _executor_unresolved("UNRESOLVED_REPLAY_ZERO_EXECUTOR_RISK", 0)

    if direction == "BUY":
        stop = synthetic_entry - signal_risk
        target = synthetic_entry + 1.5 * signal_risk
    else:
        stop = synthetic_entry + signal_risk
        target = synthetic_entry - 1.5 * signal_risk

    scanned = 0
    for bar in bars:
        bar_time = _bar_start(bar)
        if bar_time is None or bar_time < entry_time:
            continue
        high = _bar_high(bar)
        low = _bar_low(bar)
        if high is None or low is None:
            continue
        scanned += 1
        exit_spread = _spread_points_for(symbol, bar_time, row, cost_model)
        exit_spread_points = exit_spread["spread_points"] if exit_spread["spread_points"] is not None else spread_points
        exit_half_spread = exit_spread_points * point / 2.0
        if direction == "BUY":
            bid_high = high - exit_half_spread
            bid_low = low - exit_half_spread
            hit_stop = bid_low <= stop
            hit_target = bid_high >= target
        else:
            ask_high = high + exit_half_spread
            ask_low = low + exit_half_spread
            hit_stop = ask_high >= stop
            hit_target = ask_low <= target
        if hit_stop or hit_target:
            adverse_first_status = "REPLAY_SL" if hit_stop else "REPLAY_TP"
            gross_r = _gross_replay_r(adverse_first_status, synthetic_entry, stop, target)
            cost_r = spread_points / (signal_risk / point)
            net_r = gross_r - cost_r if gross_r is not None else None
            return {
                "resolution_status": adverse_first_status,
                "resolution_source": "m5_bar_replay_executor_v2_adverse_first",
                "evidence_tier": "REPLAY",
                "replay_model": "executor_v2",
                "replay_entry_time": _format_time(entry_time),
                "replay_entry_price": _fmt_float(synthetic_entry),
                "replay_synthetic_stop_loss": _fmt_float(stop),
                "replay_synthetic_take_profit": _fmt_float(target),
                "replay_signal_risk_points": _fmt_float(signal_risk / point),
                "replay_spread_points": _fmt_float(spread_points),
                "replay_bars_scanned": str(scanned),
                "replay_exit_time": _bar_end_or_start(bar),
                "replay_exit_price": _fmt_float(stop if adverse_first_status == "REPLAY_SL" else target),
                "gross_outcome_r": _fmt_float(gross_r),
                "estimated_cost_r": _fmt_float(cost_r),
                "cost_source": spread["source"],
                "net_outcome_r": _fmt_float(net_r),
            }
    unresolved = _executor_unresolved("UNRESOLVED_REPLAY_NO_SL_TP_HIT", scanned)
    unresolved.update(
        {
            "replay_entry_time": _format_time(entry_time),
            "replay_entry_price": _fmt_float(synthetic_entry),
            "replay_synthetic_stop_loss": _fmt_float(stop),
            "replay_synthetic_take_profit": _fmt_float(target),
            "replay_signal_risk_points": _fmt_float(signal_risk / point),
            "replay_spread_points": _fmt_float(spread_points),
            "cost_source": spread["source"],
        }
    )
    return unresolved


def _executor_unresolved(status: str, scanned: int) -> dict[str, str]:
    return {
        "resolution_status": status,
        "resolution_source": "m5_bar_replay_executor_v2_adverse_first",
        "replay_model": "executor_v2",
        "replay_bars_scanned": str(scanned),
    }


def _next_m5_bar_after(bars: list[dict[str, str]], start: datetime) -> dict[str, str] | None:
    for bar in bars:
        bar_time = _bar_start(bar)
        if bar_time is not None and bar_time > start:
            return bar
    return None


def _load_m5_bars(bars_dir: Path, symbol: str) -> list[dict[str, str]]:
    if not bars_dir.exists():
        return []
    candidates = sorted(bars_dir.rglob(f"{symbol}*M5*.csv"))
    if not candidates:
        return []
    rows: list[dict[str, str]] = []
    for path in candidates:
        rows.extend(_read_csv(path))
    return sorted(rows, key=lambda row: _bar_start(row) or datetime.max)


def _bar_start(bar: dict[str, str]) -> datetime | None:
    return _parse_time(bar.get("bar_start_utc") or bar.get("timestamp_utc") or bar.get("time") or "")


def _bar_end_or_start(bar: dict[str, str]) -> str:
    end = _parse_time(bar.get("bar_end_utc") or "")
    if end is not None:
        return _format_time(end)
    start = _bar_start(bar)
    return _format_time(start) if start is not None else ""


def _bar_open(bar: dict[str, str]) -> float | None:
    return _float(
        bar.get("open")
        or bar.get("mid_open")
        or bar.get("ask_open")
        or bar.get("bid_open")
        or bar.get("close")
        or bar.get("mid_close")
    )


def _bar_high(bar: dict[str, str]) -> float | None:
    return _float(bar.get("high") or bar.get("mid_high") or bar.get("ask_high") or bar.get("bid_high"))


def _bar_low(bar: dict[str, str]) -> float | None:
    return _float(bar.get("low") or bar.get("mid_low") or bar.get("ask_low") or bar.get("bid_low"))


def _normalise_trade_direction(value: str | None) -> str:
    text = str(value or "").strip().upper()
    if text in {"BUY", "LONG"}:
        return "BUY"
    if text in {"SELL", "SHORT"}:
        return "SELL"
    return ""


def _load_cost_model(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    rows = _read_csv(path)
    model: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        symbol = row.get("symbol", "").upper()
        scope = row.get("scope", "")
        bucket = row.get("bucket", "")
        if not symbol:
            continue
        if scope == "hour_utc":
            model[(symbol, f"hour_utc:{bucket}")] = row
        elif scope == "global":
            model[(symbol, "global")] = row
    return model


def _spread_points_for(
    symbol: str,
    timestamp: datetime | None,
    row: dict[str, str],
    cost_model: dict[tuple[str, str], dict[str, str]],
) -> dict[str, Any]:
    hour_key = f"hour_utc:{timestamp.hour}" if timestamp else ""
    model_row = cost_model.get((symbol, hour_key)) if hour_key else None
    if model_row is None:
        model_row = cost_model.get((symbol, "global"))
    if model_row is not None:
        spread_points = _float(model_row.get("p95_spread_points"))
        if spread_points is not None:
            return {"spread_points": spread_points, "source": "measured_p95_spread_table"}
    spread_points = _float(row.get("spread_points"))
    if spread_points is not None:
        return {"spread_points": spread_points, "source": "signal_spread_fallback"}
    return {"spread_points": None, "source": "missing_spread"}


def _stop_floor_price(symbol: str, spread_price: float) -> float:
    point = _point_size(symbol)
    base_floor = 300.0 * point if symbol == "XAUUSD" else 100.0 * point
    return max(base_floor, 3.0 * spread_price)


def _estimated_cost_r(row: dict[str, str], cost_model: dict[tuple[str, str], dict[str, str]]) -> dict[str, Any]:
    symbol = row.get("symbol", "").upper()
    stop_points = _float(row.get("stop_distance_points"))
    if stop_points is None or stop_points <= 0.0:
        entry = _float(row.get("entry_price"))
        stop = _float(row.get("stop_loss"))
        if entry is not None and stop is not None:
            stop_points = abs(entry - stop) / _point_size(symbol)
    if stop_points is None or stop_points <= 0.0:
        return {"cost_r": None, "source": "missing_stop_distance"}

    timestamp = _parse_time(row.get("timestamp_utc", "") or row.get("m5_bar_time", ""))
    spread = _spread_points_for(symbol, timestamp, row, cost_model)
    spread_points = spread["spread_points"]
    if spread_points is not None:
        return {
            "cost_r": spread_points / stop_points,
            "source": spread["source"],
        }
    return {"cost_r": None, "source": "missing_spread"}


def _gross_replay_r(status: str, entry: float, stop: float, target: float) -> float | None:
    risk = abs(entry - stop)
    if risk <= 0.0:
        return None
    if status == "REPLAY_SL":
        return -1.0
    if status == "REPLAY_TP":
        return abs(target - entry) / risk
    return None


def _point_size(symbol: str) -> float:
    if symbol.endswith("JPY"):
        return 0.001
    if symbol in {"EURUSD", "GBPUSD"}:
        return 0.00001
    return 0.01


def _fmt_float(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"


def _bar_quality_report(bars_dir: Path, signals: list[dict[str, str]]) -> list[dict[str, Any]]:
    symbols = sorted({str(row.get("symbol", "")).upper() for row in signals if row.get("symbol")})
    rows: list[dict[str, Any]] = []
    for symbol in symbols:
        bars = _load_m5_bars(bars_dir, symbol)
        parsed_times = sorted(
            time
            for time in (
                _parse_time(bar.get("bar_start_utc") or bar.get("timestamp_utc") or bar.get("time") or "")
                for bar in bars
            )
            if time is not None
        )
        duplicate_times = len(parsed_times) - len(set(parsed_times))
        gap_count = 0
        max_gap_minutes = 0.0
        expected_rows = 0
        continuity_pct = 0.0
        if parsed_times:
            unique_times = sorted(set(parsed_times))
            for left, right in zip(unique_times, unique_times[1:]):
                gap_minutes = (right - left).total_seconds() / 60.0
                if gap_minutes > 5.0:
                    gap_count += 1
                    max_gap_minutes = max(max_gap_minutes, gap_minutes)
            span_minutes = (unique_times[-1] - unique_times[0]).total_seconds() / 60.0
            expected_rows = int(span_minutes / 5.0) + 1 if span_minutes >= 0 else 0
            continuity_pct = (len(unique_times) / expected_rows * 100.0) if expected_rows else 0.0
        status = "MISSING"
        if parsed_times:
            status = "PASS" if gap_count == 0 and duplicate_times == 0 else "WARN_GAPS_OR_DUPLICATES"
        rows.append(
            {
                "symbol": symbol,
                "status": status,
                "rows": len(bars),
                "unique_bar_times": len(set(parsed_times)),
                "first_bar": parsed_times[0].strftime("%Y-%m-%d %H:%M:%S") if parsed_times else "",
                "last_bar": parsed_times[-1].strftime("%Y-%m-%d %H:%M:%S") if parsed_times else "",
                "expected_rows_from_first_to_last": expected_rows,
                "continuity_pct": f"{continuity_pct:.2f}",
                "gap_count_gt_5m": gap_count,
                "max_gap_minutes": f"{max_gap_minutes:.1f}",
                "duplicate_bar_times": duplicate_times,
            }
        )
    return rows


def _scoreboard_rows(rows: list[dict[str, str]], *, mode: str = "all_resolved") -> list[dict[str, str]]:
    if mode == "broker_joined_only":
        rows = [row for row in rows if row.get("evidence_tier") == "BROKER"]
    return _group_scoreboard_rows(rows, level="candidate") + _group_scoreboard_rows(
        _dedupe_family_rows(rows), level="family"
    )


def _dimension_scoreboards(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    dimensions = {
        "session": ("time_bucket",),
        "cost": ("cost_bucket",),
        "direction": ("normalized_direction",),
        "regime": ("regime",),
        "family": ("family",),
        "lane": ("lane",),
        "ea_symbol_session": ("candidate", "symbol", "time_bucket"),
    }
    return {name: _dimension_rows(rows, keys) for name, keys in dimensions.items()}


def _dimension_rows(rows: list[dict[str, str]], keys: tuple[str, ...]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(tuple(row.get(key, "") or "UNKNOWN" for key in keys), []).append(row)
    output: list[dict[str, str]] = []
    for key, items in sorted(grouped.items()):
        wins = sum(1 for item in items if _outcome_class(item) == "WIN")
        losses = sum(1 for item in items if _outcome_class(item) == "LOSS")
        open_rows = sum(1 for item in items if _outcome_class(item) == "OPEN")
        flat = sum(1 for item in items if _outcome_class(item) == "FLAT")
        closed = wins + losses + flat
        pnl = sum(_float(item.get("actual_profit_aed")) or 0.0 for item in items)
        replay_net = sum(_float(item.get("net_outcome_r")) or 0.0 for item in items)
        output.append(
            {
                "group": " | ".join(key),
                "rows": str(len(items)),
                "closed": str(closed),
                "wins": str(wins),
                "losses": str(losses),
                "open": str(open_rows),
                "flat": str(flat),
                "win_rate_pct": f"{(wins / (wins + losses) * 100.0):.2f}" if wins + losses else "n/a",
                "broker_profit_aed": f"{pnl:.2f}",
                "replay_net_r_sum": f"{replay_net:.4f}" if any(item.get("net_outcome_r") for item in items) else "",
            }
        )
    return output


def _group_scoreboard_rows(rows: list[dict[str, str]], *, level: str) -> list[dict[str, str]]:
    groups: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in rows:
        primary = row.get("candidate", "") if level == "candidate" else row.get("family", "")
        key = (
            primary,
            row.get("family", ""),
            row.get("symbol", ""),
            row.get("time_bucket", ""),
            row.get("direction", ""),
            row.get("normalized_direction", ""),
            row.get("legacy_shadow_action", ""),
            row.get("proposed_v2_shadow_action", ""),
            row.get("proposed_v2_shadow_reason", ""),
            row.get("trend_veto_action", ""),
            row.get("fixed_shadow_action", ""),
        )
        groups.setdefault(key, []).append(row)

    scoreboard: list[dict[str, str]] = []
    for key, items in sorted(groups.items()):
        wins = sum(1 for item in items if _outcome_class(item) == "WIN")
        losses = sum(1 for item in items if _outcome_class(item) == "LOSS")
        open_rows = sum(1 for item in items if _outcome_class(item) == "OPEN")
        flat = sum(1 for item in items if _outcome_class(item) == "FLAT")
        unresolved = sum(1 for item in items if _outcome_class(item) == "UNRESOLVED")
        broker = sum(1 for item in items if item.get("resolution_status", "").startswith("BROKER_"))
        replay = sum(1 for item in items if item.get("resolution_status", "").startswith("REPLAY_"))
        closed = wins + losses
        win_rate = (wins / closed * 100.0) if closed else 0.0
        pnl = sum(_float(item.get("actual_profit_aed")) or 0.0 for item in items)
        replay_net_values = [
            value
            for value in (_float(item.get("net_outcome_r")) for item in items if item.get("resolution_status", "").startswith("REPLAY_"))
            if value is not None
        ]
        replay_gross_wins = sum(1 for item in items if item.get("resolution_status") == "REPLAY_TP")
        replay_gross_losses = sum(1 for item in items if item.get("resolution_status") == "REPLAY_SL")
        replay_closed = replay_gross_wins + replay_gross_losses
        replay_net_wins = sum(1 for value in replay_net_values if value > 0.0)
        replay_net_losses = sum(1 for value in replay_net_values if value < 0.0)
        replay_gross_wr = (replay_gross_wins / replay_closed * 100.0) if replay_closed else 0.0
        replay_net_wr = (
            replay_net_wins / (replay_net_wins + replay_net_losses) * 100.0
            if replay_net_wins + replay_net_losses
            else 0.0
        )
        avg_cost = _average([_float(item.get("estimated_cost_r")) for item in items])
        avg_rr = _average(
            [
                abs((_float(item.get("take_profit")) or 0.0) - (_float(item.get("entry_price")) or 0.0))
                / abs((_float(item.get("entry_price")) or 0.0) - (_float(item.get("stop_loss")) or 0.0))
                for item in items
                if _float(item.get("entry_price")) is not None
                and _float(item.get("stop_loss")) is not None
                and _float(item.get("take_profit")) is not None
                and abs((_float(item.get("entry_price")) or 0.0) - (_float(item.get("stop_loss")) or 0.0)) > 0.0
            ]
        )
        net_breakeven_wr = ((1.0 + avg_cost) / (1.0 + avg_rr) * 100.0) if avg_cost is not None and avg_rr else None
        scoreboard.append(
            {
                "aggregation_level": level,
                "group": key[0],
                "family": key[1],
                "symbol": key[2],
                "time_bucket": key[3],
                "direction": key[4],
                "normalized_direction": key[5],
                "legacy_shadow_action": key[6],
                "proposed_v2_shadow_action": key[7],
                "proposed_v2_shadow_reason": key[8],
                "trend_veto_action": key[9],
                "fixed_shadow_action": key[10],
                "signals": str(len(items)),
                "broker_join": str(broker),
                "replay": str(replay),
                "unresolved": str(unresolved),
                "wins": str(wins),
                "losses": str(losses),
                "open": str(open_rows),
                "flat": str(flat),
                "closed_win_rate_pct": f"{win_rate:.2f}",
                "broker_profit_aed": f"{pnl:.2f}",
                "replay_gross_win_rate_pct": f"{replay_gross_wr:.2f}",
                "replay_net_win_rate_pct": f"{replay_net_wr:.2f}",
                "replay_net_r_sum": f"{sum(replay_net_values):.4f}" if replay_net_values else "",
                "avg_cost_r": f"{avg_cost:.4f}" if avg_cost is not None else "",
                "avg_rr": f"{avg_rr:.4f}" if avg_rr is not None else "",
                "net_breakeven_wr_pct": f"{net_breakeven_wr:.2f}" if net_breakeven_wr is not None else "",
            }
        )
    return scoreboard


def _dedupe_family_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    priority = {
        "breakout_retest": 10,
        "swing_breakout_retest_v0": 20,
        "symbol_normalized_round_retest_v0": 30,
        "round_number_retest_v0": 40,
        "session_extreme_retest_v0": 50,
    }
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (
            row.get("family", ""),
            row.get("symbol", ""),
            row.get("m5_bar_time", ""),
            row.get("normalized_direction", ""),
            row.get("time_bucket", ""),
        )
        grouped.setdefault(key, []).append(row)
    deduped: list[dict[str, str]] = []
    for items in grouped.values():
        deduped.append(sorted(items, key=lambda item: priority.get(item.get("candidate", ""), 999))[0])
    return deduped


def _average(values: list[float | None]) -> float | None:
    filtered = [value for value in values if value is not None]
    if not filtered:
        return None
    return sum(filtered) / len(filtered)


def _outcome_class(row: dict[str, str]) -> str:
    status = row.get("resolution_status", "")
    if status in {"BROKER_CLOSED_WIN", "REPLAY_TP"}:
        return "WIN"
    if status in {"BROKER_CLOSED_LOSS", "REPLAY_SL"}:
        return "LOSS"
    if status == "BROKER_MATCH_OPEN":
        return "OPEN"
    if status == "BROKER_CLOSED_FLAT_OR_UNKNOWN":
        return "FLAT"
    return "UNRESOLVED"


def _scoreboard_fields() -> list[str]:
    return [
        "aggregation_level",
        "group",
        "family",
        "symbol",
        "time_bucket",
        "direction",
        "normalized_direction",
        "legacy_shadow_action",
        "proposed_v2_shadow_action",
        "proposed_v2_shadow_reason",
        "trend_veto_action",
        "fixed_shadow_action",
        "signals",
        "broker_join",
        "replay",
        "unresolved",
        "wins",
        "losses",
        "open",
        "flat",
        "closed_win_rate_pct",
        "broker_profit_aed",
        "replay_gross_win_rate_pct",
        "replay_net_win_rate_pct",
        "replay_net_r_sum",
        "avg_cost_r",
        "avg_rr",
        "net_breakeven_wr_pct",
    ]


def _dimension_fields() -> list[str]:
    return [
        "group",
        "rows",
        "closed",
        "wins",
        "losses",
        "open",
        "flat",
        "win_rate_pct",
        "broker_profit_aed",
        "replay_net_r_sum",
    ]


def _write_scoreboard(json_path: Path, rows: list[dict[str, str]], payload: dict[str, Any]) -> None:
    md_path = json_path.with_suffix(".md")
    csv_path = json_path.with_suffix(".csv")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(
            {
                "status": payload["status"],
                "created_at_utc": payload["created_at_utc"],
                "authority": "Analysis-only observer outcome scoreboard. No MT5 runtime, chart, order, or EA setting changes.",
                "scoreboard_mode": payload.get("scoreboard_mode", "all_resolved"),
                "replay_model": payload.get("replay_model", "executor_v2"),
                "broker_join_resolved_count": payload["broker_join_resolved_count"],
                "replay_resolved_count": payload["replay_resolved_count"],
                "unresolved_count": payload["unresolved_count"],
                "rows": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_csv(csv_path, rows, _scoreboard_fields())
    md_path.write_text(_render_scoreboard_markdown(payload, rows), encoding="utf-8")


def _render_scoreboard_markdown(payload: dict[str, Any], rows: list[dict[str, str]]) -> str:
    title = "Trend-Veto Lane Scoreboard" if "TREND_VETO" in str(payload.get("scoreboard_json", "")) else "Observer Shadow-Policy Scoreboard"
    top_rows = sorted(
        rows,
        key=lambda item: (
            -int(item.get("broker_join", "0")),
            -int(item.get("replay", "0")),
            item.get("aggregation_level", ""),
            item.get("group", ""),
            item.get("symbol", ""),
        ),
    )[:40]
    return "\n".join(
        [
            f"# {title}",
            "",
            f"Status: `{payload['status']}`",
            "",
            "This report is analysis-only. It does not touch MT5 runtime, orders, charts, or running EAs.",
            "",
            "## Resolution Strength",
            "",
            f"- Scoreboard mode: `{payload.get('scoreboard_mode', 'all_resolved')}`",
            f"- Replay model: `{payload.get('replay_model', 'executor_v2')}`",
            f"- Broker-joined rows: `{payload['broker_join_resolved_count']}`",
            f"- M5 replay rows: `{payload['replay_resolved_count']}`",
            f"- Unresolved rows: `{payload['unresolved_count']}`",
            "",
            "## Top Groups",
            "",
            _table(top_rows, _scoreboard_fields()),
            "",
            "## Portfolio Rule",
            "",
            "Use `aggregation_level=family` rows for portfolio totals. Candidate rows can double-count clone signals.",
            "If replay calibration is quarantined, use scoreboards generated with `scoreboard_mode=broker_joined_only`.",
            "",
        ]
    )


def _minute_key(value: str) -> str:
    parsed = _parse_time(value)
    if parsed is None:
        return ""
    return parsed.strftime("%Y-%m-%d %H:%M")


def _offset_minute(minute: str, offset: int) -> str:
    parsed = datetime.strptime(minute, "%Y-%m-%d %H:%M")
    return (parsed + timedelta(minutes=offset)).strftime("%Y-%m-%d %H:%M")


def _parse_time(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    text = text.replace("T", " ").replace("Z", "")
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def _format_time(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _float(value: str | None) -> float | None:
    try:
        return float(str(value or "").strip())
    except ValueError:
        return None


def _counter(rows: list[dict[str, str]], *keys: str) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, ...]] = Counter()
    for row in rows:
        counts[tuple(row.get(key, "UNKNOWN") or "UNKNOWN" for key in keys)] += 1
    result: list[dict[str, Any]] = []
    for key_tuple, count in counts.most_common():
        item = {key: value for key, value in zip(keys, key_tuple)}
        item["count"] = count
        result.append(item)
    return result


def _status(rows: list[dict[str, str]], bars_supplied: bool) -> str:
    if not rows:
        return "NO_SIGNAL_ROWS"
    unresolved = sum(1 for row in rows if row["resolution_status"].startswith("UNRESOLVED"))
    if unresolved == 0:
        return "PASS_ALL_SIGNALS_RESOLVED"
    if bars_supplied:
        return "PARTIAL_REVIEW_BARS_SUPPLIED"
    return "PARTIAL_REVIEW_NEEDS_FRESH_M5_BARS"


def _resolved_fields() -> list[str]:
    return [
        "timestamp_broker",
        "m5_bar_time",
        "time_bucket",
        "candidate",
        "family",
        "lane",
        "regime",
        "symbol",
        "direction",
        "normalized_direction",
        "legacy_shadow_action",
        "legacy_shadow_reason",
        "proposed_v2_shadow_action",
        "proposed_v2_shadow_reason",
        "trend_veto_action",
        "trend_veto_reason",
        "fixed_shadow_action",
        "fixed_shadow_reason",
        "entry_price",
        "stop_loss",
        "take_profit",
        "stop_distance_points",
        "spread_points",
        "cost_bucket",
        "evidence_tier",
        "resolution_status",
        "resolution_source",
        "matched_position_ticket",
        "actual_state",
        "actual_profit_aed",
        "actual_exit_time",
        "actual_exit_price",
        "replay_model",
        "replay_entry_time",
        "replay_entry_price",
        "replay_synthetic_stop_loss",
        "replay_synthetic_take_profit",
        "replay_signal_risk_points",
        "replay_spread_points",
        "replay_bars_scanned",
        "replay_exit_time",
        "replay_exit_price",
        "gross_outcome_r",
        "estimated_cost_r",
        "cost_source",
        "net_outcome_r",
        "v1_resolution_status",
        "v1_resolution_source",
        "v1_replay_bars_scanned",
        "v1_replay_exit_time",
        "v1_replay_exit_price",
        "v1_gross_outcome_r",
        "v1_estimated_cost_r",
        "v1_cost_source",
        "v1_net_outcome_r",
        "_source_file",
    ]


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Observer Outcome Resolution Report",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["authority"],
        "",
        f"Shadow files: `{payload['shadow_files_dir']}`",
        f"Actual trades CSV: `{payload['actual_trades_csv']}`",
        f"Bars dir: `{payload['bars_dir'] or 'not supplied'}`",
        f"Replay model: `{payload['replay_model']}`",
        f"Scoreboard mode: `{payload['scoreboard_mode']}`",
        f"Signals: `{payload['signal_count']}`",
        f"Broker trade rows: `{payload['actual_trade_rows']}`",
        f"Resolved rows: `{payload['resolved_count']}`",
        f"Broker-joined rows: `{payload['broker_join_resolved_count']}`",
        f"M5 replay rows: `{payload['replay_resolved_count']}`",
        f"Unresolved rows: `{payload['unresolved_count']}`",
        f"Scoreboard JSON: `{payload['scoreboard_json']}`",
        f"Scoreboard CSV: `{payload['scoreboard_csv']}`",
        "",
        "## Notes",
        "",
    ]
    lines.extend(f"- {note}" for note in payload["notes"])
    lines.extend(
        [
            "",
            "## By Resolution Status",
            "",
            _table(payload["by_resolution_status"], ["resolution_status", "count"]),
            "",
            "## By Evidence Tier",
            "",
            _table(payload["by_evidence_tier"], ["evidence_tier", "resolution_status", "count"]),
            "",
            "## By Resolution Source",
            "",
            _table(payload["by_resolution_source"], ["resolution_source", "resolution_status", "count"]),
            "",
            "## Broker-Fill Scoreboards",
            "",
            "These tables use only `evidence_tier=BROKER` rows. They are the authoritative observer outcome view.",
            "",
            "### By Session",
            "",
            _table(payload["broker_fill_scoreboards"]["session"], _dimension_fields()),
            "",
            "### By Cost Bucket",
            "",
            _table(payload["broker_fill_scoreboards"]["cost"], _dimension_fields()),
            "",
            "### By Direction",
            "",
            _table(payload["broker_fill_scoreboards"]["direction"], _dimension_fields()),
            "",
            "### By Regime",
            "",
            _table(payload["broker_fill_scoreboards"]["regime"], _dimension_fields()),
            "",
            "### By Family",
            "",
            _table(payload["broker_fill_scoreboards"]["family"], _dimension_fields()),
            "",
            "### By Lane",
            "",
            _table(payload["broker_fill_scoreboards"]["lane"], _dimension_fields()),
            "",
            "### By EA / Symbol / Session",
            "",
            _table(payload["broker_fill_scoreboards"]["ea_symbol_session"], _dimension_fields()),
            "",
            "## Replay Reference Scoreboards",
            "",
            "These tables use only `evidence_tier=REPLAY` rows. Treat them as secondary reference evidence.",
            "",
            "### Replay By Session",
            "",
            _table(payload["replay_reference_scoreboards"]["session"], _dimension_fields()),
            "",
            "## By Proposed V2 Action",
            "",
            _table(payload["by_proposed_v2_action"], ["proposed_v2_shadow_action", "resolution_status", "count"]),
            "",
            "## By Candidate",
            "",
            _table(payload["by_candidate"], ["candidate", "count"]),
            "",
            "## Bar Export Quality",
            "",
            _table(
                payload["bar_quality"],
                [
                    "symbol",
                    "status",
                    "rows",
                    "first_bar",
                    "last_bar",
                    "continuity_pct",
                    "gap_count_gt_5m",
                    "duplicate_bar_times",
                ],
            ),
            "",
            "## Boundary",
            "",
            "- This is analysis-only.",
            "- It does not modify MT5 runtime or running EAs.",
            "- Rows without broker match or fresh M5 bars remain unresolved.",
            "",
        ]
    )
    return "\n".join(lines)


def _table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve observer would-signals against broker trades and optional M5 bars.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--shadow-files-dir", type=Path, default=DEFAULT_SHADOW_FILES_DIR)
    parser.add_argument("--actual-trades-csv", type=Path, default=None)
    parser.add_argument("--bars-dir", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--signal-glob", default=DEFAULT_SIGNAL_GLOB)
    parser.add_argument("--scoreboard-json", type=Path, default=None)
    parser.add_argument("--cost-model-csv", type=Path, default=None)
    parser.add_argument("--scoreboard-mode", choices=["all_resolved", "broker_joined_only"], default="all_resolved")
    args = parser.parse_args()
    output = generate_observer_outcome_resolution(
        args.phase1_root,
        shadow_files_dir=args.shadow_files_dir,
        actual_trades_csv=args.actual_trades_csv,
        bars_dir=args.bars_dir,
        output_json=args.output_json,
        signal_glob=args.signal_glob,
        scoreboard_json=args.scoreboard_json,
        cost_model_csv=args.cost_model_csv,
        scoreboard_mode=args.scoreboard_mode,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
