from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_DEMO_SHADOW_OPERATOR_RUNBOOK_STATUS.json"
SCHEMA_VERSION = "a3_ml_demo_shadow_operator_runbook_status_v1"


def generate_demo_shadow_operator_runbook(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    reports = root / "outputs" / "reports"
    registry = load_mt5_account_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    c11 = _read_json(reports / "A3_ML_READINESS_GAP_REPORT.json")
    c15 = _read_json(reports / "A3_ML_OBSERVER_MANUAL_ATTACH_PACKET.json")
    c25 = _read_json(reports / "A3_ML_BROKER_SHADOW_MANUAL_ATTACH_PACKET.json")
    c26 = _read_json(reports / "A3_ML_RESEARCH_PREVIEW_HANDOFF_REHEARSAL_STATUS.json")
    c28 = _read_json(reports / "A3_ML_DEMO_SHADOW_POST_ATTACH_MONITOR_STATUS.json")
    c30 = _read_json(reports / "A3_ML_BROKER_SHADOW_PRESET_DEPLOY_STATUS.json")
    c31 = _read_json(reports / "A3_ML_DEMO_ATTACH_WATCH_STATUS.json")
    c32 = _read_json(reports / "A3_ML_DEMO_OPERATOR_LAUNCH_KIT_STATUS.json")
    accounts = [_account_row(account, c15, c25) for account in registry.accounts]
    status = _status(c15, c25, c26, c28, c11, c30)
    payload = {
        "status": status,
        "stage": "C29-DEMO-SHADOW-OPERATOR-RUNBOOK",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", ""),
        "authorization": {
            "official_model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "summary": {
            "c11_readiness_gap": c11.get("status", "MISSING"),
            "c15_observer_manual_attach": c15.get("status", "MISSING"),
            "c25_broker_shadow_manual_attach": c25.get("status", "MISSING"),
            "c26_research_preview_handoff": c26.get("status", "MISSING"),
            "c28_demo_shadow_post_attach": c28.get("status", "MISSING"),
            "c30_broker_shadow_preset_deploy": c30.get("status", "MISSING"),
            "c31_demo_attach_watch": c31.get("status", "MISSING"),
            "c32_demo_operator_launch_kit": c32.get("status", "MISSING"),
        },
        "accounts": accounts,
        "readiness_gaps": _readiness_gaps(c11),
        "operator_steps": _operator_steps(),
        "commands": _commands(root),
        "pass_conditions": _pass_conditions(),
        "inputs": {
            "registry_path": str(root / "config" / "ml" / "mt5_accounts.yaml"),
            "c11_readiness_gap": str(reports / "A3_ML_READINESS_GAP_REPORT.json"),
            "c15_observer_manual_attach": str(reports / "A3_ML_OBSERVER_MANUAL_ATTACH_PACKET.json"),
            "c25_broker_shadow_manual_attach": str(reports / "A3_ML_BROKER_SHADOW_MANUAL_ATTACH_PACKET.json"),
            "c26_research_preview_handoff": str(reports / "A3_ML_RESEARCH_PREVIEW_HANDOFF_REHEARSAL_STATUS.json"),
            "c28_demo_shadow_post_attach": str(reports / "A3_ML_DEMO_SHADOW_POST_ATTACH_MONITOR_STATUS.json"),
            "c30_broker_shadow_preset_deploy": str(reports / "A3_ML_BROKER_SHADOW_PRESET_DEPLOY_STATUS.json"),
            "c31_demo_attach_watch": str(reports / "A3_ML_DEMO_ATTACH_WATCH_STATUS.json"),
            "c32_demo_operator_launch_kit": str(reports / "A3_ML_DEMO_OPERATOR_LAUNCH_KIT_STATUS.json"),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
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


def render_demo_shadow_operator_runbook_md(payload: dict[str, Any]) -> str:
    summary_rows = [{"Item": key, "Status": str(value)} for key, value in payload.get("summary", {}).items()]
    account_rows = [
        {
            "Account": item.get("account_label", ""),
            "Observer logs": str(item.get("observer_runtime_logging", False)).lower(),
            "Broker tap": str(item.get("broker_shadow_tap_exists", False)).lower(),
            "Safe presets": str(item.get("safe_broker_shadow_presets", False)).lower(),
            "Handoff": str(item.get("handoff_exists", False)).lower(),
            "Terminal": item.get("terminal_exe", ""),
        }
        for item in payload.get("accounts", [])
    ]
    gap_rows = [
        {"Gate": item.get("gate", ""), "Gap": str(item.get("gap_text", ""))}
        for item in payload.get("readiness_gaps", [])
    ]
    steps = "\n".join(f"{index}. {step}" for index, step in enumerate(payload.get("operator_steps", []), start=1))
    commands = "\n".join(f"- {key}: `{value}`" for key, value in payload.get("commands", {}).items())
    pass_conditions = "\n".join(f"- {item}" for item in payload.get("pass_conditions", []))
    attach_matrix = _attach_matrix_lines(payload.get("accounts", []))
    return "\n".join(
        [
            "# A3 ML Demo Shadow Operator Runbook",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Summary",
            "",
            _table(summary_rows, ["Item", "Status"]) if summary_rows else "No summary.",
            "",
            "## Account State",
            "",
            _table(account_rows, ["Account", "Observer logs", "Broker tap", "Safe presets", "Handoff", "Terminal"]) if account_rows else "No accounts configured.",
            "",
            "## Exact Attach Matrix",
            "",
            attach_matrix,
            "",
            "## Operator Steps",
            "",
            steps,
            "",
            "## Commands",
            "",
            commands,
            "",
            "## Pass Conditions",
            "",
            pass_conditions,
            "",
            "## Data Gaps",
            "",
            _table(gap_rows, ["Gate", "Gap"]) if gap_rows else "No failed data gates in the current gap report.",
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


def _status(c15: dict[str, Any], c25: dict[str, Any], c26: dict[str, Any], c28: dict[str, Any], c11: dict[str, Any], c30: dict[str, Any]) -> str:
    if c30.get("status") != "DEPLOYED_SAFE_PASSIVE_PRESETS" and c28.get("status") != "DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS":
        return "ACTION_REQUIRED_DEPLOY_BROKER_SHADOW_PRESETS"
    if c15.get("status") == "PREFLIGHT_BLOCKED" or c25.get("status") == "PREFLIGHT_BLOCKED":
        return "PREFLIGHT_BLOCKED"
    if c26.get("status") != "PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED":
        return "ACTION_REQUIRED_PUBLISH_RESEARCH_PREVIEW_HANDOFF"
    if c28.get("status") == "DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS":
        if c11.get("status") == "C03_PASS":
            return "DEMO_SHADOW_RUNTIME_CONFIRMED_DATA_READY"
        return "DEMO_SHADOW_RUNTIME_CONFIRMED_WAITING_FOR_DATA"
    if c15.get("status") in {"MANUAL_ATTACH_REQUIRED", "PARTIAL_RUNTIME_LOGS_PRESENT"}:
        return "ACTION_REQUIRED_MANUAL_ATTACH"
    if c25.get("status") in {"MANUAL_ATTACH_REQUIRED", "PARTIAL_BROKER_SHADOW_RUNTIME_PRESENT"}:
        return "ACTION_REQUIRED_MANUAL_ATTACH"
    return "WAITING_FOR_DEMO_SHADOW_RUNTIME_PROOF"


def _account_row(account: MT5AccountSpec, c15: dict[str, Any], c25: dict[str, Any]) -> dict[str, Any]:
    observer = _by_label(c15, account.account_label)
    broker = _by_label(c25, account.account_label)
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "role": account.role,
        "terminal_exe": account.terminal_exe,
        "files_root": (account.files_roots[0] if account.files_roots else ""),
        "observer_runtime_logging": bool(observer.get("startup_log_exists") and observer.get("prediction_log_exists")),
        "observer_expert_exists": bool(observer.get("expert_exists")),
        "observer_preset_exists": bool(observer.get("preset_exists")),
        "observer_expert_name": "A3MlPredictionObserver",
        "observer_preset_path": observer.get("preset_path", ""),
        "handoff_exists": bool(observer.get("handoff_exists") or broker.get("handoff_exists")),
        "broker_shadow_tap_exists": bool(broker.get("broker_shadow_tap_exists")),
        "recommended_broker_shadow_experts": broker.get("recommended_experts", []),
        "safe_broker_shadow_presets": bool(broker.get("safe_preset_deployed_all", False)),
        "safe_broker_shadow_preset_names": broker.get("safe_preset_names", []),
        "safe_broker_shadow_preset_paths": broker.get("safe_preset_paths", []),
        "broker_shadow_tap_path": broker.get("broker_shadow_tap_path", ""),
    }


def _operator_steps() -> list[str]:
    return [
        "Open MT5 terminal A1, A2, and A3.",
        "On each account, open or select an XAUUSD M5 chart and attach A3MlPredictionObserver with the passive preset.",
        "On each account, attach or reload the recommended broker-shadow expert from the account state/details.",
        "For each broker-shadow expert, load the matching C30 safe preset before clicking OK.",
        "Confirm all broker-shadow settings stay dry-run/passive: InpDryRunOnly=true, InpBrokerActionAllowed=false, InpMlShadowReadEnabled=true.",
        "Run the C31 command while or after attaching to see which exact runtime files are still missing.",
        "Run the C28 command and wait for DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS.",
        "After C28 passes, keep collecting data and run the refresh command after market data advances.",
    ]


def _commands(root: Path) -> dict[str, str]:
    python = _quote(sys.executable)
    root_arg = _quote(str(root))
    c28 = _quote(str(root / "scripts" / "c28_wait_for_demo_shadow_post_attach.py"))
    c24 = _quote(str(root / "scripts" / "c24_generate_demo_prediction_action_packet.py"))
    c23 = _quote(str(root / "scripts" / "c23_run_demo_python_launch_controller.py"))
    c25 = _quote(str(root / "scripts" / "c25_generate_broker_shadow_manual_attach_packet.py"))
    c30 = _quote(str(root / "scripts" / "c30_deploy_broker_shadow_presets.py"))
    c31 = _quote(str(root / "scripts" / "c31_watch_demo_attach.py"))
    c32 = _quote(str(root / "scripts" / "c32_generate_demo_operator_launch_kit.py"))
    kit = _quote(str(root / "outputs" / "reports" / "A3_ML_DEMO_OPERATOR_LAUNCH_KIT.ps1"))
    return {
        "generate_operator_launch_kit": f"{python} {c32} --root {root_arg}",
        "run_operator_launch_kit": f"powershell -ExecutionPolicy Bypass -File {kit}",
        "deploy_broker_shadow_safe_presets": f"{python} {c30} --root {root_arg} --deploy",
        "broker_shadow_attach_packet": f"{python} {c25} --root {root_arg}",
        "demo_attach_watch": f"{python} {c31} --root {root_arg} --timeout-seconds 300 --poll-seconds 5",
        "post_attach_demo_shadow_wait": f"{python} {c28} --root {root_arg} --timeout-seconds 300 --poll-seconds 5",
        "check_action_packet": f"{python} {c24} --root {root_arg}",
        "refresh_after_market_data": f"{python} {c23} --root {root_arg} --refresh-live-readonly --post-attach-timeout-seconds 300 --post-attach-poll-seconds 5",
    }


def _pass_conditions() -> list[str]:
    return [
        "C28 status is DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS.",
        "C30 status is DEPLOYED_SAFE_PASSIVE_PRESETS.",
        "C27 has confirmed ml_available=true, ml_action=ABSTAIN, and ml_broker_action_authorized=false on A1/A2/A3.",
        "C20 shows passive observer runtime and broker shadow tap runtime on all accounts.",
        "C24 still shows broker_action_authorized=false.",
    ]


def _attach_matrix_lines(accounts: list[dict[str, Any]]) -> str:
    if not accounts:
        return "No accounts configured."
    lines: list[str] = []
    for item in accounts:
        experts = item.get("recommended_broker_shadow_experts", [])
        preset_names = item.get("safe_broker_shadow_preset_names", [])
        preset_paths = item.get("safe_broker_shadow_preset_paths", [])
        pairs = []
        for index, expert in enumerate(experts):
            preset_name = preset_names[index] if index < len(preset_names) else "-"
            preset_path = preset_paths[index] if index < len(preset_paths) else ""
            suffix = f" using {preset_name}" if preset_name != "-" else ""
            if preset_path:
                suffix += f" ({preset_path})"
            pairs.append(f"{expert}{suffix}")
        lines.extend(
            [
                f"### {item.get('account_label', '')} {item.get('account_scope', '')}",
                "",
                f"- Terminal: {item.get('terminal_exe', '')}",
                f"- Observer: {item.get('observer_expert_name', 'A3MlPredictionObserver')} using {item.get('observer_preset_path', '')}",
                f"- Broker-shadow: {', '.join(pairs) if pairs else '-'}",
                f"- Broker-shadow log to confirm: {item.get('broker_shadow_tap_path', '')}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _readiness_gaps(c11: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in c11.get("gate_gaps", []) if not item.get("passed")]


def _next_allowed_stage(status: str) -> str:
    if status == "DEMO_SHADOW_RUNTIME_CONFIRMED_DATA_READY":
        return "Demo-shadow runtime and data gates are ready. Run C10/C23 review before any official passive EA consumption."
    if status == "DEMO_SHADOW_RUNTIME_CONFIRMED_WAITING_FOR_DATA":
        return "Demo-shadow runtime is confirmed. Continue collecting/exporting A1/A2/A3 data until C03/C05/C04/C06 authorize official demo-shadow predictions."
    if status == "ACTION_REQUIRED_DEPLOY_BROKER_SHADOW_PRESETS":
        return "Run C30 with --deploy, regenerate C25/C29, then attach or reload MT5 EAs using the generated safe presets."
    if status == "ACTION_REQUIRED_MANUAL_ATTACH":
        return "Attach or reload the observer and broker-shadow consumers on A1/A2/A3, then run the C28 command."
    if status == "ACTION_REQUIRED_PUBLISH_RESEARCH_PREVIEW_HANDOFF":
        return "Run C26 with --publish, then attach/reload MT5 EAs and run C28."
    if status == "WAITING_FOR_DEMO_SHADOW_RUNTIME_PROOF":
        return "Run C28 with a positive timeout after MT5 attach/reload."
    return "Fix preflight blockers in C15/C25, then regenerate C29."


def _by_label(payload: dict[str, Any], label: str) -> dict[str, Any]:
    for item in payload.get("accounts", []):
        if item.get("account_label") == label:
            return item
    return {}


def _quote(value: str) -> str:
    return f"'{value}'"


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_demo_shadow_operator_runbook_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c29_demo_shadow_operator_runbook_report"] = payload["outputs"]["status_report_json"]
    pointer["c29_demo_shadow_operator_runbook_status"] = payload["status"]
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
