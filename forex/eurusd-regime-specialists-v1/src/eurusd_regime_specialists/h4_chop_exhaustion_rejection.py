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
from .h4_trend_pullback_continuation import (
    add_pullback_features,
    protected_date_overlap,
    summarize_windows,
)
from .h4_unused_regime_frequency_expansion import simulate_long
from .neutral_h4_quiet_state_transfer import (
    add_h4_regimes,
    aggregate_h1,
    load_m5,
    sha256_file,
    simulate_short,
)


def build_exhaustion_masks(
    h1: pd.DataFrame, hypothesis: dict[str, Any]
) -> dict[str, pd.Series]:
    date = h1["timestamp"].dt.strftime("%Y-%m-%d")
    hour = h1["timestamp"].dt.hour
    envelope = float(hypothesis["envelope_atr_multiple"]) * h1["atr"]
    lower = h1["h1_ema"] - envelope
    upper = h1["h1_ema"] + envelope
    common = (
        hour.isin(hypothesis["decision_hours_utc"])
        & h1["complete_hour"]
        & h1["contiguous_next"]
        & h1["regime"].eq(hypothesis["owned_regime"])
        & h1["atr"].notna()
        & h1["h1_ema"].notna()
        & (
            h1["body_fraction"]
            >= float(hypothesis["body_fraction_minimum"])
        )
    ).fillna(False)
    raw_long = (
        common
        & (h1["mid_low"] <= lower)
        & (h1["mid_close"] > lower)
        & (h1["mid_close"] > h1["mid_open"])
    )
    raw_short = (
        common
        & (h1["mid_high"] >= upper)
        & (h1["mid_close"] < upper)
        & (h1["mid_close"] < h1["mid_open"])
    )
    first = (
        (raw_long | raw_short)
        & (raw_long | raw_short).groupby(date).cumsum().eq(1)
    )
    return {
        "LONG": first & raw_long & ~raw_short,
        "SHORT": first & raw_short & ~raw_long,
    }


def make_candidate(
    hypothesis: dict[str, Any], side: str
) -> dict[str, Any]:
    return {
        "specialist_id": hypothesis["specialist_id"],
        "owned_regime": hypothesis["owned_regime"],
        "direction": side,
        "stop_atr_multiple": float(hypothesis["stop_h1_atr_multiple"]),
        "target_r_multiple": float(hypothesis["target_r_multiple"]),
        "maximum_hold_hours": int(hypothesis["maximum_hold_hours"]),
    }


def enforce_one_open_position(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    ordered = trades.sort_values(
        ["entry_time_utc", "exit_time_utc", "side"]
    ).reset_index(drop=True)
    accepted: list[int] = []
    blocked_until: pd.Timestamp | None = None
    for index, trade in ordered.iterrows():
        entry = pd.Timestamp(trade["entry_time_utc"])
        if blocked_until is not None and entry <= blocked_until:
            continue
        accepted.append(index)
        blocked_until = pd.Timestamp(trade["exit_time_utc"])
    return ordered.loc[accepted].reset_index(drop=True)


def simulate_both_sides(
    h1: pd.DataFrame,
    m5: pd.DataFrame,
    masks: dict[str, pd.Series],
    hypothesis: dict[str, Any],
    anchor: dict[str, Any],
    delay: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    pieces = []
    diagnostics: dict[str, Any] = {}
    for side in ("LONG", "SHORT"):
        candidate = make_candidate(hypothesis, side)
        if side == "LONG":
            trades, diagnostic = simulate_long(
                h1,
                m5,
                masks[side],
                candidate,
                anchor,
                entry_delay_minutes=delay,
            )
        else:
            trades, diagnostic = simulate_short(
                h1,
                m5,
                masks[side],
                candidate,
                anchor,
                entry_delay_minutes=delay,
            )
        pieces.append(trades)
        diagnostics[side] = diagnostic
    combined = enforce_one_open_position(
        pd.concat(pieces, ignore_index=True)
    )
    diagnostics["cross_side_overlap_rejections"] = (
        sum(len(piece) for piece in pieces) - len(combined)
    )
    return combined, diagnostics


def side_metrics(trades: pd.DataFrame) -> dict[str, dict[str, Any]]:
    return {
        side: _scenario_summary(trades[trades["side"].eq(side)].copy())
        for side in ("LONG", "SHORT")
    }


def development_checks(
    windows: dict[str, dict[str, Any]],
    stressed: dict[str, Any],
    sides: dict[str, dict[str, Any]],
    gates: dict[str, Any],
) -> dict[str, bool]:
    full = windows["FULL_DEVELOPMENT"]
    return {
        "minimum_trades": full["trades"] >= int(gates["minimum_trades"]),
        "minimum_trades_each_side": all(
            sides[side]["trades"] >= int(gates["minimum_trades_each_side"])
            for side in ("LONG", "SHORT")
        ),
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
        "minimum_each_side_profit_factor": all(
            sides[side]["profit_factor"]
            >= float(gates["minimum_each_side_profit_factor"])
            for side in ("LONG", "SHORT")
        ),
        "top_5pct_winners_removed_profit_factor": full[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "maximum_closed_trade_drawdown": full["maximum_drawdown_r"]
        <= float(gates["maximum_closed_trade_drawdown_r"]),
    }


def validation_checks(
    windows: dict[str, dict[str, Any]],
    stressed: dict[str, Any],
    sides: dict[str, dict[str, Any]],
    delay_metrics: dict[str, dict[str, Any]],
    overlap: dict[str, Any],
    gates: dict[str, Any],
) -> dict[str, bool]:
    full = windows["FULL_VALIDATION"]
    return {
        "minimum_trades": full["trades"] >= int(gates["minimum_trades"]),
        "minimum_trades_each_side": all(
            sides[side]["trades"] >= int(gates["minimum_trades_each_side"])
            for side in ("LONG", "SHORT")
        ),
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
        "minimum_each_side_profit_factor": all(
            sides[side]["profit_factor"]
            >= float(gates["minimum_each_side_profit_factor"])
            for side in ("LONG", "SHORT")
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
        "minimum_15m_delay_profit_factor": delay_metrics["15m"][
            "profit_factor"
        ]
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
    dev = result["development"]["windows"]["FULL_DEVELOPMENT"]
    dev_sides = result["development"]["side_metrics"]
    if result["validation"] is None:
        validation_text = "Locked validation remained unopened."
    else:
        validation = result["validation"]
        full = validation["windows"]["FULL_VALIDATION"]
        overlap = validation["protected_date_overlap"]
        validation_text = f"""| Trades | PF | +0.5 pip PF | Best-5%-removed PF | New dates | Admitted |
|---:|---:|---:|---:|---:|---:|
| {full["trades"]} | {full["profit_factor"]:.3f} | {validation["stressed"]["profit_factor"]:.3f} | {full["top_5pct_winners_removed_profit_factor"]:.3f} | {overlap["unique_dates"]} | {validation["admitted"]} |"""
    return f"""# EURUSD H4 chop exhaustion-rejection result

Status: **{result["status"]}**

Demo-order authorization: **false**

## Development

| Trades | Win rate | Payoff | PF | +0.5 pip PF | Selected |
|---:|---:|---:|---:|---:|---:|
| {dev["trades"]} | {dev["win_rate"]:.2%} | {dev["realized_payoff_ratio"]:.3f} | {dev["profit_factor"]:.3f} | {result["development"]["stressed"]["profit_factor"]:.3f} | {result["development"]["selected"]} |

Long: {dev_sides["LONG"]["trades"]} trades, PF {dev_sides["LONG"]["profit_factor"]:.3f}.

Short: {dev_sides["SHORT"]["trades"]} trades, PF {dev_sides["SHORT"]["profit_factor"]:.3f}.

## Locked validation

{validation_text}

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
    masks = build_exhaustion_masks(h1, config["hypothesis"])
    protected = pd.read_csv(protected_path)
    protected_dates = set(protected["entry_date"].astype(str))

    base, base_diagnostics = simulate_both_sides(
        h1, m5, masks, config["hypothesis"], anchor, 0
    )
    development_trades = _evaluation_subset(
        base, config["development_windows"]["FULL_DEVELOPMENT"]
    )
    development_windows = summarize_windows(
        development_trades, config["development_windows"]
    )
    development_stressed = _scenario_summary(
        apply_round_trip_cost(development_trades, 0.5)
    )
    development_sides = side_metrics(development_trades)
    dev_checks = development_checks(
        development_windows,
        development_stressed,
        development_sides,
        config["development_admission"],
    )
    selected = all(dev_checks.values())
    validation: dict[str, Any] | None = None
    diagnostics: dict[str, Any] = {"0m": base_diagnostics}
    validation_trades = pd.DataFrame()

    if selected:
        validation_trades = _evaluation_subset(
            base, config["locked_validation_windows"]["FULL_VALIDATION"]
        )
        validation_windows = summarize_windows(
            validation_trades, config["locked_validation_windows"]
        )
        validation_stressed = _scenario_summary(
            apply_round_trip_cost(validation_trades, 0.5)
        )
        validation_sides = side_metrics(validation_trades)
        delay_metrics: dict[str, dict[str, Any]] = {}
        for delay in config["execution"]["entry_delay_minutes"]:
            delayed, delay_diagnostics = simulate_both_sides(
                h1,
                m5,
                masks,
                config["hypothesis"],
                anchor,
                int(delay),
            )
            diagnostics[f"{delay}m"] = delay_diagnostics
            delay_metrics[f"{delay}m"] = _scenario_summary(
                _evaluation_subset(
                    delayed,
                    config["locked_validation_windows"]["FULL_VALIDATION"],
                )
            )
        recent = _evaluation_subset(
            validation_trades,
            ["2024-07-01T00:00:00Z", "2026-07-01T00:00:00Z"],
        )
        overlap = protected_date_overlap(
            recent,
            protected_dates,
            broker_weekdays=int(
                config["protected_broker_ledger"]["weekdays"]
            ),
        )
        val_checks = validation_checks(
            validation_windows,
            validation_stressed,
            validation_sides,
            delay_metrics,
            overlap,
            config["locked_validation_admission"],
        )
        validation = {
            "windows": validation_windows,
            "stressed": validation_stressed,
            "side_metrics": validation_sides,
            "delay_metrics": delay_metrics,
            "protected_date_overlap": overlap,
            "checks": val_checks,
            "admitted": all(val_checks.values()),
        }

    if not selected:
        status = "DEVELOPMENT_REJECTED_VALIDATION_UNOPENED"
    elif validation is not None and validation["admitted"]:
        status = "HISTORICAL_CANDIDATE_REQUIRES_FRESH_CONFIRMATION"
    else:
        status = "LOCKED_VALIDATION_REJECTED"
    result = {
        "schema_version": "eurusd_h4_chop_exhaustion_rejection_result_v1",
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_sha256": anchor["source"]["sha256"],
        "research_boundary": "RETROSPECTIVE_CAUSAL_NOT_PRISTINE_OOS",
        "broker_action_allowed": False,
        "demo_order_authorized": False,
        "data_audit": data_audit,
        "diagnostics": diagnostics,
        "development": {
            "windows": development_windows,
            "stressed": development_stressed,
            "side_metrics": development_sides,
            "checks": dev_checks,
            "selected": selected,
        },
        "validation": validation,
        "status": status,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    validation_trades.to_csv(
        output_dir / "VALIDATION_TRADES.csv", index=False
    )
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "RESULT.md").write_text(
        render_report(result), encoding="utf-8"
    )
    return result

