from __future__ import annotations

from dataclasses import asdict, is_dataclass
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
from scipy import stats


PACKAGE = Path(__file__).resolve().parents[1]
FAST_RESEARCH = PACKAGE.parent
REPO = PACKAGE.parents[2]
PHASE0_SRC = REPO / "xau-usd" / "xauusd-phase0" / "src"
if str(PHASE0_SRC) not in sys.path:
    sys.path.insert(0, str(PHASE0_SRC))


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


R1 = _load_module(
    "out_of_era_r1_exact",
    FAST_RESEARCH / "mt5-r1-uptrend-portability-v1" / "src" / "portability.py",
)
EVENT = _load_module(
    "out_of_era_nfp_exact",
    FAST_RESEARCH
    / "macro-event-reaction-replication-v2"
    / "src"
    / "event_reaction.py",
)

from phase0.gld_etf_flow_data import GLD_ETF_FLOW_FRAME_KEY  # noqa: E402
from phase0.strategies.h4_gld_etf_flow_reversal_v0 import (  # noqa: E402
    H4GldEtfFlowReversalV0Strategy,
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_side_specific_m5(
    replay_root: Path, months: Iterable[str]
) -> pd.DataFrame:
    month_list = list(months)
    sides: dict[str, pd.DataFrame] = {}
    for side in ("bid", "ask", "mid"):
        frames: list[pd.DataFrame] = []
        for month in month_list:
            year, number = month.split("-")
            path = (
                replay_root
                / "bars"
                / "XAUUSD"
                / side
                / "M5"
                / f"year={year}"
                / f"month={number}"
                / "bars.parquet"
            )
            if not path.is_file():
                raise FileNotFoundError(path)
            frame = pd.read_parquet(path)
            frame["timestamp_utc"] = pd.to_datetime(
                frame["timestamp_utc"], utc=True, errors="raise"
            )
            frames.append(frame)
        combined = pd.concat(frames, ignore_index=True).sort_values(
            "timestamp_utc", kind="mergesort"
        )
        if combined["timestamp_utc"].duplicated().any():
            raise ValueError(f"Duplicate {side} M5 timestamps")
        rename = {
            value: f"{side}_{value}" for value in ("open", "high", "low", "close")
        }
        sides[side] = combined[
            ["timestamp_utc", "timestamp_ms", "tick_count", *rename]
        ].rename(columns=rename)
    counts = {side: len(frame) for side, frame in sides.items()}
    if len(set(counts.values())) != 1:
        raise ValueError(f"Side-specific M5 row counts differ: {counts}")
    merged = sides["bid"].rename(columns={"tick_count": "tick_count_bid"})
    merged = merged.merge(
        sides["ask"].drop(columns=["timestamp_ms"]).rename(
            columns={"tick_count": "tick_count_ask"}
        ),
        on="timestamp_utc",
        how="inner",
        validate="one_to_one",
    )
    merged = merged.merge(
        sides["mid"].drop(columns=["timestamp_ms"]).rename(
            columns={"tick_count": "tick_count_mid"}
        ),
        on="timestamp_utc",
        how="inner",
        validate="one_to_one",
    )
    if len(merged) != counts["bid"]:
        raise ValueError("Bid/Ask/Mid M5 timestamps are not exactly aligned")
    prices = [
        f"{side}_{field}"
        for side in ("bid", "ask", "mid")
        for field in ("open", "high", "low", "close")
    ]
    if (~np.isfinite(merged[prices]) | (merged[prices] <= 0.0)).any().any():
        raise ValueError("Invalid side-specific M5 price")
    if (merged["ask_open"] < merged["bid_open"]).any():
        raise ValueError("Crossed M5 opening quote")
    merged["bar_start_utc"] = merged["timestamp_utc"]
    merged["bar_end_utc"] = merged["bar_start_utc"] + pd.Timedelta(minutes=5)
    merged["timestamp_utc"] = merged["bar_end_utc"]
    merged["timeframe"] = "M5"
    merged["tick_count"] = merged["tick_count_mid"]
    previous = merged["mid_close"].shift(1)
    true_range = pd.concat(
        [
            merged["mid_high"] - merged["mid_low"],
            (merged["mid_high"] - previous).abs(),
            (merged["mid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    merged["atr"] = true_range.ewm(
        alpha=1.0 / 14.0, adjust=False, min_periods=14
    ).mean()
    return merged.sort_values("bar_start_utc", kind="mergesort").reset_index(
        drop=True
    )


def run_r1(m5: pd.DataFrame, source_config: Mapping[str, Any]) -> pd.DataFrame:
    d1, h4 = R1.BASE.prepare_signal_bars(m5, source_config["signal"])
    enriched, _ = R1.attach_r1_regime(
        m5,
        d1,
        h4,
        source_config["signal"],
        source_config["regime"],
    )
    candidates = R1.generate_r1_candidates(enriched, source_config["signal"])
    _, all_trades = R1.BASE.simulate_candidates(
        m5, candidates, source_config["execution"]
    )
    settings = source_config["policies"]["PORTFOLIO_CONSTRAINED_PRIMARY"]
    trades = R1.BASE.apply_policy(
        all_trades, "PORTFOLIO_CONSTRAINED_PRIMARY", settings
    )
    if trades.empty:
        return pd.DataFrame()
    result = trades.copy()
    if "candidate_id" in result:
        result["source_candidate_id"] = result["candidate_id"].astype(str)
    result["candidate_id"] = "R1_UPTREND_PORTABILITY_EXACT"
    result["source_policy_id"] = "PORTFOLIO_CONSTRAINED_PRIMARY"
    return result


def _official_nfp_calendar(path: Path) -> pd.DataFrame:
    rows = json.loads(path.read_text(encoding="utf-8"))
    calendar = pd.DataFrame(rows)
    calendar["event_type"] = "NFP"
    calendar["event_id"] = "NFP_" + calendar["date"]
    calendar["event_time_utc"] = pd.to_datetime(
        calendar["date"] + " 08:30:00"
    ).dt.tz_localize("America/New_York").dt.tz_convert("UTC")
    calendar["source_kind"] = "BLS_OFFICIAL_ARCHIVE"
    calendar["source_url"] = calendar["primaryUrl"]
    if calendar["event_id"].duplicated().any():
        raise ValueError("Duplicate NFP event IDs")
    return calendar.sort_values("event_time_utc", kind="mergesort").reset_index(
        drop=True
    )


def run_nfp(
    m5: pd.DataFrame,
    tick_store_root: Path,
    calendar_path: Path,
    source_config: Mapping[str, Any],
) -> tuple[pd.DataFrame, int, dict[str, Any]]:
    policy = next(
        item
        for item in source_config["policies"]
        if item["policy_id"] == "EVENT_NFP_FADE_RR2"
    )
    calendar = _official_nfp_calendar(calendar_path)
    candidates: list[dict[str, Any]] = []
    for event in calendar.itertuples(index=False):
        candidate = EVENT.candidate_for_event_policy(event, policy, m5)
        if candidate is not None:
            candidate["regime"] = "OUT_OF_ERA_UNROUTED"
            candidates.append(candidate)
    frame = pd.DataFrame(candidates)
    if frame.empty:
        return pd.DataFrame(), len(calendar), {"candidate_rows": 0}
    source = dict(source_config["source"])
    outcomes, audit = EVENT.label_candidates(
        frame,
        m5,
        tick_store_root,
        "XAUUSD",
        source,
        source_config["execution"],
    )
    if outcomes.empty:
        return outcomes, len(calendar), audit
    outcomes = outcomes.copy()
    outcomes["source_candidate_id"] = outcomes["candidate_id"].astype(str)
    outcomes["candidate_id"] = "NFP_FADE_RR2_EXACT"
    outcomes["source_policy_id"] = "EVENT_NFP_FADE_RR2"
    return outcomes, len(calendar), audit


def _h4_mid_frame(m5: pd.DataFrame, minimum_rows: int) -> pd.DataFrame:
    h4 = R1.BASE.aggregate_calendar_bars(m5, 240, "H4", minimum_rows)
    for field in ("open", "high", "low", "close"):
        h4[field] = h4[f"mid_{field}"]
    return h4


def _plan_dict(plan: Any) -> dict[str, Any]:
    if is_dataclass(plan):
        return asdict(plan)
    return dict(plan)


def simulate_gld_plan(
    m5: pd.DataFrame,
    signal_time: pd.Timestamp,
    direction: str,
    stop: float,
    target: float,
    execution: Mapping[str, Any],
) -> dict[str, Any] | None:
    starts = m5["bar_start_utc"].to_numpy(dtype="datetime64[ns]")
    decision = pd.Timestamp(signal_time)
    entry_index = int(
        np.searchsorted(starts, np.datetime64(decision.tz_convert(None)), side="left")
    )
    if entry_index >= len(m5):
        return None
    entry_time = pd.Timestamp(m5["bar_start_utc"].iat[entry_index])
    delay = (entry_time - decision).total_seconds() / 60.0
    if delay < 0.0 or delay > float(execution["maximum_entry_gap_minutes"]):
        return None
    side = direction.upper()
    entry = float(
        m5["ask_open"].iat[entry_index]
        if side == "LONG"
        else m5["bid_open"].iat[entry_index]
    )
    spread = float(m5["ask_open"].iat[entry_index] - m5["bid_open"].iat[entry_index])
    risk = entry - stop if side == "LONG" else stop - entry
    if risk < float(execution["minimum_stop_distance_usd"]):
        return None
    if spread > float(execution["maximum_entry_spread_usd"]):
        return None
    if spread / risk > float(execution["maximum_entry_spread_r"]):
        return None
    if (side == "LONG" and target <= entry) or (side == "SHORT" and target >= entry):
        return None
    maximum = min(
        len(m5), entry_index + int(execution["gld_maximum_hold_m5_bars"])
    )
    exit_index = maximum - 1
    exit_price = float(
        m5["bid_close"].iat[exit_index]
        if side == "LONG"
        else m5["ask_close"].iat[exit_index]
    )
    reason = "MAX_HOLD"
    exit_at_open = False
    ambiguous = False
    for index in range(entry_index, maximum):
        if side == "LONG":
            open_price = float(m5["bid_open"].iat[index])
            low = float(m5["bid_low"].iat[index])
            high = float(m5["bid_high"].iat[index])
            if open_price <= stop:
                exit_index, exit_price, reason, exit_at_open = (
                    index,
                    open_price,
                    "GAP_THROUGH_STOP",
                    True,
                )
                break
            if open_price >= target:
                exit_index, exit_price, reason, exit_at_open = (
                    index,
                    target,
                    "TARGET_GAP_FROZEN_TARGET",
                    True,
                )
                break
            stop_hit, target_hit = low <= stop, high >= target
        else:
            open_price = float(m5["ask_open"].iat[index])
            low = float(m5["ask_low"].iat[index])
            high = float(m5["ask_high"].iat[index])
            if open_price >= stop:
                exit_index, exit_price, reason, exit_at_open = (
                    index,
                    open_price,
                    "GAP_THROUGH_STOP",
                    True,
                )
                break
            if open_price <= target:
                exit_index, exit_price, reason, exit_at_open = (
                    index,
                    target,
                    "TARGET_GAP_FROZEN_TARGET",
                    True,
                )
                break
            stop_hit, target_hit = high >= stop, low <= target
        if stop_hit:
            exit_index, exit_price = index, stop
            ambiguous = bool(target_hit)
            reason = "AMBIGUOUS_M5_STOP_FIRST" if ambiguous else "STOP"
            break
        if target_hit:
            exit_index, exit_price, reason = index, target, "TARGET"
            break
    exit_time = pd.Timestamp(
        m5["bar_start_utc"].iat[exit_index]
        if exit_at_open
        else m5["bar_end_utc"].iat[exit_index]
    )
    sign = 1.0 if side == "LONG" else -1.0
    gross_r = sign * (exit_price - entry) / risk
    holding_days = max(0.0, (exit_time - entry_time).total_seconds() / 86400.0)
    risk_usd = risk * float(execution["ounces_at_0_01_lot"])
    extra_cost_r = (
        float(execution["ticket_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    return {
        "entry_time": entry_time,
        "exit_time": exit_time,
        "direction": side,
        "entry_price": entry,
        "exit_price": exit_price,
        "stop": stop,
        "target": target,
        "initial_risk_price": risk,
        "risk_usd": risk_usd,
        "entry_spread": spread,
        "entry_spread_r": spread / risk,
        "exit_reason": reason,
        "gross_r": gross_r,
        "stress_net_r": gross_r
        - extra_cost_r
        - float(execution["stress_slippage_r"]),
        "extra_cost_r": extra_cost_r,
        "holding_minutes": (exit_time - entry_time).total_seconds() / 60.0,
        "ambiguous_m5": ambiguous,
    }


def run_gld(
    m5: pd.DataFrame,
    gld_path: Path,
    execution: Mapping[str, Any],
) -> pd.DataFrame:
    h4 = _h4_mid_frame(
        m5, int(execution["minimum_m5_rows_per_h4_bucket"])
    )
    gld = pd.read_csv(gld_path)
    gld["timestamp_utc"] = pd.to_datetime(
        gld["timestamp_utc"], utc=True, errors="raise"
    )
    strategy = H4GldEtfFlowReversalV0Strategy()
    context = {
        "H4": h4,
        GLD_ETF_FLOW_FRAME_KEY: gld,
        "symbol": "XAUUSD",
        "open_position_exists": False,
    }
    signals = strategy.generate_signals(context)
    rows: list[dict[str, Any]] = []
    active_until: pd.Timestamp | None = None
    for signal in signals:
        plan = _plan_dict(strategy.build_trade_plan(signal, context))
        outcome = simulate_gld_plan(
            m5,
            pd.Timestamp(signal.timestamp_utc),
            signal.direction,
            float(plan["stop_loss"]),
            float(plan["take_profit"]),
            execution,
        )
        if outcome is None:
            continue
        if active_until is not None and outcome["entry_time"] < active_until:
            continue
        active_until = outcome["exit_time"]
        rows.append(
            {
                "candidate_id": "GLD_FLOW_REVERSAL_V0_EXACT",
                "source_policy_id": "h4_gld_etf_flow_reversal_v0",
                "signal_time": pd.Timestamp(signal.timestamp_utc),
                **outcome,
            }
        )
    return pd.DataFrame(rows)


def profit_factor(values: pd.Series) -> float:
    wins = float(values[values > 0.0].sum())
    losses = float(-values[values < 0.0].sum())
    if losses == 0.0:
        return float("inf") if wins > 0.0 else 0.0
    return wins / losses


def closed_drawdown(values: pd.Series) -> float:
    equity = values.cumsum()
    if equity.empty:
        return 0.0
    return float((equity.cummax() - equity).max())


def one_sided_daily_pvalue(trades: pd.DataFrame) -> float:
    if len(trades) < 2:
        return 1.0
    daily = trades.assign(
        day=pd.to_datetime(trades["entry_time"], utc=True).dt.floor("D")
    ).groupby("day", sort=True)["stress_net_r"].sum()
    if len(daily) < 2:
        return 1.0
    if float(daily.std(ddof=1)) == 0.0:
        return 0.0 if float(daily.mean()) > 0.0 else 1.0
    result = stats.ttest_1samp(
        daily.to_numpy(dtype=float), 0.0, alternative="greater"
    )
    return float(result.pvalue) if np.isfinite(result.pvalue) else 1.0


def holm_adjust(pvalues: Mapping[str, float]) -> dict[str, float]:
    ordered = sorted(pvalues, key=lambda key: pvalues[key])
    count = len(ordered)
    running = 0.0
    adjusted: dict[str, float] = {}
    for rank, key in enumerate(ordered):
        running = max(running, (count - rank) * float(pvalues[key]))
        adjusted[key] = min(1.0, running)
    return adjusted


def summarize(
    candidate_id: str,
    trades: pd.DataFrame,
    gate: Mapping[str, Any],
    event_count: int | None = None,
) -> dict[str, Any]:
    values = (
        trades["stress_net_r"].astype(float)
        if not trades.empty
        else pd.Series(dtype=float)
    )
    yearly = (
        trades.assign(
            year=pd.to_datetime(trades["entry_time"], utc=True).dt.year
        ).groupby("year", sort=True)["stress_net_r"].sum()
        if not trades.empty
        else pd.Series(dtype=float)
    )
    removed = values.sort_values(ascending=False).iloc[
        int(gate["top_winners_removed"]) :
    ]
    result = {
        "candidate_id": candidate_id,
        "trades": int(len(trades)),
        "stress_net_r": float(values.sum()),
        "stress_pf": profit_factor(values),
        "average_stress_r": float(values.mean()) if len(values) else 0.0,
        "closed_drawdown_r": closed_drawdown(values),
        "positive_active_year_share": (
            float((yearly > 0.0).mean()) if len(yearly) else 0.0
        ),
        "top_winners_removed_stress_net_r": float(removed.sum()),
        "daily_pvalue": one_sided_daily_pvalue(trades),
    }
    if event_count is not None:
        result["event_count"] = int(event_count)
        result["event_participation"] = (
            len(trades) / event_count if event_count else 0.0
        )
    return result


def gate_checks(
    metrics: Mapping[str, Any], gate: Mapping[str, Any], holm_pvalue: float
) -> dict[str, bool]:
    checks = {
        "minimum_trades": int(metrics["trades"]) >= int(gate["minimum_trades"]),
        "minimum_stress_pf": float(metrics["stress_pf"])
        >= float(gate["minimum_stress_pf"]),
        "minimum_average_stress_r": float(metrics["average_stress_r"])
        >= float(gate["minimum_average_stress_r"]),
        "maximum_closed_drawdown_r": float(metrics["closed_drawdown_r"])
        <= float(gate["maximum_closed_drawdown_r"]),
        "minimum_positive_active_year_share": float(
            metrics["positive_active_year_share"]
        )
        >= float(gate["minimum_positive_active_year_share"]),
        "top_winners_removed_positive": float(
            metrics["top_winners_removed_stress_net_r"]
        )
        > 0.0,
        "maximum_holm_pvalue": holm_pvalue
        <= float(gate["maximum_holm_pvalue"]),
    }
    if "minimum_event_participation" in gate:
        checks["minimum_event_participation"] = float(
            metrics.get("event_participation", 0.0)
        ) >= float(gate["minimum_event_participation"])
    return checks
