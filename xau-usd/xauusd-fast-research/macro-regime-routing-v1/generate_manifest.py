from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from campaign import generate_manifest  # noqa: E402
from foundation import load_foundation  # noqa: E402


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "macro_regime_routing_v1.json").read_text(encoding="utf-8")
    )
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / config["outputs"]["manifest"]
    if manifest_path.exists():
        raise FileExistsError(
            "Manifest already exists; delete only before contract lock"
        )
    foundation = load_foundation(config)
    manifest = generate_manifest(foundation.decisions, config)
    manifest.to_csv(manifest_path, index=False, lineterminator="\n")
    print(
        json.dumps(
            {
                "manifest": str(manifest_path),
                "attempts": int(len(manifest)),
                "attempt_first": int(manifest["attempt_no"].min()),
                "attempt_last": int(manifest["attempt_no"].max()),
                "owners": manifest.groupby("regime_owner").size().to_dict(),
                "mechanics": manifest.groupby("mechanic").size().to_dict(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
