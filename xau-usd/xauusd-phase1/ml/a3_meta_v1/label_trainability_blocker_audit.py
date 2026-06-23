from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_LABEL_TRAINABILITY_BLOCKER_STATUS.json"
STATUS_REVIEW_REQUIRED = "LABEL_PROMOTION_REVIEW_REQUIRED_SLIPPAGE_BLOCKED"
STATUS_WAITING_FOR_LABELS = "WAITING_FOR_MATURE_LABELS"
STATUS_PARTIALLY_ACTIVE = "TRAINABILITY_PARTIALLY_ACTIVE_REVIEW_REQUIRED"


def generate_label_trainability_blocker_audit(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    label_audit = _read_json(reports / "C02_LABEL_AUDIT.json")
    c01 = _read_json(reports / "C02_C01_DATA_AUDIT.json")
    slippage = _read_json(reports / "C02_SLIPPAGE_READINESS.json")
    labeled_decisions = _csv_counts(reports / "C02_LABELED_DECISIONS.csv")
    c01_snapshot = _csv_counts(reports / "A3_ML_C01_SNAPSHOT_ROWS.csv")
    slippage_deficits = _slippage_deficits(slippage)
    status = _status(label_audit, c01, c01_snapshot, slippage)
    payload = {
        "status": status,
        "stage": "C38-LABEL-TRAINABILITY-BLOCKER-AUDIT",
        "created_at_utc": _utc_now(),
        "schema_version": "a3_ml_label_trainability_blocker_status_v1",
        "dataset_version": label_audit.get("dataset_version") or c01.get("dataset_version", ""),
        "summary": {
            "c02_label_status": label_audit.get("status", "MISSING"),
            "c02_diagnostic_labels_only": bool(label_audit.get("boundary", {}).get("diagnostic_labels_only", False)),
            "c02_labels": label_audit.get("counts", {}).get("labels", 0),
            "c02_mature_labels": label_audit.get("counts", {}).get("mature", 0),
            "c02_positive_labels": label_audit.get("counts", {}).get("positive", 0),
            "c02_negative_labels": label_audit.get("counts", {}).get("negative", 0),
            "c02_labeled_decision_rows": labeled_decisions["rows"],
            "c01_snapshot_rows": c01_snapshot["rows"],
            "c01_candidate_trainable_rows": c01_snapshot["candidate_trainable_true"],
            "c01_candidate_trainable_groups": c01.get("labeled_and_trainable_setup_groups", {}).get(
                "candidate_trainable_groups", 0
            ),
            "c01_label_status_counts": c01_snapshot["label_status_counts"],
            "c01_global_feature_budget": c01.get("global_feature_budget", 0),
            "slippage_status": slippage.get("status", "MISSING"),
        },
        "label_status_counts": {
            "c02_labeled_decisions": labeled_decisions["label_status_counts"],
            "c01_snapshot": c01_snapshot["label_status_counts"],
        },
        "slippage_deficits": slippage_deficits,
        "blockers": _blockers(label_audit, c01, c01_snapshot, slippage, slippage_deficits),
        "required_changes_before_trainable_labels": _required_changes(slippage_deficits),
        "authorization": {
            "label_promotion_authorized": False,
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "model_training_authorized": False,
            "label_promotion_authorized": False,
            "python_demo_predictions_authorized": False,
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_label_trainability_blocker_audit_md(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    deficit_rows = [
        {
            "Account": row.get("account_label", ""),
            "Status": row.get("slippage_status", ""),
            "Entry Deficit": str(row.get("entry_fills_deficit", 0)),
            "SL Deficit": str(row.get("sl_exits_deficit", 0)),
            "TP Deficit": str(row.get("tp_exits_deficit", 0)),
            "Request Deficit": str(row.get("request_price_resolved_deficit", 0)),
        }
        for row in payload.get("slippage_deficits", [])
    ]
    blockers = "\n".join(f"- {item}" for item in payload.get("blockers", []))
    changes = "\n".join(f"- {item}" for item in payload.get("required_changes_before_trainable_labels", []))
    return "\n".join(
        [
            "# A3 ML Label Trainability Blocker Audit",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Summary",
            "",
            f"- C02 mature labels: {summary.get('c02_mature_labels', 0)}.",
            f"- C02 positive/negative: {summary.get('c02_positive_labels', 0)} / {summary.get('c02_negative_labels', 0)}.",
            f"- C01 snapshot rows: {summary.get('c01_snapshot_rows', 0)}.",
            f"- C01 candidate-trainable rows: {summary.get('c01_candidate_trainable_rows', 0)}.",
            f"- C01 candidate-trainable groups: {summary.get('c01_candidate_trainable_groups', 0)}.",
            f"- C01 feature budget: {summary.get('c01_global_feature_budget', 0)}.",
            f"- Slippage status: {summary.get('slippage_status', '')}.",
            "",
            "## Slippage Deficits",
            "",
            _table(deficit_rows, ["Account", "Status", "Entry Deficit", "SL Deficit", "TP Deficit", "Request Deficit"])
            if deficit_rows
            else "No slippage rows.",
            "",
            "## Blockers",
            "",
            blockers or "- none",
            "",
            "## Required Changes",
            "",
            changes or "- none",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Model training authorized: false.",
            "- Label promotion authorized: false.",
            "- Python demo predictions authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _status(
    label_audit: dict[str, Any],
    c01: dict[str, Any],
    c01_snapshot: dict[str, Any],
    slippage: dict[str, Any],
) -> str:
    if int(label_audit.get("counts", {}).get("mature", 0) or 0) <= 0:
        return STATUS_WAITING_FOR_LABELS
    if c01_snapshot["candidate_trainable_true"] > 0 or int(
        c01.get("labeled_and_trainable_setup_groups", {}).get("candidate_trainable_groups", 0) or 0
    ) > 0:
        return STATUS_PARTIALLY_ACTIVE
    if slippage.get("status") != "ADEQUATE":
        return STATUS_REVIEW_REQUIRED
    return "LABEL_PROMOTION_REVIEW_REQUIRED"


def _blockers(
    label_audit: dict[str, Any],
    c01: dict[str, Any],
    c01_snapshot: dict[str, Any],
    slippage: dict[str, Any],
    slippage_deficits: list[dict[str, Any]],
) -> list[str]:
    blockers = []
    if label_audit.get("boundary", {}).get("diagnostic_labels_only", False):
        blockers.append("C02 labels are explicitly diagnostic-only.")
    if c01_snapshot["candidate_trainable_true"] == 0:
        blockers.append("C01 snapshot has zero candidate_trainable=true rows.")
    if int(c01.get("global_feature_budget", 0) or 0) == 0:
        blockers.append("C01 global_feature_budget is 0 because trainable groups are 0.")
    if slippage.get("status") != "ADEQUATE":
        bad_accounts = [row["account_label"] for row in slippage_deficits if row["slippage_status"] != "ADEQUATE"]
        blockers.append("Slippage readiness is not ADEQUATE" + (f" for {', '.join(bad_accounts)}." if bad_accounts else "."))
    return blockers


def _required_changes(slippage_deficits: list[dict[str, Any]]) -> list[str]:
    actions = [
        "Reviewer must approve a label-promotion rule before C01 may treat diagnostic tick labels as trainable.",
        "C01 must consume C02 label_status/y_net_R fields only under that reviewed promotion rule.",
        "C03 must rerun after label promotion and still keep python_demo_predictions_authorized=false until all gates pass.",
    ]
    for row in slippage_deficits:
        if row["slippage_status"] != "ADEQUATE":
            actions.append(
                f"{row['account_label']} needs entry={row['entry_fills_deficit']}, "
                f"SL={row['sl_exits_deficit']}, TP={row['tp_exits_deficit']}, "
                f"request-price={row['request_price_resolved_deficit']} more slippage-ready records."
            )
    actions.append("Keep broker_action_authorized=false.")
    return actions


def _slippage_deficits(slippage: dict[str, Any]) -> list[dict[str, Any]]:
    requirements = slippage.get("requirements", {})
    rows = []
    for account in slippage.get("accounts", []):
        row = dict(account)
        for key in ("entry_fills", "sl_exits", "tp_exits", "request_price_resolved"):
            row[f"{key}_deficit"] = max(int(requirements.get(key, 0) or 0) - int(account.get(key, 0) or 0), 0)
        rows.append(row)
    return rows


def _csv_counts(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"rows": 0, "candidate_trainable_true": 0, "label_status_counts": {}}
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    label_counts = Counter(str(row.get("label_status", "")) for row in rows)
    return {
        "rows": len(rows),
        "candidate_trainable_true": sum(
            1 for row in rows if str(row.get("candidate_trainable", "")).strip().lower() == "true"
        ),
        "label_status_counts": dict(sorted(label_counts.items())),
    }


def _next_allowed_stage(status: str) -> str:
    if status == STATUS_WAITING_FOR_LABELS:
        return "Continue collecting until diagnostic labels mature, then rerun C38."
    return "Ask reviewer for a label-promotion decision; continue slippage collection for weak accounts; keep demo Python unauthorized."


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_label_trainability_blocker_audit_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c38_label_trainability_blocker_report"] = payload["outputs"]["status_report_json"]
    pointer["c38_label_trainability_blocker_status"] = payload["status"]
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
