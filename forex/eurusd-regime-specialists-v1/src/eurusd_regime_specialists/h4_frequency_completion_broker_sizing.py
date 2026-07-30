from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from .h4_chop_anchor_validation import _scenario_summary
from .h4_dual_regime_portfolio_diagnostic import (
    apply_weighted_cost,
    concurrency_audit,
)
from .h4_frequency_completion_equal_risk import set_equal_trade_risk
from .neutral_h4_quiet_state_transfer import sha256_file
from .session_health_specialist_portfolio import _windows


IDENTITY_COLUMNS = [
    "specialist_id",
    "portfolio_sleeve",
    "signal_time_utc",
    "entry_time_utc",
    "exit_time_utc",
    "side",
    "entry",
    "stop",
    "target",
    "exit",
    "exit_reason",
]


def is_legal_volume(
    lot: float,
    minimum: float,
    maximum: float,
    step: float,
) -> bool:
    if minimum <= 0.0 or maximum < minimum or step <= 0.0:
        return False
    if lot < minimum - 1e-12 or lot > maximum + 1e-12:
        return False
    units = lot / step
    return math.isclose(units, round(units), abs_tol=1e-10)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _render(result: dict[str, Any]) -> str:
    full = result["windows"]["FULL_AUDIT"]
    recent = result["windows"]["RECENT_2024H2_2026H1"]
    latest12 = result["windows"]["LATEST_12_MONTHS"]
    latest6 = result["windows"]["LATEST_6_MONTHS"]
    cash = result["execution_cash_by_window"]
    return f"""# EURUSD H4 broker-executable sizing lock

Status: **{result["status"]}**

The 2,532 frozen trade identities are unchanged. The earlier 0.015-lot
interpretation is not on Capital.com's observed 0.01 lot grid, so the executable
contract is uniformly reduced to 0.01 lot per trade.

| Window | Trades | Win rate | Payoff | PF | Net R | 0.01-lot P&L |
|---|---:|---:|---:|---:|---:|---:|
| Full 2017-2026 | {full["trades"]} | {full["win_rate"]:.2%} | {full["realized_payoff_ratio"]:.3f} | {full["profit_factor"]:.3f} | {full["net_r"]:+.3f} | ${cash["FULL_AUDIT"]:+.2f} |
| Recent 2024H2-2026H1 | {recent["trades"]} | {recent["win_rate"]:.2%} | {recent["realized_payoff_ratio"]:.3f} | {recent["profit_factor"]:.3f} | {recent["net_r"]:+.3f} | ${cash["RECENT_2024H2_2026H1"]:+.2f} |
| Latest 12 months | {latest12["trades"]} | {latest12["win_rate"]:.2%} | {latest12["realized_payoff_ratio"]:.3f} | {latest12["profit_factor"]:.3f} | {latest12["net_r"]:+.3f} | ${cash["LATEST_12_MONTHS"]:+.2f} |
| Latest 6 months | {latest6["trades"]} | {latest6["win_rate"]:.2%} | {latest6["realized_payoff_ratio"]:.3f} | {latest6["profit_factor"]:.3f} | {latest6["net_r"]:+.3f} | ${cash["LATEST_6_MONTHS"]:+.2f} |

Lot grid: minimum {result["execution"]["broker_volume_minimum"]:.2f},
step {result["execution"]["broker_volume_step"]:.2f}, selected
{result["execution"]["lot_per_trade"]:.2f}.
Maximum concurrent positions/risk:
{result["concurrency"]["maximum_concurrent_positions"]} /
{result["concurrency"]["maximum_concurrent_initial_risk_units"]:.2f}R.

This locks research sizing only. It does not authorize demo or live orders.
"""


def run(
    config_path: Path,
    output_dir: Path,
) -> tuple[dict[str, Any], pd.DataFrame]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    root = config_path.parent.parent
    result_path = root / config["passed_parent_result"]["path"]
    ledger_path = root / config["immutable_parent_ledger"]["path"]
    for path, expected in (
        (result_path, config["passed_parent_result"]["sha256"]),
        (ledger_path, config["immutable_parent_ledger"]["sha256"]),
    ):
        if sha256_file(path) != expected:
            raise RuntimeError(f"Checksum mismatch: {path}")
    parent_result = json.loads(result_path.read_text(encoding="utf-8"))
    if (
        parent_result["status"]
        != config["passed_parent_result"]["expected_status"]
        or not all(parent_result["gate_results"].values())
    ):
        raise RuntimeError("The frozen parent did not pass every research gate")
    parent = pd.read_csv(
        ledger_path,
        parse_dates=[
            "signal_time_utc",
            "entry_time_utc",
            "exit_time_utc",
        ],
    )
    if len(parent) != int(config["immutable_parent_ledger"]["expected_rows"]):
        raise RuntimeError("Unexpected immutable parent row count")
    identity = parent[IDENTITY_COLUMNS].copy()
    risk = float(config["research_risk_weight_per_trade"])
    portfolio = set_equal_trade_risk(parent, risk)
    identity_unchanged = identity.equals(portfolio[IDENTITY_COLUMNS])
    if not identity_unchanged:
        raise RuntimeError("Broker sizing changed trade identity")
    execution = config["execution"]
    lot = float(execution["reference_full_risk_lot"]) * risk
    legal = is_legal_volume(
        lot,
        float(execution["broker_volume_minimum"]),
        float(execution["broker_volume_maximum"]),
        float(execution["broker_volume_step"]),
    )
    windows = _windows(portfolio, config["reporting_windows"])
    scenarios = {
        "COST_PLUS_0P5_PIP": _scenario_summary(
            apply_weighted_cost(portfolio, 0.5)
        ),
        "COST_PLUS_1P0_PIP": _scenario_summary(
            apply_weighted_cost(portfolio, 1.0)
        ),
    }
    concurrence = concurrency_audit(portfolio)
    parent_windows = parent_result["windows"]
    pf_invariant = all(
        math.isclose(
            float(windows[name]["profit_factor"]),
            float(parent_windows[name]["profit_factor"]),
            rel_tol=1e-12,
            abs_tol=1e-12,
        )
        for name in windows
    )
    gates = {
        "parent_research_gates_all_passed": all(
            parent_result["gate_results"].values()
        ),
        "all_2532_trade_identities_unchanged": identity_unchanged,
        "profit_factor_invariant_under_uniform_scaling": pf_invariant,
        "exact_required_lot": math.isclose(
            lot,
            float(execution["required_lot_per_trade"]),
            abs_tol=1e-12,
        ),
        "broker_volume_grid_legal": legal,
        "maximum_concurrent_positions": (
            int(concurrence["maximum_concurrent_positions"])
            <= int(config["risk_limits"]["maximum_concurrent_positions"])
        ),
        "maximum_concurrent_initial_risk": (
            float(concurrence["maximum_concurrent_initial_risk_units"])
            <= float(
                config["risk_limits"][
                    "maximum_concurrent_initial_risk_units"
                ]
            )
            + 1e-12
        ),
    }
    cash_multiplier = (
        float(execution["reference_full_risk_lot"]) / 0.01
    )
    result = {
        "schema_version": (
            "eurusd_h4_frequency_completion_broker_sizing_result_v1"
        ),
        "status": (
            "BROKER_SIZING_AND_RESEARCH_EDGE_LOCKED"
            if all(gates.values())
            else "BROKER_SIZING_REJECTED"
        ),
        "demo_ready": False,
        "live_ready": False,
        "broker_action_allowed": False,
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "parent_result_sha256": sha256_file(result_path),
        "parent_ledger_sha256": sha256_file(ledger_path),
        "execution": {
            "reference_full_risk_lot": float(
                execution["reference_full_risk_lot"]
            ),
            "lot_per_trade": lot,
            "broker_volume_minimum": float(
                execution["broker_volume_minimum"]
            ),
            "broker_volume_maximum": float(
                execution["broker_volume_maximum"]
            ),
            "broker_volume_step": float(execution["broker_volume_step"]),
            "cash_multiplier_from_weighted_001_lot_field": cash_multiplier,
        },
        "research_risk_weight_per_trade": risk,
        "trade_identity_unchanged": identity_unchanged,
        "frequency": parent_result["frequency"],
        "concurrency": concurrence,
        "windows": windows,
        "scenarios": scenarios,
        "execution_cash_by_window": {
            name: float(summary["pnl_usd_001_lot"]) * cash_multiplier
            for name, summary in windows.items()
        },
        "inherited_trade_bootstrap": parent_result["trade_bootstrap"],
        "inherited_calendar_bootstrap": parent_result["calendar_bootstrap"],
        "gate_results": gates,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    portfolio.to_csv(output_dir / "TRADES.csv", index=False)
    (output_dir / "RESULT.json").write_text(
        json.dumps(_json_safe(result), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "RESULT.md").write_text(
        _render(result),
        encoding="utf-8",
        newline="\n",
    )
    return result, portfolio
