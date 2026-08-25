from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "run_forward_horizon_audit.py"


def load_script():
    spec = importlib.util.spec_from_file_location("forward_horizon_audit_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_poisson_horizon_reaches_requested_probability() -> None:
    module = load_script()
    mean = module.poisson_mean_for_probability(10, 0.90)
    assert module.poisson_probability_at_least(10, mean) >= 0.90
    assert module.poisson_probability_at_least(10, mean - 1e-6) < 0.90


def test_component_horizon_uses_observed_event_rate() -> None:
    module = load_script()
    result = module.component_horizon(
        observed_events=10,
        observed_trades=1000,
        required_events=20,
        annual_trades=250.0,
    )
    assert math.isclose(result["event_rate_per_trade"], 0.01)
    assert math.isclose(result["expected_trades_to_required_events"], 2000.0)
    assert math.isclose(result["expected_years_to_required_events"], 8.0)


def test_committed_horizon_report_keeps_exposed_august_separate() -> None:
    report = json.loads(
        (ROOT / "FORWARD_COMPONENT_HORIZON_AUDIT.json").read_text(encoding="utf-8")
    )
    anti = report["historical_rate_scenarios"][
        "v57_weak_followthrough_anti_chase"
    ]
    exposed = report["exposed_august_diagnostic"]
    assert anti["observed_events"] == 1
    assert exposed["anti_chase_events"] == 3
    assert exposed["selection_contaminated"] is True
    assert report["pooled_historical_plus_exposed_anti_chase_scenario"][
        "not_usable_for_authorization"
    ]
    assert report["deployment_authorized"] is False
    assert all(len(value) == 64 for value in report["input_sha256"].values())
