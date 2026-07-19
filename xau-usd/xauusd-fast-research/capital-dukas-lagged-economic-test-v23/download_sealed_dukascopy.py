from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from economic_test import (  # noqa: E402
    acquire_dukascopy_confirmation,
    canonical_hash,
    load_config,
    resolve,
    sha256_file,
    verify_locked_inputs,
)


def verify_contract(config: dict) -> dict:
    path = ROOT / config["outputs"]["directory"] / config["outputs"][
        "contract_lock"
    ]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if canonical_hash(payload, "contract_sha256") != payload["contract_sha256"]:
        raise ValueError("V23 contract self-hash mismatch")
    if not bool(payload["july_dukascopy_absent_at_lock"]):
        raise ValueError("V23 did not seal July Dukascopy before acquisition")
    for record in payload["package_files"]:
        package_path = REPO / record["path"]
        if sha256_file(package_path) != record["sha256"]:
            raise ValueError(f"Locked V23 file changed: {record['path']}")
    verify_locked_inputs(config, ROOT)
    return payload


def main() -> int:
    config = load_config(ROOT)
    contract = verify_contract(config)
    path = resolve(ROOT, str(config["confirmation"]["dukascopy_manifest"]))
    if path.exists():
        raise FileExistsError("V23 Dukascopy source manifest already exists")
    manifest = acquire_dukascopy_confirmation(config)
    manifest["contract_sha256_before_acquisition"] = contract["contract_sha256"]
    manifest["manifest_sha256"] = canonical_hash(manifest, "manifest_sha256")
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "contract_sha256": contract["contract_sha256"],
                "dukascopy_file_count": manifest["dukascopy_file_count"],
                "nonempty_hour_count": manifest["nonempty_hour_count"],
                "tick_count": manifest["tick_count"],
                "manifest_sha256": manifest["manifest_sha256"],
                "paid_source_used": manifest["paid_source_used"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
