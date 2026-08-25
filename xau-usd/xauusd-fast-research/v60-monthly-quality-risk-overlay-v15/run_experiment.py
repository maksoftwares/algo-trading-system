from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG = ROOT / "config" / "experiment.json"
OUTPUTS = ROOT / "outputs"


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    runner = REPO_ROOT / config["inputs"]["v14_runner"]["path"]
    spec = importlib.util.spec_from_file_location("v15_shared_runner", runner)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load V14 runner: {runner}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.ROOT = ROOT
    module.REPO_ROOT = REPO_ROOT
    module.CONFIG = CONFIG
    module.OUTPUTS = OUTPUTS
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
