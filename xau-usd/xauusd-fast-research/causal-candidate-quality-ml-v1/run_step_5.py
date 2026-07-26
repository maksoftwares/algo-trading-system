from __future__ import annotations

import json
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
sys.path.insert(0, str(PACKAGE / "src"))

from step_5_runner import run_step_5  # noqa: E402


def main() -> None:
    result = run_step_5(
        repo_root=REPO,
        package_root=PACKAGE,
        config_path=PACKAGE
        / "config"
        / "step_5_shared_account_portfolio_contract_v1.json",
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
