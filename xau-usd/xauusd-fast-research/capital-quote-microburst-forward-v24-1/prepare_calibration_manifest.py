from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from microburst import (  # noqa: E402
    canonical_hash,
    file_record,
    load_config,
)


def main() -> int:
    config = load_config(ROOT)
    source = config["source"]
    path = Path(source["calibration_file"])
    if not path.is_file():
        raise FileNotFoundError(path)
    record = file_record(path)
    if record["sha256"] != source["calibration_file_sha256"]:
        raise ValueError("V24 calibration file changed before manifest lock")
    manifest = {
        "schema_version": "xauusd_v24_1_calibration_source_manifest",
        "calibration_files": [record],
        "window": {
            "start_inclusive_utc": source["calibration_start_inclusive_utc"],
            "end_exclusive_utc": source["calibration_end_exclusive_utc"],
        },
        "economic_outcomes_allowed": False,
        "paid_source_used": False,
    }
    manifest["manifest_sha256"] = canonical_hash(manifest, "manifest_sha256")
    output = ROOT / source["calibration_manifest"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
