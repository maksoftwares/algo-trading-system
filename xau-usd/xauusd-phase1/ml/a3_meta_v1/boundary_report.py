from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountRegistry, load_mt5_account_registry
from .safety import scan_c02_python_safety


DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "C02_READ_ONLY_BOUNDARY_BUILD.json"


def generate_c02_read_only_boundary_report(
    root: Path,
    registry_path: Path | None = None,
    output_json: Path | None = None,
) -> Path:
    root = root.resolve()
    registry_path = (registry_path or root / "config" / "ml" / "mt5_accounts.yaml").resolve()
    output_json = (output_json or root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md")
    registry = load_mt5_account_registry(registry_path)
    findings = scan_c02_python_safety(root / "ml" / "a3_meta_v1")
    payload: dict[str, Any] = {
        "status": "PASS" if not findings else "FAIL_CLOSED",
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "stage": "C02-00",
        "boundary": {
            "read_only_scaffold_only": True,
            "mt5_connection_attempted": False,
            "data_exported": False,
            "model_training_authorized": False,
            "broker_action_authorized": False,
            "terminal_runtime_change_authorized": False,
        },
        "registry": _registry_summary(registry, registry_path),
        "safety_findings": [asdict(finding) for finding in findings],
        "next_allowed_stage": "C02-01 account verification workers after review",
        "prohibited_in_c02_00": [
            "MT5 connection",
            "data export",
            "model training",
            "broker action",
            "terminal launch",
            "account switching",
            "symbol selection",
            "chart/profile/preset mutation",
        ],
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return output_json


def _registry_summary(registry: MT5AccountRegistry, registry_path: Path) -> dict[str, Any]:
    return {
        "path": str(registry_path),
        "schema_version": registry.schema_version,
        "common": {
            "symbol": registry.common.symbol,
            "expected_server_regex": registry.common.expected_server_regex,
            "require_demo_trade_mode": registry.common.require_demo_trade_mode,
            "require_existing_terminal_process": registry.common.require_existing_terminal_process,
            "allow_mt5_login_call": registry.common.allow_mt5_login_call,
            "allow_symbol_select_call": registry.common.allow_symbol_select_call,
            "export_timezone": registry.common.export_timezone,
            "snapshot_safety_lag_minutes": registry.common.snapshot_safety_lag_minutes,
        },
        "accounts": [
            {
                "account_scope": account.account_scope,
                "account_label": account.account_label,
                "expected_login": account.expected_login,
                "terminal_exe": account.terminal_exe,
                "expected_data_path": account.expected_data_path,
                "portable": account.portable,
                "role": account.role,
                "symbol": account.symbol,
                "files_roots_count": len(account.files_roots),
                "log_catalog": account.log_catalog,
            }
            for account in registry.accounts
        ],
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    rows = [
        {
            "Account": account["account_label"],
            "Scope": account["account_scope"],
            "Login": account["expected_login"],
            "Terminal": account["terminal_exe"],
            "Portable": str(account["portable"]).lower(),
            "Role": account["role"],
        }
        for account in payload["registry"]["accounts"]
    ]
    return "\n".join(
        [
            "# C02 Read-Only Boundary Build",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Boundary",
            "",
            "- Stage: C02-00 scaffold only.",
            "- MT5 connection attempted: false.",
            "- Data exported: false.",
            "- Model training authorized: false.",
            "- Broker action authorized: false.",
            "- Terminal runtime change authorized: false.",
            "",
            "## Registry",
            "",
            _table(rows, ["Account", "Scope", "Login", "Terminal", "Portable", "Role"]),
            "",
            "## Safety Scan",
            "",
            "No C02 Python safety findings." if not payload["safety_findings"] else json.dumps(payload["safety_findings"], indent=2),
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _table(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(str(row.get(column, "")).replace("|", "\\|") for column in columns) + " |" for row in rows]
    return "\n".join([header, separator, *body])
