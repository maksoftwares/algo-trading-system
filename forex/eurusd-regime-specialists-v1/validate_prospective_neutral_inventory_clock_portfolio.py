from __future__ import annotations

import argparse
import json
import math
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import pandas as pd

import prospective_neutral_inventory_clock_transfer as transfer
import validate_prospective_neutral_inventory_unwind_0005 as primary
from capture_prospective_neutral_inventory_unwind_0005 import (
    _serialize,
    _timestamp,
)
from capture_prospective_neutral_inventory_unwind_0005_path import (
    _existing_path,
)
from eurusd_regime_specialists.prospective_neutral_validation_v1_1 import (
    temporal_oracle_metrics,
)
from eurusd_regime_specialists.research import PACKAGE_ROOT, sha256_file

CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_prospective_neutral_inventory_clock_portfolio_v1.json"
)
LOCK_PATH = (
    PACKAGE_ROOT / "EURUSD_NEUTRAL_PROSPECTIVE_INVENTORY_CLOCK_PORTFOLIO_"
    "PREREG_2026_07_29.sha256.json"
)
PRIMARY_LEDGER_ROOT = Path(
    "D:/AlgoTradingData/prospective/eurusd-neutral-inventory-unwind-0005-v1/ledger"
)
PRIMARY_PATH_ROOT = Path(
    "D:/AlgoTradingData/prospective/eurusd-neutral-inventory-unwind-0005-v1/path"
)
PRIMARY_ORACLE_ROOT = Path(
    "D:/AlgoTradingData/prospective/eurusd-neutral-inventory-unwind-0005-v1/oracle"
)
TRANSFER_LEDGER_ROOT = Path(
    "D:/AlgoTradingData/prospective/eurusd-neutral-inventory-clock-transfer-v1/ledger"
)
TRANSFER_PATH_ROOT = Path(
    "D:/AlgoTradingData/prospective/eurusd-neutral-inventory-clock-transfer-v1/path"
)
CLOCKS = ("0005", "0605", "1205")


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_preregistration() -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    required = {
        "locked_before_first_component_observation": True,
        "locked_with_zero_primary_decisions": True,
        "locked_with_zero_transfer_decisions": True,
        "locked_with_zero_primary_paths": True,
        "locked_with_zero_transfer_paths": True,
        "historical_backtest_allowed": False,
        "historical_eurusd_pnl_allowed": False,
        "component_selection_allowed": False,
        "clock_reweighting_allowed": False,
        "broker_action_allowed": False,
    }
    if any(lock.get(key) is not value for key, value in required.items()):
        raise RuntimeError("Three-clock portfolio lock is incomplete")
    for relative, expected in lock["files"].items():
        if sha256_file(PACKAGE_ROOT / relative) != expected:
            raise RuntimeError(
                f"Three-clock portfolio implementation drift: {relative}"
            )
    primary.verify_preregistration()
    transfer.verify_preregistration()
    return lock


def _component_rows(
    decisions: Iterable[Mapping[str, Any]],
    path_root: Path,
    *,
    evaluated_at_utc: pd.Timestamp,
    fixed_clock: str | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for decision in decisions:
        clock = str(fixed_clock) if fixed_clock is not None else str(decision["clock"])
        if clock not in CLOCKS:
            raise RuntimeError(f"Unexpected portfolio clock: {clock}")
        row: dict[str, Any] = {
            "signal_id": str(decision["decision_sha256"]),
            "component_campaign_id": str(decision["campaign_id"]),
            "entry_date_utc": str(decision["entry_date_utc"]),
            "entry_time_utc": decision["entry_time_utc"],
            "clock": clock,
            "side": str(decision["side"]),
            "decision_status": str(decision["status"]),
            "status": "CASH",
        }
        if decision["status"] == "SIGNAL":
            path = _existing_path(
                path_root,
                str(decision["decision_sha256"]),
            )
            if (
                path is None
                or _timestamp(path["path_captured_at_utc"]) > evaluated_at_utc
            ):
                row["status"] = "PENDING_PATH"
            else:
                row.update(path["execution"])
                row["signal_id"] = str(decision["decision_sha256"])
                row["component_campaign_id"] = str(decision["campaign_id"])
                row["entry_date_utc"] = str(decision["entry_date_utc"])
                row["entry_time_utc"] = decision["entry_time_utc"]
                row["clock"] = clock
                row["decision_status"] = str(decision["status"])
        rows.append(row)
    return rows


def collect_portfolio_rows(
    *,
    evaluated_at_utc: Any,
    primary_ledger_root: Path = PRIMARY_LEDGER_ROOT,
    primary_path_root: Path = PRIMARY_PATH_ROOT,
    transfer_ledger_root: Path = TRANSFER_LEDGER_ROOT,
    transfer_path_root: Path = TRANSFER_PATH_ROOT,
) -> pd.DataFrame:
    evaluated = _timestamp(evaluated_at_utc)
    primary_decisions = primary._load_decisions(
        primary_ledger_root,
        evaluated,
    )
    transfer_decisions = transfer._load_decisions(
        transfer_ledger_root,
        evaluated,
    )
    rows = [
        *_component_rows(
            primary_decisions,
            primary_path_root,
            evaluated_at_utc=evaluated,
            fixed_clock="0005",
        ),
        *_component_rows(
            transfer_decisions,
            transfer_path_root,
            evaluated_at_utc=evaluated,
        ),
    ]
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "signal_id",
                "component_campaign_id",
                "entry_date_utc",
                "entry_time_utc",
                "clock",
                "side",
                "decision_status",
                "status",
                "r",
                "extra_half_pip_stress_r",
                "entry_tick_time_utc",
                "exit_time_utc",
            ]
        )
    if frame["signal_id"].duplicated().any():
        raise RuntimeError("Duplicate signal identity across components")
    return frame.sort_values(["entry_time_utc", "clock", "signal_id"]).reset_index(
        drop=True
    )


def interval_integrity(closed: pd.DataFrame) -> dict[str, Any]:
    if closed.empty:
        return {
            "duplicate_entry_timestamps": [],
            "overlaps": [],
            "maximum_concurrent_positions": 0,
            "no_duplicate_entry_timestamps": True,
            "no_position_overlap": True,
        }
    frame = closed.copy()
    frame["entry_tick_time_utc"] = pd.to_datetime(
        frame["entry_tick_time_utc"],
        utc=True,
    ).dt.as_unit("ns")
    frame["exit_time_utc"] = pd.to_datetime(
        frame["exit_time_utc"],
        utc=True,
    ).dt.as_unit("ns")
    frame = frame.sort_values(
        ["entry_tick_time_utc", "clock", "signal_id"]
    ).reset_index(drop=True)
    duplicates = sorted(
        {
            value.isoformat()
            for value in frame.loc[
                frame["entry_tick_time_utc"].duplicated(keep=False),
                "entry_tick_time_utc",
            ]
        }
    )
    overlaps: list[dict[str, Any]] = []
    active: list[tuple[pd.Timestamp, str]] = []
    maximum_concurrent = 0
    for row in frame.to_dict(orient="records"):
        entry = _timestamp(row["entry_tick_time_utc"])
        active = [
            (exit_time, signal_id)
            for exit_time, signal_id in active
            if exit_time > entry
        ]
        if active:
            overlaps.append(
                {
                    "signal_id": row["signal_id"],
                    "entry_time_utc": entry,
                    "overlapping_signal_ids": [signal_id for _, signal_id in active],
                }
            )
        active.append(
            (
                _timestamp(row["exit_time_utc"]),
                str(row["signal_id"]),
            )
        )
        maximum_concurrent = max(maximum_concurrent, len(active))
    return {
        "duplicate_entry_timestamps": duplicates,
        "overlaps": overlaps,
        "maximum_concurrent_positions": maximum_concurrent,
        "no_duplicate_entry_timestamps": not duplicates,
        "no_position_overlap": not overlaps,
    }


def _top_winners_removed(closed: pd.DataFrame) -> dict[str, Any]:
    if closed.empty:
        result = primary.trade_metrics([])
        result["removed_winners"] = 0
        return result
    winner_count = int(closed["r"].gt(0.0).sum())
    removed = max(1, math.ceil(winner_count * 0.05)) if winner_count else 0
    drop_index = closed.nlargest(removed, "r").index if removed else pd.Index([])
    result = primary.trade_metrics(closed.drop(index=drop_index)["r"])
    result["removed_winners"] = removed
    return result


def _window_metrics(
    closed: pd.DataFrame,
    evaluated: pd.Timestamp,
    months: int,
) -> dict[str, Any]:
    cutoff = evaluated - pd.DateOffset(months=int(months))
    if closed.empty:
        return primary.trade_metrics([])
    entries = pd.to_datetime(
        closed["entry_time_utc"],
        utc=True,
    ).dt.as_unit("ns")
    return primary.trade_metrics(closed.loc[entries.ge(cutoff), "r"])


def _component_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": status["status"],
        "all_gates_passed": bool(status["all_gates_passed"]),
        "research_review_allowed": bool(status["research_review_allowed"]),
        "frequency": status["frequency"],
        "overall": status["overall"],
    }


def _active_weekdays(
    start: pd.Timestamp,
    evaluated: pd.Timestamp,
) -> int:
    if evaluated < start:
        return 0
    return int(
        sum(
            day.weekday() < 5
            for day in pd.date_range(
                start.floor("D"),
                evaluated.floor("D"),
                freq="D",
            )
        )
    )


def build_validation_status(
    *,
    evaluated_at_utc: Any | None = None,
    primary_ledger_root: Path = PRIMARY_LEDGER_ROOT,
    primary_path_root: Path = PRIMARY_PATH_ROOT,
    primary_oracle_root: Path = PRIMARY_ORACLE_ROOT,
    transfer_ledger_root: Path = TRANSFER_LEDGER_ROOT,
    transfer_path_root: Path = TRANSFER_PATH_ROOT,
) -> dict[str, Any]:
    verify_preregistration()
    cfg = load_config()
    evaluated = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if evaluated_at_utc is None
        else _timestamp(evaluated_at_utc)
    )
    start = _timestamp(cfg["prospective_start_utc"])
    primary_status = primary.build_validation_status(
        evaluated_at_utc=evaluated,
        ledger_root=primary_ledger_root,
        path_root=primary_path_root,
        oracle_root=primary_oracle_root,
    )
    transfer_status = transfer.build_validation_status(
        evaluated_at_utc=evaluated,
        ledger_root=transfer_ledger_root,
        path_root=transfer_path_root,
        oracle_root=transfer.DEFAULT_ORACLE_ROOT,
    )
    routed = collect_portfolio_rows(
        evaluated_at_utc=evaluated,
        primary_ledger_root=primary_ledger_root,
        primary_path_root=primary_path_root,
        transfer_ledger_root=transfer_ledger_root,
        transfer_path_root=transfer_path_root,
    )
    closed = routed[routed["status"].eq("CLOSED")].copy()
    overall = primary.trade_metrics(closed.get("r", pd.Series(dtype=float)))
    stressed = primary.trade_metrics(
        closed.get(
            "extra_half_pip_stress_r",
            pd.Series(dtype=float),
        )
    )
    by_clock = {
        clock: primary.trade_metrics(closed.loc[closed["clock"].eq(clock), "r"])
        for clock in CLOCKS
    }
    by_side = {
        side: primary.trade_metrics(closed.loc[closed["side"].eq(side), "r"])
        for side in ("LONG", "SHORT")
    }
    trailing = {
        "3_months": _window_metrics(closed, evaluated, 3),
        "6_months": _window_metrics(closed, evaluated, 6),
        "12_months": _window_metrics(closed, evaluated, 12),
    }
    top_removed = _top_winners_removed(closed)
    monthly = primary._monthly_metrics(closed)
    intervals = interval_integrity(closed)
    oracle, completed_dates = primary._load_oracle(
        primary_oracle_root,
        evaluated,
    )
    gates = cfg["prospective_admission"]
    temporal_by_clock = {
        clock: temporal_oracle_metrics(
            routed[routed["clock"].eq(clock)],
            oracle,
            completed_dates,
            windows_minutes=[int(gates["temporal_oracle_window_minutes"])],
            grid_minutes=int(gates["uniform_entry_grid_minutes"]),
        )
        for clock in CLOCKS
    }
    all_oracle_dates = bool(
        len(closed)
        and all(
            temporal_by_clock[clock]["all_closed_trade_oracle_dates_available"]
            for clock in CLOCKS
            if by_clock[clock]["trades"] > 0
        )
    )
    same_day_matches = 0
    if all_oracle_dates:
        neutral = oracle[oracle["regime"].eq("NEUTRAL")].copy()
        neutral["oracle_date"] = neutral["oracle_date"].astype(str)
        for trade in closed.to_dict(orient="records"):
            day = _timestamp(trade["entry_time_utc"]).strftime("%Y-%m-%d")
            same_day_matches += int(
                (
                    neutral["oracle_date"].eq(day)
                    & neutral["side"].eq(str(trade["side"]))
                ).any()
            )
    same_day_precision = (
        same_day_matches / len(closed) if len(closed) and all_oracle_dates else None
    )
    elapsed_months = max(
        0,
        (evaluated.year - start.year) * 12 + evaluated.month - start.month,
    )
    active_weekdays = _active_weekdays(start, evaluated)
    component_checks = {
        "primary_0005_all_gates": bool(primary_status["all_gates_passed"]),
        "transfer_0605_1205_all_gates": bool(transfer_status["all_gates_passed"]),
    }
    component_readiness = {
        "primary_0005_sample_ready": bool(
            all(primary_status["sample_gate_results"].values())
        ),
        "primary_0005_oracle_dates_ready": bool(
            primary_status["oracle_gate_results"]["all_closed_trade_oracle_dates"]
        ),
        "transfer_0605_1205_sample_ready": bool(
            all(transfer_status["sample_gate_results"].values())
        ),
        "transfer_0605_1205_oracle_dates_ready": bool(
            transfer_status["oracle_gate_results"]["all_closed_trade_oracle_dates"]
        ),
    }
    sample_checks = {
        "minimum_calendar_months": elapsed_months
        >= int(gates["minimum_calendar_months"]),
        "minimum_total_closed_trades": len(closed)
        >= int(gates["minimum_total_closed_trades"]),
        "minimum_0005_trades": by_clock["0005"]["trades"]
        >= int(gates["minimum_0005_trades"]),
        "minimum_0605_trades": by_clock["0605"]["trades"]
        >= int(gates["minimum_0605_trades"]),
        "minimum_1205_trades": by_clock["1205"]["trades"]
        >= int(gates["minimum_1205_trades"]),
        "minimum_each_side_trades": all(
            by_side[side]["trades"] >= int(gates["minimum_each_side_trades"])
            for side in ("LONG", "SHORT")
        ),
        "all_signal_paths_closed": not routed["status"].eq("PENDING_PATH").any(),
    }
    economic_checks = {
        "overall_win_rate": float(gates["minimum_overall_win_rate"])
        <= overall["win_rate"]
        <= float(gates["maximum_overall_win_rate"]),
        "overall_payoff": float(gates["minimum_overall_realized_payoff_ratio"])
        <= overall["realized_payoff_ratio"]
        <= float(gates["maximum_overall_realized_payoff_ratio"]),
        "overall_profit_factor": overall["profit_factor"]
        >= float(gates["minimum_overall_profit_factor"]),
        "stressed_profit_factor": stressed["profit_factor"]
        >= float(gates["minimum_stressed_profit_factor"]),
        "each_clock_positive": all(
            by_clock[clock]["profit_factor"]
            >= float(gates["minimum_each_clock_profit_factor"])
            and by_clock[clock]["net_r"]
            > float(gates["minimum_each_clock_net_r_exclusive"])
            for clock in CLOCKS
        ),
        "both_side_profit_factors": all(
            by_side[side]["profit_factor"]
            >= float(gates["minimum_each_side_profit_factor"])
            for side in ("LONG", "SHORT")
        ),
        "trailing_6_month_profit_factor": trailing["6_months"]["profit_factor"]
        >= float(gates["minimum_trailing_6_month_profit_factor"]),
        "trailing_6_month_net_r": trailing["6_months"]["net_r"]
        > float(gates["minimum_trailing_6_month_net_r_exclusive"]),
        "maximum_drawdown": overall["max_drawdown_r"]
        <= float(gates["maximum_closed_trade_drawdown_r"]),
        "top_5pct_removed_profit_factor": top_removed["profit_factor"]
        >= float(gates["minimum_top_5pct_removed_profit_factor"]),
        "positive_active_month_rate": monthly["positive_active_month_rate"]
        >= float(gates["minimum_positive_active_month_rate"]),
        "monthly_profit_concentration": monthly[
            "largest_month_share_of_positive_profit"
        ]
        <= float(gates["maximum_largest_month_share_of_positive_profit"]),
        "no_duplicate_entry_timestamps": bool(
            intervals["no_duplicate_entry_timestamps"]
        ),
        "no_position_overlap": bool(intervals["no_position_overlap"]),
        "maximum_concurrent_positions": int(intervals["maximum_concurrent_positions"])
        <= int(cfg["portfolio_contract"]["maximum_concurrent_positions"]),
    }
    clock_oracle_checks: dict[str, dict[str, bool]] = {}
    window_key = f"within_{int(gates['temporal_oracle_window_minutes'])}_minutes"
    for clock in CLOCKS:
        temporal = temporal_by_clock[clock]
        window = temporal["windows"][window_key]
        clock_oracle_checks[clock] = {
            "all_closed_trade_oracle_dates": bool(
                temporal["all_closed_trade_oracle_dates_available"]
            ),
            "one_prediction_per_date": bool(
                temporal["one_strategy_trade_per_utc_date"]
            ),
            "exact_uniform_null_valid": bool(window["exact_null_valid"]),
            "temporal_precision": bool(
                window["precision"] is not None
                and window["precision"]
                >= float(gates["minimum_each_clock_temporal_oracle_precision"])
            ),
            "temporal_lift": bool(
                window["precision_lift_over_uniform_time_and_side"] is not None
                and window["precision_lift_over_uniform_time_and_side"]
                > float(
                    gates[
                        "minimum_each_clock_temporal_lift_over_uniform_null_exclusive"
                    ]
                )
            ),
            "bonferroni_uniform_null_test": bool(
                window["uniform_time_and_side_poisson_binomial_tail_p_value"]
                is not None
                and window["uniform_time_and_side_poisson_binomial_tail_p_value"]
                <= float(gates["maximum_each_clock_temporal_uniform_null_p_value"])
            ),
        }
    oracle_checks = {
        "all_closed_trade_oracle_dates": all_oracle_dates,
        "same_day_same_side_precision": bool(
            same_day_precision is not None
            and same_day_precision
            >= float(gates["minimum_same_day_same_side_oracle_precision"])
        ),
        "all_three_clock_temporal_gates": all(
            all(checks.values()) for checks in clock_oracle_checks.values()
        ),
    }
    sample_passed = bool(all(sample_checks.values()))
    evaluation_ready = bool(
        sample_passed and all_oracle_dates and all(component_readiness.values())
    )
    all_passed = bool(
        evaluation_ready
        and all(component_checks.values())
        and all(economic_checks.values())
        and all(oracle_checks.values())
    )
    if evaluated < start:
        status = "WAITING_FOR_PROSPECTIVE_START"
    elif not evaluation_ready:
        status = "ACCUMULATING_PROSPECTIVE_EVIDENCE"
    elif all_passed:
        status = "INDEPENDENT_RESEARCH_REVIEW_REQUIRED"
    else:
        status = "REJECTED_WITHOUT_RETUNING"
    return _serialize(
        {
            "schema_version": (
                "eurusd_neutral_prospective_inventory_clock_portfolio_validation_v1"
            ),
            "status": status,
            "prospective_start_utc": start,
            "evaluated_at_utc": evaluated,
            "promotion_unit": ("FIXED_THREE_CLOCK_0005_0605_1205_PORTFOLIO"),
            "component_selection_allowed": False,
            "clock_reweighting_allowed": False,
            "component_status": {
                "0005": _component_summary(primary_status),
                "0605_1205": _component_summary(transfer_status),
            },
            "frequency": {
                "eligible_decisions_recorded": len(routed),
                "signals": int(routed["decision_status"].eq("SIGNAL").sum()),
                "cash_decisions": int(routed["decision_status"].eq("CASH").sum()),
                "closed_trades": len(closed),
                "elapsed_calendar_months": elapsed_months,
                "elapsed_active_weekdays": active_weekdays,
                "completed_trades_per_elapsed_active_weekday": (
                    len(closed) / active_weekdays if active_weekdays else 0.0
                ),
            },
            "overall": overall,
            "by_clock": by_clock,
            "by_side": by_side,
            "trailing_windows": trailing,
            "extra_half_pip_round_trip": stressed,
            "top_5pct_winners_removed": top_removed,
            "monthly": monthly,
            "interval_integrity": intervals,
            "same_day_oracle_resemblance": {
                "matches": same_day_matches,
                "precision": same_day_precision,
            },
            "temporal_oracle_resemblance_by_clock": temporal_by_clock,
            "component_readiness": component_readiness,
            "component_gate_results": component_checks,
            "sample_gate_results": sample_checks,
            "economic_and_robustness_gate_results": economic_checks,
            "clock_oracle_gate_results": clock_oracle_checks,
            "oracle_gate_results": oracle_checks,
            "all_gates_passed": all_passed,
            "research_review_allowed": all_passed,
            "controlled_demo_ready": False,
            "historical_eurusd_pnl_loaded": False,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("status",))
    return parser.parse_args()


def main() -> int:
    parse_args()
    print(json.dumps(build_validation_status(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
