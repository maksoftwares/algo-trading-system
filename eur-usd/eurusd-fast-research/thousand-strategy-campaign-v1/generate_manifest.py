from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs" / "EURUSD_HUNT_V1_ARTIFACT_MANIFEST.json"


def main() -> int:
    artifacts = []
    for path in sorted(ROOT.rglob("*")):
        if (
            not path.is_file()
            or path == OUTPUT
            or "__pycache__" in path.parts
            or ".pytest_cache" in path.parts
        ):
            continue
        data = path.read_bytes()
        artifacts.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    payload = {
        "schema_version": "eurusd_hunt_v1_artifact_manifest",
        "status": "NO_DISCOVERY_SURVIVOR_STOP_V1",
        "artifacts": artifacts,
    }
    OUTPUT.write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Frozen {len(artifacts)} EURUSD hunt artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
