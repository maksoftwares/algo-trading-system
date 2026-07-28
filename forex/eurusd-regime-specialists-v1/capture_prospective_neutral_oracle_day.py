from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from capture_prospective_dukascopy_event_m5 import (
    build_completed_m5,
    decode_ticks,
    fetch_hour,
)

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.prospective_neutral_oracle_evaluation import (
    build_daily_perfect_oracle,
    load_config,
    load_next_day_context,
    oracle_capture_ready,
    required_oracle_hours,
    verify_lock,
)
from eurusd_regime_specialists.research import sha256_file

DEFAULT_ORACLE_ROOT = Path(
    "D:/AlgoTradingData/prospective/eurusd-neutral-macro-crossasset-agreement-v1/oracle"
)
DEFAULT_OWNERSHIP_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-macro-crossasset-agreement-v1/ownership"
)
SCHEMA_VERSION = "eurusd_neutral_prospective_oracle_day_v1"
LABEL_COLUMNS = [
    "oracle_date",
    "oracle_trade_number",
    "side",
    "entry_time_utc",
    "exit_time_utc",
    "exit_reason",
    "nominal_target_r",
    "risk_tier_pips",
    "fallback_risk_tier",
    "entry_price",
    "stop_price",
    "target_price",
    "exit_price",
    "r",
    "fixed_0p01_lot_usd",
    "risk_distance",
    "risk_pips",
    "state_time_utc",
    "matched_state_time_utc",
    "direction",
    "shock",
    "DXY_compressed",
    "EURUSD_compressed",
    "regime",
    "regime_definition",
    "oracle_label_known_time_utc",
    "oracle_date_complete",
    "market_inventory_sha256",
    "ownership_manifest_sha256",
]


def _utc(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware")
    return timestamp.tz_convert("UTC").as_unit("ns")


def _day(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    if timestamp != timestamp.floor("D"):
        raise ValueError("Oracle date must be UTC midnight")
    return timestamp.as_unit("ns")


def _serialize(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Mapping):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(_serialize(value), indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _write_immutable(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise RuntimeError(f"Refusing to overwrite oracle evidence: {path}")


def _safe_path(root: Path, value: Any) -> Path:
    relative = Path(str(value))
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError("Oracle evidence path escapes its root")
    root_resolved = root.resolve()
    path = (root / relative).resolve()
    if path != root_resolved and root_resolved not in path.parents:
        raise RuntimeError("Oracle evidence path escapes its root")
    return path


def _verified_reference(
    root: Path,
    reference: Mapping[str, Any],
    label: str,
) -> tuple[Path, str]:
    path = _safe_path(root, reference["relative_path"])
    expected = str(reference["sha256"]).lower()
    if len(expected) != 64:
        raise RuntimeError(f"{label} hash is invalid")
    if not path.is_file() or sha256_file(path) != expected:
        raise RuntimeError(f"{label} hash drift")
    return path, expected


def _existing_capture(
    oracle_root: Path,
    oracle_date: pd.Timestamp,
) -> dict[str, Any] | None:
    manifests = sorted(
        oracle_root.glob(f"manifests/MANIFEST_{oracle_date:%Y-%m-%d}_*.json")
    )
    if not manifests:
        return None
    if len(manifests) != 1:
        raise RuntimeError("Oracle date has multiple immutable manifests")
    manifest_path = manifests[0]
    payload = manifest_path.read_bytes()
    manifest_hash = _sha256_bytes(payload)
    if manifest_path.name != (
        f"MANIFEST_{oracle_date:%Y-%m-%d}_{manifest_hash[:16]}.json"
    ):
        raise RuntimeError("Oracle manifest name/hash drift")
    manifest = json.loads(payload)
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise RuntimeError("Unexpected oracle manifest schema")
    if manifest.get("broker_action_allowed") is not False:
        raise RuntimeError("Oracle broker boundary drift")
    for row in manifest["raw_snapshots"]:
        _verified_reference(
            oracle_root,
            {
                "relative_path": row["raw_relative_path"],
                "sha256": row["raw_sha256"],
            },
            "Oracle raw snapshot",
        )
        _verified_reference(
            oracle_root,
            {
                "relative_path": row["metadata_relative_path"],
                "sha256": row["metadata_sha256"],
            },
            "Oracle metadata",
        )
    market_path, market_hash = _verified_reference(
        oracle_root,
        manifest["normalized_market"],
        "Oracle normalized market",
    )
    labels_path, labels_hash = _verified_reference(
        oracle_root,
        manifest["oracle_labels"],
        "Oracle label snapshot",
    )
    market = pd.read_parquet(market_path)
    labels = pd.read_parquet(labels_path)
    if len(market) != int(manifest["normalized_market"]["rows"]) or len(labels) != int(
        manifest["oracle_labels"]["rows"]
    ):
        raise RuntimeError("Oracle existing row-count drift")
    return {
        "status": str(manifest["status"]),
        "oracle_date": oracle_date,
        "oracle_rows": len(labels),
        "neutral_oracle_rows": (
            int(labels["regime"].eq("NEUTRAL").sum()) if len(labels) else 0
        ),
        "oracle_label_known_time_utc": manifest["oracle_label_known_time_utc"],
        "normalized_market_sha256": market_hash,
        "oracle_labels_sha256": labels_hash,
        "manifest_relative_path": manifest_path.relative_to(oracle_root).as_posix(),
        "manifest_sha256": manifest_hash,
        "network_request_made": False,
        "historical_pnl_loaded": False,
        "broker_action_allowed": False,
    }


def capture_oracle_date(
    oracle_date: Any,
    oracle_root: Path = DEFAULT_ORACLE_ROOT,
    ownership_root: Path = DEFAULT_OWNERSHIP_ROOT,
    *,
    now_utc: Any | None = None,
    fetcher: Callable[[str, pd.Timestamp], tuple[bytes, dict[str, Any]]] = fetch_hour,
) -> dict[str, Any]:
    day = _day(oracle_date)
    cfg = load_config()
    if day < _utc(cfg["prospective_start_utc"]):
        raise ValueError("Oracle date precedes prospective start")
    observed = (
        pd.Timestamp.now(tz="UTC").as_unit("ns") if now_utc is None else _utc(now_utc)
    )
    if day.weekday() >= 5:
        return _serialize(
            {
                "status": "ORACLE_DATE_NOT_WEEKDAY",
                "oracle_date": day,
                "network_request_made": False,
                "historical_pnl_loaded": False,
                "broker_action_allowed": False,
            }
        )
    existing = _existing_capture(oracle_root, day)
    if existing is not None:
        return _serialize(existing)
    earliest = day + pd.Timedelta(hours=36, seconds=60)
    if not oracle_capture_ready(day, observed):
        return _serialize(
            {
                "status": "WAITING_FOR_ORACLE_DAY_COMPLETION",
                "oracle_date": day,
                "earliest_capture_utc": earliest,
                "network_request_made": False,
                "historical_pnl_loaded": False,
                "broker_action_allowed": False,
            }
        )
    try:
        state, context = load_next_day_context(ownership_root, day)
    except FileNotFoundError:
        return _serialize(
            {
                "status": "WAITING_FOR_NEXT_DAY_OWNERSHIP_CONTEXT",
                "oracle_date": day,
                "required_ownership_date": day + pd.Timedelta(days=1),
                "network_request_made": False,
                "historical_pnl_loaded": False,
                "broker_action_allowed": False,
            }
        )

    raw_records: list[dict[str, Any]] = []
    tick_frames: list[pd.DataFrame] = []
    for hour in required_oracle_hours(day):
        payload, metadata = fetcher("EURUSD", hour)
        if str(metadata.get("symbol")) != "EURUSD":
            raise RuntimeError("Oracle fetch returned another symbol")
        if _utc(metadata.get("hour_utc")) != hour:
            raise RuntimeError("Oracle fetch returned another hour")
        item_observed = _utc(metadata["observed_at_utc"])
        raw_hash = _sha256_bytes(payload)
        stem = f"{hour:%Y%m%dT%H0000Z}_{item_observed:%Y%m%dT%H%M%SZ}_{raw_hash[:16]}"
        raw_relative = Path("raw") / f"{day:%Y-%m-%d}" / f"{stem}.json"
        metadata_relative = Path("metadata") / f"{day:%Y-%m-%d}" / f"{stem}.json"
        raw_path = oracle_root / raw_relative
        metadata_path = oracle_root / metadata_relative
        _write_immutable(raw_path, payload)
        stored_metadata = {
            "schema_version": SCHEMA_VERSION,
            "oracle_date": day,
            **metadata,
            "raw_relative_path": raw_relative,
            "raw_sha256": raw_hash,
            "broker_action_allowed": False,
        }
        _write_immutable(metadata_path, _json_bytes(stored_metadata))
        ticks = decode_ticks(payload, "EURUSD", hour)
        tick_frames.append(ticks)
        raw_records.append(
            {
                "hour_utc": hour,
                "observed_at_utc": item_observed,
                "raw_relative_path": raw_relative,
                "raw_sha256": raw_hash,
                "metadata_relative_path": metadata_relative,
                "metadata_sha256": sha256_file(metadata_path),
                "tick_count": len(ticks),
            }
        )
    market_observed = max(row["observed_at_utc"] for row in raw_records)
    if market_observed < earliest:
        raise RuntimeError("Fetched oracle market evidence predates safe known time")
    all_ticks = (
        pd.concat(tick_frames, ignore_index=True) if tick_frames else pd.DataFrame()
    )
    market = build_completed_m5(all_ticks, market_observed)
    market["timestamp_utc"] = pd.to_datetime(
        market["timestamp_utc"], utc=True
    ).dt.as_unit("ns")
    market = (
        market[
            market["timestamp_utc"].ge(day)
            & market["timestamp_utc"].lt(day + pd.Timedelta(hours=36))
        ]
        .sort_values("timestamp_utc")
        .reset_index(drop=True)
    )
    if market["timestamp_utc"].duplicated().any():
        raise RuntimeError("Oracle market contains duplicate M5 bars")
    inventory_hash = _sha256_bytes(
        json.dumps(
            _serialize(raw_records),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    oracle, census = build_daily_perfect_oracle(market, state, day)
    label_known = max(
        earliest,
        market_observed,
        _utc(context["ownership_observed_at_utc"]),
    )
    if oracle.empty:
        labels = pd.DataFrame(columns=LABEL_COLUMNS)
    else:
        labels = oracle.copy()
        labels["oracle_label_known_time_utc"] = label_known
        labels["oracle_date_complete"] = True
        labels["market_inventory_sha256"] = inventory_hash
        labels["ownership_manifest_sha256"] = context["ownership_manifest_sha256"]
        labels = labels[LABEL_COLUMNS]
    market_relative = (
        Path("normalized") / f"EURUSD_{day:%Y-%m-%d}_{inventory_hash[:16]}.parquet"
    )
    labels_relative = (
        Path("labels") / f"ORACLE_{day:%Y-%m-%d}_{inventory_hash[:16]}.parquet"
    )
    market_path = oracle_root / market_relative
    labels_path = oracle_root / labels_relative
    market_path.parent.mkdir(parents=True, exist_ok=True)
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    if market_path.exists():
        pd.testing.assert_frame_equal(
            pd.read_parquet(market_path).reset_index(drop=True),
            market.reset_index(drop=True),
            check_dtype=False,
        )
    else:
        market.to_parquet(market_path, index=False, compression="zstd")
    if labels_path.exists():
        pd.testing.assert_frame_equal(
            pd.read_parquet(labels_path).reset_index(drop=True),
            labels.reset_index(drop=True),
            check_dtype=False,
        )
    else:
        labels.to_parquet(labels_path, index=False, compression="zstd")
    status = (
        "ORACLE_DATE_COMPLETE"
        if census["status"] == "ORACLE_COMPLETE"
        else "ORACLE_DATE_COMPLETE_UNAVAILABLE"
    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "oracle_date": day,
        "oracle_label_known_time_utc": label_known,
        "raw_snapshots": raw_records,
        "market_inventory_sha256": inventory_hash,
        "normalized_market": {
            "relative_path": market_relative,
            "sha256": sha256_file(market_path),
            "rows": len(market),
        },
        "oracle_labels": {
            "relative_path": labels_relative,
            "sha256": sha256_file(labels_path),
            "rows": len(labels),
            "neutral_rows": (
                int(labels["regime"].eq("NEUTRAL").sum()) if len(labels) else 0
            ),
        },
        "next_day_context": context,
        "oracle_census": census,
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
    manifest_hash = _sha256_bytes(manifest_payload)
    manifest_relative = (
        Path("manifests") / f"MANIFEST_{day:%Y-%m-%d}_{manifest_hash[:16]}.json"
    )
    manifest_path = oracle_root / manifest_relative
    _write_immutable(manifest_path, manifest_payload)
    return _serialize(
        {
            "status": status,
            "oracle_date": day,
            "oracle_rows": len(labels),
            "neutral_oracle_rows": (
                int(labels["regime"].eq("NEUTRAL").sum()) if len(labels) else 0
            ),
            "oracle_label_known_time_utc": label_known,
            "normalized_market_sha256": sha256_file(market_path),
            "oracle_labels_sha256": sha256_file(labels_path),
            "manifest_relative_path": manifest_relative,
            "manifest_sha256": manifest_hash,
            "network_request_made": True,
            "historical_pnl_loaded": False,
            "broker_action_allowed": False,
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("capture",))
    parser.add_argument("--oracle-date", required=True)
    parser.add_argument("--oracle-root", type=Path, default=DEFAULT_ORACLE_ROOT)
    parser.add_argument(
        "--ownership-root",
        type=Path,
        default=DEFAULT_OWNERSHIP_ROOT,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    verify_lock()
    result = capture_oracle_date(
        args.oracle_date,
        args.oracle_root,
        args.ownership_root,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
