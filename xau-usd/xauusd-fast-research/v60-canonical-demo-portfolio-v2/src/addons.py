from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from executor import append_event, atomic_write_json, parse_utc, utc_text
from feeds import REPO_ROOT, RESEARCH_ROOT, _load_module, _target_guard, _transport


STATE_SCHEMA = "xauusd_v60_canonical_addon_state_v2"
HEALTH_SLEEVES = (
    "V7_SWING_HEALTH",
    "V8_RETEST_HEALTH",
    "V57_BREAK_SWING_H4ADX_HIGH",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_id(sleeve: str, event_id: str) -> str:
    return hashlib.sha256(f"{sleeve}|{event_id}".encode("ascii")).hexdigest()[:24]


def _profit_factor(values: list[float]) -> float:
    gain = sum(value for value in values if value > 0.0)
    loss = -sum(value for value in values if value < 0.0)
    if loss == 0.0:
        return math.inf if gain > 0.0 else 0.0
    return gain / loss


def _execute_single_rule(
    frame: pd.DataFrame, maximum_open: int = 1, maximum_daily: int = 2
) -> pd.DataFrame:
    ordered = frame.sort_values(["entry_time", "event_id"], kind="mergesort").drop_duplicates(
        "event_id", keep="first"
    )
    active: list[pd.Timestamp] = []
    daily: dict[Any, int] = {}
    accepted: list[int] = []
    for index, row in ordered.iterrows():
        active = [exit_time for exit_time in active if exit_time > row["entry_time"]]
        date = row["entry_time"].date()
        if len(active) >= maximum_open or daily.get(date, 0) >= maximum_daily:
            continue
        accepted.append(index)
        active.append(row["exit_time"])
        daily[date] = daily.get(date, 0) + 1
    return ordered.loc[accepted].copy().reset_index(drop=True)


def _mechanism(frame: pd.DataFrame) -> pd.Series:
    return pd.Series(
        np.select(
            [
                frame["BREAK_AND_RUN"].eq(1)
                & frame["DOWNSIDE_IMPULSE_RETEST"].eq(0)
                & frame["OPENING_RANGE_REVERSAL"].eq(0),
                frame["BREAK_AND_RUN"].eq(0)
                & frame["DOWNSIDE_IMPULSE_RETEST"].eq(1)
                & frame["OPENING_RANGE_REVERSAL"].eq(0),
                frame["BREAK_AND_RUN"].eq(0)
                & frame["DOWNSIDE_IMPULSE_RETEST"].eq(0)
                & frame["OPENING_RANGE_REVERSAL"].eq(1),
            ],
            ["BREAK", "RETEST", "OPEN_REV"],
            default="MULTI",
        ),
        index=frame.index,
    )


def historical_rule_frames(config: Mapping[str, Any]) -> dict[str, pd.DataFrame]:
    actions = pd.read_parquet(REPO_ROOT / config["feeds"]["historical_action_labels"])
    for column in ("signal_time", "entry_time", "exit_time"):
        actions[column] = pd.to_datetime(actions[column], utc=True)
    actions["mechanism"] = _mechanism(actions)
    actions["h1adx"] = pd.cut(
        actions["h1_adx"], [-np.inf, 20.0, 30.0, np.inf], labels=["LOW", "MID", "HIGH"]
    ).astype(str)
    actions["atrstate"] = pd.cut(
        actions["atr_ratio"], [-np.inf, 0.8, 1.2, np.inf], labels=["LOW", "NORMAL", "HIGH"]
    ).astype(str)
    actions["h4adx"] = pd.cut(
        actions["h4_adx"], [-np.inf, 20.0, 30.0, np.inf], labels=["LOW", "MID", "HIGH"]
    ).astype(str)

    v7 = actions.loc[
        actions["regime"].ne("UNSAFE_SHOCK")
        & actions["action_id"].eq("SWING_2R_36H")
        & actions["h1_adx"].gt(20.0)
        & actions["h1_adx"].le(30.0)
        & actions["dir_return_1h_atr"].le(-0.25)
    ]
    v7 = _execute_single_rule(v7)
    v8 = actions.loc[
        actions["regime"].ne("UNSAFE_SHOCK")
        & actions["mechanism"].eq("RETEST")
        & actions["action_id"].eq("INTRADAY_1P5R_12H")
        & actions["h1adx"].eq("MID")
        & actions["atrstate"].eq("HIGH")
    ]
    v8 = _execute_single_rule(v8)
    v57 = actions.loc[
        actions["regime"].ne("UNSAFE_SHOCK")
        & actions["mechanism"].eq("BREAK")
        & actions["action_id"].eq("SWING_2R_36H")
        & actions["h4adx"].eq("HIGH")
    ]
    v57 = _execute_single_rule(v57)

    return {
        "V7_SWING_HEALTH": v7,
        "V8_RETEST_HEALTH": v8,
        "V57_BREAK_SWING_H4ADX_HIGH": v57,
    }


def _seed_history(config: Mapping[str, Any]) -> dict[str, Any]:
    sleeves = historical_rule_frames(config)
    result: dict[str, Any] = {}
    for sleeve, frame in sleeves.items():
        completed = frame.sort_values(["exit_time", "event_id"], kind="mergesort").tail(100)
        history = [
            {
                "event_id": str(row.event_id),
                "exit_time_utc": pd.Timestamp(row.exit_time).isoformat().replace("+00:00", "Z"),
                "pnl_usd": float(row.stress_net_r) * float(row.risk_usd),
            }
            for row in completed.itertuples(index=False)
        ]
        result[sleeve] = {
            "history": history,
            "pending": [],
            "daily_entries": {},
            "seen_events": {},
        }
    return result


def _load_state(path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    if path.is_file():
        state = _read_json(path)
        if state.get("schema_version") != STATE_SCHEMA:
            raise ValueError("Unexpected add-on state schema")
        return state
    return {
        "schema_version": STATE_SCHEMA,
        "created_at_utc": utc_text(datetime.now(UTC)),
        "historical_seed_source": str(config["feeds"]["historical_action_labels"]),
        "sleeves": _seed_history(config),
        "v25": {"seen_signals": {}, "pending": [], "daily_entries": {}, "cooldown_until_utc": None},
    }


def _rates_frame(rates: Any, minutes: int, point: float) -> pd.DataFrame:
    frame = pd.DataFrame(rates)
    required = {"time", "open", "high", "low", "close", "spread", "tick_volume"}
    if frame.empty or not required.issubset(frame.columns):
        raise ValueError(f"MT5 {minutes}-minute bars are unavailable")
    frame["bar_start_utc"] = pd.to_datetime(frame["time"], unit="s", utc=True)
    frame["bar_end_utc"] = frame["bar_start_utc"] + pd.Timedelta(minutes=minutes)
    spread = frame["spread"].astype(float) * float(point)
    for field in ("open", "high", "low", "close"):
        frame[f"bid_{field}"] = frame[field].astype(float)
        frame[f"ask_{field}"] = frame[field].astype(float) + spread
        frame[f"mid_{field}"] = frame[field].astype(float) + spread / 2.0
    frame["timestamp_utc"] = frame["bar_end_utc"]
    frame["tick_count"] = frame["tick_volume"].astype(float)
    return frame.sort_values("bar_start_utc", kind="mergesort").drop_duplicates(
        "bar_start_utc", keep="last"
    ).reset_index(drop=True)


def _market_frames(mt5: Any, symbol: str, point: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    now = pd.Timestamp.now(tz="UTC")
    completed_m5 = now.floor("5min")
    raw_m5 = _rates_frame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 60_000), 5, point)
    m5 = raw_m5.loc[raw_m5["bar_end_utc"].le(completed_m5)].copy()
    h1 = _rates_frame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 6_000), 60, point)
    h1 = h1.loc[h1["bar_end_utc"].le(now.floor("1h"))].copy()
    h4 = _rates_frame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 1_600), 240, point)
    h4 = h4.loc[h4["bar_end_utc"].le(now.floor("4h"))].copy()

    feature_module = _load_module(
        "v60_v2_addon_market_features",
        RESEARCH_ROOT / "high-frequency-expansion-v1" / "src" / "dataset.py",
    )
    regime_module = _load_module(
        "v60_v2_addon_regimes",
        RESEARCH_ROOT / "independent-specialists-v1" / "src" / "research.py",
    )
    expansion_config = _read_json(
        RESEARCH_ROOT / "high-frequency-expansion-v1" / "config" / "high_frequency_expansion_v1.json"
    )
    classified_h4 = regime_module.classify_h4(h4, expansion_config["regime"])
    m5["quote_intensity_ratio"] = 1.0
    m5["tick_imbalance_5m"] = 0.0
    m5["tick_imbalance_15m"] = 0.0
    m5["tick_book_imbalance_mean"] = 0.0
    m5["tick_microprice_edge_mean"] = 0.0
    m5["price_efficiency_5m"] = 0.0
    market = feature_module.prepare_market_features(m5, h1, classified_h4)
    return raw_m5, market


def _sensor_events(config: Mapping[str, Any]) -> pd.DataFrame:
    root = Path(config["feeds"]["terminal_files_directory"])
    rows: list[pd.DataFrame] = []
    expected_runs = {
        "BREAK_AND_RUN": "V60_V2_BREAK_AND_RUN_SENSOR",
        "DOWNSIDE_IMPULSE_RETEST": "V60_V2_DOWNSIDE_RETEST_SENSOR",
        "OPENING_RANGE_REVERSAL": "V60_V2_OPENING_REVERSAL_SENSOR",
    }
    for family, filename in config["feeds"]["sensor_logs"].items():
        path = root / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path, sep="\t", on_bad_lines="skip")
        required = {"timestamp_broker", "run_id", "stage", "direction"}
        if not required.issubset(frame.columns):
            raise ValueError(f"Sensor log schema changed: {path}")
        frame = frame.loc[
            frame["run_id"].eq(expected_runs[family])
            & frame["stage"].eq("WOULD_SIGNAL")
            & frame["direction"].isin(["LONG", "SHORT"])
        ].copy()
        if frame.empty:
            continue
        frame["signal_time"] = pd.to_datetime(
            frame["timestamp_broker"], format="%Y.%m.%d %H:%M:%S", utc=True
        )
        frame["family"] = family
        rows.append(frame[["signal_time", "direction", "family"]])
    if not rows:
        return pd.DataFrame(columns=["signal_time", "direction", *expected_runs])
    raw = pd.concat(rows, ignore_index=True).drop_duplicates()
    flags = (
        raw.assign(value=1)
        .pivot_table(
            index=["signal_time", "direction"],
            columns="family",
            values="value",
            aggfunc="max",
            fill_value=0,
        )
        .reset_index()
    )
    flags.columns.name = None
    for family in expected_runs:
        if family not in flags:
            flags[family] = 0
    flags["event_id"] = (
        flags["signal_time"].dt.strftime("%Y%m%dT%H%M%SZ") + "_" + flags["direction"]
    )
    return flags.sort_values(["signal_time", "direction"], kind="mergesort").reset_index(drop=True)


def _resolve_bar_pending(
    sleeve: dict[str, Any], bars: pd.DataFrame, as_of: pd.Timestamp, *, inclusive: bool
) -> None:
    remaining: list[dict[str, Any]] = []
    resolved: list[dict[str, Any]] = []
    for pending in sleeve["pending"]:
        entry_time = pd.Timestamp(pending["entry_time_utc"])
        deadline = pd.Timestamp(pending["deadline_utc"])
        selected = bars.loc[
            bars["bar_start_utc"].ge(entry_time)
            & bars["bar_start_utc"].le(as_of)
        ]
        direction = 1 if pending["direction"] == "LONG" else -1
        exit_time: pd.Timestamp | None = None
        exit_price = float(pending["entry_price"])
        for row in selected.itertuples(index=False):
            start = pd.Timestamp(row.bar_start_utc)
            if start >= deadline:
                exit_time = start
                exit_price = float(row.bid_open if direction > 0 else row.ask_open)
                break
            executable_open = float(row.bid_open if direction > 0 else row.ask_open)
            executable_low = float(row.bid_low if direction > 0 else row.ask_low)
            executable_high = float(row.bid_high if direction > 0 else row.ask_high)
            stop_hit = executable_low <= pending["stop"] if direction > 0 else executable_high >= pending["stop"]
            target_hit = executable_high >= pending["target"] if direction > 0 else executable_low <= pending["target"]
            if (direction > 0 and executable_open < pending["stop"]) or (
                direction < 0 and executable_open > pending["stop"]
            ):
                exit_time, exit_price = start, executable_open
                break
            if (direction > 0 and executable_open >= pending["target"]) or (
                direction < 0 and executable_open <= pending["target"]
            ):
                exit_time, exit_price = start, float(pending["target"])
                break
            if stop_hit:
                exit_time, exit_price = pd.Timestamp(row.bar_end_utc), float(pending["stop"])
                break
            if target_hit:
                exit_time, exit_price = pd.Timestamp(row.bar_end_utc), float(pending["target"])
                break
        if exit_time is None or exit_time > as_of or (not inclusive and exit_time == as_of):
            remaining.append(pending)
            continue
        hold_days = max(0.0, (exit_time - entry_time).total_seconds() / 86_400.0)
        gross_r = direction * (exit_price - float(pending["entry_price"])) / float(pending["risk_usd"])
        extra_cost_r = (0.30 + hold_days * 0.35) / float(pending["risk_usd"])
        pnl = (gross_r - extra_cost_r - 0.05) * float(pending["risk_usd"])
        resolved.append(
            {"event_id": pending["event_id"], "exit_time_utc": exit_time.isoformat().replace("+00:00", "Z"), "pnl_usd": pnl}
        )
    sleeve["pending"] = remaining
    sleeve["history"] = sorted(
        [*sleeve["history"], *resolved], key=lambda item: (item["exit_time_utc"], item["event_id"])
    )[-100:]


def _health(sleeve: Mapping[str, Any]) -> tuple[bool, float, float, int]:
    values = [float(item["pnl_usd"]) for item in sleeve["history"][-100:]]
    pf = _profit_factor(values)
    net = sum(values)
    return len(values) >= 100 and pf >= 1.0 and net > 0.0, pf, net, len(values)


def _event_features(event: Any, market: pd.DataFrame) -> dict[str, Any] | None:
    feature_time = pd.Timestamp(event.signal_time).floor("5min")
    selected = market.loc[market["timestamp_utc"].eq(feature_time)]
    if selected.empty:
        return None
    row = selected.iloc[-1]
    sign = 1.0 if event.direction == "LONG" else -1.0
    return {
        "regime": str(row["regime"]),
        "h1_adx": float(row["h1_adx"]),
        "atr_ratio": float(row["atr_ratio"]),
        "h4_adx": float(row["adx_h4"]),
        "dir_return_1h_atr": sign * float(row["return_1h_atr"]),
        "signal_atr": float(row["atr_m5"]),
    }


def _append_once(path: Path, row: Mapping[str, Any]) -> bool:
    candidate_id = str(row["candidate_id"])
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("candidate_id") == candidate_id:
                return False
    append_event(path, row)
    return True


def _process_health_events(
    config: Mapping[str, Any], state: dict[str, Any], raw_m5: pd.DataFrame, market: pd.DataFrame
) -> dict[str, Any]:
    activation = pd.Timestamp(config["feeds"]["activation_utc"])
    events = _sensor_events(config)
    events = events.loc[events["signal_time"].ge(activation)]
    output = _transport(config, "addons") / "addon_candidates.jsonl"
    emitted = 0
    decisions: dict[str, int] = {}
    complete_bars = raw_m5.loc[raw_m5["bar_end_utc"].le(pd.Timestamp.now(tz="UTC").floor("5min"))]

    for event in events.itertuples(index=False):
        features = _event_features(event, market)
        if features is None or not all(math.isfinite(float(features[key])) for key in ("h1_adx", "atr_ratio", "h4_adx", "dir_return_1h_atr", "signal_atr")):
            continue
        pure_break = event.BREAK_AND_RUN == 1 and event.DOWNSIDE_IMPULSE_RETEST == 0 and event.OPENING_RANGE_REVERSAL == 0
        pure_retest = event.BREAK_AND_RUN == 0 and event.DOWNSIDE_IMPULSE_RETEST == 1 and event.OPENING_RANGE_REVERSAL == 0
        eligible = {
            "V7_SWING_HEALTH": features["regime"] != "UNSAFE_SHOCK"
            and 20.0 < features["h1_adx"] <= 30.0
            and features["dir_return_1h_atr"] <= -0.25,
            "V8_RETEST_HEALTH": features["regime"] != "UNSAFE_SHOCK"
            and pure_retest
            and 20.0 < features["h1_adx"] <= 30.0
            and features["atr_ratio"] > 1.2,
            "V57_BREAK_SWING_H4ADX_HIGH": features["regime"] != "UNSAFE_SHOCK"
            and pure_break
            and features["h4_adx"] > 30.0,
        }
        emitted_event: set[str] = set()
        for sleeve_id in HEALTH_SLEEVES:
            sleeve = state["sleeves"][sleeve_id]
            if event.event_id in sleeve["seen_events"]:
                if sleeve["seen_events"][event.event_id] == "EMITTED":
                    emitted_event.add(sleeve_id)
                continue
            _resolve_bar_pending(sleeve, complete_bars, pd.Timestamp(event.signal_time), inclusive=False)
            if not eligible[sleeve_id]:
                sleeve["seen_events"][event.event_id] = "RULE_INELIGIBLE"
                continue
            entry_time = pd.Timestamp(event.signal_time).ceil("5min")
            entry_rows = raw_m5.loc[raw_m5["bar_start_utc"].eq(entry_time)]
            if entry_rows.empty:
                continue
            entry_row = entry_rows.iloc[-1]
            day = entry_time.date().isoformat()
            active = [item for item in sleeve["pending"] if pd.Timestamp(item["deadline_utc"]) > entry_time]
            if len(active) >= 1 or int(sleeve["daily_entries"].get(day, 0)) >= 2:
                sleeve["seen_events"][event.event_id] = "VIRTUAL_CAPACITY_BLOCK"
                continue
            if sleeve_id == "V8_RETEST_HEALTH":
                stop_atr, minimum_stop, target_r, hold_hours, maximum_risk = 1.5, 3.0, 1.5, 12.0, 20.0
            else:
                stop_atr, minimum_stop, target_r, hold_hours, maximum_risk = 2.25, 3.5, 2.0, 36.0, 30.0
            risk = max(stop_atr * features["signal_atr"], minimum_stop)
            direction = 1 if event.direction == "LONG" else -1
            entry = float(entry_row["ask_open"] if direction > 0 else entry_row["bid_open"])
            pending = {
                "event_id": event.event_id,
                "entry_time_utc": entry_time.isoformat().replace("+00:00", "Z"),
                "deadline_utc": (entry_time + pd.Timedelta(hours=hold_hours)).isoformat().replace("+00:00", "Z"),
                "direction": event.direction,
                "entry_price": entry,
                "stop": entry - direction * risk,
                "target": entry + direction * target_r * risk,
                "risk_usd": risk,
            }
            sleeve["pending"].append(pending)
            sleeve["daily_entries"][day] = int(sleeve["daily_entries"].get(day, 0)) + 1
            passed, pf, net, count = _health(sleeve)
            reason = "HEALTH_PASS" if passed else "HEALTH_BLOCK"
            if risk > maximum_risk:
                reason = "RISK_CAP_BLOCK"
            if sleeve_id == "V57_BREAK_SWING_H4ADX_HIGH" and emitted_event.intersection(
                {"V7_SWING_HEALTH", "V8_RETEST_HEALTH"}
            ):
                reason = "DUPLICATE_EVENT_BLOCK"
            if reason == "HEALTH_PASS":
                row = {
                    "candidate_id": _candidate_id(sleeve_id, event.event_id),
                    "event_id": event.event_id,
                    "specialist_id": sleeve_id,
                    "scheduled_entry_time_utc": entry_time.isoformat().replace("+00:00", "Z"),
                    "direction": event.direction,
                    "signal_atr": features["signal_atr"],
                    "stop_atr": risk / features["signal_atr"],
                    "target_r": target_r,
                    "hold_hours": hold_hours,
                    "health_completed_count": count,
                    "health_profit_factor": pf,
                    "health_net_usd": net,
                }
                emitted += int(_append_once(output, row))
                emitted_event.add(sleeve_id)
                sleeve["seen_events"][event.event_id] = "EMITTED"
            else:
                sleeve["seen_events"][event.event_id] = reason
            decisions[reason] = decisions.get(reason, 0) + 1

    now = pd.Timestamp.now(tz="UTC")
    for sleeve_id in HEALTH_SLEEVES:
        _resolve_bar_pending(state["sleeves"][sleeve_id], complete_bars, now, inclusive=True)
    return {"events_observed": int(len(events)), "candidates_emitted": emitted, "decision_counts": decisions}


def _process_v25(
    mt5: Any,
    config: Mapping[str, Any],
    state: dict[str, Any],
    raw_m5: pd.DataFrame,
) -> dict[str, Any]:
    now = pd.Timestamp.now(tz="UTC")
    tick_start = now - pd.Timedelta(days=4)
    ticks = mt5.copy_ticks_range(
        config["account"]["symbol"], tick_start.to_pydatetime(), now.to_pydatetime(), mt5.COPY_TICKS_ALL
    )
    tick_frame = pd.DataFrame(ticks)
    if tick_frame.empty:
        return {"ready": False, "reason": "NO_MT5_TICK_HISTORY"}
    tick_frame = tick_frame.rename(columns={"time_msc": "tick_time_msc"})
    tick_frame["spread_price"] = tick_frame["ask"] - tick_frame["bid"]

    def resolve_pending(as_of: pd.Timestamp, *, inclusive: bool) -> None:
        remaining: list[dict[str, Any]] = []
        exits: list[pd.Timestamp] = []
        as_of_ms = int(as_of.value // 1_000_000)
        for pending in state["v25"]["pending"]:
            if "entry_tick_msc" not in pending:
                remaining.append(pending)
                continue
            deadline_ms = int(pd.Timestamp(pending["deadline_utc"]).value // 1_000_000)
            selected = tick_frame.loc[
                tick_frame["tick_time_msc"].ge(int(pending["entry_tick_msc"]))
                & tick_frame["tick_time_msc"].le(as_of_ms)
            ]
            direction_sign = int(pending["direction_sign"])
            executable = selected["bid"] if direction_sign > 0 else selected["ask"]
            stop_hit = executable.le(float(pending["stop"])) if direction_sign > 0 else executable.ge(float(pending["stop"]))
            target_hit = executable.ge(float(pending["target"])) if direction_sign > 0 else executable.le(float(pending["target"]))
            hit = selected.loc[stop_hit | target_hit]
            exit_msc: int | None = None
            if not hit.empty:
                exit_msc = int(hit.iloc[0]["tick_time_msc"])
            elif as_of_ms >= deadline_ms:
                horizon = tick_frame.loc[tick_frame["tick_time_msc"].ge(deadline_ms)]
                if not horizon.empty and int(horizon.iloc[0]["tick_time_msc"]) <= as_of_ms:
                    exit_msc = int(horizon.iloc[0]["tick_time_msc"])
            if exit_msc is None or (not inclusive and exit_msc == as_of_ms):
                remaining.append(pending)
                continue
            exits.append(pd.Timestamp(exit_msc, unit="ms", tz="UTC"))
        state["v25"]["pending"] = remaining
        if exits:
            latest = max(exits) + pd.Timedelta(minutes=5)
            current = state["v25"].get("cooldown_until_utc")
            if current is None or latest > pd.Timestamp(current):
                state["v25"]["cooldown_until_utc"] = latest.isoformat().replace("+00:00", "Z")

    r4_package = RESEARCH_ROOT / "capital-r4-chop-forward-v34"
    r4 = _load_module("v60_v2_v25_transport", r4_package / "src" / "chop_forward.py")
    frozen = r4.load_frozen(REPO_ROOT, r4_package)
    quality = _read_json(r4_package / "config" / "capital_r4_chop_forward_v34.json")["data_quality"]
    quote_m5 = r4.aggregate_capital_quotes(tick_frame, completed_through=now.floor("5min"), quality=quality)
    historical = r4.add_historical_micro_placeholders(
        raw_m5.loc[raw_m5["bar_end_utc"].le(now.floor("5min"))]
    )
    combined = r4.overlay_quote_bars(historical, quote_m5)
    frame = r4.build_feature_frame(combined, frozen)
    v25_package = RESEARCH_ROOT / "chop-failed-reversion-rawtick-v25"
    v25 = _load_module("v60_v2_v25_rule", v25_package / "src" / "confirmation.py")
    v25_config = _read_json(v25_package / "config" / "chop_failed_reversion_rawtick_v25.json")
    definition = v25_config["candidate"]
    mask, direction = v25.independent_signal_mask_direction(frame, definition["parameters"])
    mask = (
        mask
        & frame["quote_quality_passed"].fillna(False)
        & frame["quote_contiguous_15m"].fillna(False)
        & frame["bar_end_utc"].ge(pd.Timestamp(config["feeds"]["activation_utc"]))
    )
    output = _transport(config, "addons") / "addon_candidates.jsonl"
    emitted = 0
    observed = 0
    for index in np.flatnonzero(mask.to_numpy(dtype=bool)):
        signal_time = pd.Timestamp(frame["bar_end_utc"].iat[int(index)])
        event_id = f"V25_{signal_time.strftime('%Y%m%dT%H%M%SZ')}"
        if event_id in state["v25"]["seen_signals"]:
            continue
        observed += 1
        resolve_pending(signal_time, inclusive=False)
        active = list(state["v25"]["pending"])
        cooldown = state["v25"].get("cooldown_until_utc")
        if active or (cooldown and signal_time < pd.Timestamp(cooldown)):
            state["v25"]["seen_signals"][event_id] = "VIRTUAL_CAPACITY_BLOCK"
            continue
        sign = int(direction.iat[int(index)])
        signal_atr = float(frame["risk_atr"].iat[int(index)])
        timely = tick_frame.loc[
            tick_frame["tick_time_msc"].ge(int(signal_time.value // 1_000_000))
            & tick_frame["tick_time_msc"].le(
                int((signal_time + pd.Timedelta(minutes=5)).value // 1_000_000)
            )
        ]
        if timely.empty:
            state["v25"]["seen_signals"][event_id] = "NO_TIMELY_ENTRY_QUOTE"
            continue
        entry_quote = timely.iloc[0]
        entry_time = pd.Timestamp(int(entry_quote["tick_time_msc"]), unit="ms", tz="UTC")
        day = entry_time.date().isoformat()
        if int(state["v25"]["daily_entries"].get(day, 0)) >= 4:
            state["v25"]["seen_signals"][event_id] = "VIRTUAL_DAILY_CAP"
            continue
        risk = signal_atr
        entry_price = float(entry_quote["ask"] if sign > 0 else entry_quote["bid"])
        spread_r = float(entry_quote["ask"] - entry_quote["bid"]) / risk
        if not math.isfinite(risk) or risk <= 0.0 or risk > 50.0 or spread_r > 0.15:
            state["v25"]["seen_signals"][event_id] = "VIRTUAL_EXECUTION_GUARD"
            continue
        candidate = {
            "candidate_id": _candidate_id("V25_CHOP", event_id),
            "event_id": event_id,
            "specialist_id": "V25_CHOP",
            "origin_attempt": 39583,
            "scheduled_entry_time_utc": signal_time.isoformat().replace("+00:00", "Z"),
            "direction": "LONG" if sign > 0 else "SHORT",
            "direction_sign": sign,
            "signal_atr": signal_atr,
            "stop_atr": 1.0,
            "target_r": 2.0,
            "hold_hours": 12.0,
        }
        emitted += int(_append_once(output, candidate))
        state["v25"]["seen_signals"][event_id] = "EMITTED"
        state["v25"]["daily_entries"][day] = int(state["v25"]["daily_entries"].get(day, 0)) + 1
        state["v25"]["pending"].append(
            {
                "event_id": event_id,
                "entry_tick_msc": int(entry_quote["tick_time_msc"]),
                "deadline_utc": (entry_time + pd.Timedelta(hours=12)).isoformat().replace("+00:00", "Z"),
                "direction_sign": sign,
                "stop": entry_price - sign * risk,
                "target": entry_price + sign * 2.0 * risk,
            }
        )
    resolve_pending(now, inclusive=True)
    return {
        "ready": len(quote_m5) >= 384,
        "tick_rows": int(len(tick_frame)),
        "quality_m5_rows": int(quote_m5["quote_quality_passed"].sum()) if not quote_m5.empty else 0,
        "signals_observed": observed,
        "candidates_emitted": emitted,
    }


def run_addon_feeds(config: Mapping[str, Any], *, include_v25: bool) -> dict[str, Any]:
    import MetaTrader5 as mt5

    terminal = str(Path(config["account"]["terminal_exe"]))
    if not mt5.initialize(path=terminal, portable=True):
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:
        account = mt5.account_info()
        terminal_info = mt5.terminal_info()
        _target_guard(config)(account, terminal_info)
        symbol = mt5.symbol_info(config["account"]["symbol"])
        if symbol is None:
            raise RuntimeError("XAUUSD symbol information is unavailable")
        raw_m5, market = _market_frames(mt5, config["account"]["symbol"], float(symbol.point))
        runtime = _transport(config, "addons")
        state_path = runtime / "addon_state.json"
        state = _load_state(state_path, config)
        health = _process_health_events(config, state, raw_m5, market)
        v25 = _process_v25(mt5, config, state, raw_m5) if include_v25 else {"ready": None, "reason": "NOT_DUE"}
        atomic_write_json(state_path, state)
        status = {
            "schema_version": "xauusd_v60_canonical_addon_status_v2",
            "updated_at_utc": utc_text(datetime.now(UTC)),
            "account_login": int(account.login),
            "ml_used": False,
            "health_sleeves": health,
            "v25": v25,
            "ready": True,
        }
        atomic_write_json(runtime / "runtime_status.json", status)
        return status
    finally:
        mt5.shutdown()
