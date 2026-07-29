from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from capture_prospective_neutral_inventory_unwind_0005 import (
    DEFAULT_LEDGER_ROOT,
    _entry_date,
    _existing_record,
    _serialize,
    _timestamp,
    load_config,
    verify_preregistration,
)
from capture_prospective_neutral_inventory_unwind_0005_path import (
    DEFAULT_OUTPUT_ROOT as DEFAULT_PATH_ROOT,
)
from capture_prospective_neutral_inventory_unwind_0005_path import (
    _existing_path,
)
from eurusd_regime_specialists.prospective_neutral_validation_v1_1 import (
    temporal_oracle_metrics,
)
from eurusd_regime_specialists.research import sha256_file


DEFAULT_ORACLE_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-inventory-unwind-0005-v1/oracle"
)


def trade_metrics(values: Iterable[float]) -> dict[str, Any]:
    series = pd.Series(list(values), dtype=float)
    wins = series[series > 0.0]
    losses = series[series < 0.0]
    average_win = float(wins.mean()) if len(wins) else 0.0
    average_loss = float(-losses.mean()) if len(losses) else 0.0
    payoff = (
        float(average_win / average_loss)
        if average_loss > 0.0
        else math.inf
        if average_win > 0.0
        else 0.0
    )
    gross_win = float(wins.sum())
    gross_loss = float(-losses.sum())
    profit_factor = (
        float(gross_win / gross_loss)
        if gross_loss > 0.0
        else math.inf
        if gross_win > 0.0
        else 0.0
    )
    equity = series.cumsum()
    running_peak = equity.cummax().clip(lower=0.0)
    drawdown = running_peak - equity
    return {
        "trades": int(len(series)),
        "wins": int(len(wins)),
        "losses": int(len(losses)),
        "breakevens": int(series.eq(0.0).sum()),
        "win_rate": float(len(wins) / len(series)) if len(series) else 0.0,
        "average_win_r": average_win,
        "average_loss_r": average_loss,
        "realized_payoff_ratio": payoff,
        "profit_factor": profit_factor,
        "net_r": float(series.sum()),
        "expectancy_r": float(series.mean()) if len(series) else 0.0,
        "max_drawdown_r": (
            float(drawdown.max()) if len(drawdown) else 0.0
        ),
    }


def _load_decisions(
    ledger_root: Path,
    as_of: pd.Timestamp,
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    dates: set[str] = set()
    for path in sorted((ledger_root / "decisions").glob("DECISION_*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        created = _timestamp(raw["decision_created_at_utc"])
        if created > as_of:
            continue
        day = str(raw["entry_date_utc"])
        if day in dates:
            raise RuntimeError("Duplicate prospective decision date")
        verified = _existing_record(
            ledger_root,
            "decisions",
            _entry_date(f"{day}T00:00:00Z"),
            prefix="DECISION",
        )
        if verified is None:
            raise RuntimeError("Decision disappeared during validation")
        decisions.append(verified)
        dates.add(day)
    return decisions


def _load_oracle(
    oracle_root: Path,
    as_of: pd.Timestamp,
) -> tuple[pd.DataFrame, set[str]]:
    frames: list[pd.DataFrame] = []
    completed: set[str] = set()
    for path in sorted(
        (oracle_root / "manifests").glob("MANIFEST_*.json")
    ):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        known = _timestamp(manifest["oracle_label_known_time_utc"])
        if known > as_of:
            continue
        labels_ref = manifest["oracle_labels"]
        labels_path = oracle_root / labels_ref["relative_path"]
        if (
            not labels_path.is_file()
            or sha256_file(labels_path) != labels_ref["sha256"]
        ):
            raise RuntimeError("Prospective oracle label evidence drift")
        labels = pd.read_parquet(labels_path)
        if len(labels) != int(labels_ref["rows"]):
            raise RuntimeError("Prospective oracle row-count drift")
        frames.append(labels)
        if bool(manifest.get("oracle_date_complete")):
            completed.add(str(manifest["oracle_date"]))
    if not frames:
        return pd.DataFrame(), completed
    oracle = pd.concat(frames, ignore_index=True)
    if "oracle_row_id" not in oracle.columns:
        oracle["oracle_row_id"] = np.arange(len(oracle), dtype=int)
    return oracle, completed


def _monthly_metrics(closed: pd.DataFrame) -> dict[str, Any]:
    if closed.empty:
        return {
            "active_months": 0,
            "positive_active_months": 0,
            "positive_active_month_rate": 0.0,
            "largest_month_share_of_positive_profit": 0.0,
            "months": {},
        }
    frame = closed.copy()
    frame["month"] = pd.to_datetime(
        frame["entry_time_utc"], utc=True
    ).dt.strftime("%Y-%m")
    months = {
        str(month): trade_metrics(group["r"])
        for month, group in frame.groupby("month", sort=True)
    }
    positive = {
        month: values["net_r"]
        for month, values in months.items()
        if values["net_r"] > 0.0
    }
    total_positive = sum(positive.values())
    concentration = (
        max(positive.values()) / total_positive
        if total_positive > 0.0
        else 0.0
    )
    return {
        "active_months": len(months),
        "positive_active_months": len(positive),
        "positive_active_month_rate": (
            len(positive) / len(months) if months else 0.0
        ),
        "largest_month_share_of_positive_profit": concentration,
        "months": months,
    }


def build_validation_status(
    *,
    evaluated_at_utc: Any | None = None,
    ledger_root: Path = DEFAULT_LEDGER_ROOT,
    path_root: Path = DEFAULT_PATH_ROOT,
    oracle_root: Path = DEFAULT_ORACLE_ROOT,
) -> dict[str, Any]:
    verify_preregistration()
    cfg = load_config()
    evaluated = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if evaluated_at_utc is None
        else _timestamp(evaluated_at_utc)
    )
    start = _timestamp(cfg["prospective_start_utc"])
    decisions = _load_decisions(ledger_root, evaluated)
    routed_rows: list[dict[str, Any]] = []
    for decision in decisions:
        row = {
            "signal_id": decision["decision_sha256"],
            "entry_date_utc": decision["entry_date_utc"],
            "entry_time_utc": decision["entry_time_utc"],
            "side": decision["side"],
            "decision_status": decision["status"],
            "status": "CASH",
        }
        if decision["status"] == "SIGNAL":
            path = _existing_path(
                path_root, str(decision["decision_sha256"])
            )
            if path is None:
                row["status"] = "PENDING_PATH"
            elif _timestamp(path["path_captured_at_utc"]) > evaluated:
                row["status"] = "PENDING_PATH"
            else:
                execution = path["execution"]
                row.update(execution)
                row["signal_id"] = decision["decision_sha256"]
                row["decision_status"] = decision["status"]
        routed_rows.append(row)
    routed = pd.DataFrame(routed_rows)
    if routed.empty:
        routed = pd.DataFrame(
            columns=[
                "signal_id",
                "entry_date_utc",
                "entry_time_utc",
                "side",
                "decision_status",
                "status",
                "r",
                "extra_half_pip_stress_r",
            ]
        )
    closed = routed[routed["status"].eq("CLOSED")].copy()
    overall = trade_metrics(closed.get("r", pd.Series(dtype=float)))
    by_side = {
        side: trade_metrics(
            closed.loc[closed["side"].eq(side), "r"]
        )
        for side in ("LONG", "SHORT")
    }
    stress = trade_metrics(
        closed.get(
            "extra_half_pip_stress_r", pd.Series(dtype=float)
        )
    )
    if closed.empty:
        top_removed = trade_metrics([])
        removed = 0
    else:
        winner_count = int(closed["r"].gt(0.0).sum())
        removed = (
            max(1, math.ceil(winner_count * 0.05))
            if winner_count
            else 0
        )
        drop_index = (
            closed.nlargest(removed, "r").index
            if removed
            else pd.Index([])
        )
        top_removed = trade_metrics(
            closed.drop(index=drop_index)["r"]
        )
    top_removed["removed_winners"] = removed
    monthly = _monthly_metrics(closed)
    oracle, completed_dates = _load_oracle(oracle_root, evaluated)
    temporal = temporal_oracle_metrics(
        routed,
        oracle,
        completed_dates,
        windows_minutes=[15],
        grid_minutes=5,
    )
    primary = temporal["windows"]["within_15_minutes"]
    same_day_matches = 0
    if not closed.empty and temporal[
        "all_closed_trade_oracle_dates_available"
    ]:
        neutral = oracle[oracle["regime"].eq("NEUTRAL")].copy()
        neutral["oracle_date"] = neutral["oracle_date"].astype(str)
        for _, trade in closed.iterrows():
            day = pd.Timestamp(
                trade["entry_time_utc"]
            ).strftime("%Y-%m-%d")
            same_day_matches += int(
                (
                    neutral["oracle_date"].eq(day)
                    & neutral["side"].eq(trade["side"])
                ).any()
            )
    same_day_precision = (
        same_day_matches / len(closed)
        if len(closed)
        and temporal["all_closed_trade_oracle_dates_available"]
        else None
    )
    elapsed_months = max(
        0,
        (evaluated.year - start.year) * 12
        + evaluated.month
        - start.month,
    )
    gates = cfg["prospective_admission"]
    sample_checks = {
        "minimum_calendar_months": elapsed_months
        >= int(gates["minimum_calendar_months"]),
        "minimum_executed_trades": len(closed)
        >= int(gates["minimum_executed_trades"]),
        "minimum_each_side_trades": all(
            by_side[side]["trades"]
            >= int(gates["minimum_each_side_trades"])
            for side in ("LONG", "SHORT")
        ),
        "all_signal_paths_closed": not routed["status"].eq(
            "PENDING_PATH"
        ).any(),
    }
    economic_checks = {
        "overall_win_rate": float(
            gates["minimum_overall_win_rate"]
        )
        <= overall["win_rate"]
        <= float(gates["maximum_overall_win_rate"]),
        "overall_payoff": float(
            gates["minimum_overall_realized_payoff_ratio"]
        )
        <= overall["realized_payoff_ratio"]
        <= float(
            gates["maximum_overall_realized_payoff_ratio"]
        ),
        "overall_profit_factor": overall["profit_factor"]
        >= float(gates["minimum_overall_profit_factor"]),
        "both_side_profit_factors": all(
            by_side[side]["profit_factor"]
            >= float(gates["minimum_each_side_profit_factor"])
            for side in ("LONG", "SHORT")
        ),
        "maximum_drawdown": overall["max_drawdown_r"]
        <= float(gates["maximum_drawdown_r"]),
        "extra_half_pip_profit_factor": stress["profit_factor"]
        >= float(gates["minimum_extra_half_pip_profit_factor"]),
        "top_5pct_removed_profit_factor": top_removed[
            "profit_factor"
        ]
        >= float(gates["minimum_top_5pct_removed_profit_factor"]),
        "positive_active_month_rate": monthly[
            "positive_active_month_rate"
        ]
        >= float(gates["minimum_positive_active_month_rate"]),
        "monthly_profit_concentration": monthly[
            "largest_month_share_of_positive_profit"
        ]
        <= float(
            gates["maximum_largest_month_share_of_positive_profit"]
        ),
    }
    oracle_checks = {
        "all_closed_trade_oracle_dates": temporal[
            "all_closed_trade_oracle_dates_available"
        ],
        "same_day_same_side_precision": (
            same_day_precision is not None
            and same_day_precision
            >= float(
                gates[
                    "minimum_same_day_same_side_oracle_precision"
                ]
            )
        ),
        "temporal_precision": (
            primary["precision"] is not None
            and primary["precision"]
            >= float(gates["minimum_temporal_oracle_precision"])
        ),
        "temporal_lift": (
            primary["precision_lift_over_uniform_time_and_side"]
            is not None
            and primary[
                "precision_lift_over_uniform_time_and_side"
            ]
            >= float(
                gates[
                    "minimum_temporal_lift_over_exact_uniform_time_and_side_null"
                ]
            )
        ),
        "temporal_uniform_null_test": (
            primary[
                "uniform_time_and_side_poisson_binomial_tail_p_value"
            ]
            is not None
            and primary[
                "uniform_time_and_side_poisson_binomial_tail_p_value"
            ]
            <= float(
                gates["maximum_temporal_uniform_null_p_value"]
            )
        ),
    }
    all_passed = bool(
        all(sample_checks.values())
        and all(economic_checks.values())
        and all(oracle_checks.values())
    )
    if evaluated < start:
        status = "WAITING_FOR_PROSPECTIVE_START"
    elif all_passed:
        status = "INDEPENDENT_RESEARCH_REVIEW_REQUIRED"
    else:
        status = "ACCUMULATING_PROSPECTIVE_EVIDENCE"
    return _serialize(
        {
            "schema_version": (
                "eurusd_neutral_prospective_inventory_validation_v1"
            ),
            "status": status,
            "prospective_start_utc": start,
            "evaluated_at_utc": evaluated,
            "frequency": {
                "eligible_decisions_recorded": len(decisions),
                "signals": int(
                    sum(row["status"] == "SIGNAL" for row in decisions)
                ),
                "cash_decisions": int(
                    sum(row["status"] == "CASH" for row in decisions)
                ),
                "closed_trades": len(closed),
                "elapsed_calendar_months": elapsed_months,
            },
            "overall": overall,
            "by_side": by_side,
            "extra_half_pip_round_trip": stress,
            "top_5pct_winners_removed": top_removed,
            "monthly": monthly,
            "same_day_oracle_resemblance": {
                "matches": same_day_matches,
                "precision": same_day_precision,
            },
            "temporal_oracle_resemblance": temporal,
            "sample_gate_results": sample_checks,
            "economic_and_robustness_gate_results": economic_checks,
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
