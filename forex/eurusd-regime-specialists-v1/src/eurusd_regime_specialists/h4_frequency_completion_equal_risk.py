from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from .h4_chop_anchor_validation import (
    _scenario_summary,
    circular_block_bootstrap,
)
from .h4_dual_regime_portfolio_diagnostic import (
    apply_weighted_cost,
    circular_calendar_month_bootstrap,
    concurrency_audit,
)
from .neutral_h4_quiet_state_transfer import sha256_file
from .session_health_specialist_portfolio import (
    _gate_results,
    _latest_months,
    _windows,
)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def set_equal_trade_risk(
    trades: pd.DataFrame, target_risk_weight: float
) -> pd.DataFrame:
    if float(target_risk_weight) <= 0.0:
        raise ValueError("Target risk weight must be positive")
    current = trades["portfolio_risk_weight"].astype(float)
    if current.le(0.0).any():
        raise ValueError("Every parent trade must have positive risk")
    factor = float(target_risk_weight) / current
    result = trades.copy()
    for column in (
        "portfolio_risk_weight",
        "r",
        "stress_r",
        "pnl_usd_001_lot",
        "pnl_usd_001_lot_equivalent",
    ):
        if column == "portfolio_risk_weight":
            result[column] = float(target_risk_weight)
        elif column in result:
            result[column] = result[column].astype(float) * factor
    return result


def _render_report(result: dict[str, Any]) -> str:
    full = result["windows"]["FULL_AUDIT"]
    recent = result["windows"]["RECENT_2024H2_2026H1"]
    latest = result["windows"]["LATEST_6_MONTHS"]
    failed = [
        name for name, passed in result["gate_results"].items() if not passed
    ]
    cash = result["execution_cash_by_window"]
    return f"""# EURUSD H4 frequency-completion equal-risk result

Status: **{result["status"]}**

| Window | Trades | Win rate | Payoff | PF | Net portfolio R | 0.015-lot P&L | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full 2017-2026 | {full["trades"]} | {full["win_rate"]:.2%} | {full["realized_payoff_ratio"]:.3f} | {full["profit_factor"]:.3f} | {full["net_r"]:+.3f} | ${cash["FULL_AUDIT"]:+.2f} | {full["maximum_drawdown_r"]:.3f}R |
| Recent 2024H2-2026H1 | {recent["trades"]} | {recent["win_rate"]:.2%} | {recent["realized_payoff_ratio"]:.3f} | {recent["profit_factor"]:.3f} | {recent["net_r"]:+.3f} | ${cash["RECENT_2024H2_2026H1"]:+.2f} | {recent["maximum_drawdown_r"]:.3f}R |
| Latest six months | {latest["trades"]} | {latest["win_rate"]:.2%} | {latest["realized_payoff_ratio"]:.3f} | {latest["profit_factor"]:.3f} | {latest["net_r"]:+.3f} | ${cash["LATEST_6_MONTHS"]:+.2f} | {latest["maximum_drawdown_r"]:.3f}R |

Frequency: {result["frequency"]["trades_per_fx_day"]:.3f} trades per FX day.
Calendar coverage: {result["frequency"]["active_day_share"]:.2%}.
Equal risk per trade: {result["equal_trade_risk_weight"]:.3f}R.
0.1-lot reference equivalent: {result["execution"]["lot_per_trade"]:.3f} lot.
Maximum concurrent initial risk: {result["concurrency"]["maximum_concurrent_initial_risk_units"]:.3f}R.
0.5-pip stressed PF: {result["scenarios"]["COST_PLUS_0P5_PIP"]["profit_factor"]:.3f}.
1.0-pip stressed PF: {result["scenarios"]["COST_PLUS_1P0_PIP"]["profit_factor"]:.3f}.
Best-5%-removed PF: {full["top_5pct_winners_removed_profit_factor"]:.3f}.
Failed gates: {", ".join(failed) if failed else "none"}.

Adaptive historical research only; no broker orders are authorized.
"""


def run(
    config_path: Path, output_dir: Path
) -> tuple[dict[str, Any], pd.DataFrame]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    root = config_path.parent.parent
    result_path = root / config["rejected_parent_result"]["path"]
    ledger_path = root / config["immutable_parent_ledger"]["path"]
    for path, expected in (
        (result_path, config["rejected_parent_result"]["sha256"]),
        (ledger_path, config["immutable_parent_ledger"]["sha256"]),
    ):
        if sha256_file(path) != expected:
            raise RuntimeError(f"Checksum mismatch: {path}")
    parent_result = json.loads(result_path.read_text(encoding="utf-8"))
    if parent_result["status"] != config["rejected_parent_result"][
        "expected_status"
    ]:
        raise RuntimeError("Unexpected parent result status")
    if not parent_result["gate_results"][
        "all_added_components_standalone_qualified"
    ]:
        raise RuntimeError("Parent added components did not qualify")

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
    identity_columns = [
        "specialist_id",
        "portfolio_sleeve",
        "signal_time_utc",
        "entry_time_utc",
        "exit_time_utc",
        "side",
    ]
    identity_before = parent[identity_columns].copy()
    portfolio = set_equal_trade_risk(
        parent, float(config["equal_trade_risk_weight"])
    )
    if not identity_before.equals(portfolio[identity_columns]):
        raise RuntimeError("Equal-risk policy changed trade identity")

    windows = _windows(portfolio, config["reporting_windows"])
    scenarios = {
        "COST_PLUS_0P5_PIP": _scenario_summary(
            apply_weighted_cost(portfolio, 0.5)
        ),
        "COST_PLUS_1P0_PIP": _scenario_summary(
            apply_weighted_cost(portfolio, 1.0)
        ),
    }
    bootstrap = config["bootstrap"]
    trade_bootstrap = circular_block_bootstrap(
        portfolio["r"].to_numpy(dtype=float),
        samples=int(bootstrap["samples"]),
        block_trades=int(bootstrap["trade_block_trades"]),
        seed=int(bootstrap["seed"]),
        lower_quantile=float(bootstrap["lower_quantile"]),
    )
    start, end = map(pd.Timestamp, config["evaluation_window"])
    calendar_bootstrap = circular_calendar_month_bootstrap(
        portfolio,
        start=start,
        end=end,
        samples=int(bootstrap["samples"]),
        block_months=int(bootstrap["calendar_block_months"]),
        seed=int(bootstrap["seed"]),
        lower_quantile=float(bootstrap["lower_quantile"]),
    )
    fx_days = int(parent_result["frequency"]["fx_days"])
    active_days = int(
        portfolio["entry_time_utc"].dt.strftime("%Y-%m-%d").nunique()
    )
    frequency = {
        "trades": len(portfolio),
        "fx_days": fx_days,
        "trades_per_fx_day": len(portfolio) / fx_days,
        "active_trade_days": active_days,
        "active_day_share": active_days / fx_days,
        "trades_per_active_day": len(portfolio) / active_days,
    }
    gates = _gate_results(
        windows,
        scenarios,
        trade_bootstrap,
        calendar_bootstrap,
        frequency,
        config["admission"],
    )
    concurrence = concurrency_audit(portfolio)
    gates["maximum_concurrent_initial_risk"] = (
        concurrence["maximum_concurrent_initial_risk_units"]
        <= float(
            config["risk_limits"][
                "maximum_concurrent_initial_risk_units"
            ]
        )
    )
    lot = float(config["execution"]["reference_full_risk_lot"]) * float(
        config["equal_trade_risk_weight"]
    )
    cash_multiplier = (
        float(config["execution"]["reference_full_risk_lot"]) / 0.01
    )
    gates["minimum_executable_lot"] = lot >= float(
        config["execution"]["minimum_broker_lot"]
    )
    gates["all_parent_components_standalone_qualified"] = True
    status = (
        "BACKTEST_FREQUENCY_AND_EDGE_GATES_PASSED"
        if all(gates.values())
        else "REJECTED_H4_FREQUENCY_COMPLETION_EQUAL_RISK"
    )
    result = {
        "schema_version": (
            "eurusd_h4_frequency_completion_equal_risk_result_v1"
        ),
        "status": status,
        "demo_ready": False,
        "live_ready": False,
        "broker_action_allowed": False,
        "adaptive_historical_development_not_pristine_oos": True,
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "parent_result_sha256": sha256_file(result_path),
        "parent_ledger_sha256": sha256_file(ledger_path),
        "trade_identity_unchanged": True,
        "equal_trade_risk_weight": float(
            config["equal_trade_risk_weight"]
        ),
        "execution": {
            "reference_full_risk_lot": float(
                config["execution"]["reference_full_risk_lot"]
            ),
            "lot_per_trade": lot,
            "minimum_broker_lot": float(
                config["execution"]["minimum_broker_lot"]
            ),
            "cash_multiplier_from_weighted_001_lot_field": cash_multiplier,
        },
        "concurrency": concurrence,
        "frequency": frequency,
        "windows": windows,
        "scenarios": scenarios,
        "trade_bootstrap": trade_bootstrap,
        "calendar_bootstrap": calendar_bootstrap,
        "latest_6_months_by_month": _latest_months(portfolio),
        "execution_cash_by_window": {
            name: float(summary["pnl_usd_001_lot"]) * cash_multiplier
            for name, summary in windows.items()
        },
        "latest_6_months_execution_cash_by_month": {
            row["month"]: float(row["pnl_usd_001_lot"])
            * cash_multiplier
            for row in _latest_months(portfolio)
        },
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
        _render_report(result), encoding="utf-8", newline="\n"
    )
    return result, portfolio
