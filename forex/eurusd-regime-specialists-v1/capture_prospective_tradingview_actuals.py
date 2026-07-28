from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from capture_prospective_tradingview_consensus import (
    DEFAULT_OUTPUT_ROOT,
    MINIMUM_LEAD_SECONDS,
    _serialize,
    _utc,
    fetch_snapshot,
    sha256_bytes,
    sha256_file,
    write_immutable,
)
from download_neutral_tradingview_consensus import (
    TICKERS,
    _number,
    _valid_payload,
)


SCHEMA_VERSION = "eurusd_neutral_prospective_actual_snapshot_v1"
MINIMUM_POST_RELEASE_SECONDS = 60
ACTUAL_COLUMNS = [
    "family",
    "event_time_utc",
    "forecast_value",
    "forecast_observed_at_utc",
    "forecast_lead_seconds",
    "forecast_raw_snapshot_relative_path",
    "forecast_raw_snapshot_sha256",
    "tradingview_event_id",
    "tradingview_ticker",
    "actual_value",
    "actual_observed_at_utc",
    "actual_lag_seconds",
    "actual_raw_snapshot_relative_path",
    "actual_raw_snapshot_sha256",
    "surprise_value",
    "macro_side",
    "capture_semantics",
]


def empty_actual_ledger() -> pd.DataFrame:
    return pd.DataFrame(columns=ACTUAL_COLUMNS)


def load_latest_pre_release_forecasts(
    output_root: Path,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in sorted(output_root.glob("normalized/*.parquet")):
        frame = pd.read_parquet(path)
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    for column in ("event_time_utc", "observed_at_utc"):
        combined[column] = pd.to_datetime(combined[column], utc=True)
    calculated_lead = (
        combined["event_time_utc"] - combined["observed_at_utc"]
    ).dt.total_seconds()
    valid = (
        calculated_lead.ge(MINIMUM_LEAD_SECONDS)
        & combined["lead_seconds"].ge(MINIMUM_LEAD_SECONDS)
        & combined["forecast_value"].notna()
    )
    if not valid.all():
        raise RuntimeError("Invalid row in pre-release evidence ledger")
    key = [
        "tradingview_event_id",
        "tradingview_ticker",
        "event_time_utc",
    ]
    latest = (
        combined.sort_values([*key, "observed_at_utc"])
        .drop_duplicates(key, keep="last")
        .reset_index(drop=True)
    )
    return latest


def mature_forecasts(
    forecasts: pd.DataFrame,
    observed_at: pd.Timestamp,
    *,
    minimum_post_release_seconds: int = MINIMUM_POST_RELEASE_SECONDS,
) -> pd.DataFrame:
    if forecasts.empty:
        return forecasts.copy()
    observed = _utc(observed_at)
    frame = forecasts.copy()
    frame["event_time_utc"] = pd.to_datetime(
        frame["event_time_utc"], utc=True
    )
    maturity = frame["event_time_utc"] + pd.Timedelta(
        seconds=minimum_post_release_seconds
    )
    return frame[maturity.le(observed)].copy()


def build_post_release_rows(
    payload: dict[str, Any],
    observed_at: pd.Timestamp,
    eligible_forecasts: pd.DataFrame,
    raw_relative_path: str,
    raw_sha256: str,
    *,
    minimum_post_release_seconds: int = MINIMUM_POST_RELEASE_SECONDS,
) -> tuple[pd.DataFrame, dict[str, int]]:
    observed = _utc(observed_at)
    forecasts = eligible_forecasts.copy()
    if forecasts.empty:
        return empty_actual_ledger(), {
            "target_provider_events": 0,
            "unmatched_pre_release_event": 0,
            "not_strictly_post_release": 0,
            "actual_missing": 0,
        }
    for column in ("event_time_utc", "observed_at_utc"):
        forecasts[column] = pd.to_datetime(
            forecasts[column], utc=True
        ).dt.as_unit("ns")
    calculated_lead = (
        forecasts["event_time_utc"] - forecasts["observed_at_utc"]
    ).dt.total_seconds()
    if (
        calculated_lead.lt(MINIMUM_LEAD_SECONDS).any()
        or forecasts["lead_seconds"].lt(MINIMUM_LEAD_SECONDS).any()
    ):
        raise RuntimeError(
            "Forecast linkage lacks the required pre-release lead"
        )
    forecast_keys = {
        (
            str(row.tradingview_event_id),
            str(row.tradingview_ticker),
            pd.Timestamp(row.event_time_utc),
        ): row
        for row in forecasts.itertuples(index=False)
    }
    rows: list[dict[str, Any]] = []
    excluded = {
        "target_provider_events": 0,
        "unmatched_pre_release_event": 0,
        "not_strictly_post_release": 0,
        "actual_missing": 0,
    }
    for event in payload.get("result", []):
        ticker = str(event.get("ticker") or "")
        family = TICKERS.get(ticker)
        if family is None:
            continue
        excluded["target_provider_events"] += 1
        event_time = _utc(event.get("date"))
        key = (
            str(event.get("id") or ""),
            ticker,
            event_time,
        )
        forecast = forecast_keys.get(key)
        if forecast is None:
            excluded["unmatched_pre_release_event"] += 1
            continue
        lag_seconds = (observed - event_time).total_seconds()
        if lag_seconds < minimum_post_release_seconds:
            excluded["not_strictly_post_release"] += 1
            continue
        actual = _number(event, "actualRaw", "actual")
        if actual is None:
            excluded["actual_missing"] += 1
            continue
        surprise = float(actual) - float(forecast.forecast_value)
        if surprise > 0:
            side = "SHORT"
        elif surprise < 0:
            side = "LONG"
        else:
            side = "CASH"
        rows.append(
            {
                "family": family,
                "event_time_utc": event_time,
                "forecast_value": float(forecast.forecast_value),
                "forecast_observed_at_utc": pd.Timestamp(
                    forecast.observed_at_utc
                ),
                "forecast_lead_seconds": float(
                    forecast.lead_seconds
                ),
                "forecast_raw_snapshot_relative_path": str(
                    forecast.raw_snapshot_relative_path
                ),
                "forecast_raw_snapshot_sha256": str(
                    forecast.raw_snapshot_sha256
                ),
                "tradingview_event_id": key[0],
                "tradingview_ticker": ticker,
                "actual_value": float(actual),
                "actual_observed_at_utc": observed,
                "actual_lag_seconds": lag_seconds,
                "actual_raw_snapshot_relative_path": raw_relative_path,
                "actual_raw_snapshot_sha256": raw_sha256,
                "surprise_value": surprise,
                "macro_side": side,
                "capture_semantics": (
                    "LINKED_PRE_RELEASE_FORECAST_AND_POST_RELEASE_ACTUAL"
                ),
            }
        )
    if not rows:
        return empty_actual_ledger(), excluded
    frame = pd.DataFrame(rows)[ACTUAL_COLUMNS].sort_values(
        ["event_time_utc", "family", "tradingview_event_id"]
    ).reset_index(drop=True)
    if not frame["forecast_observed_at_utc"].lt(
        frame["event_time_utc"]
    ).all():
        raise RuntimeError("Post-release row lost pre-release linkage")
    if not frame["actual_observed_at_utc"].gt(
        frame["event_time_utc"]
    ).all():
        raise RuntimeError("Actual was not observed after release")
    return frame, excluded


def post_release_evidence_chain(output_root: Path) -> str:
    digest = hashlib.sha256()
    paths = sorted(
        [
            *output_root.glob("post_release_raw/*.json"),
            *output_root.glob("post_release_metadata/*.json"),
            *output_root.glob("post_release_normalized/*.parquet"),
        ],
        key=lambda path: path.relative_to(output_root).as_posix(),
    )
    for path in paths:
        relative = path.relative_to(output_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def persist_post_release_snapshot(
    output_root: Path,
    raw_payload: bytes,
    capture_metadata: dict[str, Any],
    eligible_forecasts: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame]:
    payload = _valid_payload(raw_payload)
    observed_at = _utc(capture_metadata["observed_at_utc"])
    raw_hash = sha256_bytes(raw_payload)
    stem = (
        observed_at.strftime("%Y%m%dT%H%M%SZ")
        + "_"
        + raw_hash[:16]
    )
    raw_relative = Path("post_release_raw") / f"{stem}.json"
    metadata_relative = (
        Path("post_release_metadata") / f"{stem}.json"
    )
    normalized_relative = (
        Path("post_release_normalized") / f"{stem}.parquet"
    )
    raw_path = output_root / raw_relative
    metadata_path = output_root / metadata_relative
    normalized_path = output_root / normalized_relative
    write_immutable(raw_path, raw_payload)
    rows, excluded = build_post_release_rows(
        payload,
        observed_at,
        eligible_forecasts,
        raw_relative.as_posix(),
        raw_hash,
    )
    metadata = {
        "schema_version": SCHEMA_VERSION,
        **capture_metadata,
        "raw_relative_path": raw_relative,
        "raw_sha256": raw_hash,
        "eligible_pre_release_forecasts": int(
            len(eligible_forecasts)
        ),
        "linked_actual_rows": int(len(rows)),
        "exclusions": excluded,
    }
    write_immutable(
        metadata_path,
        (json.dumps(_serialize(metadata), indent=2) + "\n").encode(
            "utf-8"
        ),
    )
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
    chain = post_release_evidence_chain(output_root)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "observed_at_utc": observed_at,
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
        "post_release_evidence_chain_sha256": chain,
        "strict_linkage": {
            "pre_release_forecast_required": True,
            "forecast_observed_before_event": True,
            "actual_observed_after_event": True,
            "event_id_ticker_and_timestamp_exact_match": True,
        },
        "broker_action_allowed": False,
    }
    manifest_relative = (
        Path("post_release_manifests")
        / f"MANIFEST_{stem}_{chain[:12]}.json"
    )
    manifest_path = output_root / manifest_relative
    write_immutable(
        manifest_path,
        (json.dumps(_serialize(manifest), indent=2) + "\n").encode(
            "utf-8"
        ),
    )
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    now = pd.Timestamp.now(tz="UTC").as_unit("ns")
    forecasts = load_latest_pre_release_forecasts(args.output_root)
    eligible = mature_forecasts(forecasts, now)
    if eligible.empty:
        print(
            json.dumps(
                {
                    "status": "NO_MATURE_PRE_RELEASE_FORECASTS",
                    "observed_at_utc": now.isoformat(),
                    "pre_release_forecasts": int(len(forecasts)),
                    "mature_forecasts": 0,
                    "network_request_made": False,
                    "broker_action_allowed": False,
                },
                indent=2,
            )
        )
        return 0
    start = eligible["event_time_utc"].min().floor("D")
    end = eligible["event_time_utc"].max().ceil("D") + pd.Timedelta(
        days=1
    )
    payload, metadata = fetch_snapshot(start, end)
    manifest, rows = persist_post_release_snapshot(
        args.output_root, payload, metadata, eligible
    )
    print(
        json.dumps(
            {
                "status": (
                    "LINKED_ACTUALS_CAPTURED"
                    if len(rows)
                    else "MATURE_EVENTS_ACTUALS_NOT_YET_PRESENT"
                ),
                "linked_actual_rows": int(len(rows)),
                "events": (
                    rows[
                        [
                            "family",
                            "event_time_utc",
                            "forecast_value",
                            "actual_value",
                            "surprise_value",
                            "macro_side",
                        ]
                    ].to_dict(orient="records")
                    if len(rows)
                    else []
                ),
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
