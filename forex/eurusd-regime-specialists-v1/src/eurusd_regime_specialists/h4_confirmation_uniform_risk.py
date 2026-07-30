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


def scale_uniformly(trades: pd.DataFrame, scale: float) -> pd.DataFrame:
    if not 0.0 < float(scale) <= 1.0:
        raise ValueError("Uniform risk scale must be in (0, 1]")
    result = trades.copy()
    for column in (
        "portfolio_risk_weight",
        "r",
        "stress_r",
        "pnl_usd_001_lot",
        "pnl_usd_001_lot_equivalent",
    ):
        if column in result:
            result[column] = result[column].astype(float) * float(scale)
    return result


def _render_report(result: dict[str, Any]) -> str:
    full = result["windows"]["FULL_AUDIT"]
    recent = result["windows"]["RECENT_2024H2_2026H1"]
    latest = result["windows"]["LATEST_6_MONTHS"]
    failed = [
        name for name, passed in result["gate_results"].items() if not passed
    ]
    return f"""# EURUSD H4 confirmation uniform-risk result

Status: **{result["status"]}**

| Window | Trades | Win rate | Payoff | PF | Net portfolio R | USD at scaled 0.01-lot equivalents |
|---|---:|---:|---:|---:|---:|---:|
| Full 2017-2026 | {full["trades"]} | {full["win_rate"]:.2%} | {full["realized_payoff_ratio"]:.3f} | {full["profit_factor"]:.3f} | {full["net_r"]:+.3f} | ${full["pnl_usd_001_lot"]:+.2f} |
| Recent 2024H2-2026H1 | {recent["trades"]} | {recent["win_rate"]:.2%} | {recent["realized_payoff_ratio"]:.3f} | {recent["profit_factor"]:.3f} | {recent["net_r"]:+.3f} | ${recent["pnl_usd_001_lot"]:+.2f} |
| Latest six months | {latest["trades"]} | {latest["win_rate"]:.2%} | {latest["realized_payoff_ratio"]:.3f} | {latest["profit_factor"]:.3f} | {latest["net_r"]:+.3f} | ${latest["pnl_usd_001_lot"]:+.2f} |

Frequency: {result["frequency"]["trades_per_fx_day"]:.3f} trades per FX day.
Maximum drawdown: {full["maximum_drawdown_r"]:.3f} scaled portfolio R.
0.5-pip stressed PF: {result["scenarios"]["COST_PLUS_0P5_PIP"]["profit_factor"]:.3f}.
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
    result_path = root / config["parent_result"]["path"]
    ledger_path = root / config["parent_trade_ledger"]["path"]
    if sha256_file(result_path) != config["parent_result"]["sha256"]:
        raise RuntimeError("Parent result checksum mismatch")
    if sha256_file(ledger_path) != config["parent_trade_ledger"]["sha256"]:
        raise RuntimeError("Parent trade-ledger checksum mismatch")
    parent = pd.read_csv(
        ledger_path,
        parse_dates=[
            "signal_time_utc",
            "entry_time_utc",
            "exit_time_utc",
        ],
    )
    if len(parent) != int(config["parent_trade_ledger"]["expected_rows"]):
        raise RuntimeError("Unexpected parent trade count")
    portfolio = scale_uniformly(parent, float(config["uniform_risk_scale"]))
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
    fx_days = 2476
    frequency = {
        "trades": len(portfolio),
        "fx_days": fx_days,
        "trades_per_fx_day": len(portfolio) / fx_days,
        "active_trade_days": int(
            portfolio["entry_time_utc"].dt.strftime("%Y-%m-%d").nunique()
        ),
    }
    gates = _gate_results(
        windows,
        scenarios,
        trade_bootstrap,
        calendar_bootstrap,
        frequency,
        config["admission"],
    )
    result = {
        "schema_version": "eurusd_h4_confirmation_uniform_risk_result_v1",
        "status": (
            "BACKTEST_GATES_PASSED_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if all(gates.values())
            else "REJECTED_H4_CONFIRMATION_UNIFORM_RISK"
        ),
        "demo_ready": False,
        "live_ready": False,
        "broker_action_allowed": False,
        "adaptive_historical_development_not_pristine_oos": True,
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "uniform_risk_scale": float(config["uniform_risk_scale"]),
        "concurrency": concurrency_audit(portfolio),
        "frequency": frequency,
        "windows": windows,
        "scenarios": scenarios,
        "trade_bootstrap": trade_bootstrap,
        "calendar_bootstrap": calendar_bootstrap,
        "latest_6_months_by_month": _latest_months(portfolio),
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
