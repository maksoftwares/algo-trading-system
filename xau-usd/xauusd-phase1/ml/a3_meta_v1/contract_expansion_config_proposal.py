from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from .contract_scope import DEFAULT_CONFIG, KNOWN_EXPANSION_FAMILIES, SCHEMA_VERSION, normalize_family_name
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_CONTRACT_EXPANSION_CONFIG_PROPOSAL_STATUS.json"
STAGE = "C36-CONTRACT-EXPANSION-CONFIG-PROPOSAL"
STATUS_WAITING = "WAITING_FOR_REVIEW_APPROVAL"
STATUS_READY = "READY_TO_WRITE_APPROVED_CONFIG"
STATUS_WRITTEN = "APPROVED_CONFIG_WRITTEN"


def generate_contract_expansion_config_proposal(
    root: Path,
    report_json: Path | None = None,
    *,
    allowed_families: tuple[str, ...] | list[str] | None = None,
    review_reference: str = "",
    authorize: bool = False,
    write_config: bool = False,
    config_json: Path | None = None,
) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    config_json = (config_json or root / DEFAULT_CONFIG).resolve()
    c34 = _read_json(reports / "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json")
    c35 = _read_json(reports / "A3_ML_CONTRACT_EXPANSION_PACKET_STATUS.json")
    selected_families = _normalize_allowed_families(allowed_families)
    if authorize:
        _validate_authorized_request(selected_families, review_reference)
    candidates = _candidate_rows(c34.get("out_of_scope_candidates", []))
    selected = [candidate for candidate in candidates if candidate["family"] in set(selected_families)]
    proposed_config = _proposed_config(
        selected,
        selected_families,
        review_reference=review_reference,
        authorize=authorize,
    )
    status = STATUS_WAITING
    config_written = False
    if authorize:
        status = STATUS_READY
    if write_config:
        if not authorize:
            raise ValueError("write_config requires authorize=true")
        config_json.parent.mkdir(parents=True, exist_ok=True)
        _write_json_atomic(config_json, proposed_config)
        status = STATUS_WRITTEN
        config_written = True
    payload = {
        "status": status,
        "stage": STAGE,
        "created_at_utc": _utc_now(),
        "schema_version": "a3_ml_contract_expansion_config_proposal_status_v1",
        "dataset_version": c34.get("dataset_version") or c35.get("dataset_version", ""),
        "c34_status": c34.get("status", "MISSING"),
        "c35_status": c35.get("status", "MISSING"),
        "selected_families": list(selected_families),
        "review_reference": review_reference,
        "candidate_summary": _summary(candidates, selected),
        "family_summary": _family_summary(candidates, selected),
        "selected_entries": selected,
        "proposed_config_if_approved": proposed_config,
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
            "target_config_json": str(config_json),
        },
        "authorization": {
            "contract_expansion_config_authorized": bool(authorize),
            "config_write_attempted": bool(write_config),
            "config_written": bool(config_written),
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "terminal_runtime_change_authorized": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_contract_expansion_config_proposal_md(payload: dict[str, Any]) -> str:
    family_rows = [
        {
            "Family": item.get("family", ""),
            "Candidate Rows": str(item.get("candidate_would_signal_rows", 0)),
            "Selected Rows": str(item.get("selected_would_signal_rows", 0)),
            "Files": str(item.get("candidate_files", 0)),
        }
        for item in payload.get("family_summary", [])
    ]
    selected_rows = [
        {
            "Account": item.get("account_label", ""),
            "Family": item.get("family", ""),
            "Rows": str(item.get("would_signal_rows", 0)),
            "File": item.get("filename", ""),
        }
        for item in payload.get("selected_entries", [])
    ]
    return "\n".join(
        [
            "# A3 ML Contract Expansion Config Proposal",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Summary",
            "",
            f"- C34 status: {payload.get('c34_status', '')}.",
            f"- C35 status: {payload.get('c35_status', '')}.",
            f"- Selected families: {', '.join(payload.get('selected_families', [])) or 'none'}.",
            f"- Candidate files: {payload.get('candidate_summary', {}).get('candidate_files', 0)}.",
            f"- Selected files: {payload.get('candidate_summary', {}).get('selected_files', 0)}.",
            f"- Config written: {str(payload.get('authorization', {}).get('config_written', False)).lower()}.",
            "",
            "## Families",
            "",
            _table(family_rows, ["Family", "Candidate Rows", "Selected Rows", "Files"]) if family_rows else "No candidate families.",
            "",
            "## Selected Entries",
            "",
            _table(selected_rows, ["Account", "Family", "Rows", "File"]) if selected_rows else "No entries selected yet.",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Terminal runtime change authorized: false.",
            "- Model training authorized: false.",
            "- Python demo predictions authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _candidate_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in candidates:
        family = normalize_family_name(item.get("family"), item.get("filename"))
        if family not in KNOWN_EXPANSION_FAMILIES:
            continue
        filename = str(item.get("filename", "")).strip()
        account_label = str(item.get("account_label", "")).strip()
        if not filename or not account_label:
            continue
        rows.append(
            {
                "account_label": account_label,
                "account_scope": str(item.get("account_scope", "")).strip(),
                "filename": filename,
                "family": family,
                "logical_source_name": _logical_source_name(account_label, family, filename),
                "source_type": _source_type(filename),
                "schema_version": "csv_runtime_log_v1",
                "append_active": False,
                "would_signal_rows": int(item.get("would_signal_rows", 0) or 0),
                "min_signal_utc": item.get("min_signal_utc", ""),
                "max_signal_utc": item.get("max_signal_utc", ""),
                "review_reason": "C34 out-of-scope candidate; requires reviewer-approved contract expansion",
            }
        )
    return sorted(rows, key=lambda row: (row["account_label"], row["family"], row["filename"]))


def _proposed_config(
    selected: list[dict[str, Any]],
    selected_families: tuple[str, ...],
    *,
    review_reference: str,
    authorize: bool,
) -> dict[str, Any]:
    accounts: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for item in selected:
        account = accounts.setdefault(item["account_label"], {"entries": []})
        account["entries"].append(
            {
                "logical_source_name": item["logical_source_name"],
                "source_type": item["source_type"],
                "filename": item["filename"],
                "schema_version": item["schema_version"],
                "family": item["family"],
                "append_active": item["append_active"],
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_expansion_authorized": bool(authorize),
        "review_reference": review_reference if authorize else "",
        "allowed_families": list(selected_families) if authorize else [],
        "accounts": accounts if authorize else {},
    }


def _summary(candidates: list[dict[str, Any]], selected: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "candidate_files": len(candidates),
        "candidate_would_signal_rows": sum(item["would_signal_rows"] for item in candidates),
        "selected_files": len(selected),
        "selected_would_signal_rows": sum(item["would_signal_rows"] for item in selected),
    }


def _family_summary(candidates: list[dict[str, Any]], selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected_by_family: dict[str, int] = defaultdict(int)
    by_family: dict[str, dict[str, Any]] = {}
    for item in candidates:
        bucket = by_family.setdefault(
            item["family"],
            {"family": item["family"], "candidate_would_signal_rows": 0, "candidate_files": 0},
        )
        bucket["candidate_would_signal_rows"] += item["would_signal_rows"]
        bucket["candidate_files"] += 1
    for item in selected:
        selected_by_family[item["family"]] += item["would_signal_rows"]
    rows = []
    for family, bucket in sorted(by_family.items()):
        rows.append({**bucket, "selected_would_signal_rows": selected_by_family[family]})
    return rows


def _normalize_allowed_families(values: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    if not values:
        return ()
    output = []
    seen = set()
    for value in values:
        family = normalize_family_name(value)
        if family not in KNOWN_EXPANSION_FAMILIES:
            raise ValueError(f"unknown expansion family: {value}")
        if family not in seen:
            output.append(family)
            seen.add(family)
    return tuple(output)


def _validate_authorized_request(selected_families: tuple[str, ...], review_reference: str) -> None:
    if not selected_families:
        raise ValueError("authorize=true requires at least one allowed family")
    if not review_reference.strip():
        raise ValueError("authorize=true requires a non-empty review_reference")


def _logical_source_name(account_label: str, family: str, filename: str) -> str:
    stem = Path(filename).stem.lower()
    text = f"{account_label.lower()}_expansion_{family}_{stem}"
    return re.sub(r"[^a-z0-9_]+", "_", text).strip("_")[:96]


def _source_type(filename: str) -> str:
    lower = filename.lower()
    if "executor_signal" in lower:
        return "experimental_executor_signal_log"
    return "observer_signal_log"


def _next_allowed_stage(status: str) -> str:
    if status == STATUS_WRITTEN:
        return "Run C08/C07 with broker_action_authorized=false, then require C03/C05/C04/C06/C23 approval before demo Python predictions."
    if status == STATUS_READY:
        return "Config can be written only after operator confirms the reviewer approval is final. Broker action remains false."
    return "Send C35 to reviewer. After approval, rerun C36 with explicit allowed families and review reference."


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_contract_expansion_config_proposal_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c36_contract_expansion_config_proposal_report"] = payload["outputs"]["status_report_json"]
    pointer["c36_contract_expansion_config_proposal_status"] = payload["status"]
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
