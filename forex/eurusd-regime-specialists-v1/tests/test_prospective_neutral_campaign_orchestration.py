from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from eurusd_regime_specialists.prospective_neutral_campaign_orchestration import (
    load_actual_evidence,
    load_market_evidence,
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
                item.isoformat()
                if isinstance(item, pd.Timestamp)
                else str(item)
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
        "ledger": tmp_path / "ledger",
    }
    for root in roots.values():
        root.mkdir(parents=True)
    return roots


def _write_actual(root: Path) -> pd.DataFrame:
    forecast_relative = "raw/forecast.json"
    actual_relative = "post_release_raw/actual.json"
    metadata_relative = "post_release_metadata/actual.json"
    forecast_hash = _write(root / forecast_relative, b"forecast")
    actual_hash = _write(root / actual_relative, b"actual")
    metadata_hash = _write(root / metadata_relative, b"metadata")
    frame = pd.DataFrame(
        [
            {
                "family": "CPI",
                "event_time_utc": pd.Timestamp(
                    "2026-08-12T12:30:00Z"
                ),
                "forecast_value": 0.2,
                "forecast_observed_at_utc": pd.Timestamp(
                    "2026-08-12T11:00:00Z"
                ),
                "forecast_lead_seconds": 5400.0,
                "forecast_raw_snapshot_relative_path": (
                    forecast_relative
                ),
                "forecast_raw_snapshot_sha256": forecast_hash,
                "tradingview_event_id": "event-1",
                "tradingview_ticker": "ECONOMICS:USCPI",
                "actual_value": 0.1,
                "actual_observed_at_utc": pd.Timestamp(
                    "2026-08-12T12:32:00Z"
                ),
                "actual_lag_seconds": 120.0,
                "actual_raw_snapshot_relative_path": actual_relative,
                "actual_raw_snapshot_sha256": actual_hash,
                "surprise_value": -0.1,
                "macro_side": "LONG",
                "capture_semantics": ACTUAL_SEMANTICS,
            }
        ]
    )
    normalized_relative = "post_release_normalized/actual.parquet"
    normalized_path = root / normalized_relative
    normalized_path.parent.mkdir(parents=True)
    frame.to_parquet(normalized_path, index=False)
    normalized_hash = hashlib.sha256(
        normalized_path.read_bytes()
    ).hexdigest()
    manifest = {
        "schema_version": (
            "eurusd_neutral_prospective_actual_snapshot_v1"
        ),
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
        root / "post_release_manifests/MANIFEST_actual.json",
        _json_bytes(manifest),
    )
    return frame


def _market_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_time_utc": pd.Timestamp(
                    "2026-08-12T12:30:00Z"
                ),
                "observation_start_utc": pd.Timestamp(
                    "2026-08-12T12:30:00Z"
                ),
                "observation_completed_at_utc": pd.Timestamp(
                    "2026-08-12T12:45:00Z"
                ),
                "market_observed_at_utc": pd.Timestamp(
                    "2026-08-12T12:46:01Z"
                ),
                "eurusd_pre_mid": 1.1000,
                "eurusd_post_mid": 1.1010,
                "eurusd_observation_mid_high": 1.1012,
                "eurusd_observation_mid_low": 1.0998,
                "dxy_pre_mid": 100.0,
                "dxy_post_mid": 99.8,
                "treasury_pre_mid": 110.0,
                "treasury_post_mid": 110.2,
                "capture_semantics": MARKET_SEMANTICS,
            }
        ]
    )


def _write_market(root: Path) -> pd.DataFrame:
    raw_relative = "raw/EURUSD/hour.json"
    metadata_relative = "metadata/EURUSD/hour.json"
    raw_hash = _write(root / raw_relative, b"market raw")
    metadata_hash = _write(root / metadata_relative, b"market metadata")
    frame = _market_frame()
    normalized_relative = "normalized/market.parquet"
    normalized_path = root / normalized_relative
    normalized_path.parent.mkdir(parents=True)
    frame.to_parquet(normalized_path, index=False)
    normalized_hash = hashlib.sha256(
        normalized_path.read_bytes()
    ).hexdigest()
    manifest = {
        "schema_version": (
            "eurusd_neutral_prospective_event_market_m5_v1"
        ),
        "event_time_utc": "2026-08-12T12:30:00Z",
        "market_observed_at_utc": "2026-08-12T12:46:01Z",
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
        root / "manifests/MANIFEST_market.json",
        _json_bytes(manifest),
    )
    return frame


def _write_ownership(root: Path, *, neutral: bool = True) -> dict:
    record = build_neutral_ownership_record(
        eligible_date="2026-08-12T00:00:00Z",
        state_timestamp_utc="2026-08-11T23:00:00Z",
        ownership_observed_at_utc="2026-08-12T00:02:00Z",
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
    record_relative = (
        f"records/2026-08-12_{evidence_hash[:16]}.json"
    )
    record_hash = _write(root / record_relative, _json_bytes(record))
    manifest = {
        "schema_version": "eurusd_prospective_neutral_ownership_v1",
        "eligible_date": "2026-08-12T00:00:00+00:00",
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
        root
        / "manifests"
        / f"MANIFEST_2026-08-12_{manifest_hash[:16]}.json",
        manifest_payload,
    )
    return record


def _path_frame() -> pd.DataFrame:
    index = pd.date_range(
        "2026-08-12T12:50:00Z", periods=144, freq="5min"
    )
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
    normalized_hash = hashlib.sha256(
        normalized_path.read_bytes()
    ).hexdigest()
    manifest = {
        "schema_version": (
            "eurusd_neutral_prospective_trade_path_v2"
        ),
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


def _load_signal(roots: dict[str, Path]) -> dict:
    actuals, _ = load_actual_evidence(roots["consensus_and_actual"])
    markets, _ = load_market_evidence(roots["event_market"])
    ownerships, _ = load_ownership_evidence(
        roots["neutral_ownership"]
    )
    signals, _ = build_signal_ledger(
        actuals, markets, ownerships
    )
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
    signal_files = list(
        roots["ledger"].glob("signals/records/*.json")
    )
    trade_files = list(
        roots["ledger"].glob("trades/records/*.json")
    )
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
    assert first["process_manifest_sha256"] == (
        second["process_manifest_sha256"]
    )
    assert first["network_request_made"] is False
    assert first["broker_action_allowed"] is False


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
    assert len(
        list(roots["ledger"].glob("trades/records/*.json"))
    ) == 1


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
    routed = route_operational_signals(
        pd.DataFrame([first, second]), {}
    )
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
    routed = route_operational_signals(
        pd.DataFrame([first, second]), paths
    )
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
