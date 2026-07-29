from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOCK_PATH = ROOT / "config" / "IMPLEMENTATION_LOCK.json"
FILES = [
    ROOT / "PREREGISTRATION.md",
    ROOT / "config" / "PORTABLE_MATURE_TOPUP_V2.json",
    ROOT / "run_experiment.py",
    ROOT / "src" / "__init__.py",
    ROOT / "src" / "experiment.py",
    ROOT / "tests" / "test_experiment.py",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    payload = {
        "schema_version": "codex_v60_portable_mature_topup_v2_implementation_lock",
        "locked_before_result": not (ROOT / "outputs" / "RESULT.json").exists(),
        "files": {
            str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path)
            for path in FILES
        },
    }
    LOCK_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

