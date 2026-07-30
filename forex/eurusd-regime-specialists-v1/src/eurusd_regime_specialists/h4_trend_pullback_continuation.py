from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .h4_chop_anchor_validation import (
    _evaluation_subset,
    _scenario_summary,
    apply_round_trip_cost,
    audit_m5,
)
from .h4_unused_regime_frequency_expansion import simulate_long
from .neutral_h4_quiet_state_transfer import (
    add_h4_regimes,
    aggregate_h1,
    load_m5,
    sha256_file,
    simulate_short,
)

EXPERT_SPECS = {
    "H4_TREND_UP_H1_EMA_REJECTION_LONG": ("trend_up", "LONG"),
    "H4_TREND_DOWN_H1_EMA_REJECTION_SHORT": ("trend_down", "SHORT"),
}


def add_pullback_features(h1: pd.DataFrame, ema_period: int) -> pd.DataFrame:
    result = h1.copy()
    result["h1_ema"] = result["mid_close"].ewm(
        span=int(ema_period),
        adjust=False,
        min_periods=int(ema_period),
    ).mean()
    return result


def build_pullback_masks(
    h1: pd.DataFrame, hypothesis: dict[str, Any]
) -> dict[str, pd.Series]:
    date = h1["timestamp"].dt.strftime("%Y-%m-%d")
    hour = h1["timestamp"].dt.hour
    common = (
        hour.isin(hypothesis["decision_hours_utc"])
        & h1["complete_hour"]
        & h1["contiguous_next"]
        & h1["atr"].notna()
        & h1["h1_ema"].notna()
        & (
            h1["body_fraction"]
            >= float(hypothesis["body_fraction_minimum"])
        )
    ).fillna(False)
    raw_long = (
        common
        & h1["regime"].eq("trend_up")
        & (h1["mid_low"] <= h1["h1_ema"])
        & (h1["mid_close"] > h1["h1_ema"])
        & (h1["mid_close"] > h1["mid_open"])
    )
    raw_short = (
        common
        & h1["regime"].eq("trend_down")
        & (h1["mid_high"] >= h1["h1_ema"])
        & (h1["mid_close"] < h1["h1_ema"])
        & (h1["mid_close"] < h1["mid_open"])
    )
    return {
        "H4_TREND_UP_H1_EMA_REJECTION_LONG": (
            raw_long & raw_long.groupby(date).cumsum().eq(1)
        ),
        "H4_TREND_DOWN_H1_EMA_REJECTION_SHORT": (
            raw_short & raw_short.groupby(date).cumsum().eq(1)
        ),
    }


def make_candidate(
    specialist_id: str, hypothesis: dict[str, Any]
) -> dict[str, Any]:
    regime, side = EXPERT_SPECS[specialist_id]
    return {
        "specialist_id": specialist_id,
        "owned_regime": regime,
        "direction": side,
        "stop_atr_multiple": float(hypothesis["stop_h1_atr_multiple"]),
        "target_r_multiple": float(hypothesis["target_r_multiple"]),
        "maximum_hold_hours": int(hypothesis["maximum_hold_hours"]),
    }


def simulate_expert(
    h1: pd.DataFrame,
    m5: pd.DataFrame,
    mask: pd.Series,
    candidate: dict[str, Any],
    anchor: dict[str, Any],
    entry_delay_minutes: int,
) -> tuple[pd.DataFrame, dict[str, int]]:
    if candidate["direction"] == "LONG":
        return simulate_long(
            h1,
            m5,
            mask,
            candidate,
            anchor,
            entry_delay_minutes=entry_delay_minutes,
        )
    return simulate_short(
        h1,
        m5,
        mask,
        candidate,
        anchor,
        entry_delay_minutes=entry_delay_minutes,
    )


def summarize_windows(
    trades: pd.DataFrame, windows: dict[str, list[str]]
) -> dict[str, dict[str, Any]]:
    return {
        name: _scenario_summary(_evaluation_subset(trades, window))
        for name, window in windows.items()
    }


def development_checks(
    windows: dict[str, dict[str, Any]],
    stressed: dict[str, Any],
    gates: dict[str, Any],
) -> dict[str, bool]:
    full = windows["FULL_DEVELOPMENT"]
    return {
        "minimum_trades": full["trades"] >= int(gates["minimum_trades"]),
        "minimum_profit_factor": full["profit_factor"]
        >= float(gates["minimum_profit_factor"]),
        "minimum_stressed_profit_factor": stressed["profit_factor"]
        >= float(gates["minimum_stressed_profit_factor"]),
        "each_development_block_profit_factor": all(
            windows[name]["profit_factor"]
            > float(
                gates[
                    "minimum_each_development_block_profit_factor_exclusive"
                ]
            )
            for name in ("EARLY_2017_2019", "MIDDLE_2020_2022H1")
        ),
        "top_5pct_winners_removed_profit_factor": full[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "maximum_closed_trade_drawdown": full["maximum_drawdown_r"]
        <= float(gates["maximum_closed_trade_drawdown_r"]),
    }


def protected_date_overlap(
    trades: pd.DataFrame,
    protected_dates: set[str],
    *,
    broker_weekdays: int,
) -> dict[str, Any]:
    if trades.empty:
        return {
            "candidate_active_dates": 0,
            "protected_overlap_dates": 0,
            "unique_dates": 0,
            "protected_overlap_share": 0.0,
            "unique_dates_per_broker_weekday": 0.0,
        }
    dates = set(trades["entry_time_utc"].dt.strftime("%Y-%m-%d"))
    overlap = dates & protected_dates
    unique = dates - protected_dates
    return {
        "candidate_active_dates": len(dates),
        "protected_overlap_dates": len(overlap),
        "unique_dates": len(unique),
        "protected_overlap_share": len(overlap) / len(dates),
        "unique_dates_per_broker_weekday": len(unique) / int(broker_weekdays),
    }


def validation_checks(
    windows: dict[str, dict[str, Any]],
    stressed: dict[str, Any],
    delay_metrics: dict[str, dict[str, Any]],
    overlap: dict[str, Any],
    gates: dict[str, Any],
) -> dict[str, bool]:
    full = windows["FULL_VALIDATION"]
    return {
        "minimum_trades": full["trades"] >= int(gates["minimum_trades"]),
        "minimum_profit_factor": full["profit_factor"]
        >= float(gates["minimum_profit_factor"]),
        "minimum_stressed_profit_factor": stressed["profit_factor"]
        >= float(gates["minimum_stressed_profit_factor"]),
        "each_validation_block_profit_factor": all(
            windows[name]["profit_factor"]
            > float(
                gates["minimum_each_validation_block_profit_factor_exclusive"]
            )
            for name in (
                "LATE_2022H2_2024H1",
                "RECENT_2024H2_2026H1",
            )
        ),
        "latest_12_month_profit_factor": windows["LATEST_12_MONTHS"][
            "profit_factor"
        ]
        >= float(gates["minimum_latest_12_month_profit_factor"]),
        "latest_6_month_net_r": windows["LATEST_6_MONTHS"]["net_r"]
        > float(gates["minimum_latest_6_month_net_r_exclusive"]),
        "top_5pct_winners_removed_profit_factor": full[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "maximum_closed_trade_drawdown": full["maximum_drawdown_r"]
        <= float(gates["maximum_closed_trade_drawdown_r"]),
        "minimum_5m_delay_profit_factor": delay_metrics["5m"]["profit_factor"]
        >= float(gates["minimum_5m_delay_profit_factor"]),
        "minimum_15m_delay_profit_factor": delay_metrics["15m"]["profit_factor"]
        >= float(gates["minimum_15m_delay_profit_factor"]),
        "minimum_unique_dates_per_broker_weekday": overlap[
            "unique_dates_per_broker_weekday"
        ]
        >= float(gates["minimum_unique_dates_per_broker_weekday"]),
        "maximum_protected_date_overlap_share": overlap[
            "protected_overlap_share"
        ]
        <= float(gates["maximum_protected_date_overlap_share"]),
    }


def render_report(result: dict[str, Any]) -> str:
    development_rows = []
    validation_rows = []
    for expert_id, expert in result["experts"].items():
        dev = expert["development"]["windows"]["FULL_DEVELOPMENT"]
        development_rows.append(
            f"| {expert_id} | {dev['trades']} | {dev['win_rate']:.2%} | "
            f"{dev['realized_payoff_ratio']:.3f} | "
            f"{dev['profit_factor']:.3f} | "
            f"{expert['development']['stressed']['profit_factor']:.3f} | "
            f"{expert['development']['selected']} |"
        )
        if expert["validation"] is None:
            validation_rows.append(
                f"| {expert_id} | unopened | — | — | — | — | — |"
            )
        else:
            val = expert["validation"]["windows"]["FULL_VALIDATION"]
            overlap = expert["validation"]["protected_date_overlap"]
            validation_rows.append(
                f"| {expert_id} | {val['trades']} | "
                f"{val['profit_factor']:.3f} | "
                f"{expert['validation']['stressed']['profit_factor']:.3f} | "
                f"{val['top_5pct_winners_removed_profit_factor']:.3f} | "
                f"{overlap['unique_dates']} | "
                f"{expert['validation']['admitted']} |"
            )
    return f"""# EURUSD H4 trend-pullback continuation result

Status: **{result["status"]}**

Demo-order authorization: **false**

## Development selection

| Expert | Trades | Win rate | Payoff | PF | +0.5 pip PF | Selected |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(development_rows)}

## Locked validation

| Expert | Trades | PF | +0.5 pip PF | Best-5%-removed PF | New broker-window dates | Admitted |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(validation_rows)}

Selected after development: {", ".join(result["development_selected_experts"]) or "none"}.

Historically admitted after locked validation: {", ".join(result["validation_admitted_experts"]) or "none"}.

No parameter rescue or broker action is authorized.
"""


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    package_root = config_path.parent.parent
    anchor_path = package_root / config["anchor_config"]["path"]
    protected_path = package_root / config["protected_broker_ledger"]["path"]
    if sha256_file(anchor_path) != config["anchor_config"]["sha256"]:
        raise RuntimeError("Anchor configuration checksum mismatch")
    if sha256_file(protected_path) != config["protected_broker_ledger"]["sha256"]:
        raise RuntimeError("Protected broker ledger checksum mismatch")
    anchor = json.loads(anchor_path.read_bytes())
    m5 = load_m5(anchor["source"])
    data_audit = audit_m5(m5, anchor["source"])
    h1 = aggregate_h1(m5)
    h1, _ = add_h4_regimes(h1, anchor["classifier"])
    h1 = add_pullback_features(h1, int(config["hypothesis"]["h1_ema_period"]))
    masks = build_pullback_masks(h1, config["hypothesis"])
    protected = pd.read_csv(protected_path)
    protected_dates = set(protected["entry_date"].astype(str))

    raw: dict[tuple[str, int], pd.DataFrame] = {}
    diagnostics: dict[str, Any] = {}
    experts: dict[str, Any] = {}
    development_selected: list[str] = []
    validation_admitted: list[str] = []

    for expert_id in EXPERT_SPECS:
        candidate = make_candidate(expert_id, config["hypothesis"])
        trades, diagnostic = simulate_expert(
            h1, m5, masks[expert_id], candidate, anchor, 0
        )
        raw[(expert_id, 0)] = trades
        diagnostics[f"{expert_id}_0m"] = diagnostic
        dev_trades = _evaluation_subset(
            trades, config["development_windows"]["FULL_DEVELOPMENT"]
        )
        dev_windows = summarize_windows(
            dev_trades, config["development_windows"]
        )
        dev_stressed = _scenario_summary(
            apply_round_trip_cost(dev_trades, 0.5)
        )
        checks = development_checks(
            dev_windows, dev_stressed, config["development_admission"]
        )
        selected = all(checks.values())
        if selected:
            development_selected.append(expert_id)
        experts[expert_id] = {
            "development": {
                "windows": dev_windows,
                "stressed": dev_stressed,
                "checks": checks,
                "selected": selected,
            },
            "validation": None,
        }

    validation_ledger_parts: list[pd.DataFrame] = []
    for expert_id in development_selected:
        candidate = make_candidate(expert_id, config["hypothesis"])
        base_validation = _evaluation_subset(
            raw[(expert_id, 0)],
            config["locked_validation_windows"]["FULL_VALIDATION"],
        )
        validation_windows = summarize_windows(
            base_validation, config["locked_validation_windows"]
        )
        stressed = _scenario_summary(
            apply_round_trip_cost(base_validation, 0.5)
        )
        delay_metrics: dict[str, dict[str, Any]] = {}
        for delay in config["execution"]["entry_delay_minutes"]:
            delayed, diagnostic = simulate_expert(
                h1,
                m5,
                masks[expert_id],
                candidate,
                anchor,
                int(delay),
            )
            raw[(expert_id, int(delay))] = delayed
            diagnostics[f"{expert_id}_{delay}m"] = diagnostic
            delayed_validation = _evaluation_subset(
                delayed,
                config["locked_validation_windows"]["FULL_VALIDATION"],
            )
            delay_metrics[f"{delay}m"] = _scenario_summary(delayed_validation)
        recent_broker_window = _evaluation_subset(
            base_validation,
            ["2024-07-01T00:00:00Z", "2026-07-01T00:00:00Z"],
        )
        overlap = protected_date_overlap(
            recent_broker_window,
            protected_dates,
            broker_weekdays=int(
                config["protected_broker_ledger"]["weekdays"]
            ),
        )
        checks = validation_checks(
            validation_windows,
            stressed,
            delay_metrics,
            overlap,
            config["locked_validation_admission"],
        )
        admitted = all(checks.values())
        if admitted:
            validation_admitted.append(expert_id)
        tagged = base_validation.copy()
        tagged["validation_admitted"] = admitted
        validation_ledger_parts.append(tagged)
        experts[expert_id]["validation"] = {
            "windows": validation_windows,
            "stressed": stressed,
            "delay_metrics": delay_metrics,
            "protected_date_overlap": overlap,
            "checks": checks,
            "admitted": admitted,
        }

    if not development_selected:
        status = "DEVELOPMENT_REJECTED_VALIDATION_UNOPENED"
    elif not validation_admitted:
        status = "LOCKED_VALIDATION_REJECTED"
    else:
        status = "HISTORICAL_CANDIDATE_REQUIRES_FRESH_CONFIRMATION"
    result = {
        "schema_version": "eurusd_h4_trend_pullback_continuation_result_v1",
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_sha256": anchor["source"]["sha256"],
        "research_boundary": "RETROSPECTIVE_CAUSAL_NOT_PRISTINE_OOS",
        "broker_action_allowed": False,
        "demo_order_authorized": False,
        "data_audit": data_audit,
        "diagnostics": diagnostics,
        "development_selected_experts": development_selected,
        "validation_admitted_experts": validation_admitted,
        "experts": experts,
        "status": status,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    if validation_ledger_parts:
        validation_ledger = pd.concat(
            validation_ledger_parts, ignore_index=True
        ).sort_values("entry_time_utc")
    else:
        validation_ledger = pd.DataFrame()
    validation_ledger.to_csv(output_dir / "VALIDATION_TRADES.csv", index=False)
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "RESULT.md").write_text(
        render_report(result), encoding="utf-8"
    )
    return result

