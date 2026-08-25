from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG = ROOT / "config" / "experiment.json"
OUTPUTS = ROOT / "outputs"
RUNNER = REPO_ROOT / "xau-usd/xauusd-fast-research/v60-dynamic-followthrough-union-v6/run_experiment.py"


def main() -> int:
    spec = importlib.util.spec_from_file_location("v60_dynamic_v7_runner", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load dynamic runner: {RUNNER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["v60_dynamic_v7_runner"] = module
    spec.loader.exec_module(module)
    module.CONFIG = CONFIG
    module.OUTPUTS = OUTPUTS
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
