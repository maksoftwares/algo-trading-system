from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .h4_chop_anchor_validation import (
    _evaluation_subset,
    _scenario_summary,
    audit_m5,
    circular_block_bootstrap,
)
from .h4_dual_regime_portfolio_diagnostic import (
    apply_portfolio_weight,
    apply_weighted_cost,
    apply_weighted_rollover,
    circular_calendar_month_bootstrap,
    concurrency_audit,
)
from .h4_session_frequency_expansion import (
    _fx_days,
    _windows,
    apply_causal_risk_cap,
    evaluate_final_gates,
)
from .neutral_h4_quiet_state_transfer import (
    add_h4_regimes,
    aggregate_h1,
    build_signal_mask,
    load_m5,
    sha256_file,
    simulate_short,
)


def aggregate_resolution_bars(
    m5: pd.DataFrame,
    h1: pd.DataFrame,
    h4: pd.DataFrame,
    resolution_minutes: int,
) -> pd.DataFrame:
    if resolution_minutes not in (15, 30):
        raise ValueError("Intrahour resolution must be 15 or 30 minutes")
    work = m5.copy()
    work["bar_time"] = work["timestamp"].dt.floor(f"{resolution_minutes}min")
    grouped = work.groupby("bar_time", sort=True)
    bars = grouped.agg(
        mid_open=("bid_open", "first"),
        bid_high=("bid_high", "max"),
        bid_low=("bid_low", "min"),
        bid_close=("bid_close", "last"),
        ask_high=("ask_high", "max"),
        ask_low=("ask_low", "min"),
        ask_close=("ask_close", "last"),
        m5_bars=("timestamp", "size"),
    ).reset_index(names="timestamp")
    bars["mid_open"] = (
        grouped["bid_open"].first().to_numpy() + grouped["ask_open"].first().to_numpy()
    ) / 2.0
    bars["mid_high"] = (bars["bid_high"] + bars["ask_high"]) / 2.0
    bars["mid_low"] = (bars["bid_low"] + bars["ask_low"]) / 2.0
    bars["mid_close"] = (bars["bid_close"] + bars["ask_close"]) / 2.0
    bars["complete_bar"] = bars["m5_bars"].eq(resolution_minutes // 5)
    bars["body_fraction"] = (
        (bars["mid_close"] - bars["mid_open"]).abs()
        / (bars["mid_high"] - bars["mid_low"]).replace(0.0, pd.NA)
    ).astype(float)
    bars["available_time"] = bars["timestamp"] + pd.Timedelta(
        minutes=resolution_minutes
    )

    atr_source = h1[["timestamp", "atr"]].copy()
    atr_source["atr_available_time"] = atr_source["timestamp"] + pd.Timedelta(hours=1)
    bars = pd.merge_asof(
        bars.sort_values("available_time"),
        atr_source[["atr_available_time", "atr"]].sort_values("atr_available_time"),
        left_on="available_time",
        right_on="atr_available_time",
        direction="backward",
    )
    regime_source = h4[["timestamp", "regime"]].copy()
    regime_source["regime_available_time"] = regime_source["timestamp"] + pd.Timedelta(
        hours=4
    )
    bars = pd.merge_asof(
        bars.sort_values("timestamp"),
        regime_source[["regime_available_time", "regime"]].sort_values(
            "regime_available_time"
        ),
        left_on="timestamp",
        right_on="regime_available_time",
        direction="backward",
    )
    bars["regime"] = bars["regime"].fillna("transition")
    return bars


def build_resolution_mask(
    bars: pd.DataFrame,
    candidate: dict[str, Any],
    resolution_minutes: int,
) -> pd.Series:
    date = bars["timestamp"].dt.strftime("%Y-%m-%d")
    minute_of_day = bars["timestamp"].dt.hour * 60 + bars["timestamp"].dt.minute
    reference = minute_of_day.ge(0) & minute_of_day.lt(360) & bars["complete_bar"]
    ref_low = bars["mid_low"].where(reference).groupby(date).transform("min")
    ref_count = reference.groupby(date).transform("sum")
    decision = minute_of_day.ge(360) & minute_of_day.lt(600)
    raw = (
        (bars["mid_close"] < ref_low)
        & decision
        & ref_count.eq(360 // resolution_minutes)
        & bars["complete_bar"]
        & (bars["body_fraction"] >= float(candidate["body_fraction_minimum"]))
        & bars["regime"].eq(candidate["owned_regime"])
        & bars["atr"].notna()
    ).fillna(False)
    return raw & raw.groupby(date).cumsum().eq(1)


def simulate_resolution(
    bars: pd.DataFrame,
    m5: pd.DataFrame,
    mask: pd.Series,
    candidate: dict[str, Any],
    anchor: dict[str, Any],
    resolution_minutes: int,
    delay: int,
) -> tuple[pd.DataFrame, dict[str, int]]:
    simulation_bars = bars.copy()
    offset = 60 - int(resolution_minutes)
    simulation_bars["timestamp"] = simulation_bars["timestamp"] - pd.Timedelta(
        minutes=offset
    )
    trades, diagnostics = simulate_short(
        simulation_bars,
        m5,
        mask,
        candidate,
        anchor,
        entry_delay_minutes=int(delay),
    )
    if not trades.empty:
        trades["signal_time_utc"] = trades["signal_time_utc"] + pd.Timedelta(
            minutes=offset
        )
        trades["signal_resolution_minutes"] = int(resolution_minutes)
    return trades, diagnostics


def _render_report(result: dict[str, Any]) -> str:
    rows = "\n".join(
        f"| {name} | {item['resolution_minutes']} | "
        f"{item['windows']['FULL_AUDIT']['trades']} | "
        f"{item['frequency']['trade_count_gain']:.1%} | "
        f"{item['windows']['FULL_AUDIT']['profit_factor']:.3f} | "
        f"{item['scenarios']['COST_PLUS_0P5_PIP']['profit_factor']:.3f} | "
        f"{item['windows']['LATEST_12_MONTHS']['profit_factor']:.3f} | "
        f"{item['eligible']} |"
        for name, item in result["levels"].items()
    )
    selected = result["levels"][result["selected_level"]]
    latest = selected["windows"]["LATEST_6_MONTHS"]
    return f"""# EURUSD H4 intrahour frequency ladder result

Status: **{result["status"]}**

| Level | Minutes | Trades | Gain | PF | +0.5 pip PF | Latest-12M PF | Eligible |
|---|---:|---:|---:|---:|---:|---:|---:|
{rows}

Selected level: **{result["selected_level"]}**.

Selected latest six months: {latest["trades"]} trades, PF {latest["profit_factor"]:.3f}, {latest["net_r"]:+.3f}R, {latest["pnl_usd_001_lot"]:+.2f} USD.
"""


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    package_root = config_path.parent.parent
    anchor_path = package_root / config["anchor_config"]["path"]
    if sha256_file(anchor_path) != config["anchor_config"]["sha256"]:
        raise RuntimeError("Anchor configuration checksum mismatch")
    anchor = json.loads(anchor_path.read_bytes())
    m5 = load_m5(anchor["source"])
    data_audit = audit_m5(m5, anchor["source"])
    h1 = aggregate_h1(m5)
    h1, h4 = add_h4_regimes(h1, anchor["classifier"])
    templates = {item["owned_regime"]: item for item in anchor["candidates"]}
    start, end = map(pd.Timestamp, config["evaluation_window"])
    delays = (0, *config["stress_scenarios"]["entry_delay_minutes"])
    priority = config["portfolio_risk"]["fixed_priority"]
    max_risk = float(config["portfolio_risk"]["maximum_concurrent_initial_risk_units"])
    boot = config["bootstrap"]
    level_results = {}
    level_ledgers = {}
    diagnostics = {}
    protected_trade_count = 0
    intrahour_cache = {
        minutes: aggregate_resolution_bars(m5, h1, h4, minutes) for minutes in (15, 30)
    }

    for level_name, resolution in config["resolution_ladder_minutes"].items():
        resolution = int(resolution)
        delayed_ledgers = {}
        delayed_caps = {}
        for delay in delays:
            pieces = []
            for regime in ("chop", "compression"):
                candidate = dict(templates[regime])
                candidate["specialist_id"] = (
                    f"{level_name}_{regime.upper()}_FIRST_BREAK"
                )
                if resolution == 60:
                    raw, diag = simulate_short(
                        h1,
                        m5,
                        build_signal_mask(h1, candidate),
                        candidate,
                        anchor,
                        entry_delay_minutes=int(delay),
                    )
                    if not raw.empty:
                        raw["signal_resolution_minutes"] = 60
                else:
                    bars = intrahour_cache[resolution]
                    raw, diag = simulate_resolution(
                        bars,
                        m5,
                        build_resolution_mask(bars, candidate, resolution),
                        candidate,
                        anchor,
                        resolution,
                        int(delay),
                    )
                raw = _evaluation_subset(raw, config["evaluation_window"])
                diagnostics[f"{level_name}_{regime}_{delay}m"] = diag
                piece = apply_portfolio_weight(
                    raw, float(config["protected_weights"][regime])
                )
                piece["portfolio_sleeve"] = f"BASELINE_{regime.upper()}"
                pieces.append(piece)
            delayed_ledgers[int(delay)], delayed_caps[f"{delay}m"] = (
                apply_causal_risk_cap(
                    pd.concat(pieces, ignore_index=True),
                    maximum_risk=max_risk,
                    priority=priority,
                )
            )
        ledger = delayed_ledgers[0]
        if level_name == "H60_PROTECTED":
            protected_trade_count = len(ledger)
        plus_half = apply_weighted_cost(ledger, 0.5)
        plus_one = apply_weighted_cost(ledger, 1.0)
        rollover = apply_weighted_rollover(
            ledger,
            float(
                config["stress_scenarios"]["rollover_charge_pips_per_utc_21_crossing"]
            ),
        )
        scenario_ledgers = {
            "BASE": ledger,
            "COST_PLUS_0P5_PIP": plus_half,
            "COST_PLUS_1P0_PIP": plus_one,
            "ENTRY_DELAY_5M": delayed_ledgers[5],
            "ENTRY_DELAY_15M": delayed_ledgers[15],
            "ROLLOVER_0P5_PIP": rollover,
        }
        scenarios = {
            name: _scenario_summary(trades) for name, trades in scenario_ledgers.items()
        }
        windows = _windows(ledger, config["reporting_windows"])
        trade_bootstrap = circular_block_bootstrap(
            ledger["r"].to_numpy(float),
            samples=int(boot["samples"]),
            block_trades=int(boot["trade_block_trades"]),
            seed=int(boot["seed"]),
            lower_quantile=float(boot["lower_quantile"]),
        )
        calendar_bootstrap = circular_calendar_month_bootstrap(
            ledger,
            start=start,
            end=end,
            samples=int(boot["samples"]),
            block_months=int(boot["calendar_block_months"]),
            seed=int(boot["seed"]),
            lower_quantile=float(boot["lower_quantile"]),
        )
        level_ledgers[level_name] = ledger
        level_results[level_name] = {
            "resolution_minutes": resolution,
            "windows": windows,
            "scenarios": scenarios,
            "trade_bootstrap": trade_bootstrap,
            "calendar_bootstrap": calendar_bootstrap,
            "risk_cap": delayed_caps,
            "concurrency": concurrency_audit(ledger),
        }
    for level_name, item in level_results.items():
        gates = evaluate_final_gates(
            protected_trade_count,
            item["windows"],
            item["scenarios"],
            item["trade_bootstrap"],
            item["calendar_bootstrap"],
            {
                **config["frequency_preserving_edge_gates"],
                "minimum_trade_count_gain": float(
                    config["selection_rule"]["minimum_trade_count_gain_over_H60"]
                ),
            },
        )
        count = item["windows"]["FULL_AUDIT"]["trades"]
        item["frequency"] = {
            "trades": count,
            "trade_count_gain": count / protected_trade_count - 1.0,
        }
        item["gate_results"] = gates
        item["eligible"] = all(gates.values())
    eligible = [
        name
        for name in config["resolution_ladder_minutes"]
        if level_results[name]["eligible"]
    ]
    selected_level = eligible[-1] if eligible else "H60_PROTECTED"
    selected = level_results[selected_level]
    fx_days = _fx_days(m5, start, end)
    for item in level_results.values():
        item["frequency"]["fx_days"] = fx_days
        item["frequency"]["trades_per_fx_day"] = item["frequency"]["trades"] / fx_days
    result = {
        "schema_version": "eurusd_h4_intrahour_frequency_ladder_result_v1",
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_sha256": anchor["source"]["sha256"],
        "post_hoc_developmental_not_pristine_oos": True,
        "broker_action_allowed": False,
        "data_audit": data_audit,
        "diagnostics": diagnostics,
        "levels": level_results,
        "eligible_nonbaseline_levels": [
            name for name in eligible if name != "H60_PROTECTED"
        ],
        "selected_level": selected_level,
        "selected_trade_count_gain": selected["frequency"]["trade_count_gain"],
        "status": (
            "INTRAHOUR_RESOLUTION_INCREASED_FREQUENCY_WITH_EDGE_PRESERVED_REQUIRES_FRESH_CONFIRMATION"
            if selected_level != "H60_PROTECTED"
            else "NO_SAFE_INTRAHOUR_FREQUENCY_EXPANSION"
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    level_ledgers[selected_level].to_csv(
        output_dir / "SELECTED_TRADES.csv", index=False, lineterminator="\n"
    )
    pd.DataFrame(
        [
            {
                "level": name,
                "resolution_minutes": item["resolution_minutes"],
                "eligible": item["eligible"],
                **item["windows"]["FULL_AUDIT"],
                "trade_count_gain": item["frequency"]["trade_count_gain"],
                "extra_0p5pip_profit_factor": item["scenarios"]["COST_PLUS_0P5_PIP"][
                    "profit_factor"
                ],
                "latest_12_month_profit_factor": item["windows"]["LATEST_12_MONTHS"][
                    "profit_factor"
                ],
            }
            for name, item in level_results.items()
        ]
    ).to_csv(output_dir / "LEVELS.csv", index=False, lineterminator="\n")
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (
        package_root / "EURUSD_H4_INTRAHOUR_FREQUENCY_LADDER_RESULT_2026_07_30.md"
    ).write_text(
        _render_report(result),
        encoding="utf-8",
        newline="\n",
    )
    return result
