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


CONFIG = ROOT / "config" / "fx_breadth_overreaction_fade_v81.json"


def audit_month_bounds(config: dict[str, Any], scope: str) -> tuple[str, str]:
    if scope == "full":
        return str(config["source"]["first_month"]), str(
            config["source"]["last_month"]
        )
    calibration = config["calibration"]
    start = pd.Timestamp(calibration["start"])
    end = pd.Timestamp(calibration["end"]) - pd.Timedelta(nanoseconds=1)
    return start.strftime("%Y-%m"), end.strftime("%Y-%m")


def run_source_audit(scope: str = "full") -> dict[str, Any]:
    config = load_json(CONFIG)
    output = ROOT / str(config["outputs"]["directory"])
    output_key = "source_audit" if scope == "full" else "calibration_source_audit"
    path = output / str(config["outputs"][output_key])
    if path.exists():
        raise FileExistsError(f"V81 {scope} source audit already exists")
    source = config["source"]
    first_month, last_month = audit_month_bounds(config, scope)
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()
    expected = {
        "EURUSD": {"code": "EUR-USD", "name": "EUR/USD", "price_scale": 5},
        "GBPUSD": {"code": "GBP-USD", "name": "GBP/USD", "price_scale": 5},
        "USDJPY": {"code": "USD-JPY", "name": "USD/JPY", "price_scale": 3},
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
            raise ValueError(f"V81 official {symbol} evidence is invalid")
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
        raise ValueError("V81 source audit has incomplete symbol-month coverage")
    audit: dict[str, Any] = {
        "schema_version": f"xauusd_fx_breadth_overreaction_v81_{scope}_source_audit",
        "campaign_id": config["campaign_id"],
        "scope": scope,
        "decision": (
            "V81_SOURCE_AUDIT_PASS"
            if scope == "full"
            else "V81_CALIBRATION_SOURCE_AUDIT_PASS"
        ),
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
    output.mkdir(parents=True, exist_ok=True)
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
    parser = argparse.ArgumentParser(description="Audit frozen V81 source months")
    parser.add_argument("--scope", choices=("calibration", "full"), default="full")
    args = parser.parse_args()
    run_source_audit(str(args.scope))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
