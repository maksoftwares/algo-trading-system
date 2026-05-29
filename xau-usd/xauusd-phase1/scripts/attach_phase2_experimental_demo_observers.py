from __future__ import annotations

import argparse
import csv
import json
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
DEFAULT_METAEDITOR_EXE = Path("C:/Program Files/MetaTrader 5/MetaEditor64.exe")
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "PHASE2_EXPERIMENTAL_DEMO_ATTACHMENTS.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "PHASE2_EXPERIMENTAL_DEMO_ATTACHMENTS.md"
TERMINAL_READY_REPORT = Path("outputs") / "reports" / "PHASE2_EXPERIMENTAL_DEMO_TERMINAL.json"
EA_NAME = "Phase2ExperimentalDemoObserver"
EA_SOURCE = Path("mt5") / "Experts" / f"{EA_NAME}.mq5"
RUN_ID = "phase2-experimental-demo-attach-v0.1"
ACCEPTED_CANDIDATES = (
    "breakout_retest",
    "swing_breakout_retest_v0",
    "symbol_normalized_round_retest_v0",
)
PROVISIONAL_CANDIDATES = (
    "round_number_retest_v0",
    "session_extreme_retest_v0",
)
PRIMARY_SYMBOL = "XAUUSD"
MULTISYMBOL_DIR = Path("..") / "xauusd-phase0" / "outputs" / "multisymbol_results"


@dataclass(frozen=True)
class AttachmentRow:
    candidate: str
    status: str
    symbol: str
    qualification_source: str
    observer_supported: bool


@dataclass(frozen=True)
class AttachOutput:
    status: str
    json_path: Path
    markdown_path: Path
    attachment_count: int


def build_attachment_plan(phase1_root: Path) -> list[AttachmentRow]:
    rows: list[AttachmentRow] = []
    for candidate in [*ACCEPTED_CANDIDATES, *PROVISIONAL_CANDIDATES]:
        status = "ACCEPTED" if candidate in ACCEPTED_CANDIDATES else "PROVISIONAL"
        qualified = {PRIMARY_SYMBOL: "primary_xau_matrix_or_candidate_status"}
        summary = phase1_root / MULTISYMBOL_DIR / f"{candidate}_multisymbol_summary.csv"
        if summary.exists():
            with summary.open("r", encoding="utf-8", newline="") as handle:
                for item in csv.DictReader(handle):
                    symbol = (item.get("symbol") or "").strip()
                    verdict = (item.get("verdict") or "").strip().upper()
                    if symbol and verdict == "PASS":
                        qualified[symbol] = f"{summary.name}:PASS"
        for symbol in sorted(qualified):
            rows.append(
                AttachmentRow(
                    candidate=candidate,
                    status=status,
                    symbol=symbol,
                    qualification_source=qualified[symbol],
                    observer_supported=True,
                )
            )
    return rows


def attach_phase2_experimental_demo_observers(
    phase1_root: Path,
    terminal_data_dir: Path = DEFAULT_TERMINAL_DATA_DIR,
    terminal_exe: Path = DEFAULT_TERMINAL_EXE,
    metaeditor_exe: Path = DEFAULT_METAEDITOR_EXE,
    output_json: Path | None = None,
    launch: bool = True,
) -> AttachOutput:
    phase1_root = phase1_root.resolve()
    terminal_data_dir = terminal_data_dir.resolve()
    terminal_exe = terminal_exe.resolve()
    metaeditor_exe = metaeditor_exe.resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    ready_report = _read_json(phase1_root / TERMINAL_READY_REPORT)
    if ready_report.get("status") not in {
        "DEMO_TERMINAL_VERIFIED_READY_FOR_SAFE_SETUP",
        "DEMO_TERMINAL_VERIFIED_EXPERIMENTAL_OBSERVERS_ATTACHED",
    }:
        raise RuntimeError("Experimental demo terminal report is not ready for safe setup.")

    attachments = build_attachment_plan(phase1_root)
    if not attachments:
        raise RuntimeError("No qualified demo attachments were found.")

    deployed_sources = _deploy_sources(phase1_root, terminal_data_dir)
    compile_log = _compile_ea(metaeditor_exe, terminal_data_dir)
    terminal_closed = _close_terminal(terminal_exe)
    observer_log_backup_dir = _archive_existing_observer_logs(terminal_data_dir)
    backup_dir = _replace_default_profile(terminal_data_dir, attachments)
    if launch:
        subprocess.Popen([str(terminal_exe)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3.0)

    payload: dict[str, Any] = {
        "status": "ATTACHED_TO_DEMO_TERMINAL",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Experimental demo observer setup only. Attachments log telemetry and explicitly set "
            "broker_action_allowed=false; this does not mark canonical Phase 2 as passed."
        ),
        "run_id": RUN_ID,
        "terminal": {
            "terminal_exe": str(terminal_exe),
            "terminal_data_dir": str(terminal_data_dir),
            "profile": "Default",
            "profile_backup_dir": str(backup_dir),
            "observer_log_backup_dir": str(observer_log_backup_dir) if observer_log_backup_dir else "none",
            "terminal_closed_before_profile_replace": terminal_closed,
            "terminal_relaunched": launch,
        },
        "ea": {
            "name": EA_NAME,
            "deployed_sources": [str(path) for path in deployed_sources],
            "compile_log": str(compile_log),
            "dry_run_only": True,
            "broker_action_allowed": False,
        },
        "attachment_count": len(attachments),
        "attachments": [_attachment_payload(row) for row in attachments],
        "observer_limitations": [
            "breakout_retest and swing_breakout_retest_v0 use the native Phase 1 breakout-retest observer.",
            "symbol_normalized_round_retest_v0, round_number_retest_v0, and session_extreme_retest_v0 now use experimental MQL dry-run observers for signal telemetry only.",
            "All observers remain dry-run and explicitly set broker_action_allowed=false.",
        ],
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return AttachOutput("ATTACHED_TO_DEMO_TERMINAL", output_json, output_md, len(attachments))


def _archive_existing_observer_logs(terminal_data_dir: Path) -> Path | None:
    files_dir = terminal_data_dir / "MQL5" / "Files"
    candidates = [
        *files_dir.glob("experimental_demo_attachment_log*.csv"),
        *files_dir.glob("experimental_demo_attachment_startup*.csv"),
    ]
    existing = [path for path in candidates if path.exists()]
    if not existing:
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = terminal_data_dir / "_codex_quarantine" / "observer_logs" / f"experimental_demo_logs_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for path in existing:
        shutil.move(str(path), str(backup_dir / path.name))
    return backup_dir


def _deploy_sources(phase1_root: Path, terminal_data_dir: Path) -> list[Path]:
    mql5_root = terminal_data_dir / "MQL5"
    experts_dir = mql5_root / "Experts"
    include_phase1_dir = mql5_root / "Include" / "Phase1"
    experts_dir.mkdir(parents=True, exist_ok=True)
    include_phase1_dir.mkdir(parents=True, exist_ok=True)

    deployed: list[Path] = []
    ea_source = phase1_root / EA_SOURCE
    ea_target = experts_dir / ea_source.name
    shutil.copy2(ea_source, ea_target)
    deployed.append(ea_target)
    for include_name in ("Phase1Types.mqh", "Phase1BreakoutRetest.mqh"):
        source = phase1_root / "mt5" / "Include" / "Phase1" / include_name
        target = include_phase1_dir / include_name
        shutil.copy2(source, target)
        deployed.append(target)
    return deployed


def _compile_ea(metaeditor_exe: Path, terminal_data_dir: Path) -> Path:
    if not metaeditor_exe.exists():
        raise FileNotFoundError(f"MetaEditor not found: {metaeditor_exe}")

    # MetaEditor CLI truncates /compile paths at spaces on this Windows setup.
    # Compile from a no-space scratch path, then copy the produced EX5 back.
    scratch_root = Path("C:/MT5CompileScratch")
    scratch_mql5 = scratch_root / "MQL5"
    scratch_experts = scratch_mql5 / "Experts"
    scratch_include = scratch_mql5 / "Include" / "Phase1"
    scratch_experts.mkdir(parents=True, exist_ok=True)
    scratch_include.mkdir(parents=True, exist_ok=True)

    source = terminal_data_dir / "MQL5" / "Experts" / f"{EA_NAME}.mq5"
    scratch_source = scratch_experts / source.name
    shutil.copy2(source, scratch_source)
    for include_name in ("Phase1Types.mqh", "Phase1BreakoutRetest.mqh"):
        shutil.copy2(terminal_data_dir / "MQL5" / "Include" / "Phase1" / include_name, scratch_include / include_name)

    scratch_log = scratch_root / f"compile_{EA_NAME}.log"
    if scratch_log.exists():
        scratch_log.unlink()
    command = [str(metaeditor_exe), f"/compile:{scratch_source}", f"/log:{scratch_log}"]
    subprocess.run(command, check=False, timeout=90)
    scratch_ex5 = scratch_experts / f"{EA_NAME}.ex5"
    target_ex5 = terminal_data_dir / "MQL5" / "Experts" / f"{EA_NAME}.ex5"
    if not scratch_ex5.exists():
        log_text = _read_text(scratch_log)
        raise RuntimeError(f"MetaEditor did not produce {EA_NAME}.ex5. Compile log:\n{log_text}")
    shutil.copy2(scratch_ex5, target_ex5)

    log_path = terminal_data_dir / "MQL5" / "Logs" / f"compile_{EA_NAME}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if scratch_log.exists():
        shutil.copy2(scratch_log, log_path)
    log_text = _read_text(scratch_log)
    if "error(s)" in log_text.lower() and "0 error(s)" not in log_text.lower():
        raise RuntimeError(f"MetaEditor compile reported errors:\n{log_text}")
    return log_path


def _close_terminal(terminal_exe: Path) -> bool:
    ps = f"""
$target = (Resolve-Path -LiteralPath '{terminal_exe}').Path
$procs = Get-CimInstance Win32_Process | Where-Object {{ $_.ExecutablePath -eq $target }}
if(-not $procs) {{ exit 0 }}
foreach($proc in $procs) {{
  $p = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
  if($p) {{ [void]$p.CloseMainWindow() }}
}}
Start-Sleep -Seconds 5
foreach($proc in $procs) {{
  $p = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
  if($p) {{ Stop-Process -Id $proc.ProcessId -Force }}
}}
exit 0
"""
    result = subprocess.run(["powershell", "-NoProfile", "-Command", ps], text=True, capture_output=True, timeout=30)
    return result.returncode == 0


def _replace_default_profile(terminal_data_dir: Path, attachments: list[AttachmentRow]) -> Path:
    charts_root = terminal_data_dir / "MQL5" / "Profiles" / "Charts"
    default_profile = charts_root / "Default"
    backup_root = terminal_data_dir / "_codex_quarantine" / "profile_backups"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / f"default_profile_before_demo_attach_{stamp}"
    backup_dir.parent.mkdir(parents=True, exist_ok=True)
    if default_profile.exists():
        shutil.copytree(default_profile, backup_dir)
        shutil.rmtree(default_profile)
    default_profile.mkdir(parents=True, exist_ok=True)

    for index, row in enumerate(attachments, start=1):
        chart = default_profile / f"chart{index:02d}.chr"
        chart.write_text(_render_chart(row, index), encoding="utf-8")
    return backup_dir


def _render_chart(row: AttachmentRow, index: int) -> str:
    left = 20 + ((index - 1) % 3) * 42
    top = 20 + ((index - 1) // 3) * 35
    right = left + 980
    bottom = top + 720
    digits, tick_size = _symbol_format(row.symbol)
    qualified_csv = ",".join(sorted({item.symbol for item in build_attachment_plan(Path(__file__).resolve().parents[1]) if item.candidate == row.candidate}))
    return "\n".join(
        [
            "<chart>",
            f"id={int(time.time())}{index:04d}",
            f"symbol={row.symbol}",
            f"description={row.symbol}",
            "period_type=0",
            "period_size=5",
            f"digits={digits}",
            f"tick_size={tick_size}",
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
            "askline=1",
            "days=0",
            f"window_left={left}",
            f"window_top={top}",
            f"window_right={right}",
            f"window_bottom={bottom}",
            "windows_total=1",
            "",
            "<expert>",
            f"name={EA_NAME}",
            f"path=Experts\\{EA_NAME}.ex5",
            "expertmode=1",
            "<inputs>",
            f"InpRunId={RUN_ID}",
            "InpDryRunOnly=true",
            f"InpCandidate={row.candidate}",
            f"InpCandidateStatus={row.status}",
            f"InpTargetSymbol={row.symbol}",
            f"InpQualifiedSymbolsCsv={qualified_csv}",
            "InpExpectedServerMarker=Demo",
            f"InpAttachmentLogFileName={_attachment_log_name(row)}",
            f"InpStartupLogFileName={_startup_log_name(row)}",
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


def _attachment_payload(row: AttachmentRow) -> dict[str, Any]:
    payload = row.__dict__.copy()
    payload["attachment_log_file"] = _attachment_log_name(row)
    payload["startup_log_file"] = _startup_log_name(row)
    return payload


def _attachment_log_name(row: AttachmentRow) -> str:
    return f"experimental_demo_attachment_log_{_instance_slug(row)}.csv"


def _startup_log_name(row: AttachmentRow) -> str:
    return f"experimental_demo_attachment_startup_{_instance_slug(row)}.csv"


def _instance_slug(row: AttachmentRow) -> str:
    raw = f"{row.candidate}_{row.symbol}".lower()
    return "".join(char if char.isalnum() or char == "_" else "_" for char in raw)


def _symbol_format(symbol: str) -> tuple[int, str]:
    if symbol == "XAUUSD":
        return 2, "0.01"
    if symbol == "USDJPY":
        return 3, "0.001"
    return 5, "0.00001"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-16", "utf-8", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeError:
            continue
    return path.read_text(errors="replace")


def _render_markdown(payload: dict[str, Any]) -> str:
    attachments = payload["attachments"]
    lines = [
        "# Phase 2 Experimental Demo Attachments",
        "",
        f"Status: {payload['status']}",
        "",
        payload["authority"],
        "",
        f"Run ID: `{payload['run_id']}`",
        f"Attachment count: {payload['attachment_count']}",
        f"Terminal: `{payload['terminal']['terminal_exe']}`",
        f"Data folder: `{payload['terminal']['terminal_data_dir']}`",
        f"Profile backup: `{payload['terminal']['profile_backup_dir']}`",
        f"Observer log backup: `{payload['terminal']['observer_log_backup_dir']}`",
        "",
        "| Candidate | Status | Symbol | Observer | Qualification |",
        "|---|---|---|---|---|",
    ]
    for item in attachments:
        lines.append(
            "| {candidate} | {status} | {symbol} | {observer} | {qualification} |".format(
                candidate=item["candidate"],
                status=item["status"],
                symbol=item["symbol"],
                observer="native_signal_logger" if item["observer_supported"] else "attached_stub_pending_mql_observer",
                qualification=item["qualification_source"],
            )
        )
    lines.extend(
        [
            "",
            "## Limitations",
            "",
        ]
    )
    for item in payload["observer_limitations"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Attach experimental demo observers to the standard MT5 demo terminal.")
    parser.add_argument("--phase1-root", type=Path, default=Path("."))
    parser.add_argument("--terminal-data-dir", type=Path, default=DEFAULT_TERMINAL_DATA_DIR)
    parser.add_argument("--terminal-exe", type=Path, default=DEFAULT_TERMINAL_EXE)
    parser.add_argument("--metaeditor-exe", type=Path, default=DEFAULT_METAEDITOR_EXE)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--no-launch", action="store_true")
    args = parser.parse_args()

    output = attach_phase2_experimental_demo_observers(
        phase1_root=args.phase1_root,
        terminal_data_dir=args.terminal_data_dir,
        terminal_exe=args.terminal_exe,
        metaeditor_exe=args.metaeditor_exe,
        output_json=args.output_json,
        launch=not args.no_launch,
    )
    print(f"{output.status}: {output.attachment_count} attachments")
    print(output.json_path)
    print(output.markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
