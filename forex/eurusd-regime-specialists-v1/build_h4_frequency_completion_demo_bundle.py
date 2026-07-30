from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.h4_frequency_completion_demo_bundle import (
    build_bundle,
)


def main() -> None:
    result = build_bundle(
        ROOT
        / "config"
        / "frozen_h4_frequency_completion_demo_bundle_v1.json",
        ROOT / "outputs" / "h4_frequency_completion_demo_bundle",
    )
    print(
        json.dumps(
            {
                "status": result.status,
                "archive_path": str(result.archive_path),
                "archive_sha256": result.archive_sha256,
                "manifest_path": str(result.manifest_path),
                "manifest_sha256": result.manifest_sha256,
                "file_count": result.file_count,
                "deployment_performed": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
