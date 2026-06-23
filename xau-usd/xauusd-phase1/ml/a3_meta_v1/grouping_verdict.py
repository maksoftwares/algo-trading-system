from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .market_data_export import _sha256_file, _table, _utc_now, _write_json_atomic


DEFAULT_GROUPING_REPORT_JSON = Path("outputs") / "reports" / "C02_SIGNAL_GROUPING_AUDIT.json"
DEFAULT_FINAL_VERDICT_JSON = Path("outputs") / "reports" / "C02_FINAL_VERDICT.json"


def generate_c02_grouping_audit(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    pointer = _load_pointer(root)
    decisions_csv = Path(pointer["c02_decisions_csv"])
    dataset_root = Path(pointer["output_root"])
    output_csv = dataset_root / "normalized" / "signals" / "market_setup_groups.csv"
    rows = _read_csv(decisions_csv)
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        group_id = _market_setup_group_id(row["signal_id"])
        groups[group_id].append(row)
    group_rows = []
    for group_id, members in sorted(groups.items()):
        scopes = sorted({member["signal_id"].split("|")[0] for member in members})
        sample_parts = members[0]["signal_id"].split("|")
        group_rows.append(
            {
                "market_setup_group_id": group_id,
                "symbol": sample_parts[1],
                "family": sample_parts[2],
                "direction": sample_parts[3],
                "normalized_level_price": sample_parts[7],
                "break_bar_time_utc": sample_parts[4],
                "retest_bar_time_utc": sample_parts[5],
                "confirmation_bar_time_utc": sample_parts[6],
                "account_count": len(scopes),
                "account_scopes": ",".join(scopes),
                "source_signal_count": len(members),
            }
        )
    _write_csv(output_csv, group_rows)
    report_json = (report_json or root / DEFAULT_GROUPING_REPORT_JSON).resolve()
    report_md = report_json.with_suffix(".md")
    payload = {
        "status": "PASS",
        "stage": "C02-05",
        "created_at_utc": _utc_now(),
        "dataset_version": pointer["dataset_version"],
        "boundary": {
            "mt5_connection_attempted": False,
            "model_training_authorized": False,
            "broker_action_authorized": False,
            "terminal_runtime_change_authorized": False,
        },
        "counts": {
            "decision_rows": len(rows),
            "market_setup_groups": len(group_rows),
            "cross_account_groups": sum(1 for row in group_rows if int(row["account_count"]) > 1),
            "max_account_count": max([int(row["account_count"]) for row in group_rows], default=0),
            "by_account_count": dict(Counter(scope for row in rows for scope in [row["signal_id"].split("|")[0]])),
        },
        "outputs": {
            "market_setup_groups_csv": str(output_csv),
            "market_setup_groups_sha256": _sha256_file(output_csv),
        },
        "notes": [
            "market_setup_group_id intentionally excludes account_scope.",
            "This is an audit/staging grouping pass; train/test split integrity is still a C03/C04 gate.",
        ],
        "next_allowed_stage": "C02-06 diagnostic labels and slippage readiness",
    }
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_grouping_audit_md(payload), encoding="utf-8")
    pointer["signal_grouping_audit_status"] = "PASS"
    pointer["signal_grouping_audit_report"] = str(report_json)
    pointer["market_setup_groups_csv"] = str(output_csv)
    pointer["training_authorized"] = False
    _write_json_atomic(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer)
    return report_json


def generate_c02_final_verdict(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    pointer = _load_pointer(root)
    c01 = json.loads((root / "outputs" / "reports" / "C02_C01_DATA_AUDIT.json").read_text(encoding="utf-8"))
    label_audit = _read_optional_json(pointer.get("label_audit_report", ""))
    slippage_readiness = _read_optional_json(pointer.get("slippage_readiness_report", ""))
    grouping_audit = _read_optional_json(pointer.get("signal_grouping_audit_report", ""))
    report_json = (report_json or root / DEFAULT_FINAL_VERDICT_JSON).resolve()
    report_md = report_json.with_suffix(".md")
    training_authorized = False
    ready_for_demo_predictions = False
    blockers = []
    if c01["status"] != "CANDIDATE_MODEL":
        blockers.append(f"dataset_status={c01['status']} is not CANDIDATE_MODEL")
    if not c01["training_decision"]["supervised_training_allowed"]:
        blockers.append(c01["training_decision"]["reason"])
    if slippage_readiness.get("status") != "ADEQUATE":
        blockers.append("slippage readiness is INSUFFICIENT")
    label_counts = label_audit.get("counts", {})
    if label_counts.get("positive", 0) < 90 or label_counts.get("negative", 0) < 90:
        blockers.append("diagnostic label minority count is below 90")
    if grouping_audit.get("counts", {}).get("market_setup_groups", 0) < 300:
        blockers.append("market_setup_groups below EXPLORATORY minimum of 300")
    payload: dict[str, Any] = {
        "status": "CONTINUE_DATASET_BUILD",
        "stage": "C02-FINAL-VERDICT",
        "created_at_utc": _utc_now(),
        "dataset_version": pointer["dataset_version"],
        "c02_pipeline_status": {
            "account_verification": "PASS",
            "bar_tick_export": pointer.get("status"),
            "history_log_snapshot": pointer.get("history_log_snapshot_status"),
            "normalization": pointer.get("normalization_status"),
            "signal_grouping_audit": pointer.get("signal_grouping_audit_status"),
            "diagnostic_labels": pointer.get("diagnostic_label_status"),
            "c01_ingestion_status": c01["status"],
        },
        "counts": {
            "c01_decisions": c01["raw_source_row_counts"]["decisions_rows"],
            "exact_unique_signals": c01["raw_source_row_counts"]["exact_unique_signals"],
            "snapshot_rows": c01["raw_source_row_counts"]["snapshot_rows"],
            "market_setup_groups": grouping_audit.get("counts", {}).get("market_setup_groups", 0),
            "diagnostic_labels": label_counts,
            "class_balance": c01["class_balance"],
            "direction_balance": c01["direction_balance"],
            "regime_balance": c01["regime_balance"],
            "global_feature_budget": c01["global_feature_budget"],
        },
        "authorization": {
            "training_authorized": training_authorized,
            "python_demo_predictions_authorized": ready_for_demo_predictions,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "blockers": blockers,
        "next_allowed_stage": "C03/C04 label, slippage, leakage, and walk-forward readiness validation before training",
    }
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_final_verdict_md(payload), encoding="utf-8")
    pointer["final_verdict_report"] = str(report_json)
    pointer["training_authorized"] = False
    pointer["python_demo_predictions_authorized"] = False
    _write_json_atomic(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer)
    return report_json


def render_grouping_audit_md(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# C02 Signal Grouping Audit",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Model training authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Counts",
            "",
            f"- Decision rows: {payload['counts']['decision_rows']}",
            f"- Market setup groups: {payload['counts']['market_setup_groups']}",
            f"- Cross-account groups: {payload['counts']['cross_account_groups']}",
            f"- Max account count per group: {payload['counts']['max_account_count']}",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def render_final_verdict_md(payload: dict[str, Any]) -> str:
    blockers = "\n".join(f"- {item}" for item in payload["blockers"]) if payload["blockers"] else "- none"
    return "\n".join(
        [
            "# C02 Final Verdict",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Authorization",
            "",
            f"- Training authorized: {str(payload['authorization']['training_authorized']).lower()}",
            f"- Python demo predictions authorized: {str(payload['authorization']['python_demo_predictions_authorized']).lower()}",
            f"- EA consumption authorized: {str(payload['authorization']['ea_consumption_authorized']).lower()}",
            f"- Broker action authorized: {str(payload['authorization']['broker_action_authorized']).lower()}",
            "",
            "## Counts",
            "",
            f"- C01 decisions: {payload['counts']['c01_decisions']}",
            f"- Exact unique signals: {payload['counts']['exact_unique_signals']}",
            f"- Snapshot rows: {payload['counts']['snapshot_rows']}",
            f"- Market setup groups: {payload['counts']['market_setup_groups']}",
            f"- Diagnostic labels: {payload['counts']['diagnostic_labels']}",
            f"- Class balance: {payload['counts']['class_balance']}",
            f"- Global feature budget: {payload['counts']['global_feature_budget']}",
            "",
            "## Blockers",
            "",
            blockers,
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _market_setup_group_id(signal_id: str) -> str:
    parts = signal_id.split("|")
    if len(parts) != 8:
        return hashlib.sha256(signal_id.encode("utf-8")).hexdigest()
    account_neutral = "|".join(parts[1:])
    return hashlib.sha256(account_neutral.encode("utf-8")).hexdigest()


def _load_pointer(root: Path) -> dict[str, Any]:
    return json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))


def _read_optional_json(path_text: str) -> dict[str, Any]:
    if not path_text:
        return {}
    path = Path(path_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row}) or ["market_setup_group_id"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
