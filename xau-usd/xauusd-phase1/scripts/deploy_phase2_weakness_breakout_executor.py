from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TERMINAL_DATA_DIR = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
)
DEFAULT_METAEDITOR_EXE = Path("C:/Program Files/MetaTrader 5/MetaEditor64.exe")
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "P2WEAKNESS_BR_V1_DEPLOYMENT.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "P2WEAKNESS_BR_V1_DEPLOYMENT.md"
EA_NAME = "Phase2WeaknessBreakoutRetestExecutor"
EA_SOURCE = Path("mt5") / "Experts" / f"{EA_NAME}.mq5"
INCLUDE_NAMES = ("Phase1Types.mqh", "Phase1BreakoutRetest.mqh")
PRESET_NAME = "Phase2WeaknessBreakoutRetestExecutor.demo_xauusd.set"
OWNER_AUTHORIZED_TEMPLATE_NAME = "Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.template.set"
P2WEAKNESS_MAGIC = 931000


@dataclass(frozen=True)
class DeployOutput:
    status: str
    json_path: Path
    markdown_path: Path
    compile_log: Path
    deployed_ex5: Path


def deploy_phase2_weakness_breakout_executor(
    phase1_root: Path,
    terminal_data_dir: Path = DEFAULT_TERMINAL_DATA_DIR,
    metaeditor_exe: Path = DEFAULT_METAEDITOR_EXE,
    output_json: Path | None = None,
    allow_deploy: bool = False,
) -> DeployOutput:
    phase1_root = phase1_root.resolve()
    terminal_data_dir = terminal_data_dir.resolve()
    metaeditor_exe = metaeditor_exe.resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    deployed_sources: list[Path] = []
    compile_log = terminal_data_dir / "MQL5" / "Logs" / f"compile_{EA_NAME}.log"
    deployed_ex5 = terminal_data_dir / "MQL5" / "Experts" / f"{EA_NAME}.ex5"
    status = "REPORT_ONLY_NO_NEW_DEPLOYMENT"
    if allow_deploy:
        _require_deploy_preconditions(phase1_root)
        deployed_sources = _deploy_sources(phase1_root, terminal_data_dir)
        compile_log = _compile_ea(metaeditor_exe, terminal_data_dir)
        status = "PASS"
    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Experimental demo-only deployment boundary for P2WEAKNESS_BR_V1. Default mode is report-only: "
            "no copy, no compile, no chart attach, no profile replacement, no canonical Phase 2, no live trading."
        ),
        "ea": {
            "name": EA_NAME,
            "run_id": "P2WEAKNESS_BR_V1",
            "order_comment": "P2WEAKNESS_BR_V1",
            "magic_number": P2WEAKNESS_MAGIC,
            "symbol": "XAUUSD",
            "candidate": "breakout_retest",
            "deployed_sources": [str(path) for path in deployed_sources],
            "deployed_ex5": str(deployed_ex5),
            "compile_log": str(compile_log),
            "source_sha256": _sha256(phase1_root / EA_SOURCE),
            "safe_preset_sha256": _sha256(phase1_root / "mt5" / "Presets" / PRESET_NAME),
            "owner_authorized_template_sha256": _sha256(phase1_root / "mt5" / "Presets" / OWNER_AUTHORIZED_TEMPLATE_NAME),
        },
        "terminal": {
            "terminal_data_dir": str(terminal_data_dir),
            "metaeditor_exe": str(metaeditor_exe),
            "deployment_attempted": allow_deploy,
            "terminal_profile_touched": False,
            "terminal_closed_or_restarted": False,
        },
        "runtime_boundary": {
            "demo_only": True,
            "source_defaults_safe": True,
            "default_broker_action_allowed": False,
            "default_allowed_account_login": "",
            "expected_server_marker": "Demo",
            "live_or_real_server_refusal": True,
            "fixed_lot": 0.01,
            "duplicate_family_suppression": True,
            "known_demo_family_magic_ranges": "920000-920999,930000-930999,931000-931099",
            "owner_authorized_template": OWNER_AUTHORIZED_TEMPLATE_NAME,
        },
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return DeployOutput(status, output_json, output_md, compile_log, deployed_ex5)


def _require_deploy_preconditions(phase1_root: Path) -> None:
    checks = {
        "clean_clone_reconciliation": phase1_root / "outputs" / "reports" / "P2WEAKNESS_BR_V1_CLEAN_CLONE_RECONCILIATION.json",
        "source_governance_parity": phase1_root / "outputs" / "reports" / "P2WEAKNESS_BR_V1_SOURCE_GOVERNANCE_PARITY.json",
        "magic_collision_audit": phase1_root / "outputs" / "reports" / "P2WEAKNESS_BR_V1_MAGIC_COLLISION_AUDIT.json",
    }
    failures: list[str] = []
    for name, path in checks.items():
        status = _json_status(path)
        if status != "PASS":
            failures.append(f"{name}={status or 'MISSING'}")
    template = _read_text(phase1_root / "mt5" / "Presets" / OWNER_AUTHORIZED_TEMPLATE_NAME)
    if "InpDryRunOnly=true" not in template or "InpBrokerActionAllowed=false" not in template:
        failures.append("owner_authorized_template_not_non_executing")
    if (phase1_root / "mt5" / "Presets" / "Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.set").exists():
        failures.append("legacy_executing_owner_authorized_set_present")
    if failures:
        raise RuntimeError("P2WEAKNESS deploy preconditions failed: " + ", ".join(failures))


def _deploy_sources(phase1_root: Path, terminal_data_dir: Path) -> list[Path]:
    mql5_root = terminal_data_dir / "MQL5"
    experts_dir = mql5_root / "Experts"
    include_phase1_dir = mql5_root / "Include" / "Phase1"
    presets_dir = mql5_root / "Presets"
    experts_dir.mkdir(parents=True, exist_ok=True)
    include_phase1_dir.mkdir(parents=True, exist_ok=True)
    presets_dir.mkdir(parents=True, exist_ok=True)

    deployed: list[Path] = []
    source = phase1_root / EA_SOURCE
    target = experts_dir / source.name
    shutil.copy2(source, target)
    deployed.append(target)
    for include_name in INCLUDE_NAMES:
        include_source = phase1_root / "mt5" / "Include" / "Phase1" / include_name
        include_target = include_phase1_dir / include_name
        shutil.copy2(include_source, include_target)
        deployed.append(include_target)
    preset_source = phase1_root / "mt5" / "Presets" / PRESET_NAME
    preset_target = presets_dir / PRESET_NAME
    shutil.copy2(preset_source, preset_target)
    deployed.append(preset_target)
    return deployed


def _json_status(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "INVALID_JSON"
    return str(payload.get("status", ""))


def _compile_ea(metaeditor_exe: Path, terminal_data_dir: Path) -> Path:
    if not metaeditor_exe.exists():
        raise FileNotFoundError(f"MetaEditor not found: {metaeditor_exe}")

    scratch_root = Path("C:/MT5CompileScratch")
    scratch_mql5 = scratch_root / "MQL5"
    scratch_experts = scratch_mql5 / "Experts"
    scratch_include = scratch_mql5 / "Include" / "Phase1"
    scratch_experts.mkdir(parents=True, exist_ok=True)
    scratch_include.mkdir(parents=True, exist_ok=True)

    source = terminal_data_dir / "MQL5" / "Experts" / f"{EA_NAME}.mq5"
    scratch_source = scratch_experts / source.name
    shutil.copy2(source, scratch_source)
    for include_name in INCLUDE_NAMES:
        shutil.copy2(terminal_data_dir / "MQL5" / "Include" / "Phase1" / include_name, scratch_include / include_name)

    scratch_log = scratch_root / f"compile_{EA_NAME}.log"
    if scratch_log.exists():
        scratch_log.unlink()
    subprocess.run([str(metaeditor_exe), f"/compile:{scratch_source}", f"/log:{scratch_log}"], check=False, timeout=90)

    scratch_ex5 = scratch_experts / f"{EA_NAME}.ex5"
    target_ex5 = terminal_data_dir / "MQL5" / "Experts" / f"{EA_NAME}.ex5"
    if not scratch_ex5.exists():
        raise RuntimeError(f"MetaEditor did not produce {EA_NAME}.ex5. Compile log:\n{_read_text(scratch_log)}")
    shutil.copy2(scratch_ex5, target_ex5)

    log_path = terminal_data_dir / "MQL5" / "Logs" / f"compile_{EA_NAME}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if scratch_log.exists():
        shutil.copy2(scratch_log, log_path)
    log_text = _read_text(scratch_log)
    if "error(s)" in log_text.lower() and "0 error(s)" not in log_text.lower():
        raise RuntimeError(f"MetaEditor compile reported errors:\n{log_text}")
    return log_path


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-16", "utf-8", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeError:
            continue
    return path.read_text(errors="replace")


def _sha256(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render_markdown(payload: dict[str, Any]) -> str:
    ea = payload["ea"]
    terminal = payload["terminal"]
    boundary = payload["runtime_boundary"]
    lines = [
        "# Phase 2 Weakness Breakout-Retest V1 Deployment",
        "",
        f"Status: {payload['status']}",
        "",
        payload["authority"],
        "",
        "## EA Identity",
        "",
        f"- Name: `{ea['name']}`",
        f"- Run ID: `{ea['run_id']}`",
        f"- Order comment: `{ea['order_comment']}`",
        f"- Magic number: `{ea['magic_number']}`",
        f"- Candidate: `{ea['candidate']}`",
        f"- Symbol: `{ea['symbol']}`",
        f"- Source SHA256: `{ea['source_sha256']}`",
        f"- Safe preset SHA256: `{ea['safe_preset_sha256']}`",
        f"- Owner-authorized template SHA256: `{ea['owner_authorized_template_sha256']}`",
        "",
        "## Deployment",
        "",
        f"- Deployment attempted: `{terminal['deployment_attempted']}`",
        f"- Terminal data folder: `{terminal['terminal_data_dir']}`",
        f"- Deployed EX5: `{ea['deployed_ex5']}`",
        f"- Compile log: `{ea['compile_log']}`",
        f"- Terminal profile touched: `{terminal['terminal_profile_touched']}`",
        f"- Terminal closed/restarted: `{terminal['terminal_closed_or_restarted']}`",
        "",
        "## Runtime Boundary",
        "",
        f"- Demo only: `{boundary['demo_only']}`",
        f"- Source defaults safe: `{boundary['source_defaults_safe']}`",
        f"- Default broker action allowed: `{boundary['default_broker_action_allowed']}`",
        f"- Default allowed account login: `{boundary['default_allowed_account_login']}`",
        f"- Expected server marker: `{boundary['expected_server_marker']}`",
        f"- Refuses live/real server markers: `{boundary['live_or_real_server_refusal']}`",
        f"- Fixed lot: `{boundary['fixed_lot']}`",
        f"- Duplicate-family suppression: `{boundary['duplicate_family_suppression']}`",
        f"- Known demo family magic ranges: `{boundary['known_demo_family_magic_ranges']}`",
        f"- Owner-authorized template: `{boundary['owner_authorized_template']}`",
        "",
        "## Boundary",
        "",
        "Report-only mode does not prepare, copy, compile, attach, or modify MT5. `--allow-deploy` is required for copy/compile and still does not attach charts.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deploy and compile the P2WEAKNESS_BR_V1 demo executor without touching chart profiles.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--terminal-data-dir", type=Path, default=DEFAULT_TERMINAL_DATA_DIR)
    parser.add_argument("--metaeditor-exe", type=Path, default=DEFAULT_METAEDITOR_EXE)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--allow-deploy", action="store_true", help="Actually copy and compile after governance preconditions pass.")
    args = parser.parse_args(argv)

    output = deploy_phase2_weakness_breakout_executor(
        args.phase1_root,
        terminal_data_dir=args.terminal_data_dir,
        metaeditor_exe=args.metaeditor_exe,
        output_json=args.output_json,
        allow_deploy=args.allow_deploy,
    )
    print(f"Deployment: {output.status}")
    print(f"Markdown: {output.markdown_path}")
    print(f"Compile log: {output.compile_log}")
    print(f"EX5: {output.deployed_ex5}")
    return 0 if output.status in {"PASS", "REPORT_ONLY_NO_NEW_DEPLOYMENT"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
