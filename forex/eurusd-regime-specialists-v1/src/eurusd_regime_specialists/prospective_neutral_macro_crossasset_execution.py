from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from .asymmetric import payoff_metrics
from .prospective_neutral_macro_crossasset_agreement import decide_side
from .research import PACKAGE_ROOT, PIP, sha256_file


CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_prospective_neutral_macro_crossasset_execution_v2.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_EXECUTION_V2_PREREG_2026_07_28.sha256.json"
)
ACTUAL_SEMANTICS = (
    "LINKED_PRE_RELEASE_FORECAST_AND_POST_RELEASE_ACTUAL"
)
MARKET_SEMANTICS = (
    "ONLY_FULLY_COMPLETED_M5_BARS_ENTRY_BAR_EXCLUDED"
)
OWNERSHIP_SEMANTICS = (
    "FROZEN_CLASSIFIER_STATE_FROM_COMPLETED_PRIOR_H1"
)
HEX_64 = re.compile(r"[0-9a-f]{64}")


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("locked_before_prospective_start_and_first_signal")
        is not True
    ):
        raise RuntimeError("Prospective execution V2 is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Prospective execution V2 lock mismatch: {relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent = cfg["parent_strategy"]
    references = (
        ("config_path", "config_sha256"),
        ("decision_source_path", "decision_source_sha256"),
        (
            "preregistration_lock_path",
            "preregistration_lock_sha256",
        ),
    )
    for path_key, hash_key in references:
        if (
            sha256_file(PACKAGE_ROOT / parent[path_key])
            != parent[hash_key]
        ):
            raise RuntimeError(f"Parent strategy drift: {path_key}")
    market = cfg["market_capture_reference"]
    if sha256_file(PACKAGE_ROOT / market["path"]) != market["sha256"]:
        raise RuntimeError("Prospective market capture source drift")
    return checked


def _utc(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("All operational timestamps must be timezone-aware")
    return timestamp.tz_convert("UTC").as_unit("ns")


def _required(row: Mapping[str, Any], name: str) -> Any:
    if name not in row or row[name] is None:
        raise ValueError(f"Missing required evidence field: {name}")
    return row[name]


def _finite(row: Mapping[str, Any], name: str) -> float:
    value = float(_required(row, name))
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _hash(row: Mapping[str, Any], name: str) -> str:
    value = str(_required(row, name)).lower()
    if HEX_64.fullmatch(value) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256")
    return value


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        {
            str(key): (
                value.isoformat()
                if isinstance(value, pd.Timestamp)
                else value
            )
            for key, value in payload.items()
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_neutral_ownership_record(
    *,
    eligible_date: Any,
    state_timestamp_utc: Any,
    ownership_observed_at_utc: Any,
    direction: str,
    shock: bool,
    dxy_compressed: bool,
    eurusd_compressed: bool,
    source_hashes: Mapping[str, str],
) -> dict[str, Any]:
    """Freeze the parent classifier's prior-date 23:00 H1 state."""
    day = _utc(eligible_date).floor("D")
    state_time = _utc(state_timestamp_utc)
    observed = _utc(ownership_observed_at_utc)
    expected_state = day - pd.Timedelta(hours=1)
    if state_time != expected_state:
        raise ValueError(
            "Neutral ownership must use the prior-date 23:00 H1 state"
        )
    if observed < day:
        raise ValueError("Ownership cannot be observed before state completion")
    required_symbols = {
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "DOLLARIDXUSD",
        "USTBONDTRUSD",
    }
    if set(source_hashes) != required_symbols:
        raise ValueError("Ownership evidence requires all five source hashes")
    normalized_hashes = {
        symbol: str(value).lower()
        for symbol, value in source_hashes.items()
    }
    if any(
        HEX_64.fullmatch(value) is None
        for value in normalized_hashes.values()
    ):
        raise ValueError("Ownership source hash is not a SHA-256")
    is_neutral = bool(
        str(direction) == "NEUTRAL"
        and not bool(shock)
        and not (bool(dxy_compressed) and bool(eurusd_compressed))
    )
    core = {
        "eligible_date": day.strftime("%Y-%m-%d"),
        "state_timestamp_utc": state_time,
        "neutral_known_at_utc": day,
        "ownership_observed_at_utc": observed,
        "direction": str(direction),
        "shock": bool(shock),
        "dxy_compressed": bool(dxy_compressed),
        "eurusd_compressed": bool(eurusd_compressed),
        "is_neutral": is_neutral,
        "source_hashes": normalized_hashes,
        "capture_semantics": OWNERSHIP_SEMANTICS,
    }
    return {
        **core,
        "ownership_evidence_sha256": _canonical_hash(core),
    }


def verify_neutral_ownership_record(
    ownership: Mapping[str, Any],
) -> None:
    source_hashes = _required(ownership, "source_hashes")
    if not isinstance(source_hashes, Mapping):
        raise TypeError("Ownership source hashes must be a mapping")
    direction = str(_required(ownership, "direction"))
    shock = bool(_required(ownership, "shock"))
    dxy_compressed = bool(_required(ownership, "dxy_compressed"))
    eurusd_compressed = bool(
        _required(ownership, "eurusd_compressed")
    )
    expected_neutral = bool(
        direction == "NEUTRAL"
        and not shock
        and not (dxy_compressed and eurusd_compressed)
    )
    if bool(_required(ownership, "is_neutral")) != expected_neutral:
        raise ValueError("Neutral ownership flag was altered")
    normalized_hashes = {
        str(symbol): str(value).lower()
        for symbol, value in source_hashes.items()
    }
    if set(normalized_hashes) != {
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "DOLLARIDXUSD",
        "USTBONDTRUSD",
    } or any(
        HEX_64.fullmatch(value) is None
        for value in normalized_hashes.values()
    ):
        raise ValueError("Neutral ownership source hashes are invalid")
    core = {
        "eligible_date": str(
            _required(ownership, "eligible_date")
        ),
        "state_timestamp_utc": _utc(
            _required(ownership, "state_timestamp_utc")
        ),
        "neutral_known_at_utc": _utc(
            _required(ownership, "neutral_known_at_utc")
        ),
        "ownership_observed_at_utc": _utc(
            _required(ownership, "ownership_observed_at_utc")
        ),
        "direction": direction,
        "shock": shock,
        "dxy_compressed": dxy_compressed,
        "eurusd_compressed": eurusd_compressed,
        "is_neutral": expected_neutral,
        "source_hashes": normalized_hashes,
        "capture_semantics": str(
            _required(ownership, "capture_semantics")
        ),
    }
    if _hash(
        ownership, "ownership_evidence_sha256"
    ) != _canonical_hash(core):
        raise ValueError("Neutral ownership evidence hash mismatch")


def build_signal_record(
    actual: Mapping[str, Any],
    market: Mapping[str, Any],
    ownership: Mapping[str, Any],
) -> dict[str, Any]:
    """Link immutable evidence and emit one causal signal or CASH row."""
    if _required(actual, "capture_semantics") != ACTUAL_SEMANTICS:
        raise ValueError("Actual evidence semantics are not admissible")
    if _required(market, "capture_semantics") != MARKET_SEMANTICS:
        raise ValueError("Market evidence semantics are not admissible")
    if _required(ownership, "capture_semantics") != OWNERSHIP_SEMANTICS:
        raise ValueError("Ownership evidence semantics are not admissible")
    verify_neutral_ownership_record(ownership)

    event = _utc(_required(actual, "event_time_utc"))
    if event < _utc(load_config()["prospective_start_utc"]):
        raise ValueError("Event precedes the frozen prospective start")
    if _utc(_required(market, "event_time_utc")) != event:
        raise ValueError("Actual and market event timestamps do not match")
    if str(_required(ownership, "eligible_date")) != event.strftime(
        "%Y-%m-%d"
    ):
        raise ValueError("Neutral ownership date does not match event date")

    forecast_observed = _utc(
        _required(actual, "forecast_observed_at_utc")
    )
    actual_observed = _utc(
        _required(actual, "actual_observed_at_utc")
    )
    observation_completed = _utc(
        _required(market, "observation_completed_at_utc")
    )
    observation_start = _utc(
        _required(market, "observation_start_utc")
    )
    if observation_start != event.ceil("5min"):
        raise ValueError("Market observation does not start causally")
    if observation_completed != observation_start + pd.Timedelta(
        minutes=15
    ):
        raise ValueError("Market observation is not exactly three M5 bars")
    market_observed = _utc(
        _required(market, "market_observed_at_utc")
    )
    ownership_observed = _utc(
        _required(ownership, "ownership_observed_at_utc")
    )
    neutral_known = _utc(
        _required(ownership, "neutral_known_at_utc")
    )
    state_time = _utc(
        _required(ownership, "state_timestamp_utc")
    )
    if state_time != event.floor("D") - pd.Timedelta(hours=1):
        raise ValueError("Ownership state is not the frozen prior H1 bar")
    if neutral_known != event.floor("D"):
        raise ValueError("Neutral logical availability is not UTC midnight")
    if market_observed < observation_completed + pd.Timedelta(
        seconds=60
    ):
        raise ValueError("Market evidence lacks the 60-second capture lag")
    evidence_ready = max(
        actual_observed,
        market_observed,
        ownership_observed,
        observation_completed,
    )
    entry_time = evidence_ready.floor("5min") + pd.Timedelta(minutes=5)
    if entry_time.floor("D") != event.floor("D"):
        raise ValueError("Evidence-ready entry crosses the event UTC date")

    forecast = _finite(actual, "forecast_value")
    actual_value = _finite(actual, "actual_value")
    recorded_surprise = _finite(actual, "surprise_value")
    if not math.isclose(
        actual_value - forecast,
        recorded_surprise,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError("Recorded surprise does not match actual-forecast")
    expected_macro_side = (
        "SHORT"
        if recorded_surprise > 0
        else ("LONG" if recorded_surprise < 0 else "CASH")
    )
    if str(_required(actual, "macro_side")) != expected_macro_side:
        raise ValueError("Captured macro side disagrees with frozen rule")

    signal = decide_side(
        family=str(_required(actual, "family")),
        is_neutral=bool(_required(ownership, "is_neutral")),
        neutral_known_at_utc=neutral_known,
        event_time_utc=event,
        forecast_observed_at_utc=forecast_observed,
        actual_observed_at_utc=actual_observed,
        observation_completed_at_utc=observation_completed,
        entry_time_utc=entry_time,
        forecast_value=forecast,
        actual_value=actual_value,
        eurusd_pre_mid=_finite(market, "eurusd_pre_mid"),
        eurusd_post_mid=_finite(market, "eurusd_post_mid"),
        dxy_pre_mid=_finite(market, "dxy_pre_mid"),
        dxy_post_mid=_finite(market, "dxy_post_mid"),
        treasury_pre_mid=_finite(market, "treasury_pre_mid"),
        treasury_post_mid=_finite(market, "treasury_post_mid"),
    )
    evidence_hashes = {
        "forecast_raw_snapshot_sha256": _hash(
            actual, "forecast_raw_snapshot_sha256"
        ),
        "actual_raw_snapshot_sha256": _hash(
            actual, "actual_raw_snapshot_sha256"
        ),
        "market_manifest_sha256": _hash(
            market, "market_manifest_sha256"
        ),
        "market_snapshot_sha256": _hash(
            market, "market_snapshot_sha256"
        ),
        "ownership_evidence_sha256": _hash(
            ownership, "ownership_evidence_sha256"
        ),
    }
    identity = {
        "tradingview_event_id": str(
            _required(actual, "tradingview_event_id")
        ),
        "tradingview_ticker": str(
            _required(actual, "tradingview_ticker")
        ),
        "event_time_utc": event,
        **evidence_hashes,
    }
    return {
        "signal_id": _canonical_hash(identity),
        "campaign_id": (
            "eurusd-neutral-prospective-macro-crossasset-agreement-v2"
        ),
        "family": str(_required(actual, "family")),
        "tradingview_event_id": identity["tradingview_event_id"],
        "tradingview_ticker": identity["tradingview_ticker"],
        "event_time_utc": event,
        "forecast_observed_at_utc": forecast_observed,
        "actual_observed_at_utc": actual_observed,
        "observation_completed_at_utc": observation_completed,
        "market_observed_at_utc": market_observed,
        "ownership_observed_at_utc": ownership_observed,
        "evidence_ready_at_utc": evidence_ready,
        "entry_time_utc": entry_time,
        "eurusd_observation_mid_high": _finite(
            market, "eurusd_observation_mid_high"
        ),
        "eurusd_observation_mid_low": _finite(
            market, "eurusd_observation_mid_low"
        ),
        **evidence_hashes,
        **signal,
        "broker_action_allowed": False,
    }


def build_signal_ledger(
    actuals: pd.DataFrame,
    markets: pd.DataFrame,
    ownerships: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Select earliest admissible append-only evidence without revisions."""
    if actuals.empty:
        return pd.DataFrame(), {
            "linked_actual_rows": 0,
            "selected_actual_events": 0,
            "complete_market_events": 0,
            "ownership_dates": 0,
            "signals": 0,
            "cash_rows": 0,
            "missing_market": 0,
            "missing_ownership": 0,
        }
    actual = actuals.copy()
    market = markets.copy()
    ownership = ownerships.copy()
    actual["event_time_utc"] = pd.to_datetime(
        actual["event_time_utc"], utc=True
    ).dt.as_unit("ns")
    actual["actual_observed_at_utc"] = pd.to_datetime(
        actual["actual_observed_at_utc"], utc=True
    ).dt.as_unit("ns")
    key = [
        "tradingview_event_id",
        "tradingview_ticker",
        "event_time_utc",
    ]
    selected_actual = (
        actual.sort_values([*key, "actual_observed_at_utc"])
        .drop_duplicates(key, keep="first")
        .reset_index(drop=True)
    )
    if market.empty:
        selected_market = market.copy()
    else:
        market["event_time_utc"] = pd.to_datetime(
            market["event_time_utc"], utc=True
        ).dt.as_unit("ns")
        market["market_observed_at_utc"] = pd.to_datetime(
            market["market_observed_at_utc"], utc=True
        ).dt.as_unit("ns")
        selected_market = (
            market[
                market["capture_semantics"].eq(MARKET_SEMANTICS)
            ]
            .sort_values(
                ["event_time_utc", "market_observed_at_utc"]
            )
            .drop_duplicates("event_time_utc", keep="first")
            .set_index("event_time_utc", drop=False)
        )
    if ownership.empty:
        selected_ownership = ownership.copy()
    else:
        ownership["ownership_observed_at_utc"] = pd.to_datetime(
            ownership["ownership_observed_at_utc"], utc=True
        ).dt.as_unit("ns")
        selected_ownership = (
            ownership[
                ownership["capture_semantics"].eq(
                    OWNERSHIP_SEMANTICS
                )
            ]
            .sort_values(
                ["eligible_date", "ownership_observed_at_utc"]
            )
            .drop_duplicates("eligible_date", keep="first")
            .set_index("eligible_date", drop=False)
        )
    records: list[dict[str, Any]] = []
    missing_market = 0
    missing_ownership = 0
    for row in selected_actual.to_dict(orient="records"):
        event = _utc(row["event_time_utc"])
        date = event.strftime("%Y-%m-%d")
        if (
            selected_market.empty
            or event not in selected_market.index
        ):
            missing_market += 1
            continue
        if (
            selected_ownership.empty
            or date not in selected_ownership.index
        ):
            missing_ownership += 1
            continue
        records.append(
            build_signal_record(
                row,
                selected_market.loc[event].to_dict(),
                selected_ownership.loc[date].to_dict(),
            )
        )
    signals = pd.DataFrame(records)
    if not signals.empty:
        signals = signals.sort_values(
            ["entry_time_utc", "signal_id"]
        ).reset_index(drop=True)
    return signals, {
        "linked_actual_rows": int(len(actual)),
        "selected_actual_events": int(len(selected_actual)),
        "complete_market_events": int(len(selected_market)),
        "ownership_dates": int(len(selected_ownership)),
        "signals": int(len(signals)),
        "cash_rows": int(signals["side"].eq("CASH").sum())
        if len(signals)
        else 0,
        "missing_market": int(missing_market),
        "missing_ownership": int(missing_ownership),
    }


def _normalize_m5(m5: pd.DataFrame) -> pd.DataFrame:
    frame = m5.copy()
    if "timestamp_utc" in frame.columns:
        timestamps = pd.to_datetime(
            frame.pop("timestamp_utc"), utc=True
        ).dt.as_unit("ns")
        frame.index = pd.DatetimeIndex(
            timestamps, name="timestamp_utc"
        )
    else:
        if not isinstance(frame.index, pd.DatetimeIndex):
            raise ValueError("M5 path requires a UTC DatetimeIndex")
        if frame.index.tz is None:
            raise ValueError("M5 path index must be timezone-aware")
        frame.index = frame.index.tz_convert("UTC").as_unit("ns")
    required = {
        f"{side}_{field}"
        for side in ("bid", "ask")
        for field in ("open", "high", "low", "close")
    }
    if not required.issubset(frame.columns):
        raise ValueError("M5 path lacks executable bid/ask OHLC")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError("M5 path timestamps must be unique and ordered")
    values = frame[list(required)].astype(float)
    if not np.isfinite(values.to_numpy()).all():
        raise ValueError("M5 path contains non-finite prices")
    if (
        (frame["ask_open"] < frame["bid_open"]).any()
        or (frame["ask_close"] < frame["bid_close"]).any()
    ):
        raise ValueError("M5 path contains crossed executable quotes")
    return frame


def _effective_prices(
    bar: pd.Series,
    spread_floor: float,
) -> dict[str, float]:
    return {
        "bid_open": min(
            float(bar["bid_open"]),
            float(bar["ask_open"]) - spread_floor,
        ),
        "bid_high": min(
            float(bar["bid_high"]),
            float(bar["ask_high"]) - spread_floor,
        ),
        "bid_low": min(
            float(bar["bid_low"]),
            float(bar["ask_low"]) - spread_floor,
        ),
        "bid_close": min(
            float(bar["bid_close"]),
            float(bar["ask_close"]) - spread_floor,
        ),
        "ask_open": max(
            float(bar["ask_open"]),
            float(bar["bid_open"]) + spread_floor,
        ),
        "ask_high": max(
            float(bar["ask_high"]),
            float(bar["bid_high"]) + spread_floor,
        ),
        "ask_low": max(
            float(bar["ask_low"]),
            float(bar["bid_low"]) + spread_floor,
        ),
        "ask_close": max(
            float(bar["ask_close"]),
            float(bar["bid_close"]) + spread_floor,
        ),
    }


def execute_signal(
    signal: Mapping[str, Any],
    m5: pd.DataFrame,
    *,
    path_evidence_sha256: str,
) -> dict[str, Any]:
    """Evaluate one frozen signal on append-only completed M5 evidence."""
    path_hash = str(path_evidence_sha256).lower()
    if HEX_64.fullmatch(path_hash) is None:
        raise ValueError("Path evidence hash must be a SHA-256")
    side = str(_required(signal, "side"))
    base = {
        "signal_id": str(_required(signal, "signal_id")),
        "event_time_utc": _utc(_required(signal, "event_time_utc")),
        "entry_time_utc": _utc(_required(signal, "entry_time_utc")),
        "side": side,
        "path_evidence_sha256": path_hash,
        "broker_action_allowed": False,
    }
    if side == "CASH":
        return {
            **base,
            "status": "CASH_NO_TRADE",
            "exit_reason": str(_required(signal, "reason")),
        }
    if side not in {"LONG", "SHORT"}:
        raise ValueError(f"Unsupported signal side: {side}")
    evidence_ready = _utc(
        _required(signal, "evidence_ready_at_utc")
    )
    expected_entry = evidence_ready.floor("5min") + pd.Timedelta(
        minutes=5
    )
    if base["entry_time_utc"] != expected_entry:
        raise ValueError("Signal entry is not strictly after evidence")

    cfg = load_config()
    risk_cfg = cfg["risk"]
    entry_cfg = cfg["entry"]
    spread_floor = (
        float(entry_cfg["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(entry_cfg["adverse_slippage_pips_per_side"]) * PIP
    )
    frame = _normalize_m5(m5)
    entry_time = base["entry_time_utc"]
    deadline = entry_time + pd.Timedelta(
        hours=float(risk_cfg["maximum_hold_hours"])
    )
    expected = pd.date_range(
        entry_time,
        deadline - pd.Timedelta(minutes=5),
        freq="5min",
    )
    if entry_time not in frame.index:
        return {
            **base,
            "status": "PENDING_INCOMPLETE_PATH",
            "missing_timestamp_utc": entry_time,
        }

    entry_quotes = _effective_prices(
        frame.loc[entry_time], spread_floor
    )
    if side == "LONG":
        entry_price = entry_quotes["ask_open"] + slippage
        observation_low = float(
            _required(signal, "eurusd_observation_mid_low")
        )
        observation_high = float(
            _required(signal, "eurusd_observation_mid_high")
        )
        if observation_high < observation_low:
            raise ValueError("EURUSD observation extremes are inverted")
        structural_stop = (
            observation_low
            - float(risk_cfg["stop_buffer_pips"]) * PIP
        )
        raw_risk_pips = (entry_price - structural_stop) / PIP
    else:
        entry_price = entry_quotes["bid_open"] - slippage
        observation_low = float(
            _required(signal, "eurusd_observation_mid_low")
        )
        observation_high = float(
            _required(signal, "eurusd_observation_mid_high")
        )
        if observation_high < observation_low:
            raise ValueError("EURUSD observation extremes are inverted")
        structural_stop = (
            observation_high
            + float(risk_cfg["stop_buffer_pips"]) * PIP
        )
        raw_risk_pips = (structural_stop - entry_price) / PIP
    risk_pips = min(
        max(
            raw_risk_pips,
            float(risk_cfg["minimum_risk_pips"]),
        ),
        float(risk_cfg["maximum_risk_pips"]),
    )
    risk_distance = risk_pips * PIP
    stop_adjustment = (
        "FLOOR"
        if raw_risk_pips < float(risk_cfg["minimum_risk_pips"])
        else (
            "CEILING"
            if raw_risk_pips
            > float(risk_cfg["maximum_risk_pips"])
            else "NONE"
        )
    )
    target_r = float(risk_cfg["target_r"])
    if side == "LONG":
        stop = entry_price - risk_distance
        target = entry_price + target_r * risk_distance
    else:
        stop = entry_price + risk_distance
        target = entry_price - target_r * risk_distance

    common = {
        **base,
        "entry_price": entry_price,
        "structural_stop_price": structural_stop,
        "raw_structural_risk_pips": raw_risk_pips,
        "risk_pips": risk_pips,
        "risk_distance": risk_distance,
        "stop_adjustment": stop_adjustment,
        "stop_price": stop,
        "target_price": target,
        "deadline_utc": deadline,
    }
    for timestamp in expected:
        if timestamp not in frame.index:
            return {
                **common,
                "status": "PENDING_INCOMPLETE_PATH",
                "missing_timestamp_utc": timestamp,
            }
        prices = _effective_prices(
            frame.loc[timestamp], spread_floor
        )
        if side == "LONG":
            if prices["bid_low"] <= stop:
                exit_price = min(prices["bid_open"], stop) - slippage
                reason = "STOP"
            elif prices["bid_high"] >= target:
                exit_price = max(prices["bid_open"], target) - slippage
                reason = "TARGET"
            else:
                continue
        else:
            if prices["ask_high"] >= stop:
                exit_price = max(prices["ask_open"], stop) + slippage
                reason = "STOP"
            elif prices["ask_low"] <= target:
                exit_price = min(prices["ask_open"], target) + slippage
                reason = "TARGET"
            else:
                continue
        signed_move = (
            exit_price - entry_price
            if side == "LONG"
            else entry_price - exit_price
        )
        outcome_r = signed_move / risk_distance
        return {
            **common,
            "status": "CLOSED",
            "exit_time_utc": timestamp,
            "exit_price": exit_price,
            "exit_reason": reason,
            "r": outcome_r,
            "extra_half_pip_stress_r": (
                outcome_r
                - float(risk_cfg["extra_round_trip_stress_pips"])
                / risk_pips
            ),
            "fixed_0p01_lot_usd": signed_move / PIP * 0.10,
        }

    final_time = expected[-1]
    final_prices = _effective_prices(
        frame.loc[final_time], spread_floor
    )
    exit_price = (
        final_prices["bid_close"] - slippage
        if side == "LONG"
        else final_prices["ask_close"] + slippage
    )
    signed_move = (
        exit_price - entry_price
        if side == "LONG"
        else entry_price - exit_price
    )
    outcome_r = signed_move / risk_distance
    return {
        **common,
        "status": "CLOSED",
        "exit_time_utc": deadline,
        "exit_price": exit_price,
        "exit_reason": "TIME_12H",
        "r": outcome_r,
        "extra_half_pip_stress_r": (
            outcome_r
            - float(risk_cfg["extra_round_trip_stress_pips"])
            / risk_pips
        ),
        "fixed_0p01_lot_usd": signed_move / PIP * 0.10,
    }


def route_signals(
    signals: pd.DataFrame,
    m5: pd.DataFrame,
    *,
    path_evidence_sha256: str,
) -> pd.DataFrame:
    """Apply the frozen one-position rule without resolving unknown paths."""
    records: list[dict[str, Any]] = []
    open_until: pd.Timestamp | None = None
    unresolved = False
    for row in signals.sort_values(
        ["entry_time_utc", "signal_id"]
    ).to_dict(orient="records"):
        if str(row["side"]) == "CASH":
            records.append(
                execute_signal(
                    row,
                    m5,
                    path_evidence_sha256=path_evidence_sha256,
                )
            )
            continue
        entry = _utc(row["entry_time_utc"])
        if unresolved:
            records.append(
                {
                    "signal_id": row["signal_id"],
                    "event_time_utc": _utc(row["event_time_utc"]),
                    "entry_time_utc": entry,
                    "side": row["side"],
                    "status": "BLOCKED_PRIOR_POSITION_OUTCOME_PENDING",
                    "broker_action_allowed": False,
                }
            )
            continue
        if open_until is not None and entry <= open_until:
            records.append(
                {
                    "signal_id": row["signal_id"],
                    "event_time_utc": _utc(row["event_time_utc"]),
                    "entry_time_utc": entry,
                    "side": row["side"],
                    "status": "SKIPPED_POSITION_ALREADY_OPEN",
                    "broker_action_allowed": False,
                }
            )
            continue
        result = execute_signal(
            row,
            m5,
            path_evidence_sha256=path_evidence_sha256,
        )
        records.append(result)
        if result["status"] == "PENDING_INCOMPLETE_PATH":
            unresolved = True
        elif result["status"] == "CLOSED":
            open_until = _utc(result["exit_time_utc"])
    return pd.DataFrame(records)


def attach_oracle_precision_labels(
    trades: pd.DataFrame,
    oracle: pd.DataFrame,
    *,
    evaluated_at_utc: Any,
) -> pd.DataFrame:
    """Attach evaluation-only same-day/same-side labels after closure."""
    result = trades.copy()
    if result.empty:
        result["oracle_same_day_same_side"] = pd.Series(dtype=bool)
        return result
    required = {
        "entry_time_utc",
        "side",
        "regime",
        "oracle_label_known_time_utc",
    }
    if not required.issubset(oracle.columns):
        raise ValueError("Prospective oracle ledger lacks safe label fields")
    evaluated = _utc(evaluated_at_utc)
    reference = oracle.copy()
    for column in ("entry_time_utc", "oracle_label_known_time_utc"):
        reference[column] = pd.to_datetime(
            reference[column], utc=True
        ).dt.as_unit("ns")
    if reference["oracle_label_known_time_utc"].gt(evaluated).any():
        raise ValueError("Oracle label was not known by evaluation time")
    reference = reference[reference["regime"].eq("NEUTRAL")].copy()
    keys = set(
        zip(
            reference["entry_time_utc"].dt.date,
            reference["side"].astype(str),
            strict=True,
        )
    )
    result["entry_time_utc"] = pd.to_datetime(
        result["entry_time_utc"], utc=True
    ).dt.as_unit("ns")
    result["oracle_same_day_same_side"] = [
        (timestamp.date(), str(side)) in keys
        for timestamp, side in zip(
            result["entry_time_utc"],
            result["side"],
            strict=True,
        )
    ]
    return result


def _metrics(frame: pd.DataFrame, column: str = "r") -> dict[str, Any]:
    return payoff_metrics(frame, column)


def evaluate_admission(
    routed: pd.DataFrame,
    *,
    evaluated_at_utc: Any,
) -> dict[str, Any]:
    """Evaluate only the immutable prospective ledger; never historical P&L."""
    cfg = load_config()
    gate = cfg["prospective_admission"]
    start = _utc(cfg["prospective_start_utc"])
    evaluated = _utc(evaluated_at_utc)
    before_start = evaluated < start
    closed = routed[routed["status"].eq("CLOSED")].copy()
    if not closed.empty:
        if before_start:
            raise ValueError(
                "Closed trade exists before prospective start"
            )
        if closed["signal_id"].duplicated().any():
            raise ValueError("Duplicate signal entered prospective ledger")
        closed["entry_time_utc"] = pd.to_datetime(
            closed["entry_time_utc"], utc=True
        ).dt.as_unit("ns")
        closed["exit_time_utc"] = pd.to_datetime(
            closed["exit_time_utc"], utc=True
        ).dt.as_unit("ns")
        if closed["entry_time_utc"].lt(start).any():
            raise ValueError("Pre-start trade entered prospective ledger")
        if closed["exit_time_utc"].gt(evaluated).any():
            raise ValueError("Unclosed future trade entered evaluation")
        if "path_evidence_sha256" in closed.columns and any(
            HEX_64.fullmatch(str(value).lower()) is None
            for value in closed["path_evidence_sha256"]
        ):
            raise ValueError("Closed trade lacks valid path evidence hash")
        closed = closed.sort_values("exit_time_utc").reset_index(drop=True)
    overall = _metrics(closed)
    sides = {
        side: _metrics(closed[closed["side"].eq(side)])
        for side in ("LONG", "SHORT")
    }
    remove_count = (
        int(math.ceil(len(closed) * 0.05)) if len(closed) else 0
    )
    top_removed_frame = (
        closed.sort_values("r").iloc[:-remove_count].copy()
        if remove_count
        else closed.copy()
    )
    top_removed = _metrics(top_removed_frame)
    stressed = _metrics(closed, "extra_half_pip_stress_r")
    elapsed = evaluated >= start + pd.DateOffset(
        months=int(gate["minimum_calendar_months"])
    )
    sample = len(closed) >= int(gate["minimum_executed_trades"])
    oracle_complete = bool(
        len(closed)
        and "oracle_same_day_same_side" in closed.columns
        and closed["oracle_same_day_same_side"].notna().all()
    )
    oracle_precision = (
        float(closed["oracle_same_day_same_side"].astype(bool).mean())
        if oracle_complete
        else None
    )
    checks = {
        "minimum_calendar_months": bool(elapsed),
        "minimum_executed_trades": bool(sample),
        "win_rate": bool(
            float(gate["minimum_overall_win_rate"])
            <= overall["win_rate"]
            <= float(gate["maximum_overall_win_rate"])
        ),
        "payoff": bool(
            float(gate["minimum_overall_realized_payoff_ratio"])
            <= overall["realized_payoff_ratio"]
            <= float(gate["maximum_overall_realized_payoff_ratio"])
        ),
        "profit_factor": bool(
            overall["profit_factor"]
            >= float(gate["minimum_overall_profit_factor"])
        ),
        "both_sides": bool(
            all(
                sides[side]["trades"]
                >= int(gate["minimum_each_side_trades"])
                and sides[side]["profit_factor"]
                >= float(gate["minimum_each_side_profit_factor"])
                for side in ("LONG", "SHORT")
            )
        ),
        "drawdown": bool(
            overall["max_drawdown_r"]
            <= float(gate["maximum_drawdown_r"])
        ),
        "top_5pct_winner_removal": bool(
            top_removed["profit_factor"]
            >= float(
                gate["minimum_top_5pct_removed_profit_factor"]
            )
        ),
        "extra_half_pip": bool(
            stressed["profit_factor"]
            >= float(gate["minimum_extra_half_pip_profit_factor"])
        ),
        "oracle_precision": bool(
            oracle_precision is not None
            and oracle_precision
            >= float(
                gate["minimum_same_day_same_side_oracle_precision"]
            )
        ),
    }
    review_allowed = bool(all(checks.values()))
    if before_start:
        status = "WAITING_FOR_PROSPECTIVE_START"
    elif review_allowed:
        status = "RESEARCH_REVIEW_REQUIRED"
    elif not elapsed or not sample:
        status = "ACCUMULATING_PROSPECTIVE_EVIDENCE"
    else:
        status = "REJECTED_WITHOUT_RETUNING"
    return {
        "schema_version": "eurusd_neutral_prospective_admission_v2",
        "status": status,
        "prospective_start_utc": start,
        "evaluated_at_utc": evaluated,
        "historical_pnl_loaded": False,
        "closed_trades": int(len(closed)),
        "overall": overall,
        "by_side": sides,
        "top_5pct_winners_removed": top_removed,
        "extra_half_pip_round_trip": stressed,
        "oracle_same_day_same_side_precision": oracle_precision,
        "gate_results": checks,
        "research_review_allowed": review_allowed,
        "broker_action_allowed": False,
    }


__all__ = [
    "CONFIG_PATH",
    "LOCK_PATH",
    "attach_oracle_precision_labels",
    "build_neutral_ownership_record",
    "build_signal_ledger",
    "build_signal_record",
    "evaluate_admission",
    "execute_signal",
    "load_config",
    "route_signals",
    "verify_lock",
    "verify_neutral_ownership_record",
]
