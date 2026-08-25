import ast
from pathlib import Path

import pandas as pd
import pytest

import run_evaluation as runner


ROOT = Path(__file__).resolve().parents[1]


def test_package_has_no_broker_order_authority() -> None:
    for path in (ROOT / "run_evaluation.py", ROOT / "src" / "capacity.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [alias.name.lower() for alias in node.names]
                assert "metatrader5" not in names
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr.lower() not in {
                    "order_send",
                    "position_close",
                    "trade",
                }


def test_config_is_read_only_and_all_dependencies_match() -> None:
    config = runner.read_json(runner.CONFIG)
    runner.validate_config(config)
    assert config["authorization"] == {
        "read_only_inputs": True,
        "broker_actions": False,
        "runtime_changes": False,
        "demo_deployment": False,
        "live_deployment": False,
    }


def test_completed_months_excludes_boundary_and_open_months() -> None:
    boundary = pd.Timestamp("2026-08-26T00:00:00Z")
    cutoff = int(pd.Timestamp("2026-10-15T00:00:00Z").value // 1_000_000)
    assert runner.completed_months(boundary, cutoff) == ["2026-09"]


def test_state_self_hash_detects_tampering(tmp_path: Path) -> None:
    boundary = pd.Timestamp("2026-08-26T00:00:00Z")
    state = runner.initial_state(boundary, "contract")
    state["state_sha256"] = runner.state_sha256(state)
    path = tmp_path / "STATE.json"
    runner.atomic_write(path, __import__("json").dumps(state))
    loaded = runner.load_state(path, boundary, "contract")
    assert loaded["run_sequence"] == 0

    loaded["run_sequence"] = 99
    runner.atomic_write(path, __import__("json").dumps(loaded))
    with pytest.raises(ValueError, match="self-hash"):
        runner.load_state(path, boundary, "contract")


def test_comparative_gates_handle_no_loss_profit_factor() -> None:
    metrics = {
        "net_pnl_usd": 1.0,
        "profit_factor": None,
        "gross_profit_usd": 1.0,
        "maximum_lifetime_closed_drawdown_usd": 0.0,
        "maximum_lifetime_equity_drawdown_usd": 0.0,
        "open_positions_at_end": 0,
    }
    result = {
        "baseline": {**metrics, "net_pnl_usd": 0.5},
        "challenger": metrics,
        "baseline_accepted_ids": ["a"],
        "common_accepted_ids": ["a"],
        "baseline_monthly_pnl_usd": {},
        "challenger_monthly_pnl_usd": {},
        "baseline_monthly_downside": {
            "negative_month_pnl_usd": 0.0,
            "worst_month_pnl_usd": 0.0,
        },
        "challenger_monthly_downside": {
            "negative_month_pnl_usd": 0.0,
            "worst_month_pnl_usd": 0.0,
        },
    }
    gates = runner.comparative_gates(result, {"minimum_trade_retention": 0.99})
    assert all(gates.values())
