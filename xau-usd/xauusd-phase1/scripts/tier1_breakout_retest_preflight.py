from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from tier1_breakout_retest_common import (
    DEFAULT_LOCAL_PRESET,
    DEFAULT_PORTABLE_ROOT,
    DERIVED_MAGIC,
    EA_NAME,
    EA_SOURCE_REL,
    OLD_DEMO_ACCOUNT,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_PENDING_MANUAL,
    STATUS_PENDING_OWNER,
    STATUS_PENDING_RUNTIME,
    TIER1_PRESET_VALUES,
    boundary_lines,
    check,
    checks_table,
    compile_log_passed,
    demo_marker,
    mask_account,
    now_utc,
    overall_status,
    parse_mq5_inputs,
    parse_set_file,
    read_text_any_encoding,
    report_header,
    reports_dir,
    write_report_pair,
)


DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "TIER1_BREAKOUT_RETEST_PREFLIGHT_REPORT.json"


def generate_tier1_preflight(
    root: Path,
    local_preset: Path | None = None,
    portable_root: Path = DEFAULT_PORTABLE_ROOT,
    source_terminal_root: Path | None = None,
    output_json: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    local_preset = (local_preset or root / DEFAULT_LOCAL_PRESET).resolve()
    portable_root = portable_root.resolve()
    output_json = (output_json or root / DEFAULT_OUTPUT_JSON).resolve()
    preset = parse_set_file(local_preset)
    source_inputs = parse_mq5_inputs(root / EA_SOURCE_REL)
    compile_log = portable_root / "MQL5" / "Logs" / f"compile_{EA_NAME}.log"
    login = preset.get("InpAllowedAccountLoginsCsv", "")

    checks = [
        check("local_owner_preset_present", STATUS_PASS if local_preset.exists() else STATUS_PENDING_OWNER, str(local_preset)),
        check("local_owner_preset_not_under_mt5_presets", STATUS_PASS if "local" in [part.lower() for part in local_preset.parts] else STATUS_FAIL, str(local_preset)),
        check("gitignore_covers_phase1_local", _gitignore_check(root), "xau-usd/xauusd-phase1/local/ must remain ignored."),
        check("source_input_names_loaded", STATUS_PASS if source_inputs else STATUS_FAIL, str(root / EA_SOURCE_REL)),
        check("no_inp_magic_number_in_source", STATUS_PASS if "InpMagicNumber" not in source_inputs else STATUS_FAIL, "Phase2ExperimentalDemoExecutor derives magic 920101."),
        check("derived_magic_920101", STATUS_PASS if DERIVED_MAGIC == 920101 else STATUS_FAIL, f"derived_magic={DERIVED_MAGIC}"),
        check("portable_root_exists", STATUS_PASS if portable_root.exists() else STATUS_PENDING_RUNTIME, str(portable_root)),
        check("compiled_ea_present", STATUS_PASS if (portable_root / "MQL5" / "Experts" / f"{EA_NAME}.ex5").exists() else STATUS_PENDING_RUNTIME, str(portable_root / "MQL5" / "Experts" / f"{EA_NAME}.ex5")),
        check("compile_0_errors_0_warnings", STATUS_PASS if compile_log_passed(compile_log) else STATUS_PENDING_RUNTIME, str(compile_log)),
        check("old_account_1025742_not_allowlisted", STATUS_PASS if login != OLD_DEMO_ACCOUNT else STATUS_FAIL, f"allowlist={mask_account(login)}"),
        check("demo_server_marker", STATUS_PASS if demo_marker(preset.get("InpExpectedServerMarker", "")) else STATUS_FAIL if preset else STATUS_PENDING_OWNER, f"InpExpectedServerMarker={preset.get('InpExpectedServerMarker', '')!r}"),
        check("no_live_or_real_marker", STATUS_PASS if "live" not in preset.get("InpExpectedServerMarker", "").lower() and "real" not in preset.get("InpExpectedServerMarker", "").lower() else STATUS_FAIL, f"InpExpectedServerMarker={preset.get('InpExpectedServerMarker', '')!r}"),
        *_preset_exact_checks(preset, source_inputs),
        check("kill_switch_block_test", STATUS_PENDING_MANUAL, "Create tier1_bestea_kill_switch.txt, confirm EA refuses/blocks, then remove before clean attach."),
        check("single_xauusd_m5_chart_owner_confirmation", STATUS_PENDING_MANUAL, "Owner must attach only Phase2ExperimentalDemoExecutor to one XAUUSD M5 chart."),
    ]
    if source_terminal_root is not None:
        checks.append(_source_spread_logger_check(source_terminal_root.resolve(), login))

    payload = {
        "status": overall_status(checks),
        "created_at_utc": now_utc(),
        "authority": "Tier-1 breakout_retest preflight. It can clear only the isolated experimental demo lane, not canonical Phase 2.",
        "portable_root": str(portable_root),
        "local_preset": str(local_preset),
        "masked_account": mask_account(login),
        "derived_magic": DERIVED_MAGIC,
        "canonical_phase2_authorized": False,
        "charts_attached_by_codex": False,
        "checks": checks,
    }
    write_report_pair(output_json, payload, _render_preflight(payload))
    return payload


def _preset_exact_checks(preset: dict[str, str], source_inputs: dict[str, str]) -> list[dict[str, str]]:
    if not preset:
        return [check("preset_values_present", STATUS_PENDING_OWNER, "local preset missing")]
    checks: list[dict[str, str]] = []
    unknown = sorted(key for key in preset if key.startswith("Inp") and key not in source_inputs)
    checks.append(check("preset_has_only_current_source_inputs", STATUS_PASS if not unknown else STATUS_FAIL, ",".join(unknown) if unknown else "all inputs match source"))
    required = {
        "InpAllowedAccountLoginsCsv": None,
        **TIER1_PRESET_VALUES,
    }
    for key, expected in required.items():
        if key == "InpAllowedAccountLoginsCsv":
            ok = bool(preset.get(key, "").strip())
            checks.append(check("allowlist_present", STATUS_PASS if ok else STATUS_FAIL, f"{key}={mask_account(preset.get(key, ''))}"))
        else:
            actual = preset.get(key, "")
            checks.append(check(f"{key}_expected", STATUS_PASS if actual == expected else STATUS_FAIL, f"{key}={actual!r}; expected={expected!r}"))
    return checks


def _gitignore_check(root: Path) -> str:
    gitignore = root.parents[1] / ".gitignore"
    if not gitignore.exists():
        return STATUS_FAIL
    text = gitignore.read_text(encoding="utf-8", errors="replace")
    return STATUS_PASS if "xau-usd/xauusd-phase1/local/" in text and "owner_authorized" in text else STATUS_FAIL


def _source_spread_logger_check(source_terminal_root: Path, login: str) -> dict[str, str]:
    if not login:
        return check("source_terminal_not_using_tier1_account", STATUS_PENDING_OWNER, "No login in preset.")
    files_dir = source_terminal_root / "MQL5" / "Files"
    if not files_dir.exists():
        return check("source_terminal_not_using_tier1_account", STATUS_PASS, f"No MQL5/Files at {source_terminal_root}")
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    active_files = sorted(files_dir.glob(f"spread_log_{login}_*_{today}.csv"))
    if not active_files:
        return check("source_terminal_not_using_tier1_account", STATUS_PASS, f"No current spread log for {mask_account(login)} in {source_terminal_root}")
    newest = max(active_files, key=lambda path: path.stat().st_mtime)
    age_seconds = max(0.0, datetime.now(timezone.utc).timestamp() - newest.stat().st_mtime)
    status = STATUS_FAIL if age_seconds < 600 else STATUS_PENDING_MANUAL
    return check("source_terminal_not_using_tier1_account", status, f"{newest}; age_seconds={age_seconds:.0f}. Close/log out this source terminal before attaching Tier-1 EA.")


def _render_preflight(payload: dict[str, Any]) -> str:
    lines = report_header("Tier-1 Breakout Retest Preflight", payload)
    lines.extend(boundary_lines())
    lines.extend([
        f"- Portable root: `{payload['portable_root']}`",
        f"- Local preset: `{payload['local_preset']}`",
        f"- Masked account: `{payload['masked_account']}`",
        f"- Derived magic: `{payload['derived_magic']}`",
        f"- Charts attached by Codex: `{payload['charts_attached_by_codex']}`",
        "",
        "## Checks",
        "",
        *checks_table(payload["checks"]),
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Tier-1 breakout_retest preflight report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--local-preset", type=Path, default=None)
    parser.add_argument("--portable-root", type=Path, default=DEFAULT_PORTABLE_ROOT)
    parser.add_argument("--source-terminal-root", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = generate_tier1_preflight(args.root, args.local_preset, args.portable_root, args.source_terminal_root, args.output_json)
    print(f"Tier-1 preflight: {payload['status']}")
    return 0 if payload["status"] == STATUS_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
