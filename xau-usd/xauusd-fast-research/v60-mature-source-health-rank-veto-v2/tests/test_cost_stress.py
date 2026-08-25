from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "run_cost_stress.py"


def load_script():
    spec = importlib.util.spec_from_file_location("v60_v2_cost_stress_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load cost-stress script: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_cost_levels_include_unstressed_and_severe_cases() -> None:
    module = load_script()
    assert module.COST_LEVELS_USD == (0.0, 0.10, 0.20, 0.25, 0.50, 1.00)


def test_comparative_gate_excludes_frozen_dollar_identity_only() -> None:
    module = load_script()
    gates = {name: True for name in module.COMPARATIVE_GATE_NAMES}
    assert module.comparative_gates_pass(gates)
    gates["recent_windows_not_worse"] = False
    assert not module.comparative_gates_pass(gates)
