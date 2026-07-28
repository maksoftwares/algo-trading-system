from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import pandas as pd

from download_neutral_tradingview_consensus import (
    ENDPOINT,
    PROVIDER_PAGE,
    TICKERS,
    USER_AGENT,
    _number,
    _valid_payload,
)


DEFAULT_OUTPUT_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-tradingview-consensus-v1"
)
SCHEMA_VERSION = "eurusd_neutral_prospective_consensus_snapshot_v1"
MINIMUM_LEAD_SECONDS = 60
LEDGER_COLUMNS = [
    "family",
    "event_time_utc",
    "forecast_value",
    "previous_value",
    "tradingview_event_id",
    "tradingview_title",
    "tradingview_ticker",
    "importance",
    "reference_date",
    "provider_source",
    "provider_source_url",
    "observed_at_utc",
    "lead_seconds",
    "raw_snapshot_relative_path",
    "raw_snapshot_sha256",
    "capture_semantics",
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iso_utc(value: pd.Timestamp) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def calendar_url(start: pd.Timestamp, end: pd.Timestamp) -> str:
    query = urllib.parse.urlencode(
        {
            "from": _iso_utc(start),
            "to": _iso_utc(end),
            "countries": "US",
            "minImportance": 0,
        }
    )
    return f"{ENDPOINT}?{query}"


def _utc(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.as_unit("ns")


def _http_date(value: str | None) -> pd.Timestamp | None:
    if not value:
        return None
    return _utc(parsedate_to_datetime(value))


def fetch_snapshot(
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> tuple[bytes, dict[str, Any]]:
    request_started = pd.Timestamp.now(tz="UTC").as_unit("ns")
    request = urllib.request.Request(
        calendar_url(start, end),
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Origin": "https://www.tradingview.com",
            "Referer": PROVIDER_PAGE,
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
        http_date = _http_date(response.headers.get("Date"))
        headers = {
            "date": response.headers.get("Date"),
            "etag": response.headers.get("ETag"),
            "age": response.headers.get("Age"),
            "cache_control": response.headers.get("Cache-Control"),
        }
    request_finished = pd.Timestamp.now(tz="UTC").as_unit("ns")
    _valid_payload(payload)
    evidence_candidates = [request_finished]
    if http_date is not None:
        evidence_candidates.append(http_date)
    observed_at = max(evidence_candidates)
    return payload, {
        "url": request.full_url,
        "requested_window": [start, end],
        "request_started_utc": request_started,
        "request_finished_utc": request_finished,
        "http_date_utc": http_date,
        "observed_at_utc": observed_at,
        "response_headers": headers,
    }


def empty_ledger() -> pd.DataFrame:
    return pd.DataFrame(columns=LEDGER_COLUMNS)


def build_pre_release_rows(
    payload: dict[str, Any],
    observed_at: pd.Timestamp,
    raw_relative_path: str,
    raw_sha256: str,
    *,
    minimum_lead_seconds: int = MINIMUM_LEAD_SECONDS,
) -> tuple[pd.DataFrame, dict[str, int]]:
    observed = _utc(observed_at)
    rows: list[dict[str, Any]] = []
    excluded = {
        "wrong_ticker": 0,
        "not_strictly_pre_release": 0,
        "actual_already_present": 0,
        "forecast_missing": 0,
    }
    for event in payload.get("result", []):
        ticker = str(event.get("ticker") or "")
        family = TICKERS.get(ticker)
        if family is None:
            excluded["wrong_ticker"] += 1
            continue
        event_time = _utc(event.get("date"))
        lead_seconds = (
            event_time - observed
        ).total_seconds()
        if lead_seconds < minimum_lead_seconds:
            excluded["not_strictly_pre_release"] += 1
            continue
        actual = _number(event, "actualRaw", "actual")
        if actual is not None:
            excluded["actual_already_present"] += 1
            continue
        forecast = _number(event, "forecastRaw", "forecast")
        if forecast is None:
            excluded["forecast_missing"] += 1
            continue
        rows.append(
            {
                "family": family,
                "event_time_utc": event_time,
                "forecast_value": forecast,
                "previous_value": _number(
                    event, "previousRaw", "previous"
                ),
                "tradingview_event_id": str(event.get("id") or ""),
                "tradingview_title": str(event.get("title") or ""),
                "tradingview_ticker": ticker,
                "importance": event.get("importance"),
                "reference_date": event.get("referenceDate"),
                "provider_source": event.get("source"),
                "provider_source_url": event.get("source_url"),
                "observed_at_utc": observed,
                "lead_seconds": lead_seconds,
                "raw_snapshot_relative_path": raw_relative_path,
                "raw_snapshot_sha256": raw_sha256,
                "capture_semantics": (
                    "STRICTLY_PRE_RELEASE_NO_ACTUAL_PRESENT"
                ),
            }
        )
    if not rows:
        return empty_ledger(), excluded
    frame = pd.DataFrame(rows)[LEDGER_COLUMNS]
    frame["event_time_utc"] = pd.to_datetime(
        frame["event_time_utc"], utc=True
    ).dt.as_unit("ns")
    frame["observed_at_utc"] = pd.to_datetime(
        frame["observed_at_utc"], utc=True
    ).dt.as_unit("ns")
    frame = frame.sort_values(
        ["event_time_utc", "family", "tradingview_event_id"]
    ).reset_index(drop=True)
    if not frame["event_time_utc"].gt(frame["observed_at_utc"]).all():
        raise RuntimeError("Post-release row entered prospective ledger")
    if frame["lead_seconds"].lt(minimum_lead_seconds).any():
        raise RuntimeError("Prospective lead-time contract violated")
    return frame, excluded


def write_immutable(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise RuntimeError(
                f"Refusing to overwrite immutable snapshot: {path}"
            )


def evidence_chain(output_root: Path) -> str:
    digest = hashlib.sha256()
    evidence_paths = sorted(
        [
            *output_root.glob("raw/*.json"),
            *output_root.glob("metadata/*.json"),
            *output_root.glob("normalized/*.parquet"),
        ],
        key=lambda path: path.relative_to(output_root).as_posix(),
    )
    for path in evidence_paths:
        relative = path.relative_to(output_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def _serialize(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value


def persist_snapshot(
    output_root: Path,
    raw_payload: bytes,
    capture_metadata: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    payload = _valid_payload(raw_payload)
    observed_at = _utc(capture_metadata["observed_at_utc"])
    raw_hash = sha256_bytes(raw_payload)
    stem = (
        observed_at.strftime("%Y%m%dT%H%M%SZ")
        + "_"
        + raw_hash[:16]
    )
    raw_relative = Path("raw") / f"{stem}.json"
    metadata_relative = Path("metadata") / f"{stem}.json"
    normalized_relative = Path("normalized") / f"{stem}.parquet"
    raw_path = output_root / raw_relative
    metadata_path = output_root / metadata_relative
    normalized_path = output_root / normalized_relative
    write_immutable(raw_path, raw_payload)
    rows, excluded = build_pre_release_rows(
        payload,
        observed_at,
        raw_relative.as_posix(),
        raw_hash,
    )
    metadata_payload = {
        "schema_version": SCHEMA_VERSION,
        **capture_metadata,
        "raw_relative_path": raw_relative,
        "raw_sha256": raw_hash,
        "pre_release_rows": int(len(rows)),
        "exclusions": excluded,
    }
    metadata_bytes = (
        json.dumps(_serialize(metadata_payload), indent=2) + "\n"
    ).encode("utf-8")
    write_immutable(metadata_path, metadata_bytes)
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    if normalized_path.exists():
        existing = pd.read_parquet(normalized_path)
        pd.testing.assert_frame_equal(
            existing.reset_index(drop=True),
            rows.reset_index(drop=True),
            check_dtype=False,
        )
    else:
        rows.to_parquet(
            normalized_path, index=False, compression="zstd"
        )
    chain = evidence_chain(output_root)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "provider": "TradingView Economic Calendar",
        "authentication_required": False,
        "observed_at_utc": observed_at,
        "http_date_utc": capture_metadata.get("http_date_utc"),
        "raw_snapshot": {
            "relative_path": raw_relative,
            "sha256": raw_hash,
        },
        "capture_metadata": {
            "relative_path": metadata_relative,
            "sha256": sha256_file(metadata_path),
        },
        "normalized_snapshot": {
            "relative_path": normalized_relative,
            "sha256": sha256_file(normalized_path),
            "rows": int(len(rows)),
        },
        "immutable_evidence_files": {
            "raw": len(list(output_root.glob("raw/*.json"))),
            "metadata": len(list(output_root.glob("metadata/*.json"))),
            "normalized": len(
                list(output_root.glob("normalized/*.parquet"))
            ),
        },
        "evidence_chain_sha256": chain,
        "pre_release_contract": {
            "minimum_lead_seconds": MINIMUM_LEAD_SECONDS,
            "actual_field_must_be_absent": True,
            "forecast_field_must_be_present": True,
            "raw_and_normalized_snapshots_are_never_overwritten": True,
        },
        "accepted_for_prospective_point_in_time_evidence": bool(
            len(rows) > 0
        ),
        "broker_action_allowed": False,
    }
    manifest_relative = (
        Path("manifests")
        / f"MANIFEST_{stem}_{chain[:12]}.json"
    )
    manifest_path = output_root / manifest_relative
    manifest_bytes = (
        json.dumps(_serialize(manifest), indent=2) + "\n"
    ).encode("utf-8")
    write_immutable(manifest_path, manifest_bytes)
    manifest["manifest_relative_path"] = manifest_relative
    manifest["manifest_sha256"] = sha256_file(manifest_path)
    return _serialize(manifest), rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("capture",))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )
    parser.add_argument("--days-ahead", type=int, default=60)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.days_ahead < 1 or args.days_ahead > 180:
        raise RuntimeError("--days-ahead must be between 1 and 180")
    start = pd.Timestamp.now(tz="UTC").floor("D").as_unit("ns")
    end = start + pd.Timedelta(days=int(args.days_ahead))
    payload, capture_metadata = fetch_snapshot(start, end)
    manifest, rows = persist_snapshot(
        args.output_root,
        payload,
        capture_metadata,
    )
    print(
        json.dumps(
            {
                "observed_at_utc": manifest["observed_at_utc"],
                "pre_release_rows": int(len(rows)),
                "events": (
                    rows[
                        [
                            "family",
                            "event_time_utc",
                            "forecast_value",
                            "lead_seconds",
                        ]
                    ].to_dict(orient="records")
                    if len(rows)
                    else []
                ),
                "evidence_chain_sha256": manifest[
                    "evidence_chain_sha256"
                ],
                "manifest_relative_path": manifest[
                    "manifest_relative_path"
                ],
                "manifest_sha256": manifest["manifest_sha256"],
                "broker_action_allowed": False,
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
