from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "ARTIFACT_MANIFEST.csv"
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache"}
LF_NORMALIZED_SUFFIXES = {".csv", ".ini", ".json", ".md", ".mq5", ".py", ".set"}


def repository_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if path.suffix.casefold() in LF_NORMALIZED_SUFFIXES:
        return data.replace(b"\r\n", b"\n")
    return data


def main() -> None:
    rows = []
    paths = [path for path in ROOT.rglob("*") if path.is_file() and path != OUTPUT]
    for path in sorted(
        paths,
        key=lambda value: value.relative_to(ROOT).as_posix().casefold(),
    ):
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        # Git stores the package's text artifacts with LF endings. Hash that
        # canonical representation so manifests generated on Windows and Linux
        # remain identical even when a local checkout uses CRLF.
        data = repository_bytes(path)
        rows.append(
            {
                "path": relative.as_posix(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("path", "bytes", "sha256"), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} artifacts -> {OUTPUT}")


if __name__ == "__main__":
    main()
