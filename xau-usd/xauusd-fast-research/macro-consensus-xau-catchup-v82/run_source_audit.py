from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
V72_SRC = ROOT.parent / "xag-xau-eventtime-catchup-v72" / "src"
for source in (ROOT / "src", V72_SRC):
    sys.path.insert(0, str(source))

from catchup import (  # noqa: E402
    canonical_hash,
    load_json,
    month_keys,
    sha256_file,
    validate_month_manifest,
)


CONFIG = ROOT / "config" / "macro_consensus_xau_catchup_v82.json"
STAGES = (
    "development",
    "confirmation",
    "validation",
    "exam",
    "forward_confirmation",
    "forward_final",
)
SCOPES = ("calibration", *STAGES, "full")


def audit_month_bounds(config: dict[str, Any], scope: str) -> tuple[str, str]:
    if scope == "full":
        return str(config["source"]["first_month"]), str(
            config["source"]["last_month"]
        )
    if scope == "calibration":
        window = config["calibration"]
        start = pd.Timestamp(window["start"])
        end = pd.Timestamp(window["end"]) - pd.Timedelta(nanoseconds=1)
        return start.strftime("%Y-%m"), end.strftime("%Y-%m")
    if scope not in STAGES:
        raise ValueError(f"unknown V82 source-audit scope: {scope}")
    start = pd.Timestamp(config["splits"][scope][0])
    end = pd.Timestamp(config["splits"][scope][1]) - pd.Timedelta(nanoseconds=1)
    return start.strftime("%Y-%m"), end.strftime("%Y-%m")


def source_audit_output_path(config: dict[str, Any], scope: str) -> Path:
    output = ROOT / str(config["outputs"]["directory"])
    if scope == "calibration":
        return output / str(config["outputs"]["calibration_source_audit"])
    if scope == "full":
        return output / str(config["outputs"]["source_audit"])
    if scope not in STAGES:
        raise ValueError(f"unknown V82 source-audit scope: {scope}")
    return output / str(config["outputs"]["stage_source_audits"][scope])


def source_audit_decision(scope: str) -> str:
    if scope == "calibration":
        return "V82_CALIBRATION_SOURCE_AUDIT_PASS"
    if scope == "full":
        return "V82_SOURCE_AUDIT_PASS"
    if scope not in STAGES:
        raise ValueError(f"unknown V82 source-audit scope: {scope}")
    return f"V82_{scope.upper()}_SOURCE_AUDIT_PASS"


def require_prior_economic_pass(config: dict[str, Any], scope: str) -> None:
    if scope in ("calibration", "development"):
        return
    prior = STAGES[-1] if scope == "full" else STAGES[STAGES.index(scope) - 1]
    output = ROOT / str(config["outputs"]["directory"])
    path = output / f"MACRO_CONSENSUS_XAU_V82_{prior.upper()}_AUDIT.json"
    if not path.is_file():
        raise RuntimeError(
            f"V82 {scope} source remains sealed until {prior} passes"
        )
    audit = load_json(path)
    if (
        canonical_hash(audit, "audit_sha256") != audit.get("audit_sha256")
        or not bool(audit.get("gate_passed"))
    ):
        raise RuntimeError(
            f"V82 {scope} source remains sealed because {prior} failed"
        )


def run_source_audit(scope: str = "full") -> dict[str, Any]:
    config = load_json(CONFIG)
    require_prior_economic_pass(config, scope)
    path = source_audit_output_path(config, scope)
    if path.exists():
        raise FileExistsError(f"V82 {scope} source audit already exists")
    source = config["source"]
    first_month, last_month = audit_month_bounds(config, scope)
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()
    expected = {
        "DOLLARIDXUSD": {
            "code": "DOLLAR.IDX-USD",
            "name": "DOLLAR.IDX/USD",
            "price_scale": 3,
        },
        "USTBONDTRUSD": {
            "code": "USTBOND.TR-USD",
            "name": "USTBOND.TR/USD",
            "price_scale": 3,
        },
        "XAGUSD": {"code": "XAG-USD", "name": "XAG/USD", "price_scale": 3},
        "XAUUSD": {"code": "XAU-USD", "name": "XAU/USD", "price_scale": 3},
    }
    evidence_rows: dict[str, dict[str, Any]] = {}
    for symbol, spec in expected.items():
        evidence_path = storage / "source-evidence" / f"instrument-{symbol}.json"
        evidence = load_json(evidence_path)
        if (
            evidence.get("code") != spec["code"]
            or evidence.get("name") != spec["name"]
            or int(evidence.get("priceScale", -1)) != spec["price_scale"]
            or not any(
                row.get("period") == "TICK"
                for row in evidence.get("histories", [])
            )
        ):
            raise ValueError(f"V82 official {symbol} evidence is invalid")
        evidence_rows[symbol] = {
            "path": str(evidence_path),
            "sha256": sha256_file(evidence_path),
        }
    manifests: list[dict[str, Any]] = []
    for symbol, spec in source["symbols"].items():
        for year, month in month_keys(first_month, last_month):
            _, row = validate_month_manifest(storage, symbol, spec, year, month)
            manifests.append(row)
    expected_count = len(source["symbols"]) * len(
        month_keys(first_month, last_month)
    )
    if len(manifests) != expected_count:
        raise ValueError("V82 source audit has incomplete symbol-month coverage")
    audit: dict[str, Any] = {
        "schema_version": f"xauusd_macro_consensus_xau_catchup_v82_{scope}_source_audit",
        "campaign_id": config["campaign_id"],
        "scope": scope,
        "decision": source_audit_decision(scope),
        "storage_root": str(storage),
        "symbols": source["symbols"],
        "first_month": first_month,
        "last_month": last_month,
        "instrument_evidence": evidence_rows,
        "month_manifests": manifests,
        "month_manifest_count": len(manifests),
        "declared_hours": sum(int(row["hours"]) for row in manifests),
        "declared_bytes": sum(int(row["declared_bytes"]) for row in manifests),
        "declared_ticks": sum(int(row["declared_ticks"]) for row in manifests),
        "runtime_raw_file_hash_verification_required": True,
        "paid_data_used": False,
        "economic_outcomes_opened": False,
    }
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(audit, indent=2, sort_keys=True) + "\n").encode())
    print(
        json.dumps(
            {
                "decision": audit["decision"],
                "months": audit["month_manifest_count"],
                "hours": audit["declared_hours"],
                "ticks": audit["declared_ticks"],
                "audit_sha256": audit["audit_sha256"],
            },
            indent=2,
        )
    )
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit frozen V82 source months")
    parser.add_argument("--scope", choices=SCOPES, default="full")
    args = parser.parse_args()
    run_source_audit(str(args.scope))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
