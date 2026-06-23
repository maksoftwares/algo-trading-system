from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .broker_shadow_consumer_deploy import ACCOUNT_SOURCES
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_BROKER_SHADOW_MANUAL_ATTACH_PACKET.json"
SCHEMA_VERSION = "a3_ml_broker_shadow_manual_attach_packet_v1"
HANDOFF_FILE_NAME = "A3_ML_EA_HANDOFF.csv"
HANDOFF_INCLUDE_NAME = "A3MlEaHandoff.mqh"
SHADOW_TAP_INCLUDE_NAME = "A3MlShadowTap.mqh"
SHADOW_TAP_LOG_NAME = "a3_ml_broker_shadow_tap.csv"


def generate_broker_shadow_manual_attach_packet(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    reports = root / "outputs" / "reports"
    registry = load_mt5_account_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    c16 = _read_json(reports / "A3_ML_EA_CONSUMER_READINESS_STATUS.json")
    c17 = _read_json(reports / "A3_ML_BROKER_SHADOW_CONSUMER_DEPLOY_STATUS.json")
    c20 = _read_json(reports / "A3_ML_RUNTIME_EVIDENCE_STATUS.json")
    c30 = _read_json(reports / "A3_ML_BROKER_SHADOW_PRESET_DEPLOY_STATUS.json")
    accounts = [_account_payload(account, c16, c17, c20, c30) for account in registry.accounts]
    validations = _validations(accounts, c16, c17, c30)
    all_preflight_ready = all(item["passed"] for item in validations)
    all_runtime_logging = all(item["broker_shadow_tap_exists"] for item in accounts)
    any_runtime_logging = any(item["broker_shadow_tap_exists"] for item in accounts)
    if not all_preflight_ready:
        status = "PREFLIGHT_BLOCKED"
    elif all_runtime_logging:
        status = "BROKER_SHADOW_RUNTIME_PRESENT_ALL_ACCOUNTS"
    elif any_runtime_logging:
        status = "PARTIAL_BROKER_SHADOW_RUNTIME_PRESENT"
    else:
        status = "MANUAL_ATTACH_REQUIRED"
    payload = {
        "status": status,
        "stage": "C25-ML-BROKER-SHADOW-MANUAL-ATTACH-PACKET",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", ""),
        "authorization": {
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
            "manual_attach_required": status in {"MANUAL_ATTACH_REQUIRED", "PARTIAL_BROKER_SHADOW_RUNTIME_PRESENT"},
        },
        "inputs": {
            "registry_path": str(root / "config" / "ml" / "mt5_accounts.yaml"),
            "c16_ea_consumer_readiness": str(reports / "A3_ML_EA_CONSUMER_READINESS_STATUS.json"),
            "c17_broker_shadow_consumer_deploy": str(reports / "A3_ML_BROKER_SHADOW_CONSUMER_DEPLOY_STATUS.json"),
            "c20_runtime_evidence": str(reports / "A3_ML_RUNTIME_EVIDENCE_STATUS.json"),
            "c30_broker_shadow_preset_deploy": str(reports / "A3_ML_BROKER_SHADOW_PRESET_DEPLOY_STATUS.json"),
        },
        "upstream_statuses": {
            "c16_ea_consumer_readiness": c16.get("status", "MISSING"),
            "c17_broker_shadow_consumer_deploy": c17.get("status", "MISSING"),
            "c20_runtime_evidence": c20.get("status", "MISSING"),
            "c30_broker_shadow_preset_deploy": c30.get("status", "MISSING"),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "runtime_evidence": {
            "broker_shadow_tap_runtime_all_accounts": all_runtime_logging,
            "broker_shadow_tap_runtime_any_account": any_runtime_logging,
        },
        "accounts": accounts,
        "manual_attach_steps": _manual_steps(),
        "validations": validations,
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "terminal_runtime_launch_attempted": False,
            "terminal_shutdown_attempted": False,
            "profile_or_chart_file_write_attempted": False,
            "ea_file_drop_authorized": False,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer, payload)
    return report_json


def render_broker_shadow_manual_attach_packet_md(payload: dict[str, Any]) -> str:
    accounts = [
        {
            "Account": item["account_label"],
            "Login": item["account_scope"],
            "Active ready": str(item["active_broker_executors_ml_ready"]).lower(),
            "Expected EX5": str(item["expected_compiled_ex5_all_exist"]).lower(),
            "Safe presets": str(item["safe_preset_deployed_all"]).lower(),
            "Broker tap": str(item["broker_shadow_tap_exists"]).lower(),
        }
        for item in payload.get("accounts", [])
    ]
    validations = [
        {"Check": item["check"], "Passed": str(item["passed"]).lower(), "Detail": item["detail"]}
        for item in payload.get("validations", [])
    ]
    steps = "\n".join(f"{index}. {step}" for index, step in enumerate(payload.get("manual_attach_steps", []), start=1))
    account_details: list[str] = []
    for item in payload.get("accounts", []):
        recommended = ", ".join(item.get("recommended_experts", [])) or "-"
        presets = ", ".join(item.get("safe_preset_names", [])) or "-"
        account_details.extend(
            [
                f"### {item['account_label']} {item['account_scope']}",
                "",
                f"- Terminal: {item['terminal_exe']}",
                f"- Files root: {item['files_root']}",
                f"- Recommended broker-shadow expert(s): {recommended}",
                f"- Safe preset(s): {presets}",
                f"- Handoff file: {item['handoff_path']}",
                f"- Shadow tap log to watch: {item['broker_shadow_tap_path']}",
                f"- Shadow tap include: {item['shadow_tap_include_path']}",
                f"- Current active broker executor count: {item['active_broker_executor_count']}",
                "",
            ]
        )
    return "\n".join(
        [
            "# A3 ML Broker Shadow Manual Attach Packet",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Authorization",
            "",
            "- Python demo predictions authorized: false.",
            "- EA consumption authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Upstream Statuses",
            "",
            f"- C16 EA consumer readiness: {payload.get('upstream_statuses', {}).get('c16_ea_consumer_readiness', '')}",
            f"- C17 broker shadow consumer deploy: {payload.get('upstream_statuses', {}).get('c17_broker_shadow_consumer_deploy', '')}",
            f"- C20 runtime evidence: {payload.get('upstream_statuses', {}).get('c20_runtime_evidence', '')}",
            f"- C30 broker shadow preset deploy: {payload.get('upstream_statuses', {}).get('c30_broker_shadow_preset_deploy', '')}",
            "",
            "## Account Runtime State",
            "",
            _table(accounts, ["Account", "Login", "Active ready", "Expected EX5", "Safe presets", "Broker tap"]) if accounts else "No accounts configured.",
            "",
            "## Manual Attach Steps",
            "",
            steps,
            "",
            "## Account Details",
            "",
            *account_details,
            "## Validations",
            "",
            _table(validations, ["Check", "Passed", "Detail"]) if validations else "No validations ran.",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Terminal runtime launch attempted: false.",
            "- Terminal shutdown attempted: false.",
            "- Profile or chart file write attempted: false.",
            "- EA file drop authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _account_payload(account: MT5AccountSpec, c16: dict[str, Any], c17: dict[str, Any], c20: dict[str, Any], c30: dict[str, Any]) -> dict[str, Any]:
    data_root = Path(account.expected_data_path or "")
    files_root = Path(account.files_roots[0]) if account.files_roots else data_root / "MQL5" / "Files"
    c16_account = _account_by_label(c16, account.account_label)
    c20_account = _account_by_label(c20, account.account_label)
    c30_account = _account_by_label(c30, account.account_label) or _target_by_label(c30, account.account_label)
    active_broker_executors = [
        item
        for item in c16_account.get("active_broker_executors", [])
        if item.get("expert_name")
    ]
    active_profiles = [
        item
        for item in c16_account.get("attached_profiles", [])
        if item.get("enabled") is True and item.get("role") == "broker_executor_candidate"
    ]
    expected_experts = _expected_experts(account, c17)
    recommended = [item["expert_name"] for item in active_broker_executors] or [item["expert_name"] for item in expected_experts]
    safe_presets = _safe_presets(account, c30_account)
    broker_shadow_tap_path = files_root / SHADOW_TAP_LOG_NAME
    c20_tap = c20_account.get("broker_shadow_tap", {})
    handoff_path = files_root / HANDOFF_FILE_NAME
    c20_handoff = c20_account.get("handoff", {})
    active_ready = bool(active_broker_executors) and all(item.get("can_consume_ml_handoff") for item in active_broker_executors)
    expected_compiled_all = bool(expected_experts) and all(item["ex5_exists"] for item in expected_experts)
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "role": account.role,
        "terminal_exe": account.terminal_exe,
        "data_root": str(data_root),
        "files_root": str(files_root),
        "files_root_exists": files_root.exists(),
        "files_root_safe": _is_mql5_files_root(files_root),
        "handoff_path": str(handoff_path),
        "handoff_exists": bool(c20_handoff.get("exists", handoff_path.exists())),
        "shadow_tap_include_path": str(data_root / "MQL5" / "Include" / SHADOW_TAP_INCLUDE_NAME),
        "shadow_tap_include_exists": (data_root / "MQL5" / "Include" / SHADOW_TAP_INCLUDE_NAME).exists(),
        "handoff_include_path": str(data_root / "MQL5" / "Include" / HANDOFF_INCLUDE_NAME),
        "handoff_include_exists": (data_root / "MQL5" / "Include" / HANDOFF_INCLUDE_NAME).exists(),
        "broker_shadow_tap_path": str(broker_shadow_tap_path),
        "broker_shadow_tap_exists": bool(c20_tap.get("exists", broker_shadow_tap_path.exists())),
        "broker_shadow_tap_rows": int(c20_tap.get("csv_rows", 0) or 0),
        "active_profile_entries": active_profiles,
        "active_broker_executors": active_broker_executors,
        "active_broker_executor_count": len(active_broker_executors),
        "active_broker_executors_ml_ready": active_ready,
        "expected_broker_experts": expected_experts,
        "expected_compiled_ex5_all_exist": expected_compiled_all,
        "recommended_experts": recommended,
        "safe_presets": safe_presets,
        "safe_preset_names": [item["preset_name"] for item in safe_presets],
        "safe_preset_paths": [item["target_path"] for item in safe_presets],
        "safe_preset_deployed_all": bool(safe_presets) and all(item["exists"] and item["content_safe"] for item in safe_presets),
    }


def _expected_experts(account: MT5AccountSpec, c17: dict[str, Any]) -> list[dict[str, Any]]:
    data_root = Path(account.expected_data_path or "")
    deployed = [
        item
        for item in c17.get("deployed_files", [])
        if item.get("account_label") == account.account_label
    ]
    rows = []
    for source_name in ACCOUNT_SOURCES.get(account.account_label, ()):
        source_path = data_root / "MQL5" / "Experts" / source_name
        ex5_path = source_path.with_suffix(".ex5")
        rows.append(
            {
                "expert_name": Path(source_name).stem,
                "source_name": source_name,
                "source_path": str(source_path),
                "source_exists": source_path.exists(),
                "ex5_path": str(ex5_path),
                "ex5_exists": ex5_path.exists(),
                "source_reported_deployed": _artifact_reported(deployed, source_path, "expert_source"),
                "compiled_ex5_reported_deployed": _artifact_reported(deployed, ex5_path, "compiled_ex5"),
            }
        )
    return rows


def _safe_presets(account: MT5AccountSpec, c30_account: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in c30_account.get("presets", []):
        target_path = Path(item.get("target_path", ""))
        rows.append(
            {
                "expert_name": item.get("expert_name", ""),
                "source_name": item.get("source_name", ""),
                "preset_name": item.get("preset_name", ""),
                "target_path": str(target_path),
                "exists": target_path.exists(),
                "content_safe": bool(item.get("content_safe", False)),
                "account_scope": account.account_scope,
            }
        )
    return rows


def _validations(accounts: list[dict[str, Any]], c16: dict[str, Any], c17: dict[str, Any], c30: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        _check(
            "c16_broker_executor_consumers_ready",
            c16.get("status") == "BROKER_EXECUTOR_CONSUMERS_READY",
            c16.get("status", "MISSING"),
        ),
        _check(
            "c17_compiled_shadow_consumers_deployed",
            c17.get("status") == "DEPLOYED_COMPILED_SHADOW_CONSUMERS",
            c17.get("status", "MISSING"),
        ),
        _check(
            "c30_safe_passive_presets_deployed",
            c30.get("status") == "DEPLOYED_SAFE_PASSIVE_PRESETS",
            c30.get("status", "MISSING"),
        ),
    ]
    for account in accounts:
        prefix = account["account_label"]
        checks.extend(
            [
                _check(f"{prefix}_files_root_exists", bool(account["files_root_exists"]), account["files_root"]),
                _check(f"{prefix}_files_root_safe", bool(account["files_root_safe"]), account["files_root"]),
                _check(f"{prefix}_handoff_exists", bool(account["handoff_exists"]), account["handoff_path"]),
                _check(f"{prefix}_shadow_tap_include_exists", bool(account["shadow_tap_include_exists"]), account["shadow_tap_include_path"]),
                _check(f"{prefix}_handoff_include_exists", bool(account["handoff_include_exists"]), account["handoff_include_path"]),
                _check(
                    f"{prefix}_expected_compiled_ex5_exists",
                    bool(account["expected_compiled_ex5_all_exist"]),
                    _expected_ex5_detail(account),
                ),
                _check(
                    f"{prefix}_active_broker_executor_consumers_ready",
                    bool(account["active_broker_executors_ml_ready"]),
                    _active_broker_detail(account),
                ),
                _check(
                    f"{prefix}_safe_broker_shadow_presets_deployed",
                    bool(account["safe_preset_deployed_all"]),
                    _safe_preset_detail(account),
                ),
            ]
        )
    checks.append(_check("broker_action_false", True, "report-only; broker action remains false"))
    return checks


def _manual_steps() -> list[str]:
    return [
        "Open each MT5 terminal for A1, A2, and A3.",
        "Use a separate XAUUSD M5 chart for the broker-shadow check when you do not want to disturb any existing chart.",
        "Attach or reload the recommended broker-shadow expert for that account from the Account Details section.",
        "Load the matching C30 safe preset for that account and expert before clicking OK.",
        "Confirm InpDryRunOnly=true and InpBrokerActionAllowed=false before clicking OK.",
        f"Confirm InpMlShadowReadEnabled=true, InpMlHandoffFileName={HANDOFF_FILE_NAME}, and InpMlShadowLogFileName={SHADOW_TAP_LOG_NAME}.",
        f"Wait for {SHADOW_TAP_LOG_NAME} to appear in each account's MQL5/Files folder.",
        "Run C28 with --timeout-seconds 300 to wait for observer logs and Python preview read-path proof, then rerun C24.",
    ]


def _next_allowed_stage(status: str) -> str:
    if status == "BROKER_SHADOW_RUNTIME_PRESENT_ALL_ACCOUNTS":
        return "Broker shadow-tap runtime evidence is present on all accounts. Keep broker action false and continue C28/C24 readiness checks."
    if status == "PARTIAL_BROKER_SHADOW_RUNTIME_PRESENT":
        return "Some broker shadow taps are logging. Attach or reload the missing account broker-shadow charts, then rerun C28/C24."
    if status == "MANUAL_ATTACH_REQUIRED":
        return "Attach or reload dry-run broker-shadow consumers on XAUUSD M5 for A1, A2, and A3 using the C30 safe presets, then run C28 with a positive timeout."
    return "Fix C16/C17/C30 preflight or missing deployed files before expecting broker shadow tap logs."


def _active_broker_detail(account: dict[str, Any]) -> str:
    active = account.get("active_broker_executors", [])
    if not active:
        return "no active broker executor profile entries found"
    gaps = [item.get("expert_name", "") for item in active if not item.get("can_consume_ml_handoff")]
    if gaps:
        return "not ML-ready: " + ",".join(gaps)
    return "active broker executors can consume ML handoff"


def _expected_ex5_detail(account: dict[str, Any]) -> str:
    missing = [item["expert_name"] for item in account.get("expected_broker_experts", []) if not item.get("ex5_exists")]
    if missing:
        return "missing compiled EX5: " + ",".join(missing)
    return "compiled broker-shadow EX5 files exist"


def _safe_preset_detail(account: dict[str, Any]) -> str:
    presets = account.get("safe_presets", [])
    if not presets:
        return "no C30 safe presets found"
    missing = [item["preset_name"] for item in presets if not item.get("exists")]
    unsafe = [item["preset_name"] for item in presets if not item.get("content_safe")]
    if missing:
        return "missing presets: " + ",".join(missing)
    if unsafe:
        return "unsafe presets: " + ",".join(unsafe)
    return "safe C30 presets exist"


def _artifact_reported(deployed: list[dict[str, Any]], path: Path, artifact: str) -> bool:
    target = str(path)
    return any(item.get("artifact") == artifact and item.get("target_path") == target for item in deployed)


def _account_by_label(payload: dict[str, Any], label: str) -> dict[str, Any]:
    for item in payload.get("accounts", []):
        if item.get("account_label") == label:
            return item
    return {}


def _target_by_label(payload: dict[str, Any], label: str) -> dict[str, Any]:
    for item in payload.get("targets", []):
        if item.get("account_label") == label:
            return item
    return {}


def _is_mql5_files_root(path: Path) -> bool:
    parts = [part.casefold() for part in path.parts]
    return len(parts) >= 2 and parts[-2:] == ["mql5", "files"]


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_broker_shadow_manual_attach_packet_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c25_broker_shadow_manual_attach_packet_report"] = payload["outputs"]["status_report_json"]
    pointer["c25_broker_shadow_manual_attach_packet_status"] = payload["status"]
    pointer["broker_shadow_manual_attach_required"] = bool(payload["authorization"]["manual_attach_required"])
    pointer["broker_shadow_tap_runtime_evidence_all_accounts"] = bool(
        payload["runtime_evidence"]["broker_shadow_tap_runtime_all_accounts"]
    )
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _check(check: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": check, "passed": bool(passed), "detail": detail}


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
