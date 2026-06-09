from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TERMINAL_DATA_DIR = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
)
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "WR50_WIDESTOP_DEMO_ATTACHMENTS_2026_06_09.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "WR50_WIDESTOP_DEMO_ATTACHMENTS_2026_06_09.md"
DEFAULT_COMPILED_EX5 = Path("C:/MT5CompileScratch/WR50_WIDESTOP_20260609/MQL5/Experts/WR50/WR50_BreakoutWideStop_v0.ex5")
DEMO_ACCOUNT = "1025742"
DEMO_SERVER = "Capital.ComMena-Demo"
SYMBOL = "XAUUSD"
OWNER_TOKEN = "WR50_DEMO_1025742_20260609_WIDESTOP"


@dataclass(frozen=True)
class WideStopSpec:
    ea_id: str
    short_code: str
    magic: int
    magic_start: int
    magic_end: int
    target_r: str
    run_id: str
    safe_preset_name: str


SPECS = (
    WideStopSpec("wr50_wst12", "WST12", 930300, 930300, 930399, "1.20", "R260609W12", "WR50_WST12_SAFE_REVIEW_ONLY.set"),
    WideStopSpec("wr50_wst15", "WST15", 930400, 930400, 930499, "1.50", "R260609W15", "WR50_WST15_SAFE_REVIEW_ONLY.set"),
)


def attach_widestop_demo_eas(
    wr50_root: Path,
    terminal_data_dir: Path = DEFAULT_TERMINAL_DATA_DIR,
    compiled_ex5: Path = DEFAULT_COMPILED_EX5,
    output_json: Path | None = None,
) -> dict[str, Any]:
    wr50_root = wr50_root.resolve()
    terminal_data_dir = terminal_data_dir.resolve()
    compiled_ex5 = compiled_ex5.resolve()
    output_json = (output_json or wr50_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else wr50_root / DEFAULT_OUTPUT_MD

    profile_dir = terminal_data_dir / "MQL5" / "Profiles" / "Charts" / "Default"
    if not profile_dir.exists():
        raise FileNotFoundError(f"MT5 default chart profile not found: {profile_dir}")

    deploy_info = _deploy_required_files(wr50_root, terminal_data_dir, compiled_ex5)
    local_presets = _make_owner_authorized_presets(wr50_root)
    backup_dir = _backup_profile(profile_dir, terminal_data_dir)

    existing = _find_existing_widestop_charts(profile_dir)
    next_index = _next_chart_index(profile_dir)
    attachments: list[dict[str, Any]] = []
    appended_count = 0
    for spec in SPECS:
        chart_path = existing.get(spec.magic)
        action = "updated_existing_widestop_chart"
        if chart_path is None:
            chart_path = profile_dir / f"chart{next_index + appended_count:02d}.chr"
            appended_count += 1
            action = "appended_new_chart"
        preset_lines = _read_preset(local_presets[spec.magic]["path"])
        chart_path.write_text(_render_chart(spec, preset_lines, _chart_index(chart_path)), encoding="utf-8")
        attachments.append(
            {
                "action": action,
                "chart_file": str(chart_path),
                "symbol": SYMBOL,
                "period": "M5",
                "ea_name": "WR50_BreakoutWideStop_v0",
                "ea_id": spec.ea_id,
                "short_code": spec.short_code,
                "magic": spec.magic,
                "target_r": spec.target_r,
                "expert_path": "Experts\\WR50\\WR50_BreakoutWideStop_v0.ex5",
                "local_preset_path": str(local_presets[spec.magic]["path"]),
                "local_preset_sha256": local_presets[spec.magic]["sha256"],
                "run_id": spec.run_id,
            }
        )

    payload: dict[str, Any] = {
        "status": "WR50_WIDESTOP_DEMO_CHARTS_ASSIGNED_RESTART_REQUIRED",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Owner authorized demo-only WideStop attachment for XAUUSD on account "
            f"{DEMO_ACCOUNT} / {DEMO_SERVER}. This does not authorize live trading or canonical Phase 2."
        ),
        "terminal": {
            "terminal_data_dir": str(terminal_data_dir),
            "profile": "Default",
            "profile_backup_dir": str(backup_dir),
        },
        "demo_account": {
            "login": DEMO_ACCOUNT,
            "server": DEMO_SERVER,
            "symbol": SYMBOL,
        },
        "risk_controls": {
            "fixed_lot": 0.01,
            "demo_only": True,
            "owner_authorization_token_sha256": _sha256_text(OWNER_TOKEN),
            "max_cost_r": 0.0,
            "max_spread_points": 0,
            "max_trades_per_day_per_ea": 0,
            "max_open_positions_per_ea": 0,
            "max_open_wr50_positions_total": 0,
            "live_authorized": False,
            "canonical_phase2_authorized": False,
        },
        "deployed_files": deploy_info,
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


def _deploy_required_files(wr50_root: Path, terminal_data_dir: Path, compiled_ex5: Path) -> list[dict[str, str]]:
    if not compiled_ex5.exists():
        raise FileNotFoundError(f"Compiled WideStop ex5 is missing: {compiled_ex5}")

    deployed: list[dict[str, str]] = []
    expert_dir = terminal_data_dir / "MQL5" / "Experts" / "WR50"
    files_dir = terminal_data_dir / "MQL5" / "Files" / "WR50"
    expert_dir.mkdir(parents=True, exist_ok=True)
    files_dir.mkdir(parents=True, exist_ok=True)

    copies = [
        (wr50_root / "mt5" / "Experts" / "WR50_BreakoutWideStop_v0.mq5", expert_dir / "WR50_BreakoutWideStop_v0.mq5"),
        (compiled_ex5, expert_dir / "WR50_BreakoutWideStop_v0.ex5"),
        (wr50_root / "config" / "wr50_runtime_registry.csv", files_dir / "wr50_runtime_registry.csv"),
        (wr50_root / "config" / "wr50_account_allowlist.csv", files_dir / "wr50_account_allowlist.csv"),
        (wr50_root / "config" / "wr50_blackout_windows.csv", files_dir / "wr50_blackout_windows.csv"),
    ]
    for source, dest in copies:
        if not source.exists():
            raise FileNotFoundError(f"Required source file is missing: {source}")
        shutil.copy2(source, dest)
        deployed.append({"source": str(source), "destination": str(dest), "sha256": _sha256_file(dest)})
    return deployed


def _make_owner_authorized_presets(wr50_root: Path) -> dict[int, dict[str, Any]]:
    local_dir = wr50_root / "local"
    local_dir.mkdir(parents=True, exist_ok=True)
    made: dict[int, dict[str, Any]] = {}
    for spec in SPECS:
        safe_path = wr50_root / "mt5" / "Presets" / spec.safe_preset_name
        lines = _read_preset(safe_path)
        replacements = {
            "InpAllowDemoTrading": "true",
            "InpOwnerAuthorizationToken": OWNER_TOKEN,
            "InpRequiredOwnerAuthorizationToken": OWNER_TOKEN,
            "InpFixedLot": "0.01",
            "InpAllowedSymbol": SYMBOL,
            "InpMagicNumber": str(spec.magic),
            "InpMagicStart": str(spec.magic_start),
            "InpMagicEnd": str(spec.magic_end),
            "InpTargetR": spec.target_r,
            "InpMaxCostR": "0.0",
            "InpMaxSpreadPoints": "0",
            "InpMaxTradesPerDay": "0",
            "InpMaxOpenPositionsForThisEA": "0",
            "InpMaxOpenWR50PositionsTotal": "0",
            "InpAllowSharedSymbolExposure": "true",
        }
        patched = [_patch_line(line, replacements) for line in lines]
        preset_path = local_dir / f"WR50_{spec.short_code}_OWNER_AUTHORIZED_DEMO_1025742.local.set"
        preset_path.write_text("\n".join(patched) + "\n", encoding="utf-8")
        made[spec.magic] = {"path": preset_path, "sha256": _sha256_file(preset_path)}
    return made


def _patch_line(line: str, replacements: dict[str, str]) -> str:
    if "=" not in line:
        return line
    key, _value = line.split("=", 1)
    if key in replacements:
        return f"{key}={replacements[key]}"
    return line


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
        / f"default_profile_before_wr50_widestop_attach_{stamp}"
    )
    shutil.copytree(profile_dir, backup_dir)
    return backup_dir


def _find_existing_widestop_charts(profile_dir: Path) -> dict[int, Path]:
    found: dict[int, Path] = {}
    for chart in profile_dir.glob("chart*.chr"):
        text = chart.read_text(encoding="utf-8", errors="replace")
        if "path=Experts\\WR50\\WR50_BreakoutWideStop_v0.ex5" not in text:
            continue
        for match in re.finditer(r"InpMagicNumber=(\d+)", text):
            found[int(match.group(1))] = chart
    return found


def _next_chart_index(profile_dir: Path) -> int:
    indexes: list[int] = []
    for chart in profile_dir.glob("chart*.chr"):
        match = re.fullmatch(r"chart(\d+)\.chr", chart.name)
        if match:
            indexes.append(int(match.group(1)))
    return max(indexes, default=0) + 1


def _chart_index(path: Path) -> int:
    match = re.fullmatch(r"chart(\d+)\.chr", path.name)
    return int(match.group(1)) if match else int(time.time()) % 100


def _render_chart(spec: WideStopSpec, preset_lines: list[str], index: int) -> str:
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
        "name=WR50_BreakoutWideStop_v0",
        "path=Experts\\WR50\\WR50_BreakoutWideStop_v0.ex5",
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
        "# WR50 WideStop Demo Attachments",
        "",
        f"Status: {payload['status']}",
        "",
        payload["authority"],
        "",
        f"Data folder: `{payload['terminal']['terminal_data_dir']}`",
        f"Profile backup: `{payload['terminal']['profile_backup_dir']}`",
        "",
        "| EA ID | Short code | Magic | Target R | Symbol | Period | Action | Chart file |",
        "|---|---:|---:|---:|---|---|---|---|",
    ]
    for item in payload["attachments"]:
        lines.append(
            "| {ea_id} | {short_code} | {magic} | {target_r} | {symbol} | {period} | {action} | `{chart_file}` |".format(
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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Append owner-authorized WR50 WideStop demo charts to MT5 profile.")
    parser.add_argument("--wr50-root", type=Path, default=Path("."))
    parser.add_argument("--terminal-data-dir", type=Path, default=DEFAULT_TERMINAL_DATA_DIR)
    parser.add_argument("--compiled-ex5", type=Path, default=DEFAULT_COMPILED_EX5)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args()

    payload = attach_widestop_demo_eas(
        wr50_root=args.wr50_root,
        terminal_data_dir=args.terminal_data_dir,
        compiled_ex5=args.compiled_ex5,
        output_json=args.output_json,
    )
    print(f"{payload['status']}: {len(payload['attachments'])} attachments")
    print(payload["terminal"]["profile_backup_dir"])
    for item in payload["attachments"]:
        print(f"{item['action']}: {item['chart_file']} -> {item['short_code']} magic={item['magic']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
