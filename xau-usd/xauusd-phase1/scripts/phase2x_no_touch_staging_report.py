from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase2x_common import (
    ACTIVE_MAGIC,
    DEFAULT_LOCAL_PRESET,
    FIXED_LOT,
    MAX_ESTIMATED_COST_R,
    MAX_FAMILY_OPEN_POSITIONS,
    MAX_MEASURED_SPREAD_POINTS,
    RUN_ID,
    SAFE_PRESET_REL,
    TARGET_SYMBOL,
    boundary_lines,
    check,
    checks_table,
    now_utc,
    overall_status,
    parse_set_file,
    read_json,
    report_header,
    reports_dir,
    sha256,
    write_report_pair,
)


DEFAULT_JSON = Path("outputs") / "reports" / "PHASE2X_NO_TOUCH_STAGING_REPORT.json"
DEFAULT_STARTUP_CONFIG = Path("mt5") / "Config" / "p2weakness_br_v1_startup.ini"
PORTABLE_REPORT = Path("outputs") / "reports" / "PHASE2_WEAKNESS_BR_V1_PORTABLE_DEMO_TERMINAL.json"
NO_LAUNCH_STATUSES = {
    "PORTABLE_PREPARED_AND_DEPLOYED_NO_LAUNCH",
    "PORTABLE_PREPARED_NO_DEPLOY_NO_LAUNCH",
    "PORTABLE_DEPLOYED_NO_LAUNCH",
    "PORTABLE_REPORT_ONLY_NO_PREPARE_NO_DEPLOY_NO_LAUNCH",
}


def generate_phase2x_no_touch_staging_report(
    root: Path,
    output_json: Path | None = None,
    startup_config: Path | None = None,
    safe_preset: Path | None = None,
    local_preset: Path | None = None,
    portable_report: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    startup_config = (startup_config or root / DEFAULT_STARTUP_CONFIG).resolve()
    safe_preset = (safe_preset or root / SAFE_PRESET_REL).resolve()
    local_preset = (local_preset or root / DEFAULT_LOCAL_PRESET).resolve()
    portable_report = (portable_report or root / PORTABLE_REPORT).resolve()
    startup = _parse_startup_config(startup_config)
    safe_values = parse_set_file(safe_preset)
    owner_values = parse_set_file(local_preset)
    portable = read_json(portable_report)
    preflight = read_json(reports_dir(root) / "PHASE2X_DEMO_PREFLIGHT_REPORT.json")

    checks = [
        check("script_is_report_only", "PASS", "No launch, attach, close, restart, order, or file-copy action is performed."),
        check("startup_config_exists", "PASS" if startup_config.exists() else "FAIL", str(startup_config)),
        check("startup_live_trading_disabled", "PASS" if startup.get("AllowLiveTrading") == "0" else "FAIL", f"AllowLiveTrading={startup.get('AllowLiveTrading', '')!r}"),
        check("startup_uses_committed_safe_preset", "PASS" if startup.get("ExpertParameters") == safe_preset.name else "FAIL", f"ExpertParameters={startup.get('ExpertParameters', '')!r}"),
        check("startup_symbol_xauusd_m5", "PASS" if startup.get("Symbol") == TARGET_SYMBOL and startup.get("Period") == "M5" else "FAIL", f"Symbol={startup.get('Symbol', '')!r}; Period={startup.get('Period', '')!r}"),
        check("safe_preset_non_executing", "PASS" if safe_values.get("InpDryRunOnly") == "true" and safe_values.get("InpBrokerActionAllowed") == "false" else "FAIL", _preset_evidence(safe_values)),
        check("safe_preset_private_tokens_blank", "PASS" if _blank_private_inputs(safe_values) else "FAIL", "account whitelist, auth token, and cost acknowledgement must be blank in committed safe preset."),
        check("safe_preset_magic_931000", "PASS" if safe_values.get("InpMagicNumber") == str(ACTIVE_MAGIC) else "FAIL", f"InpMagicNumber={safe_values.get('InpMagicNumber', '')!r}"),
        check("owner_local_preset_present", "PASS" if local_preset.exists() else "PENDING_OWNER_ACTION", str(local_preset)),
        check("owner_local_preset_private_path", "PASS" if "local" in [part.lower() for part in local_preset.parts] else "FAIL", str(local_preset)),
        check("owner_local_preset_sha256_only", "PASS" if local_preset.exists() else "PENDING_OWNER_ACTION", sha256(local_preset)),
        check("owner_local_preset_strict_values", _owner_strict_status(owner_values), _owner_strict_evidence(owner_values)),
        check("portable_report_available", "PASS" if portable else "PENDING_RUNTIME_EVIDENCE", str(portable_report)),
        check("portable_not_launched_by_staging", _portable_no_launch_status(portable), _portable_evidence(portable)),
        check("portable_old_terminal_not_touched", _portable_old_terminal_status(portable), _portable_old_terminal_evidence(portable)),
        check("preflight_not_forced_to_pass", "PASS" if preflight.get("status") != "PASS" else "FAIL", f"preflight_status={preflight.get('status', 'MISSING')!r}"),
        check("canonical_phase2_not_promoted", "PASS", "No canonical Phase 2 readiness report is changed by this no-touch staging report."),
    ]
    payload = {
        "status": overall_status(checks),
        "created_at_utc": now_utc(),
        "authority": "Phase 2X no-touch staging report. Report-only; it does not touch existing running MT5 terminals, attach charts, launch terminals, or authorize broker execution.",
        "phase2x_demo_execution_authorized": False,
        "canonical_phase2_authorized": False,
        "live_trading_authorized": False,
        "real_capital_authorized": False,
        "startup_config": str(startup_config),
        "safe_preset": str(safe_preset),
        "local_preset": str(local_preset),
        "local_preset_sha256": sha256(local_preset),
        "portable_report": str(portable_report),
        "checks": checks,
    }
    write_report_pair(output_json, payload, _render(payload))
    return payload


def _parse_startup_config(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip() or line.lstrip().startswith("[") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _blank_private_inputs(values: dict[str, str]) -> bool:
    return all(
        not values.get(key, "").strip()
        for key in ("InpAllowedAccountLoginsCsv", "InpExperimentalAuthorizationToken", "InpCostSuspensionAcknowledgementToken")
    )


def _preset_evidence(values: dict[str, str]) -> str:
    return f"InpDryRunOnly={values.get('InpDryRunOnly', '')!r}; InpBrokerActionAllowed={values.get('InpBrokerActionAllowed', '')!r}"


def _owner_strict_status(values: dict[str, str]) -> str:
    if not values:
        return "PENDING_OWNER_ACTION"
    return "PASS" if (
        values.get("InpRunId") == RUN_ID
        and values.get("InpDryRunOnly") == "false"
        and values.get("InpBrokerActionAllowed") == "true"
        and values.get("InpTargetSymbol") == TARGET_SYMBOL
        and values.get("InpMagicNumber") == str(ACTIVE_MAGIC)
        and _float_lte(values.get("InpFixedLot"), FIXED_LOT)
        and _int_eq(values.get("InpMaxFamilyOpenPositions"), MAX_FAMILY_OPEN_POSITIONS)
        and _float_lte(values.get("InpMaxEstimatedCostR"), MAX_ESTIMATED_COST_R)
        and _float_lte(values.get("InpMaxMeasuredSpreadPoints"), MAX_MEASURED_SPREAD_POINTS)
    ) else "FAIL"


def _owner_strict_evidence(values: dict[str, str]) -> str:
    if not values:
        return "local owner preset missing"
    return (
        f"InpRunId={values.get('InpRunId', '')!r}; InpMagicNumber={values.get('InpMagicNumber', '')!r}; "
        f"InpFixedLot={values.get('InpFixedLot', '')!r}; InpMaxFamilyOpenPositions={values.get('InpMaxFamilyOpenPositions', '')!r}; "
        f"InpMaxEstimatedCostR={values.get('InpMaxEstimatedCostR', '')!r}; InpMaxMeasuredSpreadPoints={values.get('InpMaxMeasuredSpreadPoints', '')!r}"
    )


def _portable_no_launch_status(payload: dict[str, Any]) -> str:
    if not payload:
        return "PENDING_RUNTIME_EVIDENCE"
    if payload.get("launch_started") is True:
        return "FAIL"
    return "PASS" if payload.get("status") in NO_LAUNCH_STATUSES else "PENDING_RUNTIME_EVIDENCE"


def _portable_evidence(payload: dict[str, Any]) -> str:
    if not payload:
        return "portable report missing"
    return f"status={payload.get('status', '')!r}; launch_started={payload.get('launch_started')!r}"


def _portable_old_terminal_status(payload: dict[str, Any]) -> str:
    if not payload:
        return "PENDING_RUNTIME_EVIDENCE"
    return "PASS" if payload.get("old_terminal_profile_touched") is False and payload.get("old_terminal_closed_or_restarted") is False else "FAIL"


def _portable_old_terminal_evidence(payload: dict[str, Any]) -> str:
    if not payload:
        return "portable report missing"
    return f"old_terminal_profile_touched={payload.get('old_terminal_profile_touched')!r}; old_terminal_closed_or_restarted={payload.get('old_terminal_closed_or_restarted')!r}"


def _float_lte(value: object, limit: float) -> bool:
    try:
        return float(str(value)) <= limit
    except ValueError:
        return False


def _int_eq(value: object, expected: int) -> bool:
    try:
        return int(float(str(value))) == expected
    except ValueError:
        return False


def _render(payload: dict[str, Any]) -> str:
    lines = report_header("Phase 2X No-Touch Staging Report", payload)
    lines.extend(boundary_lines())
    lines.extend([
        "- Existing running MT5 terminals touched: `False`",
        "- Terminal launch attempted: `False`",
        "- Chart attach attempted: `False`",
        "- Broker execution authorized: `False`",
        f"- Local owner preset SHA256 only: `{payload['local_preset_sha256']}`",
        "",
        "## Staged Inputs",
        "",
        f"- Startup config: `{payload['startup_config']}`",
        f"- Safe preset: `{payload['safe_preset']}`",
        f"- Local owner preset: `{payload['local_preset']}`",
        f"- Portable report: `{payload['portable_report']}`",
        "",
        "## Checks",
        "",
        *checks_table(payload["checks"]),
        "",
        "## Next Runtime-Dependent Items",
        "",
        "- Safe dry-run attach evidence using the committed non-executing preset.",
        "- Kill-switch block proof.",
        "- Fresh `931000` startup/runtime rows after owner-approved attach.",
        "- Phase 2X preflight PASS before any owner-authorized demo execution.",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 2X no-touch staging report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--startup-config", type=Path, default=None)
    parser.add_argument("--safe-preset", type=Path, default=None)
    parser.add_argument("--local-preset", type=Path, default=None)
    parser.add_argument("--portable-report", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = generate_phase2x_no_touch_staging_report(
        args.root,
        args.output_json,
        args.startup_config,
        args.safe_preset,
        args.local_preset,
        args.portable_report,
    )
    print(f"Phase 2X no-touch staging: {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
