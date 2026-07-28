from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from capture_prospective_tradingview_actuals import (
    load_latest_pre_release_forecasts,
)
from capture_prospective_tradingview_consensus import (
    _utc,
)
from download_neutral_tradingview_consensus import (
    _valid_payload,
)
from eurusd_regime_specialists.prospective_neutral_campaign_orchestration import (
    load_actual_evidence,
    load_complete_paths,
    load_market_evidence,
    load_oracle_evidence,
    load_ownership_evidence,
    process_campaign,
)
from eurusd_regime_specialists.prospective_neutral_campaign_orchestration import (
    verify_lock as verify_campaign_lock,
)
from eurusd_regime_specialists.prospective_neutral_macro_crossasset_execution import (
    build_signal_ledger,
)
from eurusd_regime_specialists.research import sha256_file
from prewarm_prospective_neutral_ownership import prewarm_status

CONFIG_PATH = ROOT / "config" / "frozen_prospective_neutral_operations_planner_v1.json"
LOCK_PATH = (
    ROOT / "EURUSD_NEUTRAL_PROSPECTIVE_OPERATIONS_PLANNER_PREREG_2026_07_28.sha256.json"
)
DEFAULT_ROOTS = {
    "consensus_and_actual": Path(
        "D:/AlgoTradingData/prospective/eurusd-neutral-tradingview-consensus-v1"
    ),
    "event_market": Path(
        "D:/AlgoTradingData/prospective/"
        "eurusd-neutral-macro-crossasset-agreement-v1/market"
    ),
    "neutral_ownership": Path(
        "D:/AlgoTradingData/prospective/"
        "eurusd-neutral-macro-crossasset-agreement-v1/ownership"
    ),
    "trade_path": Path(
        "D:/AlgoTradingData/prospective/"
        "eurusd-neutral-macro-crossasset-agreement-v1/path"
    ),
    "oracle_evaluation": Path(
        "D:/AlgoTradingData/prospective/"
        "eurusd-neutral-macro-crossasset-agreement-v1/oracle"
    ),
    "ledger": Path(
        "D:/AlgoTradingData/prospective/"
        "eurusd-neutral-macro-crossasset-agreement-v1/ledger"
    ),
}
SCHEMA_VERSION = "eurusd_neutral_prospective_operations_plan_v1"


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_prospective_start_and_first_signal") is not True:
        raise RuntimeError("Prospective operations planner is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Operations planner lock mismatch: {relative}")
        checked[relative] = actual
    cfg = load_config()
    campaign = cfg["campaign_orchestration_contract"]
    if sha256_file(ROOT / campaign["path"]) != campaign["sha256"]:
        raise RuntimeError("Operations planner campaign contract drift")
    for relative, expected in cfg["source_contracts"].items():
        if sha256_file(ROOT / relative) != expected:
            raise RuntimeError(f"Operations planner source drift: {relative}")
    verify_campaign_lock()
    return checked


def _serialize(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Mapping):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return None
    return value


def _safe_reference(
    root: Path,
    reference: Mapping[str, Any],
    label: str,
) -> Path:
    relative = Path(str(reference.get("relative_path")))
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError(f"{label} escapes its evidence root")
    path = (root / relative).resolve()
    resolved_root = root.resolve()
    if resolved_root not in path.parents:
        raise RuntimeError(f"{label} escapes its evidence root")
    expected = str(reference.get("sha256")).lower()
    if len(expected) != 64 or not path.is_file():
        raise RuntimeError(f"{label} reference is incomplete")
    if sha256_file(path) != expected:
        raise RuntimeError(f"{label} hash drift")
    return path


def load_calendar_watchlist(
    root: Path,
    target_tickers: Mapping[str, str],
) -> tuple[list[dict[str, Any]], pd.Timestamp, dict[str, int]]:
    manifests = sorted(root.glob("manifests/MANIFEST_*.json"))
    if not manifests:
        raise RuntimeError("No immutable consensus snapshot is available")
    snapshots: list[tuple[pd.Timestamp, dict[str, Any], dict[str, Any]]] = []
    normalized_seen: set[str] = set()
    for path in manifests:
        payload = path.read_bytes()
        manifest = json.loads(payload)
        if (
            manifest.get("schema_version")
            != "eurusd_neutral_prospective_consensus_snapshot_v1"
            or manifest.get("broker_action_allowed") is not False
        ):
            raise RuntimeError("Unexpected consensus manifest contract")
        raw_path = _safe_reference(root, manifest["raw_snapshot"], "Consensus raw")
        _safe_reference(
            root,
            manifest["capture_metadata"],
            "Consensus metadata",
        )
        normalized = manifest["normalized_snapshot"]
        normalized_relative = str(normalized.get("relative_path"))
        if normalized_relative in normalized_seen:
            raise RuntimeError("Consensus snapshot has multiple manifests")
        normalized_seen.add(normalized_relative)
        normalized_path = _safe_reference(
            root,
            normalized,
            "Consensus normalized",
        )
        frame = pd.read_parquet(normalized_path)
        if len(frame) != int(normalized["rows"]):
            raise RuntimeError("Consensus normalized row-count drift")
        raw = _valid_payload(raw_path.read_bytes())
        snapshots.append((_utc(manifest["observed_at_utc"]), manifest, raw))
    observed, _manifest, latest_raw = max(snapshots, key=lambda row: row[0])
    events: list[dict[str, Any]] = []
    identities: set[tuple[str, str, str]] = set()
    for event in latest_raw.get("result", []):
        ticker = str(event.get("ticker") or "")
        family = target_tickers.get(ticker)
        if family is None:
            continue
        event_id = str(event.get("id") or "")
        event_time = _utc(event.get("date"))
        identity = (event_id, ticker, event_time.isoformat())
        if not event_id or identity in identities:
            raise RuntimeError("Calendar target event identity is ambiguous")
        identities.add(identity)
        events.append(
            {
                "family": family,
                "tradingview_event_id": event_id,
                "tradingview_ticker": ticker,
                "event_time_utc": event_time,
                "forecast_visible_in_latest_raw": (
                    event.get("forecastRaw") is not None
                    or event.get("forecast") is not None
                ),
                "actual_visible_in_latest_raw": (
                    event.get("actualRaw") is not None
                    or event.get("actual") is not None
                ),
            }
        )
    events.sort(
        key=lambda row: (
            row["event_time_utc"],
            row["family"],
            row["tradingview_event_id"],
        )
    )
    return (
        events,
        observed,
        {
            "consensus_manifests": len(manifests),
            "validated_normalized_snapshots": len(normalized_seen),
            "target_events_in_latest_snapshot": len(events),
        },
    )


def _event_key(row: Mapping[str, Any]) -> tuple[str, str, pd.Timestamp]:
    return (
        str(row["tradingview_event_id"]),
        str(row["tradingview_ticker"]),
        _utc(row["event_time_utc"]),
    )


def _frame_by_event(frame: pd.DataFrame) -> dict[tuple[str, str, pd.Timestamp], dict]:
    if frame.empty:
        return {}
    result: dict[tuple[str, str, pd.Timestamp], dict] = {}
    for row in frame.to_dict(orient="records"):
        key = _event_key(row)
        if key in result:
            raise RuntimeError("Selected event evidence is duplicated")
        result[key] = row
    return result


def _poll_interval(
    seconds_to_release: float,
    cadence: list[Mapping[str, Any]],
) -> int | None:
    for row in sorted(
        cadence,
        key=lambda value: int(value["minimum_seconds_to_release"]),
        reverse=True,
    ):
        if seconds_to_release >= int(row["minimum_seconds_to_release"]):
            return int(row["interval_seconds"])
    return None


def _command(template: str, **values: Any) -> str:
    normalized = {
        key: (
            _utc(value).strftime("%Y-%m-%dT%H:%M:%SZ")
            if isinstance(value, pd.Timestamp)
            else str(value)
        )
        for key, value in values.items()
    }
    return template.format(**normalized)


def _stage(
    name: str,
    status: str,
    *,
    due: bool = False,
    due_at: pd.Timestamp | None = None,
    command: str | None = None,
    reason: str,
) -> dict[str, Any]:
    return {
        "stage": name,
        "status": status,
        "due": due,
        "due_at_utc": due_at,
        "command": command,
        "reason": reason,
    }


def plan_ownership_cache_action(
    cache_status: Mapping[str, Any],
    *,
    evaluated_at_utc: Any,
    eligible_date: Any,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    now = _utc(evaluated_at_utc)
    date_text = _utc(eligible_date).strftime("%Y-%m-%d")
    missing = int(cache_status["missing_safe_symbol_hours"])
    if missing:
        return _stage(
            "OWNERSHIP_CACHE_PREWARM",
            "DUE",
            due=True,
            due_at=now,
            command=_command(
                config["commands"]["prewarm_ownership"],
                date=date_text,
            ),
            reason=(
                f"Cache {missing} newly safe symbol-hours before ownership capture"
            ),
        )
    next_hour_safe = (
        now.floor("h")
        + pd.Timedelta(hours=1)
        + pd.Timedelta(
            seconds=int(
                config["safe_lags"]["ownership_after_midnight_seconds"]
            )
        )
    )
    return _stage(
        "OWNERSHIP_CACHE_PREWARM",
        "SCHEDULED",
        due_at=next_hour_safe,
        reason="Recheck after the next completed H1 bar becomes safely available",
    )


def plan_event_actions(
    event: Mapping[str, Any],
    *,
    evaluated_at_utc: Any,
    last_calendar_capture_utc: Any,
    forecast: Mapping[str, Any] | None,
    actual: Mapping[str, Any] | None,
    market: Mapping[str, Any] | None,
    ownership: Mapping[str, Any] | None,
    signal: Mapping[str, Any] | None,
    path: Mapping[str, Any] | None,
    signal_persisted: bool,
    trade_persisted: bool,
    oracle_date_complete: bool,
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    now = _utc(evaluated_at_utc)
    event_time = _utc(event["event_time_utc"])
    event_date = event_time.normalize()
    date_text = event_date.strftime("%Y-%m-%d")
    safe = config["safe_lags"]
    commands = config["commands"]
    forecast_deadline = event_time - pd.Timedelta(
        seconds=int(safe["minimum_forecast_lead_seconds"])
    )
    stages: list[dict[str, Any]] = []

    if now < forecast_deadline:
        interval = _poll_interval(
            (event_time - now).total_seconds(),
            list(config["polling_cadence"]),
        )
        assert interval is not None
        next_poll = _utc(last_calendar_capture_utc) + pd.Timedelta(seconds=interval)
        poll_due = now >= next_poll
        stages.append(
            _stage(
                "PRE_RELEASE_FORECAST",
                "DUE" if poll_due else "SCHEDULED",
                due=poll_due,
                due_at=next_poll,
                command=commands["capture_forecast"] if poll_due else None,
                reason=(
                    "Refresh the latest admissible forecast before release"
                    if forecast is not None
                    else "Poll until the provider publishes a forecast"
                ),
            )
        )
    elif forecast is None:
        stages.append(
            _stage(
                "PRE_RELEASE_FORECAST",
                "MISSED_NO_TRADE",
                reason="No admissible forecast existed by the frozen lead deadline",
            )
        )
        return stages
    else:
        stages.append(
            _stage(
                "PRE_RELEASE_FORECAST",
                "CAPTURED",
                reason="An admissible pre-release forecast is immutable",
            )
        )

    ownership_due = event_date + pd.Timedelta(
        seconds=int(safe["ownership_after_midnight_seconds"])
    )
    if ownership is not None:
        stages.append(
            _stage(
                "NEUTRAL_OWNERSHIP",
                "CAPTURED",
                reason="Event-date ownership evidence is available",
            )
        )
    else:
        ownership_is_due = now >= ownership_due
        stages.append(
            _stage(
                "NEUTRAL_OWNERSHIP",
                "DUE" if ownership_is_due else "SCHEDULED",
                due=ownership_is_due,
                due_at=ownership_due,
                command=(
                    _command(
                        commands["capture_ownership"],
                        date=date_text,
                    )
                    if ownership_is_due
                    else None
                ),
                reason="Capture the frozen prior-H1 Neutral classification",
            )
        )

    actual_due = event_time + pd.Timedelta(
        seconds=int(safe["actual_after_release_seconds"])
    )
    if actual is not None:
        stages.append(
            _stage(
                "POST_RELEASE_ACTUAL",
                "CAPTURED",
                reason="The earliest linked actual is available",
            )
        )
    elif forecast is not None:
        actual_is_due = now >= actual_due
        stages.append(
            _stage(
                "POST_RELEASE_ACTUAL",
                "DUE" if actual_is_due else "SCHEDULED",
                due=actual_is_due,
                due_at=actual_due,
                command=commands["capture_actual"] if actual_is_due else None,
                reason="Capture the exact linked actual after its safe lag",
            )
        )

    market_due = event_time + pd.Timedelta(
        seconds=int(safe["event_market_after_release_seconds"])
    )
    if market is not None:
        stages.append(
            _stage(
                "EVENT_MARKET",
                "CAPTURED",
                reason="Three completed post-release M5 bars are available",
            )
        )
    elif forecast is not None:
        market_is_due = now >= market_due
        stages.append(
            _stage(
                "EVENT_MARKET",
                "DUE" if market_is_due else "SCHEDULED",
                due=market_is_due,
                due_at=market_due,
                command=(
                    _command(
                        commands["capture_event_market"],
                        event_time=event_time,
                    )
                    if market_is_due
                    else None
                ),
                reason="Capture EURUSD, DXY, and Treasury confirmation bars",
            )
        )

    signal_ready = signal is not None
    if signal_ready and (
        not signal_persisted
        or (path is not None and not trade_persisted)
        or (str(signal["side"]) == "CASH" and not trade_persisted)
    ):
        stages.append(
            _stage(
                "CAMPAIGN_PROCESS",
                "DUE",
                due=True,
                due_at=now,
                command=_command(
                    commands["process_campaign"],
                    as_of=now,
                ),
                reason="Persist the newly terminal immutable campaign state",
            )
        )
    elif signal_ready:
        stages.append(
            _stage(
                "CAMPAIGN_PROCESS",
                "CURRENT",
                reason="The generated signal is already represented in the ledger",
            )
        )

    if signal_ready and str(signal["side"]) != "CASH":
        path_due = _utc(signal["entry_time_utc"]) + pd.Timedelta(
            seconds=int(safe["path_after_entry_seconds"])
        )
        if path is not None:
            stages.append(
                _stage(
                    "TRADE_PATH",
                    "CAPTURED",
                    reason="The complete 12-hour path is immutable",
                )
            )
        else:
            path_is_due = now >= path_due
            stages.append(
                _stage(
                    "TRADE_PATH",
                    "DUE" if path_is_due else "SCHEDULED",
                    due=path_is_due,
                    due_at=path_due,
                    command=(
                        _command(
                            commands["capture_path"],
                            signal_id=signal["signal_id"],
                            entry_time=_utc(signal["entry_time_utc"]),
                        )
                        if path_is_due
                        else None
                    ),
                    reason="Capture the full bid/ask path after its safe deadline",
                )
            )

    if trade_persisted:
        oracle_due = event_date + pd.Timedelta(
            seconds=int(safe["oracle_after_date_midnight_seconds"])
        )
        if oracle_date_complete:
            stages.append(
                _stage(
                    "ORACLE_EVALUATION",
                    "CAPTURED",
                    reason="The late evaluation-only oracle date is complete",
                )
            )
        else:
            oracle_is_due = now >= oracle_due
            stages.append(
                _stage(
                    "ORACLE_EVALUATION",
                    "DUE" if oracle_is_due else "SCHEDULED",
                    due=oracle_is_due,
                    due_at=oracle_due,
                    command=(
                        _command(
                            commands["capture_oracle"],
                            date=date_text,
                        )
                        if oracle_is_due
                        else None
                    ),
                    reason="Attach no label until the date-plus-36h safe time",
                )
            )
    return stages


def _load_ledger_records(root: Path, kind: str) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in sorted((root / kind / "records").glob("*.json")):
        wrapper = json.loads(path.read_bytes())
        record = wrapper.get("record")
        if not isinstance(record, dict):
            raise TypeError(f"Invalid immutable {kind} record")
        signal_id = str(record.get("signal_id"))
        if signal_id in records:
            raise RuntimeError(f"Duplicate immutable {kind} signal ID")
        records[signal_id] = record
    return records


def build_operations_plan(
    *,
    evaluated_at_utc: Any,
    roots: Mapping[str, Path] = DEFAULT_ROOTS,
) -> dict[str, Any]:
    cfg = load_config()
    now = _utc(evaluated_at_utc)
    events, latest_capture, consensus_census = load_calendar_watchlist(
        roots["consensus_and_actual"],
        cfg["target_tickers"],
    )
    forecasts = load_latest_pre_release_forecasts(roots["consensus_and_actual"])
    actuals, actual_census = load_actual_evidence(
        roots["consensus_and_actual"],
        evaluated_at_utc=now,
    )
    event_identities = {_event_key(event) for event in events}
    for frame in (forecasts, actuals):
        for row in frame.to_dict(orient="records"):
            key = _event_key(row)
            if key in event_identities:
                continue
            event_identities.add(key)
            events.append(
                {
                    "family": str(row["family"]),
                    "tradingview_event_id": key[0],
                    "tradingview_ticker": key[1],
                    "event_time_utc": key[2],
                    "forecast_visible_in_latest_raw": False,
                    "actual_visible_in_latest_raw": False,
                }
            )
    events.sort(
        key=lambda row: (
            row["event_time_utc"],
            row["family"],
            row["tradingview_event_id"],
        )
    )
    markets, market_census = load_market_evidence(
        roots["event_market"],
        evaluated_at_utc=now,
    )
    ownerships, ownership_census = load_ownership_evidence(
        roots["neutral_ownership"],
        evaluated_at_utc=now,
    )
    paths, path_census = load_complete_paths(
        roots["trade_path"],
        evaluated_at_utc=now,
    )
    _oracle, oracle_dates, oracle_census = load_oracle_evidence(
        roots["oracle_evaluation"],
        roots["neutral_ownership"],
        evaluated_at_utc=now,
    )
    signals, signal_census = build_signal_ledger(
        actuals,
        markets,
        ownerships,
    )
    campaign = process_campaign(
        evaluated_at_utc=now,
        roots=roots,
        persist=False,
    )
    forecast_map = _frame_by_event(forecasts)
    actual_map = _frame_by_event(actuals)
    market_map = (
        {_utc(row["event_time_utc"]): row for row in markets.to_dict(orient="records")}
        if not markets.empty
        else {}
    )
    ownership_map = (
        {
            str(row["eligible_date"])[:10]: row
            for row in ownerships.to_dict(orient="records")
        }
        if not ownerships.empty
        else {}
    )
    signal_map = _frame_by_event(signals)
    signal_records = _load_ledger_records(roots["ledger"], "signals")
    trade_records = _load_ledger_records(roots["ledger"], "trades")
    start = _utc(cfg["prospective_start_utc"])
    upcoming = [
        event
        for event in events
        if _utc(event["event_time_utc"]) >= now
        and _utc(event["event_time_utc"]) >= start
    ]
    global_actions: list[dict[str, Any]] = []
    ownership_cache_status: dict[str, Any] | None = None
    if upcoming:
        nearest_date = _utc(upcoming[0]["event_time_utc"]).normalize()
        ownership_cache_status = prewarm_status(
            nearest_date,
            roots["neutral_ownership"],
            now_utc=now,
        )
        global_actions.append(
            plan_ownership_cache_action(
                ownership_cache_status,
                evaluated_at_utc=now,
                eligible_date=nearest_date,
                config=cfg,
            )
        )
    plans: list[dict[str, Any]] = []
    for event in events:
        event_time = _utc(event["event_time_utc"])
        if event_time < start:
            continue
        key = _event_key(event)
        signal = signal_map.get(key)
        signal_id = str(signal["signal_id"]) if signal is not None else None
        stages = plan_event_actions(
            event,
            evaluated_at_utc=now,
            last_calendar_capture_utc=latest_capture,
            forecast=forecast_map.get(key),
            actual=actual_map.get(key),
            market=market_map.get(event_time),
            ownership=ownership_map.get(event_time.strftime("%Y-%m-%d")),
            signal=signal,
            path=paths.get(signal_id) if signal_id is not None else None,
            signal_persisted=signal_id in signal_records,
            trade_persisted=signal_id in trade_records,
            oracle_date_complete=(event_time.strftime("%Y-%m-%d") in oracle_dates),
            config=cfg,
        )
        plans.append({**event, "stages": stages})
    due = [
        {
            "family": event["family"],
            "event_time_utc": event["event_time_utc"],
            **stage,
        }
        for event in plans
        for stage in event["stages"]
        if stage["due"]
    ]
    due.extend(
        {
            "family": None,
            "event_time_utc": None,
            **stage,
        }
        for stage in global_actions
        if stage["due"]
    )
    scheduled = [
        _utc(stage["due_at_utc"])
        for event in plans
        for stage in event["stages"]
        if stage["due_at_utc"] is not None and _utc(stage["due_at_utc"]) > now
    ]
    scheduled.extend(
        _utc(stage["due_at_utc"])
        for stage in global_actions
        if stage["due_at_utc"] is not None
        and _utc(stage["due_at_utc"]) > now
    )
    return _serialize(
        {
            "schema_version": SCHEMA_VERSION,
            "evaluated_at_utc": now,
            "status": "ACTION_DUE" if due else "WAITING_FOR_NEXT_SAFE_ACTION",
            "latest_calendar_capture_utc": latest_capture,
            "next_scheduled_action_utc": min(scheduled) if scheduled else None,
            "due_actions": due,
            "global_actions": global_actions,
            "events": plans,
            "census": {
                **consensus_census,
                **actual_census,
                **market_census,
                **ownership_census,
                **path_census,
                **oracle_census,
                **signal_census,
                "ownership_cache": ownership_cache_status,
            },
            "campaign_status": campaign["status"],
            "historical_pnl_loaded": False,
            "oracle_or_outcome_used_before_safe_known_time": False,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("status",))
    parser.add_argument("--as-of")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    verify_lock()
    evaluated = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if args.as_of is None
        else _utc(args.as_of)
    )
    result = build_operations_plan(evaluated_at_utc=evaluated)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
