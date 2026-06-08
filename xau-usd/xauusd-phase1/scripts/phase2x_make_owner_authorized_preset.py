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
    DEFAULT_LOCAL_PRESET,
    DEFAULT_OWNER_JSON,
    OWNER_TEMPLATE_REL,
    PHASE2X_STATUS_FAIL,
    PHASE2X_STATUS_PASS,
    boundary_lines,
    checks_table,
    mask_account,
    now_utc,
    owner_status_from_checks,
    read_json,
    render_set_file,
    report_header,
    reports_dir,
    sha256,
    strict_values_from_owner,
    validate_local_output_path,
    validate_owner_authorization,
    write_report_pair,
)


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "PHASE2X_OWNER_AUTHORIZATION_STATUS.json"


def make_owner_authorized_preset(
    root: Path,
    owner_json: Path | None = None,
    template: Path | None = None,
    output: Path | None = None,
    status_json: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    owner_json = (owner_json or root / DEFAULT_OWNER_JSON).resolve()
    template = (template or root / OWNER_TEMPLATE_REL).resolve()
    output = (output or root / DEFAULT_LOCAL_PRESET).resolve()
    status_json = (status_json or root / DEFAULT_STATUS_JSON).resolve()

    data = read_json(owner_json)
    validation_checks = validate_owner_authorization(data) if data else []
    status = owner_status_from_checks(validation_checks, owner_json)
    path_check = {"name": "local_output_path", "status": PHASE2X_STATUS_PASS, "evidence": str(output)}
    try:
        validate_local_output_path(root, output)
    except ValueError as exc:
        path_check = {"name": "local_output_path", "status": PHASE2X_STATUS_FAIL, "evidence": str(exc)}
        status = PHASE2X_STATUS_FAIL
    checks = [
        {"name": "owner_json_present", "status": PHASE2X_STATUS_PASS if owner_json.exists() else "PENDING_OWNER_ACTION", "evidence": str(owner_json)},
        *validation_checks,
        path_check,
    ]

    wrote_preset = False
    if status == PHASE2X_STATUS_PASS and path_check["status"] == PHASE2X_STATUS_PASS:
        output.parent.mkdir(parents=True, exist_ok=True)
        values = strict_values_from_owner(data)
        lines = template.read_text(encoding="utf-8", errors="replace").splitlines() if template.exists() else []
        output.write_text(render_set_file(lines, values), encoding="utf-8")
        wrote_preset = True

    payload = {
        "status": status if wrote_preset else ("PENDING_OWNER_ACTION" if not owner_json.exists() else status),
        "created_at_utc": now_utc(),
        "authority": "Phase 2X owner authorization status. The generated preset is local/private demo-only and non-canonical.",
        "owner_json": str(owner_json),
        "template": str(template),
        "local_preset": str(output),
        "local_preset_written": wrote_preset,
        "local_preset_sha256": sha256(output) if wrote_preset else "NOT_WRITTEN",
        "masked_authorized_account_login": mask_account(data.get("authorized_account_login", "")),
        "canonical_phase2_authorized": False,
        "live_trading_authorized": False,
        "real_capital_authorized": False,
        "checks": checks,
    }
    write_report_pair(status_json, payload, _render(payload))
    return payload


def _render(payload: dict[str, Any]) -> str:
    lines = report_header("Phase 2X Owner Authorization Status", payload)
    lines.extend(boundary_lines())
    lines.extend([
        "## Owner Authorization",
        "",
        f"- Owner JSON: `{payload['owner_json']}`",
        f"- Local preset written: `{payload['local_preset_written']}`",
        f"- Local preset SHA256: `{payload['local_preset_sha256']}`",
        f"- Masked account: `{payload['masked_authorized_account_login']}`",
        "",
        "## Checks",
        "",
        *checks_table(payload["checks"]),
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a local Phase 2X owner-authorized demo preset.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--owner-json", type=Path, default=None)
    parser.add_argument("--template", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--status-json", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = make_owner_authorized_preset(args.root, args.owner_json, args.template, args.output, args.status_json)
    print("WARNING: Phase 2X local preset is demo-only, non-canonical, and private.")
    print(f"Phase 2X owner authorization: {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
