from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic, parse_utc


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_ISOLATED_STRATEGY_TESTER_WORKSPACE_STATUS.json"
DEFAULT_C51_JSON = Path("outputs") / "reports" / "A3_ML_STRATEGY_TESTER_REPLAY_PACKET_STATUS.json"
SCHEMA_VERSION = "a3_ml_isolated_strategy_tester_workspace_status_v1"
STATUS_READY = "ISOLATED_STRATEGY_TESTER_WORKSPACE_READY"
STATUS_BLOCKED = "ISOLATED_STRATEGY_TESTER_WORKSPACE_BLOCKED"
DEFAULT_DEMO_SERVER = "Capital.ComMena-Demo"


def prepare_isolated_strategy_tester_workspace(
    root: Path,
    report_json: Path | None = None,
    *,
    c51_json: Path | None = None,
    workspace_root: Path | None = None,
) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    c51_json = (c51_json or root / DEFAULT_C51_JSON).resolve()
    c51 = _read_json(c51_json)
    dataset_version = str(c51.get("dataset_version") or "UNKNOWN_DATASET")
    packet_dir = Path(str(c51.get("outputs", {}).get("packet_dir") or root / "outputs" / "reports" / "strategy_tester_replay" / _safe_name(dataset_version)))
    workspace_root = (workspace_root or packet_dir / "isolated_workspaces").resolve()
    lanes = _prepare_lanes(c51, workspace_root)
    c51_ready = c51.get("status") == "STRATEGY_TESTER_REPLAY_PACKET_READY"
    ready = c51_ready and bool(lanes) and all(bool(lane.get("workspace_ready")) for lane in lanes)
    payload = {
        "status": STATUS_READY if ready else STATUS_BLOCKED,
        "stage": "C52-ISOLATED-STRATEGY-TESTER-WORKSPACE",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": dataset_version,
        "c51_status": c51.get("status", "MISSING"),
        "c51_report_json": str(c51_json),
        "workspace_root": str(workspace_root),
        "lane_count": len(lanes),
        "ready_lane_count": sum(1 for lane in lanes if lane.get("workspace_ready")),
        "lanes": lanes,
        "commands": _commands(root, report_json, lanes),
        "authorization": {
            "strategy_tester_launch_authorized": False,
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "terminal_launch_attempted": False,
            "strategy_tester_launch_attempted": False,
            "active_terminal_root_write_attempted": False,
            "terminal_config_or_account_secret_copied": False,
            "terminal_binary_copied": False,
            "history_cache_copied": False,
            "compiled_expert_copied_to_isolated_workspace": any(lane.get("copied_expert_path") for lane in lanes),
            "safe_preset_copied_to_isolated_workspace": any(lane.get("copied_preset_path") for lane in lanes),
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
            "workspace_root": str(workspace_root),
        },
        "next_allowed_stage": _next_allowed_stage(ready),
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_isolated_strategy_tester_workspace_md(payload: dict[str, Any]) -> str:
    lane_rows = [
        {
            "Account": lane.get("account_label", ""),
            "Expert": lane.get("expert_name", ""),
            "Ready": str(lane.get("workspace_ready", False)).lower(),
            "Workspace": lane.get("workspace_path", ""),
            "Config": lane.get("isolated_config_path", ""),
        }
        for lane in payload.get("lanes", [])
    ]
    copy_rows = [
        {
            "Account": lane.get("account_label", ""),
            "Expert": lane.get("expert_name", ""),
            "Artifact": artifact.get("name", ""),
            "SHA256": artifact.get("sha256", ""),
        }
        for lane in payload.get("lanes", [])
        for artifact in lane.get("artifacts", [])
    ]
    check_rows = [
        {
            "Account": lane.get("account_label", ""),
            "Expert": lane.get("expert_name", ""),
            "Check": check.get("check", ""),
            "Pass": str(check.get("passed", False)).lower(),
            "Detail": check.get("detail", ""),
        }
        for lane in payload.get("lanes", [])
        for check in lane.get("workspace_checks", [])
    ]
    command_lines = "\n".join(f"- {key}: `{value}`" for key, value in payload.get("commands", {}).items())
    return "\n".join(
        [
            "# A3 ML Isolated Strategy Tester Workspace",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            f"C51 status: {payload.get('c51_status', '')}",
            f"Ready lanes: {payload.get('ready_lane_count', 0)} / {payload.get('lane_count', 0)}",
            "",
            "## Workspaces",
            "",
            _table(lane_rows, ["Account", "Expert", "Ready", "Workspace", "Config"]),
            "",
            "## Checks",
            "",
            _table(check_rows, ["Account", "Expert", "Check", "Pass", "Detail"]),
            "",
            "## Artifact Hashes",
            "",
            _table(copy_rows, ["Account", "Expert", "Artifact", "SHA256"]),
            "",
            "## Commands",
            "",
            command_lines,
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Terminal launch attempted: false.",
            "- Strategy Tester launch attempted: false.",
            "- Active terminal root write attempted: false.",
            "- Terminal config or account secret copied: false.",
            "- Terminal binary copied: false.",
            "- History cache copied: false.",
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


def _prepare_lanes(c51: dict[str, Any], workspace_root: Path) -> list[dict[str, Any]]:
    window = c51.get("window", {}) if isinstance(c51.get("window"), dict) else {}
    lanes: list[dict[str, Any]] = []
    for lane in c51.get("lanes", []):
        if not isinstance(lane, dict):
            continue
        prepared = _prepare_lane(lane, workspace_root, window)
        lanes.append(prepared)
    return lanes


def _prepare_lane(lane: dict[str, Any], workspace_root: Path, window: dict[str, Any]) -> dict[str, Any]:
    lane_name = _lane_name(lane)
    workspace = workspace_root / lane_name
    source_expert = Path(str(lane.get("expert_deployed_path", "")))
    source_preset = Path(str(lane.get("preset_path", "")))
    expert_name = str(lane.get("expert_name", ""))
    preset_guard_checks = lane.get("preset_guard_checks", [])
    checks = [
        _check("c51_lane_config_ready", lane.get("config_ready") is True, str(lane.get("config_ready"))),
        _check("source_expert_exists", source_expert.exists(), str(source_expert)),
        _check("source_preset_exists", source_preset.exists(), str(source_preset)),
        _check("c51_preset_guards_passed", _c51_guards_passed(preset_guard_checks), "all C51 preset guards must pass"),
    ]
    ready = all(check["passed"] for check in checks)
    artifacts: list[dict[str, str]] = []
    copied_expert = ""
    copied_preset = ""
    config_path = ""
    launch_stub = ""
    tester_report = ""
    if ready:
        expert_target = workspace / "MQL5" / "Experts" / source_expert.name
        preset_target = workspace / "MQL5" / "Presets" / source_preset.name
        tester_preset_target = workspace / "MQL5" / "Profiles" / "Tester" / source_preset.name
        config_target = workspace / "Config" / f"{lane_name}.ini"
        report_target = workspace / "tester_reports" / f"{lane_name}.html"
        launch_target = workspace / f"RunReviewOnly_{lane_name}.ps1"
        expert_target.parent.mkdir(parents=True, exist_ok=True)
        preset_target.parent.mkdir(parents=True, exist_ok=True)
        tester_preset_target.parent.mkdir(parents=True, exist_ok=True)
        (workspace / "MQL5" / "Files").mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_expert, expert_target)
        shutil.copy2(source_preset, preset_target)
        shutil.copy2(source_preset, tester_preset_target)
        _write_tester_config(config_target, lane=lane, preset_name=preset_target.name, report_path=report_target, window=window)
        _write_launch_stub(launch_target, config_target)
        artifacts = [
            _artifact("expert_ex5", expert_target),
            _artifact("preset_set", preset_target),
            _artifact("tester_profile_preset_set", tester_preset_target),
            _artifact("tester_config", config_target),
            _artifact("review_only_launch_stub", launch_target),
        ]
        copied_expert = str(expert_target)
        copied_preset = str(preset_target)
        config_path = str(config_target)
        launch_stub = str(launch_target)
        tester_report = str(report_target)
    return {
        "account_label": lane.get("account_label", ""),
        "account_scope": lane.get("account_scope", ""),
        "expert_name": expert_name,
        "symbol": lane.get("symbol", "XAUUSD"),
        "timeframe": lane.get("timeframe", "M5"),
        "workspace_ready": ready,
        "workspace_path": str(workspace) if ready else "",
        "copied_expert_path": copied_expert,
        "copied_preset_path": copied_preset,
        "copied_tester_profile_preset_path": str(tester_preset_target) if ready else "",
        "isolated_config_path": config_path,
        "review_only_launch_stub": launch_stub,
        "tester_report_path": tester_report,
        "workspace_checks": checks,
        "artifacts": artifacts,
    }


def _write_tester_config(path: Path, *, lane: dict[str, Any], preset_name: str, report_path: Path, window: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    start = _tester_date(str(window.get("historical_start_utc", "")))
    end = _tester_date(str(window.get("snapshot_cutoff_utc", "")))
    lines = [
        "; Generated by C52 for an isolated Strategy Tester workspace.",
        "; Copy this workspace into a dedicated tester terminal root before launch.",
        "; This file does not authorize model training, EA consumption, or broker action.",
        "[Common]",
        f"Login={lane.get('account_scope', '')}",
        f"Server={DEFAULT_DEMO_SERVER}",
        "ProxyEnable=0",
        "NewsEnable=0",
        "",
        "[Tester]",
        f"Expert={lane.get('expert_name', '')}",
        f"ExpertParameters={preset_name}",
        f"Symbol={lane.get('symbol', 'XAUUSD')}",
        f"Period={lane.get('timeframe', 'M5')}",
        f"Login={lane.get('account_scope', '')}",
        "Model=0",
        "ExecutionMode=0",
        "Optimization=0",
        f"FromDate={start}",
        f"ToDate={end}",
        "ForwardMode=0",
        "Deposit=10000",
        "Currency=USD",
        "Leverage=1:100",
        f"Report={report_path}",
        "ReplaceReport=1",
        "ShutdownTerminal=1",
        "Visual=0",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_launch_stub(path: Path, config_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(
        [
            "param(",
            "    [Parameter(Mandatory=$true)]",
            "    [string]$IsolatedTerminalExe",
            ")",
            "$ErrorActionPreference = 'Stop'",
            "if (-not (Test-Path -LiteralPath $IsolatedTerminalExe)) { throw 'Isolated terminal64.exe was not found.' }",
            "$resolved = (Resolve-Path -LiteralPath $IsolatedTerminalExe).Path",
            "$blocked = @('AppData\\Roaming\\MetaQuotes\\Terminal','MT5PortableTier1BestEA','MT5PortableRepairLane','Program Files\\MetaTrader 5')",
            "foreach ($item in $blocked) {",
            "    if ($resolved -like \"*$item*\") { throw \"Refusing active/non-isolated terminal path: $resolved\" }",
            "}",
            "$fso = New-Object -ComObject Scripting.FileSystemObject",
            f"$configShort = $fso.GetFile('{config_path}').ShortPath",
            "& $resolved /portable ('/config:' + $configShort)",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")


def _commands(root: Path, report_json: Path, lanes: list[dict[str, Any]]) -> dict[str, str]:
    python = _quote(sys.executable)
    script = _quote(str(root / "scripts" / "c52_prepare_isolated_strategy_tester_workspace.py"))
    root_arg = _quote(str(root))
    first_stub = next((str(lane.get("review_only_launch_stub")) for lane in lanes if lane.get("review_only_launch_stub")), "<RunReviewOnly.ps1>")
    return {
        "regenerate_workspace": f"{python} {script} --root {root_arg} --report-json {_quote(str(report_json))}",
        "future_review_only_launch_template": f"powershell -ExecutionPolicy Bypass -File {_quote(first_stub)} -IsolatedTerminalExe <isolated-terminal64.exe>",
        "reviewer_question": "Ask reviewer whether isolated dry-run Strategy Tester outputs can be admitted as setup/label evidence before training.",
    }


def _next_allowed_stage(ready: bool) -> str:
    if ready:
        return (
            "Inspect the C52 workspaces, place one workspace inside a dedicated isolated tester terminal root, "
            "then run a single review-only tester launch only after explicit operator approval. "
            "Replay output remains reviewer-gated and cannot authorize Python demo predictions."
        )
    return "Fix missing C51 readiness, compiled experts, or safe presets, then regenerate C52 before any tester launch."


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_isolated_strategy_tester_workspace_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c52_isolated_strategy_tester_workspace_report"] = payload["outputs"]["status_report_json"]
    pointer["c52_isolated_strategy_tester_workspace_status"] = payload["status"]
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


def _artifact(name: str, path: Path) -> dict[str, str]:
    return {
        "name": name,
        "path": str(path),
        "sha256": _sha256(path),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed), "detail": detail}


def _c51_guards_passed(checks: Any) -> bool:
    if not isinstance(checks, list) or not checks:
        return False
    return all(isinstance(check, dict) and check.get("passed") is True for check in checks)


def _lane_name(lane: dict[str, Any]) -> str:
    config_path = str(lane.get("config_path", ""))
    if config_path:
        return _safe_name(Path(config_path).stem)
    return _safe_name(f"{lane.get('account_label', '')}_{lane.get('expert_name', '')}_{lane.get('symbol', 'XAUUSD')}_{lane.get('timeframe', 'M5')}")


def _tester_date(value: str) -> str:
    if not value:
        return datetime.now(timezone.utc).strftime("%Y.%m.%d")
    return parse_utc(value).strftime("%Y.%m.%d")


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "unnamed"


def _quote(value: str) -> str:
    return f'"{value}"' if " " in value else value
