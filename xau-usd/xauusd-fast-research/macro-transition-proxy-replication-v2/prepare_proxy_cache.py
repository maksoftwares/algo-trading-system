from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from proxy_data import build_cache, write_json  # noqa: E402


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "macro_transition_proxy_replication_v2.json").read_text(
            encoding="utf-8"
        )
    )
    source = config["proxy_source"]
    storage = Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    )
    external_root = storage / source["root"]
    acquisition = external_root / source["acquisition_manifest"]
    cache = external_root / source["cache"]
    manifest = build_cache(external_root, acquisition, cache)
    manifest_path = external_root / source["cache_manifest"]
    write_json(manifest_path, manifest)
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
