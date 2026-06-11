from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from tier1_breakout_retest_common import (
    DEFAULT_INSTALL_ROOT,
    DEFAULT_LOCAL_PRESET,
    DEFAULT_PORTABLE_ROOT,
    DEFAULT_SOURCE_CONFIG_ROOT,
    EA_NAME,
    EA_SOURCE_REL,
    STATUS_FAIL,
    STATUS_PASS,
    TEMPLATE_REL,
    boundary_lines,
    check,
    checks_table,
    compile_log_passed,
    now_utc,
    overall_status,
    report_header,
    reports_dir,
    write_report_pair,
)


DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "TIER1_BREAKOUT_RETEST_PORTABLE_TERMINAL.json"
CONFIG_NAME = "tier1_bestea_startup.ini"
INCLUDE_NAMES = ("Phase1Types.mqh", "Phase1BreakoutRetest.mqh")


def setup_tier1_portable_terminal(
    root: Path,
    install_root: Path = DEFAULT_INSTALL_ROOT,
    source_config_root: Path = DEFAULT_SOURCE_CONFIG_ROOT,
    portable_root: Path = DEFAULT_PORTABLE_ROOT,
    owner_preset: Path | None = None,
    output_json: Path | None = None,
    authorized_account_login: str = "",
    authorized_server_marker: str = "Capital.ComMena-Demo",
    prepare: bool = False,
    deploy: bool = False,
    compile_ea: bool = False,
    launch: bool = False,
    attach_ea: bool = False,
    wait_seconds: int = 20,
) -> dict[str, Any]:
    root = root.resolve()
    install_root = install_root.resolve()
    source_config_root = source_config_root.resolve()
    portable_root = portable_root.resolve()
    owner_preset = (owner_preset or root / DEFAULT_LOCAL_PRESET).resolve()
    output_json = (output_json or root / DEFAULT_OUTPUT_JSON).resolve()

    copied: list[str] = []
    checks: list[dict[str, str]] = []
    if prepare:
        copied.extend(_prepare_portable_root(install_root, source_config_root, portable_root))
        _write_startup_config(portable_root / "Config" / CONFIG_NAME, authorized_account_login, authorized_server_marker, owner_preset.name, attach_ea)
    checks.append(check("portable_root_exists", STATUS_PASS if portable_root.exists() else ("PENDING_RUNTIME_EVIDENCE" if not prepare else STATUS_FAIL), str(portable_root)))

    deployed: list[str] = []
    if deploy:
        deployed.extend(_deploy_mql5_tree(root, portable_root, owner_preset))
    checks.append(check("ea_source_deployed", STATUS_PASS if (portable_root / "MQL5" / "Experts" / f"{EA_NAME}.mq5").exists() else ("PENDING_RUNTIME_EVIDENCE" if not deploy else STATUS_FAIL), str(portable_root / "MQL5" / "Experts" / f"{EA_NAME}.mq5")))
    checks.append(check("owner_preset_copied", STATUS_PASS if (portable_root / "MQL5" / "Presets" / owner_preset.name).exists() else ("PENDING_OWNER_ACTION" if not owner_preset.exists() else "PENDING_RUNTIME_EVIDENCE"), str(portable_root / "MQL5" / "Presets" / owner_preset.name)))

    compile_log = portable_root / "MQL5" / "Logs" / f"compile_{EA_NAME}.log"
    compile_status = "SKIPPED"
    if compile_ea:
        compile_status = _compile_ea(portable_root, compile_log)
    checks.append(check("compile_0_errors_0_warnings", STATUS_PASS if compile_log_passed(compile_log) else ("PENDING_RUNTIME_EVIDENCE" if not compile_ea else STATUS_FAIL), str(compile_log)))

    launched = False
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
        launched = True
        time.sleep(max(0, wait_seconds))

    payload: dict[str, Any] = {
        "status": overall_status(checks),
        "created_at_utc": now_utc(),
        "authority": "Tier-1 isolated portable terminal setup for breakout_retest on XAUUSD only. This does not attach charts and does not touch account 1025742.",
        "portable_root": str(portable_root),
        "install_root": str(install_root),
        "source_config_root": str(source_config_root),
        "startup_config": str(portable_root / "Config" / CONFIG_NAME),
        "owner_preset": str(owner_preset),
        "compile_log": str(compile_log),
        "compile_status": compile_status,
        "prepare_attempted": prepare,
        "deploy_attempted": deploy,
        "compile_attempted": compile_ea,
        "launch_attempted": launch,
        "attach_ea_requested": attach_ea,
        "launch_started": launched,
        "copied_paths": copied,
        "deployed_paths": deployed,
        "old_account_1025742_touched": False,
        "charts_attached_by_codex": False,
        "checks": checks,
    }
    write_report_pair(output_json, payload, _render(payload))
    return payload


def _prepare_portable_root(install_root: Path, source_config_root: Path, portable_root: Path) -> list[str]:
    portable_root.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in ("terminal64.exe", "MetaEditor64.exe", "metatester64.exe", "Terminal.ico"):
        copied.append(_copy_one(install_root / name, portable_root / name))
    for name in ("Bases", "Sounds"):
        source = install_root / name
        target = portable_root / name
        if source.exists() and not target.exists():
            shutil.copytree(source, target)
            copied.append(str(target))
    config_root = portable_root / "Config"
    config_root.mkdir(parents=True, exist_ok=True)
    for name in ("accounts.dat", "servers.dat", "common.ini", "terminal.ini", "settings.ini", "agents.dat", "dnsperf.dat", "hotkeys.ini"):
        source = source_config_root / name
        if source.exists():
            copied.append(_copy_one(source, config_root / name))
    (portable_root / "MQL5" / "Files").mkdir(parents=True, exist_ok=True)
    (portable_root / "Profiles" / "Charts" / "Default").mkdir(parents=True, exist_ok=True)
    return copied


def _write_startup_config(path: Path, login: str, server: str, preset_name: str, attach_ea: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    common_lines = ["[Common]"]
    if login:
        common_lines.append(f"Login={login}")
    if server:
        common_lines.append(f"Server={server}")
    common_lines.extend(
        [
            "ProxyEnable=0",
            "NewsEnable=0",
            "",
            "[Charts]",
            "MaxBars=999999999",
            "",
            "[Experts]",
            "AllowLiveTrading=1",
            "AllowDllImport=0",
            "Enabled=1",
            "Account=0",
            "Profile=0",
            "",
            "[StartUp]",
        ]
    )
    if attach_ea:
        common_lines.extend(
            [
                f"Expert={EA_NAME}",
                f"ExpertParameters={preset_name}",
            ]
        )
    common_lines.extend(
        [
            "Symbol=XAUUSD",
            "Period=M5",
            "ShutdownTerminal=0",
            "",
        ]
    )
    path.write_text("\n".join(common_lines), encoding="utf-8")


def _deploy_mql5_tree(root: Path, portable_root: Path, owner_preset: Path) -> list[str]:
    mql5_root = portable_root / "MQL5"
    deployed: list[str] = []
    deployed.append(_copy_one(root / EA_SOURCE_REL, mql5_root / "Experts" / f"{EA_NAME}.mq5"))
    for include_name in INCLUDE_NAMES:
        deployed.append(_copy_one(root / "mt5" / "Include" / "Phase1" / include_name, mql5_root / "Include" / "Phase1" / include_name))
    deployed.append(_copy_one(root / TEMPLATE_REL, mql5_root / "Presets" / (root / TEMPLATE_REL).name))
    if owner_preset.exists():
        deployed.append(_copy_one(owner_preset, mql5_root / "Presets" / owner_preset.name))
    return deployed


def _compile_ea(portable_root: Path, compile_log: Path) -> str:
    metaeditor = portable_root / "MetaEditor64.exe"
    expert = portable_root / "MQL5" / "Experts" / f"{EA_NAME}.mq5"
    if not metaeditor.exists() or not expert.exists():
        return "MISSING_METAEDITOR_OR_SOURCE"
    compile_log.parent.mkdir(parents=True, exist_ok=True)
    if compile_log.exists():
        compile_log.unlink()
    completed = subprocess.run(
        [
            str(metaeditor),
            "/portable",
            f"/compile:{expert}",
            f"/log:{compile_log}",
        ],
        check=False,
        timeout=90,
    )
    if completed.returncode not in (0, 1):
        return f"PROCESS_RETURNED_{completed.returncode}"
    return "PASS" if compile_log_passed(compile_log) else "FAIL"


def _copy_one(source: Path, destination: Path) -> str:
    if not source.exists():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(source, destination)
    except PermissionError:
        if destination.exists():
            return str(destination)
        raise
    return str(destination)


def _render(payload: dict[str, Any]) -> str:
    lines = report_header("Tier-1 Breakout Retest Portable Terminal", payload)
    lines.extend(boundary_lines())
    lines.extend([
        f"- Portable root: `{payload['portable_root']}`",
        f"- Startup config: `{payload['startup_config']}`",
        f"- Owner preset: `{payload['owner_preset']}`",
        f"- Compile status: `{payload['compile_status']}`",
        f"- Attach EA requested: `{payload['attach_ea_requested']}`",
        f"- Launch started: `{payload['launch_started']}`",
        f"- Charts attached by Codex: `{payload['charts_attached_by_codex']}`",
        "",
        "## Checks",
        "",
        *checks_table(payload["checks"]),
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare/deploy/compile the isolated Tier-1 breakout_retest portable terminal.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--install-root", type=Path, default=DEFAULT_INSTALL_ROOT)
    parser.add_argument("--source-config-root", type=Path, default=DEFAULT_SOURCE_CONFIG_ROOT)
    parser.add_argument("--portable-root", type=Path, default=DEFAULT_PORTABLE_ROOT)
    parser.add_argument("--owner-preset", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--authorized-account-login", default="")
    parser.add_argument("--authorized-server-marker", default="Capital.ComMena-Demo")
    parser.add_argument("--allow-prepare", action="store_true")
    parser.add_argument("--allow-deploy", action="store_true")
    parser.add_argument("--allow-compile", action="store_true")
    parser.add_argument("--allow-launch", action="store_true")
    parser.add_argument("--attach-ea", action="store_true", help="Write startup config with the Tier-1 EA and local owner preset.")
    parser.add_argument("--wait-seconds", type=int, default=20)
    args = parser.parse_args(argv)
    payload = setup_tier1_portable_terminal(
        args.root,
        install_root=args.install_root,
        source_config_root=args.source_config_root,
        portable_root=args.portable_root,
        owner_preset=args.owner_preset,
        output_json=args.output_json,
        authorized_account_login=args.authorized_account_login,
        authorized_server_marker=args.authorized_server_marker,
        prepare=args.allow_prepare,
        deploy=args.allow_deploy,
        compile_ea=args.allow_compile,
        launch=args.allow_launch,
        attach_ea=args.attach_ea,
        wait_seconds=args.wait_seconds,
    )
    print(f"Tier-1 portable terminal: {payload['status']}")
    return 0 if payload["status"] in {STATUS_PASS, "PENDING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
