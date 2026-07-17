from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
R1_PATH = ROOT / "mt5-r1-uptrend-portability-v1" / "src" / "portability.py"


def _load_r1() -> Any:
    name = "xau_mt5_r1_portability_base_for_r1b"
    spec = importlib.util.spec_from_file_location(name, R1_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load R1 portability base from {R1_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


R1 = _load_r1()
run_portability = R1.run_portability
stage_metrics = R1.stage_metrics
evaluate_gate = R1.evaluate_gate
