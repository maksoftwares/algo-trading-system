from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from src.frequency_v2 import (
    FrequencyCandidate,
    load_capital_m15,
    metrics,
    route_portfolio,
    simulate,
)

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "eurusd_frequency_v2_frozen_portfolio.json"


def passes(metrics_row: dict, config: dict) -> bool:
    gate = config["gates"]
    return bool(
        metrics_row["trades_per_active_day"] >= gate["minimum_trades_per_active_day"]
        and metrics_row["profit_factor"] >= gate["minimum_profit_factor"]
        and metrics_row["win_rate"] >= gate["minimum_win_rate"]
        and metrics_row["maximum_drawdown_r"] <= gate["maximum_drawdown_r"]
        and metrics_row["positive_active_month_share"]
        >= gate["minimum_positive_active_month_share"]
        and metrics_row["top_5pct_removed_profit_factor"]
        >= gate["minimum_top_5pct_removed_profit_factor"]
    )


def main() -> None:
    config_bytes = CONFIG_PATH.read_bytes()
    config = json.loads(config_bytes)
    source = Path(config["source"])
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    if source_sha256 != config["source_sha256"]:
        raise RuntimeError("Capital.com M15 source checksum mismatch")
    regime_config = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2.json").read_text()
    )["regime_classifier"]
    frame, _ = load_capital_m15(source, regime_config)
    specialists = {
        row["candidate_id"]: FrequencyCandidate(**row) for row in config["specialists"]
    }
    if list(specialists) != config["priority"]:
        raise RuntimeError("Specialist order must exactly match frozen priority")

    output = ROOT / "outputs" / "frequency_v2_frozen"
    output.mkdir(parents=True, exist_ok=True)
    all_metrics = []
    stage_verdicts = {}
    for stage, bounds in config["windows"].items():
        start, end = (pd.Timestamp(value) for value in bounds)
        active_days = int(
            frame.loc[
                (frame["timestamp"] >= start) & (frame["timestamp"] < end),
                "active_date",
            ].nunique()
        )
        streams = {
            candidate_id: simulate(
                frame,
                candidate,
                start,
                end,
                maximum_trades_per_day=config["maximum_trades_per_active_day"],
                entry_slippage_points=config["entry_slippage_points"],
                exit_slippage_points=config["exit_slippage_points"],
            )
            for candidate_id, candidate in specialists.items()
        }
        portfolio = route_portfolio(
            streams,
            config["priority"],
            maximum_trades_per_day=config["maximum_trades_per_active_day"],
        )
        result = metrics(portfolio, active_days)
        result.update({"stage": stage, "active_days": active_days})
        all_metrics.append(result)
        pd.DataFrame(portfolio).to_csv(
            output / f"{stage.upper()}_TRADES.csv", index=False
        )
        contributors = {
            candidate_id: sum(
                trade["candidate_id"] == candidate_id for trade in portfolio
            )
            for candidate_id in config["priority"]
        }
        stage_verdicts[stage] = {
            "metrics": result,
            "contributors": contributors,
            "gate_pass": passes(result, config),
        }

    pd.DataFrame(all_metrics).to_csv(output / "STAGE_METRICS.csv", index=False)
    validation_pass = stage_verdicts["validation"]["gate_pass"]
    exam_pass = stage_verdicts["adaptive_demo_exam"]["gate_pass"]
    verdict = {
        "schema_version": "eurusd_frequency_v2_frozen_result_v1",
        "portfolio_id": config["portfolio_id"],
        "selection_status": config["selection_status"],
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_sha256": source_sha256,
        "history_quality_pct": 99,
        "maximum_open_positions": config["maximum_open_positions"],
        "maximum_trades_per_active_day": config["maximum_trades_per_active_day"],
        "distinct_regimes": len({row["regime"] for row in config["specialists"]}),
        "stages": stage_verdicts,
        "validation_gate_pass": validation_pass,
        "adaptive_demo_exam_gate_pass": exam_pass,
        "mt5_real_tick_replication_opened": False,
        "demo_ready": False,
        "verdict": (
            "OPEN_MT5_REAL_TICK_REPLICATION"
            if validation_pass and exam_pass
            else "FROZEN_PORTFOLIO_FAILED_CONTINUE_RESEARCH"
        ),
    }
    (output / "VERDICT.json").write_text(
        json.dumps(verdict, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
