from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


SCHEMA_VERSION = "xau_specialist_shadow_v1"
SPECIALIST_ID = "R1_UPTREND_LONG_V1"
EXPECTED_LOGIN = 1033669
EXPECTED_SERVER_MARKER = "Demo"
SYMBOL = "XAUUSD"
DEFAULT_TERMINAL = Path("C:/MT5PortableProspectiveCollector/terminal64.exe")
DEFAULT_RUNTIME = Path("C:/MT5PortableProspectiveCollector/MQL5/Files/specialist_shadow_v1")
HISTORY_DAYS = 1_200
POLL_SECONDS = 60


@dataclass(frozen=True)
class FrozenR1:
    module: Any
    config: dict[str, Any]
    contract_hash: str


def utc_text(value: pd.Timestamp | datetime) -> str:
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize("UTC")
    else:
        stamp = stamp.tz_convert("UTC")
    return stamp.isoformat().replace("+00:00", "Z")


def load_frozen_r1(repo_root: Path) -> FrozenR1:
    research = repo_root / "xau-usd" / "xauusd-fast-research"
    module_path = research / "mt5-r1-uptrend-portability-v1" / "src" / "portability.py"
    base_path = research / "mt5-compression-portability-v1" / "src" / "portability.py"
    config_path = (
        research
        / "mt5-r1-uptrend-portability-v1"
        / "config"
        / "mt5_r1_uptrend_portability_v1.json"
    )
    for path in (module_path, base_path, config_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    digest = hashlib.sha256()
    for path in (base_path, module_path, config_path):
        digest.update(path.read_bytes())
    contract_hash = digest.hexdigest()

    name = f"xau_r1_shadow_{contract_hash[:12]}"
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load frozen R1 module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return FrozenR1(module, json.loads(config_path.read_text(encoding="utf-8")), contract_hash)


def last_completed_h4(now_utc: datetime | pd.Timestamp) -> pd.Timestamp:
    now = pd.Timestamp(now_utc)
    if now.tzinfo is None:
        now = now.tz_localize("UTC")
    else:
        now = now.tz_convert("UTC")
    return now.floor("4h")


def mt5_rates_to_m5(
    rates: Any,
    *,
    point_size: float,
    completed_through: pd.Timestamp,
) -> pd.DataFrame:
    frame = pd.DataFrame(rates)
    required = {"time", "open", "high", "low", "close", "spread"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"MT5 M5 rates are missing columns: {missing}")
    if frame.empty:
        raise ValueError("MT5 returned no M5 rates")

    frame["bar_start_utc"] = pd.to_datetime(frame["time"], unit="s", utc=True)
    frame["bar_end_utc"] = frame["bar_start_utc"] + pd.Timedelta(minutes=5)
    frame = frame.loc[frame["bar_end_utc"] <= completed_through].copy()
    frame = frame.sort_values("bar_start_utc").drop_duplicates("bar_start_utc", keep="last")
    if frame.empty:
        raise ValueError("MT5 returned no completed M5 rates")

    spread = frame["spread"].astype(float) * float(point_size)
    for field in ("open", "high", "low", "close"):
        frame[f"bid_{field}"] = frame[field].astype(float)
        frame[f"ask_{field}"] = frame[field].astype(float) + spread
        frame[f"mid_{field}"] = frame[field].astype(float) + spread / 2.0
    frame["timestamp_utc"] = frame["bar_end_utc"]
    return frame[
        [
            "bar_start_utc",
            "bar_end_utc",
            "timestamp_utc",
            "bid_open",
            "bid_high",
            "bid_low",
            "bid_close",
            "ask_open",
            "ask_high",
            "ask_low",
            "ask_close",
            "mid_open",
            "mid_high",
            "mid_low",
            "mid_close",
        ]
    ].reset_index(drop=True)


def evaluate_r1(
    m5: pd.DataFrame,
    frozen: FrozenR1,
    *,
    completed_through: pd.Timestamp,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    base = frozen.module.BASE
    config = frozen.config
    d1, h4 = base.prepare_signal_bars(m5, config["signal"])
    d1 = d1.loc[d1["timestamp_utc"] <= completed_through].copy()
    h4 = h4.loc[h4["timestamp_utc"] <= completed_through].copy()
    enriched, _ = frozen.module.attach_r1_regime(
        m5, d1, h4, config["signal"], config["regime"]
    )
    enriched = enriched.loc[enriched["timestamp_utc"] <= completed_through].copy()
    if enriched.empty:
        raise ValueError("Insufficient completed history to evaluate R1")

    latest = enriched.iloc[-1]
    signal_time = pd.Timestamp(latest["timestamp_utc"])
    if signal_time != completed_through:
        raise ValueError(
            f"Latest completed H4 bar is {utc_text(signal_time)}, expected {utc_text(completed_through)}"
        )

    base_candidates = base.generate_candidates(enriched, config["signal"])
    exact_candidates = frozen.module.generate_r1_candidates(enriched, config["signal"])
    base_now = base_candidates.loc[base_candidates["signal_time"] == signal_time]
    exact_now = exact_candidates.loc[exact_candidates["signal_time"] == signal_time]

    state_id = deterministic_id("state", SPECIALIST_ID, signal_time, frozen.contract_hash)
    state = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "EVALUATION",
        "state_id": state_id,
        "specialist_id": SPECIALIST_ID,
        "signal_time_utc": utc_text(signal_time),
        "contract_hash": frozen.contract_hash,
        "base_signal": not base_now.empty,
        "r1_allowed": bool(latest.get("r1_allowed", False)),
        "regime_shock": bool(latest.get("regime_shock", False)),
        "d1_trend_persistent_up": bool(latest.get("d1_trend_persistent_up", False)),
        "h4_trend_up": bool(latest.get("trend_up", False)),
        "d1_supportive_up": bool(latest.get("supportive_up_d1", False)),
        "atr_percentile_d1": finite_or_none(latest.get("atr_percentile_d1")),
        "shock_atr_percentile_d1": finite_or_none(
            latest.get("shock_atr_percentile_d1")
        ),
        "body_fraction_h4": finite_or_none(latest.get("body_fraction_h4")),
        "box_high": finite_or_none(latest.get("box_high")),
        "box_low": finite_or_none(latest.get("box_low")),
        "bid_open": finite_or_none(latest.get("bid_open")),
        "bid_close": finite_or_none(latest.get("bid_close")),
        "candidate": not exact_now.empty,
        "trade_permission": False,
        "broker_action_allowed": False,
        "python_execution_authorized": False,
    }
    state["decision_reason"] = decision_reason(state)

    if exact_now.empty:
        return state, None
    candidate_row = exact_now.iloc[0]
    candidate_id = deterministic_id(
        "candidate", SPECIALIST_ID, signal_time, frozen.contract_hash
    )
    candidate = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "CANDIDATE",
        "candidate_id": candidate_id,
        "state_id": state_id,
        "specialist_id": SPECIALIST_ID,
        "signal_time_utc": utc_text(signal_time),
        "direction": "LONG",
        "stop_distance": float(candidate_row["stop_distance"]),
        "target_r": float(candidate_row["target_r"]),
        "contract_hash": frozen.contract_hash,
        "maximum_entry_gap_minutes": int(config["execution"]["maximum_entry_gap_minutes"]),
        "maximum_spread_price": float(config["execution"]["maximum_spread_price"]),
        "maximum_spread_r": float(config["execution"]["maximum_spread_r"]),
        "ticket_cost_usd": float(config["execution"]["ticket_cost_usd"]),
        "holding_cost_per_24h_usd": float(
            config["execution"]["holding_cost_per_24h_usd"]
        ),
        "stress_slippage_r": float(config["execution"]["stress_slippage_r"]),
        "trade_permission": False,
        "broker_action_allowed": False,
        "python_execution_authorized": False,
    }
    return state, candidate


def decision_reason(state: dict[str, Any]) -> str:
    if state["regime_shock"]:
        return "ABSTAIN_SHOCK"
    if not state["d1_trend_persistent_up"]:
        return "ABSTAIN_D1_TREND"
    if not state["h4_trend_up"]:
        return "ABSTAIN_H4_TREND"
    if not state["d1_supportive_up"]:
        return "ABSTAIN_D1_SUPPORT"
    if not state["base_signal"]:
        return "ABSTAIN_NO_COMPRESSION_BREAKOUT"
    return "SHADOW_CANDIDATE"


def deterministic_id(
    kind: str,
    specialist_id: str,
    signal_time: pd.Timestamp | datetime,
    contract_hash: str,
) -> str:
    payload = "|".join((kind, specialist_id, utc_text(signal_time), contract_hash))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def finite_or_none(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if np.isfinite(result) else None


def append_jsonl_once(path: Path, record: dict[str, Any], id_field: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    record_id = str(record[id_field])
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    if str(json.loads(line).get(id_field, "")) == record_id:
                        return False
                except json.JSONDecodeError:
                    continue
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return True


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def read_prospective_ticks(files_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for path in sorted(files_dir.glob("xau_prospective_*_ticks_*.csv")):
        with path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                try:
                    rows.append(
                        {
                            "timestamp_utc": pd.to_datetime(row["timestamp_utc"], utc=True),
                            "tick_time_msc": int(row["tick_time_msc"]),
                            "bid": float(row["bid"]),
                            "ask": float(row["ask"]),
                            "dry_run": row.get("dry_run", "").lower() == "true",
                            "trade_permission": row.get("trade_permission", "").lower()
                            == "true",
                            "broker_action_allowed": row.get(
                                "broker_action_allowed", ""
                            ).lower()
                            == "true",
                        }
                    )
                except (KeyError, TypeError, ValueError):
                    continue
    if not rows:
        return pd.DataFrame(columns=["timestamp_utc", "tick_time_msc", "bid", "ask"])
    result = pd.DataFrame(rows).sort_values(["tick_time_msc", "timestamp_utc"])
    result = result.drop_duplicates("tick_time_msc", keep="last").reset_index(drop=True)
    unsafe = (
        ~result["dry_run"]
        | result["trade_permission"]
        | result["broker_action_allowed"]
    )
    if unsafe.any():
        raise RuntimeError("Prospective tick ledger contains an unsafe authority state")
    return result


def resolve_candidate(
    candidate: dict[str, Any],
    ticks: pd.DataFrame,
    *,
    now_utc: datetime | pd.Timestamp,
) -> dict[str, Any]:
    signal_time = pd.to_datetime(candidate["signal_time_utc"], utc=True)
    deadline = signal_time + pd.Timedelta(
        minutes=float(candidate["maximum_entry_gap_minutes"])
    )
    now = pd.Timestamp(now_utc)
    if now.tzinfo is None:
        now = now.tz_localize("UTC")
    else:
        now = now.tz_convert("UTC")
    eligible = ticks.loc[
        (ticks["timestamp_utc"] >= signal_time) & (ticks["timestamp_utc"] <= deadline)
    ]
    base = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "OUTCOME",
        "candidate_id": candidate["candidate_id"],
        "specialist_id": candidate["specialist_id"],
        "signal_time_utc": candidate["signal_time_utc"],
        "contract_hash": candidate["contract_hash"],
        "trade_permission": False,
        "broker_action_allowed": False,
        "python_execution_authorized": False,
    }
    if eligible.empty:
        if now <= deadline:
            return {**base, "status": "AWAITING_ENTRY_TICK"}
        return {**base, "status": "REJECTED", "rejection_reason": "NO_ENTRY_TICK"}

    entry_tick = eligible.iloc[0]
    entry = float(entry_tick["ask"])
    bid_at_entry = float(entry_tick["bid"])
    spread = entry - bid_at_entry
    risk = float(candidate["stop_distance"])
    if spread < 0 or risk <= 0:
        return {**base, "status": "REJECTED", "rejection_reason": "INVALID_ENTRY_OR_RISK"}
    if spread > float(candidate["maximum_spread_price"]):
        return {**base, "status": "REJECTED", "rejection_reason": "SPREAD_PRICE_LIMIT"}
    if spread / risk > float(candidate["maximum_spread_r"]):
        return {**base, "status": "REJECTED", "rejection_reason": "SPREAD_R_LIMIT"}

    entry_time = pd.Timestamp(entry_tick["timestamp_utc"])
    path = ticks.loc[ticks["timestamp_utc"] >= entry_time].copy()
    stop = entry - risk
    target = entry + float(candidate["target_r"]) * risk
    path["stop_hit"] = path["bid"] <= stop
    path["target_hit"] = path["bid"] >= target
    hits = path.loc[path["stop_hit"] | path["target_hit"]]
    mfe_r = float((path["bid"].max() - entry) / risk)
    mae_r = float((path["bid"].min() - entry) / risk)
    common = {
        **base,
        "entry_time_utc": utc_text(entry_time),
        "entry_price": entry,
        "entry_spread": spread,
        "entry_spread_r": spread / risk,
        "initial_risk_price": risk,
        "stop": stop,
        "target": target,
        "mfe_r": mfe_r,
        "mae_r": mae_r,
        "last_observed_time_utc": utc_text(path.iloc[-1]["timestamp_utc"]),
    }
    if hits.empty:
        return {**common, "status": "OPEN"}

    hit = hits.iloc[0]
    exit_time = pd.Timestamp(hit["timestamp_utc"])
    if bool(hit["stop_hit"]):
        exit_price = min(float(hit["bid"]), stop)
        exit_reason = "STOP"
    else:
        exit_price = target
        exit_reason = "TARGET"
    gross_r = (exit_price - entry) / risk
    holding_days = max(0.0, (exit_time - entry_time).total_seconds() / 86_400.0)
    extra_cost_r = (
        float(candidate["ticket_cost_usd"])
        + holding_days * float(candidate["holding_cost_per_24h_usd"])
    ) / risk
    return {
        **common,
        "status": "CLOSED",
        "exit_time_utc": utc_text(exit_time),
        "exit_price": exit_price,
        "exit_reason": exit_reason,
        "gross_r": gross_r,
        "extra_cost_r": extra_cost_r,
        "stress_net_r": gross_r
        - extra_cost_r
        - float(candidate["stress_slippage_r"]),
        "holding_minutes": (exit_time - entry_time).total_seconds() / 60.0,
    }


def resolve_all_candidates(
    candidate_path: Path,
    tick_files_dir: Path,
    *,
    now_utc: datetime | pd.Timestamp,
) -> list[dict[str, Any]]:
    candidates = read_jsonl(candidate_path)
    ticks = read_prospective_ticks(tick_files_dir)
    return [resolve_candidate(row, ticks, now_utc=now_utc) for row in candidates]


def atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def assert_demo_read_only(account: Any, terminal: Any) -> None:
    if account is None or terminal is None:
        raise RuntimeError("MT5 account or terminal information is unavailable")
    if int(account.login) != EXPECTED_LOGIN:
        raise RuntimeError(f"Unexpected MT5 login {account.login}; expected {EXPECTED_LOGIN}")
    if EXPECTED_SERVER_MARKER.lower() not in str(account.server).lower():
        raise RuntimeError(f"MT5 server is not demo-marked: {account.server}")
    if int(account.trade_mode) != 0:
        raise RuntimeError(f"MT5 account trade mode is not demo: {account.trade_mode}")
    if not bool(terminal.connected):
        raise RuntimeError("MT5 terminal is disconnected")


def summarize_outcomes(outcomes: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for outcome in outcomes:
        status = str(outcome["status"])
        counts[status] = counts.get(status, 0) + 1
    return counts
