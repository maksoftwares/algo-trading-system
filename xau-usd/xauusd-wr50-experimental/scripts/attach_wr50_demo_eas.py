from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TERMINAL_DATA_DIR = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
)
DEFAULT_TERMINAL_EXE = Path("C:/Program Files/MetaTrader 5/terminal64.exe")
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "WR50_DEMO_ATTACHMENTS_2026_06_05.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "WR50_DEMO_ATTACHMENTS_2026_06_05.md"
DEMO_ACCOUNT = "1025742"
DEMO_SERVER = "Capital.ComMena-Demo"
SYMBOL = "XAUUSD"
RUN_ID = "R260605A"


@dataclass(frozen=True)
class EaSpec:
    chart_label: str
    ea_name: str
    preset_name: str
    magic: int
    short_code: str


EA_SPECS = (
    EaSpec("WR50 BEV0", "WR50_BreakoutEvening_v0", "WR50_BEV0_DEMO_1025742.set", 930000, "BEV0"),
    EaSpec("WR50 BQV0", "WR50_BreakoutQuality_v0", "WR50_BQV0_DEMO_1025742.set", 930100, "BQV0"),
    EaSpec("WR50 E1R0", "WR50_BreakoutExit1R_v0", "WR50_E1R0_DEMO_1025742.set", 930200, "E1R0"),
)


def attach_wr50_demo_eas(
    wr50_root: Path,
    terminal_data_dir: Path = DEFAULT_TERMINAL_DATA_DIR,
    terminal_exe: Path = DEFAULT_TERMINAL_EXE,
    output_json: Path | None = None,
    launch: bool = False,
) -> dict[str, Any]:
    wr50_root = wr50_root.resolve()
    terminal_data_dir = terminal_data_dir.resolve()
    terminal_exe = terminal_exe.resolve()
    output_json = (output_json or wr50_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else wr50_root / DEFAULT_OUTPUT_MD

    profile_dir = terminal_data_dir / "MQL5" / "Profiles" / "Charts" / "Default"
    if not profile_dir.exists():
        raise FileNotFoundError(f"MT5 default chart profile not found: {profile_dir}")

    _assert_deployed_files(terminal_data_dir)
    presets = {spec.ea_name: _read_preset(wr50_root / "mt5" / "Presets" / spec.preset_name) for spec in EA_SPECS}

    backup_dir = _backup_profile(profile_dir, terminal_data_dir)
    existing_wr50 = _find_existing_wr50_charts(profile_dir)
    next_index = _next_chart_index(profile_dir)

    attachments: list[dict[str, Any]] = []
    for offset, spec in enumerate(EA_SPECS):
        chart_path = existing_wr50.get(spec.ea_name)
        action = "updated_existing_wr50_chart"
        if chart_path is None:
            chart_path = profile_dir / f"chart{next_index + offset:02d}.chr"
            action = "appended_new_chart"
        chart_path.write_text(_render_chart(spec, presets[spec.ea_name], next_index + offset), encoding="utf-8")
        attachments.append(
            {
                "action": action,
                "chart_file": str(chart_path),
                "symbol": SYMBOL,
                "period": "M5",
                "ea_name": spec.ea_name,
                "short_code": spec.short_code,
                "magic": spec.magic,
                "expert_path": f"Experts\\WR50\\{spec.ea_name}.ex5",
                "preset": str(wr50_root / "mt5" / "Presets" / spec.preset_name),
                "run_id": RUN_ID,
            }
        )

    launched = False
    if launch:
        subprocess.Popen([str(terminal_exe)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        launched = True
        time.sleep(3.0)

    payload: dict[str, Any] = {
        "status": "WR50_DEMO_CHARTS_ASSIGNED",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "WR50 experimental demo assignment only. The EAs are allowlisted for demo account "
            f"{DEMO_ACCOUNT} on {DEMO_SERVER}; live trading remains unauthorized."
        ),
        "terminal": {
            "terminal_exe": str(terminal_exe),
            "terminal_data_dir": str(terminal_data_dir),
            "profile": "Default",
            "profile_backup_dir": str(backup_dir),
            "terminal_relaunched": launched,
        },
        "demo_account": {
            "login": DEMO_ACCOUNT,
            "server": DEMO_SERVER,
            "symbol": SYMBOL,
        },
        "risk_controls": {
            "fixed_lot": 0.01,
            "demo_only": True,
            "owner_authorization_token": "WR50_DEMO_1025742_20260605",
            "max_trades_per_day_per_ea": 5,
            "max_open_positions_per_ea": 1,
            "max_open_wr50_positions_total": 3,
            "max_daily_loss_account_currency": 100.0,
            "live_authorized": False,
            "canonical_phase2_authorized": False,
        },
        "attachments": attachments,
        "runtime_logs": {
            "startup": str(terminal_data_dir / "MQL5" / "Files" / "WR50" / "wr50_startup_log.csv"),
            "block": str(terminal_data_dir / "MQL5" / "Files" / "WR50" / "wr50_block_log.csv"),
            "signal": str(terminal_data_dir / "MQL5" / "Files" / "WR50" / "wr50_signal_log.csv"),
            "order": str(terminal_data_dir / "MQL5" / "Files" / "WR50" / "wr50_order_log.csv"),
            "ledger": str(terminal_data_dir / "MQL5" / "Files" / "WR50" / "wr50_trade_ledger.csv"),
            "error": str(terminal_data_dir / "MQL5" / "Files" / "WR50" / "wr50_error_log.csv"),
        },
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return payload


def _assert_deployed_files(terminal_data_dir: Path) -> None:
    missing: list[str] = []
    for spec in EA_SPECS:
        ex5 = terminal_data_dir / "MQL5" / "Experts" / "WR50" / f"{spec.ea_name}.ex5"
        if not ex5.exists():
            missing.append(str(ex5))
    for file_name in ("wr50_runtime_registry.csv", "wr50_account_allowlist.csv", "wr50_blackout_windows.csv"):
        path = terminal_data_dir / "MQL5" / "Files" / "WR50" / file_name
        if not path.exists():
            missing.append(str(path))
    if missing:
        raise FileNotFoundError("Required WR50 deployment files are missing:\n" + "\n".join(missing))


def _read_preset(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Preset not found: {path}")
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line and not line.startswith(";")]


def _backup_profile(profile_dir: Path, terminal_data_dir: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = (
        terminal_data_dir
        / "_codex_quarantine"
        / "profile_backups"
        / f"default_profile_before_wr50_attach_{stamp}"
    )
    shutil.copytree(profile_dir, backup_dir)
    return backup_dir


def _find_existing_wr50_charts(profile_dir: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for chart in profile_dir.glob("chart*.chr"):
        text = chart.read_text(encoding="utf-8", errors="replace")
        for spec in EA_SPECS:
            if f"path=Experts\\WR50\\{spec.ea_name}.ex5" in text:
                found[spec.ea_name] = chart
    return found


def _next_chart_index(profile_dir: Path) -> int:
    indexes: list[int] = []
    for chart in profile_dir.glob("chart*.chr"):
        match = re.fullmatch(r"chart(\d+)\.chr", chart.name)
        if match:
            indexes.append(int(match.group(1)))
    return max(indexes, default=0) + 1


def _render_chart(spec: EaSpec, preset_lines: list[str], index: int) -> str:
    left = 20 + ((index - 1) % 3) * 42
    top = 20 + ((index - 1) // 3) * 35
    right = left + 980
    bottom = top + 720
    chart_id = f"{int(time.time())}{index:04d}"
    lines = [
        "<chart>",
        f"id={chart_id}",
        f"symbol={SYMBOL}",
        "description=Gold",
        "period_type=0",
        "period_size=5",
        "digits=2",
        "tick_size=0.010000",
        "scale_fix=0",
        "scale_fixed_min=0.000000",
        "scale_fixed_max=0.000000",
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
        "bidline=1",
        "askline=1",
        "days=0",
        "descriptions=0",
        "tradelines=1",
        "tradehistory=1",
        f"window_left={left}",
        f"window_top={top}",
        f"window_right={right}",
        f"window_bottom={bottom}",
        "windows_total=1",
        "",
        "<expert>",
        f"name={spec.ea_name}",
        f"path=Experts\\WR50\\{spec.ea_name}.ex5",
        "expertmode=1",
        "<inputs>",
        *preset_lines,
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
        "expertmode=0",
        "</indicator>",
        "</window>",
        "</chart>",
        "",
    ]
    return "\n".join(lines)


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# WR50 Demo Attachments",
        "",
        f"Status: {payload['status']}",
        "",
        payload["authority"],
        "",
        f"Terminal: `{payload['terminal']['terminal_exe']}`",
        f"Data folder: `{payload['terminal']['terminal_data_dir']}`",
        f"Profile backup: `{payload['terminal']['profile_backup_dir']}`",
        f"Terminal relaunched: `{payload['terminal']['terminal_relaunched']}`",
        "",
        "| EA | Short code | Magic | Symbol | Period | Action | Chart file |",
        "|---|---:|---:|---|---|---|---|",
    ]
    for item in payload["attachments"]:
        lines.append(
            "| {ea_name} | {short_code} | {magic} | {symbol} | {period} | {action} | `{chart_file}` |".format(
                **item
            )
        )
    lines.extend(
        [
            "",
            "## Runtime Logs",
            "",
        ]
    )
    for label, path in payload["runtime_logs"].items():
        lines.append(f"- {label}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Append WR50 demo EA charts to the standard MT5 Default profile.")
    parser.add_argument("--wr50-root", type=Path, default=Path("."))
    parser.add_argument("--terminal-data-dir", type=Path, default=DEFAULT_TERMINAL_DATA_DIR)
    parser.add_argument("--terminal-exe", type=Path, default=DEFAULT_TERMINAL_EXE)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--launch", action="store_true")
    args = parser.parse_args()

    payload = attach_wr50_demo_eas(
        wr50_root=args.wr50_root,
        terminal_data_dir=args.terminal_data_dir,
        terminal_exe=args.terminal_exe,
        output_json=args.output_json,
        launch=args.launch,
    )
    print(f"{payload['status']}: {len(payload['attachments'])} attachments")
    print(payload["terminal"]["profile_backup_dir"])
    for item in payload["attachments"]:
        print(f"{item['action']}: {item['chart_file']} -> {item['ea_name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
