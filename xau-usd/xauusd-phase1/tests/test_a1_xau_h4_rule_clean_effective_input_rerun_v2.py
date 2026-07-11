from __future__ import annotations

import importlib.util
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
RUNNER = SCRIPTS / "run_a1_xau_h4_rule_clean_effective_input_rerun_v2.py"


def load():
    spec = importlib.util.spec_from_file_location("run_a1_xau_h4_rule_clean_effective_input_rerun_v2", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


R = load()


def test_runner_is_single_locked_rule_clean_cell() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "variant=h4.VARIANTS[1]" in text
    assert "for horizon in h4.extended.HORIZONS" in text
    assert "R6" not in text
    assert R.RISK_USD == 25.0
    assert R.EXPECTED_COST_R == 0.05
    assert R.HARD_COST_R == 0.10
    assert R.BOOTSTRAP_DRAWS == 10_000


def test_exit_buckets_are_july_to_june() -> None:
    assert R.exit_bucket(datetime(2020, 7, 1)) == 2020
    assert R.exit_bucket(datetime(2021, 6, 30)) == 2020
    assert R.exit_bucket(datetime(2021, 7, 1)) == 2021


def test_metric_rows_apply_locked_r_cost() -> None:
    rows = [{"pnl_usd": 50.0}, {"pnl_usd": -25.0}]
    native = R.metric_rows(rows)
    hard = R.metric_rows(rows, 0.10)
    assert native["net_usd"] == 25.0
    assert native["profit_factor"] == 2.0
    assert native["expectancy_r"] == 0.5
    assert hard["net_usd"] == 20.0
    assert hard["profit_factor"] == 1.727273
    assert hard["expectancy_r"] == 0.4


def test_small_account_feasibility_never_invents_blocked_profit() -> None:
    orders = [
        {"action": "ORDER_SEND_OK", "reason": "pass", "stop_points": "200"},
        {"action": "GUARD_BLOCK", "reason": "minimum_lot_risk_excess", "stop_points": "800"},
        {"action": "GUARD_BLOCK", "reason": "spread_too_high", "stop_points": "100"},
    ]
    evidence = R.small_account_feasibility(orders)
    row_025 = next(row for row in evidence["rows"] if row["risk_pct"] == 0.25)
    row_1 = next(row for row in evidence["rows"] if row["risk_pct"] == 1.0)
    assert row_025["candidate_events"] == 2
    assert row_025["executable_at_0p01"] == 1
    assert row_1["executable_at_0p01"] == 2


def test_evidence_failure_has_priority_over_economic_result() -> None:
    base = {
        "horizon": "five_year",
        "effective_input_verification": {"status": "EFFECTIVE_INPUTS_MISMATCH"},
        "legacy_mask_block_count": 0,
        "order_failure_count": 0,
        "management_failure_count": 0,
        "exposure": {"maximum_simultaneous_positions": 1, "maximum_aggregate_initial_risk_usd": 25.0},
        "startup_contract": {},
        "native": {"trades": 120, "net_usd": 100.0, "profit_factor": 2.0},
        "hard_stress_0p10r": {"profit_factor": 1.5, "expectancy_r": 0.1},
        "maximum_relative_equity_drawdown_pct": 5.0,
        "robustness": {},
        "small_account_feasibility": {"rows": []},
    }
    ten = {
        **base,
        "horizon": "ten_year",
        "robustness": {
            "bootstrap": {"expectancy_r_p05": 0.1, "profit_factor_p05": 1.1},
            "top10_winning_trades_removed": {"net_usd": 1.0},
            "top3_winning_entry_days_removed": {"net_usd": 1.0},
            "positive_annual_buckets": 10,
            "early_half": {"net_usd": 1.0},
            "late_half": {"net_usd": 1.0},
            "best_year_share_pct": 20.0,
            "best_24_month_share_pct": 30.0,
        },
        "small_account_feasibility": {"rows": [{"risk_pct": 0.25, "all_candidates_executable": True}]},
    }
    assert R.evaluate([base, ten])["status"] == "H4_EVIDENCE_INVALID"


def test_cli_has_no_broker_action_surface() -> None:
    destinations = {action.dest for action in R.build_parser()._actions}
    assert destinations.isdisjoint({"live", "demo", "attach", "profile", "account", "server"})
