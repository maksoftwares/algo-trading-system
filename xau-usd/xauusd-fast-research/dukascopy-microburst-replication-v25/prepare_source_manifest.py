from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from replication import build_source_manifest, load_config  # noqa: E402


def main() -> int:
    config = load_config(ROOT)
    output = ROOT / config["outputs"]["directory"]
    manifest_path = output / config["outputs"]["source_manifest"]
    contract_path = output / config["outputs"]["contract_lock"]
    if manifest_path.exists():
        raise FileExistsError("V25 source manifest already exists")
    if contract_path.exists():
        raise FileExistsError("V25 contract already exists")
    manifest = build_source_manifest(config)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(
        (json.dumps(manifest, allow_nan=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )
    print(json.dumps(manifest, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
