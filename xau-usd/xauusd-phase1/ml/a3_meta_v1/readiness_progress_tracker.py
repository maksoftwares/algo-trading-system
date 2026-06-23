from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_READINESS_PROGRESS_TRACKER_STATUS.json"
SCHEMA_VERSION = "a3_ml_readiness_progress_tracker_status_v1"
STATUS_READY = "COLLECTING_LIVE_PROGRESS_TRACKED"
STATUS_NO_DELTA = "COLLECTING_BUT_NO_DATASET_DELTA"
STATUS_REGRESSION = "DATA_REGRESSION_REVIEW_REQUIRED"
STATUS_INCOMPLETE = "DATASET_ARTIFACTS_INCOMPLETE"
STATUS_WAITING = "WAITING_FOR_MORE_DATASETS"


def generate_readiness_progress_tracker(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    c02_root = root / "data" / "ml" / "a3_meta_v1" / "c02"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    c03 = _read_json(reports / "C03_TRAINING_READINESS_REPORT.json")
    c33 = _read_json(reports / "A3_ML_DEMO_SHADOW_COLLECTION_HEALTH_STATUS.json")
    slippage = _read_json(reports / "C02_SLIPPAGE_READINESS.json")
    datasets = [_dataset_summary(path) for path in _dataset_dirs(c02_root)]
    latest = _select_latest(datasets, pointer.get("dataset_version", ""))
    previous = _previous_dataset(datasets, latest.get("dataset_version", ""))
    delta = _delta(latest, previous)
    current_gate_gaps = _current_gate_gaps(c03)
    regression_warnings = _regression_warnings(delta)
    completeness_warnings = _completeness_warnings(latest)
    payload = {
        "status": _status(datasets, latest, delta, regression_warnings),
        "stage": "C46-READINESS-PROGRESS-TRACKER",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": latest.get("dataset_version", pointer.get("dataset_version", "")),
        "dataset_count": len(datasets),
        "latest_dataset": latest,
        "previous_dataset": previous,
        "delta_from_previous": delta,
        "latest_dataset_completeness": latest.get("artifact_completeness", {}),
        "completeness_warnings": completeness_warnings,
        "regression_warnings": regression_warnings,
        "current_gate_gaps": current_gate_gaps,
        "current_slippage_deficits": _current_slippage_deficits(slippage),
        "collection_health": c33.get("collection_health", {}),
        "progress_interpretation": _progress_interpretation(
            delta,
            current_gate_gaps,
            c33,
            regression_warnings,
            completeness_warnings,
        ),
        "authorization": {
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "config_write_attempted": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "next_allowed_stage": _next_allowed_stage(current_gate_gaps),
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_readiness_progress_tracker_md(payload: dict[str, Any]) -> str:
    latest = payload.get("latest_dataset", {})
    previous = payload.get("previous_dataset", {})
    delta = payload.get("delta_from_previous", {})
    gate_rows = [
        {
            "Gate": item.get("gate", ""),
            "Observed": item.get("observed", ""),
            "Required": item.get("required", ""),
            "Passed": str(item.get("passed", False)).lower(),
        }
        for item in payload.get("current_gate_gaps", [])
    ]
    slippage_rows = [
        {
            "Account": item.get("account_label", ""),
            "Status": item.get("slippage_status", ""),
            "Entry Deficit": item.get("entry_fills_deficit", 0),
            "SL Deficit": item.get("sl_exits_deficit", 0),
            "TP Deficit": item.get("tp_exits_deficit", 0),
            "Request Deficit": item.get("request_price_resolved_deficit", 0),
        }
        for item in payload.get("current_slippage_deficits", [])
    ]
    interpretation = "\n".join(f"- {item}" for item in payload.get("progress_interpretation", []))
    completeness_warnings = "\n".join(f"- {item}" for item in payload.get("completeness_warnings", []))
    warnings = "\n".join(f"- {item}" for item in payload.get("regression_warnings", []))
    return "\n".join(
        [
            "# A3 ML Readiness Progress Tracker",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            f"Dataset count: {payload.get('dataset_count', 0)}",
            "",
            "## Latest vs Previous",
            "",
            f"- Latest dataset: {latest.get('dataset_version', '')}",
            f"- Previous dataset: {previous.get('dataset_version', '') or 'none'}",
            f"- Snapshot cutoff delta minutes: {delta.get('snapshot_cutoff_delta_minutes', 0)}",
            f"- Signal instances delta: {delta.get('signal_instances', 0)}",
            f"- Market setup groups delta: {delta.get('market_setup_groups', 0)}",
            f"- Labels delta: {delta.get('labels', 0)}",
            f"- Mature labels delta: {delta.get('mature_labels', 0)}",
            f"- Positive labels delta: {delta.get('positive_labels', 0)}",
            f"- Negative labels delta: {delta.get('negative_labels', 0)}",
            f"- Fill rows delta: {delta.get('fill_rows', 0)}",
            "",
            "## Completeness Warnings",
            "",
            completeness_warnings or "- none",
            "",
            "## Regression Warnings",
            "",
            warnings or "- none",
            "",
            "## Current Gate Gaps",
            "",
            _table(gate_rows, ["Gate", "Observed", "Required", "Passed"]) if gate_rows else "No C03 gates.",
            "",
            "## Current Slippage Deficits",
            "",
            _table(slippage_rows, ["Account", "Status", "Entry Deficit", "SL Deficit", "TP Deficit", "Request Deficit"])
            if slippage_rows
            else "No slippage deficit rows.",
            "",
            "## Interpretation",
            "",
            interpretation or "- none",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Config write attempted: false.",
            "- Model training authorized: false.",
            "- Python demo predictions authorized: false.",
            "- EA consumption authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _dataset_dirs(c02_root: Path) -> list[Path]:
    if not c02_root.exists():
        return []
    return sorted(
        [path for path in c02_root.iterdir() if path.is_dir() and path.name.startswith("xauusd_c02_multiacct_")],
        key=lambda path: path.name,
    )


def _dataset_summary(path: Path) -> dict[str, Any]:
    manifest = _read_json(path / "ROOT_BAR_TICK_EXPORT_MANIFEST.json")
    normal = _read_json(path / "normalized" / "NORMALIZATION_MANIFEST.json")
    labels = _label_summary(path / "normalized" / "labels" / "diagnostic_tick_labels.csv")
    fill_rows = _fill_summary(path / "normalized" / "fills" / "fill_reconciliation.csv")
    market_groups = _csv_row_count(path / "normalized" / "signals" / "market_setup_groups.csv")
    artifact_completeness = _artifact_completeness(path)
    return {
        "dataset_version": path.name,
        "path": str(path),
        "created_at_utc": manifest.get("created_at_utc") or normal.get("created_at_utc", ""),
        "snapshot_cutoff_utc": manifest.get("snapshot_cutoff_utc", ""),
        "signal_instances": int(normal.get("signal_instances_csv", {}).get("row_count", 0) or 0),
        "market_setup_groups": market_groups,
        "labels": labels["labels"],
        "mature_labels": labels["mature_labels"],
        "positive_labels": labels["positive_labels"],
        "negative_labels": labels["negative_labels"],
        "unresolved_labels": labels["unresolved_labels"],
        "active_span_weeks": labels["active_span_weeks"],
        "decision_min_utc": labels["decision_min_utc"],
        "decision_max_utc": labels["decision_max_utc"],
        "fill_rows": fill_rows["rows"],
        "fill_rows_by_account": fill_rows["rows_by_account"],
        "latest_tick_max_utc": _latest_tick_max(manifest),
        "artifact_completeness": artifact_completeness,
    }


def _select_latest(datasets: list[dict[str, Any]], pointer_dataset: str) -> dict[str, Any]:
    if pointer_dataset:
        for item in datasets:
            if item.get("dataset_version") == pointer_dataset:
                return item
    return datasets[-1] if datasets else {}


def _previous_dataset(datasets: list[dict[str, Any]], latest_dataset: str) -> dict[str, Any]:
    if not latest_dataset:
        return {}
    names = [item.get("dataset_version", "") for item in datasets]
    if latest_dataset not in names:
        return {}
    index = names.index(latest_dataset)
    if index <= 0:
        return {}
    return datasets[index - 1]


def _delta(latest: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    if not latest or not previous:
        return {}
    return {
        "dataset_version_from": previous.get("dataset_version", ""),
        "dataset_version_to": latest.get("dataset_version", ""),
        "snapshot_cutoff_delta_minutes": _minutes_between(
            previous.get("snapshot_cutoff_utc", ""),
            latest.get("snapshot_cutoff_utc", ""),
        ),
        "signal_instances": int(latest.get("signal_instances", 0) or 0) - int(previous.get("signal_instances", 0) or 0),
        "market_setup_groups": int(latest.get("market_setup_groups", 0) or 0) - int(previous.get("market_setup_groups", 0) or 0),
        "labels": int(latest.get("labels", 0) or 0) - int(previous.get("labels", 0) or 0),
        "mature_labels": int(latest.get("mature_labels", 0) or 0) - int(previous.get("mature_labels", 0) or 0),
        "positive_labels": int(latest.get("positive_labels", 0) or 0) - int(previous.get("positive_labels", 0) or 0),
        "negative_labels": int(latest.get("negative_labels", 0) or 0) - int(previous.get("negative_labels", 0) or 0),
        "active_span_weeks": round(float(latest.get("active_span_weeks", 0) or 0) - float(previous.get("active_span_weeks", 0) or 0), 4),
        "fill_rows": int(latest.get("fill_rows", 0) or 0) - int(previous.get("fill_rows", 0) or 0),
        "fill_rows_by_account": _account_delta(
            latest.get("fill_rows_by_account", {}),
            previous.get("fill_rows_by_account", {}),
        ),
    }


def _label_summary(path: Path) -> dict[str, Any]:
    rows = _read_csv(path)
    status_counts = Counter(row.get("label_status", "") for row in rows)
    times = [_parse_time(row.get("decision_time_utc", "")) for row in rows]
    times = [item for item in times if item is not None]
    min_time = min(times) if times else None
    max_time = max(times) if times else None
    active_span_weeks = 0.0
    if min_time and max_time:
        active_span_weeks = max((max_time - min_time).total_seconds() / (7 * 24 * 3600), 0.0)
    return {
        "labels": len(rows),
        "mature_labels": sum(1 for row in rows if str(row.get("label_mature", "")).lower() == "true"),
        "positive_labels": int(status_counts.get("TP", 0)),
        "negative_labels": int(status_counts.get("SL", 0)),
        "unresolved_labels": len(rows) - int(status_counts.get("TP", 0)) - int(status_counts.get("SL", 0)),
        "decision_min_utc": _iso(min_time),
        "decision_max_utc": _iso(max_time),
        "active_span_weeks": round(active_span_weeks, 4),
    }


def _fill_summary(path: Path) -> dict[str, Any]:
    rows = _read_csv(path)
    counts = Counter(row.get("account_label", "") for row in rows)
    return {"rows": len(rows), "rows_by_account": dict(sorted(counts.items()))}


def _artifact_completeness(dataset_root: Path) -> dict[str, Any]:
    required = [
        ("root_manifest", dataset_root / "ROOT_BAR_TICK_EXPORT_MANIFEST.json", "json"),
        ("normalization_manifest", dataset_root / "normalized" / "NORMALIZATION_MANIFEST.json", "json"),
        ("signal_instances", dataset_root / "normalized" / "signals" / "signal_instances.csv", "csv"),
        ("market_setup_groups", dataset_root / "normalized" / "signals" / "market_setup_groups.csv", "csv"),
        ("diagnostic_labels", dataset_root / "normalized" / "labels" / "diagnostic_tick_labels.csv", "csv"),
        ("fill_reconciliation", dataset_root / "normalized" / "fills" / "fill_reconciliation.csv", "csv"),
    ]
    artifacts = []
    for name, path, kind in required:
        exists = path.exists()
        row_count = _csv_row_count(path) if kind == "csv" and exists else None
        artifacts.append(
            {
                "name": name,
                "path": str(path),
                "exists": exists,
                "row_count": row_count,
            }
        )
    missing = [item["name"] for item in artifacts if not item["exists"]]
    return {
        "complete": not missing,
        "missing_artifacts": missing,
        "artifacts": artifacts,
    }


def _current_gate_gaps(c03: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "gate": item.get("gate", ""),
            "passed": bool(item.get("passed", False)),
            "observed": str(item.get("observed", "")),
            "required": str(item.get("required", "")),
        }
        for item in c03.get("checks", [])
    ]


def _current_slippage_deficits(slippage: dict[str, Any]) -> list[dict[str, Any]]:
    requirements = slippage.get("requirements", {})
    rows = []
    for account in slippage.get("accounts", []):
        row = dict(account)
        for key in ("entry_fills", "sl_exits", "tp_exits", "request_price_resolved"):
            row[f"{key}_deficit"] = max(int(requirements.get(key, 0) or 0) - int(account.get(key, 0) or 0), 0)
        rows.append(row)
    return rows


def _regression_warnings(delta: dict[str, Any]) -> list[str]:
    labels = {
        "signal_instances": "Signal instances",
        "market_setup_groups": "Market setup groups",
        "labels": "Labels",
        "mature_labels": "Mature labels",
        "fill_rows": "Fill rows",
    }
    warnings = []
    for key, label in labels.items():
        value = int(delta.get(key, 0) or 0)
        if value < 0:
            warnings.append(f"{label} decreased by {abs(value)} versus the previous dataset; review export completeness before trusting this dataset for readiness movement.")
    return warnings


def _completeness_warnings(latest: dict[str, Any]) -> list[str]:
    completeness = latest.get("artifact_completeness", {})
    missing = completeness.get("missing_artifacts", [])
    if not latest:
        return ["Latest dataset was not found; progress cannot be trusted until C02 is rebuilt."]
    if not missing:
        return []
    return [
        "Latest dataset is missing required artifacts: "
        + ", ".join(str(item) for item in missing)
        + "; rerun C07 offline repair or C43 refresh before trusting readiness movement."
    ]


def _progress_interpretation(
    delta: dict[str, Any],
    gates: list[dict[str, Any]],
    c33: dict[str, Any],
    regression_warnings: list[str],
    completeness_warnings: list[str],
) -> list[str]:
    notes = []
    if completeness_warnings:
        notes.append("The latest dataset is incomplete; complete C02/C07 artifacts before reviewing readiness progress.")
    if regression_warnings:
        notes.append("The latest dataset has negative evidence deltas; treat readiness movement as suspect until the export inputs are reviewed.")
    if not delta:
        notes.append("Only one dataset is available or the current dataset was not found; trend is unavailable.")
    elif any(int(delta.get(key, 0) or 0) > 0 for key in ("signal_instances", "labels", "mature_labels", "fill_rows")):
        notes.append("Recent collection is adding evidence, but training gates still require C03 to pass.")
    else:
        notes.append("The latest dataset did not add signal, label, or fill evidence versus the previous dataset.")
    if int(delta.get("market_setup_groups", 0) or 0) <= 0 and any(g.get("gate") == "market_setup_groups" and not g.get("passed") for g in gates):
        notes.append("Market setup groups are still stuck below 300; more qualifying current-scope setups or approved contract expansion are needed.")
    if any(g.get("gate") == "active_weeks" and not g.get("passed") for g in gates):
        notes.append("Active weeks cannot be fixed by repeated refreshes alone; it needs more calendar market time or approved older compatible decisions.")
    if any(g.get("gate") == "feature_budget" and not g.get("passed") for g in gates):
        notes.append("Feature budget remains blocked until reviewed label promotion creates trainable groups.")
    if not c33.get("collection_health", {}).get("all_accounts_collecting", False):
        notes.append("Collection health is not all-account green; fix C33 before relying on progress rates.")
    return notes


def _status(
    datasets: list[dict[str, Any]],
    latest: dict[str, Any],
    delta: dict[str, Any],
    regression_warnings: list[str],
) -> str:
    if not datasets:
        return STATUS_WAITING
    if latest and not latest.get("artifact_completeness", {}).get("complete", False):
        return STATUS_INCOMPLETE
    if len(datasets) < 2:
        return STATUS_WAITING
    if regression_warnings:
        return STATUS_REGRESSION
    if delta and any(int(delta.get(key, 0) or 0) > 0 for key in ("signal_instances", "labels", "mature_labels", "fill_rows")):
        return STATUS_READY
    return STATUS_NO_DELTA


def _next_allowed_stage(gates: list[dict[str, Any]]) -> str:
    failed = [item.get("gate", "") for item in gates if not item.get("passed", False)]
    if not failed:
        return "C03 gates appear to pass; rerun C43 and continue through C05/C04/C06/C10/C23."
    return "Keep collecting A1/A2/A3 data, send C45 to reviewer, and rerun C43/C46 after reviewer decision or new market data."


def _latest_tick_max(manifest: dict[str, Any]) -> str:
    times = []
    for account in manifest.get("account_records", []):
        for chunk in account.get("coverage", {}).get("ticks", {}).get("chunks", []):
            parsed = _parse_time(chunk.get("max_time_utc", ""))
            if parsed is not None:
                times.append(parsed)
    return _iso(max(times) if times else None)


def _csv_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _account_delta(latest: dict[str, int], previous: dict[str, int]) -> dict[str, int]:
    accounts = sorted(set(latest) | set(previous))
    return {account: int(latest.get(account, 0) or 0) - int(previous.get(account, 0) or 0) for account in accounts}


def _minutes_between(start: str, end: str) -> float:
    start_time = _parse_time(start)
    end_time = _parse_time(end)
    if start_time is None or end_time is None:
        return 0.0
    return round((end_time - start_time).total_seconds() / 60.0, 2)


def _parse_time(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_readiness_progress_tracker_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c46_readiness_progress_tracker_report"] = payload["outputs"]["status_report_json"]
    pointer["c46_readiness_progress_tracker_status"] = payload["status"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
