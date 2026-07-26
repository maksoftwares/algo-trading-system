from __future__ import annotations

import json
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
sys.path.insert(0, str(PACKAGE / "src"))

from step_4_runner import run_step_4  # noqa: E402


if __name__ == "__main__":
    result = run_step_4(
        REPO,
        PACKAGE,
        PACKAGE / "config/step_4_model_evaluation_contract_v1.json",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
