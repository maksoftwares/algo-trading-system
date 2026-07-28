from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from capture_prospective_dukascopy_event_m5 import (
    _serialize,
    _utc,
    build_completed_m5,
    decode_ticks,
    fetch_hour,
    sha256_bytes,
    sha256_file,
    write_immutable,
)


DEFAULT_OUTPUT_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-macro-crossasset-agreement-v1/path"
)
SCHEMA_VERSION = "eurusd_neutral_prospective_trade_path_v2"
MAXIMUM_HOLD_HOURS = 12
MINIMUM_CAPTURE_LAG_SECONDS = 60


def required_path_hours(
    entry_time_utc: Any,
    *,
    maximum_hold_hours: int = MAXIMUM_HOLD_HOURS,
) -> list[pd.Timestamp]:
    entry = _utc(entry_time_utc)
    deadline = entry + pd.Timedelta(hours=maximum_hold_hours)
    first = entry.floor("h")
    last = (deadline - pd.Timedelta(nanoseconds=1)).floor("h")
    return list(pd.date_range(first, last, freq="h"))


def path_capture_ready(
    entry_time_utc: Any,
    observed_at_utc: Any,
    *,
    maximum_hold_hours: int = MAXIMUM_HOLD_HOURS,
    minimum_lag_seconds: int = MINIMUM_CAPTURE_LAG_SECONDS,
) -> bool:
    entry = _utc(entry_time_utc)
    observed = _utc(observed_at_utc)
    deadline = entry + pd.Timedelta(hours=maximum_hold_hours)
    return observed >= deadline + pd.Timedelta(
        seconds=minimum_lag_seconds
    )


def _valid_signal_id(value: str) -> str:
    normalized = str(value).lower()
    if len(normalized) != 64:
        raise ValueError("signal-id must be a SHA-256")
    try:
        bytes.fromhex(normalized)
    except ValueError as error:
        raise ValueError("signal-id must be a SHA-256") from error
    return normalized


def _evidence_chain(output_root: Path) -> str:
    digest = hashlib.sha256()
    paths = sorted(
        [
            *output_root.glob("raw/**/*.json"),
            *output_root.glob("metadata/**/*.json"),
            *output_root.glob("normalized/*.parquet"),
        ],
        key=lambda path: path.relative_to(output_root).as_posix(),
    )
    for path in paths:
        digest.update(
            path.relative_to(output_root).as_posix().encode("utf-8")
        )
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def _existing_complete(
    output_root: Path,
    signal_id: str,
) -> dict[str, Any] | None:
    manifests = sorted(
        output_root.glob(f"manifests/MANIFEST_{signal_id}_*.json")
    )
    for path in reversed(manifests):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if (
            payload.get("status") == "COMPLETE"
            and payload.get("signal_id") == signal_id
        ):
            normalized = payload["normalized_snapshot"]
            normalized_path = (
                output_root / normalized["relative_path"]
            )
            if (
                not normalized_path.exists()
                or sha256_file(normalized_path) != normalized["sha256"]
            ):
                raise RuntimeError(
                    "Existing normalized trade path evidence drift"
                )
            for row in payload["raw_snapshots"]:
                raw_path = output_root / row["raw_relative_path"]
                metadata_path = (
                    output_root / row["metadata_relative_path"]
                )
                if (
                    sha256_file(raw_path) != row["raw_sha256"]
                    or sha256_file(metadata_path)
                    != row["metadata_sha256"]
                ):
                    raise RuntimeError(
                        "Existing raw trade path evidence drift"
                    )
            return {
                "status": "TRADE_PATH_CAPTURED",
                "signal_id": signal_id,
                "entry_time_utc": payload["entry_time_utc"],
                "deadline_utc": payload["deadline_utc"],
                "path_rows": payload["normalized_snapshot"]["rows"],
                "path_evidence_sha256": payload[
                    "normalized_snapshot"
                ]["sha256"],
                "manifest_relative_path": path.relative_to(
                    output_root
                ).as_posix(),
                "manifest_sha256": sha256_file(path),
                "path_evidence_chain_sha256": payload[
                    "path_evidence_chain_sha256"
                ],
                "network_request_made": False,
                "broker_action_allowed": False,
            }
    return None


def capture_trade_path(
    signal_id: str,
    entry_time_utc: Any,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    now_utc: Any | None = None,
    fetcher: Callable[
        [str, pd.Timestamp], tuple[bytes, dict[str, Any]]
    ] = fetch_hour,
) -> dict[str, Any]:
    signal = _valid_signal_id(signal_id)
    entry = _utc(entry_time_utc)
    deadline = entry + pd.Timedelta(hours=MAXIMUM_HOLD_HOURS)
    observed = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if now_utc is None
        else _utc(now_utc)
    )
    existing = _existing_complete(output_root, signal)
    if existing is not None:
        if _utc(existing["entry_time_utc"]) != entry:
            raise RuntimeError("Existing signal path has another entry time")
        return existing
    if not path_capture_ready(entry, observed):
        return {
            "status": "WAITING_FOR_12H_PATH_COMPLETION",
            "signal_id": signal,
            "entry_time_utc": entry,
            "deadline_utc": deadline,
            "earliest_capture_utc": (
                deadline
                + pd.Timedelta(seconds=MINIMUM_CAPTURE_LAG_SECONDS)
            ),
            "network_request_made": False,
            "broker_action_allowed": False,
        }

    raw_records: list[dict[str, Any]] = []
    tick_frames: list[pd.DataFrame] = []
    for hour in required_path_hours(entry):
        payload, metadata = fetcher("EURUSD", hour)
        if str(metadata.get("symbol")) != "EURUSD":
            raise RuntimeError("Trade path fetch returned another symbol")
        if _utc(metadata.get("hour_utc")) != hour:
            raise RuntimeError("Trade path fetch returned another hour")
        raw_hash = sha256_bytes(payload)
        raw_relative = (
            Path("raw")
            / signal
            / f"{hour:%Y%m%dT%H0000Z}_{raw_hash[:16]}.json"
        )
        metadata_relative = (
            Path("metadata")
            / signal
            / f"{hour:%Y%m%dT%H0000Z}_{raw_hash[:16]}.json"
        )
        raw_path = output_root / raw_relative
        metadata_path = output_root / metadata_relative
        write_immutable(raw_path, payload)
        metadata_payload = {
            "schema_version": SCHEMA_VERSION,
            "signal_id": signal,
            **metadata,
            "raw_relative_path": raw_relative,
            "raw_sha256": raw_hash,
        }
        write_immutable(
            metadata_path,
            (
                json.dumps(_serialize(metadata_payload), indent=2)
                + "\n"
            ).encode("utf-8"),
        )
        ticks = decode_ticks(payload, "EURUSD", hour)
        tick_frames.append(ticks)
        raw_records.append(
            {
                "hour_utc": hour,
                "observed_at_utc": _utc(
                    metadata["observed_at_utc"]
                ),
                "raw_relative_path": raw_relative,
                "raw_sha256": raw_hash,
                "metadata_relative_path": metadata_relative,
                "metadata_sha256": sha256_file(metadata_path),
                "tick_count": int(len(ticks)),
            }
        )
    market_observed = max(
        row["observed_at_utc"] for row in raw_records
    )
    if market_observed < deadline + pd.Timedelta(
        seconds=MINIMUM_CAPTURE_LAG_SECONDS
    ):
        raise RuntimeError(
            "Fetched path evidence predates the admissible capture time"
        )
    ticks = pd.concat(tick_frames, ignore_index=True)
    bars = build_completed_m5(ticks, market_observed)
    bars["timestamp_utc"] = pd.to_datetime(
        bars["timestamp_utc"], utc=True
    ).dt.as_unit("ns")
    path = bars[
        bars["timestamp_utc"].ge(entry)
        & bars["timestamp_utc"].lt(deadline)
    ].copy()
    expected = pd.date_range(
        entry,
        deadline - pd.Timedelta(minutes=5),
        freq="5min",
    )
    available = set(path["timestamp_utc"])
    missing = [timestamp for timestamp in expected if timestamp not in available]
    path = path.sort_values("timestamp_utc").reset_index(drop=True)
    inventory_hash = sha256_bytes(
        json.dumps(
            _serialize(raw_records),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    normalized_relative = (
        Path("normalized")
        / f"{signal}_{inventory_hash[:16]}.parquet"
    )
    normalized_path = output_root / normalized_relative
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    if normalized_path.exists():
        existing_frame = pd.read_parquet(normalized_path)
        pd.testing.assert_frame_equal(
            existing_frame.reset_index(drop=True),
            path.reset_index(drop=True),
            check_dtype=False,
        )
    else:
        path.to_parquet(
            normalized_path, index=False, compression="zstd"
        )
    chain = _evidence_chain(output_root)
    status = "COMPLETE" if not missing else "INCOMPLETE_M5_COVERAGE"
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "signal_id": signal,
        "entry_time_utc": entry,
        "deadline_utc": deadline,
        "market_observed_at_utc": market_observed,
        "required_hours_utc": required_path_hours(entry),
        "raw_snapshots": raw_records,
        "raw_inventory_sha256": inventory_hash,
        "normalized_snapshot": {
            "relative_path": normalized_relative,
            "sha256": sha256_file(normalized_path),
            "rows": int(len(path)),
        },
        "expected_m5_rows": int(len(expected)),
        "missing_m5_timestamps": missing,
        "path_evidence_chain_sha256": chain,
        "causality": {
            "capture_started_only_after_12h_deadline_plus_60s": True,
            "completed_bid_ask_m5_only": True,
            "missing_bar_action": "PENDING_INCOMPLETE_PATH",
        },
        "broker_action_allowed": False,
    }
    manifest_relative = (
        Path("manifests")
        / f"MANIFEST_{signal}_{inventory_hash[:16]}_{chain[:12]}.json"
    )
    manifest_path = output_root / manifest_relative
    write_immutable(
        manifest_path,
        (
            json.dumps(_serialize(manifest), indent=2) + "\n"
        ).encode("utf-8"),
    )
    return _serialize(
        {
            "status": (
                "TRADE_PATH_CAPTURED"
                if status == "COMPLETE"
                else "TRADE_PATH_INCOMPLETE"
            ),
            "signal_id": signal,
            "entry_time_utc": entry,
            "deadline_utc": deadline,
            "path_rows": int(len(path)),
            "missing_m5_timestamps": missing,
            "path_evidence_sha256": sha256_file(normalized_path),
            "manifest_relative_path": manifest_relative,
            "manifest_sha256": sha256_file(manifest_path),
            "path_evidence_chain_sha256": chain,
            "network_request_made": True,
            "broker_action_allowed": False,
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("capture",))
    parser.add_argument("--signal-id", required=True)
    parser.add_argument("--entry-time", required=True)
    parser.add_argument(
        "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = capture_trade_path(
        args.signal_id,
        args.entry_time,
        args.output_root,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
