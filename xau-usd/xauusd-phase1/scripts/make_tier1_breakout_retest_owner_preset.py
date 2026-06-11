from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from tier1_breakout_retest_common import (
    DEFAULT_LOCAL_PRESET,
    DEFAULT_OWNER_JSON,
    DEFAULT_PORTABLE_ROOT,
    DERIVED_MAGIC,
    EA_SOURCE_REL,
    STATUS_FAIL,
    STATUS_PASS,
    TEMPLATE_REL,
    boundary_lines,
    check,
    checks_table,
    mask_account,
    now_utc,
    overall_status,
    owner_payload_from_login,
    parse_mq5_inputs,
    read_json,
    render_set_file,
    report_header,
    reports_dir,
    sha256,
    tier1_values_from_owner,
    validate_local_output_path,
    validate_owner_authorization,
    write_report_pair,
)


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "TIER1_OWNER_AUTHORIZATION_STATUS.json"


def make_tier1_owner_preset(
    root: Path,
    owner_json: Path | None = None,
    template: Path | None = None,
    output: Path | None = None,
    status_json: Path | None = None,
    authorized_account_login: str | None = None,
    authorized_server_marker: str = "Demo",
    portable_root: Path | None = None,
    copy_to_portable: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    owner_json = (owner_json or root / DEFAULT_OWNER_JSON).resolve()
    template = (template or root / TEMPLATE_REL).resolve()
    output = (output or root / DEFAULT_LOCAL_PRESET).resolve()
    status_json = (status_json or root / DEFAULT_STATUS_JSON).resolve()
    portable_root = (portable_root or DEFAULT_PORTABLE_ROOT).resolve()

    if authorized_account_login and not owner_json.exists():
        owner_json.parent.mkdir(parents=True, exist_ok=True)
        owner_json.write_text(json.dumps(owner_payload_from_login(authorized_account_login, authorized_server_marker), indent=2), encoding="utf-8")

    data = read_json(owner_json)
    validation_checks = validate_owner_authorization(data) if data else []
    path_check = check("local_output_path", STATUS_PASS, str(output))
    try:
        validate_local_output_path(root, output)
    except ValueError as exc:
        path_check = check("local_output_path", STATUS_FAIL, str(exc))

    source_inputs = parse_mq5_inputs(root / EA_SOURCE_REL)
    input_name_checks = [
        check("source_has_no_inp_magic_number", STATUS_PASS if "InpMagicNumber" not in source_inputs else STATUS_FAIL, "Magic is derived by InstanceMagic() and expected to be 920101."),
        check("derived_magic_documented", STATUS_PASS if DERIVED_MAGIC == 920101 else STATUS_FAIL, f"derived_magic={DERIVED_MAGIC}"),
    ]

    status = overall_status([
        check("owner_json_present", STATUS_PASS if owner_json.exists() else "PENDING_OWNER_ACTION", str(owner_json)),
        *validation_checks,
        path_check,
        *input_name_checks,
    ])

    wrote_preset = False
    portable_preset: Path | None = None
    if status == STATUS_PASS:
        values = tier1_values_from_owner(data)
        unknown_inputs = sorted(key for key in values if key not in source_inputs)
        if unknown_inputs:
            input_name_checks.append(check("preset_values_match_current_source_inputs", STATUS_FAIL, ",".join(unknown_inputs)))
            status = STATUS_FAIL
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(render_set_file(template.read_text(encoding="utf-8", errors="replace").splitlines(), values), encoding="utf-8")
            wrote_preset = True
            if copy_to_portable:
                portable_preset = portable_root / "MQL5" / "Presets" / output.name
                portable_preset.parent.mkdir(parents=True, exist_ok=True)
                portable_preset.write_text(output.read_text(encoding="utf-8"), encoding="utf-8")

    checks = [
        check("owner_json_present", STATUS_PASS if owner_json.exists() else "PENDING_OWNER_ACTION", str(owner_json)),
        *validation_checks,
        path_check,
        *input_name_checks,
        check("template_present", STATUS_PASS if template.exists() else STATUS_FAIL, str(template)),
        check("local_preset_written", STATUS_PASS if wrote_preset else status, str(output)),
    ]
    if copy_to_portable:
        checks.append(check("local_preset_copied_to_portable", STATUS_PASS if portable_preset and portable_preset.exists() else STATUS_FAIL, str(portable_preset or portable_root)))

    payload = {
        "status": overall_status(checks),
        "created_at_utc": now_utc(),
        "authority": "Tier-1 breakout_retest owner authorization. Local/private demo-only preset; no canonical Phase 2 authorization.",
        "owner_json": str(owner_json),
        "template": str(template),
        "local_preset": str(output),
        "portable_preset": str(portable_preset) if portable_preset else "",
        "local_preset_written": wrote_preset,
        "local_preset_sha256": sha256(output) if wrote_preset else "NOT_WRITTEN",
        "masked_authorized_account_login": mask_account(data.get("authorized_account_login", "")),
        "derived_magic": DERIVED_MAGIC,
        "canonical_phase2_authorized": False,
        "live_trading_authorized": False,
        "real_capital_authorized": False,
        "checks": checks,
    }
    write_report_pair(status_json, payload, _render(payload))
    return payload


def _render(payload: dict[str, Any]) -> str:
    lines = report_header("Tier-1 Breakout Retest Owner Authorization", payload)
    lines.extend(boundary_lines())
    lines.extend([
        "## Owner Authorization",
        "",
        f"- Owner JSON: `{payload['owner_json']}`",
        f"- Local preset written: `{payload['local_preset_written']}`",
        f"- Local preset SHA256: `{payload['local_preset_sha256']}`",
        f"- Masked account: `{payload['masked_authorized_account_login']}`",
        f"- Derived magic: `{payload['derived_magic']}`",
        "",
        "## Checks",
        "",
        *checks_table(payload["checks"]),
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the local Tier-1 breakout_retest owner-authorized preset.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--owner-json", type=Path, default=None)
    parser.add_argument("--template", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--status-json", type=Path, default=None)
    parser.add_argument("--authorized-account-login", default=None)
    parser.add_argument("--authorized-server-marker", default="Demo")
    parser.add_argument("--portable-root", type=Path, default=None)
    parser.add_argument("--copy-to-portable", action="store_true")
    args = parser.parse_args(argv)
    payload = make_tier1_owner_preset(
        args.root,
        owner_json=args.owner_json,
        template=args.template,
        output=args.output,
        status_json=args.status_json,
        authorized_account_login=args.authorized_account_login,
        authorized_server_marker=args.authorized_server_marker,
        portable_root=args.portable_root,
        copy_to_portable=args.copy_to_portable,
    )
    print(f"Tier-1 owner authorization: {payload['status']}")
    return 0 if payload["status"] == STATUS_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
