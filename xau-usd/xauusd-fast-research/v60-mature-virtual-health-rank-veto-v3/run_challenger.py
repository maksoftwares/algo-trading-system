from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG = ROOT / "config" / "challenger.json"
EVALUATOR = REPO_ROOT / "xau-usd" / "xauusd-fast-research" / "v60-v57-degraded-rank-veto-v1" / "src" / "evaluate.py"


def main() -> int:
    spec = importlib.util.spec_from_file_location("mature_virtual_health_evaluator", EVALUATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load evaluator: {EVALUATOR}")
    evaluator = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = evaluator
    spec.loader.exec_module(evaluator)
    result, annual, vetoes = evaluator.run(CONFIG)
    evaluator.write_outputs(result, annual, vetoes, ROOT / "outputs")
    print(result["decision"])
    return 0 if result["decision"].startswith("HISTORICAL_CHALLENGER_PASSES") else 2


if __name__ == "__main__":
    raise SystemExit(main())
