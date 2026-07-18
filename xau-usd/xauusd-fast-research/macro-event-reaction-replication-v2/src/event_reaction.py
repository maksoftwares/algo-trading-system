from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
from scipy import stats


RESEARCH_ROOT = Path(__file__).resolve().parents[2]
COMEX_SOURCE = RESEARCH_ROOT / "comex-futures-foundation-v1" / "src"
if str(COMEX_SOURCE) not in sys.path:
    sys.path.insert(0, str(COMEX_SOURCE))


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


REGIMES = _load_module(
    "macro_event_replication_regimes",
    RESEARCH_ROOT / "balanced-regime-campaign-v3" / "src" / "regimes.py",
)
ENGINE = _load_module(
    "macro_event_replication_metrics",
    RESEARCH_ROOT / "ml-candidate-rankers-v1" / "src" / "engine.py",
)
SPOT = _load_module(
    "macro_event_replication_spot",
    COMEX_SOURCE / "spot_labels.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def event_source_paths(
    config: Mapping[str, Any], storage_root: Path
) -> tuple[Path, Path]:
    source = config["source"]
    root = storage_root / str(source["event_research_relative_root"])
    return (
        root / str(source["bls_calendar_relative_path"]),
        root / str(source["fomc_statements_relative_path"]),
    )


def _event_time(date_text: str, clock: str) -> pd.Timestamp:
    return pd.Timestamp(
        f"{date_text} {clock}:00", tz="America/New_York"
    ).tz_convert("UTC")


def load_event_calendar(
    config: Mapping[str, Any], storage_root: Path
) -> pd.DataFrame:
    bls_path, fomc_directory = event_source_paths(config, storage_root)
    if not bls_path.is_file() or not fomc_directory.is_dir():
        raise FileNotFoundError(
            f"Official event sources are unavailable: {bls_path}, {fomc_directory}"
        )
    start = pd.Timestamp(config["source"]["start_utc"])
    end = pd.Timestamp(config["source"]["end_exclusive_utc"])
    rows: list[dict[str, Any]] = []
    for item in json.loads(bls_path.read_text(encoding="utf-8")):
        title = str(item["title"])
        if title == "Employment Situation":
            event_type = "NFP"
        elif title == "Consumer Price Index":
            event_type = "CPI"
        else:
            continue
        event_time = _event_time(str(item["date"]), "08:30")
        if start <= event_time < end:
            rows.append(
                {
                    "event_id": f"{event_type}_{item['date']}",
                    "event_type": event_type,
                    "event_time_utc": event_time,
                    "event_date": str(item["date"]),
                    "reference": str(item.get("reference", "")),
                    "source_kind": "BLS_OFFICIAL_ARCHIVE",
                    "source_url": str(item["primaryUrl"]),
                    "source_file": str(bls_path),
                    "release_time_rule": "08:30 America/New_York",
                }
            )
    pattern = re.compile(r"monetary(\d{8})a\.html", flags=re.IGNORECASE)
    for statement in sorted(fomc_directory.glob("monetary*a.html")):
        match = pattern.fullmatch(statement.name)
        if match is None:
            continue
        date_text = pd.Timestamp(match.group(1)).date().isoformat()
        event_time = _event_time(date_text, "14:00")
        if start <= event_time < end:
            rows.append(
                {
                    "event_id": f"FOMC_{date_text}",
                    "event_type": "FOMC",
                    "event_time_utc": event_time,
                    "event_date": date_text,
                    "reference": "FOMC statement",
                    "source_kind": "FEDERAL_RESERVE_OFFICIAL_ARCHIVE",
                    "source_url": (
                        "https://www.federalreserve.gov/newsevents/pressreleases/"
                        f"monetary{match.group(1)}a.htm"
                    ),
                    "source_file": str(statement),
                    "release_time_rule": "14:00 America/New_York",
                }
            )
    calendar = pd.DataFrame(rows).sort_values(
        ["event_time_utc", "event_type"], kind="mergesort"
    )
    if calendar.empty:
        raise ValueError("Official event calendar is empty")
    if calendar["event_id"].duplicated().any():
        duplicates = calendar.loc[
            calendar["event_id"].duplicated(False), "event_id"
        ].tolist()
        raise ValueError(f"Duplicate event IDs: {duplicates}")
    expected_types = {str(item["event_type"]) for item in config["policies"]}
    if set(calendar["event_type"]) != expected_types:
        raise ValueError("The official calendar does not cover every policy event type")
    return calendar.reset_index(drop=True)


def _policy_value(policy: Any, name: str) -> Any:
    if isinstance(policy, Mapping):
        return policy[name]
    return getattr(policy, name)


def _body_fraction(row: Any) -> float:
    bar_range = float(row.bid_high) - float(row.bid_low)
    if bar_range <= 0.0:
        return 0.0
    return abs(float(row.bid_close) - float(row.bid_open)) / bar_range


def candidate_for_event_policy(
    event: Any, policy: Any, m5: pd.DataFrame
) -> dict[str, Any] | None:
    event_time = pd.Timestamp(_policy_value(event, "event_time_utc"))
    impulse_minutes = int(_policy_value(policy, "impulse_minutes"))
    range_end = event_time + pd.Timedelta(minutes=impulse_minutes)
    event_bars = m5.loc[
        m5["bar_start_utc"].ge(event_time)
        & m5["bar_start_utc"].lt(range_end)
    ].copy()
    expected_starts = pd.date_range(
        event_time,
        range_end - pd.Timedelta(minutes=5),
        freq="5min",
    )
    if len(event_bars) != len(expected_starts) or not np.array_equal(
        event_bars["bar_start_utc"].to_numpy(), expected_starts.to_numpy()
    ):
        return None
    event_high = float(event_bars["bid_high"].max())
    event_low = float(event_bars["bid_low"].min())
    end_time = event_time + pd.Timedelta(
        minutes=int(_policy_value(policy, "end_minutes"))
    )
    earliest_decision = event_time + pd.Timedelta(
        minutes=int(_policy_value(policy, "start_minutes"))
    )
    signal_bars = m5.loc[
        m5["bar_start_utc"].ge(range_end)
        & m5["bar_end_utc"].ge(earliest_decision)
        & m5["bar_end_utc"].le(end_time)
    ]
    for bar in signal_bars.itertuples(index=False):
        atr = float(bar.atr)
        if not np.isfinite(atr) or atr <= 0.0:
            continue
        body_fraction = _body_fraction(bar)
        if body_fraction < float(_policy_value(policy, "minimum_body_fraction")):
            continue
        break_zone = float(_policy_value(policy, "break_atr")) * atr
        stop_buffer = float(_policy_value(policy, "stop_buffer_atr")) * atr
        open_price = float(bar.bid_open)
        high = float(bar.bid_high)
        low = float(bar.bid_low)
        close = float(bar.bid_close)
        mode = str(_policy_value(policy, "mode"))
        direction = ""
        stop_distance = 0.0
        if mode == "IMPULSE":
            if close >= event_high + break_zone and close > open_price:
                direction = "LONG"
                stop_distance = close - (event_low - stop_buffer)
            elif close <= event_low - break_zone and close < open_price:
                direction = "SHORT"
                stop_distance = (event_high + stop_buffer) - close
        elif mode == "FADE":
            close_inside = event_low <= close <= event_high
            if low <= event_low - break_zone and close_inside and close > open_price:
                direction = "LONG"
                stop_distance = close - (low - stop_buffer)
            elif (
                high >= event_high + break_zone
                and close_inside
                and close < open_price
            ):
                direction = "SHORT"
                stop_distance = (high + stop_buffer) - close
        else:
            raise ValueError(f"Unsupported event-reaction mode: {mode}")
        if not direction or stop_distance <= 0.0:
            continue
        decision = pd.Timestamp(bar.bar_end_utc)
        candidate_text = (
            f"{_policy_value(policy, 'policy_id')}|"
            f"{_policy_value(event, 'event_id')}|{decision.isoformat()}"
        )
        return {
            "candidate_id": hashlib.sha256(
                candidate_text.encode("ascii")
            ).hexdigest(),
            "policy_id": str(_policy_value(policy, "policy_id")),
            "event_id": str(_policy_value(event, "event_id")),
            "event_type": str(_policy_value(event, "event_type")),
            "event_time_utc": event_time,
            "feature_time_utc": decision,
            "feature_lag_minutes": float((decision - event_time).total_seconds() / 60),
            "mode": mode,
            "direction": direction,
            "event_high": event_high,
            "event_low": event_low,
            "signal_open": open_price,
            "signal_high": high,
            "signal_low": low,
            "signal_close": close,
            "signal_atr": atr,
            "signal_body_fraction": body_fraction,
            "raw_stop_distance": stop_distance,
            "target_r": float(_policy_value(policy, "target_r")),
            "source_kind": str(_policy_value(event, "source_kind")),
            "source_url": str(_policy_value(event, "source_url")),
        }
    return None


def build_candidates(
    m5: pd.DataFrame,
    h4: pd.DataFrame,
    base_config: Mapping[str, Any],
    calendar: pd.DataFrame,
    policies: Iterable[Mapping[str, Any]],
) -> pd.DataFrame:
    classified = REGIMES.classify_h4(h4, base_config["regime"])
    classified["timestamp_utc"] = classified["timestamp_utc"].astype(
        "datetime64[ns, UTC]"
    )
    regime_times = classified["timestamp_utc"].astype("int64").to_numpy()
    rows: list[dict[str, Any]] = []
    for policy in policies:
        events = calendar.loc[
            calendar["event_type"].eq(str(policy["event_type"]))
        ]
        for event in events.itertuples(index=False):
            candidate = candidate_for_event_policy(event, policy, m5)
            if candidate is None:
                continue
            decision = pd.Timestamp(candidate["feature_time_utc"])
            regime_index = int(
                np.searchsorted(regime_times, decision.value, side="right") - 1
            )
            candidate["regime"] = (
                "UNAVAILABLE"
                if regime_index < 0
                else str(classified.iloc[regime_index]["regime"])
            )
            candidate["regime_feature_time_utc"] = (
                pd.NaT
                if regime_index < 0
                else classified.iloc[regime_index]["timestamp_utc"]
            )
            rows.append(candidate)
    candidates = pd.DataFrame(rows).sort_values(
        ["feature_time_utc", "policy_id"], kind="mergesort"
    )
    if candidates.empty:
        raise ValueError("Event-reaction candidate generation produced no rows")
    if candidates["candidate_id"].duplicated().any():
        raise ValueError("Event-reaction candidate IDs are not unique")
    if (
        candidates["regime_feature_time_utc"].notna()
        & candidates["regime_feature_time_utc"].gt(
            candidates["feature_time_utc"]
        )
    ).any():
        raise ValueError("Future H4 regime timestamp found in candidate ledger")
    return candidates.reset_index(drop=True)


def _timestamp_ms(value: Any) -> int:
    return int(pd.Timestamp(value).value // 1_000_000)


def _timestamp_series_ms(values: pd.Series) -> np.ndarray:
    timestamps = pd.to_datetime(values, utc=True).dt.as_unit("ms")
    return timestamps.astype("int64").to_numpy()


def _first_quote_after(
    tick_store: Any, decision_ms: int, maximum_delay_ms: int
) -> Any | None:
    for tick in tick_store.ticks_between(
        decision_ms, decision_ms + maximum_delay_ms
    ):
        if int(tick.timestamp_ms) > decision_ms:
            return tick
    return None


def first_threshold_hit(
    ticks: Iterable[Any],
    direction: str,
    stop: float,
    target: float,
    minimum_timestamp_ms: int,
    maximum_timestamp_ms: int,
) -> tuple[Any, float, str] | None:
    for tick in ticks:
        timestamp_ms = int(tick.timestamp_ms)
        if timestamp_ms < minimum_timestamp_ms:
            continue
        if timestamp_ms > maximum_timestamp_ms:
            break
        side = float(tick.bid if direction == "LONG" else tick.ask)
        stop_hit = side <= stop if direction == "LONG" else side >= stop
        target_hit = side >= target if direction == "LONG" else side <= target
        if stop_hit:
            return tick, side, "STOP"
        if target_hit:
            return tick, target, "TARGET"
    return None


def _potential_hit(row: Any, direction: str, stop: float, target: float) -> bool:
    if direction == "LONG":
        return float(row.bid_low) <= stop or float(row.bid_high) >= target
    return float(row.ask_high) >= stop or float(row.ask_low) <= target


def label_candidates(
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
    storage_root: Path,
    symbol: str,
    source: Mapping[str, Any],
    execution: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    foundation = SPOT.load_dukascopy_foundation()
    tick_store = SPOT.VerifiedSpotTickStore(
        storage_root=storage_root, symbol=symbol, foundation=foundation
    )
    if m5.empty:
        raise ValueError("Cannot label event candidates against empty M5 bars")
    starts_ms = _timestamp_series_ms(m5["bar_start_utc"])
    ends_ms = _timestamp_series_ms(m5["bar_end_utc"])
    if np.any(np.diff(starts_ms) < 0) or np.any(ends_ms <= starts_ms):
        raise ValueError("M5 bar timestamps are not ordered valid intervals")
    if not candidates.empty:
        decision_values_ms = _timestamp_series_ms(candidates["feature_time_utc"])
        outside = (decision_values_ms < starts_ms[0]) | (
            decision_values_ms >= ends_ms[-1]
        )
        if bool(outside.any()):
            raise ValueError(
                "Candidate decisions fall outside the M5 epoch-millisecond range"
            )
    rows: list[dict[str, Any]] = []
    rejection_counts: dict[str, int] = {}

    def reject(reason: str) -> None:
        rejection_counts[reason] = rejection_counts.get(reason, 0) + 1

    for number, candidate in enumerate(candidates.itertuples(index=False), start=1):
        decision_ms = _timestamp_ms(candidate.feature_time_utc)
        entry_tick = _first_quote_after(
            tick_store, decision_ms, int(source["maximum_entry_delay_ms"])
        )
        if entry_tick is None:
            reject("NO_TIMELY_ENTRY_QUOTE")
            continue
        direction = str(candidate.direction)
        entry_bid = float(entry_tick.bid)
        entry_ask = float(entry_tick.ask)
        spread = entry_ask - entry_bid
        if spread < 0.0:
            raise ValueError("Crossed quote found at event entry")
        stop_distance = max(
            float(candidate.raw_stop_distance),
            float(execution["minimum_stop_distance_usd"]),
        )
        if stop_distance > float(execution["maximum_stop_distance_usd"]):
            reject("STOP_CEILING_EXCEEDED")
            continue
        if spread > float(execution["maximum_entry_spread_usd"]):
            reject("SPREAD_CEILING_EXCEEDED")
            continue
        if spread / stop_distance > float(execution["maximum_entry_spread_r"]):
            reject("SPREAD_R_EXCEEDED")
            continue
        entry = entry_ask if direction == "LONG" else entry_bid
        stop = (
            entry - stop_distance if direction == "LONG" else entry + stop_distance
        )
        target = (
            entry + float(candidate.target_r) * stop_distance
            if direction == "LONG"
            else entry - float(candidate.target_r) * stop_distance
        )
        entry_ms = int(entry_tick.timestamp_ms)
        deadline_ms = entry_ms + int(execution["maximum_hold_hours"]) * 3_600_000
        start_index = max(
            0, int(np.searchsorted(starts_ms, entry_ms, side="right") - 1)
        )
        end_index = min(
            len(m5), int(np.searchsorted(starts_ms, deadline_ms, side="right"))
        )
        hit: tuple[Any, float, str] | None = None
        for index in range(start_index, end_index):
            bar = m5.iloc[index]
            if not _potential_hit(bar, direction, stop, target):
                continue
            scan_start = max(entry_ms, int(starts_ms[index]))
            scan_end = min(deadline_ms, int(ends_ms[index]))
            ticks = tick_store.ticks_between(scan_start, scan_end)
            hit = first_threshold_hit(
                ticks, direction, stop, target, scan_start, scan_end
            )
            if hit is not None:
                break
        if hit is None:
            grace = int(source["exit_tick_grace_ms"])
            timeout_tick = next(
                (
                    tick
                    for tick in tick_store.ticks_between(
                        deadline_ms, deadline_ms + grace
                    )
                    if int(tick.timestamp_ms) >= deadline_ms
                ),
                None,
            )
            if timeout_tick is None:
                reject("NO_TIMEOUT_QUOTE")
                continue
            exit_tick = timeout_tick
            exit_price = float(
                timeout_tick.bid if direction == "LONG" else timeout_tick.ask
            )
            exit_reason = "MAX_HOLD"
        else:
            exit_tick, exit_price, exit_reason = hit
        sign = 1.0 if direction == "LONG" else -1.0
        risk_usd = stop_distance * float(execution["ounces"])
        gross_pnl = sign * (float(exit_price) - entry) * float(execution["ounces"])
        holding_days = max(
            0.0, (int(exit_tick.timestamp_ms) - entry_ms) / 86_400_000.0
        )
        holding_cost = holding_days * float(execution["holding_cost_per_24h_usd"])
        baseline_net = gross_pnl - float(execution["ticket_cost_usd"]) - holding_cost
        stress_net = baseline_net - risk_usd * float(execution["stress_slippage_r"])
        rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "policy_id": candidate.policy_id,
                "event_id": candidate.event_id,
                "event_type": candidate.event_type,
                "mode": candidate.mode,
                "regime": candidate.regime,
                "direction": direction,
                "signal_time": candidate.feature_time_utc,
                "entry_time": pd.Timestamp(entry_ms, unit="ms", tz="UTC"),
                "exit_time": pd.Timestamp(
                    int(exit_tick.timestamp_ms), unit="ms", tz="UTC"
                ),
                "entry_price": entry,
                "exit_price": float(exit_price),
                "stop": stop,
                "target": target,
                "risk_usd": risk_usd,
                "stop_atr": stop_distance / float(candidate.signal_atr),
                "entry_spread_usd": spread,
                "entry_spread_r": spread / stop_distance,
                "gross_r": gross_pnl / risk_usd,
                "baseline_net_r": baseline_net / risk_usd,
                "stress_net_r": stress_net / risk_usd,
                "holding_minutes": (
                    int(exit_tick.timestamp_ms) - entry_ms
                )
                / 60_000.0,
                "exit_reason": exit_reason,
                "current_account_feasible": risk_usd
                <= float(execution["current_account_risk_usd"]),
            }
        )
        if number % 50 == 0:
            print(f"labeled_event_candidates={number}/{len(candidates)}", flush=True)
    outcomes = pd.DataFrame(rows)
    if not outcomes.empty:
        outcomes = outcomes.sort_values(
            ["entry_time", "policy_id"], kind="mergesort"
        ).reset_index(drop=True)
    audit = {
        "candidate_rows": int(len(candidates)),
        "outcome_rows": int(len(outcomes)),
        "rejection_rows": int(len(candidates) - len(outcomes)),
        "rejection_counts": dict(sorted(rejection_counts.items())),
        "stop_outcomes": int(
            outcomes["exit_reason"].eq("STOP").sum() if not outcomes.empty else 0
        ),
        "target_outcomes": int(
            outcomes["exit_reason"].eq("TARGET").sum() if not outcomes.empty else 0
        ),
        "max_hold_outcomes": int(
            outcomes["exit_reason"].eq("MAX_HOLD").sum()
            if not outcomes.empty
            else 0
        ),
        "raw_tick_threshold_ordering": True,
    }
    return outcomes, audit


def one_sided_trade_pvalue(trades: pd.DataFrame) -> float:
    if len(trades) < 2:
        return 1.0
    values = trades["stress_net_r"].to_numpy(dtype=float)
    if np.std(values, ddof=1) == 0.0:
        return 0.0 if np.mean(values) > 0.0 else 1.0
    result = stats.ttest_1samp(values, 0.0, alternative="greater")
    return float(result.pvalue) if np.isfinite(result.pvalue) else 1.0


def holm_adjust(values: pd.Series) -> pd.Series:
    count = len(values)
    if count == 0:
        return pd.Series(dtype=float, index=values.index)
    raw = values.to_numpy(dtype=float)
    order = np.argsort(raw)
    ranked = raw[order]
    adjusted = np.maximum.accumulate((count - np.arange(count)) * ranked)
    result = np.empty(count, dtype=float)
    result[order] = np.minimum(adjusted, 1.0)
    return pd.Series(result, index=values.index)


def policy_metrics(
    trades: pd.DataFrame,
    event_count: int,
    gate: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, bool]]:
    values = ENGINE.metrics(
        trades, event_count, int(gate["top_winners_removed"])
    )
    yearly = (
        trades.assign(year=trades["entry_time"].dt.year)
        .groupby("year", sort=True)["stress_net_r"]
        .sum()
        if not trades.empty
        else pd.Series(dtype=float)
    )
    values["event_count"] = int(event_count)
    values["event_participation"] = (
        len(trades) / event_count if event_count else 0.0
    )
    values["positive_active_year_share"] = (
        float((yearly > 0.0).mean()) if len(yearly) else 0.0
    )
    engine_gate = dict(gate)
    engine_gate["minimum_trades_per_source_day"] = float(
        gate["minimum_event_participation"]
    )
    base_pass, checks = ENGINE.evaluate_gate(values, engine_gate)
    checks.update(
        {
            "minimum_event_participation": values["event_participation"]
            >= float(gate["minimum_event_participation"]),
            "minimum_positive_active_year_share": values[
                "positive_active_year_share"
            ]
            >= float(gate["minimum_positive_active_year_share"]),
            "minimum_current_account_feasible_share": values[
                "current_account_feasible_share"
            ]
            >= float(gate["minimum_current_account_feasible_share"]),
        }
    )
    return values, {**checks, "quantitative_gate": base_pass and all(checks.values())}
