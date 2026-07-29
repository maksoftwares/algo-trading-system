from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from eurusd_regime_specialists.neutral_specialist_agreement_execution import (
    _quarantine_overlap,
    attach_oracle_matches,
    load_eurusd_m5,
    payoff_metrics,
    remove_top_winners,
    simulate_one,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_rate_differential_execution.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_RATE_DIFFERENTIAL_EXECUTION_PREREG_"
    "2026_07_29.sha256.json"
)
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_rate_differential_execution"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("frozen_before_eurusd_price_paths") is not True
        or lock.get("oracle_decision_use_allowed") is not False
        or lock.get("parameter_search_allowed") is not False
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Rate-differential execution lock is incomplete")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Rate-differential execution drift: {relative}")
        checked[relative] = actual
    return {**lock, "checked_files": checked}


def load_candidates(config: dict[str, Any]) -> pd.DataFrame:
    result_lock = config["capacity_screen_result_lock"]
    result_path = PACKAGE_ROOT / result_lock["path"]
    if sha256_file(result_path) != result_lock["sha256"]:
        raise RuntimeError("Rate capacity-screen result lock drift")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if (
        result["status"] != result_lock["required_status"]
        or float(result["selection"]["selected_threshold_bps"])
        != float(result_lock["required_selected_threshold_bps"])
    ):
        raise RuntimeError("Rate capacity screen did not authorize execution")
    source = config["candidate_source"]
    path = PACKAGE_ROOT / source["path"]
    if sha256_file(path) != source["sha256"]:
        raise RuntimeError("Rate candidate manifest drift")
    candidates = pd.read_csv(path)
    required = {
        "entry_time_utc",
        "eligible_date",
        "side",
        "observation_date",
        "observation_lag_calendar_days",
        "spread_change_bps",
        "window",
    }
    if not required.issubset(candidates.columns):
        raise RuntimeError("Rate candidate schema drift")
    candidates["entry_time_utc"] = pd.to_datetime(
        candidates["entry_time_utc"], utc=True, errors="raise"
    )
    candidates["distinct_experts"] = 1
    candidates["expert_combination"] = "OFFICIAL_RATE_DIFFERENTIAL_4BP"
    if (
        len(candidates) != int(source["rows"])
        or candidates["eligible_date"].duplicated().any()
        or not candidates["side"].isin(["LONG", "SHORT"]).all()
        or candidates["observation_lag_calendar_days"].min() < 2
        or candidates["spread_change_bps"].abs().min() < 4.0
    ):
        raise RuntimeError("Rate candidate manifest invariant drift")
    return candidates.sort_values("entry_time_utc").reset_index(drop=True)


def execute_candidates(
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    records: list[dict[str, Any]] = []
    routing: list[dict[str, Any]] = []
    open_until = pd.Timestamp.min.tz_localize("UTC")
    execution_config = {
        "execution": config["execution"],
        "quarantine": config["quarantine"],
    }
    for _, candidate in candidates.iterrows():
        entry = pd.Timestamp(candidate["entry_time_utc"])
        base = {
            "eligible_date": candidate["eligible_date"],
            "entry_time_utc": entry,
            "side": candidate["side"],
            "observation_date": candidate["observation_date"],
            "spread_change_bps": candidate["spread_change_bps"],
        }
        if _quarantine_overlap(entry, execution_config):
            routing.append({**base, "status": "CASH_QUARANTINED_PATH"})
            continue
        if entry < open_until:
            routing.append(
                {
                    **base,
                    "status": "CASH_PRIOR_POSITION_OPEN",
                    "prior_position_exit_utc": open_until,
                }
            )
            continue
        result = simulate_one(candidate, m5, config["execution"])
        routing.append({**base, "status": result["status"]})
        if result["status"] != "CLOSED":
            continue
        records.append({**candidate.to_dict(), **result})
        open_until = pd.Timestamp(result["exit_time_utc"])
    return pd.DataFrame(records), pd.DataFrame(routing)


def _period(frame: pd.DataFrame, bounds: list[str]) -> pd.DataFrame:
    start, end = (pd.Timestamp(value) for value in bounds)
    return frame[
        frame["entry_time_utc"].between(start, end, inclusive="both")
    ]


def summarize(
    trades: pd.DataFrame,
    oracle_summary: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    overall = payoff_metrics(trades)
    stressed = payoff_metrics(trades, "extra_half_pip_stress_r")
    top_removed = payoff_metrics(remove_top_winners(trades))
    windows = {
        name: payoff_metrics(_period(trades, bounds))
        for name, bounds in config["windows"].items()
    }
    sides = {
        side: payoff_metrics(trades[trades["side"].eq(side)])
        for side in ("LONG", "SHORT")
    }
    gates = config["research_gates"]
    gate_results = {
        "minimum_executed_trades": overall["trades"]
        >= int(gates["minimum_executed_trades"]),
        "development_capacity": windows["DEVELOPMENT_2019_2022"]["trades"]
        >= int(gates["minimum_development_trades"]),
        "full_oos_year_capacity": all(
            windows[name]["trades"]
            >= int(gates["minimum_trades_each_full_oos_year"])
            for name in ("OOS_2023", "OOS_2024", "OOS_2025")
        ),
        "latest_six_month_capacity": windows["LATEST_SIX_MONTHS"]["trades"]
        >= int(gates["minimum_latest_six_month_trades"]),
        "win_rate": float(gates["minimum_win_rate"])
        <= overall["win_rate"]
        <= float(gates["maximum_win_rate"]),
        "realized_payoff_ratio": float(
            gates["minimum_realized_payoff_ratio"]
        )
        <= overall["realized_payoff_ratio"]
        <= float(gates["maximum_realized_payoff_ratio"]),
        "profit_factor": overall["profit_factor"]
        >= float(gates["minimum_profit_factor"]),
        "each_window_profit_factor": all(
            windows[name]["profit_factor"]
            > float(gates["minimum_profit_factor_each_window_exclusive"])
            for name in (
                "DEVELOPMENT_2019_2022",
                "OOS_2023",
                "OOS_2024",
                "OOS_2025",
                "OOS_2026_H1",
            )
        ),
        "both_sides": all(
            sides[side]["trades"] >= int(gates["minimum_trades_each_side"])
            and sides[side]["profit_factor"]
            > float(gates["minimum_profit_factor_each_side_exclusive"])
            for side in ("LONG", "SHORT")
        ),
        "maximum_drawdown": overall["max_drawdown_r"]
        <= float(gates["maximum_drawdown_r"]),
        "extra_half_pip_profit_factor": stressed["profit_factor"]
        > float(gates["minimum_extra_half_pip_profit_factor_exclusive"]),
        "top_5pct_winners_removed_profit_factor": top_removed["profit_factor"]
        > float(
            gates["minimum_top_5pct_winners_removed_profit_factor_exclusive"]
        ),
        "oracle_precision": oracle_summary["same_side_precision_15m"]
        >= float(gates["minimum_same_side_oracle_precision_15m"]),
        "oracle_recall": oracle_summary["same_side_recall_15m"]
        >= float(gates["minimum_same_side_oracle_recall_15m"]),
    }
    return {
        "overall": overall,
        "extra_half_pip": stressed,
        "top_5pct_winners_removed": top_removed,
        "windows": windows,
        "by_side": sides,
        "oracle_resemblance": oracle_summary,
        "gate_results": gate_results,
        "all_research_gates_passed": all(gate_results.values()),
    }


def run_execution() -> dict[str, Any]:
    verify_lock()
    config = load_config()
    candidates = load_candidates(config)
    m5 = load_eurusd_m5(config)
    trades, routing = execute_candidates(candidates, m5, config)
    oracle_matches, oracle_summary = attach_oracle_matches(trades, config)
    summary = summarize(trades, oracle_summary, config)
    result = {
        "schema_version": "eurusd_neutral_rate_differential_result_v1",
        "frozen_at_utc": config["frozen_at_utc"],
        "status": (
            "RESEARCH_PASS_PROSPECTIVE_PREREGISTRATION_REQUIRED"
            if summary["all_research_gates_passed"]
            else "REJECTED_EXACT_RATE_DIFFERENTIAL_EXECUTION"
        ),
        "candidates": len(candidates),
        "executed_trades": len(trades),
        "routing_status_counts": {
            str(key): int(value)
            for key, value in routing["status"].value_counts().items()
        },
        "summary": summary,
        "retrospective_causal_not_pristine_oos": True,
        "historical_pass_can_authorize_demo": False,
        "broker_action_allowed": False,
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    csv_kwargs = {"index": False, "date_format": "%Y-%m-%dT%H:%M:%S.%fZ"}
    trades.to_csv(OUTPUT_ROOT / "TRADES.csv", **csv_kwargs)
    routing.to_csv(OUTPUT_ROOT / "ROUTING.csv", **csv_kwargs)
    oracle_matches.to_csv(OUTPUT_ROOT / "ORACLE_MATCHES.csv", **csv_kwargs)
    (OUTPUT_ROOT / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return result
