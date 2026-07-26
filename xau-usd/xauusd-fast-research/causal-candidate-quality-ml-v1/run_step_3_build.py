from __future__ import annotations

import json
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[2]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from step_3_dataset import run_step_3  # noqa: E402


def main() -> None:
    config_path = PACKAGE_ROOT / "config" / "step_3_build_v1.json"
    result = run_step_3(REPO_ROOT, PACKAGE_ROOT, config_path)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
