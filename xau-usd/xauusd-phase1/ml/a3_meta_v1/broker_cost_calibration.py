from __future__ import annotations

import csv
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from ml.a3_meta_v1.dukascopy_confirmed_event_specialists import (
    _artifact,
    _iso_ms,
    _sha256_file,
)


DEFAULT_CONTRACT = Path("config/ml/a3_ml_broker_cost_calibration_v1.json")
DAY_MS = 24 * 60 * 60 * 1000
HOUR_MS = 60 * 60 * 1000


class BrokerCostCalibrationError(RuntimeError):
    pass


def run_broker_cost_calibration(
    phase1_root: Path, contract_path: Path | None = None
) -> Path:
    phase1_root = phase1_root.resolve()
    contract_file = (contract_path or phase1_root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    validate_contract(contract)
    c02_report, account_records = load_locked_c02_source(phase1_root, contract)
    boundary = verify_cross_account_boundaries(account_records, contract)
    canonical = account_records[str(contract["c02_source_lock"]["canonical_account_label"])]
    ticks, canonical_audit = load_canonical_ticks(canonical, contract)
    dukascopy = load_locked_dukascopy_source(contract)
    report, daily, hourly, overlap = build_calibration_report(
        phase1_root=phase1_root,
        contract_file=contract_file,
        contract=contract,
        c02_report=c02_report,
        ticks=ticks,
        canonical_audit=canonical_audit,
        boundary=boundary,
        dukascopy=dukascopy,
    )
    outputs = {
        key: (phase1_root / value).resolve() for key, value in contract["outputs"].items()
    }
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(outputs["daily_metrics_csv"], index=False)
    hourly.to_csv(outputs["hourly_metrics_csv"], index=False)
    overlap.to_csv(outputs["overlap_m5_csv"], index=False)
    report["artifacts"] = {
        key: _artifact(outputs[key])
        for key in ("daily_metrics_csv", "hourly_metrics_csv", "overlap_m5_csv")
    }
    outputs["report_json"].write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    outputs["report_markdown"].write_text(render_report(report), encoding="utf-8")
    return outputs["report_json"]


def validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_broker_cost_calibration_v1":
        raise ValueError("unexpected broker cost calibration contract")
    if contract.get("symbol") != "XAUUSD":
        raise ValueError("broker cost calibration V1 is locked to XAUUSD")
    source = contract["c02_source_lock"]
    accounts = source["expected_accounts"]
    if len(accounts) != 3 or len({row["account_label"] for row in accounts}) != 3:
        raise ValueError("broker cost calibration requires three declared account exports")
    if str(source["canonical_account_label"]) not in {
        str(row["account_label"]) for row in accounts
    }:
        raise ValueError("canonical account is absent from expected accounts")
    calibration = contract["calibration"]
    if not 0 < float(calibration["broker_spread_floor_quantile"]) < 1:
        raise ValueError("broker spread floor quantile must be internal")
    if not 0 < float(calibration["maximum_total_stressed_entry_cost_r"]) <= 0.25:
        raise ValueError("cost/R ceiling differs from the conservative lock")
    controls = contract["research_controls"]
    for key in (
        "same_server_accounts_are_independent_samples",
        "historical_broker_spread_portability_claim_authorized",
        "strategy_parameter_selection_authorized",
        "model_training_authorized",
    ):
        if controls.get(key):
            raise ValueError(f"forbidden broker calibration control: {key}")
    authorization = contract["authorization"]
    if not authorization.get("research_only"):
        raise ValueError("broker cost calibration must remain research-only")
    for key in (
        "python_demo_predictions_authorized",
        "ea_consumption_authorized",
        "broker_action_authorized",
    ):
        if authorization.get(key):
            raise ValueError(f"forbidden broker calibration authorization: {key}")


def load_locked_c02_source(
    phase1_root: Path, contract: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    locked = contract["c02_source_lock"]
    report_path = (phase1_root / str(locked["report_path"])).resolve()
    if _sha256_file(report_path) != str(locked["report_sha256"]):
        raise BrokerCostCalibrationError("C02 source report hash mismatch")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if (
        report.get("status") != "PASS"
        or str(report.get("dataset_version")) != str(locked["dataset_version"])
        or str(report.get("requested_start_utc")) != str(locked["requested_start_utc"])
        or str(report.get("snapshot_cutoff_utc")) != str(locked["snapshot_cutoff_utc"])
    ):
        raise BrokerCostCalibrationError("C02 source report identity mismatch")
    manifest_path = Path(str(report["root_manifest"]["path"])).resolve()
    if (
        str(report["root_manifest"]["sha256"])
        != str(locked["root_manifest_sha256"])
        or _sha256_file(manifest_path) != str(locked["root_manifest_sha256"])
    ):
        raise BrokerCostCalibrationError("C02 root manifest hash mismatch")
    records = {str(row["account_label"]): dict(row) for row in report["account_records"]}
    expected_labels = {str(row["account_label"]) for row in locked["expected_accounts"]}
    if set(records) != expected_labels:
        raise BrokerCostCalibrationError("C02 account set mismatch")
    active_dates = set(str(value) for value in locked["active_dates_utc"])
    for expected in locked["expected_accounts"]:
        label = str(expected["account_label"])
        record = records[label]
        if (
            str(record["account_scope"]) != str(expected["account_scope"])
            or record.get("status") != "PASS"
            or not record.get("data_exported")
        ):
            raise BrokerCostCalibrationError(f"C02 account identity mismatch: {label}")
        metadata_record = _file_record(record, "mt5_metadata.json")
        metadata_path = Path(str(metadata_record["path"])).resolve()
        if _sha256_file(metadata_path) != str(metadata_record["sha256"]):
            raise BrokerCostCalibrationError(f"C02 metadata hash mismatch: {label}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if (
            str(metadata["account"]["login"]) != str(expected["account_scope"])
            or str(metadata["account"]["server"]) != str(expected["server"])
            or str(metadata["symbol"]["name"]) != str(contract["symbol"])
        ):
            raise BrokerCostCalibrationError(f"C02 metadata identity mismatch: {label}")
        tick_records = _active_tick_records(record)
        rows = sum(int(row["row_count"]) for row in tick_records)
        dates = {_tick_date(str(row["relative_path"])) for row in tick_records}
        if (
            rows != int(expected["expected_tick_rows"])
            or len(tick_records) != int(expected["expected_active_tick_files"])
            or dates != active_dates
        ):
            raise BrokerCostCalibrationError(f"C02 tick coverage mismatch: {label}")
    return report, records


def verify_cross_account_boundaries(
    records: Mapping[str, Mapping[str, Any]], contract: Mapping[str, Any]
) -> dict[str, Any]:
    labels = [str(row["account_label"]) for row in contract["c02_source_lock"]["expected_accounts"]]
    dates = [str(value) for value in contract["c02_source_lock"]["active_dates_utc"]]
    mismatches = []
    comparisons = 0
    for date in dates:
        boundaries = {}
        for label in labels:
            record = _file_record(records[label], f"XAUUSD_ticks_{date.replace('-', '')}.csv")
            path = Path(str(record["path"])).resolve()
            boundaries[label] = (
                _boundary_quote(path, first=True),
                _boundary_quote(path, first=False),
            )
        baseline = boundaries[labels[0]]
        for label in labels[1:]:
            comparisons += 2
            if boundaries[label] != baseline:
                mismatches.append(
                    {
                        "date_utc": date,
                        "account_label": label,
                        "first_matches": boundaries[label][0] == baseline[0],
                        "last_matches": boundaries[label][1] == baseline[1],
                    }
                )
    return {
        "active_dates_compared": len(dates),
        "account_labels": labels,
        "boundary_comparisons": comparisons,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "accounts_treated_as_independent_samples": False,
    }


def load_canonical_ticks(
    record: Mapping[str, Any], contract: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    calibration = contract["calibration"]
    chunks = []
    file_audit = []
    prior_timestamp: int | None = None
    chronology_ok = True
    invalid_bid_ask_rows = 0
    maximum_spread_error = 0.0
    for file_record in _active_tick_records(record):
        path = Path(str(file_record["path"])).resolve()
        if calibration["verify_all_canonical_file_hashes"] and _sha256_file(path) != str(
            file_record["sha256"]
        ):
            raise BrokerCostCalibrationError(f"canonical tick hash mismatch: {path.name}")
        file_rows = 0
        file_min: int | None = None
        file_max: int | None = None
        reader = pd.read_csv(
            path,
            usecols=["time_msc", "bid", "ask", "spread_price", "spread_points"],
            chunksize=int(calibration["tick_chunk_rows"]),
        )
        for chunk in reader:
            timestamp = chunk["time_msc"].to_numpy(dtype=np.int64)
            bid = chunk["bid"].to_numpy(dtype=float)
            ask = chunk["ask"].to_numpy(dtype=float)
            stated = chunk["spread_price"].to_numpy(dtype=float)
            actual = ask - bid
            if len(timestamp):
                file_min = int(timestamp[0]) if file_min is None else file_min
                file_max = int(timestamp[-1])
                if prior_timestamp is not None and int(timestamp[0]) < prior_timestamp:
                    chronology_ok = False
                if np.any(np.diff(timestamp) < 0):
                    chronology_ok = False
                prior_timestamp = int(timestamp[-1])
            invalid_bid_ask_rows += int(
                np.count_nonzero(
                    ~np.isfinite(bid)
                    | ~np.isfinite(ask)
                    | (bid <= 0)
                    | (ask <= 0)
                    | (ask < bid)
                )
            )
            if len(actual):
                maximum_spread_error = max(
                    maximum_spread_error,
                    float(np.nanmax(np.abs(actual - stated))),
                )
            chunks.append(
                pd.DataFrame(
                    {
                        "timestamp_ms": timestamp,
                        "bid": bid,
                        "ask": ask,
                        "spread_price": actual,
                        "spread_points": chunk["spread_points"].to_numpy(dtype=float),
                    }
                )
            )
            file_rows += len(chunk)
        if file_rows != int(file_record["row_count"]):
            raise BrokerCostCalibrationError(f"canonical tick row mismatch: {path.name}")
        file_audit.append(
            {
                "filename": path.name,
                "rows": file_rows,
                "first_timestamp_ms": file_min,
                "last_timestamp_ms": file_max,
                "sha256": str(file_record["sha256"]),
            }
        )
    ticks = pd.concat(chunks, ignore_index=True)
    exact_duplicates = int(
        ticks.duplicated(subset=["timestamp_ms", "bid", "ask"], keep=False).sum()
    )
    audit = {
        "account_label": str(record["account_label"]),
        "account_scope": str(record["account_scope"]),
        "tick_rows": len(ticks),
        "active_tick_files": len(file_audit),
        "chronological_non_decreasing": chronology_ok,
        "invalid_bid_ask_rows": invalid_bid_ask_rows,
        "maximum_spread_reconciliation_error": maximum_spread_error,
        "exact_duplicate_quote_rows": exact_duplicates,
        "first_timestamp_utc": _iso_ms(int(ticks.iloc[0]["timestamp_ms"])),
        "last_timestamp_utc": _iso_ms(int(ticks.iloc[-1]["timestamp_ms"])),
        "files": file_audit,
    }
    return ticks, audit


def load_locked_dukascopy_source(contract: Mapping[str, Any]) -> pd.DataFrame:
    locked = contract["dukascopy_source_lock"]
    root = Path(
        os.environ.get(str(locked["storage_environment_variable"]), "").strip()
        or str(locked["default_storage_root"])
    ).expanduser().resolve()
    path = (root / str(locked["feature_path"])).resolve()
    if _sha256_file(path) != str(locked["feature_sha256"]):
        raise BrokerCostCalibrationError("Dukascopy feature hash mismatch")
    columns = [
        "timestamp_ms",
        "atr",
        "bid_open",
        "ask_open",
        "tick_spread_mean",
        "tick_spread_last",
        "tick_spread_max",
    ]
    frame = pd.read_parquet(path, columns=columns).sort_values("timestamp_ms")
    if len(frame) != int(locked["feature_rows"]):
        raise BrokerCostCalibrationError("Dukascopy feature row mismatch")
    timestamps = frame["timestamp_ms"].to_numpy(dtype=np.int64)
    if np.any(np.diff(timestamps) <= 0):
        raise BrokerCostCalibrationError("Dukascopy feature chronology mismatch")
    return frame.reset_index(drop=True)


def build_calibration_report(
    *,
    phase1_root: Path,
    contract_file: Path,
    contract: Mapping[str, Any],
    c02_report: Mapping[str, Any],
    ticks: pd.DataFrame,
    canonical_audit: Mapping[str, Any],
    boundary: Mapping[str, Any],
    dukascopy: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    calibration = contract["calibration"]
    quantiles = [float(value) for value in calibration["quantiles"]]
    daily = grouped_spread_metrics(ticks, ticks["timestamp_ms"] // DAY_MS, "day_index")
    daily["date_utc"] = pd.to_datetime(
        daily.pop("day_index") * DAY_MS, unit="ms", utc=True
    ).dt.strftime("%Y-%m-%d")
    daily = daily[["date_utc", *[column for column in daily if column != "date_utc"]]]
    hourly = grouped_spread_metrics(
        ticks, (ticks["timestamp_ms"] // HOUR_MS) % 24, "hour_utc"
    )
    m5 = grouped_spread_metrics(
        ticks,
        (ticks["timestamp_ms"] // int(calibration["m5_bucket_milliseconds"]))
        * int(calibration["m5_bucket_milliseconds"]),
        "timestamp_ms",
        include_last=True,
    )
    overlap = m5.merge(dukascopy, on="timestamp_ms", how="inner", validate="one_to_one")
    overlap["time_utc"] = overlap["timestamp_ms"].map(lambda value: _iso_ms(int(value)))
    overlap["broker_spread_median_atr"] = overlap["spread_median"] / overlap["atr"]
    overlap["broker_spread_p90_atr"] = overlap["spread_p90"] / overlap["atr"]
    overlap["dukascopy_open_spread"] = overlap["ask_open"] - overlap["bid_open"]
    overlap["dukascopy_open_spread_atr"] = overlap["dukascopy_open_spread"] / overlap["atr"]
    overlap["broker_p90_minus_dukascopy_mean"] = (
        overlap["spread_p90"] - overlap["tick_spread_mean"]
    )
    overlap = overlap[
        [
            "time_utc",
            "timestamp_ms",
            "ticks",
            "spread_median",
            "spread_p90",
            "spread_p95",
            "spread_p99",
            "spread_last",
            "atr",
            "broker_spread_median_atr",
            "broker_spread_p90_atr",
            "dukascopy_open_spread",
            "dukascopy_open_spread_atr",
            "tick_spread_mean",
            "tick_spread_last",
            "tick_spread_max",
            "broker_p90_minus_dukascopy_mean",
        ]
    ]
    spread_floor = float(
        ticks["spread_price"].quantile(float(calibration["broker_spread_floor_quantile"]))
    )
    quantity = float(calibration["reference_lot_size"]) * float(
        calibration["contract_size_ounces_per_lot"]
    )
    additional_price = float(
        calibration["additional_execution_cost_usd_per_0p01_lot"]
    ) / quantity
    stressed_entry_cost = spread_floor + additional_price
    minimum_stop_distance = stressed_entry_cost / float(
        calibration["maximum_total_stressed_entry_cost_r"]
    )
    quality = {
        "c02_report_and_manifest_hashes_match": True,
        "account_identity_and_counts_match": True,
        "canonical_file_hashes_match": True,
        "canonical_rows_chronological": bool(
            canonical_audit["chronological_non_decreasing"]
        ),
        "canonical_bid_ask_valid": int(canonical_audit["invalid_bid_ask_rows"]) == 0,
        "canonical_spread_reconciles": float(
            canonical_audit["maximum_spread_reconciliation_error"]
        )
        <= float(calibration["require_spread_column_reconciliation_tolerance"]),
        "cross_account_boundary_quotes_match": int(boundary["mismatch_count"]) == 0,
        "dukascopy_source_hash_and_rows_match": len(dukascopy)
        == int(contract["dukascopy_source_lock"]["feature_rows"]),
        "minimum_overlap_m5_bars_met": len(overlap)
        >= int(calibration["minimum_overlap_m5_bars"]),
    }
    auxiliary = contract["auxiliary_demo_cost_report"]
    auxiliary_path = (phase1_root / str(auxiliary["path"])).resolve()
    auxiliary_hash_matches = _sha256_file(auxiliary_path) == str(auxiliary["sha256"])
    auxiliary_payload = json.loads(auxiliary_path.read_text(encoding="utf-8"))
    report = {
        "schema_version": str(contract["schema_version"]),
        "classification": "BROKER_COST_CALIBRATION_VALID"
        if all(quality.values())
        else "BROKER_COST_CALIBRATION_INVALID",
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "c02_source": {
            "report_sha256": str(contract["c02_source_lock"]["report_sha256"]),
            "root_manifest_sha256": str(
                contract["c02_source_lock"]["root_manifest_sha256"]
            ),
            "dataset_version": str(c02_report["dataset_version"]),
        },
        "canonical_tick_audit": dict(canonical_audit),
        "cross_account_boundary_audit": dict(boundary),
        "broker_spread_price": describe(ticks["spread_price"], quantiles),
        "broker_spread_points": describe(ticks["spread_points"], quantiles),
        "dukascopy_overlap": {
            "matched_m5_bars": len(overlap),
            "first_time_utc": str(overlap.iloc[0]["time_utc"]) if len(overlap) else "",
            "last_time_utc": str(overlap.iloc[-1]["time_utc"]) if len(overlap) else "",
            "broker_spread_median": describe(overlap["spread_median"], quantiles),
            "broker_spread_p90": describe(overlap["spread_p90"], quantiles),
            "dukascopy_spread_mean": describe(overlap["tick_spread_mean"], quantiles),
            "dukascopy_open_spread": describe(
                overlap["dukascopy_open_spread"], quantiles
            ),
            "broker_spread_p90_atr": describe(
                overlap["broker_spread_p90_atr"], quantiles
            ),
            "dukascopy_open_spread_atr": describe(
                overlap["dukascopy_open_spread_atr"], quantiles
            ),
        },
        "locked_cost_assumption": {
            "broker_spread_floor_quantile": float(
                calibration["broker_spread_floor_quantile"]
            ),
            "broker_spread_floor_price": spread_floor,
            "additional_execution_cost_usd_per_0p01_lot": float(
                calibration["additional_execution_cost_usd_per_0p01_lot"]
            ),
            "additional_execution_cost_price": additional_price,
            "total_stressed_entry_cost_price": stressed_entry_cost,
            "maximum_total_stressed_entry_cost_r": float(
                calibration["maximum_total_stressed_entry_cost_r"]
            ),
            "minimum_initial_stop_distance_price": minimum_stop_distance,
            "historical_rule": (
                "Use native Dukascopy Bid/Ask and stress entry spread to at least the "
                "broker floor; add the fixed execution cost."
            ),
        },
        "quality_gates": quality,
        "auxiliary_demo_cost_context": {
            "hash_matches": auxiliary_hash_matches,
            "used_for_calibration": False,
            "raw_source_reverification_available": False,
            "reported_status": str(auxiliary_payload.get("status", "")),
            "reported_executed_cost_r_max": auxiliary_payload.get(
                "p2weakness_order_cost_summary", {}
            ).get("executed_cost_r_max"),
        },
        "research_controls": dict(contract["research_controls"]),
        "authorization": {
            **dict(contract["authorization"]),
            "strategy_authorized": False,
            "demo_or_live_authorized": False,
        },
        "limitations": [
            "The target-broker sample covers June 2026, not ten historical years.",
            "All three accounts share one broker server and are not independent feeds.",
            "The broker spread floor is a stress input, not a historical portability claim.",
            "Calibration validity does not establish strategy expectancy.",
        ],
    }
    return report, daily, hourly, overlap


def grouped_spread_metrics(
    ticks: pd.DataFrame,
    groups: pd.Series,
    group_name: str,
    *,
    include_last: bool = False,
) -> pd.DataFrame:
    source = pd.DataFrame(
        {group_name: groups.to_numpy(), "spread_price": ticks["spread_price"].to_numpy()}
    )
    grouped = source.groupby(group_name, sort=True)["spread_price"]
    result = grouped.agg(ticks="size", spread_min="min", spread_mean="mean", spread_max="max")
    for name, quantile in (
        ("spread_median", 0.5),
        ("spread_p90", 0.9),
        ("spread_p95", 0.95),
        ("spread_p99", 0.99),
    ):
        result[name] = grouped.quantile(quantile)
    if include_last:
        result["spread_last"] = grouped.last()
    return result.reset_index()


def describe(values: pd.Series, quantiles: Sequence[float]) -> dict[str, Any]:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    output: dict[str, Any] = {
        "count": int(len(numeric)),
        "mean": float(numeric.mean()) if len(numeric) else None,
    }
    measured = numeric.quantile(list(quantiles)) if len(numeric) else pd.Series(dtype=float)
    for quantile in quantiles:
        output[f"q{quantile:g}"] = (
            float(measured.loc[quantile]) if quantile in measured.index else None
        )
    return output


def minimum_stop_distance(
    spread_floor_price: float, additional_cost_price: float, maximum_cost_r: float
) -> float:
    if spread_floor_price < 0 or additional_cost_price < 0 or maximum_cost_r <= 0:
        raise ValueError("invalid cost geometry")
    return (spread_floor_price + additional_cost_price) / maximum_cost_r


def _active_tick_records(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        [
            dict(row)
            for row in record["files"]
            if str(row["relative_path"]).startswith("XAUUSD_ticks_")
            and int(row.get("row_count") or 0) > 0
        ],
        key=lambda row: str(row["relative_path"]),
    )


def _file_record(record: Mapping[str, Any], relative_path: str) -> dict[str, Any]:
    matches = [
        dict(row) for row in record["files"] if str(row["relative_path"]) == relative_path
    ]
    if len(matches) != 1:
        raise BrokerCostCalibrationError(
            f"expected one C02 file record for {record['account_label']}:{relative_path}"
        )
    return matches[0]


def _tick_date(filename: str) -> str:
    value = filename.removeprefix("XAUUSD_ticks_").removesuffix(".csv")
    if len(value) != 8 or not value.isdigit():
        raise BrokerCostCalibrationError(f"invalid C02 tick filename: {filename}")
    return f"{value[:4]}-{value[4:6]}-{value[6:]}"


def _boundary_quote(path: Path, *, first: bool) -> tuple[str, ...]:
    columns = ("time_msc", "bid", "ask", "spread_price", "spread_points")
    with path.open("rb") as handle:
        header_line = handle.readline().decode("utf-8").strip()
        if first:
            data_line = handle.readline().decode("utf-8").strip()
        else:
            data_line = _last_nonempty_line(handle).decode("utf-8").strip()
    if not header_line or not data_line:
        raise BrokerCostCalibrationError(f"tick file has no data rows: {path}")
    header = next(csv.reader([header_line]))
    values = next(csv.reader([data_line]))
    row = dict(zip(header, values, strict=True))
    return tuple(str(row[column]) for column in columns)


def _last_nonempty_line(handle: Any) -> bytes:
    handle.seek(0, os.SEEK_END)
    position = handle.tell()
    buffer = bytearray()
    while position > 0:
        position -= 1
        handle.seek(position)
        value = handle.read(1)
        if value in (b"\n", b"\r"):
            if buffer:
                break
            continue
        buffer.extend(value)
    return bytes(reversed(buffer))


def render_report(payload: Mapping[str, Any]) -> str:
    price = payload["broker_spread_price"]
    overlap = payload["dukascopy_overlap"]
    cost = payload["locked_cost_assumption"]
    quality = payload["quality_gates"]
    lines = [
        "# A3 ML Broker Cost Calibration V1 Report",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        "## Canonical Broker Feed",
        "",
        f"- Tick rows: `{payload['canonical_tick_audit']['tick_rows']}`",
        f"- Active UTC files: `{payload['canonical_tick_audit']['active_tick_files']}`",
        f"- Spread median: `{price['q0.5']:.6f}`",
        f"- Spread 90th percentile: `{price['q0.9']:.6f}`",
        f"- Spread 99th percentile: `{price['q0.99']:.6f}`",
        f"- Spread maximum: `{price['q1']:.6f}`",
        "",
        "## Dukascopy Overlap",
        "",
        f"- Matched M5 bars: `{overlap['matched_m5_bars']}`",
        f"- Broker M5 median-spread median: `{overlap['broker_spread_median']['q0.5']:.6f}`",
        f"- Dukascopy mean-spread median: `{overlap['dukascopy_spread_mean']['q0.5']:.6f}`",
        f"- Broker p90 spread/ATR median: `{overlap['broker_spread_p90_atr']['q0.5']:.6f}`",
        f"- Dukascopy open spread/ATR median: `{overlap['dukascopy_open_spread_atr']['q0.5']:.6f}`",
        "",
        "## Locked Cost Geometry",
        "",
        f"- Broker spread floor: `{cost['broker_spread_floor_price']:.6f}`",
        f"- Additional execution cost in price: `{cost['additional_execution_cost_price']:.6f}`",
        f"- Total stressed entry cost in price: `{cost['total_stressed_entry_cost_price']:.6f}`",
        f"- Maximum cost/R: `{cost['maximum_total_stressed_entry_cost_r']:.4f}`",
        f"- Minimum initial stop distance: `{cost['minimum_initial_stop_distance_price']:.6f}`",
        "",
        "## Quality Gates",
        "",
    ]
    lines.extend(
        f"- {name}: `{'PASS' if passed else 'FAIL'}`"
        for name, passed in quality.items()
    )
    lines.extend(
        [
            "",
            "## Authorization",
            "",
            "- Strategy authorization: `false`",
            "- Model training authorization: `false`",
            "- Demo or live authorization: `false`",
            "",
        ]
    )
    return "\n".join(lines)
