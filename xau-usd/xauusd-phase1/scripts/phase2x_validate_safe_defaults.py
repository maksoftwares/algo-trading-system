from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase2x_common import (
    PHASE2X_STATUS_FAIL,
    PHASE2X_STATUS_PASS,
    SAFE_PRESET_REL,
    OWNER_TEMPLATE_REL,
    boundary_lines,
    check,
    checks_table,
    now_utc,
    overall_status,
    parse_set_file,
    report_header,
    reports_dir,
    write_report_pair,
)


DEFAULT_JSON = Path("outputs") / "reports" / "PHASE2X_SAFE_DEFAULTS_REPORT.json"


def generate_phase2x_safe_defaults_report(root: Path, output_json: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    safe = parse_set_file(root / SAFE_PRESET_REL)
    template = parse_set_file(root / OWNER_TEMPLATE_REL)
    checks = [
        _kv_check("normal_preset_dry_run", safe, "InpDryRunOnly", "true"),
        _kv_check("normal_preset_broker_action_disabled", safe, "InpBrokerActionAllowed", "false"),
        _kv_check("normal_preset_account_blank", safe, "InpAllowedAccountLoginsCsv", ""),
        _kv_check("normal_preset_auth_token_blank", safe, "InpExperimentalAuthorizationToken", ""),
        _kv_check("normal_preset_cost_ack_blank", safe, "InpCostSuspensionAcknowledgementToken", ""),
        _kv_check("owner_template_dry_run", template, "InpDryRunOnly", "true"),
        _kv_check("owner_template_broker_action_disabled", template, "InpBrokerActionAllowed", "false"),
        _no_committed_executing_set_check(root),
    ]
    payload = {
        "status": overall_status(checks),
        "created_at_utc": now_utc(),
        "authority": "Phase 2X safe-default validation. PASS does not authorize execution; it only proves committed presets remain non-executing.",
        "canonical_phase2_authorized": False,
        "live_trading_authorized": False,
        "real_capital_authorized": False,
        "checks": checks,
    }
    write_report_pair(output_json, payload, _render(payload))
    return payload


def _kv_check(name: str, values: dict[str, str], key: str, expected: str) -> dict[str, str]:
    actual = values.get(key)
    return check(name, PHASE2X_STATUS_PASS if actual == expected else PHASE2X_STATUS_FAIL, f"{key}={actual!r}; expected={expected!r}")


def _no_committed_executing_set_check(root: Path) -> dict[str, str]:
    offenders = []
    for path in sorted((root / "mt5" / "Presets").glob("*.set")):
        values = parse_set_file(path)
        if str(values.get("InpBrokerActionAllowed", "")).lower() == "true":
            offenders.append(str(path.relative_to(root)))
    return check(
        "no_committed_executing_set",
        PHASE2X_STATUS_PASS if not offenders else PHASE2X_STATUS_FAIL,
        "offenders=" + (", ".join(offenders) if offenders else "none"),
    )


def _render(payload: dict[str, Any]) -> str:
    lines = report_header("Phase 2X Safe Defaults Report", payload)
    lines.extend(boundary_lines())
    lines.extend(["## Checks", "", *checks_table(payload["checks"]), ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 2X committed safe defaults.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = generate_phase2x_safe_defaults_report(args.root, args.output_json)
    print(f"Phase 2X safe defaults: {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
