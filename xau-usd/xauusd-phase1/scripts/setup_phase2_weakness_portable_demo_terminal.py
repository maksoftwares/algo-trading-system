from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deploy_phase2_weakness_breakout_executor import deploy_phase2_weakness_breakout_executor


DEFAULT_INSTALL_ROOT = Path("C:/Program Files/MetaTrader 5")
DEFAULT_SOURCE_DATA_DIR = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
)
DEFAULT_PORTABLE_ROOT = Path("C:/MT5PortableP2WeaknessDemo")
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "PHASE2_WEAKNESS_BR_V1_PORTABLE_DEMO_TERMINAL.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "PHASE2_WEAKNESS_BR_V1_PORTABLE_DEMO_TERMINAL.md"
CONFIG_NAME = "p2weakness_br_v1_startup.ini"
LOG_NAMES = (
    "p2weakness_br_v1_startup_xauusd.csv",
    "p2weakness_br_v1_signal_log_xauusd.csv",
    "p2weakness_br_v1_order_log_xauusd.csv",
)


def setup_phase2_weakness_portable_demo_terminal(
    phase1_root: Path,
    install_root: Path = DEFAULT_INSTALL_ROOT,
    source_data_dir: Path = DEFAULT_SOURCE_DATA_DIR,
    portable_root: Path = DEFAULT_PORTABLE_ROOT,
    output_json: Path | None = None,
    prepare: bool = False,
    launch: bool = False,
    deploy: bool = False,
    wait_seconds: int = 60,
) -> Path:
    phase1_root = phase1_root.resolve()
    install_root = install_root.resolve()
    source_data_dir = source_data_dir.resolve()
    portable_root = portable_root.resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    copied = _prepare_portable_root(phase1_root, install_root, source_data_dir, portable_root) if prepare else []
    if deploy:
        deploy_output = deploy_phase2_weakness_breakout_executor(
            phase1_root,
            terminal_data_dir=portable_root,
            metaeditor_exe=install_root / "MetaEditor64.exe",
            output_json=phase1_root / "outputs" / "reports" / "P2WEAKNESS_BR_V1_PORTABLE_DEPLOYMENT.json",
            allow_deploy=True,
        )
        deployment_report = str(deploy_output.markdown_path)
        compile_log = str(deploy_output.compile_log)
        deployed_ex5 = str(deploy_output.deployed_ex5)
    else:
        deployment_report = str(phase1_root / "outputs" / "reports" / "P2WEAKNESS_BR_V1_PORTABLE_DEPLOYMENT.md")
        compile_log = str(portable_root / "MQL5" / "Logs" / "compile_Phase2WeaknessBreakoutRetestExecutor.log")
        deployed_ex5 = str(portable_root / "MQL5" / "Experts" / "Phase2WeaknessBreakoutRetestExecutor.ex5")

    launch_started = False
    if launch:
        subprocess.Popen(
            [
                str(portable_root / "terminal64.exe"),
                "/portable",
                f"/config:{portable_root / 'Config' / CONFIG_NAME}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        launch_started = True
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            state = _log_state(portable_root)
            if _attached_log_detected(state):
                break
            time.sleep(1)

    logs = _log_state(portable_root)
    if launch_started and _attached_log_detected(logs):
        status = "PORTABLE_LAUNCHED_WITH_LOG"
    elif launch_started:
        status = "PORTABLE_READY_LAUNCH_SENT"
    elif prepare and deploy:
        status = "PORTABLE_PREPARED_AND_DEPLOYED_NO_LAUNCH"
    elif prepare:
        status = "PORTABLE_PREPARED_NO_DEPLOY_NO_LAUNCH"
    elif deploy:
        status = "PORTABLE_DEPLOYED_NO_LAUNCH"
    else:
        status = "PORTABLE_REPORT_ONLY_NO_PREPARE_NO_DEPLOY_NO_LAUNCH"
    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Isolated owner-requested demo terminal for P2WEAKNESS_BR_V1. It does not touch the current "
            "Capital.com demo terminal profile or old EA charts."
        ),
        "portable_root": str(portable_root),
        "source_install_root": str(install_root),
        "source_demo_data_dir": str(source_data_dir),
        "copied_paths": copied,
        "prepare_attempted": prepare,
        "deploy_attempted": deploy,
        "launch_started": launch_started,
        "terminal_exe": str(portable_root / "terminal64.exe"),
        "startup_config": str(portable_root / "Config" / CONFIG_NAME),
        "deployment_report": deployment_report,
        "compile_log": compile_log,
        "deployed_ex5": deployed_ex5,
        "logs": logs,
        "old_terminal_profile_touched": False,
        "old_terminal_closed_or_restarted": False,
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return output_json


def _prepare_portable_root(phase1_root: Path, install_root: Path, source_data_dir: Path, portable_root: Path) -> list[str]:
    portable_root.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in ("terminal64.exe", "MetaEditor64.exe", "metatester64.exe", "Terminal.ico"):
        copied.append(_copy_one(install_root / name, portable_root / name))
    for name in ("Bases", "Profiles", "Sounds"):
        source = install_root / name
        target = portable_root / name
        if source.exists() and not target.exists():
            shutil.copytree(source, target)
            copied.append(str(target))
    _copy_config(source_data_dir / "config", portable_root / "Config", copied)
    _copy_one(phase1_root / "mt5" / "Config" / CONFIG_NAME, portable_root / "Config" / CONFIG_NAME, copied)
    (portable_root / "MQL5" / "Files").mkdir(parents=True, exist_ok=True)
    return copied


def _copy_config(source: Path, target: Path, copied: list[str]) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        destination = target / item.name
        if item.is_dir():
            if destination.exists():
                continue
            shutil.copytree(item, destination)
            copied.append(str(destination))
        elif item.name in {
            "accounts.dat",
            "servers.dat",
            "common.ini",
            "terminal.ini",
            "settings.ini",
            "agents.dat",
            "dnsperf.dat",
            "hotkeys.ini",
        }:
            copied.append(_copy_one(item, destination))


def _copy_one(source: Path, destination: Path, copied: list[str] | None = None) -> str:
    if not source.exists():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(source, destination)
    except PermissionError:
        if destination.exists():
            return str(destination)
        raise
    if copied is not None:
        copied.append(str(destination))
    return str(destination)


def _log_state(portable_root: Path) -> dict[str, Any]:
    files = portable_root / "MQL5" / "Files"
    state: dict[str, Any] = {}
    for name in LOG_NAMES:
        path = files / name
        key = name.replace(".csv", "")
        state[f"{key}_path"] = str(path)
        state[f"{key}_exists"] = path.exists()
        state[f"{key}_size"] = path.stat().st_size if path.exists() else 0
    return state


def _attached_log_detected(state: dict[str, Any]) -> bool:
    return bool(
        state.get("p2weakness_br_v1_startup_xauusd_exists")
        or state.get("p2weakness_br_v1_signal_log_xauusd_exists")
    )


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 2 Weakness BR V1 Portable Demo Terminal",
        "",
        f"Status: {payload['status']}",
        "",
        payload["authority"],
        "",
        f"- Portable root: `{payload['portable_root']}`",
        f"- Terminal exe: `{payload['terminal_exe']}`",
        f"- Startup config: `{payload['startup_config']}`",
        f"- Prepare attempted: `{payload['prepare_attempted']}`",
        f"- Deploy attempted: `{payload['deploy_attempted']}`",
        f"- Launch started: `{payload['launch_started']}`",
        f"- Deployment report: `{payload['deployment_report']}`",
        f"- Compile log: `{payload['compile_log']}`",
        f"- Deployed EX5: `{payload['deployed_ex5']}`",
        f"- Old terminal profile touched: `{payload['old_terminal_profile_touched']}`",
        f"- Old terminal closed/restarted: `{payload['old_terminal_closed_or_restarted']}`",
        "",
        "## Runtime Logs",
        "",
    ]
    for key, value in payload["logs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report on, or explicitly prepare, an isolated P2WEAKNESS_BR_V1 portable demo terminal.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--install-root", type=Path, default=DEFAULT_INSTALL_ROOT)
    parser.add_argument("--source-data-dir", type=Path, default=DEFAULT_SOURCE_DATA_DIR)
    parser.add_argument("--portable-root", type=Path, default=DEFAULT_PORTABLE_ROOT)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--allow-prepare", action="store_true", help="Copy terminal/config files into the isolated portable root.")
    parser.add_argument("--allow-launch", action="store_true", help="Launch the isolated portable terminal after explicit preparation.")
    parser.add_argument("--allow-deploy", action="store_true", help="Deploy/copy/compile the P2WEAKNESS EA after all deploy preconditions pass.")
    parser.add_argument("--wait-seconds", type=int, default=60)
    args = parser.parse_args(argv)
    output = setup_phase2_weakness_portable_demo_terminal(
        args.phase1_root,
        install_root=args.install_root,
        source_data_dir=args.source_data_dir,
        portable_root=args.portable_root,
        output_json=args.output_json,
        prepare=args.allow_prepare,
        launch=args.allow_launch,
        deploy=args.allow_deploy,
        wait_seconds=args.wait_seconds,
    )
    print(output.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
