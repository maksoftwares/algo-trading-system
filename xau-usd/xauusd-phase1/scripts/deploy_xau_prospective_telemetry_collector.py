from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EA_NAME = "XauProspectiveTelemetryCollector"
EA_SOURCE = Path("mt5") / "Experts" / f"{EA_NAME}.mq5"
PRESET_SOURCE = Path("mt5") / "Presets" / f"{EA_NAME}.passive_xauusd.set"
DEFAULT_SOURCE_TERMINAL_ROOT = Path("C:/MT5PortableRepairLane")
DEFAULT_TARGET_ROOT = Path("C:/MT5PortableProspectiveCollector")

PROTECTED_RUNTIME_ROOTS = (
    Path("C:/Program Files/MetaTrader 5"),
    Path("C:/MT5PortableGoldMission"),
    Path("C:/MT5PortableTier1BestEA"),
    Path("C:/MT5PortableRepairLane"),
    Path("C:/MT5PortablePositionPathObserver"),
    Path("C:/MT5PortableTier1PathObserver"),
    Path("C:/MT5PortableShadowFixObservers"),
    Path("C:/MT5PortableTrendGuardedFixObservers"),
    Path("C:/MT5PortableSpreadLogger"),
    Path(
        "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/"
        "D0E8209F77C8CF37AD8BF550E51FF075"
    ),
)


def deploy_collector(
    phase1_root: Path,
    source_terminal_root: Path = DEFAULT_SOURCE_TERMINAL_ROOT,
    target_root: Path = DEFAULT_TARGET_ROOT,
    *,
    prepare: bool = False,
    deploy: bool = False,
    launch: bool = False,
    startup_login: str = "",
    startup_server: str = "",
    wait_seconds: int = 45,
) -> Path:
    phase1_root = phase1_root.resolve()
    source_terminal_root = source_terminal_root.resolve()
    target_root = target_root.resolve()
    _guard_target_root(source_terminal_root, target_root)

    actions: list[str] = []
    if prepare:
        actions.extend(_prepare_portable_root(source_terminal_root, target_root))

    compile_log: Path | None = None
    profile_backup: Path | None = None
    log_backup: Path | None = None
    startup_config: Path | None = None
    target_was_running = False
    if deploy:
        _require_prepared_root(target_root)
        target_was_running = _close_target_terminal(target_root)
        log_backup = _archive_existing_logs(target_root)
        actions.extend(_deploy_sources(phase1_root, target_root))
        compile_log = _compile_ea(target_root)
        profile_backup = _install_single_collector_profile(phase1_root, target_root)
        startup_config = _write_startup_config(target_root, startup_login, startup_server)

    if launch:
        _require_prepared_root(target_root)
        if startup_config is None:
            startup_config = _write_startup_config(target_root, startup_login, startup_server)
        command = [
            str(target_root / "terminal64.exe"),
            "/portable",
            f"/config:{startup_config}",
        ]
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _wait_for_collection(target_root, wait_seconds)

    health = inspect_collection_health(target_root)
    payload: dict[str, Any] = {
        "schema_version": "xau_prospective_collector_deployment_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": health["status"],
        "authority": {
            "telemetry_only": True,
            "trade_permission": False,
            "broker_action_allowed": False,
            "python_execution_authorized": False,
            "paid_data_authorized": False,
            "multiple_provider_id_creation_authorized": False,
        },
        "phase1_root": str(phase1_root),
        "source_terminal_root": str(source_terminal_root),
        "target_root": str(target_root),
        "prepare_attempted": prepare,
        "deploy_attempted": deploy,
        "launch_attempted": launch,
        "target_was_running_before_deploy": target_was_running,
        "actions": actions,
        "compile_log": str(compile_log) if compile_log else "not_requested",
        "profile_backup": str(profile_backup) if profile_backup else "none",
        "log_backup": str(log_backup) if log_backup else "none",
        "startup_config": str(startup_config) if startup_config else "not_requested",
        "health": health,
    }
    report_json = target_root / "collector_status.json"
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (target_root / "collector_status.md").write_text(_render_markdown(payload), encoding="utf-8")
    return report_json


def _guard_target_root(source_terminal_root: Path, target_root: Path) -> None:
    source = source_terminal_root.resolve()
    target = target_root.resolve()
    if target == source or source in target.parents:
        raise RuntimeError("Refusing to deploy the collector over its credential source terminal")
    for protected in PROTECTED_RUNTIME_ROOTS:
        protected_resolved = protected.resolve()
        if target == protected_resolved or protected_resolved in target.parents:
            raise RuntimeError(f"Refusing to alter protected MT5 runtime root: {target}")
    if target == Path(target.anchor):
        raise RuntimeError(f"Refusing unsafe collector target root: {target}")


def _require_prepared_root(target_root: Path) -> None:
    for name in ("terminal64.exe", "MetaEditor64.exe"):
        path = target_root / name
        if not path.exists():
            raise FileNotFoundError(f"Collector runtime is not prepared: {path}")


def _prepare_portable_root(source_root: Path, target_root: Path) -> list[str]:
    _require_source_root(source_root)
    target_root.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in ("terminal64.exe", "MetaEditor64.exe", "metatester64.exe", "Terminal.ico", "origin.txt"):
        source = source_root / name
        if source.exists():
            copied.append(_copy_one(source, target_root / name))

    source_config = source_root / "Config"
    target_config = target_root / "Config"
    target_config.mkdir(parents=True, exist_ok=True)
    allowed_config_names = {
        "accounts.dat",
        "servers.dat",
        "common.ini",
        "terminal.ini",
        "settings.ini",
        "agents.dat",
        "dnsperf.dat",
        "hotkeys.ini",
    }
    for item in source_config.iterdir():
        if item.is_file() and item.name in allowed_config_names:
            copied.append(_copy_one(item, target_config / item.name))

    for relative in (
        Path("MQL5/Experts"),
        Path("MQL5/Files"),
        Path("MQL5/Logs"),
        Path("MQL5/Presets"),
        Path("MQL5/Profiles/Charts"),
        Path("logs"),
    ):
        (target_root / relative).mkdir(parents=True, exist_ok=True)
    return copied


def _require_source_root(source_root: Path) -> None:
    for name in ("terminal64.exe", "MetaEditor64.exe", "Config"):
        path = source_root / name
        if not path.exists():
            raise FileNotFoundError(f"Credential source terminal is incomplete: {path}")


def _copy_one(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return str(destination)


def _deploy_sources(phase1_root: Path, target_root: Path) -> list[str]:
    deployed: list[str] = []
    for relative in (EA_SOURCE, PRESET_SOURCE):
        source = phase1_root / relative
        if not source.exists():
            raise FileNotFoundError(source)
        if relative == EA_SOURCE:
            destination = target_root / "MQL5" / "Experts" / source.name
        else:
            destination = target_root / "MQL5" / "Presets" / source.name
        deployed.append(_copy_one(source, destination))
    return deployed


def _archive_existing_logs(target_root: Path) -> Path | None:
    files_dir = target_root / "MQL5" / "Files"
    if not files_dir.exists():
        return None
    existing = sorted(files_dir.glob("xau_prospective_*.csv"))
    if not existing:
        return None
    _assert_within(files_dir, target_root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    backup = target_root / "_codex_quarantine" / "telemetry_logs" / stamp
    backup.mkdir(parents=True, exist_ok=False)
    _assert_within(backup, target_root)
    for path in existing:
        _assert_within(path, target_root)
        shutil.move(str(path), str(backup / path.name))
    return backup


def _compile_ea(target_root: Path) -> Path:
    source = target_root / "MQL5" / "Experts" / f"{EA_NAME}.mq5"
    binary = source.with_suffix(".ex5")
    log = target_root / "MQL5" / "Logs" / f"compile_{EA_NAME}.log"
    if binary.exists():
        binary.unlink()
    if log.exists():
        log.unlink()
    completed = subprocess.run(
        [
            str(target_root / "MetaEditor64.exe"),
            "/portable",
            f"/compile:{source}",
            f"/log:{log}",
        ],
        check=False,
        timeout=90,
    )
    text = _read_text(log)
    if completed.returncode not in (0, 1) or not binary.exists():
        raise RuntimeError(f"Collector compile did not produce {binary}. Log:\n{text}")
    if "0 errors" not in text.lower() and "0 error(s)" not in text.lower():
        raise RuntimeError(f"Collector compile did not report zero errors. Log:\n{text}")
    return log


def _install_single_collector_profile(phase1_root: Path, target_root: Path) -> Path | None:
    charts_root = target_root / "MQL5" / "Profiles" / "Charts"
    default_profile = charts_root / "Default"
    backup: Path | None = None
    if default_profile.exists():
        _assert_within(default_profile, target_root)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        backup = target_root / "_codex_quarantine" / "profile_backups" / f"Default_{stamp}"
        backup.parent.mkdir(parents=True, exist_ok=True)
        _assert_within(backup, target_root)
        shutil.move(str(default_profile), str(backup))
    default_profile.mkdir(parents=True, exist_ok=True)
    (default_profile / "chart01.chr").write_text(_render_chart(phase1_root), encoding="utf-8")
    return backup


def _assert_within(path: Path, root: Path) -> None:
    resolved = path.resolve()
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise RuntimeError(f"Path escapes dedicated collector root: {resolved}")


def _render_chart(phase1_root: Path) -> str:
    preset_inputs = [
        line.strip()
        for line in (phase1_root / PRESET_SOURCE).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith(";")
    ]
    return "\n".join(
        [
            "<chart>",
            f"id={int(time.time())}0001",
            "symbol=XAUUSD",
            "description=XAUUSD",
            "period_type=0",
            "period_size=5",
            "digits=2",
            "tick_size=0.01",
            "scale_fix=0",
            "scale=3",
            "mode=1",
            "fore=0",
            "grid=0",
            "volume=0",
            "scroll=1",
            "shift=1",
            "ohlc=0",
            "one_click=0",
            "one_click_btn=0",
            "askline=1",
            "windows_total=1",
            "",
            "<expert>",
            f"name={EA_NAME}",
            f"path=Experts\\{EA_NAME}.ex5",
            "expertmode=0",
            "<inputs>",
            *preset_inputs,
            "</inputs>",
            "</expert>",
            "",
            "<window>",
            "height=100.000000",
            "objects=0",
            "<indicator>",
            "name=Main",
            "path=",
            "apply=1",
            "</indicator>",
            "</window>",
            "</chart>",
            "",
        ]
    )


def _write_startup_config(target_root: Path, login: str, server: str) -> Path:
    path = target_root / "Config" / "xau_prospective_collector_startup.ini"
    lines = ["[Common]"]
    if login:
        lines.append(f"Login={login}")
    if server:
        lines.append(f"Server={server}")
    lines.extend(
        [
            "ProxyEnable=0",
            "NewsEnable=0",
            "",
            "[Charts]",
            "MaxBars=999999999",
            "",
            "[Experts]",
            "AllowLiveTrading=0",
            "AllowDllImport=0",
            "Enabled=1",
            "Account=0",
            "Profile=0",
            "",
            "[StartUp]",
            "Symbol=XAUUSD",
            "Period=M5",
            "ShutdownTerminal=0",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _close_target_terminal(target_root: Path) -> bool:
    terminal = (target_root / "terminal64.exe").resolve()
    if not terminal.exists():
        return False
    command = (
        "$target=(Resolve-Path -LiteralPath '" + str(terminal).replace("'", "''") + "').Path;"
        "$items=Get-CimInstance Win32_Process -Filter \"Name='terminal64.exe'\" | "
        "Where-Object {$_.ExecutablePath -eq $target};"
        "if(-not $items){exit 3};"
        "foreach($item in $items){$p=Get-Process -Id $item.ProcessId -ErrorAction SilentlyContinue;"
        "if($p){[void]$p.CloseMainWindow()}};"
        "Start-Sleep -Seconds 5;"
        "foreach($item in $items){$p=Get-Process -Id $item.ProcessId -ErrorAction SilentlyContinue;"
        "if($p){Stop-Process -Id $item.ProcessId -Force}};exit 0"
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        check=False,
        text=True,
        capture_output=True,
        timeout=30,
    )
    return completed.returncode == 0


def _wait_for_collection(target_root: Path, wait_seconds: int) -> None:
    if wait_seconds <= 0:
        return
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        health = inspect_collection_health(target_root)
        if health["startup_active"] and health["heartbeat_rows"] > 0 and health["tick_rows"] > 0:
            return
        time.sleep(1.0)


def inspect_collection_health(target_root: Path) -> dict[str, Any]:
    files_dir = target_root / "MQL5" / "Files"
    startup_files = sorted(files_dir.glob("xau_prospective_*_startup.csv")) if files_dir.exists() else []
    tick_files = sorted(files_dir.glob("xau_prospective_*_ticks_*.csv")) if files_dir.exists() else []
    book_files = sorted(files_dir.glob("xau_prospective_*_book_*.csv")) if files_dir.exists() else []
    transaction_files = sorted(files_dir.glob("xau_prospective_*_transactions_*.csv")) if files_dir.exists() else []
    heartbeat_files = sorted(files_dir.glob("xau_prospective_*_heartbeat_*.csv")) if files_dir.exists() else []

    latest_startup = _latest_csv_row(startup_files[-1]) if startup_files else {}
    latest_heartbeat = _latest_csv_row(heartbeat_files[-1]) if heartbeat_files else {}
    tick_rows = sum(_data_row_count(path) for path in tick_files)
    book_rows = sum(_data_row_count(path) for path in book_files)
    transaction_rows = sum(_data_row_count(path) for path in transaction_files)
    heartbeat_rows = sum(_data_row_count(path) for path in heartbeat_files)
    book_types = sorted(_unique_csv_values(book_files, "book_type"))
    has_real_depth = any(value and value != "EMPTY" for value in book_types)
    startup_active = latest_startup.get("status") == "ACTIVE"
    book_subscribed = latest_startup.get("book_subscribed") == "true"

    if startup_active and heartbeat_rows > 0 and tick_rows > 0 and has_real_depth:
        status = "ACTIVE_TICKS_AND_DEPTH"
    elif startup_active and heartbeat_rows > 0 and tick_rows > 0 and book_subscribed:
        status = "ACTIVE_TICKS_DEPTH_EMPTY"
    elif startup_active and heartbeat_rows > 0 and tick_rows > 0:
        status = "ACTIVE_TICKS_DEPTH_UNAVAILABLE"
    elif startup_active and heartbeat_rows > 0:
        status = "ACTIVE_WAITING_FOR_TICKS"
    elif startup_files:
        status = "STARTUP_NOT_ACTIVE"
    else:
        status = "NOT_RUNNING"

    return {
        "status": status,
        "files_dir": str(files_dir),
        "startup_active": startup_active,
        "account_login": latest_startup.get("account_login", "unknown"),
        "account_server": latest_startup.get("account_server", "unknown"),
        "book_subscribed": book_subscribed,
        "book_subscription_error": latest_startup.get("book_subscription_error", "unknown"),
        "book_types": book_types,
        "real_depth_observed": has_real_depth,
        "startup_files": [str(path) for path in startup_files],
        "tick_files": [str(path) for path in tick_files],
        "book_files": [str(path) for path in book_files],
        "transaction_files": [str(path) for path in transaction_files],
        "heartbeat_files": [str(path) for path in heartbeat_files],
        "tick_rows": tick_rows,
        "book_rows": book_rows,
        "transaction_rows": transaction_rows,
        "heartbeat_rows": heartbeat_rows,
        "latest_startup": latest_startup,
        "latest_heartbeat": latest_heartbeat,
    }


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    payload = path.read_bytes()
    if payload.startswith((b"\xff\xfe", b"\xfe\xff")):
        return payload.decode("utf-16")
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return payload.decode(encoding)
        except UnicodeError:
            continue
    return payload.decode("utf-8", errors="replace")


def _latest_csv_row(path: Path) -> dict[str, str]:
    rows = list(csv.DictReader(_read_text(path).splitlines()))
    return rows[-1] if rows else {}


def _data_row_count(path: Path) -> int:
    lines = [line for line in _read_text(path).splitlines() if line.strip()]
    return max(0, len(lines) - 1)


def _unique_csv_values(paths: list[Path], column: str) -> set[str]:
    values: set[str] = set()
    for path in paths:
        for row in csv.DictReader(_read_text(path).splitlines()):
            values.add(row.get(column, ""))
    return values


def _render_markdown(payload: dict[str, Any]) -> str:
    health = payload["health"]
    return "\n".join(
        [
            "# XAU Prospective Telemetry Collector",
            "",
            f"Status: `{payload['status']}`",
            "",
            "This runtime is telemetry-only. Trading, Python execution, paid data, and provider-ID creation are not authorized.",
            "",
            f"- Account: `{health['account_login']}`",
            f"- Server: `{health['account_server']}`",
            f"- Tick rows: `{health['tick_rows']}`",
            f"- Heartbeat rows: `{health['heartbeat_rows']}`",
            f"- Transaction rows: `{health['transaction_rows']}`",
            f"- Depth subscribed: `{health['book_subscribed']}`",
            f"- Real depth observed: `{health['real_depth_observed']}`",
            f"- Depth row types: `{', '.join(health['book_types']) or 'none'}`",
            f"- Runtime files: `{health['files_dir']}`",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy a passive XAUUSD prospective telemetry collector.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-terminal-root", type=Path, default=DEFAULT_SOURCE_TERMINAL_ROOT)
    parser.add_argument("--target-root", type=Path, default=DEFAULT_TARGET_ROOT)
    parser.add_argument("--allow-prepare", action="store_true")
    parser.add_argument("--allow-deploy", action="store_true")
    parser.add_argument("--allow-launch", action="store_true")
    parser.add_argument("--startup-login", default="")
    parser.add_argument("--startup-server", default="")
    parser.add_argument("--wait-seconds", type=int, default=45)
    args = parser.parse_args()

    report = deploy_collector(
        phase1_root=args.phase1_root,
        source_terminal_root=args.source_terminal_root,
        target_root=args.target_root,
        prepare=args.allow_prepare,
        deploy=args.allow_deploy,
        launch=args.allow_launch,
        startup_login=args.startup_login,
        startup_server=args.startup_server,
        wait_seconds=args.wait_seconds,
    )
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
