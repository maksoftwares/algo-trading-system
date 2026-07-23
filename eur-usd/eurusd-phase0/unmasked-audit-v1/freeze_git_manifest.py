from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
MANIFEST = ROOT / "outputs" / "locked" / "ARTIFACT_MANIFEST.json"


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=REPO)


def main() -> int:
    prefix = ROOT.relative_to(REPO).as_posix()
    paths = [
        line
        for line in git("ls-files", "--cached", "--", prefix).decode("utf-8").splitlines()
        if line and line != MANIFEST.relative_to(REPO).as_posix()
    ]
    artifacts = []
    for path in sorted(paths):
        data = git("show", f":{path}")
        artifacts.append(
            {
                "path": path,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    payload = {
        "schema_version": "eurusd_v1_unmasked_artifact_manifest_v1",
        "hash_basis": "Git index blob bytes; stable after clean checkout",
        "candidate_id": "EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1_UNMASKED_AUDIT",
        "artifacts": artifacts,
    }
    MANIFEST.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"{len(artifacts)} staged artifacts frozen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
