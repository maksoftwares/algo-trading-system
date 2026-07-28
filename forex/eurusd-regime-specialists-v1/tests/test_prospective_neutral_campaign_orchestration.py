from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from eurusd_regime_specialists.prospective_neutral_campaign_orchestration import (
    attach_completed_oracle_labels,
    load_actual_evidence,
    load_market_evidence,
    load_oracle_evidence,
    load_ownership_evidence,
    process_campaign,
    reconcile_signal_records,
    route_operational_signals,
)
from eurusd_regime_specialists.prospective_neutral_macro_crossasset_execution import (
    ACTUAL_SEMANTICS,
    MARKET_SEMANTICS,
    build_neutral_ownership_record,
    build_signal_ledger,
)


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            default=lambda item: (
                item.isoformat() if isinstance(item, pd.Timestamp) else str(item)
            ),
        )
        + "\n"
    ).encode()


def _write(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _roots(tmp_path: Path) -> dict[str, Path]:
    roots = {
        "consensus_and_actual": tmp_path / "actual",
        "event_market": tmp_path / "market",
        "neutral_ownership": tmp_path / "ownership",
        "trade_path": tmp_path / "path",
        "oracle_evaluation": tmp_path / "oracle",
        "ledger": tmp_path / "ledger",
    }
    for root in roots.values():
        root.mkdir(parents=True)
    return roots


def _write_actual(
    root: Path,
    *,
    suffix: str = "actual",
    actual_value: float = 0.1,
    actual_observed_at: str = "2026-08-12T12:32:00Z",
) -> pd.DataFrame:
    forecast_relative = "raw/forecast.json"
    actual_relative = f"post_release_raw/{suffix}.json"
    metadata_relative = f"post_release_metadata/{suffix}.json"
    forecast_hash = _write(root / forecast_relative, b"forecast")
    actual_hash = _write(
        root / actual_relative,
        f"actual:{actual_value}".encode(),
    )
    metadata_hash = _write(
        root / metadata_relative,
        f"metadata:{suffix}".encode(),
    )
    event_time = pd.Timestamp("2026-08-12T12:30:00Z")
    actual_observed = pd.Timestamp(actual_observed_at)
    forecast_value = 0.2
    surprise = actual_value - forecast_value
    macro_side = "LONG" if surprise < 0 else ("SHORT" if surprise > 0 else "CASH")
    frame = pd.DataFrame(
        [
            {
                "family": "CPI",
                "event_time_utc": event_time,
                "forecast_value": forecast_value,
                "forecast_observed_at_utc": pd.Timestamp("2026-08-12T11:00:00Z"),
                "forecast_lead_seconds": 5400.0,
                "forecast_raw_snapshot_relative_path": (forecast_relative),
                "forecast_raw_snapshot_sha256": forecast_hash,
                "tradingview_event_id": "event-1",
                "tradingview_ticker": "ECONOMICS:USCPI",
                "actual_value": actual_value,
                "actual_observed_at_utc": actual_observed,
                "actual_lag_seconds": float(
                    (actual_observed - event_time).total_seconds()
                ),
                "actual_raw_snapshot_relative_path": actual_relative,
                "actual_raw_snapshot_sha256": actual_hash,
                "surprise_value": surprise,
                "macro_side": macro_side,
                "capture_semantics": ACTUAL_SEMANTICS,
            }
        ]
    )
    normalized_relative = f"post_release_normalized/{suffix}.parquet"
    normalized_path = root / normalized_relative
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(normalized_path, index=False)
    normalized_hash = hashlib.sha256(normalized_path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": ("eurusd_neutral_prospective_actual_snapshot_v1"),
        "raw_snapshot": {
            "relative_path": actual_relative,
            "sha256": actual_hash,
        },
        "capture_metadata": {
            "relative_path": metadata_relative,
            "sha256": metadata_hash,
        },
        "normalized_snapshot": {
            "relative_path": normalized_relative,
            "sha256": normalized_hash,
            "rows": 1,
        },
        "broker_action_allowed": False,
    }
    _write(
        root / f"post_release_manifests/MANIFEST_{suffix}.json",
        _json_bytes(manifest),
    )
    return frame


def _market_frame(
    *,
    market_observed_at: str = "2026-08-12T12:46:01Z",
    eurusd_post_mid: float = 1.1010,
    dxy_post_mid: float = 99.8,
    treasury_post_mid: float = 110.2,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_time_utc": pd.Timestamp("2026-08-12T12:30:00Z"),
                "observation_start_utc": pd.Timestamp("2026-08-12T12:30:00Z"),
                "observation_completed_at_utc": pd.Timestamp("2026-08-12T12:45:00Z"),
                "market_observed_at_utc": pd.Timestamp(market_observed_at),
                "eurusd_pre_mid": 1.1000,
                "eurusd_post_mid": eurusd_post_mid,
                "eurusd_observation_mid_high": 1.1012,
                "eurusd_observation_mid_low": 1.0998,
                "dxy_pre_mid": 100.0,
                "dxy_post_mid": dxy_post_mid,
                "treasury_pre_mid": 110.0,
                "treasury_post_mid": treasury_post_mid,
                "capture_semantics": MARKET_SEMANTICS,
            }
        ]
    )


def _write_market(
    root: Path,
    *,
    suffix: str = "market",
    market_observed_at: str = "2026-08-12T12:46:01Z",
    eurusd_post_mid: float = 1.1010,
    dxy_post_mid: float = 99.8,
    treasury_post_mid: float = 110.2,
) -> pd.DataFrame:
    raw_relative = f"raw/EURUSD/{suffix}.json"
    metadata_relative = f"metadata/EURUSD/{suffix}.json"
    raw_hash = _write(root / raw_relative, f"market raw:{suffix}".encode())
    metadata_hash = _write(
        root / metadata_relative,
        f"market metadata:{suffix}".encode(),
    )
    frame = _market_frame(
        market_observed_at=market_observed_at,
        eurusd_post_mid=eurusd_post_mid,
        dxy_post_mid=dxy_post_mid,
        treasury_post_mid=treasury_post_mid,
    )
    normalized_relative = f"normalized/{suffix}.parquet"
    normalized_path = root / normalized_relative
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(normalized_path, index=False)
    normalized_hash = hashlib.sha256(normalized_path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": ("eurusd_neutral_prospective_event_market_m5_v1"),
        "event_time_utc": "2026-08-12T12:30:00Z",
        "market_observed_at_utc": market_observed_at,
        "coverage": "COMPLETE",
        "raw_snapshots": [
            {
                "raw_relative_path": raw_relative,
                "raw_sha256": raw_hash,
                "metadata_relative_path": metadata_relative,
                "metadata_sha256": metadata_hash,
            }
        ],
        "normalized_snapshot": {
            "relative_path": normalized_relative,
            "sha256": normalized_hash,
            "rows": 1,
        },
        "broker_action_allowed": False,
    }
    _write(
        root / f"manifests/MANIFEST_{suffix}.json",
        _json_bytes(manifest),
    )
    return frame


def _write_ownership(
    root: Path,
    *,
    neutral: bool = True,
    eligible_date: str = "2026-08-12",
) -> dict:
    day = pd.Timestamp(eligible_date, tz="UTC")
    day_string = day.strftime("%Y-%m-%d")
    record = build_neutral_ownership_record(
        eligible_date=day,
        state_timestamp_utc=day - pd.Timedelta(hours=1),
        ownership_observed_at_utc=day + pd.Timedelta(minutes=2),
        direction="NEUTRAL" if neutral else "USD_UP",
        shock=False,
        dxy_compressed=False,
        eurusd_compressed=False,
        source_hashes={
            "EURUSD": "1" * 64,
            "GBPUSD": "2" * 64,
            "USDJPY": "3" * 64,
            "DOLLARIDXUSD": "4" * 64,
            "USTBONDTRUSD": "5" * 64,
        },
    )
    record["classifier_terminal_features_sha256"] = "f" * 64
    evidence_hash = record["ownership_evidence_sha256"]
    record_relative = f"records/{day_string}_{evidence_hash[:16]}.json"
    record_hash = _write(root / record_relative, _json_bytes(record))
    manifest = {
        "schema_version": "eurusd_prospective_neutral_ownership_v1",
        "eligible_date": day,
        "ownership_observed_at_utc": day + pd.Timedelta(minutes=2),
        "ownership_record": {
            "relative_path": record_relative,
            "sha256": record_hash,
            "ownership_evidence_sha256": evidence_hash,
            "is_neutral": record["is_neutral"],
        },
        "broker_action_allowed": False,
    }
    manifest_payload = _json_bytes(manifest)
    manifest_hash = hashlib.sha256(manifest_payload).hexdigest()
    _write(
        root / "manifests" / f"MANIFEST_{day_string}_{manifest_hash[:16]}.json",
        manifest_payload,
    )
    return record


def _path_frame() -> pd.DataFrame:
    index = pd.date_range("2026-08-12T12:50:00Z", periods=144, freq="5min")
    return pd.DataFrame(
        {
            "timestamp_utc": index,
            "bid_open": 1.1000,
            "bid_high": 1.1001,
            "bid_low": 1.0999,
            "bid_close": 1.1000,
            "ask_open": 1.1001,
            "ask_high": 1.1002,
            "ask_low": 1.1000,
            "ask_close": 1.1001,
        }
    )


def _write_path(root: Path, signal_id: str) -> pd.DataFrame:
    raw_relative = f"raw/{signal_id}/hour.json"
    metadata_relative = f"metadata/{signal_id}/hour.json"
    raw_hash = _write(root / raw_relative, b"path raw")
    metadata_hash = _write(root / metadata_relative, b"path metadata")
    frame = _path_frame()
    normalized_relative = f"normalized/{signal_id}.parquet"
    normalized_path = root / normalized_relative
    normalized_path.parent.mkdir(parents=True)
    frame.to_parquet(normalized_path, index=False)
    normalized_hash = hashlib.sha256(normalized_path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": ("eurusd_neutral_prospective_trade_path_v2"),
        "status": "COMPLETE",
        "signal_id": signal_id,
        "entry_time_utc": "2026-08-12T12:50:00Z",
        "deadline_utc": "2026-08-13T00:50:00Z",
        "market_observed_at_utc": "2026-08-13T00:51:01Z",
        "raw_snapshots": [
            {
                "raw_relative_path": raw_relative,
                "raw_sha256": raw_hash,
                "metadata_relative_path": metadata_relative,
                "metadata_sha256": metadata_hash,
            }
        ],
        "normalized_snapshot": {
            "relative_path": normalized_relative,
            "sha256": normalized_hash,
            "rows": 144,
        },
        "expected_m5_rows": 144,
        "missing_m5_timestamps": [],
        "broker_action_allowed": False,
    }
    _write(
        root / f"manifests/MANIFEST_{signal_id}_path.json",
        _json_bytes(manifest),
    )
    return frame


def _write_oracle(
    root: Path,
    ownership_root: Path,
    *,
    known_time: str = "2026-08-13T12:01:01Z",
    status: str = "ORACLE_DATE_COMPLETE",
    label_side: str = "LONG",
) -> Path:
    day = pd.Timestamp("2026-08-12T00:00:00Z")
    known = pd.Timestamp(known_time)
    next_day = "2026-08-13"
    if not list(ownership_root.glob(f"manifests/MANIFEST_{next_day}_*.json")):
        _write_ownership(
            ownership_root,
            eligible_date=next_day,
        )
    ownership_manifest_path = next(
        ownership_root.glob(f"manifests/MANIFEST_{next_day}_*.json")
    )
    ownership_manifest_hash = hashlib.sha256(
        ownership_manifest_path.read_bytes()
    ).hexdigest()
    ownership_manifest = json.loads(ownership_manifest_path.read_bytes())
    ownership_record_reference = ownership_manifest["ownership_record"]

    raw_rows = []
    for hour in pd.date_range(day, periods=36, freq="h"):
        raw_relative = f"raw/2026-08-12/{hour:%Y%m%dT%H0000Z}.json"
        metadata_relative = f"metadata/2026-08-12/{hour:%Y%m%dT%H0000Z}.json"
        raw_hash = _write(root / raw_relative, b"{}")
        metadata = {
            "schema_version": "eurusd_neutral_prospective_oracle_day_v1",
            "oracle_date": day,
            "symbol": "EURUSD",
            "hour_utc": hour,
            "observed_at_utc": known,
            "raw_relative_path": raw_relative,
            "raw_sha256": raw_hash,
            "broker_action_allowed": False,
        }
        metadata_hash = _write(root / metadata_relative, _json_bytes(metadata))
        raw_rows.append(
            {
                "hour_utc": hour,
                "observed_at_utc": known,
                "raw_relative_path": raw_relative,
                "raw_sha256": raw_hash,
                "metadata_relative_path": metadata_relative,
                "metadata_sha256": metadata_hash,
                "tick_count": 0,
            }
        )

    inventory_hash = "9" * 64
    market = pd.DataFrame({"timestamp_utc": [pd.Timestamp("2026-08-12T00:00:00Z")]})
    market_relative = "normalized/EURUSD_2026-08-12_test.parquet"
    market_path = root / market_relative
    market_path.parent.mkdir(parents=True, exist_ok=True)
    market.to_parquet(market_path, index=False)
    market_hash = hashlib.sha256(market_path.read_bytes()).hexdigest()

    label_columns = [
        "oracle_date",
        "oracle_trade_number",
        "side",
        "entry_time_utc",
        "regime",
        "oracle_label_known_time_utc",
        "oracle_date_complete",
        "market_inventory_sha256",
        "ownership_manifest_sha256",
    ]
    if status == "ORACLE_DATE_COMPLETE":
        labels = pd.DataFrame(
            [
                {
                    "oracle_date": "2026-08-12",
                    "oracle_trade_number": position,
                    "side": label_side,
                    "entry_time_utc": day + pd.Timedelta(hours=position),
                    "regime": "NEUTRAL",
                    "oracle_label_known_time_utc": known,
                    "oracle_date_complete": True,
                    "market_inventory_sha256": inventory_hash,
                    "ownership_manifest_sha256": (ownership_manifest_hash),
                }
                for position in range(1, 5)
            ]
        )
    else:
        labels = pd.DataFrame(columns=label_columns)
    labels_relative = "labels/ORACLE_2026-08-12_test.parquet"
    labels_path = root / labels_relative
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    labels.to_parquet(labels_path, index=False)
    labels_hash = hashlib.sha256(labels_path.read_bytes()).hexdigest()

    context = {
        "eligible_date": pd.Timestamp("2026-08-13T00:00:00Z"),
        "ownership_observed_at_utc": pd.Timestamp("2026-08-13T00:02:00Z"),
        "ownership_manifest_relative_path": (
            ownership_manifest_path.relative_to(ownership_root).as_posix()
        ),
        "ownership_manifest_sha256": ownership_manifest_hash,
        "ownership_record_relative_path": ownership_record_reference["relative_path"],
        "ownership_record_sha256": ownership_record_reference["sha256"],
        "ownership_evidence_sha256": ownership_record_reference[
            "ownership_evidence_sha256"
        ],
    }
    manifest = {
        "schema_version": "eurusd_neutral_prospective_oracle_day_v1",
        "status": status,
        "oracle_date": day,
        "oracle_label_known_time_utc": known,
        "raw_snapshots": raw_rows,
        "market_inventory_sha256": inventory_hash,
        "normalized_market": {
            "relative_path": market_relative,
            "sha256": market_hash,
            "rows": len(market),
        },
        "oracle_labels": {
            "relative_path": labels_relative,
            "sha256": labels_hash,
            "rows": len(labels),
            "neutral_rows": (
                int(labels["regime"].eq("NEUTRAL").sum()) if len(labels) else 0
            ),
        },
        "next_day_context": context,
        "oracle_census": {
            "status": (
                "ORACLE_COMPLETE"
                if status == "ORACLE_DATE_COMPLETE"
                else "ORACLE_UNAVAILABLE_INSUFFICIENT_FOUR_WINNERS"
            )
        },
        "causality": {
            "capture_after_date_plus_36h_plus_60s": True,
            "next_day_context_required": True,
            "labels_evaluation_only": True,
            "signals_or_trades_changed": False,
        },
        "historical_pnl_loaded": False,
        "broker_action_allowed": False,
    }
    manifest_payload = _json_bytes(manifest)
    manifest_hash = hashlib.sha256(manifest_payload).hexdigest()
    manifest_path = (
        root / "manifests" / f"MANIFEST_2026-08-12_{manifest_hash[:16]}.json"
    )
    _write(manifest_path, manifest_payload)
    return manifest_path


def _load_signal(roots: dict[str, Path]) -> dict:
    actuals, _ = load_actual_evidence(roots["consensus_and_actual"])
    markets, _ = load_market_evidence(roots["event_market"])
    ownerships, _ = load_ownership_evidence(roots["neutral_ownership"])
    signals, _ = build_signal_ledger(actuals, markets, ownerships)
    assert len(signals) == 1
    return signals.iloc[0].to_dict()


def test_market_loader_injects_required_manifest_and_snapshot_hashes(
    tmp_path: Path,
) -> None:
    roots = _roots(tmp_path)
    _write_market(roots["event_market"])
    frame, census = load_market_evidence(roots["event_market"])
    assert len(frame) == 1
    assert len(frame["market_manifest_sha256"].iloc[0]) == 64
    assert len(frame["market_snapshot_sha256"].iloc[0]) == 64
    assert census["complete_market_rows"] == 1


def test_end_to_end_process_is_append_only_and_idempotent(
    tmp_path: Path,
) -> None:
    roots = _roots(tmp_path)
    _write_actual(roots["consensus_and_actual"])
    _write_market(roots["event_market"])
    _write_ownership(roots["neutral_ownership"])
    signal = _load_signal(roots)
    _write_path(roots["trade_path"], signal["signal_id"])

    first = process_campaign(
        evaluated_at_utc="2026-08-13T01:00:00Z",
        roots=roots,
        persist=True,
    )
    signal_files = list(roots["ledger"].glob("signals/records/*.json"))
    trade_files = list(roots["ledger"].glob("trades/records/*.json"))
    second = process_campaign(
        evaluated_at_utc="2026-08-13T01:00:00Z",
        roots=roots,
        persist=True,
    )
    assert first["routed_status_counts"] == {"CLOSED": 1}
    assert first["admission"]["closed_trades"] == 1
    assert len(signal_files) == 1
    assert len(trade_files) == 1
    assert len(list(roots["ledger"].glob("signals/records/*.json"))) == 1
    assert len(list(roots["ledger"].glob("trades/records/*.json"))) == 1
    assert first["process_manifest_sha256"] == (second["process_manifest_sha256"])
    assert first["network_request_made"] is False
    assert first["broker_action_allowed"] is False


def test_later_contradictory_actual_and_market_revisions_cannot_change_trade(
    tmp_path: Path,
) -> None:
    roots = _roots(tmp_path)
    _write_actual(roots["consensus_and_actual"])
    _write_market(roots["event_market"])
    _write_ownership(roots["neutral_ownership"])
    signal = _load_signal(roots)
    assert signal["side"] == "LONG"
    _write_path(roots["trade_path"], signal["signal_id"])

    first = process_campaign(
        evaluated_at_utc="2026-08-13T01:00:00Z",
        roots=roots,
        persist=True,
    )
    signal_payloads = {
        path.name: path.read_bytes()
        for path in roots["ledger"].glob("signals/records/*.json")
    }
    trade_payloads = {
        path.name: path.read_bytes()
        for path in roots["ledger"].glob("trades/records/*.json")
    }

    late_actual = _write_actual(
        roots["consensus_and_actual"],
        suffix="actual_late_short_revision",
        actual_value=0.4,
        actual_observed_at="2026-08-12T12:40:00Z",
    )
    late_market = _write_market(
        roots["event_market"],
        suffix="market_late_short_revision",
        market_observed_at="2026-08-12T12:55:00Z",
        eurusd_post_mid=1.0990,
        dxy_post_mid=100.2,
        treasury_post_mid=109.8,
    )
    assert late_actual["macro_side"].iloc[0] == "SHORT"
    assert late_market["eurusd_post_mid"].iloc[0] < late_market["eurusd_pre_mid"].iloc[0]
    assert late_market["dxy_post_mid"].iloc[0] > late_market["dxy_pre_mid"].iloc[0]
    assert (
        late_market["treasury_post_mid"].iloc[0]
        < late_market["treasury_pre_mid"].iloc[0]
    )

    second = process_campaign(
        evaluated_at_utc="2026-08-13T01:00:00Z",
        roots=roots,
        persist=True,
    )
    assert first["routed_status_counts"] == second["routed_status_counts"] == {
        "CLOSED": 1
    }
    assert second["evidence_census"]["actual_rows"] == 2
    assert second["evidence_census"]["complete_market_rows"] == 2
    assert second["signal_census"]["selected_actual_events"] == 1
    assert second["signal_census"]["complete_market_events"] == 1
    assert first["evidence_inventory_sha256"] != second["evidence_inventory_sha256"]
    assert first["process_manifest_sha256"] != second["process_manifest_sha256"]
    assert {
        path.name: path.read_bytes()
        for path in roots["ledger"].glob("signals/records/*.json")
    } == signal_payloads
    assert {
        path.name: path.read_bytes()
        for path in roots["ledger"].glob("trades/records/*.json")
    } == trade_payloads


def test_cash_signal_persists_without_any_path(tmp_path: Path) -> None:
    roots = _roots(tmp_path)
    _write_actual(roots["consensus_and_actual"])
    _write_market(roots["event_market"])
    _write_ownership(roots["neutral_ownership"], neutral=False)
    result = process_campaign(
        evaluated_at_utc="2026-08-13T01:00:00Z",
        roots=roots,
        persist=True,
    )
    assert result["routed_status_counts"] == {"CASH_NO_TRADE": 1}
    assert result["evidence_census"]["complete_paths"] == 0
    assert len(list(roots["ledger"].glob("trades/records/*.json"))) == 1


def test_pending_prior_path_blocks_later_non_cash_signal(
    tmp_path: Path,
) -> None:
    roots = _roots(tmp_path)
    _write_actual(roots["consensus_and_actual"])
    _write_market(roots["event_market"])
    _write_ownership(roots["neutral_ownership"])
    first = _load_signal(roots)
    second = {
        **first,
        "signal_id": "b" * 64,
        "event_time_utc": pd.Timestamp("2026-08-12T13:30:00Z"),
        "entry_time_utc": pd.Timestamp("2026-08-12T13:50:00Z"),
    }
    routed = route_operational_signals(pd.DataFrame([first, second]), {})
    assert routed["status"].tolist() == [
        "PENDING_COMPLETE_PATH_NOT_AVAILABLE",
        "BLOCKED_PRIOR_POSITION_OUTCOME_PENDING",
    ]


def test_position_overlap_is_terminally_skipped(tmp_path: Path) -> None:
    roots = _roots(tmp_path)
    _write_actual(roots["consensus_and_actual"])
    _write_market(roots["event_market"])
    _write_ownership(roots["neutral_ownership"])
    first = _load_signal(roots)
    second = {
        **first,
        "signal_id": "b" * 64,
        "event_time_utc": pd.Timestamp("2026-08-12T13:30:00Z"),
        "entry_time_utc": pd.Timestamp("2026-08-12T13:50:00Z"),
    }
    paths = {
        first["signal_id"]: {
            "frame": _path_frame(),
            "entry_time_utc": first["entry_time_utc"],
            "path_evidence_sha256": "d" * 64,
            "path_manifest_sha256": "e" * 64,
        }
    }
    routed = route_operational_signals(pd.DataFrame([first, second]), paths)
    assert routed["status"].tolist() == [
        "CLOSED",
        "SKIPPED_POSITION_ALREADY_OPEN",
    ]


def test_tampered_market_snapshot_fails_closed(tmp_path: Path) -> None:
    roots = _roots(tmp_path)
    frame = _write_market(roots["event_market"])
    frame["eurusd_post_mid"] = 9.0
    frame.to_parquet(
        roots["event_market"] / "normalized/market.parquet",
        index=False,
    )
    with pytest.raises(RuntimeError, match="hash drift"):
        load_market_evidence(roots["event_market"])


def test_existing_signal_cannot_be_replaced_by_another_event_revision(
    tmp_path: Path,
) -> None:
    roots = _roots(tmp_path)
    _write_actual(roots["consensus_and_actual"])
    _write_market(roots["event_market"])
    _write_ownership(roots["neutral_ownership"])
    original = _load_signal(roots)
    reconcile_signal_records(
        pd.DataFrame([original]),
        roots["ledger"],
        persist=True,
    )
    replacement = {**original, "signal_id": "b" * 64}
    with pytest.raises(RuntimeError, match="cannot be reconstructed"):
        reconcile_signal_records(
            pd.DataFrame([replacement]),
            roots["ledger"],
            persist=False,
        )


def test_empty_campaign_reports_prospective_start_before_capture_gap(
    tmp_path: Path,
) -> None:
    result = process_campaign(
        evaluated_at_utc="2026-07-28T23:00:00Z",
        roots=_roots(tmp_path),
        persist=False,
    )
    assert result["status"] == "WAITING_FOR_PROSPECTIVE_START"
    assert result["network_request_made"] is False


def test_oracle_loader_withholds_labels_until_their_safe_known_time(
    tmp_path: Path,
) -> None:
    roots = _roots(tmp_path)
    _write_oracle(
        roots["oracle_evaluation"],
        roots["neutral_ownership"],
    )
    early, early_dates, early_census = load_oracle_evidence(
        roots["oracle_evaluation"],
        roots["neutral_ownership"],
        evaluated_at_utc="2026-08-13T12:01:00Z",
    )
    assert early.empty
    assert early_dates == set()
    assert early_census["oracle_dates_not_yet_known"] == 1

    labels, dates, census = load_oracle_evidence(
        roots["oracle_evaluation"],
        roots["neutral_ownership"],
        evaluated_at_utc="2026-08-13T12:01:01Z",
    )
    assert len(labels) == 4
    assert dates == {"2026-08-12"}
    assert census["oracle_dates_known_as_of"] == 1
    assert census["neutral_oracle_label_rows_known_as_of"] == 4


def test_completed_unavailable_oracle_date_labels_closed_trade_false() -> None:
    routed = pd.DataFrame(
        [
            {
                "signal_id": "a" * 64,
                "status": "CLOSED",
                "entry_time_utc": pd.Timestamp("2026-08-12T12:50:00Z"),
                "side": "LONG",
            },
            {
                "signal_id": "b" * 64,
                "status": "CLOSED",
                "entry_time_utc": pd.Timestamp("2026-08-13T12:50:00Z"),
                "side": "LONG",
            },
            {
                "signal_id": "c" * 64,
                "status": "CASH_NO_TRADE",
                "entry_time_utc": pd.Timestamp("2026-08-12T14:00:00Z"),
                "side": "CASH",
            },
        ]
    )
    labels = pd.DataFrame(
        [
            {
                "oracle_date": "2026-08-12",
                "side": "LONG",
                "regime": "NEUTRAL",
                "oracle_label_known_time_utc": pd.Timestamp("2026-08-14T00:00:00Z"),
            }
        ]
    )
    labeled = attach_completed_oracle_labels(
        routed,
        labels,
        {"2026-08-12", "2026-08-13"},
        evaluated_at_utc="2026-08-14T00:00:00Z",
    )
    assert labeled["oracle_same_day_same_side"].iloc[0] == True
    assert labeled["oracle_same_day_same_side"].iloc[1] == False
    assert pd.isna(labeled["oracle_same_day_same_side"].iloc[2])


def test_oracle_labels_never_change_persisted_signals_or_trades(
    tmp_path: Path,
) -> None:
    roots = _roots(tmp_path)
    _write_actual(roots["consensus_and_actual"])
    _write_market(roots["event_market"])
    _write_ownership(roots["neutral_ownership"])
    signal = _load_signal(roots)
    _write_path(roots["trade_path"], signal["signal_id"])

    before = process_campaign(
        evaluated_at_utc="2026-08-13T01:00:00Z",
        roots=roots,
        persist=True,
    )
    signal_records = list(roots["ledger"].glob("signals/records/*.json"))
    trade_records = list(roots["ledger"].glob("trades/records/*.json"))
    signal_payloads = {path.name: path.read_bytes() for path in signal_records}
    trade_payloads = {path.name: path.read_bytes() for path in trade_records}
    assert before["admission"]["oracle_same_day_same_side_precision"] is None

    _write_oracle(
        roots["oracle_evaluation"],
        roots["neutral_ownership"],
    )
    after = process_campaign(
        evaluated_at_utc="2026-08-14T00:00:00Z",
        roots=roots,
        persist=True,
    )
    assert {
        path.name: path.read_bytes()
        for path in roots["ledger"].glob("signals/records/*.json")
    } == signal_payloads
    assert {
        path.name: path.read_bytes()
        for path in roots["ledger"].glob("trades/records/*.json")
    } == trade_payloads
    assert after["admission"]["oracle_same_day_same_side_precision"] == 1.0
    assert after["oracle_evaluation"]["closed_trades_with_known_oracle_date"] == 1
    for payload in [*signal_payloads.values(), *trade_payloads.values()]:
        assert b"oracle_same_day_same_side" not in payload


def test_tampered_oracle_labels_fail_closed(tmp_path: Path) -> None:
    roots = _roots(tmp_path)
    manifest_path = _write_oracle(
        roots["oracle_evaluation"],
        roots["neutral_ownership"],
    )
    manifest = json.loads(manifest_path.read_bytes())
    labels_path = (
        roots["oracle_evaluation"] / manifest["oracle_labels"]["relative_path"]
    )
    labels = pd.read_parquet(labels_path)
    labels.loc[0, "side"] = "SHORT"
    labels.to_parquet(labels_path, index=False)
    with pytest.raises(RuntimeError, match="hash drift"):
        load_oracle_evidence(
            roots["oracle_evaluation"],
            roots["neutral_ownership"],
            evaluated_at_utc="2026-08-14T00:00:00Z",
        )
