from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from economic_test import build_capital_manifest, load_config, resolve  # noqa: E402


def main() -> int:
    config = load_config(ROOT)
    path = resolve(ROOT, str(config["confirmation"]["capital_manifest"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError("V23 Capital source manifest already exists")
    manifest = build_capital_manifest(config)
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "capital_file_count": manifest["capital_file_count"],
                "manifest_sha256": manifest["manifest_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
