from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
V72_SRC = ROOT.parent / "xag-xau-eventtime-catchup-v72" / "src"
for source in (ROOT / "src", V72_SRC):
    sys.path.insert(0, str(source))

from catchup import (  # noqa: E402
    canonical_hash,
    load_json,
    month_keys,
    validate_month_manifest,
)


CONFIG = ROOT / "config" / "xag_xau_eventtime_antisignal_v73.json"


def run_exam_source_audit() -> dict[str, Any]:
    config = load_json(CONFIG)
    output = ROOT / str(config["outputs"]["directory"])
    path = output / str(config["outputs"]["exam_source_audit"])
    if path.exists():
        raise FileExistsError("V73 exam source audit already exists")
    validation_path = output / "XAG_XAU_V73_VALIDATION_AUDIT.json"
    validation = load_json(validation_path)
    if (
        not bool(validation.get("gate_passed"))
        or canonical_hash(validation, "audit_sha256") != validation.get("audit_sha256")
    ):
        raise RuntimeError("V73 exam source remains sealed until validation passes")
    source = config["source"]
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()
    manifests: list[dict[str, Any]] = []
    for symbol, spec in source["symbols"].items():
        for year, month in month_keys(source["exam_first_month"], source["exam_last_month"]):
            _, row = validate_month_manifest(storage, symbol, spec, year, month)
            manifests.append(row)
    audit: dict[str, Any] = {
        "schema_version": "xauusd_xag_xau_v73_exam_source_audit",
        "campaign_id": str(config["campaign_id"]),
        "decision": "V73_EXAM_SOURCE_AUDIT_PASS",
        "first_month": source["exam_first_month"],
        "last_month": source["exam_last_month"],
        "month_manifests": manifests,
        "month_manifest_count": len(manifests),
        "runtime_raw_file_hash_verification_required": True,
        "paid_data_used": False,
        "economic_outcomes_opened": False,
    }
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    path.write_bytes(
        (json.dumps(audit, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    print(json.dumps({"decision": audit["decision"], "audit_sha256": audit["audit_sha256"]}, indent=2))
    return audit


if __name__ == "__main__":
    run_exam_source_audit()

