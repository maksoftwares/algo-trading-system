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


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_STATUS.json"
DEFAULT_C51_JSON = Path("outputs") / "reports" / "A3_ML_STRATEGY_TESTER_REPLAY_PACKET_STATUS.json"
DEFAULT_C52_JSON = Path("outputs") / "reports" / "A3_ML_ISOLATED_STRATEGY_TESTER_WORKSPACE_STATUS.json"
SCHEMA_VERSION = "a3_ml_isolated_strategy_tester_terminal_root_status_v1"
STATUS_READY = "ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_READY"
STATUS_BLOCKED = "ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_BLOCKED"
DEFAULT_LANE_PREFERENCE = ("A2_Phase2ExperimentalDemoExecutor_XAUUSD_M5",)
COPY_BINARY_NAMES = ("terminal64.exe", "MetaEditor64.exe", "metatester64.exe", "Terminal.ico")
LAUNCH_APPROVAL_TOKEN = "RUN_ISOLATED_TESTER_REVIEW_ONLY"
EXTERNAL_SAFE_ROOT = Path("C:/A3IsolatedStrategyTester")
DEFAULT_DEMO_SERVER = "Capital.ComMena-Demo"


def prepare_isolated_strategy_tester_terminal_root(
    root: Path,
    report_json: Path | None = None,
    *,
    c51_json: Path | None = None,
    c52_json: Path | None = None,
    lane_id: str | None = None,
    terminal_root: Path | None = None,
) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    c51_json = (c51_json or root / DEFAULT_C51_JSON).resolve()
    c52_json = (c52_json or root / DEFAULT_C52_JSON).resolve()
    c51 = _read_json(c51_json)
    c52 = _read_json(c52_json)
    selected = _select_lane(c51, c52, lane_id)
    dataset_version = str(c52.get("dataset_version") or c51.get("dataset_version") or "UNKNOWN_DATASET")
    lane_name = selected.get("lane_name", "")
    terminal_root = (terminal_root or _default_terminal_root(root, c52, lane_name)).resolve()
    target_guard = _target_within_allowed_roots(root, terminal_root)
    prepared = _prepare_terminal_root(selected, terminal_root) if target_guard["passed"] else _blocked_terminal_root(selected, terminal_root, target_guard)
    ready = (
        c51.get("status") == "STRATEGY_TESTER_REPLAY_PACKET_READY"
        and c52.get("status") == "ISOLATED_STRATEGY_TESTER_WORKSPACE_READY"
        and prepared.get("terminal_root_ready") is True
    )
    payload = {
        "status": STATUS_READY if ready else STATUS_BLOCKED,
        "stage": "C53-ISOLATED-STRATEGY-TESTER-TERMINAL-ROOT",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": dataset_version,
        "c51_status": c51.get("status", "MISSING"),
        "c52_status": c52.get("status", "MISSING"),
        "selected_lane_id": lane_name,
        "selected_lane": prepared,
        "commands": _commands(root, report_json, prepared),
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
            "account_dat_copied": False,
            "server_dat_copied": False,
            "terminal_binary_copied": bool(prepared.get("terminal_binary_copied")),
            "history_cache_copied": False,
            "compiled_expert_copied_to_isolated_terminal_root": bool(prepared.get("compiled_expert_copied")),
            "safe_preset_copied_to_isolated_terminal_root": bool(prepared.get("safe_preset_copied")),
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
            "terminal_root": str(terminal_root),
        },
        "next_allowed_stage": _next_allowed_stage(ready),
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_isolated_strategy_tester_terminal_root_md(payload: dict[str, Any]) -> str:
    lane = payload.get("selected_lane", {})
    check_rows = [
        {
            "Check": check.get("check", ""),
            "Pass": str(check.get("passed", False)).lower(),
            "Detail": check.get("detail", ""),
        }
        for check in lane.get("checks", [])
    ]
    artifact_rows = [
        {
            "Artifact": artifact.get("name", ""),
            "Path": artifact.get("path", ""),
            "SHA256": artifact.get("sha256", ""),
        }
        for artifact in lane.get("artifacts", [])
    ]
    command_lines = "\n".join(f"- {key}: `{value}`" for key, value in payload.get("commands", {}).items())
    return "\n".join(
        [
            "# A3 ML Isolated Strategy Tester Terminal Root",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            f"Selected lane: {payload.get('selected_lane_id', '')}",
            f"C51 status: {payload.get('c51_status', '')}",
            f"C52 status: {payload.get('c52_status', '')}",
            "",
            "## Terminal Root",
            "",
            f"- Path: {lane.get('terminal_root', '')}.",
            f"- Terminal executable: {lane.get('isolated_terminal_exe', '')}.",
            f"- Tester config: {lane.get('tester_config_path', '')}.",
            f"- Review-only launcher: {lane.get('review_only_launch_stub', '')}.",
            "",
            "## Checks",
            "",
            _table(check_rows, ["Check", "Pass", "Detail"]),
            "",
            "## Artifact Hashes",
            "",
            _table(artifact_rows, ["Artifact", "Path", "SHA256"]),
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
            "- accounts.dat copied: false.",
            "- servers.dat copied: false.",
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


def _prepare_terminal_root(selected: dict[str, Any], terminal_root: Path) -> dict[str, Any]:
    c51_lane = selected.get("c51_lane", {})
    c52_lane = selected.get("c52_lane", {})
    source_terminal_exe = Path(str(c51_lane.get("terminal_exe", "")))
    source_terminal_dir = source_terminal_exe.parent
    workspace = Path(str(c52_lane.get("workspace_path", "")))
    lane_name = selected.get("lane_name", "")
    checks = [
        _check("lane_selected", bool(lane_name), lane_name or "no lane selected"),
        _check("c52_workspace_ready", c52_lane.get("workspace_ready") is True, str(c52_lane.get("workspace_ready"))),
        _check("source_terminal_exe_exists", source_terminal_exe.exists(), str(source_terminal_exe)),
        _check("source_workspace_exists", workspace.exists(), str(workspace)),
    ]
    if not all(check["passed"] for check in checks):
        return _blocked_terminal_root(selected, terminal_root, *checks)

    terminal_root.mkdir(parents=True, exist_ok=True)
    _remove_prohibited_config_files(terminal_root)
    binary_artifacts = _copy_terminal_binaries(source_terminal_dir, terminal_root)
    copied_binary_names = {Path(artifact["path"]).name for artifact in binary_artifacts}
    terminal_exe = terminal_root / "terminal64.exe"
    shutil.copytree(workspace / "MQL5", terminal_root / "MQL5", dirs_exist_ok=True)
    source_preset = Path(str(c52_lane.get("copied_preset_path", "")))
    tester_preset_target = terminal_root / "MQL5" / "Profiles" / "Tester" / source_preset.name
    tester_preset_target.parent.mkdir(parents=True, exist_ok=True)
    if source_preset.exists():
        shutil.copy2(source_preset, tester_preset_target)
    config_path = terminal_root / "Config" / f"{lane_name}.ini"
    report_path = terminal_root / "tester_reports" / f"{lane_name}.html"
    _write_tester_config(config_path, lane=c51_lane, preset_name=Path(str(c52_lane.get("copied_preset_path", ""))).name, report_path=report_path, window=selected.get("window", {}))
    launch_stub = terminal_root / f"RunReviewOnly_{lane_name}.ps1"
    _write_launch_stub(launch_stub, terminal_exe, config_path)
    _write_boundary_markers(terminal_root)
    artifacts = [
        *binary_artifacts,
        _artifact("expert_ex5", terminal_root / "MQL5" / "Experts" / Path(str(c52_lane.get("copied_expert_path", ""))).name),
        _artifact("preset_set", terminal_root / "MQL5" / "Presets" / Path(str(c52_lane.get("copied_preset_path", ""))).name),
        _artifact("tester_profile_preset_set", tester_preset_target),
        _artifact("tester_config", config_path),
        _artifact("review_only_launch_stub", launch_stub),
    ]
    checks.extend(
        [
            _check("terminal64_copied", "terminal64.exe" in copied_binary_names and terminal_exe.exists(), str(terminal_exe)),
            _check("account_secret_files_absent", _secret_files_absent(terminal_root), "accounts.dat/servers.dat/common.ini were not copied"),
            _check("tester_profile_preset_written", tester_preset_target.exists(), str(tester_preset_target)),
            _check("tester_config_written", config_path.exists(), str(config_path)),
            _check("review_only_launch_stub_written", launch_stub.exists(), str(launch_stub)),
        ]
    )
    ready = all(check["passed"] for check in checks)
    return {
        "lane_name": lane_name,
        "account_label": c51_lane.get("account_label", ""),
        "account_scope": c51_lane.get("account_scope", ""),
        "expert_name": c51_lane.get("expert_name", ""),
        "terminal_root_ready": ready,
        "terminal_root": str(terminal_root) if ready else "",
        "source_terminal_exe": str(source_terminal_exe),
        "isolated_terminal_exe": str(terminal_exe) if terminal_exe.exists() else "",
        "tester_config_path": str(config_path) if config_path.exists() else "",
        "review_only_launch_stub": str(launch_stub) if launch_stub.exists() else "",
        "terminal_binary_copied": "terminal64.exe" in copied_binary_names,
        "compiled_expert_copied": (terminal_root / "MQL5" / "Experts" / Path(str(c52_lane.get("copied_expert_path", ""))).name).exists(),
        "safe_preset_copied": (terminal_root / "MQL5" / "Presets" / Path(str(c52_lane.get("copied_preset_path", ""))).name).exists(),
        "tester_profile_preset_copied": tester_preset_target.exists(),
        "checks": checks,
        "artifacts": artifacts if ready else [],
    }


def _blocked_terminal_root(selected: dict[str, Any], terminal_root: Path, *extra_checks: dict[str, Any]) -> dict[str, Any]:
    checks = list(extra_checks) if extra_checks else [_check("terminal_root_not_prepared", False, str(terminal_root))]
    c51_lane = selected.get("c51_lane", {})
    return {
        "lane_name": selected.get("lane_name", ""),
        "account_label": c51_lane.get("account_label", ""),
        "account_scope": c51_lane.get("account_scope", ""),
        "expert_name": c51_lane.get("expert_name", ""),
        "terminal_root_ready": False,
        "terminal_root": "",
        "source_terminal_exe": str(c51_lane.get("terminal_exe", "")),
        "isolated_terminal_exe": "",
        "tester_config_path": "",
        "review_only_launch_stub": "",
        "terminal_binary_copied": False,
        "compiled_expert_copied": False,
        "safe_preset_copied": False,
        "checks": checks,
        "artifacts": [],
    }


def _select_lane(c51: dict[str, Any], c52: dict[str, Any], requested_lane_id: str | None) -> dict[str, Any]:
    c51_by_name = {_lane_name(lane): lane for lane in c51.get("lanes", []) if isinstance(lane, dict)}
    c52_by_name = {_lane_name(lane): lane for lane in c52.get("lanes", []) if isinstance(lane, dict)}
    candidates = [requested_lane_id] if requested_lane_id else [*DEFAULT_LANE_PREFERENCE, *c52_by_name.keys()]
    for candidate in candidates:
        if not candidate:
            continue
        if candidate in c51_by_name and candidate in c52_by_name:
            return {
                "lane_name": candidate,
                "c51_lane": c51_by_name[candidate],
                "c52_lane": c52_by_name[candidate],
                "window": c51.get("window", {}),
            }
    return {"lane_name": requested_lane_id or "", "c51_lane": {}, "c52_lane": {}, "window": c51.get("window", {})}


def _copy_terminal_binaries(source_dir: Path, terminal_root: Path) -> list[dict[str, str]]:
    artifacts: list[dict[str, str]] = []
    for name in COPY_BINARY_NAMES:
        source = source_dir / name
        if not source.exists():
            continue
        target = terminal_root / name
        shutil.copy2(source, target)
        artifacts.append(_artifact(f"terminal_binary_{name}", target))
    return artifacts


def _write_tester_config(path: Path, *, lane: dict[str, Any], preset_name: str, report_path: Path, window: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    start = _tester_date(str(window.get("historical_start_utc", "")))
    end = _tester_date(str(window.get("snapshot_cutoff_utc", "")))
    lines = [
        "; Generated by C53 for a dedicated isolated tester terminal root.",
        "; No account secrets or active terminal profile/config files were copied.",
        "; Launch remains review-only and requires the approval token in the PowerShell stub.",
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


def _write_launch_stub(path: Path, terminal_exe: Path, config_path: Path) -> None:
    text = "\n".join(
        [
            "param(",
            "    [Parameter(Mandatory=$true)]",
            "    [string]$ApprovalToken",
            ")",
            "$ErrorActionPreference = 'Stop'",
            f"if ($ApprovalToken -ne '{LAUNCH_APPROVAL_TOKEN}') {{ throw 'Approval token mismatch.' }}",
            f"$terminal = '{terminal_exe}'",
            f"$config = '{config_path}'",
            "if (-not (Test-Path -LiteralPath $terminal)) { throw 'Isolated terminal64.exe was not found.' }",
            "if (-not (Test-Path -LiteralPath $config)) { throw 'Tester config was not found.' }",
            "$resolved = (Resolve-Path -LiteralPath $terminal).Path",
            "$blocked = @('AppData\\Roaming\\MetaQuotes\\Terminal','MT5PortableTier1BestEA','MT5PortableRepairLane','Program Files\\MetaTrader 5')",
            "foreach ($item in $blocked) {",
            "    if ($resolved -like \"*$item*\") { throw \"Refusing active/non-isolated terminal path: $resolved\" }",
            "}",
            "$fso = New-Object -ComObject Scripting.FileSystemObject",
            "$configShort = $fso.GetFile($config).ShortPath",
            "$configArg = '/config:' + $configShort",
            "Start-Process -FilePath $resolved -ArgumentList @('/portable', $configArg) -Wait",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")


def _write_boundary_markers(terminal_root: Path) -> None:
    (terminal_root / "Config").mkdir(parents=True, exist_ok=True)
    (terminal_root / "MQL5" / "Files").mkdir(parents=True, exist_ok=True)
    (terminal_root / "Config" / "NO_ACCOUNT_SECRETS_COPIED.txt").write_text(
        "C53 copied no accounts.dat, servers.dat, common.ini, terminal.ini, history cache, or active profile files.\n",
        encoding="utf-8",
    )
    (terminal_root / "MQL5" / "Files" / "README_REPLAY_ONLY.txt").write_text(
        "This isolated root is for dry-run Strategy Tester replay evidence only. It does not authorize model training or broker action.\n",
        encoding="utf-8",
    )


def _commands(root: Path, report_json: Path, selected: dict[str, Any]) -> dict[str, str]:
    python = _quote(sys.executable)
    script = _quote(str(root / "scripts" / "c53_prepare_isolated_strategy_tester_terminal_root.py"))
    root_arg = _quote(str(root))
    lane_arg = selected.get("lane_name", "<lane_id>")
    launch_stub = selected.get("review_only_launch_stub") or "<RunReviewOnly.ps1>"
    return {
        "regenerate_terminal_root": f"{python} {script} --root {root_arg} --report-json {_quote(str(report_json))} --lane-id {lane_arg}",
        "future_review_only_launch": f"powershell -ExecutionPolicy Bypass -File {_quote(str(launch_stub))} -ApprovalToken {LAUNCH_APPROVAL_TOKEN}",
        "post_launch_rebuild": "After reviewer-approved replay output exists, hash logs and ask reviewer before importing any replay labels.",
    }


def _next_allowed_stage(ready: bool) -> str:
    if ready:
        return (
            "The isolated tester terminal root is prepared for one lane. "
            "A future launch must be explicit, single-lane, review-only, and followed by log hashing before any reviewer decision."
        )
    return "Fix C51/C52 readiness, missing terminal binaries, or missing C52 workspace files before attempting any replay launch."


def _target_within_allowed_roots(root: Path, terminal_root: Path) -> dict[str, Any]:
    allowed = (root / "outputs" / "reports" / "strategy_tester_replay").resolve()
    external = EXTERNAL_SAFE_ROOT.resolve()
    try:
        terminal_root.relative_to(allowed)
        return _check("terminal_root_inside_allowed_isolated_roots", True, str(terminal_root))
    except ValueError:
        pass
    try:
        terminal_root.relative_to(external)
        return _check("terminal_root_inside_allowed_isolated_roots", True, str(terminal_root))
    except ValueError:
        return _check(
            "terminal_root_inside_allowed_isolated_roots",
            False,
            f"{terminal_root} is outside {allowed} and {external}",
        )


def _default_terminal_root(root: Path, c52: dict[str, Any], lane_name: str) -> Path:
    if sys.platform == "win32" and (root / "config" / "ml" / "mt5_accounts.yaml").exists():
        return EXTERNAL_SAFE_ROOT / lane_name
    return Path(str(c52.get("workspace_root", root / "outputs" / "reports" / "strategy_tester_replay"))) / ".." / "isolated_terminal_roots" / lane_name


def _secret_files_absent(terminal_root: Path) -> bool:
    prohibited = (
        terminal_root / "Config" / "accounts.dat",
        terminal_root / "Config" / "servers.dat",
        terminal_root / "Config" / "common.ini",
        terminal_root / "Config" / "terminal.ini",
    )
    return not any(path.exists() for path in prohibited)


def _remove_prohibited_config_files(terminal_root: Path) -> None:
    for path in (
        terminal_root / "Config" / "accounts.dat",
        terminal_root / "Config" / "servers.dat",
        terminal_root / "Config" / "common.ini",
        terminal_root / "Config" / "terminal.ini",
    ):
        if path.exists():
            path.unlink()


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_isolated_strategy_tester_terminal_root_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c53_isolated_strategy_tester_terminal_root_report"] = payload["outputs"]["status_report_json"]
    pointer["c53_isolated_strategy_tester_terminal_root_status"] = payload["status"]
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
    return {"name": name, "path": str(path), "sha256": _sha256(path)}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed), "detail": detail}


def _lane_name(lane: dict[str, Any]) -> str:
    for key in ("isolated_config_path", "config_path"):
        value = str(lane.get(key, ""))
        if value:
            return _safe_name(Path(value).stem)
    return _safe_name(f"{lane.get('account_label', '')}_{lane.get('expert_name', '')}_{lane.get('symbol', 'XAUUSD')}_{lane.get('timeframe', 'M5')}")


def _tester_date(value: str) -> str:
    if not value:
        return datetime.now(timezone.utc).strftime("%Y.%m.%d")
    return parse_utc(value).strftime("%Y.%m.%d")


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "unnamed"


def _quote(value: str) -> str:
    return f'"{value}"' if " " in value else value
