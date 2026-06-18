from __future__ import annotations

import csv
import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_presets(root: Path, *, unsafe_committed: bool = False) -> None:
    presets = root / "mt5" / "Presets"
    presets.mkdir(parents=True)
    (presets / "Phase2WeaknessBreakoutRetestExecutor.demo_xauusd.set").write_text(
        "\n".join(
            [
                "InpRunId=P2WEAKNESS_BR_V1",
                "InpDryRunOnly=true",
                "InpBrokerActionAllowed=false" if not unsafe_committed else "InpBrokerActionAllowed=true",
                "InpTargetSymbol=XAUUSD",
                "InpAllowedAccountLoginsCsv=",
                "InpExperimentalAuthorizationToken=",
                "InpCostSuspensionAcknowledgementToken=",
                "InpMagicNumber=931000",
            ]
        ),
        encoding="utf-8",
    )
    (presets / "Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.template.set").write_text(
        "\n".join(
            [
                "InpRunId=P2WEAKNESS_BR_V1",
                "InpDryRunOnly=true",
                "InpBrokerActionAllowed=false",
                "InpTargetSymbol=XAUUSD",
                "InpExpectedServerMarker=Demo",
                "InpAllowedAccountLoginsCsv=<OWNER_TO_FILL>",
                "InpExperimentalAuthorizationToken=",
                "InpRequiredExperimentalAuthorizationToken=EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY",
                "InpCostSuspensionAcknowledgementToken=",
                "InpRequiredCostSuspensionAcknowledgementToken=I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT",
                "InpMagicNumber=931000",
                "InpFixedLot=0.01",
            ]
        ),
        encoding="utf-8",
    )


def valid_owner_json(**overrides):
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    data = {
        "authorization_status": "APPROVED_FOR_EXPERIMENTAL_DEMO_ONLY",
        "owner_name": "Owner",
        "approved_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "expires_at_utc": expires.isoformat().replace("+00:00", "Z"),
        "authorized_account_login": "1025742",
        "authorized_server_marker": "Demo",
        "authorized_symbol": "XAUUSD",
        "authorized_candidate": "P2WEAKNESS_BR_V1",
        "authorized_magic": 931000,
        "fixed_lot": 0.01,
        "max_orders_per_day": 2,
        "max_account_orders_per_day": 3,
        "max_family_open_positions": 1,
        "max_estimated_cost_r": 0.15,
        "max_measured_spread_points": 75.0,
        "experimental_authorization_token": "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY",
        "cost_suspension_acknowledgement_token": "I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT",
    }
    data.update(overrides)
    return data


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_status_md(path: Path, status: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# Report\n\nOverall status: {status}\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
