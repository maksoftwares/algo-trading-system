from __future__ import annotations

import calendar
from functools import lru_cache
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT.parent
REPO = ROOT.parents[2]
PARITY_SECTIONS = ("data_quality", "feature", "episode", "simulation", "gates")
HOUR_MS = 3_600_000
DAY_MS = 24 * HOUR_MS


def load_config(root: Path = ROOT) -> dict[str, Any]:
    path = root / "config" / "dukascopy_microburst_replication_v25.json"
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(payload: Mapping[str, Any], omitted_key: str) -> str:
    work = dict(payload)
    work.pop(omitted_key, None)
    encoded = json.dumps(
        work,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def storage_root(config: Mapping[str, Any]) -> Path:
    source = config["source"]
    return Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()


def file_record(path: Path, base: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": resolved.relative_to(base.resolve()).as_posix(),
        "bytes": int(resolved.stat().st_size),
        "sha256": sha256_file(resolved),
    }


def verify_record(record: Mapping[str, Any], base: Path, label: str) -> Path:
    path = (base / str(record["path"])).resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} path escaped its root: {path}") from exc
    if not path.is_file():
        raise FileNotFoundError(path)
    if int(path.stat().st_size) != int(record["bytes"]):
        raise ValueError(f"{label} size changed: {record['path']}")
    if sha256_file(path) != str(record["sha256"]):
        raise ValueError(f"{label} hash changed: {record['path']}")
    return path


def frozen_v24_root(config: Mapping[str, Any]) -> Path:
    return (ROOT / str(config["frozen_v24_1"]["root_relative"])).resolve()


def load_locked_v24(config: Mapping[str, Any]) -> ModuleType:
    frozen = config["frozen_v24_1"]
    dependency_root = frozen_v24_root(config)
    paths_and_hashes = (
        (frozen["config_relative"], frozen["config_file_sha256"]),
        (frozen["module_relative"], frozen["module_file_sha256"]),
        (frozen["contract_relative"], frozen["contract_file_sha256"]),
    )
    for relative, expected_hash in paths_and_hashes:
        path = dependency_root / str(relative)
        if not path.is_file() or sha256_file(path) != str(expected_hash):
            raise ValueError(f"V25 frozen V24.1 dependency changed: {path}")
    contract = json.loads(
        (dependency_root / str(frozen["contract_relative"])).read_text(
            encoding="utf-8"
        )
    )
    if str(contract["contract_sha256"]) != str(frozen["contract_sha256"]):
        raise ValueError("V25 V24.1 contract identity changed")
    module_path = dependency_root / str(frozen["module_relative"])
    spec = importlib.util.spec_from_file_location("v25_locked_v24_microburst", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def assert_frozen_rule_parity(
    config: Mapping[str, Any], v24: ModuleType | None = None
) -> None:
    module = v24 or load_locked_v24(config)
    origin = module.load_config(frozen_v24_root(config))
    differences = [key for key in PARITY_SECTIONS if config[key] != origin[key]]
    if differences:
        raise ValueError(f"V25 rule differs from frozen V24.1: {differences}")


def _month_periods(config: Mapping[str, Any]) -> pd.PeriodIndex:
    source = config["source"]
    start = pd.Timestamp(source["start_inclusive_utc"]).tz_localize(None).to_period("M")
    end = (
        pd.Timestamp(source["end_exclusive_utc"]).tz_localize(None).to_period("M")
        - 1
    )
    return pd.period_range(start, end, freq="M")


def _validate_inventory(config: Mapping[str, Any], root: Path) -> tuple[Path, dict[str, Any]]:
    source = config["source"]
    path = root / str(source["source_inventory"])
    if sha256_file(path) != str(source["source_inventory_sha256"]):
        raise ValueError("V25 source inventory hash changed")
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected_count = int(source["raw_month_manifest_count"])
    rows = list(payload["inventory"]["rows"])
    checks = {
        "symbol": str(payload["symbol"]) == str(source["symbol"]),
        "start_month": str(payload["locked_period"]["start_month"])
        == str(_month_periods(config)[0]),
        "end_month": str(payload["locked_period"]["end_month"])
        == str(_month_periods(config)[-1]),
        "expected_months": int(payload["inventory"]["expected_months"])
        == expected_count,
        "valid_months": int(payload["inventory"]["valid_months"]) == expected_count,
        "invalid_months": int(payload["inventory"]["invalid_months"]) == 0,
        "missing_months": int(payload["inventory"]["missing_months"]) == 0,
        "ready": bool(payload["inventory"]["ready"]),
        "row_count": len(rows) == expected_count,
    }
    if not all(checks.values()):
        raise ValueError(f"V25 source inventory is not complete: {checks}")
    return path, payload


def build_source_manifest(config: Mapping[str, Any]) -> dict[str, Any]:
    root = storage_root(config)
    source = config["source"]
    inventory_path, inventory = _validate_inventory(config, root)
    inventory_rows = {str(row["month"]): row for row in inventory["inventory"]["rows"]}
    raw_root = root / str(source["raw_tick_root"])
    monthly_records: list[dict[str, Any]] = []
    for period in _month_periods(config):
        month = str(period)
        month_root = raw_root / f"year={period.year:04d}" / f"month={period.month:02d}"
        acquisition_path = month_root / "_ACQUISITION_MANIFEST.json"
        frozen_path = month_root / "_FROZEN_MANIFEST.json"
        acquisition = json.loads(acquisition_path.read_text(encoding="utf-8"))
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
        expected_hours = calendar.monthrange(period.year, period.month)[1] * 24
        rows = list(acquisition.get("rows", []))
        expected_hour_ids = {
            hour.strftime("%Y%m%d%H")
            for hour in pd.date_range(period.start_time, periods=expected_hours, freq="h")
        }
        actual_hour_ids = {Path(str(row["path"])).stem for row in rows}
        acquisition_ok = (
            str(acquisition.get("month")) == month
            and str(acquisition.get("symbol")) == str(source["symbol"])
            and len(rows) == expected_hours
            and actual_hour_ids == expected_hour_ids
            and all(str(row.get("symbol")) == str(source["symbol"]) for row in rows)
            and all(
                str(row.get("status")) in {"DOWNLOADED_VALID", "RESUMED_VALID"}
                for row in rows
            )
            and all(int(row.get("bytes", -1)) >= 0 for row in rows)
            and all(int(row.get("tick_count", -1)) >= 0 for row in rows)
            and all(len(str(row.get("sha256", ""))) == 64 for row in rows)
        )
        frozen_ok = (
            str(frozen.get("month")) == month
            and str(frozen.get("symbol")) == str(source["symbol"])
            and bool(frozen.get("complete"))
            and bool(frozen.get("frozen"))
            and int(frozen.get("expected_hour_files", -1)) == expected_hours
            and int(frozen.get("observed_hour_files", -1)) == expected_hours
            and len(str(frozen.get("files_sha256", ""))) == 64
        )
        inventory_row = inventory_rows.get(month)
        inventory_ok = bool(
            inventory_row
            and str(inventory_row.get("status")) == "VALID"
            and bool(inventory_row.get("frozen"))
            and int(inventory_row.get("hour_files", -1)) == expected_hours
            and int(inventory_row.get("bytes", -1))
            == (
                sum(int(row["bytes"]) for row in rows)
                + int(acquisition_path.stat().st_size)
                + int(frozen_path.stat().st_size)
            )
            and len(str(inventory_row.get("partition_signature", ""))) == 64
        )
        if not acquisition_ok or not frozen_ok or not inventory_ok:
            raise ValueError(
                f"V25 month is not frozen and internally consistent: {month} "
                f"acquisition={acquisition_ok} frozen={frozen_ok} inventory={inventory_ok}"
            )
        monthly_records.append(
            {
                "month": month,
                "hour_files": expected_hours,
                "raw_bytes": int(sum(int(row["bytes"]) for row in rows)),
                "tick_count": int(sum(int(row["tick_count"]) for row in rows)),
                "partition_signature": str(inventory_row["partition_signature"]),
                "files_sha256": str(frozen["files_sha256"]),
                "acquisition_manifest": file_record(acquisition_path, root),
                "frozen_manifest": file_record(frozen_path, root),
            }
        )
    manifest: dict[str, Any] = {
        "schema_version": "xauusd_dukascopy_microburst_v25_source_manifest",
        "symbol": source["symbol"],
        "window": {
            "start_inclusive_utc": source["start_inclusive_utc"],
            "end_exclusive_utc": source["end_exclusive_utc"],
        },
        "source_inventory": file_record(inventory_path, root),
        "month_count": len(monthly_records),
        "hour_file_count": int(sum(row["hour_files"] for row in monthly_records)),
        "raw_bytes": int(sum(row["raw_bytes"] for row in monthly_records)),
        "tick_count": int(sum(row["tick_count"] for row in monthly_records)),
        "months": monthly_records,
        "candidate_generation_performed": False,
        "economic_outcomes_opened": False,
        "paid_data_used": False,
    }
    manifest["manifest_sha256"] = canonical_hash(manifest, "manifest_sha256")
    return manifest


def verify_source_manifest(
    manifest: Mapping[str, Any], config: Mapping[str, Any]
) -> None:
    if canonical_hash(manifest, "manifest_sha256") != str(manifest["manifest_sha256"]):
        raise ValueError("V25 source manifest self-hash changed")
    source = config["source"]
    checks = {
        "symbol": str(manifest["symbol"]) == str(source["symbol"]),
        "start": str(manifest["window"]["start_inclusive_utc"])
        == str(source["start_inclusive_utc"]),
        "end": str(manifest["window"]["end_exclusive_utc"])
        == str(source["end_exclusive_utc"]),
        "months": int(manifest["month_count"])
        == int(source["raw_month_manifest_count"]),
        "no_candidates": not bool(manifest["candidate_generation_performed"]),
        "no_outcomes": not bool(manifest["economic_outcomes_opened"]),
        "free_source": not bool(manifest["paid_data_used"]),
    }
    if not all(checks.values()):
        raise ValueError(f"V25 source manifest controls failed: {checks}")


def decode_hour_payload(
    payload: Mapping[str, Any], hour: pd.Timestamp, price_decimals: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    required = (
        "timestamp",
        "multiplier",
        "bid",
        "ask",
        "times",
        "bids",
        "asks",
        "bidVolumes",
        "askVolumes",
    )
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"V25 Dukascopy fields missing: {missing}")
    arrays = ("times", "bids", "asks", "bidVolumes", "askVolumes")
    lengths = [len(payload[key]) for key in arrays]
    if len(set(lengths)) != 1:
        raise ValueError(f"V25 Dukascopy arrays differ: {lengths}")
    hour_start_ms = int(hour.value // 1_000_000)
    if int(payload["timestamp"]) != hour_start_ms:
        raise ValueError("V25 Dukascopy payload timestamp differs from its source hour")
    if lengths[0] == 0:
        empty_i = np.array([], dtype=np.int64)
        empty_f = np.array([], dtype=float)
        return empty_i, empty_f, empty_f.copy()
    multiplier = float(payload["multiplier"])
    if not np.isfinite(multiplier) or multiplier <= 0.0:
        raise ValueError("V25 Dukascopy multiplier is invalid")
    deltas = np.asarray(payload["times"], dtype=np.int64)
    if bool(np.any(deltas < 0)):
        raise ValueError("V25 Dukascopy time delta is negative")
    times = hour_start_ms + np.cumsum(deltas, dtype=np.int64)
    if times[0] < hour_start_ms or times[-1] >= hour_start_ms + HOUR_MS:
        raise ValueError("V25 Dukascopy ticks escape their source hour")
    factor = float(10**price_decimals)
    bids = np.floor(
        (
            float(payload["bid"])
            + np.cumsum(np.asarray(payload["bids"], dtype=float)) * multiplier
        )
        * factor
        + 0.5
        + 1e-9
    ) / factor
    asks = np.floor(
        (
            float(payload["ask"])
            + np.cumsum(np.asarray(payload["asks"], dtype=float)) * multiplier
        )
        * factor
        + 0.5
        + 1e-9
    ) / factor
    if bool(
        np.any(~np.isfinite(bids))
        or np.any(~np.isfinite(asks))
        or np.any(bids <= 0.0)
        or np.any(asks < bids)
    ):
        raise ValueError("V25 Dukascopy quote is invalid")
    return times, bids, asks


class VerifiedDukascopyStore:
    def __init__(self, config: Mapping[str, Any], manifest: Mapping[str, Any]) -> None:
        verify_source_manifest(manifest, config)
        self.config = config
        self.root = storage_root(config)
        self.source = config["source"]
        self.months = {str(row["month"]): row for row in manifest["months"]}
        self._monthly_rows: dict[str, dict[str, Any]] = {}
        self._verified_raw: dict[str, dict[str, Any]] = {}
        self.start_ms = int(
            pd.Timestamp(self.source["start_inclusive_utc"]).value // 1_000_000
        )
        self.end_ms = int(
            pd.Timestamp(self.source["end_exclusive_utc"]).value // 1_000_000
        )

    def _load_month(self, month: str) -> dict[str, Any]:
        if month in self._monthly_rows:
            return self._monthly_rows[month]
        record = self.months.get(month)
        if record is None:
            raise ValueError(f"V25 source month is outside the lock: {month}")
        acquisition_path = verify_record(
            record["acquisition_manifest"], self.root, "V25 acquisition manifest"
        )
        verify_record(record["frozen_manifest"], self.root, "V25 frozen manifest")
        acquisition = json.loads(acquisition_path.read_text(encoding="utf-8"))
        rows = {str(row["path"]): row for row in acquisition["rows"]}
        if len(rows) != int(record["hour_files"]):
            raise ValueError(f"V25 acquisition manifest row count changed: {month}")
        self._monthly_rows[month] = rows
        return rows

    @lru_cache(maxsize=72)
    def load_hour(
        self, hour_key: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        hour_ms = int(hour_key) * HOUR_MS
        if hour_ms < self.start_ms or hour_ms >= self.end_ms:
            empty_i = np.array([], dtype=np.int64)
            empty_f = np.array([], dtype=float)
            return empty_i, empty_f, empty_f.copy()
        hour = pd.Timestamp(hour_ms, unit="ms", tz="UTC")
        month = hour.strftime("%Y-%m")
        relative = (
            Path(str(self.source["raw_tick_root"]))
            / f"year={hour.year:04d}"
            / f"month={hour.month:02d}"
            / f"{hour:%Y%m%d%H}.json"
        ).as_posix()
        row = self._load_month(month).get(relative)
        if row is None:
            raise FileNotFoundError(f"V25 locked hour is missing: {relative}")
        path = (self.root / relative).resolve()
        raw = path.read_bytes()
        if len(raw) != int(row["bytes"]) or sha256_bytes(raw) != str(row["sha256"]):
            raise ValueError(f"V25 raw hour changed: {relative}")
        payload = json.loads(raw)
        arrays = decode_hour_payload(payload, hour, int(self.source["price_decimals"]))
        if len(arrays[0]) != int(row["tick_count"]):
            raise ValueError(f"V25 raw hour tick count changed: {relative}")
        self._verified_raw[relative] = {
            "path": relative,
            "bytes": int(row["bytes"]),
            "sha256": str(row["sha256"]),
            "tick_count": int(row["tick_count"]),
        }
        return arrays

    def load_context(
        self, day: pd.Timestamp, stage_end_ms: int
    ) -> tuple[pd.DataFrame, pd.DataFrame, int]:
        day_start_ms = int(day.value // 1_000_000)
        day_end_ms = day_start_ms + DAY_MS
        context_start_ms = max(self.start_ms, day_start_ms - HOUR_MS)
        context_end_ms = min(self.end_ms, int(stage_end_ms), day_end_ms + HOUR_MS)
        first_hour = context_start_ms // HOUR_MS
        final_hour = (context_end_ms - 1) // HOUR_MS
        chunks: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
        for hour_key in range(first_hour, final_hour + 1):
            arrays = self.load_hour(hour_key)
            if len(arrays[0]):
                chunks.append(arrays)
        columns = ("tick_time_msc", "bid", "ask", "spread_price", "date_utc")
        if not chunks:
            empty = pd.DataFrame(columns=columns)
            return empty, empty.copy(), 0
        times = np.concatenate([chunk[0] for chunk in chunks])
        bids = np.concatenate([chunk[1] for chunk in chunks])
        asks = np.concatenate([chunk[2] for chunk in chunks])
        in_day_raw = (times >= day_start_ms) & (times < day_end_ms)
        raw_day_rows = int(in_day_raw.sum())
        raw = pd.DataFrame({"tick_time_msc": times, "bid": bids, "ask": asks})
        raw = raw.sort_values("tick_time_msc", kind="mergesort")
        ticks = raw.drop_duplicates("tick_time_msc", keep="last").reset_index(drop=True)
        ticks["spread_price"] = ticks["ask"] - ticks["bid"]
        ticks["date_utc"] = pd.to_datetime(
            ticks["tick_time_msc"], unit="ms", utc=True
        ).dt.strftime("%Y-%m-%d")
        day_ticks = ticks.loc[
            ticks["tick_time_msc"].ge(day_start_ms)
            & ticks["tick_time_msc"].lt(day_end_ms)
        ].reset_index(drop=True)
        return ticks.loc[:, columns], day_ticks.loc[:, columns], raw_day_rows

    def source_audit(self) -> dict[str, Any]:
        records = sorted(self._verified_raw.values(), key=lambda row: str(row["path"]))
        digest_payload = {"files": records}
        return {
            "verified_hour_files": len(records),
            "verified_raw_bytes": int(sum(row["bytes"] for row in records)),
            "verified_tick_rows": int(sum(row["tick_count"] for row in records)),
            "verified_file_record_sha256": canonical_hash(digest_payload, "unused"),
            "all_loaded_hours_sha256_verified": True,
        }


def maximum_label_path_ms(config: Mapping[str, Any]) -> int:
    simulation = config["simulation"]
    return (
        int(simulation["maximum_entry_delay_ms"])
        + int(simulation["hold_seconds"]) * 1000
        + int(simulation["maximum_exit_delay_ms"])
    )


def label_path_within_stage(
    candidate_time_ms: int, stage_end_ms: int, config: Mapping[str, Any]
) -> bool:
    return int(candidate_time_ms) + maximum_label_path_ms(config) < int(stage_end_ms)


def _empty_quality_record(day: pd.Timestamp) -> dict[str, Any]:
    return {
        "date_utc": day.strftime("%Y-%m-%d"),
        "weekday": int(day.weekday()),
        "unique_quotes": 0,
        "start_offset_hours": None,
        "end_offset_hours": None,
        "p99_interquote_gap_ms": None,
        "raw_rows": 0,
        "unique_milliseconds": 0,
        "duplicate_millisecond_rows": 0,
        "duplicate_millisecond_share": 0.0,
        "eligible_full_weekday": False,
    }


def _stable_concat(frames: Iterable[pd.DataFrame], columns: Iterable[str]) -> pd.DataFrame:
    materialized = [frame for frame in frames if not frame.empty]
    if not materialized:
        return pd.DataFrame(columns=list(columns))
    return pd.concat(materialized, ignore_index=True).loc[:, list(columns)]


def evaluate_replication_stage(
    config: Mapping[str, Any],
    stage: Mapping[str, Any],
    store: VerifiedDukascopyStore,
    v24: ModuleType,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    assert_frozen_rule_parity(config, v24)
    start = pd.Timestamp(stage["start_inclusive_utc"])
    end = pd.Timestamp(stage["end_exclusive_utc"])
    start_ms = int(start.value // 1_000_000)
    end_ms = int(end.value // 1_000_000)
    days = pd.date_range(start.normalize(), end - pd.Timedelta(days=1), freq="D")
    candidate_frames: list[pd.DataFrame] = []
    trade_frames: list[pd.DataFrame] = []
    quality_records: list[dict[str, Any]] = []
    eligible_dates: list[str] = []
    candidate_columns = [*v24.CANDIDATE_COLUMNS, "evidence_partition"]

    for day in days:
        context, day_ticks, raw_day_rows = store.load_context(day, end_ms)
        date_utc = day.strftime("%Y-%m-%d")
        if day_ticks.empty:
            quality_records.append(_empty_quality_record(day))
            continue
        unique_rows = int(len(day_ticks))
        raw_daily = pd.DataFrame(
            {
                "date_utc": [date_utc],
                "raw_rows": [raw_day_rows],
                "unique_milliseconds": [unique_rows],
                "duplicate_millisecond_rows": [raw_day_rows - unique_rows],
                "duplicate_millisecond_share": [
                    (raw_day_rows - unique_rows) / raw_day_rows
                    if raw_day_rows
                    else 0.0
                ],
            }
        )
        quality = v24.assess_full_days(day_ticks, raw_daily, config)
        if len(quality) != 1:
            raise ValueError(f"V25 expected one source-quality row for {date_utc}")
        quality_record = quality.iloc[0].to_dict()
        quality_records.append(quality_record)
        eligible = bool(quality_record["eligible_full_weekday"])
        if eligible:
            eligible_dates.append(date_utc)

        generated, _ = v24.generate_candidates(context, config)
        selected = generated.loc[
            generated["date_utc"].eq(date_utc)
            & generated["tick_time_msc"].ge(start_ms)
            & generated["tick_time_msc"].map(
                lambda value: label_path_within_stage(int(value), end_ms, config)
            )
        ].copy()
        selected["evidence_partition"] = str(stage["id"])
        selected = selected.loc[:, candidate_columns]
        candidate_frames.append(selected)
        if eligible and not selected.empty:
            trade_frames.append(
                v24.simulate_trades(
                    context,
                    selected,
                    [date_utc],
                    str(stage["id"]),
                    config,
                )
            )

    candidates = _stable_concat(candidate_frames, candidate_columns)
    trade_columns = (
        "evidence_partition",
        "date_utc",
        "utc_block_start_ms",
        "candidate_time_utc",
        "candidate_time_msc",
        "side",
        "signed_update_imbalance",
        "displacement_price",
        "entry_time_msc",
        "entry_delay_ms",
        "entry_bid",
        "entry_ask",
        "exit_time_msc",
        "exit_delay_ms",
        "exit_bid",
        "exit_ask",
        "observed_bidask_move",
        "base_pnl_dollars",
        "stress_pnl_dollars",
        "reference_lot",
    )
    trades = _stable_concat(trade_frames, trade_columns)
    quality_frame = pd.DataFrame(quality_records).sort_values("date_utc")
    if not eligible_dates:
        raise ValueError(f"V25 stage has no eligible full weekdays: {stage['id']}")
    frozen_audit, daily = v24.evaluate_stage(
        trades, eligible_dates, str(stage["id"]), config
    )
    frozen_audit.pop("audit_sha256", None)
    audit: dict[str, Any] = {
        "schema_version": "xauusd_dukascopy_microburst_v25_stage_audit",
        "evidence_partition": str(stage["id"]),
        "stage_window": {
            "start_inclusive_utc": str(stage["start_inclusive_utc"]),
            "end_exclusive_utc": str(stage["end_exclusive_utc"]),
        },
        "eligible_full_weekdays": len(eligible_dates),
        "calendar_days_inspected": len(days),
        "candidate_count_all_source_days": int(len(candidates)),
        "candidate_count_eligible_days": int(
            candidates["date_utc"].isin(eligible_dates).sum()
        ),
        "executable_trade_count": int(len(trades)),
        "maximum_label_path_ms": maximum_label_path_ms(config),
        "stage_boundary_label_purge_applied": True,
        "frozen_v24_1_gate_audit": frozen_audit,
        "gate_passed": bool(frozen_audit["gate_passed"]),
        "decision": (
            f"V25_{stage['id']}_PASS_NEXT_STAGE_REMAINS_SEALED"
            if bool(frozen_audit["gate_passed"])
            else f"V25_{stage['id']}_FAIL_TERMINAL"
        ),
        "source_audit": store.source_audit(),
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "broker_action_authorized": False,
    }
    return candidates, trades, daily, quality_frame, audit


def stage_artifact_names(stage: Mapping[str, Any]) -> dict[str, str]:
    prefix = str(stage["artifact_prefix"])
    return {
        "candidates": f"{prefix}_CANDIDATES.csv",
        "trades": f"{prefix}_TRADES.csv",
        "daily": f"{prefix}_DAILY.csv",
        "quality": f"{prefix}_SOURCE_QUALITY.csv",
        "audit": f"{prefix}_AUDIT.json",
    }


def first_runnable_stage(
    config: Mapping[str, Any], existing_audits: Mapping[str, Mapping[str, Any]]
) -> Mapping[str, Any] | None:
    for stage in config["stages"]:
        stage_id = str(stage["id"])
        if stage_id not in existing_audits:
            return stage
        if not bool(existing_audits[stage_id]["gate_passed"]):
            return None
    return None
