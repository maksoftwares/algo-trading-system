from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT
    / "EURUSD_PROSPECTIVE_MULTISYMBOL_COLLECTOR_MANIFEST_2026_07_30.sha256.json"
)


def included_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path != OUTPUT
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    ]


def main() -> None:
    files = {}
    for path in sorted(included_files()):
        relative = path.relative_to(ROOT).as_posix()
        files[relative] = {
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    payload = {
        "artifact": "EURUSD_PROSPECTIVE_MULTISYMBOL_COLLECTOR_V1",
        "generated_on": "2026-07-30",
        "files": files,
    }
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
