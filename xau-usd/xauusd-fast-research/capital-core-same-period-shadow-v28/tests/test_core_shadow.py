from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "core_shadow.py"


def _load_module():
    name = "capital_core_shadow_v28_test"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_candidate_id_is_contract_bound_and_deterministic() -> None:
    module = _load_module()
    first = module._candidate_id("source", "contract-a")
    second = module._candidate_id("source", "contract-a")
    changed = module._candidate_id("source", "contract-b")

    assert first == second
    assert first != changed


def test_empty_candidate_schema_is_stable() -> None:
    module = _load_module()

    assert tuple(pd.DataFrame(columns=module.CANDIDATE_COLUMNS).columns) == (
        module.CANDIDATE_COLUMNS
    )


def test_runner_has_no_execution_surface() -> None:
    runner = (ROOT / "run_shadow.py").read_text(encoding="utf-8")
    source = MODULE_PATH.read_text(encoding="utf-8")
    forbidden = ("order_send", "order_check", "TRADE_ACTION_", "CTrade")
    for token in forbidden:
        assert token not in runner
        assert token not in source
    assert '"trade_permission": False' in source
    assert '"broker_action_allowed": False' in source
    assert '"python_execution_authorized": False' in source
