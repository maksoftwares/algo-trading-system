from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .demo_shadow_operator_runbook import generate_demo_shadow_operator_runbook
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_DEMO_OPERATOR_LAUNCH_KIT_STATUS.json"
DEFAULT_KIT_SCRIPT = Path("outputs") / "reports" / "A3_ML_DEMO_OPERATOR_LAUNCH_KIT.ps1"
SCHEMA_VERSION = "a3_ml_demo_operator_launch_kit_status_v1"
FORBIDDEN_SCRIPT_TOKENS = (
    "OrderSend",
    "OrderSendAsync",
    "CTrade",
    "TRADE_ACTION_",
    "AutoTrading",
    "AllowLiveTrading=1",
    "Start-Process",
    "Stop-Process",
    "Remove-Item",
    "Move-Item",
)


def generate_demo_operator_launch_kit(root: Path, report_json: Path | None = None, kit_script: Path | None = None) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    kit_script = (kit_script or root / DEFAULT_KIT_SCRIPT).resolve()
    c29_path = generate_demo_shadow_operator_runbook(root)
    reports = root / "outputs" / "reports"
    c29 = _read_json(c29_path)
    c31 = _read_json(reports / "A3_ML_DEMO_ATTACH_WATCH_STATUS.json")
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    accounts = c29.get("accounts", [])
    script_text = _render_kit_script(root, c29, c31)
    validations = _validations(accounts, script_text, kit_script)
    ready = all(item["passed"] for item in validations)
    if c31.get("status") == "ATTACH_RUNTIME_FILES_PRESENT_ALL_ACCOUNTS":
        status = "ATTACH_FILES_READY_RUN_C28"
    elif ready:
        status = "READY_OPERATOR_ATTACH_KIT"
    else:
        status = "PREFLIGHT_BLOCKED"
    kit_script.parent.mkdir(parents=True, exist_ok=True)
    kit_script.write_text(script_text, encoding="utf-8")
    payload = {
        "status": status,
        "stage": "C32-DEMO-OPERATOR-LAUNCH-KIT",
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
            "c29_demo_shadow_operator_runbook": c29.get("status", "MISSING"),
            "c31_demo_attach_watch": c31.get("status", "MISSING"),
            "account_count": len(accounts),
        },
        "accounts": accounts,
        "commands": _commands(root, kit_script),
        "inputs": {
            "c29_demo_shadow_operator_runbook": str(c29_path),
            "c31_demo_attach_watch": str(reports / "A3_ML_DEMO_ATTACH_WATCH_STATUS.json"),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
            "operator_kit_script": str(kit_script),
        },
        "validations": validations,
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "terminal_runtime_launch_attempted": False,
            "terminal_shutdown_attempted": False,
            "profile_or_chart_file_write_attempted": False,
            "operator_script_generated": True,
            "operator_script_executed": False,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer, payload)
    return report_json


def render_demo_operator_launch_kit_md(payload: dict[str, Any]) -> str:
    accounts = [
        {
            "Account": item.get("account_label", ""),
            "Login": item.get("account_scope", ""),
            "Observer": item.get("observer_expert_name", ""),
            "Broker-shadow": ", ".join(item.get("recommended_broker_shadow_experts", [])),
        }
        for item in payload.get("accounts", [])
    ]
    validations = [
        {"Check": item["check"], "Passed": str(item["passed"]).lower(), "Detail": item["detail"]}
        for item in payload.get("validations", [])
    ]
    commands = "\n".join(f"- {key}: `{value}`" for key, value in payload.get("commands", {}).items())
    return "\n".join(
        [
            "# A3 ML Demo Operator Launch Kit Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Summary",
            "",
            f"- C29 runbook: {payload.get('summary', {}).get('c29_demo_shadow_operator_runbook', '')}.",
            f"- C31 attach watch: {payload.get('summary', {}).get('c31_demo_attach_watch', '')}.",
            f"- Operator kit script: {payload.get('outputs', {}).get('operator_kit_script', '')}.",
            "",
            "## Accounts",
            "",
            _table(accounts, ["Account", "Login", "Observer", "Broker-shadow"]) if accounts else "No accounts configured.",
            "",
            "## Commands",
            "",
            commands,
            "",
            "## Validations",
            "",
            _table(validations, ["Check", "Passed", "Detail"]) if validations else "No validations ran.",
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
            "- Operator script generated: true.",
            "- Operator script executed: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _render_kit_script(root: Path, c29: dict[str, Any], c31: dict[str, Any]) -> str:
    python = sys.executable
    c31_script = root / "scripts" / "c31_watch_demo_attach.py"
    c28_script = root / "scripts" / "c28_wait_for_demo_shadow_post_attach.py"
    lines = [
        "$ErrorActionPreference = 'Stop'",
        f"$Python = {_ps_quote(python)}",
        f"$Root = {_ps_quote(str(root))}",
        "",
        "Write-Host 'A3 ML demo attach kit'",
        "Write-Host 'This script does not launch MT5, change profiles, or authorize broker action.'",
        "Write-Host ''",
        "Write-Host 'Attach matrix:'",
        "Write-Host @'",
        _attach_matrix(c29.get("accounts", [])),
        "'@",
        "Write-Host ''",
        f"Write-Host 'Current C31 status: {c31.get('status', 'MISSING')}'",
        "Write-Host 'Start/continue MT5 manual attach, then leave this watcher running.'",
        f"& $Python {_ps_quote(str(c31_script))} --root $Root --timeout-seconds 300 --poll-seconds 5",
        "Write-Host ''",
        "Write-Host 'If C31 reports ATTACH_RUNTIME_FILES_PRESENT_ALL_ACCOUNTS, run the final C28 proof:'",
        f"Write-Host (\"& '{python}' '{c28_script}' --root '{root}' --timeout-seconds 300 --poll-seconds 5\")",
        "",
    ]
    return "\n".join(lines)


def _attach_matrix(accounts: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for account in accounts:
        rows.extend(
            [
                f"{account.get('account_label', '')} {account.get('account_scope', '')}",
                f"  Terminal: {account.get('terminal_exe', '')}",
                f"  Observer: {account.get('observer_expert_name', 'A3MlPredictionObserver')}",
                f"  Observer preset: {account.get('observer_preset_path', '')}",
                "  Broker-shadow:",
            ]
        )
        experts = account.get("recommended_broker_shadow_experts", [])
        presets = account.get("safe_broker_shadow_preset_names", [])
        for index, expert in enumerate(experts):
            preset = presets[index] if index < len(presets) else "-"
            rows.append(f"    - {expert} using {preset}")
        rows.append(f"  Watch log: {account.get('broker_shadow_tap_path', '')}")
        rows.append("")
    return "\n".join(rows).rstrip()


def _validations(accounts: list[dict[str, Any]], script_text: str, kit_script: Path) -> list[dict[str, Any]]:
    forbidden = [token for token in FORBIDDEN_SCRIPT_TOKENS if token in script_text]
    return [
        _check("accounts_present", bool(accounts), f"accounts={len(accounts)}"),
        _check("kit_script_target_safe", _is_reports_file(kit_script), str(kit_script)),
        _check("script_contains_c31_watch", "c31_watch_demo_attach.py" in script_text, "C31 watcher command"),
        _check("script_contains_c28_proof_command", "c28_wait_for_demo_shadow_post_attach.py" in script_text, "C28 proof command"),
        _check("script_has_no_broker_action_tokens", not forbidden, ",".join(forbidden) if forbidden else "ok"),
    ]


def _commands(root: Path, kit_script: Path) -> dict[str, str]:
    python = _quote(sys.executable)
    root_arg = _quote(str(root))
    c32 = _quote(str(root / "scripts" / "c32_generate_demo_operator_launch_kit.py"))
    c31 = _quote(str(root / "scripts" / "c31_watch_demo_attach.py"))
    c28 = _quote(str(root / "scripts" / "c28_wait_for_demo_shadow_post_attach.py"))
    return {
        "regenerate_operator_launch_kit": f"{python} {c32} --root {root_arg}",
        "run_operator_launch_kit": f"powershell -ExecutionPolicy Bypass -File {_quote(str(kit_script))}",
        "demo_attach_watch": f"{python} {c31} --root {root_arg} --timeout-seconds 300 --poll-seconds 5",
        "post_attach_demo_shadow_wait": f"{python} {c28} --root {root_arg} --timeout-seconds 300 --poll-seconds 5",
    }


def _next_allowed_stage(status: str) -> str:
    if status == "ATTACH_FILES_READY_RUN_C28":
        return "C31 attach files are present. Run C28 for final Python preview read-path proof."
    if status == "READY_OPERATOR_ATTACH_KIT":
        return "Run the generated operator kit while attaching/reloading MT5 EAs, then run C28 after C31 passes."
    return "Fix C32 kit validations, regenerate the runbook, then rerun C32."


def _is_reports_file(path: Path) -> bool:
    parts = tuple(part.casefold() for part in path.parts)
    return len(parts) >= 3 and parts[-3:-1] == ("outputs", "reports") and path.suffix.casefold() == ".ps1"


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_demo_operator_launch_kit_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c32_demo_operator_launch_kit_report"] = payload["outputs"]["status_report_json"]
    pointer["c32_demo_operator_launch_kit_status"] = payload["status"]
    pointer["c32_demo_operator_launch_kit_script"] = payload["outputs"]["operator_kit_script"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _check(check: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": check, "passed": bool(passed), "detail": detail}


def _ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _quote(value: str) -> str:
    return f"'{value}'"


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
