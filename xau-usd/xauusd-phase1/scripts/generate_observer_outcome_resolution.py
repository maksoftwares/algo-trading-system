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
DEFAULT_SCOREBOARD_JSON = Path("outputs") / "reports" / "OBSERVER_TREND_VETO_SCOREBOARD.json"
DEFAULT_SCOREBOARD_MD = Path("outputs") / "reports" / "OBSERVER_TREND_VETO_SCOREBOARD.md"
DEFAULT_SCOREBOARD_CSV = Path("outputs") / "reports" / "OBSERVER_TREND_VETO_SCOREBOARD.csv"

ROUND_RETEST_CLONE_CANDIDATES = {"symbol_normalized_round_retest_v0", "round_number_retest_v0"}
WEAKNESS_TIME_BLOCKS = {"Morning 06:00-11:59", "Afternoon 12:00-15:59"}


def generate_observer_outcome_resolution(
    phase1_root: Path,
    shadow_files_dir: Path = DEFAULT_SHADOW_FILES_DIR,
    actual_trades_csv: Path | None = None,
    bars_dir: Path | None = None,
    output_json: Path | None = None,
) -> Path:
    phase1_root = phase1_root.resolve()
    shadow_files_dir = shadow_files_dir.resolve()
    actual_trades_csv = (actual_trades_csv or phase1_root / DEFAULT_ACTUAL_TRADES).resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_MD
    output_csv = output_json.with_suffix(".csv") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_CSV
    output_json.parent.mkdir(parents=True, exist_ok=True)

    signals = [row for row in _read_shadow_rows(shadow_files_dir) if _truthy(row.get("would_signal"))]
    actual_rows = _read_csv(actual_trades_csv)
    actual_index = _actual_index(actual_rows)
    bars_cache: dict[str, list[dict[str, str]]] = {}
    resolved_rows = [
        _resolve_signal(row, actual_index, bars_dir.resolve() if bars_dir else None, bars_cache)
        for row in signals
    ]
    scoreboard_rows = _scoreboard_rows(resolved_rows)
    bar_quality = _bar_quality_report(bars_dir.resolve(), signals) if bars_dir else []
    payload: dict[str, Any] = {
        "status": _status(resolved_rows, bool(bars_dir)),
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Read-only outcome resolution for observer signals. It joins to exported broker trades and optionally "
            "replays SL/TP against supplied M5 bars. It does not touch MT5 runtime, orders, positions, profiles, "
            "charts, or running EAs."
        ),
        "shadow_files_dir": str(shadow_files_dir),
        "actual_trades_csv": str(actual_trades_csv),
        "bars_dir": str(bars_dir.resolve()) if bars_dir else "",
        "signal_count": len(signals),
        "actual_trade_rows": len(actual_rows),
        "resolved_count": sum(1 for row in resolved_rows if row["resolution_status"].startswith(("BROKER_", "REPLAY_"))),
        "broker_join_resolved_count": sum(1 for row in resolved_rows if row["resolution_status"].startswith("BROKER_")),
        "replay_resolved_count": sum(1 for row in resolved_rows if row["resolution_status"].startswith("REPLAY_")),
        "unresolved_count": sum(1 for row in resolved_rows if row["resolution_status"].startswith("UNRESOLVED")),
        "by_resolution_status": _counter(resolved_rows, "resolution_status"),
        "by_resolution_source": _counter(resolved_rows, "resolution_source", "resolution_status"),
        "by_candidate": _counter(resolved_rows, "candidate"),
        "by_candidate_status": _counter(resolved_rows, "candidate", "resolution_status"),
        "by_proposed_v2_action": _counter(resolved_rows, "proposed_v2_shadow_action", "resolution_status"),
        "by_time_bucket": _counter(resolved_rows, "time_bucket", "resolution_status"),
        "bar_quality": bar_quality,
        "scoreboard_rows": scoreboard_rows,
        "scoreboard_json": str((phase1_root / DEFAULT_SCOREBOARD_JSON).resolve()),
        "scoreboard_md": str((phase1_root / DEFAULT_SCOREBOARD_MD).resolve()),
        "scoreboard_csv": str((phase1_root / DEFAULT_SCOREBOARD_CSV).resolve()),
        "notes": [
            "Broker-trade join is the preferred proof when the demo EA actually took the same signal.",
            "M5 replay is only used when a bars_dir is provided and matching June 2026 bars exist.",
            "Replay uses adverse-first same-bar ordering, so if SL and TP are both touched in the same M5 bar the row is scored as SL.",
            "Rows without broker match or bars are left unresolved; no outcome is guessed.",
            "Observer LONG/SHORT directions are normalized to broker BUY/SELL only for matching and replay; the original direction is preserved.",
            "Proposed v2 shadow policy blocks the round-retest clone family: symbol_normalized_round_retest_v0 and round_number_retest_v0.",
        ],
    }
    _write_csv(output_csv, resolved_rows, _resolved_fields())
    _write_scoreboard(phase1_root, scoreboard_rows, payload)
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return output_json


def _read_shadow_rows(files_dir: Path) -> list[dict[str, str]]:
    if not files_dir.exists():
        return []
    rows: list[dict[str, str]] = []
    for path in sorted(files_dir.glob("shadow_fix_observer_signal_log_*.csv")):
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
) -> dict[str, str]:
    resolved = _base_resolved_row(row)
    if not resolved["normalized_direction"]:
        resolved["resolution_status"] = "UNRESOLVED_UNKNOWN_DIRECTION"
        return resolved
    broker_match = _find_broker_match(row, actual_index)
    if broker_match:
        resolved.update(_broker_resolution(broker_match))
        return resolved
    replay = _replay_resolution(row, bars_dir, bars_cache) if bars_dir else None
    if replay:
        resolved.update(replay)
        return resolved
    resolved["resolution_status"] = "UNRESOLVED_NO_BROKER_MATCH_NO_REPLAY_BARS"
    return resolved


def _base_resolved_row(row: dict[str, str]) -> dict[str, str]:
    proposed_action, proposed_reason = _proposed_v2_action(row)
    return {
        "timestamp_broker": row.get("timestamp_broker", ""),
        "m5_bar_time": row.get("m5_bar_time", ""),
        "time_bucket": row.get("time_bucket", ""),
        "candidate": row.get("candidate", ""),
        "symbol": row.get("symbol", ""),
        "direction": row.get("direction", ""),
        "normalized_direction": _normalise_trade_direction(row.get("direction", "")),
        "legacy_shadow_action": row.get("shadow_action", ""),
        "legacy_shadow_reason": row.get("shadow_reason", ""),
        "proposed_v2_shadow_action": proposed_action,
        "proposed_v2_shadow_reason": proposed_reason,
        "entry_price": row.get("entry_price", ""),
        "stop_loss": row.get("stop_loss", ""),
        "take_profit": row.get("take_profit", ""),
        "resolution_status": "UNRESOLVED",
        "resolution_source": "",
        "matched_position_ticket": "",
        "actual_state": "",
        "actual_profit_aed": "",
        "actual_exit_time": "",
        "actual_exit_price": "",
        "replay_bars_scanned": "",
        "replay_exit_time": "",
        "replay_exit_price": "",
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
        "matched_position_ticket": row.get("position_ticket", ""),
        "actual_state": state,
        "actual_profit_aed": row.get("profit_aed", ""),
        "actual_exit_time": row.get("exit_time", ""),
        "actual_exit_price": row.get("exit_price", ""),
    }


def _replay_resolution(row: dict[str, str], bars_dir: Path | None, bars_cache: dict[str, list[dict[str, str]]]) -> dict[str, str] | None:
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
            return {
                "resolution_status": adverse_first_status,
                "resolution_source": "m5_bar_replay_adverse_first",
                "replay_bars_scanned": str(scanned),
                "replay_exit_time": bar.get("bar_end_utc") or bar.get("timestamp_utc") or "",
                "replay_exit_price": str(stop if adverse_first_status == "REPLAY_SL" else target),
            }
    return {
        "resolution_status": "UNRESOLVED_REPLAY_NO_SL_TP_HIT",
        "resolution_source": "m5_bar_replay_adverse_first",
        "replay_bars_scanned": str(scanned),
    }


def _load_m5_bars(bars_dir: Path, symbol: str) -> list[dict[str, str]]:
    if not bars_dir.exists():
        return []
    candidates = sorted(bars_dir.rglob(f"{symbol}*M5*.csv"))
    if not candidates:
        return []
    rows: list[dict[str, str]] = []
    for path in candidates:
        rows.extend(_read_csv(path))
    return rows


def _normalise_trade_direction(value: str | None) -> str:
    text = str(value or "").strip().upper()
    if text in {"BUY", "LONG"}:
        return "BUY"
    if text in {"SELL", "SHORT"}:
        return "SELL"
    return ""


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


def _scoreboard_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    groups: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in rows:
        key = (
            row.get("candidate", ""),
            row.get("symbol", ""),
            row.get("time_bucket", ""),
            row.get("direction", ""),
            row.get("normalized_direction", ""),
            row.get("legacy_shadow_action", ""),
            row.get("proposed_v2_shadow_action", ""),
            row.get("proposed_v2_shadow_reason", ""),
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
        scoreboard.append(
            {
                "candidate": key[0],
                "symbol": key[1],
                "time_bucket": key[2],
                "direction": key[3],
                "normalized_direction": key[4],
                "legacy_shadow_action": key[5],
                "proposed_v2_shadow_action": key[6],
                "proposed_v2_shadow_reason": key[7],
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
            }
        )
    return scoreboard


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
        "candidate",
        "symbol",
        "time_bucket",
        "direction",
        "normalized_direction",
        "legacy_shadow_action",
        "proposed_v2_shadow_action",
        "proposed_v2_shadow_reason",
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
    ]


def _write_scoreboard(phase1_root: Path, rows: list[dict[str, str]], payload: dict[str, Any]) -> None:
    json_path = phase1_root / DEFAULT_SCOREBOARD_JSON
    md_path = phase1_root / DEFAULT_SCOREBOARD_MD
    csv_path = phase1_root / DEFAULT_SCOREBOARD_CSV
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(
            {
                "status": payload["status"],
                "created_at_utc": payload["created_at_utc"],
                "authority": "Analysis-only observer outcome scoreboard. No MT5 runtime, chart, order, or EA setting changes.",
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
    top_rows = sorted(
        rows,
        key=lambda item: (
            -int(item.get("broker_join", "0")),
            -int(item.get("replay", "0")),
            item.get("candidate", ""),
            item.get("symbol", ""),
        ),
    )[:40]
    return "\n".join(
        [
            "# Observer Trend-Veto Scoreboard",
            "",
            f"Status: `{payload['status']}`",
            "",
            "This report is analysis-only. It does not touch MT5 runtime, orders, charts, or running EAs.",
            "",
            "## Resolution Strength",
            "",
            f"- Broker-joined rows: `{payload['broker_join_resolved_count']}`",
            f"- M5 replay rows: `{payload['replay_resolved_count']}`",
            f"- Unresolved rows: `{payload['unresolved_count']}`",
            "",
            "## Top Groups",
            "",
            _table(top_rows, _scoreboard_fields()),
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
        "symbol",
        "direction",
        "normalized_direction",
        "legacy_shadow_action",
        "legacy_shadow_reason",
        "proposed_v2_shadow_action",
        "proposed_v2_shadow_reason",
        "entry_price",
        "stop_loss",
        "take_profit",
        "resolution_status",
        "resolution_source",
        "matched_position_ticket",
        "actual_state",
        "actual_profit_aed",
        "actual_exit_time",
        "actual_exit_price",
        "replay_bars_scanned",
        "replay_exit_time",
        "replay_exit_price",
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
            "## By Resolution Source",
            "",
            _table(payload["by_resolution_source"], ["resolution_source", "resolution_status", "count"]),
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
    args = parser.parse_args()
    output = generate_observer_outcome_resolution(
        args.phase1_root,
        shadow_files_dir=args.shadow_files_dir,
        actual_trades_csv=args.actual_trades_csv,
        bars_dir=args.bars_dir,
        output_json=args.output_json,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
