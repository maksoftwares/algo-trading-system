from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .isolated_strategy_tester_terminal_root import LAUNCH_APPROVAL_TOKEN
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_STRATEGY_TESTER_REPLAY_LAUNCH_STATUS.json"
DEFAULT_C53_JSON = Path("outputs") / "reports" / "A3_ML_ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_STATUS.json"
SCHEMA_VERSION = "a3_ml_strategy_tester_replay_launch_status_v1"
STATUS_COMPLETED_OUTPUTS_FOUND = "STRATEGY_TESTER_REPLAY_LAUNCH_COMPLETED_OUTPUTS_FOUND"
STATUS_COMPLETED_NO_OUTPUTS = "STRATEGY_TESTER_REPLAY_LAUNCH_COMPLETED_NO_OUTPUTS"
STATUS_TIMED_OUT = "STRATEGY_TESTER_REPLAY_LAUNCH_TIMED_OUT_STOPPED"
STATUS_FAILED = "STRATEGY_TESTER_REPLAY_LAUNCH_FAILED_PRECHECK"
DEFAULT_TIMEOUT_SECONDS = 180

Launcher = Callable[[list[str], Path, int], dict[str, Any]]


def run_isolated_strategy_tester_replay_launch(
    root: Path,
    report_json: Path | None = None,
    *,
    c53_json: Path | None = None,
    approval_token: str = "",
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    allow_isolated_account_context: bool = False,
    launcher: Launcher | None = None,
) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    c53_json = (c53_json or root / DEFAULT_C53_JSON).resolve()
    c53 = _read_json(c53_json)
    selected = c53.get("selected_lane", {}) if isinstance(c53.get("selected_lane"), dict) else {}
    prechecks = _prechecks(root, c53, selected, approval_token, allow_isolated_account_context)
    started_at = _utc_now()
    launch_result: dict[str, Any] = {
        "attempted": False,
        "returncode": None,
        "timed_out": False,
        "duration_seconds": 0.0,
        "stdout": "",
        "stderr": "",
    }
    if all(check["passed"] for check in prechecks):
        terminal = Path(str(selected.get("isolated_terminal_exe", ""))).resolve()
        config = Path(str(selected.get("tester_config_path", ""))).resolve()
        command = [str(terminal), "/portable", f"/config:{_short_path(config)}"]
        launch_result = (launcher or _launch_process)(command, terminal.parent, int(timeout_seconds))
    outputs = _collect_outputs(Path(str(selected.get("terminal_root", ""))), started_at)
    status = _status(prechecks, launch_result, outputs)
    payload = {
        "status": status,
        "stage": "C54-ISOLATED-STRATEGY-TESTER-REPLAY-LAUNCH",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": c53.get("dataset_version", ""),
        "c53_status": c53.get("status", "MISSING"),
        "selected_lane_id": c53.get("selected_lane_id", ""),
        "timeout_seconds": int(timeout_seconds),
        "prechecks": prechecks,
        "launch_result": launch_result,
        "replay_outputs": outputs,
        "authorization": {
            "strategy_tester_launch_authorized_for_this_run": approval_token == LAUNCH_APPROVAL_TOKEN,
            "isolated_account_context_allowed_for_this_run": bool(allow_isolated_account_context),
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted": bool(launch_result.get("attempted")),
            "terminal_launch_attempted": bool(launch_result.get("attempted")),
            "strategy_tester_launch_attempted": bool(launch_result.get("attempted")),
            "active_terminal_root_write_attempted": False,
            "terminal_config_or_account_secret_copied": False,
            "isolated_account_context_present": bool(_account_context_files(Path(str(selected.get("terminal_root", ""))))),
            "isolated_account_context_allowed_for_this_run": bool(allow_isolated_account_context),
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
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


def render_isolated_strategy_tester_replay_launch_md(payload: dict[str, Any]) -> str:
    check_rows = [
        {
            "Check": check.get("check", ""),
            "Pass": str(check.get("passed", False)).lower(),
            "Detail": check.get("detail", ""),
        }
        for check in payload.get("prechecks", [])
    ]
    output_rows = [
        {
            "Path": item.get("path", ""),
            "Size": item.get("size_bytes", ""),
            "SHA256": item.get("sha256", ""),
        }
        for item in payload.get("replay_outputs", [])
    ]
    launch = payload.get("launch_result", {})
    return "\n".join(
        [
            "# A3 ML Strategy Tester Replay Launch Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            f"Selected lane: {payload.get('selected_lane_id', '')}",
            f"C53 status: {payload.get('c53_status', '')}",
            "",
            "## Launch Result",
            "",
            f"- Attempted: {str(launch.get('attempted', False)).lower()}.",
            f"- Timed out: {str(launch.get('timed_out', False)).lower()}.",
            f"- Return code: {launch.get('returncode')}.",
            f"- Duration seconds: {launch.get('duration_seconds', 0)}.",
            f"- Isolated account context allowed: {str(payload['authorization'].get('isolated_account_context_allowed_for_this_run', False)).lower()}.",
            "",
            "## Preconditions",
            "",
            _table(check_rows, ["Check", "Pass", "Detail"]),
            "",
            "## Replay Outputs",
            "",
            _table(output_rows, ["Path", "Size", "SHA256"]),
            "",
            "## Boundary",
            "",
            f"- MT5 connection attempted: {str(payload['boundary']['mt5_connection_attempted']).lower()}.",
            f"- Terminal launch attempted: {str(payload['boundary']['terminal_launch_attempted']).lower()}.",
            f"- Strategy Tester launch attempted: {str(payload['boundary']['strategy_tester_launch_attempted']).lower()}.",
            "- Active terminal root write attempted: false.",
            "- Terminal config or account secret copied: false.",
            f"- Isolated account context present: {str(payload['boundary'].get('isolated_account_context_present', False)).lower()}.",
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


def _launch_process(command: list[str], cwd: Path, timeout_seconds: int) -> dict[str, Any]:
    started = time.monotonic()
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=creationflags,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
        timed_out = False
    except subprocess.TimeoutExpired:
        timed_out = True
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate(timeout=15)
    return {
        "attempted": True,
        "command": command,
        "cwd": str(cwd),
        "returncode": process.returncode,
        "timed_out": timed_out,
        "duration_seconds": round(time.monotonic() - started, 3),
        "stdout": (stdout or "")[-4000:],
        "stderr": (stderr or "")[-4000:],
    }


def _prechecks(
    root: Path,
    c53: dict[str, Any],
    selected: dict[str, Any],
    approval_token: str,
    allow_isolated_account_context: bool,
) -> list[dict[str, Any]]:
    terminal = Path(str(selected.get("isolated_terminal_exe", "")))
    config = Path(str(selected.get("tester_config_path", "")))
    terminal_root = Path(str(selected.get("terminal_root", "")))
    account_context_files = _account_context_files(terminal_root)
    return [
        _check("approval_token_valid", approval_token == LAUNCH_APPROVAL_TOKEN, "explicit launch token required"),
        _check("c53_ready", c53.get("status") == "ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_READY", str(c53.get("status", ""))),
        _check("selected_lane_ready", selected.get("terminal_root_ready") is True, str(selected.get("terminal_root_ready"))),
        _check("terminal_root_inside_allowed_isolated_roots", _inside_allowed_isolated_roots(root, terminal_root), str(terminal_root)),
        _check("not_active_terminal_root", _not_active_terminal_root(terminal_root), str(terminal_root)),
        _check("isolated_terminal_exe_exists", terminal.exists(), str(terminal)),
        _check("tester_config_exists", config.exists(), str(config)),
        _check(
            "account_context_absent_or_explicitly_allowed",
            not account_context_files or bool(allow_isolated_account_context),
            _account_context_detail(account_context_files, allow_isolated_account_context),
        ),
    ]


def _collect_outputs(terminal_root: Path, started_at_utc: str) -> list[dict[str, Any]]:
    if not terminal_root.exists():
        return []
    start = datetime.fromisoformat(started_at_utc.replace("Z", "+00:00"))
    roots = [
        terminal_root / "tester_reports",
        terminal_root / "MQL5" / "Files",
        terminal_root / "MQL5" / "Logs",
        terminal_root / "Logs",
        terminal_root / "Tester" / "logs",
    ]
    roots.extend(sorted(terminal_root.glob("Tester/Agent-*/MQL5/Files")))
    roots.extend(sorted(terminal_root.glob("Tester/Agent-*/logs")))
    outputs: list[dict[str, Any]] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            stat = path.stat()
            modified = datetime.fromtimestamp(stat.st_mtime, timezone.utc)
            if modified < start:
                continue
            outputs.append(
                {
                    "path": str(path),
                    "size_bytes": stat.st_size,
                    "modified_utc": modified.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                    "sha256": _sha256(path),
                }
            )
    return outputs


def _status(prechecks: list[dict[str, Any]], launch_result: dict[str, Any], outputs: list[dict[str, Any]]) -> str:
    if not all(check["passed"] for check in prechecks):
        return STATUS_FAILED
    if launch_result.get("timed_out"):
        return STATUS_TIMED_OUT
    if outputs:
        return STATUS_COMPLETED_OUTPUTS_FOUND
    return STATUS_COMPLETED_NO_OUTPUTS


def _next_allowed_stage(status: str) -> str:
    if status == STATUS_COMPLETED_OUTPUTS_FOUND:
        return "Inspect and hash-review replay outputs, then ask the reviewer before importing any replay labels."
    if status == STATUS_COMPLETED_NO_OUTPUTS:
        return "Inspect the isolated terminal logs/config manually; no replay output was found, so no labels can be imported."
    if status == STATUS_TIMED_OUT:
        return "Inspect partial logs in the isolated root. Do not rerun until the timeout cause is understood."
    return "Fix failed prechecks before any Strategy Tester launch."


def _inside_allowed_isolated_roots(root: Path, path: Path) -> bool:
    allowed = (root / "outputs" / "reports" / "strategy_tester_replay").resolve()
    external = Path("C:/A3IsolatedStrategyTester").resolve()
    try:
        path.resolve().relative_to(allowed)
        return True
    except ValueError:
        pass
    try:
        path.resolve().relative_to(external)
        return True
    except ValueError:
        return False


def _not_active_terminal_root(path: Path) -> bool:
    normalized = str(path.resolve()).replace("\\", "/").casefold()
    blocked = (
        "appdata/roaming/metaquotes/terminal",
        "mt5portabletier1bestea",
        "mt5portablerepairlane",
        "program files/metatrader 5",
    )
    return not any(item in normalized for item in blocked)


def _account_context_files(terminal_root: Path) -> list[Path]:
    candidates = (
        terminal_root / "Config" / "accounts.dat",
        terminal_root / "Config" / "servers.dat",
        terminal_root / "Config" / "common.ini",
        terminal_root / "Config" / "terminal.ini",
    )
    return [path for path in candidates if path.exists()]


def _account_context_detail(paths: list[Path], allowed: bool) -> str:
    if not paths:
        return "accounts.dat/servers.dat/common.ini/terminal.ini absent"
    names = ", ".join(path.name for path in paths)
    return f"isolated account context present ({names}); explicit allow flag={str(bool(allowed)).lower()}"


def _short_path(path: Path) -> str:
    if sys.platform != "win32":
        return str(path)
    try:
        import ctypes

        resolved = str(path.resolve())
        buffer = ctypes.create_unicode_buffer(32768)
        result = ctypes.windll.kernel32.GetShortPathNameW(resolved, buffer, len(buffer))
        if result:
            return buffer.value
    except Exception:
        pass
    return str(path)


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_isolated_strategy_tester_replay_launch_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c54_strategy_tester_replay_launch_report"] = payload["outputs"]["status_report_json"]
    pointer["c54_strategy_tester_replay_launch_status"] = payload["status"]
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed), "detail": detail}
