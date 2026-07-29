from __future__ import annotations

import json
from pathlib import Path

from src.serving import LOCK_PATH, OUTPUTS, ROOT, sha256_file


FILES = [
    "PREREGISTRATION.md",
    "config/PROSPECTIVE_SERVING_V3.json",
    "capture_mt5_snapshot.py",
    "build_bundle.py",
    "run_parity.py",
    "src/__init__.py",
    "src/serving.py",
    "tests/test_serving.py",
]


def main() -> int:
    forbidden = [
        OUTPUTS / "MODEL_BUNDLE.joblib",
        OUTPUTS / "BUILD_AUDIT.json",
        OUTPUTS / "PARITY_RESULT.json",
    ]
    if any(path.exists() for path in forbidden):
        raise RuntimeError("A result exists; implementation cannot be relocked")
    lock = {
        "schema_version": (
            "codex_v60_portable_mature_topup_prospective_v3_implementation_lock"
        ),
        "locked_before_result": True,
        "files": {relative: sha256_file(ROOT / relative) for relative in FILES},
    }
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.write_text(
        json.dumps(lock, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(LOCK_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
