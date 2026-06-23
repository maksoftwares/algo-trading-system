from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .market_data_export import _sha256_file, _table, _utc_now, _write_json_atomic


DEFAULT_CONTRACT = Path("config") / "ml" / "a3_ml_training_contract.json"
DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_EXPLORATORY_TRAINING_REHEARSAL_STATUS.json"
DEFAULT_ARTIFACT_JSON = Path("outputs") / "reports" / "A3_ML_EXPLORATORY_MODEL_REHEARSAL_ARTIFACT.json"
DEFAULT_PREVIEW_CSV = Path("outputs") / "reports" / "A3_ML_EXPLORATORY_SHADOW_PREVIEW.csv"
SCHEMA_VERSION = "a3_ml_exploratory_training_rehearsal_status_v1"
ARTIFACT_SCHEMA_VERSION = "a3_ml_exploratory_model_rehearsal_artifact_v1"
PREVIEW_SCHEMA_VERSION = "a3_ml_exploratory_shadow_preview_v1"


def run_exploratory_training_rehearsal(root: Path, contract_path: Path | None = None) -> Path:
    root = root.resolve()
    contract_path = (contract_path or root / DEFAULT_CONTRACT).resolve()
    reports = root / "outputs" / "reports"
    contract = _read_json(contract_path)
    pointer_path = reports / "C02_DATASET_POINTER.json"
    pointer = _read_json(pointer_path)
    readiness_path = _resolve_report(
        root,
        contract.get("readiness_report_json"),
        "outputs/reports/C03_TRAINING_READINESS_REPORT.json",
        "outputs/reports/A3_ML_TRAINING_READINESS_REPORT.json",
    )
    data_audit_path = _resolve_report(
        root,
        contract.get("data_audit_json"),
        "outputs/reports/C02_C01_DATA_AUDIT.json",
        "outputs/reports/A3_ML_C01_DATA_AUDIT.json",
    )
    snapshot_path = _resolve_report(
        root,
        contract.get("snapshot_csv"),
        "outputs/reports/A3_ML_C01_SNAPSHOT_ROWS.csv",
    )
    status_json = root / DEFAULT_STATUS_JSON
    artifact_json = root / DEFAULT_ARTIFACT_JSON
    preview_csv = root / DEFAULT_PREVIEW_CSV

    readiness = _read_json(readiness_path)
    data_audit = _read_json(data_audit_path)
    rows = _read_csv(snapshot_path)
    diagnostic_rows = _diagnostic_label_rows(rows)
    candidate_rows = _candidate_training_rows(rows)
    refusal_reasons = _refusal_reasons(snapshot_path, diagnostic_rows)

    artifact_sha256 = ""
    preview_row_count = 0
    if refusal_reasons:
        status = "REHEARSAL_REFUSED_NO_DIAGNOSTIC_ROWS"
    else:
        status = "REHEARSED_RESEARCH_ONLY"
        artifact = _build_artifact(
            contract=contract,
            readiness=readiness,
            data_audit=data_audit,
            pointer=pointer,
            rows=diagnostic_rows,
            candidate_rows=candidate_rows,
        )
        artifact_json.parent.mkdir(parents=True, exist_ok=True)
        artifact_json.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
        artifact_sha256 = _sha256_file(artifact_json)
        preview_row_count = _write_preview_csv(preview_csv, artifact, rows)

    payload = _status_payload(
        status=status,
        contract_path=contract_path,
        readiness_path=readiness_path,
        data_audit_path=data_audit_path,
        snapshot_path=snapshot_path,
        status_json=status_json,
        artifact_json=artifact_json,
        artifact_sha256=artifact_sha256,
        preview_csv=preview_csv,
        preview_row_count=preview_row_count,
        readiness=readiness,
        data_audit=data_audit,
        pointer=pointer,
        snapshot_rows=len(rows),
        diagnostic_rows=diagnostic_rows,
        candidate_rows=candidate_rows,
        refusal_reasons=refusal_reasons,
    )
    _write_status(status_json, payload)
    _update_pointer(pointer_path, pointer, payload)
    return status_json


def render_exploratory_training_rehearsal_md(payload: dict[str, Any]) -> str:
    reasons = payload.get("refusal_reasons", [])
    reason_lines = "\n".join(f"- {reason}" for reason in reasons) if reasons else "- none"
    blockers = payload.get("official_gate_blockers", [])
    blocker_lines = "\n".join(f"- {item}" for item in blockers) if blockers else "- none"
    counts = payload.get("training_population", {})
    count_rows = [
        {"Metric": "snapshot_rows", "Value": str(counts.get("snapshot_rows", 0))},
        {"Metric": "diagnostic_labeled_rows", "Value": str(counts.get("diagnostic_labeled_rows", 0))},
        {"Metric": "official_candidate_trainable_rows", "Value": str(counts.get("official_candidate_trainable_rows", 0))},
        {"Metric": "positive", "Value": str(counts.get("positive", 0))},
        {"Metric": "negative", "Value": str(counts.get("negative", 0))},
        {"Metric": "minority", "Value": str(counts.get("minority", 0))},
    ]
    return "\n".join(
        [
            "# A3 ML Exploratory Training Rehearsal Status",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Meaning",
            "",
            "This is a quarantined research rehearsal only. It does not create the official C05 model artifact and it does not authorize Python demo predictions, EA consumption, or broker action.",
            "",
            "## Population",
            "",
            _table(count_rows, ["Metric", "Value"]),
            "",
            "## Inputs",
            "",
            f"- Readiness report: {payload['inputs']['readiness_report']}",
            f"- Data audit: {payload['inputs']['data_audit']}",
            f"- Snapshot CSV: {payload['inputs']['snapshot_csv']}",
            "",
            "## Outputs",
            "",
            f"- Rehearsal artifact: {payload['outputs']['rehearsal_artifact_json']}",
            f"- Artifact SHA256: {payload['outputs']['rehearsal_artifact_sha256']}",
            f"- Shadow preview CSV: {payload['outputs']['shadow_preview_csv']}",
            f"- Shadow preview rows: {payload['outputs']['shadow_preview_rows']}",
            "",
            "## Official Gate Blockers",
            "",
            blocker_lines,
            "",
            "## Refusal Reasons",
            "",
            reason_lines,
            "",
            "## Authorization",
            "",
            "- Official model training authorized: false.",
            "- Python demo predictions authorized: false.",
            "- EA consumption authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Terminal runtime change authorized: false.",
            "- EA file drop authorized: false.",
            "- Official model artifact written: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _status_payload(
    *,
    status: str,
    contract_path: Path,
    readiness_path: Path,
    data_audit_path: Path,
    snapshot_path: Path,
    status_json: Path,
    artifact_json: Path,
    artifact_sha256: str,
    preview_csv: Path,
    preview_row_count: int,
    readiness: dict[str, Any],
    data_audit: dict[str, Any],
    pointer: dict[str, Any],
    snapshot_rows: int,
    diagnostic_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, str]],
    refusal_reasons: list[str],
) -> dict[str, Any]:
    labels = Counter(row.get("y_win_expected", "") for row in diagnostic_rows)
    official_blockers = _official_gate_blockers(readiness, data_audit)
    positive = labels.get("1", 0)
    negative = labels.get("0", 0)
    return {
        "status": status,
        "stage": "C18-EXPLORATORY-TRAINING-REHEARSAL",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", readiness.get("dataset_version", data_audit.get("dataset_version", ""))),
        "readiness_status": readiness.get("status", "UNKNOWN"),
        "c01_status": data_audit.get("status", "UNKNOWN"),
        "training_population": {
            "snapshot_rows": snapshot_rows,
            "diagnostic_labeled_rows": len(diagnostic_rows),
            "official_candidate_trainable_rows": len(candidate_rows),
            "positive": positive,
            "negative": negative,
            "minority": min(positive, negative),
        },
        "authorization": {
            "exploratory_rehearsal_executed": status == "REHEARSED_RESEARCH_ONLY",
            "official_model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "quarantine": {
            "official_model_artifact": False,
            "eligible_for_c04_shadow_bridge": False,
            "eligible_for_c06_ea_handoff": False,
            "prediction_rows_force_abstain": True,
            "reason": "C18 uses diagnostic labels only to rehearse Python training/scoring while C03/C05 remain closed.",
        },
        "inputs": {
            "contract": str(contract_path),
            "readiness_report": str(readiness_path),
            "data_audit": str(data_audit_path),
            "snapshot_csv": str(snapshot_path),
        },
        "outputs": {
            "status_report_json": str(status_json),
            "status_report_md": str(status_json.with_suffix(".md")),
            "rehearsal_artifact_json": str(artifact_json) if status == "REHEARSED_RESEARCH_ONLY" else "",
            "rehearsal_artifact_sha256": artifact_sha256,
            "shadow_preview_csv": str(preview_csv) if status == "REHEARSED_RESEARCH_ONLY" else "",
            "shadow_preview_rows": preview_row_count,
        },
        "official_gate_blockers": official_blockers,
        "refusal_reasons": refusal_reasons,
        "boundary": {
            "mt5_connection_attempted": False,
            "terminal_runtime_change_authorized": False,
            "ea_file_drop_authorized": False,
            "official_model_artifact_written": False,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": (
            "Use this only to verify Python training/scoring mechanics. Continue A1/A2/A3 data collection, rerun C03, then let C05 create the official model only after readiness passes."
            if status == "REHEARSED_RESEARCH_ONLY"
            else "Collect labeled diagnostic rows, rerun the C02/C03 pipeline, then rerun C18."
        ),
    }


def _build_artifact(
    *,
    contract: dict[str, Any],
    readiness: dict[str, Any],
    data_audit: dict[str, Any],
    pointer: dict[str, Any],
    rows: list[dict[str, str]],
    candidate_rows: list[dict[str, str]],
) -> dict[str, Any]:
    labels = [int(row["y_win_expected"]) for row in rows]
    positive = sum(labels)
    feature_schema_hash = _sha256_text(json.dumps(data_audit.get("feature_availability", []), separators=(",", ":"), sort_keys=True))
    dataset_version = pointer.get("dataset_version", readiness.get("dataset_version", "UNKNOWN_DATASET"))
    model_id = f"a3_m0_exploratory_rehearsal_{dataset_version}_{feature_schema_hash[:8]}"
    return {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "status": "REHEARSED_RESEARCH_ONLY",
        "created_at_utc": _utc_now(),
        "model_id": model_id,
        "model_family": "M0_DIAGNOSTIC_BASE_RATE_REHEARSAL",
        "official_model_artifact": False,
        "eligible_for_c04_shadow_bridge": False,
        "eligible_for_c06_ea_handoff": False,
        "dataset_version": dataset_version,
        "feature_schema_hash": feature_schema_hash,
        "official_selected_features": list(data_audit.get("selected_features", [])),
        "contract_model_family": contract.get("model_family", ""),
        "training_summary": {
            "snapshot_rows": int(data_audit.get("raw_source_row_counts", {}).get("snapshot_rows", len(rows))),
            "diagnostic_labeled_rows": len(rows),
            "official_candidate_trainable_rows": len(candidate_rows),
            "positive": positive,
            "negative": len(rows) - positive,
            "minority": min(positive, len(rows) - positive),
            "global_positive_rate": round(_smooth_rate(positive, len(rows)), 10),
            "in_sample_preview_only": True,
        },
        "rates": {
            "global": round(_smooth_rate(positive, len(rows)), 10),
            "by_account": _rates(rows, ["account_scope"]),
            "by_direction": _rates(rows, ["direction"]),
            "by_account_direction": _rates(rows, ["account_scope", "direction"]),
            "by_regime": _rates(rows, ["regime"]),
            "by_session": _rates(rows, ["session_bucket"]),
        },
        "official_gate_snapshot": {
            "readiness_status": readiness.get("status", "UNKNOWN"),
            "c01_status": data_audit.get("status", "UNKNOWN"),
            "official_gate_blockers": _official_gate_blockers(readiness, data_audit),
        },
        "action_policy": {
            "preview_action": "ABSTAIN",
            "reason": "EXPLORATORY_REHEARSAL_NOT_AUTHORIZED_FOR_DEMO",
            "broker_action_authorized": False,
        },
        "authorization": {
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "shadow_only": True,
            "research_only": True,
            "mt5_connection_attempted": False,
            "terminal_runtime_change_authorized": False,
            "official_model_artifact_written": False,
            "broker_action_authorized": False,
        },
    }


def _write_preview_csv(preview_csv: Path, artifact: dict[str, Any], rows: list[dict[str, str]]) -> int:
    fields = [
        "schema_version",
        "model_id",
        "dataset_version",
        "account_scope",
        "account_label",
        "symbol",
        "source_signal_id",
        "setup_group_id",
        "decision_time_utc",
        "direction",
        "regime",
        "session_bucket",
        "p_win_rehearsal",
        "model_group",
        "preview_action",
        "authorization_status",
        "reason",
        "broker_action_authorized",
    ]
    preview_csv.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    rates = artifact.get("rates", {})
    with preview_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            p_win, model_group = _score_row(row, rates)
            writer.writerow(
                {
                    "schema_version": PREVIEW_SCHEMA_VERSION,
                    "model_id": artifact.get("model_id", ""),
                    "dataset_version": artifact.get("dataset_version", ""),
                    "account_scope": row.get("account_scope", ""),
                    "account_label": row.get("account_label", ""),
                    "symbol": row.get("symbol", ""),
                    "source_signal_id": row.get("source_signal_id", ""),
                    "setup_group_id": row.get("setup_group_id", ""),
                    "decision_time_utc": row.get("decision_time_utc", ""),
                    "direction": row.get("direction", ""),
                    "regime": row.get("regime", ""),
                    "session_bucket": row.get("session_bucket", ""),
                    "p_win_rehearsal": f"{p_win:.10f}",
                    "model_group": model_group,
                    "preview_action": "ABSTAIN",
                    "authorization_status": "RESEARCH_ONLY_NOT_AUTHORIZED",
                    "reason": "EXPLORATORY_REHEARSAL_NOT_AUTHORIZED_FOR_DEMO",
                    "broker_action_authorized": "false",
                }
            )
            count += 1
    return count


def _score_row(row: dict[str, str], rates: dict[str, Any]) -> tuple[float, str]:
    account_direction_key = f"{row.get('account_scope', '')}|{row.get('direction', '')}"
    by_account_direction = rates.get("by_account_direction", {})
    if account_direction_key in by_account_direction:
        return float(by_account_direction[account_direction_key].get("p_win", rates.get("global", 0.5))), f"account_direction:{account_direction_key}"
    direction_key = row.get("direction", "")
    by_direction = rates.get("by_direction", {})
    if direction_key in by_direction:
        return float(by_direction[direction_key].get("p_win", rates.get("global", 0.5))), f"direction:{direction_key}"
    return float(rates.get("global", 0.5)), "global"


def _diagnostic_label_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("y_win_expected") in {"0", "1"}]


def _candidate_training_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if str(row.get("candidate_trainable", "")).lower() == "true"
        and row.get("y_win_expected") in {"0", "1"}
    ]


def _refusal_reasons(snapshot_path: Path, diagnostic_rows: list[dict[str, str]]) -> list[str]:
    reasons: list[str] = []
    if not snapshot_path.exists():
        reasons.append(f"snapshot CSV missing: {snapshot_path}")
    if not diagnostic_rows:
        reasons.append("diagnostic labeled rows=0, required > 0 for rehearsal")
    labels = Counter(row.get("y_win_expected", "") for row in diagnostic_rows)
    if diagnostic_rows and (labels.get("0", 0) == 0 or labels.get("1", 0) == 0):
        reasons.append("diagnostic labels must include at least one positive and one negative row for rate rehearsal")
    return reasons


def _official_gate_blockers(readiness: dict[str, Any], data_audit: dict[str, Any]) -> list[str]:
    blockers = [
        f"{check.get('gate')} observed {check.get('observed')} required {check.get('required')}"
        for check in readiness.get("checks", [])
        if not check.get("passed", False)
    ]
    training_decision = data_audit.get("training_decision", {})
    if not training_decision.get("supervised_training_allowed", False):
        reason = training_decision.get("reason", "supervised training not allowed")
        blockers.append(f"C01 supervised_training_allowed=false: {reason}")
    return blockers


def _rates(rows: list[dict[str, str]], keys: list[str]) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups["|".join(str(row.get(key, "")) for key in keys)].append(row)
    output = {}
    for key, group_rows in sorted(groups.items()):
        positive = sum(1 for row in group_rows if row.get("y_win_expected") == "1")
        output[key] = {
            "rows": len(group_rows),
            "positive": positive,
            "negative": len(group_rows) - positive,
            "p_win": round(_smooth_rate(positive, len(group_rows)), 10),
        }
    return output


def _smooth_rate(positive: int, total: int) -> float:
    if total <= 0:
        return 0.5
    return (positive + 0.5) / (total + 1.0)


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_exploratory_training_rehearsal_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c18_exploratory_training_rehearsal_report"] = payload["outputs"]["status_report_json"]
    pointer["c18_exploratory_training_rehearsal_status"] = payload["status"]
    pointer["c18_exploratory_training_rehearsal_artifact"] = payload["outputs"]["rehearsal_artifact_json"]
    pointer["c18_exploratory_shadow_preview_csv"] = payload["outputs"]["shadow_preview_csv"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _resolve_report(root: Path, configured: str | None, *fallbacks: str) -> Path:
    candidates = [configured, *fallbacks]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if not path.is_absolute():
            path = root / path
        if path.exists():
            return path.resolve()
    first = Path(next(item for item in candidates if item))
    return (first if first.is_absolute() else root / first).resolve()


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
