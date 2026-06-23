from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .contract_scope import BASE_FAMILY, load_contract_scope, normalize_family_name
from .market_data_export import _iso, _sha256_file, _table, _utc_now, _write_json_atomic, parse_utc


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "C02_NORMALIZATION_REPORT.json"
DEFAULT_DECISIONS_CSV = Path("outputs") / "reports" / "C02_NORMALIZED_DECISIONS.csv"
DEFAULT_TRADES_CSV = Path("outputs") / "reports" / "C02_NORMALIZED_TRADES.csv"
RAW_CANDIDATE_ID = "B0_RAW_ALL_SESSION"
SYMBOL = "XAUUSD"
FAMILY = BASE_FAMILY


def normalize_c02_snapshot(
    root: Path,
    dataset_version: str | None = None,
    report_json: Path | None = None,
) -> Path:
    root = root.resolve()
    pointer = _load_pointer(root)
    dataset_version = dataset_version or pointer["dataset_version"]
    dataset_root = Path(pointer["output_root"]) if dataset_version == pointer["dataset_version"] else root / "data" / "ml" / "a3_meta_v1" / "c02" / dataset_version
    normalized_root = dataset_root / "normalized"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    report_md = report_json.with_suffix(".md")

    contract_scope = load_contract_scope(root)
    source_files = _collect_source_files(dataset_root)
    signal_instances = _collect_signal_instances(dataset_version, dataset_root, set(contract_scope.active_families))
    decisions = _build_c01_decisions(signal_instances)
    bars_dir = normalized_root / "c01_bars"
    bars_outputs = _write_c01_bars(dataset_root, bars_dir)
    decisions_csv = root / DEFAULT_DECISIONS_CSV
    trades_csv = root / DEFAULT_TRADES_CSV
    source_files_csv = normalized_root / "source_files.csv"
    signal_instances_csv = normalized_root / "signals" / "signal_instances.csv"
    _write_csv(source_files_csv, source_files)
    _write_csv(signal_instances_csv, signal_instances)
    _write_csv(decisions_csv, decisions, _decision_fields())
    _write_csv(trades_csv, [], ["signal_id", "candidate_id", "outcome", "exit_time", "loss_class"])
    manifest = {
        "manifest_schema_version": "c02_normalization_manifest_v1",
        "dataset_version": dataset_version,
        "created_at_utc": _utc_now(),
        "source_files_csv": _file_record(source_files_csv, len(source_files)),
        "signal_instances_csv": _file_record(signal_instances_csv, len(signal_instances)),
        "decisions_csv": _file_record(decisions_csv, len(decisions)),
        "trades_csv": _file_record(trades_csv, 0),
        "bars_outputs": bars_outputs,
        "training_authorized": False,
        "broker_action_authorized": False,
        "contract_scope": contract_scope.scope_name,
        "active_families": list(contract_scope.active_families),
    }
    manifest_file = _write_json_atomic(normalized_root / "NORMALIZATION_MANIFEST.json", manifest)
    counts = {
        "source_files": len(source_files),
        "signal_instances": len(signal_instances),
        "c01_decisions": len(decisions),
        "would_signal_instances": sum(1 for row in signal_instances if row["would_signal"] == "true"),
        "by_account": _by_account(signal_instances, decisions),
    }
    payload = {
        "status": "PASS",
        "stage": "C02-04",
        "created_at_utc": _utc_now(),
        "dataset_version": dataset_version,
        "dataset_root": str(dataset_root),
        "normalized_root": str(normalized_root),
        "boundary": {
            "mt5_connection_attempted": False,
            "model_training_authorized": False,
            "broker_action_authorized": False,
            "terminal_runtime_change_authorized": False,
            "normalization_only": True,
        },
        "counts": counts,
        "contract_scope": {
            "scope_name": contract_scope.scope_name,
            "contract_expansion_authorized": contract_scope.contract_expansion_authorized,
            "active_families": list(contract_scope.active_families),
            "review_reference": contract_scope.review_reference,
        },
        "outputs": {
            "normalization_manifest": manifest_file["path"],
            "source_files_csv": str(source_files_csv),
            "signal_instances_csv": str(signal_instances_csv),
            "decisions_csv": str(decisions_csv),
            "trades_csv": str(trades_csv),
            "bars_dir": str(bars_dir),
        },
        "notes": [
            "C02 normalized decisions are staging rows only; no model training is authorized.",
            "Signal component times are reconstructed from the completed M5 bar before decision time for C01 compatibility and remain diagnostic until C03 grouping/label promotion.",
            "Trades CSV is intentionally empty until C02 fill reconciliation can map broker fills to source signal ids.",
        ],
        "next_allowed_stage": "C02-05 signal grouping and C01 ingestion audit",
    }
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_normalization_report_md(payload), encoding="utf-8")
    pointer["normalization_status"] = "PASS"
    pointer["normalization_report"] = str(report_json)
    pointer["c02_decisions_csv"] = str(decisions_csv)
    pointer["c02_trades_csv"] = str(trades_csv)
    pointer["c02_bars_dir"] = str(bars_dir)
    pointer["training_authorized"] = False
    _write_json_atomic(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer)
    return report_json


def render_normalization_report_md(payload: dict[str, Any]) -> str:
    rows = [
        {
            "Account": account,
            "Signal Instances": values["signal_instances"],
            "C01 Decisions": values["c01_decisions"],
            "Would Signals": values["would_signals"],
        }
        for account, values in payload["counts"]["by_account"].items()
    ]
    return "\n".join(
        [
            "# C02 Normalization Report",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Boundary",
            "",
            "- Stage: C02-04 normalized source tables.",
            "- MT5 connection attempted: false.",
            "- Model training authorized: false.",
            "- Broker action authorized: false.",
            "- Terminal runtime change authorized: false.",
            "",
            "## Counts",
            "",
            f"- Source files: {payload['counts']['source_files']}",
            f"- Signal instances: {payload['counts']['signal_instances']}",
            f"- Would-signal instances: {payload['counts']['would_signal_instances']}",
            f"- C01 decisions: {payload['counts']['c01_decisions']}",
            "",
            "## Accounts",
            "",
            _table(rows, ["Account", "Signal Instances", "Would Signals", "C01 Decisions"]),
            "",
            "## Outputs",
            "",
            f"- Decisions CSV: {payload['outputs']['decisions_csv']}",
            f"- Trades CSV: {payload['outputs']['trades_csv']}",
            f"- Bars dir: {payload['outputs']['bars_dir']}",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _collect_source_files(dataset_root: Path) -> list[dict[str, Any]]:
    rows = []
    for manifest in sorted(dataset_root.glob("raw/*/manifest/*MANIFEST.json")):
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        account_label = payload.get("account_label", manifest.parts[-3])
        for item in payload.get("files", []):
            row = dict(item)
            row["account_label"] = account_label
            row["manifest"] = str(manifest)
            rows.append(row)
    return rows


def _collect_signal_instances(dataset_version: str, dataset_root: Path, allowed_families: set[str] | None = None) -> list[dict[str, Any]]:
    allowed_families = allowed_families or {FAMILY}
    rows: list[dict[str, Any]] = []
    for manifest in sorted(dataset_root.glob("raw/*/manifest/HISTORY_LOG_MANIFEST.json")):
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        account_label = payload["account_label"]
        account_scope = payload["account_scope"]
        for source in payload.get("log_records", []):
            if "signal_log" not in source.get("source_type", ""):
                continue
            path_text = source.get("snapshot_path")
            if not path_text:
                continue
            path = Path(path_text)
            if not path.exists():
                continue
            for index, raw in enumerate(_read_csv(path), start=1):
                symbol = (raw.get("symbol") or raw.get("qualified_symbol") or "").upper()
                family = _family_from_source(source, raw)
                mapped = {
                    "dataset_version": dataset_version,
                    "account_scope": account_scope,
                    "account_label": account_label,
                    "source_type": source.get("source_type", ""),
                    "logical_source_name": source.get("logical_source_name", ""),
                    "source_file_sha256": source.get("sha256", ""),
                    "source_row_number": index,
                    "timestamp_utc": _normalize_time(raw.get("timestamp_utc") or raw.get("timestamp_broker") or ""),
                    "timestamp_broker_raw": raw.get("timestamp_broker", ""),
                    "run_id": raw.get("run_id", ""),
                    "account_server": raw.get("account_server", ""),
                    "symbol": symbol,
                    "candidate": raw.get("candidate") or family,
                    "family": family,
                    "magic": raw.get("magic", ""),
                    "stage": raw.get("stage", ""),
                    "direction": _normalize_direction(raw.get("direction", "")),
                    "would_signal": "true" if _truthy(raw.get("would_signal")) else "false",
                    "reason_code": raw.get("reason_code") or raw.get("guard_reason", ""),
                    "level_kind": raw.get("level_kind", ""),
                    "level_price": raw.get("level_price", ""),
                    "entry_price": raw.get("entry_price", ""),
                    "stop_loss": raw.get("stop_loss", ""),
                    "take_profit": raw.get("take_profit", ""),
                    "stop_distance_points": raw.get("stop_distance_points", ""),
                    "spread_points": raw.get("spread_points", ""),
                    "estimated_cost_R": raw.get("estimated_cost_R") or raw.get("cost_R") or "",
                    "m5_bar_time": _normalize_time(raw.get("m5_bar_time", "")),
                    "schema_mapping_status": "MAPPED_COMMON_SIGNAL_COLUMNS",
                }
                if mapped["symbol"] == SYMBOL and mapped["family"] in allowed_families:
                    rows.append(mapped)
    rows.sort(key=lambda row: (row["account_scope"], row["timestamp_utc"], row["logical_source_name"], int(row["source_row_number"])))
    return rows


def _build_c01_decisions(signal_instances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions = []
    seen = set()
    for row in signal_instances:
        if row["would_signal"] != "true":
            continue
        direction = _normalize_direction(row["direction"])
        if direction not in {"LONG", "SHORT"}:
            continue
        decision_time = _parse_time(row["timestamp_utc"])
        completed_bar_time = _floor_m5(decision_time) - timedelta(minutes=5)
        level = _first_float(row.get("level_price"), row.get("entry_price"))
        if level is None:
            continue
        break_time = completed_bar_time - timedelta(minutes=10)
        retest_time = completed_bar_time - timedelta(minutes=5)
        confirmation_time = completed_bar_time
        family = row["family"]
        signal_id = "|".join(
            [
                row["account_scope"],
                SYMBOL,
                family,
                direction,
                _iso_no_t(break_time),
                _iso_no_t(retest_time),
                _iso_no_t(confirmation_time),
                f"{level:.2f}",
            ]
        )
        unique = (signal_id, row["logical_source_name"], row["source_row_number"])
        if unique in seen:
            continue
        seen.add(unique)
        decisions.append(
            {
                "signal_id": signal_id,
                "candidate_id": RAW_CANDIDATE_ID,
                "decision_time": _iso_no_t(decision_time),
                "opened": "false",
                "reason": row.get("reason_code", ""),
                "session_bucket": _session_bucket(decision_time),
                "cost_R": row.get("estimated_cost_R", ""),
                "final_r_if_raw": "",
                "source_logical_source_name": row["logical_source_name"],
                "source_file_sha256": row["source_file_sha256"],
                "source_row_number": row["source_row_number"],
                "schema_mapping_status": "DIAGNOSTIC_COMPONENT_TIMES_FROM_COMPLETED_DECISION_BAR",
            }
        )
    decisions.sort(key=lambda row: row["decision_time"])
    return decisions


def _write_c01_bars(dataset_root: Path, bars_dir: Path) -> list[dict[str, Any]]:
    bars_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for timeframe, minutes in (("M5", 5), ("H1", 60), ("D1", 1440)):
        source = dataset_root / "raw" / "A1" / "bars" / f"XAUUSD_{timeframe}.csv"
        rows = []
        for raw in _read_csv(source):
            start = _parse_time(raw["time_utc"])
            rows.append(
                {
                    "bar_start_utc": _iso_no_t(start),
                    "bar_end_utc": _iso_no_t(start + timedelta(minutes=minutes)),
                    "open": raw.get("open", ""),
                    "high": raw.get("high", ""),
                    "low": raw.get("low", ""),
                    "close": raw.get("close", ""),
                    "tick_volume": raw.get("tick_volume", ""),
                    "spread": raw.get("spread", ""),
                }
            )
        target = bars_dir / f"XAUUSD_{timeframe}_20260601_to_latest.csv"
        _write_csv(target, rows, ["bar_start_utc", "bar_end_utc", "open", "high", "low", "close", "tick_volume", "spread"])
        outputs.append(_file_record(target, len(rows)))
    return outputs


def _by_account(signal_instances: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    instances = Counter(row["account_label"] for row in signal_instances)
    would = Counter(row["account_label"] for row in signal_instances if row["would_signal"] == "true")
    decision_counts: Counter[str] = Counter()
    for row in decisions:
        decision_counts[_account_label(row["signal_id"].split("|")[0])] += 1
    labels = sorted(set(instances) | set(would) | set(decision_counts))
    return {
        label: {
            "signal_instances": instances[label],
            "would_signals": would[label],
            "c01_decisions": decision_counts[label],
        }
        for label in labels
    }


def _load_pointer(root: Path) -> dict[str, Any]:
    return json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = fieldnames or sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _file_record(path: Path, row_count: int) -> dict[str, Any]:
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
        "row_count": row_count,
    }


def _decision_fields() -> list[str]:
    return [
        "signal_id",
        "candidate_id",
        "decision_time",
        "opened",
        "reason",
        "session_bucket",
        "cost_R",
        "final_r_if_raw",
        "source_logical_source_name",
        "source_file_sha256",
        "source_row_number",
        "schema_mapping_status",
    ]


def _family_from_source(source: dict[str, Any], row: dict[str, str]) -> str:
    return normalize_family_name(
        row.get("candidate"),
        row.get("comment"),
        source.get("family"),
        source.get("filename"),
        source.get("logical_source_name"),
    )


def _normalize_direction(value: str) -> str:
    text = str(value).strip().upper()
    if text in {"BUY", "LONG"}:
        return "LONG"
    if text in {"SELL", "SHORT"}:
        return "SHORT"
    return text


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _normalize_time(value: str) -> str:
    if not value:
        return ""
    try:
        return _iso_no_t(_parse_time(value))
    except ValueError:
        return ""


def _parse_time(value: str) -> datetime:
    text = str(value).strip().replace("T", " ").replace("Z", "").replace("+00:00", "")
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def _iso_no_t(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat(sep=" ").replace("+00:00", "Z")


def _floor_m5(value: datetime) -> datetime:
    return value.replace(minute=(value.minute // 5) * 5, second=0, microsecond=0)


def _first_float(*values: Any) -> float | None:
    for value in values:
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if not math.isnan(number) and not math.isinf(number) and number > 0:
            return number
    return None


def _session_bucket(timestamp: datetime) -> str:
    minutes = timestamp.hour * 60 + timestamp.minute
    if 6 * 60 <= minutes < 12 * 60:
        return "Morning 06:00-11:59"
    if 12 * 60 <= minutes < 16 * 60:
        return "Afternoon 12:00-15:59"
    if 16 * 60 <= minutes < 20 * 60:
        return "Evening 16:00-19:59"
    return "Night 20:00-05:59"


def _account_label(scope: str) -> str:
    return {"1025742": "A1", "1033030": "A2", "1033669": "A3"}.get(scope, scope)
